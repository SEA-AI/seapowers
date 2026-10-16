---
name: pipeline-timeline
description: "Measure and explain what a GStreamer element, setting or code change costs in the Core-Backend worker pipeline on a Jetson device (Watchkeeper/Kraken, Sentry, Brain), and produce the frame-by-frame hover timeline page. Knows the pipeline threads (muxer, stage 1 inference, stage 2 post-processing, N/S batches, 4 muxer batch buffers, Python GIL coupling) and checks that this still matches the code before testing. Runs interleaved on/off campaigns with Tools/scripts/power_mode_perf.sh and gst-shark, analyses worker fps, network runs/s, per-element time, latency per batch, CPU/GPU load and power. Use it whenever someone wants to know why the worker is slow, which thread is the bottleneck, what alertsocket / an element / a plugin change does to fps, latency or watts, wants an A/B perf test on a device, or wants the timeline graph (again), even if they don't name the script."
license: MIT
---

# Pipeline timeline

Measure the cost of one element or change in the worker pipeline on a real device, find which thread sets the pace, and draw it batch by batch. Built from the SEA-1517 alertsocket investigation (2026-10); its results are the reference for what "normal" looks like.

Read these when you need them:
- `references/pipeline.md`: threads, element order, N/S batches, muxer buffers, Python coupling, how to tell the bottleneck. **Read before interpreting any number.**
- `references/measurement.md`: device checklist, campaign, what each tracer record means, metric definitions, pitfalls.

## Workflow

Run every command from the Core-Backend repo root (the scripts read the code with `git show`). `SKILL` = this skill's base directory, shown when the skill loads; the scripts, references and the HTML template live there.

**Data already exists** (a campaign folder from earlier): do step 1 with `--run-dir`, skip steps 2–4, continue at step 5.

### 1. Check that the pipeline map still holds
The code changes; the map in `references/pipeline.md` is a snapshot. Before planning or running anything:

```bash
python3 $SKILL/scripts/check_pipeline.py --rev <commit> --element <element> --profile <profile> [--run-dir <pmp folder>]
```

- `<commit>`: the Core-Backend commit installed on the device (`~/versions.json`), not your checkout.
- `<profile>`: from the device's `~/POWER_Const/hardwareVersion`, e.g. `Oscar_V10_1024S_Gen_2` → `1024S_Gen_2` (Kraken units are Watchkeeper 1024S Gen 2).
- `--run-dir`: a campaign folder; reports what actually ran (mock, scenario, model, network time, extended API). Devices often carry test patches on top of the commit, so trust the run over the commit for those.
 Every `CHANGED`/`MISSING` line means your understanding is out of date: read the changed code, tell the user what changed and what it means for the test, and update `references/pipeline.md` if the change is permanent. Typical consequences: element moved to another thread, different inference implementation (Python vs C++ changes the coupling), `processing_interval` ≠ 1 (cycle length changes), a different muxer pool size (pass `--pool`), no GPU MockCNN (port develop `7aa03a9ae` or measure with the real scene).

### 2. Agree on the question and the cases
Settle with the user, in a few words: element or change under test, cases (usually on/off), load (100-object stress, 20-object normal, or real scene), runs per case (3) and duration (60 s).

The two cases are two versions of one runtime file, so nothing else changes between runs. Make them from the installed file and show the user the `diff`:
- alertsocket since PR #1107: off = installed file; on = `self._enabled = False` → `True` in `__init__` (nothing in the pipeline sets the property).
- alertsocket before PR #1107: on = installed file (runs whenever the extended API is active); off = first check in `do_transform_ip` replaced by `if True:` so it returns `Gst.FlowReturn.OK` at once.
- Other elements: the smallest change that turns the work off without changing anything else (not a pipeline property that other elements also read).

### 3. Prepare the device
Follow the checklist in `references/measurement.md` §1. Hard rules:
- The user stops `worker.service` (needs their sudo). Never type, store or reuse a password; if one is pasted, say it should be rotated.
- Back up every runtime file you change, copy with `rsync -a` (no `--delete`), never `rm -rf` runtime folders, never commit or push from the device or for test-only changes.
- Do not change the power mode or run `jetson_clocks`.
- New folder per campaign on the device.

