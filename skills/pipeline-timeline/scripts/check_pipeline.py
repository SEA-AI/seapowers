#!/usr/bin/env python3
"""Check that references/pipeline.md still matches the code under test.

Usage (from the Core-Backend repo root; SKILL = this skill's base directory):
    python3 $SKILL/scripts/check_pipeline.py --rev <commit> [--element alertsocket] [--profile 1024S_Gen_2] [--run-dir <pmp>]

<commit> = the Core-Backend commit installed on the device (~/versions.json). Reads files with `git show`,
so the working tree is not touched. Prints one line per fact: OK, CHANGED (update your understanding and
references/pipeline.md before measuring) or MISSING.

--run-dir <pmp folder>: also read what actually ran (console log of a campaign). Devices can carry
test patches on top of <commit> (e.g. the GPU MockCNN); the run shows whether they were active.
--profile <name>: the device's worker profile (from ~/POWER_Const/hardwareVersion, e.g.
Oscar_V10_1024S_Gen_2 -> 1024S_Gen_2); only that profile's processing_interval is checked.
"""

import argparse
import json
import re
import subprocess
import sys

EXPECTED_ELEMENTS = [
    "capsfilter", "queue", "batch_validation", "inference|inferencecpp", "queue",
    "ignoremaskfilter", "cpptransformation", "sensorfusion", "horizon_detection", "applystabilisation",
    "detectionhorizonfilter", "cppdistanceestimation", "imgtracker", "radar_fusion",
    "trajectoryclassification", "object_relabeller", "threatlevelmanager", "alarmmanager",
    "postprocessing", "metadatacache", "alertsocket", "wsstatus",
]


def show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def ls(rev, path):
    r = subprocess.run(["git", "ls-tree", "--name-only", f"{rev}", path + "/"], capture_output=True, text=True)
    return r.stdout.split()


