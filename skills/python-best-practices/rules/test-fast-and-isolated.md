---
title: Tests Must Be Fast and Hermetic — Mock All External I/O
impact: HIGH
impactDescription: Fast feedback loop; no flaky tests from network or disk state
tags: testing, pytest, mocking, isolation, speed
---

## Tests Must Be Fast and Hermetic — Mock All External I/O

A test that calls a real network endpoint, writes to disk, or loads a large model is not a
unit test — it is a slow, flaky integration test. Mock external dependencies at the boundary
of your code, not deep inside it.

**Incorrect (test depends on real HTTP call):**

```python
def test_fetch_vessel_data():
    result = fetch_vessel_data(mmsi="123456789")   # real HTTP request
    assert result["name"] is not None
```

**Correct (patch the HTTP client at the boundary):**

```python
from unittest.mock import patch, MagicMock

def test_fetch_vessel_data_returns_name():
    mock_response = MagicMock()
    mock_response.json.return_value = {"mmsi": "123456789", "name": "EVER GIVEN"}
    mock_response.raise_for_status.return_value = None

    with patch("mypackage.vessels.httpx.get", return_value=mock_response):
        result = fetch_vessel_data(mmsi="123456789")

    assert result["name"] == "EVER GIVEN"
```

**With pytest monkeypatch (preferred for simple cases):**

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

Mark genuinely slow tests (`@pytest.mark.slow`) so they can be skipped during local
development (`uv run pytest -m "not slow"`).
