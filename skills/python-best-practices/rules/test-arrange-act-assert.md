---
title: Structure Every Test with Arrange-Act-Assert
impact: HIGH
impactDescription: Tests are readable and maintainable; failures are instantly diagnosable
tags: testing, pytest, structure, aaa
---

## Structure Every Test with Arrange-Act-Assert

Every test has three phases: **Arrange** (set up inputs and dependencies), **Act** (call the
thing under test — one call), **Assert** (verify the outcome). Separate them with a blank
line. One behaviour per test.

**Incorrect (unstructured, multiple assertions on unrelated things):**

```python
def test_detector():
    det = Detector(threshold=0.5)
    img = load_image("test.jpg")
    r = det.detect(img)
    assert r is not None
    assert len(r) > 0
    assert r[0].confidence > 0.5
    assert r[0].label == "boat"
    det2 = Detector(threshold=0.9)
    assert det2.detect(img) == []
```

**Correct (one behaviour, clear structure):**

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
    assert results[0].confidence > 0.5


def test_detect_returns_empty_when_all_boxes_below_threshold():
    # Arrange
    detector = Detector(threshold=0.99)
    image = make_test_image(objects=["boat"])

    # Act
    results = detector.detect(image)

    # Assert
    assert results == []
```

Name tests after the behaviour they verify (`test_<what>_<when>_<expected>`), not after
the function name (`test_detect`).
