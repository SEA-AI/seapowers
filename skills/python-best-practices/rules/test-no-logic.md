---
title: No Branching Logic or Loops Inside Tests
impact: HIGH
impactDescription: Tests remain trustworthy; failures are unambiguous
tags: testing, pytest, test-quality, anti-patterns
---

## No Branching Logic or Loops Inside Tests

A test with `if`, `for`, or `while` inside it is a test that can pass for the wrong reason.
If the condition is never true, or the loop never executes, you get a green test that proved
nothing. Move iteration to `parametrize` and conditions to separate test functions.

**Incorrect (conditional assertion — may silently skip the check):**

```python
def test_high_confidence_boxes_have_labels():
    results = detector.detect(sample_image)
    for box in results:
        if box.confidence > 0.8:          # what if there are no high-confidence boxes?
            assert box.label is not None   # this assert may never run
```

**Correct (assert the precondition, then assert the property):**

```python
def test_high_confidence_boxes_have_labels():
    results = detector.detect(sample_image)
    high_conf = [b for b in results if b.confidence > 0.8]

    assert len(high_conf) > 0, "test data must contain high-confidence boxes"
    assert all(b.label is not None for b in high_conf)
```

**Rule of thumb:** If you need an `if` inside a test, you probably need two tests.
If you need a loop, you probably need `parametrize`.
