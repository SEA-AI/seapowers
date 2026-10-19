---
name: launch-export-model
description: Launch the ml-ops export_model W&B job (.pt → .onnx → TensorRT .engine) from a plain-language request instead of the W&B Launch UI. Use when the user wants to export, convert, or compile a model to ONNX or TensorRT, build a DAN, or launch the export-model job.
---

# Launch export_model

Turn the user's request into a run config, show it, and on approval submit it with `wandb launch`.

## Context

The job runs three steps: export each model to ONNX, merge two cameras into one DAN ONNX if two models are given, then compile a TensorRT engine over SSH on the target device.

- **YOLO vs AHOY**: `detection` only = object detection (YOLO). Adding `horizon` weights = object + horizon detection (AHOY).
- **DAN** (Day And Night): thermal + RGB in one ONNX, one inference call. Only for dual-camera products; single-camera products export one model.
- **`imgsz` vs `infsz`**: `imgsz` is the ONNX input, the camera frame size. `infsz` is the network size; when it differs, a resize + pad is baked into the graph and boxes are scaled back to `imgsz`. Leave `infsz` empty to run at `imgsz`.
- **Weight refs**: W&B registry `Collection:version` or run artifact `entity/project/artifact:version`.
- **`trt_flags`**: `trtexec` syntax depends on the device's TensorRT version (e.g. `--memPoolSize=workspace:8G` on TRT 10+, `--workspace=<MB>` on older). Start from the product default in `platforms.yaml` and change only what the user asks for.
- **Engines are hardware-specific**: they only run on the GPU they were built on, so the SSH host must be the target device type.

## Progress bar

If the `plan_progress` tool is missing, offer the `plan-progress` plugin first, before any other question, and say it is optional: the export works the same without it. Then carry on either way:

- Terminal: `/plugin marketplace add zycck/claude-mods`, then `/plugin install plan-progress@zycck-mods` (two separate commands).
- Desktop app: **+** next to the prompt → **Plugins** → **Add marketplace** `zycck/claude-mods` → add `plan-progress`.
- It is active right after install; no restart or hot reload. The animated (twinkling) bar is on by default; if it looks static, turn `twinkle` on in `/plan-progress-settings`.

If the `plan_progress` tool is available, create one bar per export as soon as the skill starts, with `id` `export-<run name>` and the run name as `title`:

| Stage | Steps |
|---|---|
| Setup | Check gh, wandb · Fetch schema · Build config · Validate config |
| Launch | Confirm with user · Queue run · Agent picks up |
| ONNX | Export models · Compose DAN (single model: `skipped`) |
| TensorRT | With `trt: false`: one step `Compile` with status `skipped`. With an estimate of N min: 20 steps `Compile 5%` … `Compile 100%` (each about N/20 min), so the compile, which takes nearly all the time, fills most of the bar. Without one: a single `Compile` step |
| Cleanup | Report artifacts · Stop watcher |

Move it with `{id, next: true}` as each step finishes. While the bar is up, it is the progress report: write no chat text for a step or a `progress` line, only for a failure, a question, or the final result. Before asking the user anything, set `state: "needs_input"`. On a failure, send `failed` with the cause as `note`. After cleanup, send `state: "done"`. Without the tool, report each step in one short chat line instead.

## 0. Find the job

First run `gh auth status`. If `gh` is missing, stop and propose an install for the user's OS, then `gh auth login`:

