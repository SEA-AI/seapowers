"""Watch an export-model run: current stage plus a progress bar against past runtimes.

Usage: uv run -q --with wandb python watch_run.py <entity/project/run_id> [poll_seconds]

The estimate is the mean runtime of past finished runs that produced an engine
for the same product and cameras, so it improves with every run.
"""

import sys
import time
from datetime import datetime, timezone

import wandb


def cameras(run) -> tuple:
    return tuple(sorted(m.get("type", "") for m in run.config.get("models", []) if isinstance(m, dict)))


def estimate(api, run) -> tuple[float | None, int]:
    product, cams = run.config.get("product"), cameras(run)
    same_product, same_cams = [], []
    for past in api.runs(f"{run.entity}/{run.project}", filters={"state": "finished"}, per_page=100):
        if past.id == run.id or past.config.get("product") != product:
            continue
        if not any(a.type == "trt-engine" for a in past.logged_artifacts()):
            continue
        runtime = past.summary.get("_runtime")
        if runtime:
            same_product.append(runtime)
            if cameras(past) == cams:
                same_cams.append(runtime)
    # ponytail: plain mean, filter outliers if a stuck run ever skews it
    samples = same_cams or same_product
    return (sum(samples) / len(samples), len(samples)) if samples else (None, 0)


def stage(run) -> str:
    if run.state != "running":
        return run.state
    types = {a.type for a in run.logged_artifacts()}
    return "TRT compile" if "onnx-model" in types else "ONNX export"


def bar(elapsed: float, total: float | None, width: int = 20) -> str:
    if not total:
        return f"{elapsed / 60:.0f} min elapsed (no past runs to estimate from)"
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
        if run.state != "running":
            print("artifacts:", [f"{a.type}:{a.name}" for a in run.logged_artifacts()], flush=True)
            return
        time.sleep(poll)


if __name__ == "__main__":
    main()
