#!/usr/bin/env bash
# Device-side control for record-device-app. Every command prints one-line events: EVENT detail
# Usage: HOST=user@ip DATA_DIR=<abs recording dir> [PRODUCT=<product>] [WORKER_DIR=<dir, relative to device home or absolute>] \
#        device.sh preflight|start|wait-ready|status|stop
# PRODUCT is the exception: only needed when ~/POWER_Const has no hardwareVersion/module_info.
set -u
: "${HOST:?}" "${PRODUCT:=}" "${DATA_DIR:=}" "${WORKER_DIR:=}"
WORKER_DIR=${WORKER_DIR#\~/}  # "~/Worker" means the same as "Worker" (paths are relative to the device home)

# Device conventions (SKILL.md mirrors them for readers)
CANDIDATES="Worker Core-Backend/Worker"   # worker folders tried in order, relative to the device home
MTX=localhost:9997/v3                     # MediaMTX API on the device
SESSION=rda                               # tmux session; one run per device at a time
LOG=/tmp/record_device_app.log
RUNNER=/tmp/record_device_app_run.sh
SEEN=/tmp/record_device_app.seen        # exists once this run's worker was seen, so a gone worker reads as a crash
STOP_MARK='== stopped by device.sh =='  # last log line after `stop`, so status can tell a stop from a crash
# Timing settings (whole seconds): defaults suit a LAN; override per run via env.
READY_TIMEOUT_S=${READY_TIMEOUT_S:-270}  # wait for the worker to start and every camera's WebRTC stream to flow
KILL_GRACE_S=${KILL_GRACE_S:-3}          # after asking the old worker to stop, before force-killing it
SSH_TIMEOUT_S=${SSH_TIMEOUT_S:-5}        # ssh connect timeout; raise over VPN or mobile links
SAMPLE_S=2                               # gap between two byte counts when checking that video flows
for v in READY_TIMEOUT_S KILL_GRACE_S SSH_TIMEOUT_S; do
  [[ ${!v} =~ ^[1-9][0-9]*$ ]] || { echo "BAD_ARGS $v must be a whole number >= 1"; exit 2; }
done
# keepalive: a link that drops mid-command fails within ~2x SSH_TIMEOUT_S instead of hanging
r() { ssh -o BatchMode=yes -o ConnectTimeout="$SSH_TIMEOUT_S" -o ServerAliveInterval="$SSH_TIMEOUT_S" -o ServerAliveCountMax=2 "$HOST" "$@"; }

# Remote snippet that picks the run command: `make run` if ~/Makefile exists, else worker.py in WORKER_DIR or
# the first candidate folder that has one. Leaves the command in "$@" and the folder as the cwd; exit 3 if none.
if [ -n "$WORKER_DIR" ]; then FIND="d=$(printf %q "$WORKER_DIR")"
else FIND="for d in $CANDIDATES; do [ -f \"\$d/worker.py\" ] && break; done"; fi
CHOOSE="cd ~; if [ -f Makefile ]; then set -- make run; else $FIND; [ -f \"\$d/worker.py\" ] || exit 3; cd \"\$d\"; set -- python3 worker.py; fi"

# Remote helpers. The worker is tracked as a descendant of the tmux pane, not by command-line pattern,
# so it works whatever launcher make uses and never matches this ssh command itself.
H="S=$SESSION; MTX=$MTX; G=$KILL_GRACE_S; SEEN=$SEEN; "'tree() { for c in $(pgrep -P "$1"); do echo "$c"; tree "$c"; done; }
pane() { tmux list-panes -t "$S" -F "#{pane_pid}" 2>/dev/null; }
worker() { p=$(pane); [ -n "$p" ] || return 1; for c in $(tree "$p"); do tr "\0" "\n" </proc/$c/cmdline 2>/dev/null | grep -qxE "(.*/)?worker\.py" && { touch "$SEEN"; return 0; }; done; return 1; }
kill_all() { p=$(pane); pids=$( [ -n "$p" ] && tree "$p"); tmux kill-session -t "$S" 2>/dev/null; rm -f "$SEEN"
  [ -n "$pids" ] && { kill $pids 2>/dev/null; sleep "$G"; kill -9 $pids 2>/dev/null; }; true; }
webrtc_bytes() { curl -s -m3 "$MTX/paths/list" | python3 -c "import json,sys
try: [print(p[\"name\"], p.get(\"inboundBytes\", p.get(\"bytesReceived\", 0))) for p in json.load(sys.stdin).get(\"items\", []) if p.get(\"name\", \"\").endswith(\"_webrtc\")]
except Exception: print(\"NOAPI\")" 2>/dev/null || echo NOAPI; }'
tail_log() { r "tail -15 $LOG 2>/dev/null" | tr '\n' ' '; }  # one line, so the event stays one line

case "${1:-}" in preflight|start) [ -n "$DATA_DIR" ] || { echo "BAD_ARGS DATA_DIR is required"; exit 2; };; esac

case "${1:-}" in
preflight)
  r true 2>/dev/null || { echo "PREFLIGHT_FAIL ssh to $HOST"; exit 1; }
  r "test -d $(printf %q "$DATA_DIR")" || { echo "PREFLIGHT_FAIL data dir missing: $DATA_DIR"; exit 1; }
  if [ -z "$PRODUCT" ]; then
    r 'for f in ~/POWER_Const/hardwareVersion* ~/POWER_Const/module_info*; do [ -e "$f" ] && exit 0; done; exit 1' \
      || { echo "PREFLIGHT_FAIL no hardwareVersion/module_info in ~/POWER_Const: device can't infer its product, pass PRODUCT"; exit 1; }
  fi
  run=$(r "$CHOOSE; echo \"\$PWD: \$*\"") \
    || { echo "PREFLIGHT_FAIL no ~/Makefile and no worker.py in ${WORKER_DIR:-$CANDIDATES}: pass WORKER_DIR"; exit 1; }
  r "test -e ~/POWER_Const/system_successfully_registered" || echo "WARN registration bypass file missing (expect a registration gate)"
  missing=$(r 'for c in tmux curl python3 pgrep; do command -v $c >/dev/null || printf "%s " $c; done')
  [ -z "$missing" ] || { echo "PREFLIGHT_FAIL missing on device: $missing"; exit 1; }
  [ "$(r "$H; webrtc_bytes")" != NOAPI ] || echo "WARN MediaMTX API not reachable at $MTX yet (fine if the worker starts it)"
  # something else (a service, another user) already streaming would make READY meaningless
  r "$H; tmux has-session -t \$S 2>/dev/null && exit 1; a=\$(webrtc_bytes); sleep $SAMPLE_S; [ \"\$a\" != \"\$(webrtc_bytes)\" ]" \
    && echo "WARN video is already streaming without this skill's worker; stop it first or READY may be misleading"
  echo "RUN_CMD $run${PRODUCT:+ (PRODUCT=$PRODUCT)}"
  # Each video file is one camera (recordings are never split per camera); the worker stops when the first
  # stream ends, so the clip is as long as the shortest file.
  clip=$(r "command -v ffprobe >/dev/null && find $(printf %q "$DATA_DIR") -type f \\( -name '*.mp4' -o -name '*.avi' -o -name '*.mkv' \\) \\
    -exec ffprobe -v error -show_entries format=duration -of csv=p=0 {} \\; 2>/dev/null \\
    | awk '/^[0-9.]+\$/ { n++; if (m == \"\" || \$1 < m) m = \$1 } END { if (n) printf \"%.0f (%d cameras)\", m, n }'")
  echo "CLIP_SECONDS ${clip:-unknown}"
  echo "PREFLIGHT_OK"
  ;;
start)
  # The run command goes into a remote script: no nested quoting, paths with spaces survive.
  # bash -ic because PYTHONPATH and friends often live only in ~/.bashrc. Unbuffered, so the log is current.
  env="export PYTHONUNBUFFERED=1 DATA_DIR=$(printf %q "$DATA_DIR")${PRODUCT:+; export PRODUCT=$(printf %q "$PRODUCT")}"
  r "$H; kill_all; cat > $RUNNER" <<<"$env; $CHOOSE; exec \"\$@\"" || { echo "UNREACHABLE ssh to $HOST failed"; exit 1; }
  r "tmux new -d -s $SESSION \"bash -ic 'bash $RUNNER 2>&1 | tee $LOG'\""
  case $? in 0) ;; 255) echo "UNREACHABLE ssh to $HOST failed"; exit 1;; *) echo "CRASH tmux could not start the worker"; exit 1;; esac
  echo "STARTED $(date +%T%z)"
  exec bash "$0" wait-ready  # the old worker is already dead here, so flowing bytes mean the new one
  ;;
