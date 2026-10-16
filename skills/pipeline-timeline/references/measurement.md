# Measuring on a Jetson device

## Contents
1. Device preparation checklist
2. Running a campaign
3. What the tracer records mean
4. Metric definitions
5. Pitfalls seen in practice

## 1. Device preparation checklist

Run these over SSH (`power@<device>`) before any measurement and write the answers into the report:

- **Version:** `cat ~/versions.json` → Core-Backend commit and package. Run `check_pipeline.py` against that commit.
- **Libraries link:** `ldd ~/Core/build/cpputils/libutils.so | grep "not found"` must print nothing. One package build (Ubuntu 18.04 toolchain on a JetPack 6 device) needed `libjsoncpp.so.1` and the worker exited at start.
- **Power mode:** `nvpmodel -q`. Never change it or run `jetson_clocks`; record it.
- **Worker stopped:** `systemctl is-active worker.service` must be `inactive` and no `python3 .../worker.py` may run, or it holds the cameras. Stopping needs sudo: ask the user to run `ssh -t power@<device> 'sudo systemctl stop worker.service'`. Never type or reuse a password, even if the user pastes one; if they do, tell them to rotate it.
- **Feature under test active:** e.g. for alertsocket the extended API (`~/POWER_Const/interface_activated` or a license). Without it the element does nothing in both cases.
- **Mock that keeps the GPU busy:** settings field `mock_cnn_enabled` must exist in `Core/managers/settings/groups/detection.py`. Master's old Python MockCNN only **sleeps** (no GPU load); develop commit `7aa03a9ae` runs the real network and replaces its results. Scenarios: `20_buoys_center.json`, `50_objects_stress.json`, `100_objects_stress.json` in `Inference_lib/NN/scenarios/`.
- **Scripts on the device are current:** compare `~/Tools/scripts/power_mode_perf.sh`, `measure_worker_cpu.py` and `parse_perf_report.py` with the repo; copy with `rsync -a` (no `--delete`) if they differ.
- **gst-shark installed:** `gst-inspect-1.0 proctime` and `~/gst-shark/scripts/analizer/gstshark-report.py` exist.
- **Back up** any runtime file you change (`~/<work>/backup_installed/`), never `rm -rf` runtime folders, never commit or push.

## 2. Running a campaign

Use `scripts/campaign.sh` (copy it to a new folder on the device, one folder per campaign). It:
- swaps the file under test before every run and checks it with `diff`,
- alternates cases (on, off, on, off, …) so drift affects both equally,
- calls `~/Tools/scripts/power_mode_perf.sh` with a unique `PERF_LABEL` per run (the script refuses to reuse labels),
- adds the element under test to `PERF_TRACERS` (the default filter does **not** include e.g. alertsocket),
- sets `SETTINGS_OVERRIDES` (inference verbose + mock scenario) and the matching env vars,
- restores the installed file at the end.

Defaults that worked: 3 runs per case, 60 s each, 30 s pause. Each run takes ~80 s with startup and report. `power_mode_perf.sh` drops the first 15 s. Run it with `nohup … < /dev/null &` so SSH can disconnect.

`power_mode_perf.sh` also passes `do_tracker_rotcomp=false`, a stale setting name that has no effect (SEA-AI/Core-Backend#1108). Note it if still present.

## 3. What the tracer records mean

The console log of every run (`<label>_console.log`) contains the raw gst-shark records because `GST_DEBUG=GST_TRACER:7` prints to stderr. Format:

`<elapsed> <pid> <thread-id> TRACE GST_TRACER :0:: proctime, element=(string)<name>, time=(string)<duration>;`

- **Thread id** tells which thread logged it (T5 vs T6 etc.).
- **`proctime` of an element** = time in that element. With `infer-only=True` (default in `power_mode_perf.sh`) element records are logged **only for N batches**; S batches are invisible. A timeline drawn from these records alone shows gaps where stage 2 is actually busy with S batches.
- **`proctime` of a queue** is logged when a batch **leaves** the queue; `time` = how long it waited. Queue records exist for **every** batch. Entry time = log time − wait.
- Queues are FIFO. `scripts/batches.py` uses that to follow each batch: N/S from whether an inference record starts when the batch leaves `queue_processing`, then matching its stage-1 end with the entry time of a `queue_inference` record.
- `queuelevel` records give the fill level of each queue (where the waiting is).
- `framerate` records are per-second counts per pad (`wsstatus_src` = worker fps).

The gst-shark CTF directories are deleted by `power_mode_perf.sh` after the report; the console logs are the raw data.

## 4. Metric definitions

| Metric | Source |
|---|---|
| Worker fps (batches/s) | `<label>_metrics.json` → `wsstatus_src.framerate_mean_fps` |
| Network runs/s (processing fps) | timestamps of `Model profiling` lines (needs `inference_verbose`) |
| Element time per batch | `metrics.json` → `<element>.proctime_mean_ms` (N batches only with infer-only) |
| Inference split | `Model profiling` (pre / network / post) and `[.. ms] get_images_from_batch` medians; rest = whole element − parts (Python inference only) |
| Stage 2 per batch | `batches.py`: next stage-2 start − this start; exact only when stage 2 never idles |
| Latency | muxer → end of stage 2 per batch (`batches.py`), reported separately for N and S |
| Power, CPU, GPU | `<label>_worker_cpu.json` (tegrastats, after 15 s warm-up). VDD_IN = whole Jetson module; VDD_CPU_GPU_CV = CPU + GPU + CV rail |

Report N-batch latency as "detection delay"; do not average N and S. Do not compare temperatures on a full product (ambient and enclosure dominate); compare power.

## 5. Pitfalls seen in practice

- A run can crash at startup when the IMU fails to open (OpenCV assertion). Repeat it with a new label; do not mix it in.
- Network time drifted 172 → 106 ms between two installs of the "same" software. Do a 40 s sanity run (no tracer) and compare the network median with earlier runs before a campaign.
- With the old sleep-only MockCNN, inference time is fixed and the GPU idles; results say nothing about GPU load or power.
- Model check: `make_timeline.py` reports model vs measured cycle time. If they differ by more than ~10 %, the stage times or the pipeline assumptions (pool size, interval, camera fps) are off; recheck before publishing.
