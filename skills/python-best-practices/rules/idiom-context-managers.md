---
title: Always Use with for Resources; Write Context Managers for Cleanup
impact: MEDIUM
impactDescription: Prevents resource leaks even when exceptions occur
tags: idioms, context-managers, resources, with-statement
---

## Always Use with for Resources; Write Context Managers for Cleanup

Files, network connections, locks, and database cursors must be opened with `with`. It
guarantees `__exit__` is called even when an exception is raised, preventing leaks.

**Incorrect (manual close — skipped on exception):**

```python
f = open("data.json")
data = json.load(f)
f.close()              # not called if json.load raises
```

**Correct:**

```python
with open("data.json") as f:
    data = json.load(f)
```

**Multiple resources in one statement (Python 3.10+ preferred style):**

```python
with (
    open("input.bin", "rb") as src,
    open("output.bin", "wb") as dst,
):
    dst.write(process(src.read()))
```

**Writing your own context manager with contextlib:**

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")

with timer("inference"):
    results = model.predict(image)
```

Use `contextlib.contextmanager` for simple cases. Implement `__enter__`/`__exit__` on a
class only when the context manager needs to carry meaningful state.

Reference: [contextlib docs](https://docs.python.org/3/library/contextlib.html)
