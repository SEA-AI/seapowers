"""SEA-1517: follow every batch through stage 1 (inference) and stage 2 (post-processing).

Usage: python3 batches.py <runs dir>
Reads the raw gst-shark records in <case>_<n>_console.log. Only the Python standard library is needed.

Method:
- queue_processing / queue_inference records are logged when a batch leaves the queue; time = how long it waited.
- A batch is N (network ran) if an inference proctime record starts at the moment it left queue_processing.
- Queues are FIFO, so a batch is matched to the queue_inference record whose entry time equals its stage-1 end.
- Stage 2 time per batch = next batch's stage-2 start minus this one's (exact when stage 2 is never idle).
"""

import bisect
import re
import statistics as st
import sys
from pathlib import Path

LINE = re.compile(r"^(\d+):(\d\d):(\d\d\.\d+)\s+\d+\s+0x[0-9a-f]+\s+TRACE\s+GST_TRACER :0:: proctime, "
                  r"element=\(string\)(\w+), time=\(string\)(\d+):(\d\d):(\d\d\.\d+)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
WANT = {"queue_processing", "inference", "queue_inference"}


def sec(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


def batches(path):
    ev = []
    for line in path.open(errors="replace"):
        m = LINE.match(ANSI.sub("", line))
        if m and m.group(4) in WANT:
            ev.append((sec(*m.group(1, 2, 3)), m.group(4), sec(*m.group(5, 6, 7))))
    tmin, tmax = ev[0][0] + 15, ev[-1][0] - 3
    qp = sorted(e for e in ev if e[1] == "queue_processing")
    B = [dict(kind="S", mux=p[0] - p[2], s1s=p[0], s1e=p[0]) for p in qp]
    starts = [b["s1s"] for b in B]
    for e in ev:
        if e[1] != "inference":
            continue
        s = e[0] - e[2]
        i = bisect.bisect_left(starts, s)
        c = min((c for c in (i - 1, i) if 0 <= c < len(B)), key=lambda c: abs(starts[c] - s))
        if abs(starts[c] - s) < 0.01:
            B[c]["kind"], B[c]["s1e"] = "N", e[0]
    for i in range(1, len(B)):
        if B[i]["kind"] == "S":
            B[i]["s1e"] = max(B[i]["s1s"], B[i - 1]["s1e"])
    qi = sorted((e[0] - e[2], e[0]) for e in ev if e[1] == "queue_inference")
    entries = [x[0] for x in qi]
    pops = sorted(x[1] for x in qi)
    for b in B:
        i = bisect.bisect_left(entries, b["s1e"] - 0.003)
        cs = [c for c in (i - 1, i, i + 1) if 0 <= c < len(entries) and abs(entries[c] - b["s1e"]) < 0.003]
        if cs:
            b["s2s"] = qi[min(cs, key=lambda c: abs(entries[c] - b["s1e"]))][1]
    out = []
    for b in B:
        if "s2s" not in b or not tmin < b["mux"] < tmax:
            continue
        k = bisect.bisect_right(pops, b["s2s"] + 1e-4)
        if k < len(pops):
            b["s2"] = pops[k] - b["s2s"]
            out.append(b)
    return out


def main(D):
  if not list(D.glob("*_console.log")):
      sys.exit(f"usage: batches.py <pmp folder>   (no *_console.log found in {D})")
  rows = {}
  for p in sorted(D.glob("*_console.log")):
      case = p.name.split("_")[0]
      for b in batches(p):
          rows.setdefault((case, b["kind"]), []).append(b)

  ms = lambda xs: 1e3 * st.median(xs)
  print("| median per batch | " + " | ".join(f"{c} {k}" for c, k in sorted(rows)) + " |")
  print("|---" * (len(rows) + 1) + "|")
  for label, f in [
      ("wait in front of stage 1", lambda b: b["s1s"] - b["mux"]),
      ("stage 1", lambda b: b["s1e"] - b["s1s"]),
      ("wait in front of stage 2", lambda b: b["s2s"] - b["s1e"]),
      ("stage 2 (start to next start)", lambda b: b["s2"]),
      ("muxer to stage 2 start", lambda b: b["s2s"] - b["mux"]),
      ("muxer to end of stage 2", lambda b: b["s2s"] - b["mux"] + b["s2"]),
  ]:
      print(f"| {label} | " + " | ".join(f"{ms([f(b) for b in rows[k]]):.0f} ms" for k in sorted(rows)) + " |")
  print("| batches | " + " | ".join(str(len(rows[k])) for k in sorted(rows)) + " |")
  print("\nStage 2 'start to next start' is the real stage-2 time only when stage 2 never idles (alertsocket on);"
        " with alertsocket off it includes idle time.")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "pmp"))