### 4. Run the campaign
Copy `scripts/campaign.sh` to the device folder, put `<case>.<file>` variants next to it, adjust the variables at the top, then:

```bash
nohup ./campaign.sh > campaign.log 2>&1 < /dev/null &
```

Wait with an until-loop on `CAMPAIGN END` in `campaign.log` instead of sleeping. Check `rc=0` per run; repeat a crashed run under a new label.

### 5. Analyse
Fetch the folder (`rsync -a power@<device>:<folder>/ <local>/`), then:

```bash
python3 $SKILL/scripts/verify.py <local>/pmp <element>   # fps, element time, inference split, queue fill, power per run
python3 $SKILL/scripts/batches.py <local>/pmp            # per-batch waits, stage times, latency for N and S
```

Find the bottleneck per `references/pipeline.md` §6: compare stage 1 and stage 2 **per cycle** (interval + 1 batches), and check where the queue fill sits.

### 6. Build the timeline page

```bash
python3 $SKILL/scripts/make_timeline.py --scenario "100 objects=<local>/pmp" [--scenario "20 objects=<other>/pmp"] \
    --element <element> --out timeline.html [--pool 4 --interval 1 --camera-fps 12] \
    [--eyebrow "SEA-1517 · Kraken unit · Orin NX 20 W" --title "What alertsocket costs in the worker pipeline"]
```

The page follows the SEA.AI Brand Book (white background, the 7 brand colours, Barlow Semi Condensed, logo top-right, "SEA.AI CONFIDENTIAL" footer). `--eyebrow` becomes the red section label: keep it short and ALL CAPS-friendly. No em dashes in titles or notes.

It prints model vs measured cycle time per case, gap = (model − measured) / measured. A few percent negative is normal, because the model leaves out untraced steps. More than 10 % apart in either direction means the stage times or the assumptions do not describe the run: find out why before showing it. Take `--pool` and `--interval` from the step-1 check. Publish the page as an Artifact if the user wants to share it (it is self-contained, theme-aware, hover works on touch).

### 7. Report
Lead with the answer. Then a small table, then the why. Keep these straight, they caused most of the confusion last time:
- **Worker fps** (batches/s, max = camera fps 12) vs **network runs/s** (processing fps, max 6 with interval 1) vs **stream fps** (camera rate 12; gst-shark reads ~13).
- An element in stage 2 runs on **every** batch; inference does real work only on N. Compare per cycle.
- Latency: give N-batch latency (the one carrying detections); do not average N and S.
- Two threads are "parallel" across batches, never within one batch; on master both are Python, so they also slow each other.
- Power: VDD_IN = whole Jetson module. Compare power, not temperature, on a full product.
- Mark anything inferred rather than measured (e.g. "frames are repeated in the stream").
- If the output could affect a customer, a live system or a safety decision, end with "⚠ Review by a qualified person required before use."

## Reference result (SEA-1517, Watchkeeper/Kraken, Orin NX 20 W, package 4.4-9)

| | 100 obj off | 100 obj on | 20 obj off | 20 obj on |
|---|---|---|---|---|
| Network runs/s (max 6) | 5.5 | 3.6 | 6.0 | 5.5 |
| Worker fps | 10.5 | 6.9 | 11.5 | 10.4 |
| alertsocket per batch | 0.4 ms | 103 ms | 0.2 ms | 73 ms |
| Stage 2 per batch | ~50 ms | 143 ms | ~15 ms | 91 ms |
| Latency N batch | 313 ms | 500 ms | 167 ms | 343 ms |
| VDD_IN | 12.1 W | 11.4 W | 12.2 W | 12.4 W |

Bottleneck: off = inference (100 obj) or camera (20 obj); on = stage 2. These are the numbers of that one campaign (raw data in `~/sea1517_v2/` and `~/sea1517_v3/` on the Kraken test unit). A rerun of the same setup should land within about 5 %; a bigger difference means something changed (software, device state, load), so find out what before comparing elements.
