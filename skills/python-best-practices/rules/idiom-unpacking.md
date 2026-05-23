---
title: Use Tuple Unpacking and * Spread Instead of Index Access
impact: MEDIUM
impactDescription: More readable; breaks loudly when structure changes
tags: idioms, unpacking, destructuring, readability
---

## Use Tuple Unpacking and * Spread Instead of Index Access

Unpacking names values at the point of use, making code self-documenting. Index access
(`result[0]`, `result[1]`) is fragile — if the structure changes, the error appears at
the wrong place and with no useful message.

**Incorrect (index access):**

```python
box = detection["box"]
x1 = box[0]
y1 = box[1]
x2 = box[2]
y2 = box[3]
width = x2 - x1
```

**Correct (tuple unpacking):**

```python
x1, y1, x2, y2 = detection["box"]
width = x2 - x1
```

**Star unpacking for head/tail patterns:**

```python
first, *rest = items            # first element and everything else
*init, last = items             # all but last, and last
head, *middle, tail = items     # first, middle, last
```

**Unpacking in for loops:**

```python
# Incorrect
for pair in coordinates:
    lat = pair[0]
    lon = pair[1]
    process(lat, lon)

# Correct
for lat, lon in coordinates:
    process(lat, lon)
```

**Swap without temp variable:**

```python
a, b = b, a
```

**Unpacking function return values into named variables:**

```python
# Instead of: result = get_bounding_box(); x, y, w, h = result.x, result.y, ...
# Use a dataclass/namedtuple and unpack or access by name — don't return raw tuples
# from public APIs. Raw tuple returns are fine for private helpers.
```
