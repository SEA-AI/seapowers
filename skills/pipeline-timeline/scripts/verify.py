#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Recompute the run metrics (fps, element times, inference split, queue fill, power) from power_mode_perf.sh output.

Usage: uv run verify.py <pmp output dir> <element>   (expects <case>_<n>_{console.log,metrics.json,worker_cpu.json})
"""

import json
import re
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit("usage: verify.py <pmp folder> <element>")
D, ELEMENT = Path(sys.argv[1]), sys.argv[2]
CASES = {}
for p in sorted(D.glob("*_metrics.json")):
    run = p.name[: -len("_metrics.json")]
    CASES.setdefault(run.rsplit("_", 1)[0], []).append(run)
if not CASES:
    sys.exit(f"no *_metrics.json found in {D}")
for runs in CASES.values():
    for r in runs:
        for suffix in ("console.log", "worker_cpu.json"):
            if not (D / f"{r}_{suffix}").exists():
                sys.exit(f"missing {D / f'{r}_{suffix}'}: is the run complete?")
SKIP = 10  # first inferred batches of each run, warm-up

PROFILE = re.compile(
    r"Model profiling:\s*([\d.]+) ms - preprocess,\s*([\d.]+) ms - inference,\s*([\d.]+) ms - postprocess"
)
LOG_TS = re.compile(
    r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) .*Model profiling", re.MULTILINE
)
QUEUE = re.compile(
    r"queuelevel, queue=\(string\)(queue_processing|queue_inference), .*?size_buffers=\(uint\)(\d+)"
)


def run_numbers(r):
    text = (D / f"{r}_console.log").read_text(errors="replace")
    met = json.loads((D / f"{r}_metrics.json").read_text())["metrics"]
    cpu = json.loads((D / f"{r}_worker_cpu.json").read_text())["metrics"]

    # gst-shark (proctime runs with infer-only=True: only batches the network ran on)
    proc = lambda e: met[e]["proctime_mean_ms"]["value"]
    fps = lambda p: met[p]["framerate_mean_fps"]["value"]

    # inference log (inference_verbose=true): one "Model profiling" line per network run
    prof = [tuple(map(float, m)) for m in PROFILE.findall(text)][SKIP:]
    fetch = [
        float(x) for x in re.findall(r"\[\s*([\d.]+) ms\] get_images_from_batch", text)
    ][SKIP:]
    elem = [
        x
        for x in (
            float(x) for x in re.findall(r"\[\s*([\d.]+) ms\] do_transform_ip", text)
        )
        if x > 10
    ][SKIP:]
    ts = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S,%f") for x in LOG_TS.findall(text)][
        SKIP:
    ]

    queues = {}
    for name, n in QUEUE.findall(text):
        queues.setdefault(name, []).append(int(n))
    qmean = {
        k: st.mean(v[len(v) // 4 :]) for k, v in queues.items()
    }  # skip first quarter (startup)

    return {
        "batches_per_s (wsstatus out, gst-shark framerate)": fps("wsstatus_src"),
        "network_runs_per_s (log timestamps)": (len(ts) - 1)
        / (ts[-1] - ts[0]).total_seconds(),
        "inference element ms (gst-shark, inferred batches)": proc("inference"),
        f"{ELEMENT} ms (gst-shark, inferred batches)": proc(ELEMENT),
        "inference element ms (log, median)": st.median(elem),
        "  image copy to CPU ms (log, median)": st.median(fetch),
        "  preprocess ms (log, median)": st.median(p[0] for p in prof),
        "  network ms (log, median)": st.median(p[1] for p in prof),
        "  postprocess ms (log, median)": st.median(p[2] for p in prof),
        "queue_processing fill (buffers, mean)": qmean.get("queue_processing"),
        "queue_inference fill (buffers, mean)": qmean.get("queue_inference"),
        "VDD_IN W": cpu["power_in_mw"]["value"] / 1000,
        "VDD_CPU_GPU_CV W": cpu["power_compute_mw"]["value"] / 1000,
        "CPU %": cpu["cpu_system_tegrastats_pct"]["value"],
        "GPU %": cpu["gpu_pct"]["value"],
        "RTSP RGB1 fps": fps("encodingbin_rtsp_RGB1_src"),
        "nvpmodel": json.loads((D / f"{r}_worker_cpu.json").read_text())["nvpmodel"],
    }


try:
    rows = {r: run_numbers(r) for runs in CASES.values() for r in runs}
except (KeyError, ValueError, ZeroDivisionError, st.StatisticsError) as e:
    sys.exit(
        f"a run lacks data ({type(e).__name__}: {e}); check that {ELEMENT} was traced and inference_verbose was on"
    )
keys = list(next(iter(rows.values())).keys())
order = [r for runs in CASES.values() for r in runs]
print(
    "| metric | "
    + " | ".join(order)
    + " | "
    + " | ".join(f"{c} mean" for c in CASES)
    + " |"
)
print("|---" * (len(order) + len(CASES) + 1) + "|")
for k in keys:
    vals = [rows[r][k] for r in order]
    if isinstance(vals[0], str):
        print(f"| {k} | " + " | ".join(vals) + " |" + " |" * len(CASES))
        continue
    m = {c: [rows[r][k] for r in runs] for c, runs in CASES.items()}
    m = {c: st.mean(v) if None not in v else None for c, v in m.items()}
    num = lambda v: "–" if v is None else f"{v:.2f}"
    print(
        f"| {k} | "
        + " | ".join(num(v) for v in vals)
        + " | "
        + " | ".join(num(m[c]) for c in CASES)
        + " |"
    )
