---
name: launch-export-model
description: Launch the ml-ops export_model W&B job (.pt → .onnx → TensorRT .engine) from a plain-language request instead of the W&B Launch UI. Use when the user wants to export, convert, or compile a model to ONNX or TensorRT, build a DAN, or launch the export-model job.
---

# Launch export_model

Turn the user's request into a run config, show it, and on approval launch it and follow it to the end.

The job (`jobs/export_model/` in `SEA-AI/ml-ops`) is the single source of truth: its schema, product defaults and README define every field, product, camera and default. Read them on every run instead of relying on anything remembered here.

## Progress bar

If the `plan_progress` tool is missing, offer the `plan-progress` plugin first, before any other question, and say it is optional: the export works the same without it. It installs from the `zycck/claude-mods` marketplace (`plan-progress@zycck-mods`); guide the user through `/plugin` in the terminal or **+** → **Plugins** in the desktop app. Then carry on either way.

If the `plan_progress` tool is available, create one bar per export as soon as the skill starts, with `id` `export-<run name>` and the run name as `title`:

| Stage | Steps |
|---|---|
| Setup | Check tools · Read job · Build config · Validate config |
| Launch | Confirm with user · Queue run · Agent picks up |
| ONNX | Export models · Compose DAN (single model: `skipped`) |
| TensorRT | With `trt: false`: one step `Compile` with status `skipped`. With an estimate of N min: 20 steps `Compile 5%` … `Compile 100%` (each about N/20 min), so the compile, which takes nearly all the time, fills most of the bar. Without one: a single `Compile` step |
| Cleanup | Report artifacts · Stop watcher |

Move it with `{id, next: true}` as each step finishes. While the bar is up, it is the progress report: write no chat text for a step or a `progress` line, only for a failure, a question, or the final result. Before asking the user anything, set `state: "needs_input"`. On a failure, send `failed` with the cause as `note`. After cleanup, send `state: "done"`. Without the tool, report each step in one short chat line instead.

## 0. Tools and the job

Make sure `gh` and `wandb` are installed and logged in (`gh auth status`; `wandb.Api().default_entity` answers `sea-ai`). Otherwise guide the user to install or log in for their OS, from what you find in the tools' own docs. `SEA-AI/ml-ops` is private, and the W&B account must belong to the `sea-ai` entity.

Fetch the job's definition from the branch the run will use (default `develop`) into a temp folder `$JOB`:

```bash
JOB=$(mktemp -d)
for f in config_schema.py platforms.yaml README.md; do
  gh api "repos/SEA-AI/ml-ops/contents/jobs/export_model/$f?ref=develop" \
    -H "Accept: application/vnd.github.raw" > "$JOB/$f"
done
```

Read all three before asking anything: `config_schema.py` (fields, descriptions, validation), `platforms.yaml` (products, cameras, defaults), `README.md` (concepts, example configs).

## 1. Collect inputs

Ask only what the request leaves open, in this order:

1. **Product**: one of the products in `platforms.yaml`, or another device.
2. **Defaults**: for a known product, show its `platforms.yaml` values as one table and let the user accept or change each. For another device there are no defaults, so ask for every value the schema needs.
3. **Models**: cameras and weights per camera. For "latest", look up the registry and the newest training runs, and say which version you picked and why. Use the README example configs as the template, including their model names: the job images built before the DAN prefix came from the camera type still take the prefix from the model name.
4. **Queue**: suggest the one recent `export-model` runs used (`_wandb.launch_queue_name` in their config) and confirm.

## 2. Write and validate

Write a draft to a temp file with the run config under `overrides.run_config`, as `wandb launch` expects. Top-level `name` becomes the W&B run name: `<arch>-<product>`, with `arch` = `dan` for two models, else `yolo` or `ahoy`; then per model `-<model name>-<imgsz WxH>`, plus `-inf<infsz WxH>` when `infsz` differs from `imgsz`.

Validate the draft with the job's own schema and expand it into the **full config**: every field the job reads, with the `platforms.yaml` defaults filled in. The full config replaces the draft and is what gets launched, so the run uses exactly what the user approved, even if `platforms.yaml` changes later:

```bash
cd "$JOB" && uv run -q --with pydantic --with pyyaml python -c "
import json, sys
from config_schema import ExportJobConfig
path = sys.argv[1]
launch = json.load(open(path))
c = ExportJobConfig.model_validate(launch['overrides']['run_config'])
platform = c.platforms()[c.product.value]
full = c.model_dump(mode='json')
full['models'] = [m.model_dump(mode='json') for m in c.resolved_models()]
for key in ('trt_flags', 'ssh_host'):
    full[key] = full.get(key) or platform[key]
launch['overrides']['run_config'] = full
json.dump(launch, open(path, 'w'), indent=2)
print(json.dumps(launch, indent=2))
" <config.json>
```

Fix and re-run on a validation error. Mention product-level settings that are not part of the config (such as `trt7_compatible`) next to the JSON.

## 3. Confirm, then launch

Show the run name, a table of the resolved values per model, and the **full** launch JSON from step 2 exactly as it will be sent, never a shortened draft: pretty-printed (`indent=2`), in a `json` code block in the chat message. Never put the JSON inside a question dialog, which strips the indentation; ask the yes/no question separately, at the end of the message. Show the JSON again with every launch question, even when nothing changed. Launch only after an explicit yes.

## 4. Launch and watch

Launch and follow the run with the bundled `watch_run.py` (`--help` lists its modes and output lines), run with the `Monitor` tool, re-armed when it expires; without `Monitor`, a background command you read:

```bash
uv run -q --with wandb python "<this skill's folder>/watch_run.py" submit <config.json> --queue <queue>
```

`submit` follows the run created from this queue item, never the project's newest run, since another export may start at the same time. To re-arm after an expiry, watch the run path instead. Each output line moves the bar:

- `queued <id>`: `Queue run` done, `Agent picks up` active.
- `start <name> <url> estimate=<min|none> ...`: `Agent picks up` done; give the user the W&B run link. With an estimate, resend the stages with the 20 `Compile n%` steps.
- `stage ONNX export`: `Export models` active. `stage TRT compile`: ONNX done, first compile step active.
- `progress <n>`: `next` once per line. It holds at 95% until the run ends.
- `end finished ...`: all compile steps done, then Cleanup. `end failed|crashed|killed`: `failed` on the active step.

If the run fails, read the tail of its `output.log` and report the cause. SSH errors (unreachable host, authentication failed) need a fix on the launch agent's SSH setup, not in the config.

## 5. After a release build: link the weights in the registry

When the user says an engine goes to the devices (not for test exports), offer once to link its detection weights into the W&B model registry, so a collection's `latest` is what the shipped engine contains:

- List the collections of the `model` registry and suggest, per camera, the one that matches the config's product and camera. The user can pick another or name a new one.
- Link only a camera with exactly one `detection` ref; an ensemble or horizon weights cannot be represented by one `latest`. The engine artifact's metadata stays the complete record of the release.
- Link, do not copy (`Artifact.link`), and only after an explicit yes, since `latest` moves for everyone who loads it. Check that the new version's digest equals the source's, and cite the registry version together with the engine artifact wherever the engine is documented.
