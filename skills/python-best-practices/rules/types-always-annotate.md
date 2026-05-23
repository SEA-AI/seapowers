---
title: Annotate Every Function Signature
impact: HIGH
impactDescription: Enables static analysis; prevents entire classes of bugs
tags: types, annotations, mypy, readability
---

## Annotate Every Function Signature

Annotate the types of all function parameters and return values. Skip body variable
annotations only when the type is unambiguous from the assignment. Run mypy in strict mode
(`mypy --strict` or `strict = true` in pyproject.toml) to enforce this.

**Incorrect (no annotations — mypy cannot check callers):**

```python
def compute_iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_w = max(0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = (ax2-ax1)*(ay2-ay1) + (bx2-bx1)*(by2-by1) - inter
    return inter / union if union else 0
```

**Correct:**

```python
from typing import TypeAlias

Box = TypeAlias = tuple[float, float, float, float]  # x1, y1, x2, y2

def compute_iou(box_a: Box, box_b: Box) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union else 0.0
```

Use `TypeAlias` (or the new `type` statement in Python 3.12+) to name complex types rather
than repeating `tuple[float, float, float, float]` everywhere.

Reference: [mypy cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