def run_facts(d):
    """What a campaign actually ran with, from its first console log."""
    from pathlib import Path
    logs = sorted(Path(d).glob("*_console.log"))
    if not logs:
        return {"run-dir": f"no *_console.log in {d}"}
    text = logs[0].read_text(errors="replace")
    net = [float(x) for x in re.findall(r"Model profiling:\s*[\d.]+ ms - preprocess,\s*([\d.]+) ms - inference", text)][10:]
    scen = re.search(r"Loaded scenario from \S*/(\S+\.json)", text)
    model = re.search(r"Using model: \S*?(\w+)\S*$", text, re.M)
    return {
        "mock_cnn_enabled": '"mock_cnn_enabled": true' in text or "mock_cnn_enabled=true" in text,
        "mock scenario": scen.group(1) if scen else "none",
        "model": model.group(1) if model else "?",
        "network median ms": round(sorted(net)[len(net) // 2], 1) if net else "no Model profiling lines",
        "extended API active": "EXTENDED_API'>: True" in text,
    }


def report(status, what, detail=""):
    print(f"{status:8s} {what}" + (f": {detail}" if detail else ""))
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--element", default="alertsocket", help="element under test")
    ap.add_argument("--run-dir", default=None, help="pmp folder of a campaign, to confirm what actually ran")
    ap.add_argument("--profile", default=None, help="worker profile folder name, e.g. 1024S_Gen_2")
    a = ap.parse_args()
    rev = a.rev
    results = []
    print(f"Pipeline check against {rev}\n")

    pb = show(rev, "Core/Gst/plugins/python/processing_bin.py")
    if pb is None:
        results.append(report("MISSING", "processing_bin.py"))
    else:
        m = re.search(r"elements = \[(.*?)\n\s*\]", pb, re.S)
        found = re.findall(r'\("(\w+)",\s*"(\w+)"\)', m.group(1)) if m else []
        factories = [f for f, _ in found]
        names = [n for _, n in found]
        ok = len(factories) == len(EXPECTED_ELEMENTS) and all(
            re.fullmatch(e, f) for e, f in zip(EXPECTED_ELEMENTS, factories))
        results.append(report("OK" if ok else "CHANGED", "processing bin element order",
                              " → ".join(names)))
        qpos = [n for f, n in found if f == "queue"]
        results.append(report("OK" if qpos == ["queue_processing", "queue_inference"] else "CHANGED",
                              "queues inside the processing bin (thread starts)", ", ".join(qpos)))
        inf = [f for f, n in found if n == "inference"]
        lang = {"inference": "Python inference_py.py", "inferencecpp": "C++ inferencecpp"}.get(inf[0] if inf else "", "?")
        results.append(report("INFO", "stage-1 inference element", f"{inf[0] if inf else '?'} ({lang})"))
        if a.element not in names:
            results.append(report("CHANGED", f"element under test '{a.element}' in the processing bin", "not found"))
        else:
            idx = names.index(a.element)
            stage = "T6 (after queue_inference)" if idx > names.index("queue_inference") else "T5 or earlier"
            results.append(report("INFO", f"'{a.element}' runs in", stage))
        pool = re.search(r'"buffer-pool-size",\s*(\d+)', pb)
        cond = "USE_NEW_NVSTREAMMUX" in pb
        results.append(report("OK" if pool and pool.group(1) == "4" else "CHANGED", "muxer buffer-pool-size",
                              f"{pool.group(1) if pool else 'not set'} (only with legacy muxer: {cond})"))

    env = show(rev, "Core/WorkerProfiles/common.env") or ""
    m = re.search(r'^USE_NEW_NVSTREAMMUX="?(\w+)"?', env, re.M)
    results.append(report("OK" if m and m.group(1) == "no" else "CHANGED", "USE_NEW_NVSTREAMMUX in common.env",
                          m.group(1) if m else "not set"))

    profs = [p for p in ls(rev, "Core/WorkerProfiles/Watchkeeper") if not p.endswith((".env", ".json", ".md"))]
    if a.profile:
        profs = [p for p in profs if p.split("/")[-1] == a.profile] or profs
    for prof in profs:
        pj = show(rev, f"{prof}/parameters.json")
        if pj:
            try:
                iv = json.loads(pj).get("processing_interval")
            except json.JSONDecodeError:
                iv = "unreadable"
            results.append(report("OK" if iv == 1 else "CHANGED", f"processing_interval {prof.split('/')[-1]}", str(iv)))

    det = show(rev, "Core/managers/settings/groups/detection.py") or ""
    run = run_facts(a.run_dir) if a.run_dir else {}
    if "mock_cnn_enabled" in det:
        results.append(report("OK", "GPU MockCNN setting mock_cnn_enabled", "present"))
    elif run.get("mock_cnn_enabled"):
        results.append(report("INFO", "GPU MockCNN", f"not in {rev}, but the run used it (patched on the device)"))
    else:
        results.append(report("MISSING", "GPU MockCNN setting mock_cnn_enabled",
                              "absent: only the sleep-only MockCNN exists; port develop 7aa03a9ae for GPU load"))
    for k, v in run.items():
        results.append(report("RUN", k, str(v)))

    el = show(rev, f"Core/Gst/plugins/python/{a.element}.py")
    if el is not None:
        has_enabled = re.search(r'nick="Enabled"', el) is not None
        results.append(report("INFO", f"'{a.element}' has an 'enabled' property", str(has_enabled)))
        if a.element == "alertsocket":
            resize_called = "_crop_and_resize_frame(" in el.split("def _crop_and_resize_frame")[-1] if "def _crop_and_resize_frame" in el else False
            results.append(report("INFO", "alertsocket resizes the snapshot before JPEG", str(resize_called)))

    pmp = show(rev, "Tools/scripts/power_mode_perf.sh")
    if pmp is None:
        pmp = show("origin/develop", "Tools/scripts/power_mode_perf.sh")
        results.append(report("INFO", f"Tools/scripts/power_mode_perf.sh not in {rev}",
                              "using origin/develop's copy; copy develop's Tools/scripts to the device" if pmp
                              else "not on origin/develop either"))
    if pmp is not None:
        tr = re.search(r'PERF_TRACERS="\$\{PERF_TRACERS:-(.*?)\}"', pmp)
        filt = tr.group(1) if tr else ""
        results.append(report("INFO", "power_mode_perf.sh default tracers include the element",
                              str(a.element in filt)))
        results.append(report("INFO", "proctime infer-only (S batches not traced)", str("infer-only=True" in filt)))
        if "do_tracker_rotcomp" in pmp:
            results.append(report("INFO", "power_mode_perf.sh passes stale do_tracker_rotcomp", "no effect, see #1108"))

    changed = [r for r in results if r in ("CHANGED", "MISSING")]
    print(f"\n{len(changed)} item(s) differ from references/pipeline.md." if changed else "\nAll checked facts match.")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
