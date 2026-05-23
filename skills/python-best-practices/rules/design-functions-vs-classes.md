---
title: Prefer Functions; Use Classes Only for State or Interface
impact: HIGH
impactDescription: Simpler code, easier to test, less indirection
tags: design, functions, classes, architecture, oop
---

## Prefer Functions; Use Classes Only for State or Interface

A class that has no instance state and only one method (or only static methods) is just a
function with extra steps. Prefer plain functions — they are easier to test, import,
and compose.

**When a class IS justified:**
1. You need to carry mutable state across multiple method calls
2. You need to implement a `Protocol` (adapter, repository, strategy pattern)
3. You need lifecycle management (`__enter__`/`__exit__`, `__init__`/`close`)

**Incorrect (class with no real state):**

```python
class DataNormalizer:
    def normalize(self, values: list[float]) -> list[float]:
        minimum = min(values)
        maximum = max(values)
        return [(v - minimum) / (maximum - minimum) for v in values]

normalizer = DataNormalizer()
result = normalizer.normalize(data)
```

**Correct (plain function):**

```python
def normalize(values: list[float]) -> list[float]:
    minimum = min(values)
    maximum = max(values)
    return [(v - minimum) / (maximum - minimum) for v in values]

result = normalize(data)
```

**Correct (class justified by state):**

```python
@dataclass
class RunningStats:
    """Incrementally computes mean and variance without storing all values."""
    _count: int = 0
    _mean: float = 0.0
    _m2: float = 0.0

    def update(self, value: float) -> None:
        self._count += 1
        delta = value - self._mean
        self._mean += delta / self._count
        self._m2 += delta * (value - self._mean)

    @property
    def variance(self) -> float:
        return self._m2 / self._count if self._count > 1 else 0.0
```
