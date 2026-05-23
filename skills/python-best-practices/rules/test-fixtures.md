---
title: Use Fixtures for Shared Setup; Scope Them Correctly
impact: HIGH
impactDescription: Eliminates duplicated setup; controls expensive resource creation
tags: testing, pytest, fixtures, setup
---

## Use Fixtures for Shared Setup; Scope Them Correctly

Fixtures replace `setUp`/`tearDown` and avoid copy-pasting setup code across tests.
Set the correct scope to avoid recreating expensive objects unnecessarily.

| Scope | Created | Use for |
|-------|---------|---------|
| `function` (default) | Each test | Mutable objects, anything that changes state |
| `module` | Once per file | Read-only resources loaded from disk |
| `session` | Once per run | DB connections, server processes, large models |

**Incorrect (repeated setup in each test):**

```python
def test_parse_valid():
    parser = ResultParser(strict=True)   # duplicated
    assert parser.parse('{"label":"boat"}') is not None

def test_parse_invalid():
    parser = ResultParser(strict=True)   # duplicated
    with pytest.raises(ValueError):
        parser.parse("not json")
```

**Correct (fixture):**

```python
import pytest

@pytest.fixture
def strict_parser() -> ResultParser:
    return ResultParser(strict=True)


def test_parse_valid(strict_parser: ResultParser):
    assert strict_parser.parse('{"label":"boat"}') is not None


def test_parse_invalid(strict_parser: ResultParser):
    with pytest.raises(ValueError):
        strict_parser.parse("not json")
```

**Fixture with teardown (yield):**

```python
@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection(TEST_DB_URL)
    yield conn
    conn.close()      # teardown runs after all tests in scope finish
```

Reference: [pytest fixtures docs](https://docs.pytest.org/en/stable/how-to/fixtures.html)
