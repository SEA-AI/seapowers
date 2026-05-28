# Testing with pytest

## pytest only

Stick to pytest idioms throughout. Do **not** mix in `unittest.TestCase`, `self.assert*`,
or `setUp`/`tearDown` — pytest fixtures replace all of that and compose better.

## Structure: Arrange → Act → Assert

Every test has exactly three phases, separated by blank lines. One behaviour per test.
Name tests after what they verify: `test_<what>_when_<condition>_<expected_outcome>`.

```python
def test_filter_detections_when_threshold_high_returns_empty():
    # Arrange
    detections = [Detection(label="boat", confidence=0.4)]

    # Act
    result = filter_by_confidence(detections, threshold=0.9)

    # Assert
    assert result == []
```

## conftest.py — shared fixtures

Fixtures defined in `conftest.py` are auto-discovered by pytest — no imports needed.
Place it in `tests/` for project-wide fixtures; add nested `conftest.py` files only for
fixtures scoped to a subdirectory.

```python
# tests/conftest.py
import pytest
from mypackage.db import create_connection

@pytest.fixture(scope="session")
def db():
    """One real DB connection for the entire test run."""
    conn = create_connection(":memory:")
    yield conn
    conn.close()

@pytest.fixture
def clean_db(db):
    """Wipe tables before each test that needs a clean slate."""
    db.execute("DELETE FROM detections")
    yield db
```

## Fixture scopes

Choose scope to avoid recreating expensive objects unnecessarily:

| Scope | Created | Use for |
|-------|---------|---------|
| `function` (default) | Each test | Mutable objects, anything that changes state |
| `module` | Once per file | Read-only data loaded from disk |
| `session` | Once per run | DB connections, HTTP clients, large models |

When a high-scope fixture (e.g. `session`) needs cleanup, use `yield` — the code after
`yield` runs as teardown.

## Parametrize for input variations

Use `@pytest.mark.parametrize` instead of writing multiple near-identical test functions
or looping inside a single test. Each parameter set gets an independent pass/fail result.

```python
@pytest.mark.parametrize("threshold,expected", [
    (0.9, 0),
    (0.5, 2),
    (0.1, 5),
])
def test_filter_returns_correct_count(threshold: float, expected: int) -> None:
    result = filter_by_confidence(SAMPLE_DETECTIONS, threshold)
    assert len(result) == expected
```

Use `pytest.param(..., id="descriptive-name")` to give cases readable names in the output.

## Mock external I/O at the boundary

Mock at the edge of your system (HTTP calls, DB queries, filesystem), not deep inside
your own logic. Use `monkeypatch` for simple attribute/env patches; use `pytest-mock`
(`uv add --dev pytest-mock`) for richer mocking — it provides a `mocker` fixture that
is pytest-native and auto-cleans up after each test.

```python
from types import SimpleNamespace

# Simple patch with monkeypatch
def test_fetch_vessel_returns_name(monkeypatch):
    fake = SimpleNamespace(json=lambda: {"name": "EVER GIVEN"})
    monkeypatch.setattr("mypackage.vessels.httpx.get", lambda url, **_: fake)
    assert fetch_vessel("123456789")["name"] == "EVER GIVEN"

# Richer mock with pytest-mock
def test_fetch_vessel_returns_name(mocker):
    mock_get = mocker.patch("mypackage.vessels.httpx.get")
    mock_get.return_value.json.return_value = {"name": "EVER GIVEN"}
    assert fetch_vessel("123456789")["name"] == "EVER GIVEN"
```

Mark tests that genuinely require external services with `@pytest.mark.integration` and
skip them locally: `uv run pytest -m "not integration"`.

## Avoid

- **Testing implementation details** — test observable behaviour and outputs, not internal
  state or method calls. Tests that mirror the implementation break on every refactor even
  when behaviour is unchanged.
- **Over-mocking** — if you mock everything inside a function, you're testing the mocks,
  not the logic. Mock boundaries (I/O), not internals.
- **`if` / `for` inside test bodies** — a conditional assertion that never executes is a
  silent false positive. Use `parametrize` or split into separate tests instead.
- **Assertions inside helper functions** — pytest reports the line where `assert` lives;
  if it's buried in a helper, the failure points to the wrong place.
- **Sharing mutable state between tests** — use function-scoped fixtures; relying on test
  execution order creates flaky tests.
