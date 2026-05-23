---
title: Use async/await Only for I/O-Bound Work
impact: MEDIUM
impactDescription: Avoids false concurrency; matches the right tool to the workload
tags: async, concurrency, io-bound, cpu-bound
---

## Use async/await Only for I/O-Bound Work

`async`/`await` enables concurrent I/O by interleaving coroutines while waiting for
network or disk operations. It provides **zero benefit** for CPU-bound work and adds
overhead. Use the right tool:

| Workload | Tool |
|----------|------|
| Network requests, DB queries, file I/O | `asyncio` + `async`/`await` |
| CPU-intensive computation (image processing, ML) | `multiprocessing` / `ProcessPoolExecutor` |
| Mixed: async loop that needs CPU work | `loop.run_in_executor(executor, ...)` |

**Incorrect (async on CPU work — no concurrency gained, overhead added):**

```python
async def run_inference(image: np.ndarray) -> list[Detection]:
    # model.predict is pure CPU/GPU — async adds nothing
    return model.predict(image)
```

**Correct (sync for CPU, async for I/O):**

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def run_inference(image: np.ndarray) -> list[Detection]:
    """CPU-bound — plain sync function."""
    return model.predict(image)

async def fetch_and_detect(url: str, executor: ProcessPoolExecutor) -> list[Detection]:
    """I/O to fetch, then CPU to detect — bridge with run_in_executor."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)          # I/O — awaited
    image = decode_image(response.content)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, run_inference, image)  # CPU in process pool
```

Do not mark every function `async` by default. Only functions that contain `await`
expressions (or call functions that do) should be `async`.
