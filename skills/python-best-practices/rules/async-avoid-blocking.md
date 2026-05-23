---
title: Never Call Blocking Code Inside an Async Function
impact: MEDIUM
impactDescription: Blocking the event loop freezes all concurrent coroutines
tags: async, blocking, event-loop, concurrency
---

## Never Call Blocking Code Inside an Async Function

Calling a blocking function (synchronous I/O, `time.sleep`, CPU-heavy code) inside an
`async` function freezes the entire event loop — no other coroutines can run until it
returns. This eliminates all concurrency benefits.

**Common blocking calls to avoid in async context:**

| Blocking (wrong) | Async equivalent |
|-----------------|-----------------|
| `requests.get(url)` | `httpx.AsyncClient().get(url)` |
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `open(path).read()` | `aiofiles.open(path)` or offload |
| CPU computation | `loop.run_in_executor(executor, fn)` |
| `subprocess.run(...)` | `asyncio.create_subprocess_exec(...)` |

**Incorrect:**

```python
async def poll_vessels(mmsis: list[str]) -> list[Position]:
    positions = []
    for mmsi in mmsis:
        time.sleep(0.1)                    # blocks entire event loop
        r = requests.get(f"/api/{mmsi}")   # synchronous HTTP
        positions.append(r.json())
    return positions
```

**Correct:**

```python
import asyncio
import httpx

async def poll_vessels(mmsis: list[str]) -> list[Position]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"/api/{mmsi}") for mmsi in mmsis]
        responses = await asyncio.gather(*tasks)
    return [r.json() for r in responses]
```

If you must call a blocking library function and cannot replace it, offload it:

```python
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(None, blocking_fn, arg1, arg2)
```
