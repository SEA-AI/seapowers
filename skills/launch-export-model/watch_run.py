"""Watch an export-model run and print one line per stage change.

Usage: uv run -q --with wandb python watch_run.py <entity/project/run_id> [poll_seconds]

Output, one line each:
  start <name> <url> estimate=<min|none> samples=<n>
  stage <ONNX export|TRT compile> elapsed=<min>
  progress <5..95> elapsed=<min>   (TRT compile, every 5% of the estimate; only with one)
  end <finished|failed|crashed|killed> elapsed=<min> artifacts=<type:name,...>

The estimate is the mean runtime of past finished runs that built an engine on the
same compile device (SSH host) for the same network type (dan, ahoy, yolo). No match
means no estimate: compile times are not comparable across devices.
"""

import sys
import time
from datetime import datetime, timezone

import wandb


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


def builds_engine(run) -> bool:
    """Same rule as the job's coerce_trt_bool: only "false" (any case) or False skips TRT."""
    return str(run.config.get("trt", True)).lower() != "false"


def stage(run) -> str:
    if not builds_engine(run):
        return "ONNX export"
    types = {a.type for a in run.logged_artifacts()}
    return "TRT compile" if "onnx-model" in types else "ONNX export"


def main() -> None:
    path, poll = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 30
    api = wandb.Api()
    run = api.run(path)
    total, n = estimate(api, run) if builds_engine(run) else (None, 0)
    eta = f"{total / 60:.0f}" if total else "none"
    print(f"start {run.name} {run.url} estimate={eta} samples={n}", flush=True)
    started = datetime.fromisoformat(run.created_at.replace("Z", "+00:00"))
    last, reported = None, 0
    while True:
        run.load(force=True)  # Api caches runs; without a forced reload the state never changes
        if run.state != "running":
            artifacts = ",".join(f"{a.type}:{a.name}" for a in run.logged_artifacts())
            print(f"end {run.state} elapsed={run.summary.get('_runtime', 0) / 60:.0f} artifacts={artifacts}", flush=True)
            return
        current = stage(run)
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        if current != last:
            print(f"stage {current} elapsed={elapsed:.0f}", flush=True)
            last = current
        if total and current == "TRT compile":
            # 5% slices of the estimate, held at 95% until the run really ends
            pct = min(int(elapsed * 60 / total * 20) * 5, 95)
            while reported < pct:
                reported += 5
                print(f"progress {reported} elapsed={elapsed:.0f}", flush=True)
        time.sleep(poll)


if __name__ == "__main__":
    main()
