---
title: Prefer Comprehensions; Use Generators for Large Sequences
impact: MEDIUM
impactDescription: More readable and often faster than map/filter/loop equivalents
tags: idioms, comprehensions, generators, performance
---

## Prefer Comprehensions; Use Generators for Large Sequences

List/dict/set comprehensions are idiomatic Python. They are cleaner than `map`/`filter`
with `lambda` and are generally faster than equivalent `for` loops that call `.append()`.

Use a **generator expression** (round brackets) instead of a list comprehension when:
- You only iterate once (no need to materialise the full list)
- The sequence is large (saves memory)

**Incorrect (map/filter with lambda):**

```python
labels = list(map(lambda d: d.label, detections))
high_conf = list(filter(lambda d: d.confidence > 0.5, detections))
```

**Correct (comprehensions):**

```python
labels = [d.label for d in detections]
high_conf = [d for d in detections if d.confidence > 0.5]
```

**Generator for large sequences or single-pass iteration:**

```python
# Don't materialise if you only need the sum
total_area = sum(d.width * d.height for d in detections)

# Dict comprehension
label_to_conf = {d.label: d.confidence for d in detections}

# Set comprehension for unique values
unique_labels = {d.label for d in detections}
```

**Avoid nested comprehensions beyond two levels** — they become harder to read than
a plain loop:

```python
# Hard to read
flat = [item for sublist in matrix for item in sublist if item > 0]

# Clearer
flat = []
for sublist in matrix:
    flat.extend(x for x in sublist if x > 0)
```
