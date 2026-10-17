---
name: launch-export-model
description: Launch the ml-ops export_model W&B job (.pt → .onnx → TensorRT .engine) from a plain-language request instead of the W&B Launch UI. Use when the user wants to export, convert, or compile a model to ONNX or TensorRT, build a DAN, or launch export-model-job.
---

# Launch export_model

Turn the user's request into a run config, show it, and on approval submit it with `wandb launch`.

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

Read `$JOB/config_schema.py` and `$JOB/platforms.yaml` for the current fields and product defaults. Then ask only for what the request leaves open:

- **product**: a key of `platforms.yaml` (e.g. `watchkeeper`, `sentry`).
- **models**: one entry per camera. One model = single ONNX, two = DAN. Per model:
  - `name`, `type` (`thermal` | `rgb`)
  - `detection`: list of W&B artifact refs (`collection:version`). Two+ refs = ensemble.
  - `horizon`: ref, or omit for plain YOLO (sets AHOY).
  - `imgsz`, `infsz`, `batch_size`: omit to use the product default. `imgsz`/`infsz` are `["H", "W"]` strings.
- **trt**: `false` stops after ONNX.
- **trt_flags**: full `trtexec` flag string; omit for the product default. Show the default from `platforms.yaml` when asking.
- **ssh_host**, **fname**, **yolov5_branch**, **export.fuse/half**: omit unless the user asks.
- **queue**: W&B launch queue name. Ask; there is no default.

Omit every key the user did not set so the job applies `platforms.yaml` defaults.

## 2. Write and validate

Write the config to a temp file (e.g. `$TMPDIR/export-<product>-<yyyymmdd-HHMM>.json`), with the run config under `overrides.run_config` as `wandb launch` expects:

```json
{
  "overrides": {
    "run_config": {
      "product": "watchkeeper",
      "models": [
        {"name": "thermal", "type": "thermal", "detection": ["YOLOv5n-IR:latest"]},
        {"name": "rgb", "type": "rgb", "detection": ["YOLOv5n-RGB:latest"], "infsz": ["576", "960"]}
      ],
      "trt_flags": "--inputIOFormats=uint8:chw --memPoolSize=workspace:8G --fp16"
    }
  }
}
```

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

Show the user the resolved table (model, type, detection, horizon, imgsz, infsz, batch_size, trt_flags, queue). Launch only after an explicit yes:

```bash
wandb launch -j sea-ai/export-model/export-model-job:latest -e sea-ai -p export-model \
  --queue <queue> --config <config.json>
```

Report the queued run link from the output.
