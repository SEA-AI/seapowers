---
name: pipeline-timeline
description: "Measures and explains what a GStreamer element, setting or code change costs in the Core-Backend worker pipeline on a Jetson device (Watchkeeper/Kraken, Sentry, Pod, Brain): worker fps, network runs per second, time per element and per thread, latency per batch, CPU/GPU load and power. Runs interleaved on/off campaigns with Tools/scripts/power_mode_perf.sh and gst-shark, finds which thread sets the pace, and draws a frame-by-frame hover timeline page. Use it whenever someone asks why the worker is slow, which thread is the bottleneck, what an element or plugin change does to fps, latency or watts, wants an A/B performance test on a device, or wants the timeline graph, even if they do not name the scripts."
license: MIT
---

# Pipeline timeline

Measure what one element or change costs in the worker pipeline on a real device, find which thread sets the pace, and show it batch by batch.

The pipeline changes with the code, so this skill does not describe it element by element. Read it from the Core-Backend commit installed on the device; `references/pipeline.md` says where to look and which concepts matter (threads, N/S batches, muxer buffers, Python coupling, how to tell the bottleneck). Read it before interpreting any number. `references/measurement.md` has the device checklist, what the tracer records mean, metric definitions and pitfalls.

## Setup

- Run the scripts from a Core-Backend checkout with `uv run` (`SKILL` = this skill's base directory). They declare their dependencies inline; `make_timeline.py` needs `jinja2`, the others only the standard library.
- Device access over SSH as `power@<device>`. The user stops and starts `worker.service` (needs their sudo).
- gst-shark on the device (`gst-inspect-1.0 proctime`).

## Workflow

**Data already exists** (a campaign folder from earlier): skip to step 4.

1. **Agree on the question and the cases** with the user, in a few words: element or change under test, cases (usually on/off), load (a mock scenario by object count, or the real scene), runs per case and duration. Make the two cases as two versions of one runtime file, so nothing else changes between runs: the smallest edit that turns the work off (an early return, or the element's own switch property), not a pipeline-wide property other elements also read. Show the user the `diff`.
2. **Prepare the device** with the checklist in `references/measurement.md`. Hard rules: back up every runtime file you change, copy with `rsync -a` (no `--delete`), never `rm -rf` runtime folders, never commit or push for test-only changes, do not change the power mode or run `jetson_clocks`, one new folder per campaign. Never type, store or reuse a password; if one is pasted, say it should be rotated.
3. **Run the campaign.** Copy `scripts/campaign.sh` to the device folder, put `<case>.<file>` variants next to it, set the variables at the top, start it with `nohup ./campaign.sh > campaign.log 2>&1 < /dev/null &`, wait with an until-loop on `CAMPAIGN END` in `campaign.log`, check `rc=0` per run and repeat a crashed run under a new label.
4. **Analyse.** Fetch the folder (`rsync -a power@<device>:<folder>/ <local>/`), then:
   ```bash
   uv run $SKILL/scripts/verify.py <local>/pmp <element>   # fps, element time, inference split, queue fill, power per run
   uv run $SKILL/scripts/batches.py <local>/pmp            # per-batch waits, stage times, latency for N and S
   ```
   Compare stage 1 and stage 2 per cycle and check where the queues fill (`references/pipeline.md`).
5. **Build the timeline page.**
   ```bash
   uv run $SKILL/scripts/make_timeline.py --scenario "<label>=<local>/pmp" [--scenario ...] --element <element> \
       --out timeline.html --interval <processing_interval> --pool <buffer pool> --camera-fps <rate> \
       [--eyebrow "<short label>" --title "<title>"]
   ```
   Take interval, pool and camera rate from the installed code and the device. The script prints model vs measured cycle time per case; more than ~10 % apart means the stage times or the assumptions do not describe the run, so find out why before showing it. The page follows the SEA.AI brand (`sea-ai-brand` skill) and is self-contained; publish it as an Artifact if the user wants to share it.
6. **Report.** Lead with the answer, then a small table, then the why. Keep apart worker fps, network runs per second and stream fps; compare per cycle; give N-batch latency (the one carrying detections) and do not average N and S; compare power, not temperature; mark anything inferred rather than measured. If the result could affect a customer, a live system or a safety decision, end with "⚠ Review by a qualified person required before use."

## Example: what the output looks like

From the SEA-1517 alertsocket investigation (Watchkeeper/Kraken, Orin NX 20 W, network every 2nd batch, 3 runs × 60 s per case):

| | 100 obj off | 100 obj on | 20 obj off | 20 obj on |
|---|---|---|---|---|
| Network runs/s | 5.5 | 3.6 | 6.0 | 5.5 |
| Worker fps | 10.5 | 6.9 | 11.5 | 10.4 |
| alertsocket per batch | 0.4 ms | 103 ms | 0.2 ms | 73 ms |
| Stage 2 per batch | ~50 ms | 143 ms | ~15 ms | 91 ms |
| Latency N batch | 313 ms | 500 ms | 167 ms | 343 ms |
| VDD_IN | 12.1 W | 11.4 W | 12.2 W | 12.4 W |

Conclusion in one line: with alertsocket off, inference (100 objects) or the camera (20 objects) sets the pace; with it on, stage 2 does. The timeline page shows the muxer, stage 1 and stage 2 as lanes, one block per batch, with hover details per block. These are the numbers of that one setup; use them to judge whether a new result is plausible, not as expected values for other devices or code.
