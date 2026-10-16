#!/bin/bash
# Interleaved A/B campaign on the device with Tools/scripts/power_mode_perf.sh.
#
# Copy this file into a NEW folder on the device (e.g. ~/perf_<ticket>_<date>/), put the two variants of the
# file under test next to it as <case>.<basename> (e.g. on.alertsocket.py, off.alertsocket.py), adjust the
# variables below, then start it detached:
#     nohup ./campaign.sh > campaign.log 2>&1 < /dev/null &
# The worker service must be stopped first (needs the user's sudo).
set -u

WORK="$(cd "$(dirname "$0")" && pwd)"
TARGET="/home/power/Core/Gst/plugins/python/alertsocket.py"   # runtime file swapped per case
ELEMENT="alertsocket"                                           # element added to the tracer filter
CASES="on off"                                                  # order of the first round; alternates after
ROUNDS=3
DURATION=60                                                     # seconds per run (power_mode_perf drops 15 s)
PAUSE=30                                                        # seconds idle between runs
SCENARIO="100_objects_stress.json"                              # mock scenario; "" = real detections
PRODUCT="watchkeeper"
TOOLS="/home/power/Tools/scripts"

BASE="$(basename "$TARGET")"
OUT="$WORK/pmp"; mkdir -p "$OUT"
for c in $CASES; do [ -f "$WORK/$c.$BASE" ] || { echo "missing $WORK/$c.$BASE"; exit 2; }; done
cp -n "$TARGET" "$WORK/installed.$BASE"      # keep the installed file

if [ -n "$SCENARIO" ]; then
  printf '{"detection": {"inference_verbose": true, "mock_cnn_enabled": true, "mock_scenario": "%s"}}\n' "$SCENARIO" > "$WORK/overrides.json"
  MOCK_ENV="mock_cnn_enabled=true mock_scenario=$SCENARIO"
else
  printf '{"detection": {"inference_verbose": true, "mock_cnn_enabled": false}}\n' > "$WORK/overrides.json"
  MOCK_ENV="mock_cnn_enabled=false"
fi

# default power_mode_perf.sh tracer string with the element under test added
TR="proctime(filter=inference|ignoremaskfilter|cpptransformation|sensorfusion|apply_stabilisation|horizon_detection|detection_horizon_filter|cppdistanceestimation|imgtracker|threatlevelmanager|postprocessing|bboxcache|alarmmanager|wsminiimages|track_object|${ELEMENT}|wsstatus|queue|encodingbin_rtsp,infer-only=True);framerate(filter=^inference|${ELEMENT}|wsstatus|encodingbin_rtsp|shmsink_rtsp);detectioncount(filter=imgtracker,infer-only=True);queuelevel"

echo "CAMPAIGN START $(date -u +%FT%TZ) element=$ELEMENT scenario=${SCENARIO:-real} rounds=$ROUNDS duration=$DURATION"
first=1
for n in $(seq 1 "$ROUNDS"); do
  for c in $CASES; do
    run="${c}_${n}"
    [ $first = 1 ] && first=0 || sleep "$PAUSE"
    cp "$WORK/$c.$BASE" "$TARGET"
    diff -q "$WORK/$c.$BASE" "$TARGET" >/dev/null || { echo "copy mismatch for $run"; exit 2; }
    echo "START $run $(date -u +%FT%TZ)"
    env PERF_PRODUCT="$PRODUCT" PERF_LABEL="$run" PERF_OUT_DIR="$OUT" PERF_DURATION="$DURATION" PERF_TRACERS="$TR" \
      SETTINGS_OVERRIDES="$WORK/overrides.json" $MOCK_ENV \
      "$TOOLS/power_mode_perf.sh" > "$OUT/${run}_console.log" 2>&1
    echo "END $run rc=$? $(date -u +%FT%TZ)"
  done
  CASES="$(echo $CASES | awk '{for (i=NF; i>0; i--) printf "%s ", $i}')"   # alternate the order each round
done
cp "$WORK/installed.$BASE" "$TARGET"
echo "CAMPAIGN END $(date -u +%FT%TZ) (installed file restored)"
