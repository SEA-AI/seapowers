#!/usr/bin/env python3
"""Build the frame-by-frame timeline page (hover per batch) from power_mode_perf.sh campaign output.

Usage:
    python3 make_timeline.py --scenario "100 objects=/path/to/pmp" [--scenario "20 objects=/path/to/pmp"] \
        --element alertsocket --out timeline.html [--cases off,on] [--interval 1] [--pool 4] [--camera-fps 12]

Each pmp folder holds <case>_<n>_console.log / _metrics.json / _worker_cpu.json (one campaign).
Prints the model-vs-measured check per case; a gap above 10 % means the stage times or the pipeline
assumptions (pool, interval, camera fps) do not describe the run, so do not publish before checking.
Only the Python standard library is needed.
"""

import argparse
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from batches import batches  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*m")
REC = re.compile(r"^(\d+):(\d\d):(\d\d\.\d+)\s+\d+\s+(0x[0-9a-f]+)\s+TRACE\s+GST_TRACER :0:: (\w+), (?:element|queue)=\(string\)(\w+), "
                 r"(?:time=\(string\)(\d+):(\d\d):(\d\d\.\d+)|.*?size_buffers=\(uint\)(\d+))")
PROFILE = re.compile(r"Model profiling:\s*([\d.]+) ms - preprocess,\s*([\d.]+) ms - inference,\s*([\d.]+) ms - postprocess")
SKIP = 10


