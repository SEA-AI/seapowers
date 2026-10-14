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
STOP_MARK='== stopped by device.sh =='  # last log line after `stop`, so status can tell a stop from a crash
r() { ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST" "$@"; }

# Remote snippet that picks the run command: `make run` if ~/Makefile exists, else worker.py in WORKER_DIR or
# the first candidate folder that has one. Leaves the command in "$@" and the folder as the cwd; exit 3 if none.
if [ -n "$WORKER_DIR" ]; then FIND="d=$(printf %q "$WORKER_DIR")"
else FIND="for d in $CANDIDATES; do [ -f \"\$d/worker.py\" ] && break; done"; fi
CHOOSE="cd ~; if [ -f Makefile ]; then set -- make run; else $FIND; [ -f \"\$d/worker.py\" ] || exit 3; cd \"\$d\"; set -- python3 worker.py; fi"

# Remote helpers. The worker is tracked as a descendant of the tmux pane, not by command-line pattern,
# so it works whatever launcher make uses and never matches this ssh command itself.
H="S=$SESSION; MTX=$MTX; "'tree() { for c in $(pgrep -P "$1"); do echo "$c"; tree "$c"; done; }
pane() { tmux list-panes -t "$S" -F "#{pane_pid}" 2>/dev/null; }
worker() { p=$(pane); [ -n "$p" ] || return 1; for c in $(tree "$p"); do grep -qa worker.py /proc/$c/cmdline 2>/dev/null && return 0; done; return 1; }
kill_all() { p=$(pane); pids=$( [ -n "$p" ] && tree "$p"); tmux kill-session -t "$S" 2>/dev/null
  [ -n "$pids" ] && { kill $pids 2>/dev/null; sleep 3; kill -9 $pids 2>/dev/null; }; true; }
webrtc_bytes() { curl -s -m3 "$MTX/paths/list" | python3 -c "import json,sys
try: print(sum(p.get(\"inboundBytes\", p.get(\"bytesReceived\", 0)) for p in json.load(sys.stdin).get(\"items\", []) if p.get(\"name\", \"\").endswith(\"_webrtc\")))
except Exception: print(\"NOAPI\")" 2>/dev/null || echo NOAPI; }'
tail_log() { r "tail -15 $LOG 2>/dev/null" | tr '\n' ' '; }  # one line, so the event stays one line

case "${1:-}" in
preflight)
  [ -n "$DATA_DIR" ] || { echo "PREFLIGHT_FAIL DATA_DIR is required"; exit 1; }
  r true 2>/dev/null || { echo "PREFLIGHT_FAIL ssh to $HOST"; exit 1; }
  r "test -d $(printf %q "$DATA_DIR")" || { echo "PREFLIGHT_FAIL data dir missing: $DATA_DIR"; exit 1; }
  if [ -z "$PRODUCT" ]; then
    r "ls ~/POWER_Const/hardwareVersion* ~/POWER_Const/module_info* >/dev/null 2>&1" \
      || { echo "PREFLIGHT_FAIL no hardwareVersion/module_info in ~/POWER_Const: device can't infer its product, pass PRODUCT"; exit 1; }
  fi
  run=$(r "$CHOOSE; echo \"\$PWD: \$*\"") \
    || { echo "PREFLIGHT_FAIL no ~/Makefile and no worker.py in ${WORKER_DIR:-$CANDIDATES}: pass WORKER_DIR"; exit 1; }
  r "test -e ~/POWER_Const/system_successfully_registered" || echo "WARN registration bypass file missing (expect a registration gate)"
  missing=$(r 'for c in tmux curl python3 pgrep; do command -v $c >/dev/null || printf "%s " $c; done')
  [ -z "$missing" ] || { echo "PREFLIGHT_FAIL missing on device: $missing"; exit 1; }
  [ "$(r "$H; webrtc_bytes")" != NOAPI ] || { echo "PREFLIGHT_FAIL MediaMTX API not reachable at $MTX on the device"; exit 1; }
  echo "RUN_CMD $run${PRODUCT:+ (PRODUCT=$PRODUCT)}"
  # estimate = longest single video file (cameras play in parallel); wrong for segmented recordings or other formats
  secs=$(r "command -v ffprobe >/dev/null && find $(printf %q "$DATA_DIR") -type f \( -name '*.mp4' -o -name '*.mkv' -o -name '*.h264' -o -name '*.ts' \) \
    -exec ffprobe -v error -show_entries format=duration -of csv=p=0 {} \; 2>/dev/null | grep -E '^[0-9.]+$' | sort -n | tail -1")
  echo "CLIP_SECONDS ${secs:-unknown}"
  echo "PREFLIGHT_OK"
  ;;
start)
  [ -n "$DATA_DIR" ] || { echo "CRASH DATA_DIR is required"; exit 1; }
  # The run command goes into a remote script: no nested quoting, paths with spaces survive.
  # bash -ic because PYTHONPATH and friends often live only in ~/.bashrc.
  env="export DATA_DIR=$(printf %q "$DATA_DIR")${PRODUCT:+; export PRODUCT=$(printf %q "$PRODUCT")}"
  r "$H; kill_all; cat > $RUNNER" <<<"$env; $CHOOSE; exec \"\$@\"" || { echo "CRASH could not reach device"; exit 1; }
  r "tmux new -d -s $SESSION \"bash -ic 'bash $RUNNER 2>&1 | tee $LOG'\"" || { echo "CRASH tmux could not start the worker"; exit 1; }
  echo "STARTED $(date +%T%z)"
  # the launcher takes a few seconds to spawn the worker; wait-ready treats "no worker" as a crash
  r "$H; for i in \$(seq 30); do worker && exit 0; sleep 1; done; exit 1" || { echo "CRASH worker never spawned: $(tail_log)"; exit 1; }
  exec bash "$0" wait-ready  # the old worker is already dead here, so flowing bytes mean the new one
  ;;
wait-ready)
  # Ready = video bytes flowing into MediaMTX (open ports and its "ready" flag can be stale).
  # Crash = the worker process is gone (the log has harmless tracebacks).
  for _ in $(seq 60); do
    out=$(r "$H; worker || echo DEAD; webrtc_bytes; sleep 2; webrtc_bytes")
    case "$out" in *DEAD*) echo "CRASH $(tail_log)"; exit 1;; *NOAPI*) echo "CRASH MediaMTX API unreachable"; exit 1;; esac
    a=$(sed -n 1p <<<"$out"); b=$(sed -n 2p <<<"$out")
    [ "${b:-0}" -gt "${a:-0}" ] && { echo "READY $(date +%T%z) webrtc bytes flowing"; exit 0; }
    sleep 1
  done
  echo "CRASH no webrtc bytes after 60 checks: $(tail_log)"; exit 1
  ;;
status)
  # The tmux session closes when the worker exits, so without a session the log decides:
  # stopped by us (or never started) = STOPPED, "End-of-stream" (current log text) = ENDED, anything else = CRASH.
  state=$(r "$H; if tmux has-session -t \$S 2>/dev/null; then
      if grep -q 'End-of-stream' $LOG 2>/dev/null; then echo ENDED; elif worker; then echo RUNNING; else echo CRASH; fi
    elif [ ! -s $LOG ] || tail -1 $LOG | grep -qF '$STOP_MARK'; then echo STOPPED
    elif grep -q 'End-of-stream' $LOG; then echo ENDED; else echo CRASH; fi")
  [ -n "$state" ] || { echo "CRASH could not reach device"; exit 1; }
  [ "$state" = CRASH ] && echo "CRASH $(tail_log)" || echo "$state"
  ;;
stop)
  r "$H; kill_all; echo '$STOP_MARK' >> $LOG" && echo STOPPED || { echo "CRASH could not reach device"; exit 1; }
  ;;
*) echo "usage: device.sh preflight|start|wait-ready|status|stop"; exit 2;;
esac
