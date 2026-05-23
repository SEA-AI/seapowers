# Python Best Practices — Compiled Reference

All 20 rules expanded. Generated from `rules/`. See `SKILL.md` for the index.

---

## 1. Project Setup with uv (CRITICAL)

### Use uv for All Project and Dependency Management

`uv` replaces `pip`, `venv`, `pip-tools`, and `poetry` in one fast tool. Never use `pip install` directly in a project — it bypasses the lockfile and breaks reproducibility.

```bash
uv init my-project          # create new project with pyproject.toml + .venv
uv add requests             # add runtime dependency
uv add --dev pytest ruff    # add dev-only dependency
uv remove requests          # remove dependency
uv sync                     # install all deps from lockfile (CI / fresh clone)
uv run pytest               # run command inside the managed environment
uv run python script.py     # run a script without activating venv manually
uv lock --upgrade            # upgrade all deps and regenerate lockfile
```

Commit both `pyproject.toml` and `uv.lock`. Never run bare `pip install`.

---

### All Config in pyproject.toml — No requirements.txt or setup.py

`pyproject.toml` is the modern standard. All dependency declarations, tool configuration
(ruff, mypy, pytest), and package metadata live here.

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27"]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.4", "mypy>=1.10"]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

### Use src/ Layout for Packages, Flat Layout for Scripts

**src/ layout** — use when the project is an installable package:

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── core.py
├── tests/
├── pyproject.toml
└── uv.lock
```

**Flat layout** — acceptable for scripts, CLIs, and internal tooling:

```
my-tool/
├── my_tool/
│   ├── __init__.py
│   └── main.py
├── tests/
├── pyproject.toml
└── uv.lock
```

Tests always live outside the package directory.

---

## 2. Design Decisions (HIGH)

### Dataclasses for Internal Data, Pydantic at Trust Boundaries

**Decision rule:** _Has this data been validated yet?_ If no → Pydantic. If yes → dataclass.

- **`@dataclass`** — internal domain objects, fast, no validation overhead, works with mypy
- **Pydantic `BaseModel`** — HTTP request/response bodies, config/env parsing, file/JSON I/O

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

Use `frozen=True` on value objects (coordinates, measurements) for hashability and
immutability.

---

### Prefer Functions; Use Classes Only for State or Interface

A class with no instance state and one method is just a function with extra steps.

**When a class IS justified:**
1. You need mutable state across multiple method calls
2. You need to implement a `Protocol`
3. You need lifecycle management (`__enter__`/`__exit__`)

```python
# Wrong — no state, just a function
class DataNormalizer:
    def normalize(self, values: list[float]) -> list[float]: ...

# Right
def normalize(values: list[float]) -> list[float]: ...

# Right — class justified by state
@dataclass
class RunningStats:
    _count: int = 0
    _mean: float = 0.0
    _m2: float = 0.0

    def update(self, value: float) -> None: ...

    @property
    def variance(self) -> float: ...
```

---

### Favour Composition and Protocol Over Inheritance

Define interfaces with `Protocol` — structural typing, no coupling, trivial to mock.

```python
from typing import Protocol

class Detector(Protocol):
    def detect(self, image: bytes) -> list[Detection]: ...

class YOLODetector:           # satisfies Detector without inheriting
    def detect(self, image: bytes) -> list[Detection]: ...

class MockDetector:           # test double needs no production imports
    def detect(self, image: bytes) -> list[Detection]:
        return []
```

Use inheritance only for true "is-a" relationships with shared implementation. Cap depth at 1–2 levels.

---

### Return Early to Eliminate Nesting (Guard Clauses)

Handle error/edge cases first, then write the happy path without nesting.

```python
# Wrong — nested happy path
def process_detection(result: dict) -> BoundingBox | None:
    if result is not None:
        if "boxes" in result:
            if len(result["boxes"]) > 0:
                best = max(result["boxes"], key=lambda b: b["confidence"])
                if best["confidence"] > 0.5:
                    return BoundingBox(**best)
    return None

# Right — guard clauses
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

---

## 3. Testing with pytest (HIGH)

### Structure Every Test with Arrange-Act-Assert

```python
def test_detect_returns_boxes_above_threshold():
    # Arrange
    detector = Detector(threshold=0.5)
    image = make_test_image(objects=["boat"])

    # Act
    results = detector.detect(image)

    # Assert
    assert len(results) == 1
    assert results[0].label == "boat"
```

Name tests after behaviour: `test_<what>_<when>_<expected>`. One behaviour per test.

---

### Use Fixtures for Shared Setup; Scope Them Correctly

| Scope | Created | Use for |
|-------|---------|---------|
| `function` (default) | Each test | Mutable objects |
| `module` | Once per file | Read-only resources |
| `session` | Once per run | DB connections, large models |

```python
@pytest.fixture
def strict_parser() -> ResultParser:
    return ResultParser(strict=True)

@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection(TEST_DB_URL)
    yield conn
    conn.close()
```

---

### Use @pytest.mark.parametrize for Input Variations

```python
@pytest.mark.parametrize("threshold,expected_count", [
    (0.9, 0),
    (0.5, 2),
    (0.1, 5),
])
def test_filter_by_threshold(threshold: float, expected_count: int) -> None:
    result = filter_by_threshold(SAMPLE_DETECTIONS, threshold)
    assert len(result) == expected_count
```

Each parameter set is an independent test. Use `pytest.param(..., id="name")` for readable output.

