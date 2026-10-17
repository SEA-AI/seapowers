"""Watch an export-model run: current stage plus a progress bar against past runtimes.

Usage: uv run -q --with wandb python watch_run.py <entity/project/run_id> [poll_seconds]

The estimate is the mean runtime of past finished runs that built an engine with
the same product, compile device (SSH host), trt_flags and networks. No match means
no estimate: compile times are not comparable across devices.
"""

import sys
import time
from datetime import datetime, timezone

import wandb


def build_key(run) -> tuple:
    """Runs compile in the same time only on the same device with the same networks."""
    host = (run.config.get("ssh_host") or "default").split("@")[-1]
    models = tuple(
        (m.get("type"), tuple(m.get("detection") or []), m.get("horizon"),
         tuple(m.get("imgsz") or []), tuple(m.get("infsz") or []), str(m.get("batch_size")))
        for m in run.config.get("models", []) if isinstance(m, dict)
    )
    return run.config.get("product"), host, run.config.get("trt_flags") or "", models


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
        return f"{elapsed / 60:.0f} min elapsed (no past run on this device with these networks)"
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