- macOS: `brew install gh`
- Ubuntu/Debian: `sudo apt install gh` (or the official apt repo in https://github.com/cli/cli/blob/trunk/docs/install_linux.md for a current version)
- Windows: `winget install --id GitHub.cli`

If `gh` is installed but not logged in, ask the user to run `gh auth login`; `SEA-AI/ml-ops` is private.

Then check W&B the same way:

```bash
wandb --version
uv run -q --with wandb python -c "import wandb; print(wandb.Api().default_entity)"
```

If `wandb` is missing, propose `uv tool install wandb` (or `pip install wandb`). If the second command fails, ask the user to run `wandb login` with their key from https://wandb.ai/authorize. The account must be a member of the `sea-ai` entity.

The job lives in `jobs/export_model/` of `SEA-AI/ml-ops`. Fetch its config files from `develop` into a temp folder; below, `$JOB` is that folder:

```bash
JOB=$(mktemp -d)
for f in config_schema.py platforms.yaml; do
  gh api "repos/SEA-AI/ml-ops/contents/jobs/export_model/$f?ref=develop" \
    -H "Accept: application/vnd.github.raw" > "$JOB/$f"
done
```

## 1. Collect inputs

Read `$JOB/config_schema.py` and `$JOB/platforms.yaml`. Skip any question the request already answers. Ask in this order:

1. **Product**: Sentry, Watchkeeper, or another device.
2. **Defaults**, depending on the answer:
   - **Sentry or Watchkeeper**: show that product's defaults from `platforms.yaml` as one table and ask the user to accept or change each value: compile device (`ssh_host`), `trt_flags`, and per camera `imgsz`, `infsz` (empty = same as `imgsz`) and `batch_size`.
   - **Another device**: there are no defaults, so ask for each value: `ssh_host` (`user@host` if it needs a user), `trt_flags`, and per camera `imgsz`, `infsz` and `batch_size`. Also ask whether its TensorRT is 7 (older Jetsons) or 8+; the config has no field for this, so pick the product whose `trt7_compatible` matches (`sentry` = TRT 7, `watchkeeper` = TRT 8+) and override everything else.
3. **Inputs**: which cameras (`thermal`, `rgb`, or both = DAN) and per camera. Model `name` is `ir` for the thermal camera and `rgb` for the RGB camera, with thermal listed first: Core-Backend finds DAN inputs by the `ir_`/`rgb_` prefixes, and older job images take the prefix from `name`.
   - `detection`: W&B artifact refs (`collection:version` or `entity/project/artifact:version`). Two+ refs = ensemble. For "latest", check the registry and the newest training runs, and show which version you picked and why.
   - `horizon`: ref for AHOY, or none for plain YOLO.
4. **Queue**: suggest the one recent `export-model` runs used (`_wandb.launch_queue_name` in their config) and confirm.

`trt: false` stops after ONNX. `fname`, `yolov5_branch` and `export.fuse/half` stay out unless the user asks. In the config, set only the values that differ from the product defaults, so the job applies `platforms.yaml` for the rest.

## 2. Write and validate

Write the config to a temp file (e.g. `$TMPDIR/export-<product>-<yyyymmdd-HHMM>.json`), with the run config under `overrides.run_config` as `wandb launch` expects. Top-level `name` becomes the W&B run name:

```json
{
  "name": "dan-watchkeeper-ir-1312x640-rgb-1920x576-inf960x576",
  "overrides": {
    "run_config": {
      "product": "watchkeeper",
      "models": [
        {"name": "ir", "type": "thermal", "detection": ["YOLOv5n-IR:latest"]},
        {"name": "rgb", "type": "rgb", "detection": ["YOLOv5n-RGB:latest"], "infsz": ["576", "960"]}
      ],
      "trt_flags": "--inputIOFormats=uint8:chw --memPoolSize=workspace:8G --fp16"
    }
  }
}
```

Build `name` from the resolved values (step below prints them), sizes as `WxH`:

- `<arch>-<product>`, with `arch` = `dan` for two models, else `yolo` or `ahoy` (horizon set).
- Then per model: `-<camera>-<imgsz WxH>`, with `ir` for thermal and `rgb` for rgb. Add `-inf<infsz WxH>` when `infsz` differs from `imgsz`.
- Example: `dan-sentry-ir-640x512-rgb-1280x960`, `ahoy-watchkeeper-rgb-3600x1080-inf1920x576`.

Validate it against the schema and print the resolved per-model values:

```bash
cd "$JOB" && uv run --with pydantic --with pyyaml python -c "
import json, sys
from config_schema import ExportJobConfig
c = ExportJobConfig.model_validate(json.load(open(sys.argv[1]))['overrides']['run_config'])
for m in c.resolved_models(): print(m.model_dump(mode='json'))
print('trt:', c.trt, '| trt_flags:', c.trt_flags or c.platforms()[c.product.value]['trt_flags'])
" <config.json>
```

Fix and re-run on a validation error.

## 3. Confirm, then launch

Show the user the run name, the resolved table (model, type, detection, horizon, imgsz, infsz, batch_size, trt_flags, ssh_host, queue) and the full launch JSON exactly as it will be sent: pretty-printed (`json.dumps(..., indent=2)`, one key per line, nested lists and objects expanded), in a `json` code block in the chat message. Never put the JSON inside a question dialog (`AskUserQuestion`), which strips the indentation; ask the yes/no question separately. Show the JSON again in the same message as every launch question, even when nothing changed since it was last shown, so the yes always answers a JSON on screen. Launch only after an explicit yes:

```bash
wandb launch -j sea-ai/export-model/export-model:latest -e sea-ai -p export-model \
  --queue <queue> --config <config.json>
```

Report the queued run link from the output.

## 4. Watch progress

`wandb launch` only queues the run. Find it as the newest run in `sea-ai/export-model` once an agent picks it up (step `Agent picks up`), give the W&B run link (its Logs tab shows the live console), then run the bundled watcher with the `Monitor` tool (re-armed when it expires; without `Monitor`, a background command you read):

```bash
uv run -q --with wandb python "<this skill's folder>/watch_run.py" sea-ai/export-model/<run_id>
```

It prints one line per stage change, and each line moves the bar:

- `start ... estimate=<min|none>`: with an estimate, resend the stages with the 20 `Compile n%` steps.
- `stage ONNX export`: `Export models` active. `stage TRT compile`: ONNX done, first compile step active.
- `progress <n>`: `next` once per line (one per 5%). It stops at 95% until the run ends.
- `end finished ...`: all compile steps done, then the Cleanup steps. `end failed|crashed|killed`: `failed` on the active step.

The estimate is the mean runtime of past finished runs on the same compile device (SSH host) for the same network type (`dan`, `ahoy`, `yolo`). Other devices never count: compile times differ across Jetson models. W&B keeps every run, so the estimate sharpens with each export; nothing is stored locally. Export takes about a minute; nearly all the time is TRT compile.

If the run fails, read the tail of its `output.log` and report the cause. SSH errors (unreachable host, authentication failed) need a fix on the launch agent's SSH setup, not in the config. A host that needs a specific user goes in as `user@host`.
