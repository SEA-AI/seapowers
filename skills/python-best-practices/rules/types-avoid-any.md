---
title: Avoid Any — Use Specific Types, Unknown, or Protocol
impact: HIGH
impactDescription: Any silently disables type checking for everything it touches
tags: types, any, mypy, type-safety
---

## Avoid Any — Use Specific Types, Unknown, or Protocol

`Any` infects: a variable typed `Any` turns off type checking for every operation on it
and every value derived from it. It is the type-system equivalent of `# noqa`.

**Common Any traps and their fixes:**

```python
# BAD — Any from untyped third-party lib bleeds through
import cv2
frame: Any = cv2.imread("image.jpg")

# GOOD — narrow immediately with a cast or assertion
import cv2
import numpy as np
frame: np.ndarray = cv2.imread("image.jpg")   # known shape: (H, W, 3) uint8
```

```python
# BAD — lazy dict typing
def parse_config(raw: dict) -> dict:
    return {"threshold": float(raw["threshold"])}

# GOOD — typed in and out
from typing import TypedDict

class RawConfig(TypedDict):
    threshold: str

class Config(TypedDict):
    threshold: float

def parse_config(raw: RawConfig) -> Config:
    return {"threshold": float(raw["threshold"])}
```

```python
# BAD — Any for "I don't know the type yet"
def process(data: Any) -> Any: ...

# GOOD — use object (accepts anything, operations must be explicit)
# or Unknown (safer: requires narrowing before use — needs `from typing import Never`)
# or a Protocol if you need a specific interface
def process(data: object) -> None: ...
```

When you truly cannot avoid `Any` (legacy code, missing stubs), isolate it with `cast()`
at the boundary and annotate why: `# type: ignore[misc]  # third-party lib has no stubs`.

Reference: [mypy Any docs](https://mypy.readthedocs.io/en/stable/dynamic_typing.html)
