# Device-side commands for record-device-app. device.py sends this file over ssh: bash -s -- CMD [ARGS].
# Everything runs inside main(), so a child that reads stdin (ffprobe) can't eat the rest of the script.

# Device conventions (SKILL.md lists the ones to suspect when a step fails)
CANDIDATES="Worker Core-Backend/Worker"  # worker folders tried in order, relative to the device home
MTX=localhost:9997/v3                    # MediaMTX API on the device
PIDF=/tmp/record_device_app.pid          # launcher's pid; one run per device at a time
LOG=/tmp/record_device_app.log
RUNNER=/tmp/record_device_app_run.sh
SEEN=/tmp/record_device_app.seen         # exists once this run's worker was seen, so a gone worker reads as a crash
STOP_MARK='== stopped by record-device-app =='  # last log line after stop, so status can tell a stop from a crash
MARK="== record-device-app =="           # output before it comes from the login shell (e.g. ~/.bashrc), not us
SAMPLE_S=2                               # gap between two byte counts when checking that video flows

# The worker is found among the launcher's descendants by its worker.py argument,
# so it works whatever launcher make uses.
tree() { for c in $(pgrep -P "$1"); do echo "$c"; tree "$c"; done; }
launcher() { local p; p=$(cat "$PIDF" 2>/dev/null) && kill -0 "$p" 2>/dev/null && echo "$p"; }  # pid while it runs
worker() {
  local p c; p=$(launcher) || return 1
  for c in $(tree "$p"); do
    tr "\0" "\n" </proc/"$c"/cmdline 2>/dev/null | grep -qxE "(.*/)?worker\.py" && { touch "$SEEN"; return 0; }
  done
  return 1
}
kill_all() {  # $1: grace seconds between TERM and KILL
  local p pids; p=$(launcher) && pids="$p $(tree "$p")"
  rm -f "$PIDF" "$SEEN"
  [ -n "${pids:-}" ] && { kill $pids 2>/dev/null; sleep "$1"; kill -9 $pids 2>/dev/null; }; true
}
api() { curl -sf -m3 "$MTX/paths/list"; }
videos() { find "$1" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.avi' -o -iname '*.mkv' \); }  # one per camera
cameras() { videos "$1" | wc -l; }
duration() {  # seconds of one video: GStreamer's discoverer (the worker needs GStreamer anyway), else ffprobe
  if command -v gst-discoverer-1.0 >/dev/null; then
    gst-discoverer-1.0 "$1" </dev/null 2>/dev/null | awk '/Duration:/ { split($2, t, ":"); print t[1] * 3600 + t[2] * 60 + t[3]; exit }'
  elif command -v ffprobe >/dev/null; then
    ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" </dev/null 2>/dev/null
  fi
}

# Run command: `make run` if ~/Makefile exists, else worker.py in $1 (WORKER_DIR) or the first candidate folder.
# Leaves the command in RUN and the folder as the cwd; fails if there is none.
choose() {
  cd ~ || return 1
  if [ -f Makefile ]; then RUN=(make run); return 0; fi
  local d
  if [ -n "$1" ]; then d=$1; else for d in $CANDIDATES; do [ -f "$d/worker.py" ] && break; done; fi
  [ -f "$d/worker.py" ] && cd "$d" && RUN=(python3 worker.py)
}

preflight() {  # $1 DATA_DIR, $2 PRODUCT ("" = the device infers it), $3 WORKER_DIR, $4 SETTINGS_OVERRIDES
  [ -d "$1" ] || { echo "PREFLIGHT_FAIL data dir missing: $1"; return 1; }
  [ -z "$4" ] || [ -f "$4" ] || { echo "PREFLIGHT_FAIL settings overrides file missing: $4"; return 1; }
  if [ -z "$2" ] && ! compgen -G "$HOME/POWER_Const/hardwareVersion*" >/dev/null \
    && ! compgen -G "$HOME/POWER_Const/module_info*" >/dev/null; then
    echo "PREFLIGHT_FAIL no hardwareVersion/module_info in ~/POWER_Const: device can't infer its product, pass PRODUCT"
    return 1
  fi
  local c missing="" clip
  choose "$3" || { echo "PREFLIGHT_FAIL no ~/Makefile and no worker.py in ${3:-$CANDIDATES}: pass WORKER_DIR"; return 1; }
  [ -e ~/POWER_Const/system_successfully_registered ] \
    || echo "WARN registration bypass file missing (expect a registration gate)"
  for c in setsid curl pgrep "${RUN[0]}"; do command -v "$c" >/dev/null || missing+="$c "; done  # RUN[0]: make or python3
  [ -z "$missing" ] || { echo "PREFLIGHT_FAIL missing on device: $missing"; return 1; }
  echo "RUN_CMD $PWD: ${RUN[*]}${2:+ (PRODUCT=$2)}"
  # Each video file is one camera; the worker stops when the first stream ends, so the clip lasts as long as
  # the shortest file.
  clip=$(videos "$1" | while read -r f; do duration "$f"; done \
    | awk '/^[0-9.]+$/ { n++; if (m == "" || $1 < m) m = $1 } END { if (n) printf "%.0f (%d cameras)", m, n }')
  echo "CLIP_SECONDS ${clip:-unknown}"  # device.py adds the streaming checks and PREFLIGHT_OK
}

launch() {  # $1 DATA_DIR, $2 PRODUCT, $3 WORKER_DIR, $4 grace seconds, $5 SETTINGS_OVERRIDES; exit 3: no worker
  choose "$3" || return 3
  kill_all "$4"
  : >"$LOG"  # tee only truncates it after ~/.bashrc is sourced; until then status would read the old run
  # bash -ic because PYTHONPATH and friends often live only in ~/.bashrc. Unbuffered, so the log is current.
  { printf 'export PYTHONUNBUFFERED=1 DATA_DIR=%q\n' "$1"
    [ -z "$2" ] || printf 'export PRODUCT=%q\n' "$2"
    [ -z "$5" ] || printf 'export SETTINGS_OVERRIDES=%q\n' "$5"
    printf 'cd %q && exec' "$PWD"; printf ' %q' "${RUN[@]}"; echo; } >"$RUNNER"
  # setsid: its own session, so it outlives this ssh connection; all fds closed, so ssh doesn't wait for it
  setsid bash -ic "bash $RUNNER 2>&1 | tee $LOG" </dev/null >/dev/null 2>&1 &
  echo $! >"$PIDF"
}

probe() { status; api; echo; echo ---; sleep "$SAMPLE_S"; api; echo; }  # state, then two MediaMTX samples

status() {
  # The launcher exits when the worker does, so without it the log decides:
  # stopped by us (or never started) = STOPPED, "End-of-stream" (current log text) = ENDED, anything else = CRASH.
  if launcher >/dev/null; then
    if grep -q End-of-stream "$LOG" 2>/dev/null; then echo ENDED; elif worker; then echo RUNNING
    elif [ -e "$SEEN" ]; then echo GONE; else echo LAUNCHING; fi
  elif [ ! -e "$LOG" ] || tail -1 "$LOG" | grep -qF "$STOP_MARK"; then echo STOPPED
  elif grep -q End-of-stream "$LOG"; then echo ENDED; else echo CRASH; fi
}

stop() { kill_all "$1"; echo "$STOP_MARK" >>"$LOG"; }  # $1: grace seconds
logtail() { tail -15 "$LOG" 2>/dev/null; }

main() {
  echo "$MARK"
  case "${1:-}" in
    preflight | launch | probe | status | stop | logtail | cameras) "$@" ;;
    *) echo "BAD_ARGS unknown device command: ${1:-}"; return 2 ;;
  esac
}
main "$@"
