# Measuring on a Jetson device

## Device checklist

Run these over SSH (`power@<device>`) before any measurement and write the answers into the report:

- **Version:** `cat ~/versions.json`: Core-Backend commit and package. Read the pipeline details from that commit (see `pipeline.md`).
- **Libraries link:** `ldd ~/Core/build/cpputils/libutils.so | grep "not found"` must print nothing; a package built with another toolchain can miss a library and the worker exits at start.
- **Power mode:** `nvpmodel -q`. Never change it or run `jetson_clocks`; record it.
- **Worker stopped:** `systemctl is-active worker.service` must be `inactive` and no `worker.py` may run, or it holds the cameras. Stopping needs sudo: ask the user to run `ssh -t power@<device> 'sudo systemctl stop worker.service'`. Never type or reuse a password, even if the user pastes one; if they do, tell them to rotate it.
- **Feature under test active:** the element must actually do its work in the "on" case. Example: alertsocket only runs with the extended API (`~/POWER_Const/interface_activated` or a license). Without it, both cases measure nothing.
- **Load that keeps the GPU busy:** a mock CNN that runs the real network and replaces its results gives repeatable load; an old mock that only sleeps leaves the GPU idle and says nothing about GPU load or power. Check what `mock_cnn_enabled` does in the installed code. Scenarios are the JSON files in `Core/Gst/plugins/python/Inference_lib/NN/scenarios/`; pick by object count.
- **Scripts on the device are current:** compare `~/Tools/scripts/power_mode_perf.sh`, `measure_worker_cpu.py` and `parse_perf_report.py` with the repo; copy with `rsync -a` (no `--delete`) if they differ.
- **gst-shark installed:** `gst-inspect-1.0 proctime` and `~/gst-shark/scripts/analizer/gstshark-report.py` exist.
- **Back up** any runtime file you change, never `rm -rf` runtime folders, never commit or push.

## Running a campaign

Use `scripts/campaign.sh` (one new folder on the device per campaign). It:
- swaps the file under test before every run and checks it with `diff`, and puts the installed file back on every exit;
- alternates the cases (on, off, off, on, …) so drift hits both equally;
- calls `power_mode_perf.sh` with a unique `PERF_LABEL` per run (the script refuses to reuse labels);
- adds the element under test to the script's default tracer string (the default filter may not include it);
- sets `SETTINGS_OVERRIDES` (inference verbose, mock scenario).

Defaults that worked: 3 runs per case, 60 s each, 30 s pause. `power_mode_perf.sh` drops the first 15 s. Run it with `nohup … < /dev/null &` so SSH can disconnect.

## What the tracer records mean

The console log of every run (`<label>_console.log`) holds the raw gst-shark records (`GST_DEBUG=GST_TRACER:7`):

`<elapsed> <pid> <thread-id> TRACE GST_TRACER :0:: proctime, element=(string)<name>, time=(string)<duration>;`

- **Thread id** tells which thread logged the record.
- **`proctime` of an element** = time in that element. With `infer-only=True` element records exist **only for N batches**; S batches are invisible, so a timeline from these records alone shows gaps where stage 2 is busy with S batches.
- **`proctime` of a queue** is logged when a batch **leaves** the queue; `time` = how long it waited. Queue records exist for every batch. Entry time = log time − wait.
- Queues are FIFO; `scripts/batches.py` uses that to follow each batch through both stages.
- `queuelevel` records give the fill level of each queue (where the waiting is).
- `framerate` records are per-second counts per pad (`wsstatus_src` = worker fps).

`power_mode_perf.sh` deletes the gst-shark CTF folders after the report; the console logs are the raw data.

## Metric definitions

| Metric | Source |
|---|---|
| Worker fps (batches/s) | `<label>_metrics.json` → `wsstatus_src.framerate_mean_fps` |
| Network runs/s | timestamps of the `Model profiling` lines (needs `inference_verbose`) |
| Element time per batch | `metrics.json` → `<element>.proctime_mean_ms` (N batches only with infer-only) |
| Inference split | `Model profiling` (pre / network / post) and `get_images_from_batch` medians; rest = whole element − parts |
| Stage 2 per batch | `batches.py`: next stage-2 start − this start; exact only when stage 2 never idles |
| Latency | muxer → end of stage 2 per batch (`batches.py`), separately for N and S |
| Power, CPU, GPU | `<label>_worker_cpu.json` (tegrastats after warm-up). VDD_IN = whole Jetson module; VDD_CPU_GPU_CV = CPU + GPU + CV rail |

## Pitfalls seen in practice

- A run can crash at startup (e.g. the IMU fails to open). Repeat it under a new label; do not mix it in.
- Network time can differ between two installs of the "same" software. Do a short sanity run (no tracer) and compare the network median with earlier runs before a campaign.
- The GPU clock follows load: with idle gaps (e.g. a skipped batch every cycle) it drops and each network run gets slower. Record the clocks; do not compare runs with different clock states.
- The tracer adds overhead. Compare traced with traced, untraced with untraced.
- Do not compare temperatures on a full product (ambient and enclosure dominate); compare power.
- `make_timeline.py` reports model vs measured cycle time. More than ~10 % apart means the stage times or the assumptions (pool size, interval, camera rate) do not describe the run; find out why before publishing.
