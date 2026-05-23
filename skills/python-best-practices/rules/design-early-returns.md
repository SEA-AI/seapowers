---
title: Return Early to Eliminate Nesting (Guard Clauses)
impact: MEDIUM
impactDescription: Reduces cognitive load; makes error paths explicit
tags: design, guard-clauses, nesting, readability
---

## Return Early to Eliminate Nesting (Guard Clauses)

Handle error/edge cases first with early returns or raises, then write the happy path
without nesting. Deep nesting (3+ levels) is a sign the function should be split or
rewritten with guard clauses.

**Incorrect (nested happy path):**

```python
def process_detection(result: dict) -> BoundingBox | None:
    if result is not None:
        if "boxes" in result:
            boxes = result["boxes"]
            if len(boxes) > 0:
                best = max(boxes, key=lambda b: b["confidence"])
                if best["confidence"] > 0.5:
                    return BoundingBox(**best)
    return None
```

**Correct (guard clauses, flat happy path):**

```python
def process_detection(result: dict) -> BoundingBox | None:
    if result is None or "boxes" not in result:
        return None
    boxes = result["boxes"]
    if not boxes:
        return None
    best = max(boxes, key=lambda b: b["confidence"])
    if best["confidence"] <= 0.5:
        return None
    return BoundingBox(**best)
```

The same pattern applies to `raise` — validate inputs at the top of a function and
raise immediately, rather than wrapping the body in an `if valid:` block.
