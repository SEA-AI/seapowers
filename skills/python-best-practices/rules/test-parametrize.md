---
title: Use @pytest.mark.parametrize for Input Variations
impact: HIGH
impactDescription: Tests all edge cases without code duplication
tags: testing, pytest, parametrize, edge-cases
---

## Use @pytest.mark.parametrize for Input Variations

When testing the same behaviour with different inputs, use `parametrize` instead of writing
multiple near-identical test functions or — worse — loops inside a test.

**Incorrect (loop inside test — only first failure is visible):**

```python
def test_threshold_filtering():
    cases = [(0.9, 0), (0.5, 2), (0.1, 5)]
    for threshold, expected_count in cases:
        result = filter_by_threshold(detections, threshold)
        assert len(result) == expected_count   # failure here masks remaining cases
```

**Incorrect (duplicated test functions):**

```python
def test_threshold_09():
    assert len(filter_by_threshold(detections, 0.9)) == 0

def test_threshold_05():
    assert len(filter_by_threshold(detections, 0.5)) == 2
```

**Correct:**

```python
import pytest

@pytest.mark.parametrize("threshold,expected_count", [
    (0.9, 0),
    (0.5, 2),
    (0.1, 5),
])
def test_filter_by_threshold_returns_correct_count(
    threshold: float, expected_count: int
) -> None:
    result = filter_by_threshold(SAMPLE_DETECTIONS, threshold)
    assert len(result) == expected_count
```

Each parameter set runs as an independent test case with its own pass/fail status.
Use `pytest.param(..., id="descriptive-name")` to give cases readable names in the output.

Reference: [pytest parametrize docs](https://docs.pytest.org/en/stable/how-to/parametrize.html)