---

### No Branching Logic or Loops Inside Tests

A test with `if` or `for` can pass for the wrong reason (condition never true, loop never runs).

```python
# Wrong
def test_high_confidence_boxes_have_labels():
    for box in results:
        if box.confidence > 0.8:
            assert box.label is not None   # may never execute

# Right
def test_high_confidence_boxes_have_labels():
    high_conf = [b for b in results if b.confidence > 0.8]
    assert len(high_conf) > 0, "test data must contain high-confidence boxes"
    assert all(b.label is not None for b in high_conf)
```

---

### Tests Must Be Fast and Hermetic — Mock All External I/O

```python
def test_fetch_vessel_data_returns_name(monkeypatch):
    def fake_get(url, **_):
        mock = MagicMock()
        mock.json.return_value = {"name": "EVER GIVEN"}
        return mock

    monkeypatch.setattr("mypackage.vessels.httpx.get", fake_get)
    result = fetch_vessel_data(mmsi="123456789")
    assert result["name"] == "EVER GIVEN"
```

Mark slow tests `@pytest.mark.slow`. Run with `uv run pytest -m "not slow"` locally.

---

## 4. Type Safety (HIGH)

### Annotate Every Function Signature

```python
from typing import TypeAlias

Box: TypeAlias = tuple[float, float, float, float]  # x1, y1, x2, y2

def compute_iou(box_a: Box, box_b: Box) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union else 0.0
```

Run `mypy --strict`. Use `TypeAlias` (or `type` in Python 3.12+) for complex types.

---

### Avoid Any — Use Specific Types, Unknown, or Protocol

`Any` disables type checking for everything it touches.

```python
# Bad
def parse_config(raw: dict) -> dict: ...

# Good — typed in and out
class RawConfig(TypedDict):
    threshold: str

class Config(TypedDict):
    threshold: float

def parse_config(raw: RawConfig) -> Config:
    return {"threshold": float(raw["threshold"])}
```

When truly unavoidable, isolate with `cast()` and annotate why: `# type: ignore[misc]`.

---

### Define Interfaces with Protocol, Not Abstract Base Classes

```python
from typing import Protocol

class Storage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class S3Storage:              # no import of Storage needed
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...

class InMemoryStorage:        # test double needs no production imports
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}
    def save(self, key: str, data: bytes) -> None:
        self._store[key] = data
    def load(self, key: str) -> bytes:
        return self._store[key]
```

---

## 5. Python Idioms (MEDIUM)

### Prefer Comprehensions; Use Generators for Large Sequences

```python
labels     = [d.label for d in detections]
high_conf  = [d for d in detections if d.confidence > 0.5]
total_area = sum(d.width * d.height for d in detections)   # generator — no list
label_conf = {d.label: d.confidence for d in detections}   # dict comprehension
unique     = {d.label for d in detections}                  # set comprehension
```

Avoid nested comprehensions beyond two levels — use a plain loop instead.

---

### Always Use with for Resources; Write Context Managers for Cleanup

```python
with open("data.json") as f:
    data = json.load(f)

# Multiple resources (Python 3.10+)
with (
    open("input.bin", "rb") as src,
    open("output.bin", "wb") as dst,
):
    dst.write(process(src.read()))

# Custom context manager
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label}: {time.perf_counter() - start:.3f}s")
```

---

### Use Tuple Unpacking and * Spread Instead of Index Access

```python
x1, y1, x2, y2 = detection["box"]      # not box[0], box[1], ...
first, *rest    = items
*init, last     = items
a, b            = b, a                  # swap

for lat, lon in coordinates:            # unpack in loop
    process(lat, lon)
```

---

## 6. Async Patterns (MEDIUM)

### Use async/await Only for I/O-Bound Work

| Workload | Tool |
|----------|------|
| Network requests, DB queries, file I/O | `asyncio` + `async`/`await` |
| CPU-intensive computation | `ProcessPoolExecutor` |
| Async loop needing CPU work | `loop.run_in_executor(executor, fn)` |

```python
def run_inference(image: np.ndarray) -> list[Detection]:
    """CPU-bound — plain sync function."""
    return model.predict(image)

async def fetch_and_detect(url: str, executor: ProcessPoolExecutor) -> list[Detection]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    image = decode_image(response.content)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, run_inference, image)
```

---

### Use asyncio.gather or TaskGroup for Concurrent Independent I/O

```python
# gather — Python 3.8+
position, voyage, metadata = await asyncio.gather(
    fetch_position(mmsi),
    fetch_voyage(mmsi),
    fetch_metadata(mmsi),
)

# TaskGroup — Python 3.11+ (preferred: cancels siblings on failure)
async with asyncio.TaskGroup() as tg:
    t_pos  = tg.create_task(fetch_position(mmsi))
    t_voy  = tg.create_task(fetch_voyage(mmsi))
    t_meta = tg.create_task(fetch_metadata(mmsi))
return VesselInfo(t_pos.result(), t_voy.result(), t_meta.result())
```

---

### Never Call Blocking Code Inside an Async Function

| Blocking (wrong) | Async equivalent |
|-----------------|-----------------|
| `requests.get(url)` | `httpx.AsyncClient().get(url)` |
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `open(path).read()` | `aiofiles.open(path)` or offload |
| CPU computation | `loop.run_in_executor(executor, fn)` |

```python
# If you must call a blocking function:
result = await loop.run_in_executor(None, blocking_fn, arg1, arg2)
```
