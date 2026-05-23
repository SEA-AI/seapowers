---
title: Favour Composition and Protocol Over Inheritance
impact: HIGH
impactDescription: Avoids fragile base class problem; enables easy mocking and testing
tags: design, composition, inheritance, protocol, architecture
---

## Favour Composition and Protocol Over Inheritance

Deep inheritance hierarchies couple code together and make testing difficult. Prefer
composing small objects or functions. Use `Protocol` to define interfaces — it enables
structural subtyping (duck typing with type-checker support) without forcing a shared base class.

**Incorrect (inheritance for interface):**

```python
from abc import ABC, abstractmethod

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, image: bytes) -> list[Detection]: ...

class YOLODetector(BaseDetector):
    def detect(self, image: bytes) -> list[Detection]: ...

class MockDetector(BaseDetector):   # test double forced to inherit
    def detect(self, image: bytes) -> list[Detection]:
        return []
```

**Correct (Protocol for interface, composition for behaviour):**

```python
from typing import Protocol

class Detector(Protocol):
    def detect(self, image: bytes) -> list[Detection]: ...

# No inheritance required — any class with the right signature satisfies Detector
class YOLODetector:
    def detect(self, image: bytes) -> list[Detection]: ...

class MockDetector:                 # test double needs no imports from production code
    def detect(self, image: bytes) -> list[Detection]:
        return []

def run_pipeline(detector: Detector, images: list[bytes]) -> list[list[Detection]]:
    return [detector.detect(img) for img in images]
```

Use inheritance only for true "is-a" relationships where subclasses share significant
implementation — and even then, cap depth at one or two levels.

Reference: [typing.Protocol docs](https://docs.python.org/3/library/typing.html#typing.Protocol)
