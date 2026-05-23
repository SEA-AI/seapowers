---
title: Define Interfaces with Protocol, Not Abstract Base Classes
impact: MEDIUM
impactDescription: Structural typing; no forced inheritance; easy to mock
tags: types, protocol, abc, interfaces, structural-typing
---

## Define Interfaces with Protocol, Not Abstract Base Classes

`Protocol` enables structural subtyping: any class with the right methods satisfies the
interface, without importing or inheriting from it. This decouples callers from
implementations and makes test doubles trivial to write.

**Incorrect (ABC forces inheritance coupling):**

```python
from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> None: ...

    @abstractmethod
    def load(self, key: str) -> bytes: ...

class S3Storage(Storage):          # must import and inherit Storage
    ...

class InMemoryStorage(Storage):    # test double must also inherit
    def save(self, key: str, data: bytes) -> None:
        self._store[key] = data
    def load(self, key: str) -> bytes:
        return self._store[key]
```

**Correct (Protocol — zero coupling):**

```python
from typing import Protocol

class Storage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class S3Storage:                   # no import of Storage needed
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class InMemoryStorage:             # test double needs no production imports
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}
    def save(self, key: str, data: bytes) -> None:
        self._store[key] = data
    def load(self, key: str) -> bytes:
        return self._store[key]

def process(storage: Storage, key: str) -> None:   # accepts both
    data = storage.load(key)
    ...
```

Use `@runtime_checkable` on the Protocol only if you need `isinstance()` checks.

Reference: [PEP 544 — Protocols](https://peps.python.org/pep-0544/)