wait-ready)
  # Ready = every camera's WebRTC path receiving bytes (open ports and MediaMTX's "ready" flag can be stale).
  # Launcher gone, or this run's worker gone: status decides (STOPPED, ENDED or CRASH; the log has harmless
  # tracebacks). The launcher may take a while to spawn the worker (building?). Slow is not a crash: NOT_READY.
  end=$(( $(date +%s) + READY_TIMEOUT_S ))
  while [ "$(date +%s)" -lt "$end" ]; do
    out=$(r "$H; if worker; then echo WORKER; elif ! tmux has-session -t \$S 2>/dev/null; then echo DEAD; elif [ -e \$SEEN ]; then echo GONE; fi
      webrtc_bytes; echo ---; sleep $SAMPLE_S; webrtc_bytes") || { out=UNREACHABLE; sleep 1; continue; }  # a hiccup isn't a crash
    case "$out" in
      *DEAD*|*GONE*) exec bash "$0" status;;  # status tells an ended clip, a stop and a crash apart
    esac  # NOAPI: MediaMTX not up yet, keep waiting
    # ready when the same paths are listed before and after the pause, each with more bytes after it
    if n=$(awk '/^---$/ { after = 1; next } !/_webrtc/ { next } !after { a[$1] = $2; n++ } after { m++; if ($2 > a[$1]) up++ }
        END { if (n && up == n && m == n) print n; else exit 1 }' <<<"$out"); then
      echo "READY $(date +%T%z) all $n camera streams flowing"; exit 0
    fi
    sleep 1
  done
  case "$out" in UNREACHABLE) why="device unreachable over ssh";; *WORKER*NOAPI*) why="MediaMTX API unreachable";;
    *WORKER*) why="not every camera streams";;
    *) why="no worker process yet, launcher still running (building?)";; esac
  echo "NOT_READY $why after ${READY_TIMEOUT_S}s. Run wait-ready again, or check: $(tail_log)"; exit 1
  ;;
