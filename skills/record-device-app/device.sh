#!/usr/bin/env bash
# Device-side control for record-device-app. Every command prints one-line events: EVENT detail
# Usage: HOST=user@ip DATA_DIR=<abs recording dir> [PRODUCT=<product>] [WORKER_DIR=<dir, relative to device home or absolute>] \
#        device.sh preflight|start|wait-ready|status|stop
# PRODUCT is the exception: only needed when ~/POWER_Const has no hardwareVersion/module_info.
set -u
: "${HOST:?}" "${PRODUCT:=}" "${DATA_DIR:=}"
# Worker folder (used after `cd ~`, so relative = from device home): WORKER_DIR if given, else the first of
# ~/Worker (usual) and ~/Core-Backend/Worker that has a worker.py. Ignored when ~/Makefile exists (make run).
WORKER_DIR=${WORKER_DIR:-}
if [ -n "$WORKER_DIR" ]; then FIND="d=$(printf %q "$WORKER_DIR")"
else FIND='for d in Worker Core-Backend/Worker; do [ -f "$d/worker.py" ] && break; done'; fi
# One run per device at a time: fixed tmux session and /tmp paths.
LOG=/tmp/record_device_app.log
RUNNER=/tmp/record_device_app_run.sh
r() { ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST" "$@"; }

# Remote helpers (single-quoted: expanded on the device). The worker is tracked as a descendant of the
# tmux pane, not by command-line pattern, so it works whatever launcher make uses and never matches ssh itself.
H='tree() { for c in $(pgrep -P "$1"); do echo "$c"; tree "$c"; done; }
pane() { tmux list-panes -t rda -F "#{pane_pid}" 2>/dev/null; }
worker() { p=$(pane); [ -n "$p" ] || return 1; for c in $(tree "$p"); do grep -qa worker.py /proc/$c/cmdline 2>/dev/null && return 0; done; return 1; }
kill_all() { p=$(pane); pids=$( [ -n "$p" ] && tree "$p"); tmux kill-session -t rda 2>/dev/null
  [ -n "$pids" ] && { kill $pids 2>/dev/null; sleep 3; kill -9 $pids 2>/dev/null; }; true; }
webrtc_bytes() { curl -s -m3 localhost:9997/v3/paths/list | python3 -c "import json,sys
try: print(sum(p.get(\"inboundBytes\", 0) for p in json.load(sys.stdin).get(\"items\", []) if p.get(\"name\", \"\").endswith(\"_webrtc\")))
except Exception: print(\"NOAPI\")" 2>/dev/null || echo NOAPI; }'

case "${1:-}" in
preflight)
  [ -n "$DATA_DIR" ] || { echo "PREFLIGHT_FAIL DATA_DIR is required"; exit 1; }
  r true 2>/dev/null || { echo "PREFLIGHT_FAIL ssh to $HOST"; exit 1; }
  r "test -d $(printf %q "$DATA_DIR")" || { echo "PREFLIGHT_FAIL data dir missing: $DATA_DIR"; exit 1; }
  if [ -z "$PRODUCT" ]; then
    r "ls ~/POWER_Const/hardwareVersion* ~/POWER_Const/module_info* >/dev/null 2>&1" \
      || { echo "PREFLIGHT_FAIL no hardwareVersion/module_info in ~/POWER_Const: device can't infer its product, pass PRODUCT"; exit 1; }
  fi
  r "cd ~ && { test -f Makefile || { $FIND; test -f \"\$d/worker.py\"; }; }" \
    || { echo "PREFLIGHT_FAIL no ~/Makefile and no worker.py in ${WORKER_DIR:-~/Worker or ~/Core-Backend/Worker}: pass WORKER_DIR"; exit 1; }
  r "test -e ~/POWER_Const/system_successfully_registered" || echo "WARN registration bypass file missing (app will show 'Register to SEA.AI')"
  missing=$(r 'for c in tmux curl python3; do command -v $c >/dev/null || printf "%s " $c; done')
  [ -z "$missing" ] || { echo "PREFLIGHT_FAIL missing on device: $missing"; exit 1; }
  # current convention: MediaMTX API on :9997 (v3); readiness depends on it
  [ "$(r "$H; webrtc_bytes")" != NOAPI ] || { echo "PREFLIGHT_FAIL MediaMTX API not reachable at localhost:9997/v3 on the device"; exit 1; }
  echo "RUN_CMD $(r "cd ~ && if [ -f Makefile ]; then echo 'make run'; else $FIND; echo \"cd ~/\$d && python3 worker.py\"; fi")${PRODUCT:+ (PRODUCT=$PRODUCT)}"
  # estimate = longest single video file (cameras play in parallel); wrong for segmented recordings
  secs=$(r "command -v ffprobe >/dev/null && find $(printf %q "$DATA_DIR") -type f \( -name '*.mp4' -o -name '*.mkv' -o -name '*.h264' -o -name '*.ts' \) \
    -exec ffprobe -v error -show_entries format=duration -of csv=p=0 {} \; 2>/dev/null | sort -n | tail -1")
  echo "CLIP_SECONDS ${secs:-unknown}"
  echo "PREFLIGHT_OK"
  ;;
start)
  # The run command goes into a remote script: no nested quoting, paths with spaces survive.
  # bash -ic because PYTHONPATH and friends often live only in ~/.bashrc.
  env="export DATA_DIR=$(printf %q "$DATA_DIR")${PRODUCT:+; export PRODUCT=$(printf %q "$PRODUCT")}"
  run="cd ~ && if [ -f Makefile ]; then exec make run; else $FIND; cd \"\$d\" && exec python3 worker.py; fi"
  r "$H; kill_all; cat > $RUNNER" <<<"$env; $run" || { echo "CRASH could not reach device"; exit 1; }
  r "tmux new -d -s rda \"bash -ic 'bash $RUNNER 2>&1 | tee $LOG'\"" && echo "STARTED $(date +%T%z)" || exit 1
  # launcher takes a few seconds to spawn the worker; wait-ready treats "no worker" as a crash
  r "$H; for i in \$(seq 30); do worker && exit 0; sleep 1; done; exit 1" \
    || { echo "CRASH worker never spawned: $(r "tail -15 $LOG")"; exit 1; }
  exec "$0" wait-ready  # old worker is already dead here, so flowing bytes mean the new one
  ;;
wait-ready)
  # ready = MediaMTX *_webrtc paths receiving bytes. An open port or MediaMTX "ready":true is not enough
  # (other services listen; "ready" persists across worker restarts). Crash = worker gone, not "Traceback in log".
  for _ in $(seq 60); do
    out=$(r "$H; worker || echo DEAD; webrtc_bytes; sleep 2; webrtc_bytes")
    case "$out" in *DEAD*) echo "CRASH $(r "tail -15 $LOG")"; exit 1;; *NOAPI*) echo "CRASH MediaMTX API unreachable"; exit 1;; esac
    a=$(sed -n 1p <<<"$out"); b=$(sed -n 2p <<<"$out")
    [ "${b:-0}" -gt "${a:-0}" ] && { echo "READY $(date +%T%z) webrtc bytes flowing"; exit 0; }
    sleep 1
  done
  echo "CRASH no webrtc bytes after 60 checks: $(r "tail -5 $LOG")"; exit 1
  ;;
status)
  # ENDED relies on the worker logging "End-of-stream" (current log text)
  r "$H; if ! tmux has-session -t rda 2>/dev/null; then echo STOPPED; elif grep -q 'End-of-stream' $LOG 2>/dev/null; then echo ENDED; \
     elif worker; then echo RUNNING; else echo CRASH; tail -15 $LOG; fi"
  ;;
stop)
  r "$H; kill_all" && echo STOPPED
  ;;
*) echo "usage: device.sh preflight|start|wait-ready|status|stop"; exit 2;;
esac