def sec(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


def med(xs, default=None):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else default


def run_raw(path):
    """Verbose split, wsstatus spans in stage 2, queue fill for one console log."""
    text = path.read_text(errors="replace")
    prof = [tuple(map(float, m)) for m in PROFILE.findall(text)][SKIP:]
    fetch = [float(x) for x in re.findall(r"\[\s*([\d.]+) ms\] get_images_from_batch", text)][SKIP:]
    elem = [x for x in (float(x) for x in re.findall(r"\[\s*([\d.]+) ms\] do_transform_ip", text)) if x > 10][SKIP:]
    pops, ws, qi_lvl = [], [], []
    for line in text.splitlines():
        m = REC.match(ANSI.sub("", line))
        if not m:
            continue
        t = sec(*m.group(1, 2, 3))
        kind, name = m.group(5), m.group(6)
        if kind == "proctime" and name == "queue_inference":
            pops.append(t)
        elif kind == "proctime" and name == "wsstatus":
            ws.append(t)
        elif kind == "queuelevel" and name == "queue_inference":
            qi_lvl.append(int(m.group(10)))
    pops.sort()
    ws.sort()
    spans = []
    for a, b in zip(pops, pops[1:]):
        w = [x for x in ws if a < x <= b]
        if w:
            spans.append(w[0] - a)
    return {
        "pre": med([p[0] for p in prof]), "net": med([p[1] for p in prof]), "post": med([p[2] for p in prof]),
        "copy": med(fetch), "element": med(elem), "runs_ts": len(prof),
        "ws_span": med(spans[len(spans) // 5:]), "qi_fill": st.mean(qi_lvl[len(qi_lvl) // 4:]) if qi_lvl else 0.0,
        "net_rate": network_rate(text),
    }


def network_rate(text):
    from datetime import datetime
    ts = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S,%f") for x in
          re.findall(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) .*Model profiling", text, re.M)][SKIP:]
    return (len(ts) - 1) / (ts[-1] - ts[0]).total_seconds() if len(ts) > 2 else None


def summarize_case(d, case, element):
    runs = sorted(p.name[: -len("_console.log")] for p in d.glob(f"{case}_*_console.log"))
    if not runs:
        raise SystemExit(f"no runs for case '{case}' in {d}")
    raw = [run_raw(d / f"{r}_console.log") for r in runs]
    met = [json.loads((d / f"{r}_metrics.json").read_text())["metrics"] for r in runs if (d / f"{r}_metrics.json").exists()]
    cpu = [json.loads((d / f"{r}_worker_cpu.json").read_text())["metrics"] for r in runs if (d / f"{r}_worker_cpu.json").exists()]
    bs = [b for r in runs for b in batches(d / f"{r}_console.log")]
    N = [b for b in bs if b["kind"] == "N"]
    S = [b for b in bs if b["kind"] == "S"]
    mean = lambda xs: st.mean([x for x in xs if x is not None]) if any(x is not None for x in xs) else None
    g = lambda m, k, f: m.get(k, {}).get(f, {}).get("value")
    out = {
        "runs": runs,
        "batches_per_s": mean([g(m, "wsstatus_src", "framerate_mean_fps") for m in met]),
        "network_runs_per_s": mean([r["net_rate"] for r in raw]),
        "inference_ms": mean([g(m, "inference", "proctime_mean_ms") for m in met]),
        "element_ms": mean([g(m, element, "proctime_mean_ms") for m in met]),
        "vdd_in_w": mean([c["power_in_mw"]["value"] / 1000 for c in cpu]),
        "vdd_cpu_gpu_cv_w": mean([c["power_compute_mw"]["value"] / 1000 for c in cpu]),
        "cpu_pct": mean([c["cpu_system_tegrastats_pct"]["value"] for c in cpu]),
        "gpu_pct": mean([c["gpu_pct"]["value"] for c in cpu]),
        "qi_fill": mean([r["qi_fill"] for r in raw]),
        "s1_N_ms": 1e3 * med([b["s1e"] - b["s1s"] for b in N], 0),
        "s2_N_next_ms": 1e3 * med([b["s2"] for b in N], 0),
        "s2_S_next_ms": 1e3 * med([b["s2"] for b in S], 0),
        "ws_span_ms": 1e3 * med([r["ws_span"] for r in raw], 0),
        "latency_N_ms": 1e3 * med([b["s2s"] - b["mux"] + b["s2"] for b in N], 0),
        "latency_S_ms": 1e3 * med([b["s2s"] - b["mux"] + b["s2"] for b in S], 0),
        "split": {k: med([r[k] for r in raw]) for k in ("copy", "pre", "net", "post", "element")},
    }
    return out


def blocks(c, element_label):
    """Stage parts per batch type for the template: s1/s2 = [N parts, S parts], parts = [kind, ms, estimate]."""
    sp = c["split"]
    s1n_total = round(c["s1_N_ms"]) or round(c["inference_ms"] or 0)
    if all(sp[k] is not None for k in ("copy", "pre", "net", "post")):
        rest = max(1, s1n_total - round(sp["copy"] + sp["pre"] + sp["net"] + sp["post"]))
        s1n = [["copy", round(sp["copy"])], ["pre", max(1, round(sp["pre"]))], ["net", round(sp["net"])],
               ["pre", max(1, round(sp["post"]))], ["rest", rest]]
    else:
        s1n = [["inf", s1n_total]]
    saturated = (c["qi_fill"] or 0) > 0.5          # stage 2 never idles -> next-start gap is its real time
    el = c["element_ms"] or 0
    if saturated:
        s2n_total, s2s_total, est = c["s2_N_next_ms"], c["s2_S_next_ms"], False
    else:
        s2n_total, s2s_total, est = c["ws_span_ms"] or 10, None, True
    def split2(total, estimate):
        total = round(total)
        if el >= 1 and total > el:
            return [["other", max(1, total - round(el)), estimate], ["el", round(el), estimate]]
        return [["other", max(1, total), estimate]]
    s2n = split2(s2n_total, not saturated)   # when stage 2 idles, which batch a wsstatus record belongs to is uncertain
    s2s = split2(s2s_total, False) if s2s_total is not None else split2(min(5 + (el if el >= 1 else 0), s2n_total), True)
    return {"s1": [s1n, [["pre", 1]]], "s2": [s2n, s2s], "s2_estimated": not saturated}


def simulate(s1, s2, interval, pool, fps, n=80):
    tick, b = 1000 / fps, []
    total = lambda p: sum(x[1] for x in p)
    for i in range(n):
        kind = 0 if i % (interval + 1) == 0 else 1
        rel = b[i - pool][4] if i >= pool else 0
        cam = (math.floor(b[-1][0] / tick + 1e-6) + 1) * tick if b else 0
        mux = max(rel, cam)
        s1s = max(mux, b[-1][2] if b else 0)
        s1e = s1s + total(s1[kind])
        s2s = max(s1e, b[-1][4] if b else 0)
        b.append((mux, s1s, s1e, s2s, s2s + total(s2[kind])))
    return b[60][2] - b[60 - (interval + 1)][2]


def fmt(x, nd=1, unit=""):
    return "–" if x is None else f"{x:.{nd}f}{unit}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", action="append", required=True, help='"label=path/to/pmp"')
    ap.add_argument("--element", default="alertsocket")
    ap.add_argument("--cases", default="off,on")
    ap.add_argument("--interval", type=int, default=1)
    ap.add_argument("--pool", type=int, default=4)
    ap.add_argument("--camera-fps", type=float, default=12)
    ap.add_argument("--span-ms", type=int, default=1300)
    ap.add_argument("--title", default=None)
    ap.add_argument("--eyebrow", default="Worker pipeline · Jetson")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cases = a.cases.split(",")
    print("model check: gap = (model - measured) / measured; a few % negative is normal (the model leaves out untraced steps)")
    groups, tables, notes = [], [], []
    for sc in a.scenario:
        label, path = sc.split("=", 1)
        d = Path(path)
        summ = {c: summarize_case(d, c, a.element) for c in cases}
        gcases = []
        for c in cases:
            bl = blocks(summ[c], a.element)
            measured_cycle = (a.interval + 1) * 1000 / summ[c]["batches_per_s"] if summ[c]["batches_per_s"] else None
            model_cycle = simulate(bl["s1"], bl["s2"], a.interval, a.pool, a.camera_fps)
            gap = (model_cycle - measured_cycle) / measured_cycle * 100 if measured_cycle else None
            flag = "" if gap is None or abs(gap) <= 10 else "  <-- CHECK: model and measurement disagree"
            print(f"[{label} / {a.element} {c}] model {model_cycle:.0f} ms per cycle, measured "
                  f"{fmt(measured_cycle, 0)} ms ({fmt(gap, 0, ' %')}){flag}")
            notes.append(f"{label}, {c}: model {model_cycle:.0f} ms, measured {fmt(measured_cycle, 0)} ms per cycle")
            gcases.append({"title": f"{a.element} {c}, {label}", "s1": bl["s1"], "s2": bl["s2"],
                           "measured_cycle_ms": measured_cycle})
            summ[c]["s2_estimated"] = bl["s2_estimated"]
        groups.append({"title": label, "cases": gcases, "interval": a.interval, "pool": a.pool,
                       "camera_fps": a.camera_fps, "span_ms": a.span_ms})
        hdr = "".join(f"<th>{a.element} {c}</th>" for c in cases)
        rows = [
            ("Worker fps (batches/s, wsstatus)", "batches_per_s", 2, ""),
            ("Network runs / s", "network_runs_per_s", 2, ""),
            ("Inference per N batch", "inference_ms", 0, " ms"),
            (f"{a.element} per batch", "element_ms", 1, " ms"),
            ("Stage 1 per N batch", "s1_N_ms", 0, " ms"),
            ("Stage 2 per batch (next-start gap)", "s2_N_next_ms", 0, " ms"),
            ("Latency N batch (muxer → end of stage 2)", "latency_N_ms", 0, " ms"),
            ("Latency S batch", "latency_S_ms", 0, " ms"),
            ("queue_inference fill (batches)", "qi_fill", 2, ""),
            ("Input power VDD_IN", "vdd_in_w", 2, " W"),
            ("CPU + GPU rail VDD_CPU_GPU_CV", "vdd_cpu_gpu_cv_w", 2, " W"),
            ("CPU load", "cpu_pct", 0, " %"),
            ("GPU load", "gpu_pct", 0, " %"),
        ]
        body = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{fmt(summ[c][k], nd, u)}</td>" for c in cases) + "</tr>"
                       for name, k, nd, u in rows)
        body += "<tr><td>Runs</td>" + "".join(f"<td>{len(summ[c]['runs'])}</td>" for c in cases) + "</tr>"
        tables.append(f'<h3 style="font-family:var(--display);margin:16px 0 0">{label}</h3>'
                      f'<div class="tablewrap"><table><tr><th></th>{hdr}</tr>{body}</table></div>')
        est_cases = [c for c in cases if summ[c]["s2_estimated"]]
        if est_cases:
            tables.append(f'<p class="sub">Stage 2 idles in {", ".join(est_cases)} ({label}): its next-start gap '
                          "includes idle time, so the timeline uses the traced N-batch span and an estimate for S (dashed).</p>")
    tpl = (Path(__file__).parent.parent / "assets" / "timeline_template.html").read_text()
    title = a.title or f"What {a.element} costs in the worker pipeline"
    page = (tpl.replace("__GROUPS_JSON__", json.dumps(groups))
               .replace("__TABLES__", "\n".join(tables))
               .replace("__ELEMENT__", a.element)
               .replace("__TITLE__", title)
               .replace("__EYEBROW__", a.eyebrow)
               .replace("__SUBTITLE__", f"{a.element} on vs off, {', '.join(s.split('=')[0] for s in a.scenario)}. "
                                        "Medians and means over the runs of each case.")
               .replace("__MODEL_NOTE__", "Timeline drawn from a model of the threads (muxer with "
                        f"{a.pool} batch buffers, {a.camera_fps:g} fps cameras, network every {a.interval + 1}. batch) "
                        "using the measured stage times. " + "; ".join(notes) + ".")
               .replace("__FOOTER__", "Figures are unverified until checked against the raw logs. "
                        "⚠ Review by a qualified person required before use."))
    Path(a.out).write_text(page)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