status)
  # The tmux session closes when the worker exits, so without a session the log decides:
  # stopped by us (or never started) = STOPPED, "End-of-stream" (current log text) = ENDED, anything else = CRASH.
  # A session without a worker: CRASH if this run's worker was already seen, else still launching (NOT_READY).
  state=$(r "$H; if tmux has-session -t \$S 2>/dev/null; then
      if grep -q 'End-of-stream' $LOG 2>/dev/null; then echo ENDED; elif worker; then echo RUNNING; elif [ -e \$SEEN ]; then echo GONE; else echo LAUNCHING; fi
    elif [ ! -e $LOG ] || tail -1 $LOG | grep -qF '$STOP_MARK'; then echo STOPPED
    elif grep -q 'End-of-stream' $LOG; then echo ENDED; else echo CRASH; fi")
  [ -n "$state" ] || { echo "UNREACHABLE ssh to $HOST failed"; exit 1; }
  case $state in
    CRASH) echo "CRASH $(tail_log)"; exit 1;;
    GONE) echo "CRASH worker exited, launcher still running: $(tail_log)"; exit 1;;
    LAUNCHING) echo "NOT_READY launcher running, no worker process yet: $(tail_log)"; exit 1;;
    *) echo "$state";;
  esac
  ;;
stop)
  r "$H; kill_all; echo '$STOP_MARK' >> $LOG" && echo STOPPED || { echo "UNREACHABLE ssh to $HOST failed"; exit 1; }
  ;;
*) echo "usage: device.sh preflight|start|wait-ready|status|stop"; exit 2;;
esac
