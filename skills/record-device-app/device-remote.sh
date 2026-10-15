# Device-side commands for record-device-app. device.py sends this file over ssh: bash -s -- CMD [ARGS].
# Everything runs inside main(), so a child that reads stdin (ffprobe) can't eat the rest of the script.

# Device conventions (keep the list in SKILL.md in sync)
CANDIDATES="Worker Core-Backend/Worker"  # worker folders tried in order, relative to the device home
MTX=localhost:9997/v3                    # MediaMTX API on the device
S=rda                                    # tmux session; one run per device at a time
LOG=/tmp/record_device_app.log
RUNNER=/tmp/record_device_app_run.sh
SEEN=/tmp/record_device_app.seen         # exists once this run's worker was seen, so a gone worker reads as a crash
STOP_MARK='== stopped by record-device-app =='  # last log line after stop, so status can tell a stop from a crash
SAMPLE_S=2                               # gap between two byte counts when checking that video flows

# The worker is found among the tmux pane's descendants by its worker.py argument,
# so it works whatever launcher make uses.
tree() { for c in $(pgrep -P "$1"); do echo "$c"; tree "$c"; done; }
pane() { tmux list-panes -t "$S" -F "#{pane_pid}" 2>/dev/null; }
worker() {
  local p c; p=$(pane); [ -n "$p" ] || return 1
  for c in $(tree "$p"); do
    tr "\0" "\n" </proc/"$c"/cmdline 2>/dev/null | grep -qxE "(.*/)?worker\.py" && { touch "$SEEN"; return 0; }
  done
  return 1
}
kill_all() {  # $1: grace seconds between TERM and KILL
  local p pids; p=$(pane); [ -n "$p" ] && pids=$(tree "$p")
  tmux kill-session -t "$S" 2>/dev/null; rm -f "$SEEN"
  [ -n "${pids:-}" ] && { kill $pids 2>/dev/null; sleep "$1"; kill -9 $pids 2>/dev/null; }; true
}
api() { curl -sf -m3 "$MTX/paths/list"; }
videos() { find "$1" -type f \( -name '*.mp4' -o -name '*.avi' -o -name '*.mkv' \); }  # one file per camera
cameras() { videos "$1" | wc -l; }

# Run command: `make run` if ~/Makefile exists, else worker.py in $1 (WORKER_DIR) or the first candidate folder.
# Leaves the command in RUN and the folder as the cwd; fails if there is none.
choose() {
  cd ~ || return 1
  if [ -f Makefile ]; then RUN=(make run); return 0; fi
  local d
  if [ -n "$1" ]; then d=$1; else for d in $CANDIDATES; do [ -f "$d/worker.py" ] && break; done; fi
  [ -f "$d/worker.py" ] && cd "$d" && RUN=(python3 worker.py)
}

preflight() {  # $1 DATA_DIR, $2 PRODUCT ("" = the device infers it), $3 WORKER_DIR; prints events
  [ -d "$1" ] || { echo "PREFLIGHT_FAIL data dir missing: $1"; return 1; }
  if [ -z "$2" ] && ! compgen -G "$HOME/POWER_Const/hardwareVersion*" >/dev/null \
    && ! compgen -G "$HOME/POWER_Const/module_info*" >/dev/null; then
    echo "PREFLIGHT_FAIL no hardwareVersion/module_info in ~/POWER_Const: device can't infer its product, pass PRODUCT"
    return 1
  fi
  local c tools="tmux curl pgrep" missing="" clip
  choose "$3" || { echo "PREFLIGHT_FAIL no ~/Makefile and no worker.py in ${3:-$CANDIDATES}: pass WORKER_DIR"; return 1; }
  tools+=" ${RUN[0]}"  # make or python3
  [ -e ~/POWER_Const/system_successfully_registered ] \
    || echo "WARN registration bypass file missing (expect a registration gate)"
  for c in $tools; do command -v $c >/dev/null || missing+="$c "; done
  [ -z "$missing" ] || { echo "PREFLIGHT_FAIL missing on device: $missing"; return 1; }
  echo "RUN_CMD $PWD: ${RUN[*]}${2:+ (PRODUCT=$2)}"
  # Each video file is one camera; the worker stops when the first stream ends, so the clip lasts as long as
  # the shortest file.
  command -v ffprobe >/dev/null && clip=$(videos "$1" | while read -r f; do
    ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" </dev/null 2>/dev/null; done \
    | awk '/^[0-9.]+$/ { n++; if (m == "" || $1 < m) m = $1 } END { if (n) printf "%.0f (%d cameras)", m, n }')
  echo "CLIP_SECONDS ${clip:-unknown}"  # device.py adds the streaming checks and PREFLIGHT_OK
}

launch() {  # $1 DATA_DIR, $2 PRODUCT, $3 WORKER_DIR, $4 grace seconds; exit 3: no worker to run
  choose "$3" || return 3
  kill_all "$4"
  : >"$LOG"  # tee only truncates it after ~/.bashrc is sourced; until then status would read the old run
  # bash -ic because PYTHONPATH and friends often live only in ~/.bashrc. Unbuffered, so the log is current.
  { printf 'export PYTHONUNBUFFERED=1 DATA_DIR=%q\n' "$1"
    [ -z "$2" ] || printf 'export PRODUCT=%q\n' "$2"
    printf 'cd %q && exec' "$PWD"; printf ' %q' "${RUN[@]}"; echo; } >"$RUNNER"
  tmux new -d -s "$S" "bash -ic 'bash $RUNNER 2>&1 | tee $LOG'"
}

probe() { status; api; echo; echo ---; sleep "$SAMPLE_S"; api; echo; }  # state, then two MediaMTX samples

status() {
  # The tmux session closes when the worker exits, so without a session the log decides:
  # stopped by us (or never started) = STOPPED, "End-of-stream" (current log text) = ENDED, anything else = CRASH.
  if tmux has-session -t "$S" 2>/dev/null; then
    if grep -q End-of-stream "$LOG" 2>/dev/null; then echo ENDED; elif worker; then echo RUNNING
    elif [ -e "$SEEN" ]; then echo GONE; else echo LAUNCHING; fi
  elif [ ! -e "$LOG" ] || tail -1 "$LOG" | grep -qF "$STOP_MARK"; then echo STOPPED
  elif grep -q End-of-stream "$LOG"; then echo ENDED; else echo CRASH; fi
}

stop() { kill_all "$1"; echo "$STOP_MARK" >>"$LOG"; }  # $1: grace seconds
logtail() { tail -15 "$LOG" 2>/dev/null; }

main() {
  case "${1:-}" in
    preflight | launch | probe | status | stop | logtail | cameras) "$@" ;;
    *) echo "BAD_ARGS unknown device command: ${1:-}"; return 2 ;;
  esac
}
main "$@"
