---
title: Use asyncio.gather or TaskGroup for Concurrent Independent I/O
impact: MEDIUM
impactDescription: Parallel I/O reduces total latency to max(individual latency)
tags: async, concurrency, gather, taskgroup, performance
---

## Use asyncio.gather or TaskGroup for Concurrent Independent I/O

Sequential `await` calls are serial — each waits for the previous one to complete.
When operations are independent, run them concurrently with `asyncio.gather` (Python 3.8+)
or `asyncio.TaskGroup` (Python 3.11+ — preferred for its cleaner error handling).

**Incorrect (sequential, 3× the latency):**

```python
async def enrich_vessel(mmsi: str) -> VesselInfo:
    position = await fetch_position(mmsi)
    voyage = await fetch_voyage(mmsi)
    metadata = await fetch_metadata(mmsi)
    return VesselInfo(position, voyage, metadata)
```

**Correct with asyncio.gather:**

```python
async def enrich_vessel(mmsi: str) -> VesselInfo:
    position, voyage, metadata = await asyncio.gather(
        fetch_position(mmsi),
        fetch_voyage(mmsi),
        fetch_metadata(mmsi),
    )
    return VesselInfo(position, voyage, metadata)
```

**Correct with TaskGroup (Python 3.11+ — preferred):**

```python
async def enrich_vessel(mmsi: str) -> VesselInfo:
    async with asyncio.TaskGroup() as tg:
        t_pos  = tg.create_task(fetch_position(mmsi))
        t_voy  = tg.create_task(fetch_voyage(mmsi))
        t_meta = tg.create_task(fetch_metadata(mmsi))
    # All tasks completed or all cancelled on first exception
    return VesselInfo(t_pos.result(), t_voy.result(), t_meta.result())
```

`TaskGroup` is preferred over `gather` for new code because it propagates exceptions
correctly and cancels sibling tasks on failure.

Reference: [asyncio.TaskGroup docs](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup)
