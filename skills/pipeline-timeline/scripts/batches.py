#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Follow every batch through stage 1 (inference thread) and stage 2 (post-processing thread).

Usage: uv run batches.py <campaign folder>
Reads the raw gst-shark records in <case>_<n>_console.log.

Method:
- A queue record is logged when a batch leaves the queue; its time is how long the batch waited there.
- A batch is N (network ran) if an inference record starts when the batch leaves queue_processing.
- Queues are FIFO, so a batch belongs to the queue_inference record whose entry time equals its stage-1 end.
- Stage 2 per batch = next stage-2 start minus this one (exact only while stage 2 never idles).
"""

import bisect
import itertools
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

RECORD = re.compile(
    r"^(\d+):(\d\d):(\d\d\.\d+)\s+\d+\s+0x[0-9a-f]+\s+TRACE\s+GST_TRACER :0:: proctime, "
    r"element=\(string\)(\w+), time=\(string\)(\d+):(\d\d):(\d\d\.\d+)"
)
ANSI = re.compile(r"\x1b\[[0-9;]*m")
TRACKED = {"queue_processing", "inference", "queue_inference"}
WARMUP_S, TAIL_S = 15, 3  # skip startup and shutdown of each run
NETWORK_MATCH_S = (
    0.01  # an inference record starts within this of the batch leaving queue_processing
)
QUEUE_MATCH_S = (
    0.003  # a queue_inference entry within this of a batch's stage-1 end is that batch
)


@dataclass
class Record:
    logged: float  # seconds since start, when the record was written
    element: str
    duration: float  # seconds

    @property
    def start(self) -> float:
        return self.logged - self.duration


@dataclass
class Batch:
    kind: str  # "N": network ran, "S": network skipped
    muxed: float  # entered queue_processing
    stage1_start: float
    stage1_end: float
    stage2_start: float | None = None
    stage2: float | None = None  # until the next batch's stage 2 starts


def seconds(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


def read_records(path: Path) -> list[Record]:
    records = []
    for line in path.open(errors="replace"):
        m = RECORD.match(ANSI.sub("", line))
        if m and m.group(4) in TRACKED:
            records.append(
                Record(
                    seconds(*m.group(1, 2, 3)), m.group(4), seconds(*m.group(5, 6, 7))
                )
            )
    return records


def batches_from_queue(records: list[Record]) -> list[Batch]:
    """One batch per batch that left queue_processing, all S until a network run is found."""
    leaving = sorted(
        (r for r in records if r.element == "queue_processing"), key=lambda r: r.logged
    )
    return [Batch("S", r.start, r.logged, r.logged) for r in leaving]


def mark_network_runs(batches: list[Batch], records: list[Record]) -> None:
    starts = [b.stage1_start for b in batches]
    for r in records:
        if r.element != "inference":
            continue
        i = bisect.bisect_left(starts, r.start)
        nearest = min(
            (c for c in (i - 1, i) if 0 <= c < len(batches)),
            key=lambda c: abs(starts[c] - r.start),
        )
        if abs(starts[nearest] - r.start) < NETWORK_MATCH_S:
            batches[nearest].kind, batches[nearest].stage1_end = "N", r.logged


def end_skipped_batches(batches: list[Batch]) -> None:
    """An S batch leaves stage 1 once the batch before it has left."""
    for prev, b in itertools.pairwise(batches):
        if b.kind == "S":
            b.stage1_end = max(b.stage1_start, prev.stage1_end)


def attach_stage2(batches: list[Batch], records: list[Record]) -> None:
    queued = sorted(
        (r for r in records if r.element == "queue_inference"), key=lambda r: r.start
    )
    entries = [r.start for r in queued]
    for b in batches:
        i = bisect.bisect_left(entries, b.stage1_end - QUEUE_MATCH_S)
        close = [
            c
            for c in (i - 1, i, i + 1)
            if 0 <= c < len(entries) and abs(entries[c] - b.stage1_end) < QUEUE_MATCH_S
        ]
        if close:
            b.stage2_start = queued[
                min(close, key=lambda c: abs(entries[c] - b.stage1_end))
            ].logged
    stage2_starts = sorted(r.logged for r in queued)
    for b in batches:
        if b.stage2_start is not None:
            k = bisect.bisect_right(stage2_starts, b.stage2_start + 1e-4)
            if k < len(stage2_starts):
                b.stage2 = stage2_starts[k] - b.stage2_start


def batches(path: Path) -> list[Batch]:
    """Batches of one run with both stages known, outside warm-up and shutdown."""
    records = read_records(path)
    if not records:
        return []
    first, last = records[0].logged + WARMUP_S, records[-1].logged - TAIL_S
    found = batches_from_queue(records)
    mark_network_runs(found, records)
    end_skipped_batches(found)
    attach_stage2(found, records)
    return [b for b in found if b.stage2 is not None and first < b.muxed < last]


def latency(b: Batch) -> float:
    """Muxer to end of stage 2."""
    assert b.stage2_start is not None and b.stage2 is not None, (
        "only complete batches have a latency"
    )
    return b.stage2_start - b.muxed + b.stage2


def main(folder: Path) -> None:
    logs = sorted(folder.glob("*_console.log"))
    if not logs:
        sys.exit(
            f"usage: batches.py <campaign folder>   (no *_console.log in {folder})"
        )
    groups: dict[tuple[str, str], list[Batch]] = {}
    for path in logs:
        case = path.name.split("_")[0]
        for b in batches(path):
            groups.setdefault((case, b.kind), []).append(b)
    if not groups:
        sys.exit(
            f"no complete batches found in {folder}: are the gst-shark proctime records in the console logs?"
        )

    columns = sorted(groups)
    ms = lambda values: f"{1e3 * statistics.median(values):.0f} ms"
    print(
        "| median per batch | "
        + " | ".join(f"{case} {kind}" for case, kind in columns)
        + " |"
    )
    print("|---" * (len(columns) + 1) + "|")
    for label, value in [
        ("wait in front of stage 1", lambda b: b.stage1_start - b.muxed),
        ("stage 1", lambda b: b.stage1_end - b.stage1_start),
        ("wait in front of stage 2", lambda b: b.stage2_start - b.stage1_end),
        ("stage 2 (start to next start)", lambda b: b.stage2),
        ("muxer to stage 2 start", lambda b: b.stage2_start - b.muxed),
        ("muxer to end of stage 2", latency),
    ]:
        print(
            f"| {label} | "
            + " | ".join(ms([value(b) for b in groups[c]]) for c in columns)
            + " |"
        )
    print("| batches | " + " | ".join(str(len(groups[c])) for c in columns) + " |")
    print(
        "\n'stage 2 (start to next start)' is the real stage-2 time only while stage 2 never idles;"
        " when it idles, it includes the idle time."
    )


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "pmp"))
