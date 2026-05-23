---
title: Dataclasses for Internal Data, Pydantic at Trust Boundaries
impact: HIGH
impactDescription: Correct validation where it matters; no overhead where it doesn't
tags: design, dataclass, pydantic, validation, architecture
---

## Dataclasses for Internal Data, Pydantic at Trust Boundaries

**Use `@dataclass`** for internal domain objects where data is already trusted (came from
your own code or a validated layer). Fast, zero-dependency, works with mypy perfectly.

**Use Pydantic `BaseModel`** at trust boundaries: HTTP request/response bodies, config/env
parsing, file or JSON I/O, anything that arrives as raw external data.

**Decision rule:** _Has this data been validated yet?_ If no → Pydantic. If yes → dataclass.

**Incorrect (Pydantic everywhere, including internal):**

```python
from pydantic import BaseModel

class BoundingBox(BaseModel):      # used only inside the detection pipeline
    x: float
    y: float
    width: float
    height: float

class DetectionResult(BaseModel):  # computed internally, never serialized
    boxes: list[BoundingBox]
    confidence: float
```

**Correct (Pydantic at edge, dataclass inside):**

```python
from dataclasses import dataclass
from pydantic import BaseModel

# At the API boundary — validate incoming JSON
class DetectionRequest(BaseModel):
    image_url: str
    threshold: float = 0.5

# Internal domain objects — fast, no overhead
@dataclass(frozen=True)
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

@dataclass
class DetectionResult:
    boxes: list[BoundingBox]
    confidence: float
```

Use `frozen=True` on dataclasses representing value objects (coordinates, measurements)
to get hashability and prevent accidental mutation.
