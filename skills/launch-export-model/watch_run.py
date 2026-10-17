"""Watch an export-model run: current stage plus a progress bar against past runtimes.

Usage: uv run -q --with wandb python watch_run.py <entity/project/run_id> [poll_seconds]

The estimate is the mean runtime of past finished runs that built an engine on the
same compile device (SSH host) for the same network type (dan, ahoy, yolo). No match
means no estimate: compile times are not comparable across devices.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import wandb

# Read by the export-progress Claude Code mod to draw a live bar above the prompt.
STATUS_FILE = Path.home() / ".claude" / "export-progress.json"


def build_key(run) -> tuple[str, str]:
    """Compile time depends on the device and the network type, not on the weights."""
    models = [m for m in run.config.get("models", []) if isinstance(m, dict)]
    net = "dan" if len(models) > 1 else "ahoy" if any(m.get("horizon") for m in models) else "yolo"
    host = (run.config.get("ssh_host") or f"default-{run.config.get('product')}").split("@")[-1]
    return host, net


def estimate(api, run) -> tuple[float | None, int]:
    key = build_key(run)
    samples = [
        past.summary["_runtime"]
        for past in api.runs(f"{run.entity}/{run.project}", filters={"state": "finished"}, per_page=100)
        if past.id != run.id
        and past.summary.get("_runtime")
        and build_key(past) == key
        and any(a.type == "trt-engine" for a in past.logged_artifacts())
    ]
    # ponytail: plain mean, filter outliers if a stuck run ever skews it
    return (sum(samples) / len(samples), len(samples)) if samples else (None, 0)


def stage(run) -> str:
    if run.state != "running":
        return run.state
    types = {a.type for a in run.logged_artifacts()}
    return "TRT compile" if "onnx-model" in types else "ONNX export"


def bar(elapsed: float, total: float | None, width: int = 20) -> str:
    if not total:
        return f"{elapsed / 60:.0f} min elapsed (no past run of this network type on this device)"
    frac = min(elapsed / total, 1.0 if elapsed == total else 0.99)
    filled = int(frac * width)
    return f"[{'#' * filled}{'-' * (width - filled)}] {frac:.0%} · {elapsed / 60:.0f}/{total / 60:.0f} min"


def main() -> None:
    path, poll = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 30
    api = wandb.Api()
    run = api.run(path)
    total, n = estimate(api, run)
    print(f"{run.name} {run.url} · estimate from {n} past run(s)", flush=True)
    started = datetime.fromisoformat(run.created_at.replace("Z", "+00:00"))
    while True:
        run = api.run(path)
        current = stage(run)
        elapsed = run.summary.get("_runtime") if run.state != "running" else (datetime.now(timezone.utc) - started).total_seconds()
        print(f"{current:<12} {bar(elapsed, elapsed if run.state == 'finished' else total)}", flush=True)
        STATUS_FILE.write_text(json.dumps({
            "name": run.name, "url": run.url, "stage": current, "state": run.state,
            "elapsed_min": elapsed / 60, "total_min": total / 60 if total else None,
            "updated_ms": int(time.time() * 1000),
        }))
        if run.state != "running":
            print("artifacts:", [f"{a.type}:{a.name}" for a in run.logged_artifacts()], flush=True)
            return
        time.sleep(poll)


if __name__ == "__main__":
    main()
