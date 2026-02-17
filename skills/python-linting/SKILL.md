---
name: python-linting
description: >
  SEA.AI Python formatting and linting conventions based on Ruff. Use when writing,
  reviewing, or refactoring Python code to produce Ruff-compliant output on the first pass.
  Triggers on any task involving Python code in SEA.AI repositories.
---

# Python Linting & Formatting

SEA.AI Python projects use **Ruff** as the single linter and formatter. The canonical config
is synced weekly from Core-Backend into `ruff.toml` alongside this skill. When in doubt,
consult that file for the full rule set.

## Python Version Compatibility

All code MUST be compatible with **Python 3.6**. Avoid these post-3.6 features:

- **Type hints** — use `typing` generics (`List`, `Dict`, `Optional`, `Union`, `Tuple`), not built-in generics (`list[str]`) or `X | Y` union syntax. Do not use `from __future__ import annotations`.
- **Syntax** — no walrus operator (`:=`), no `match`/`case`, no positional-only params (`/`), no `dict | dict` merge operator.
- **Stdlib** — no `dataclasses`, `TypedDict`, `Protocol`, `Literal` (use `typing_extensions` if needed), no `str.removeprefix`/`removesuffix`, no `zoneinfo` (use `pytz`).

```python
# good (Python 3.6)
from typing import Dict, List, Optional

def process(items: List[str], config: Optional[Dict[str, int]] = None) -> bool:
    ...

# bad (3.9+ / 3.10+)
def process(items: list[str], config: dict[str, int] | None = None) -> bool:
    ...
```

## Formatting

- **Line length:** 120 characters
- **Indent:** 4 spaces (no tabs)
- **Quotes:** Double quotes (`"`)
- **Trailing commas:** Keep them (magic trailing comma is respected)
- **Docstring code:** Formatted, dynamic line length

```python
# good
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# bad - single quotes, no trailing comma
result = some_function(
    argument_one,
    argument_two,
    argument_three
)
```

## Imports

Imports are sorted by **isort** (via Ruff `I` rules). Additional rules:

- **Absolute imports only** — no relative imports (`TID252`)
- **`TYPE_CHECKING` blocks** — imports used only for type hints go inside `if TYPE_CHECKING:` (`TC` rules)
- Top-of-file import position is not enforced (`E402` ignored) to allow lazy loading
- **Use `typing` module generics** — `List`, `Dict`, `Tuple`, `Optional`, `Union` from `typing`, not built-in generics

```python
# good
import logging
from typing import TYPE_CHECKING, Dict, List, Optional

from core.module import MyClass

if TYPE_CHECKING:
    from core.other import HeavyType

# bad - relative import
from .module import MyClass
```

## Naming

PEP 8 naming is enforced (`N` rules):

- **Functions / methods:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_CASE`
- **Dummy variables:** Prefix with `_`

Exception: single-letter matrix/tensor names (`K`, `R`, `H`, `T`, `P`, `B`, `C`, `W`, `G` and
their prefixed variants like `R_x`, `Hk_world`) are allowed for mathematical code.

## Docstrings

Google-style docstrings (`convention = "google"`):

- Use triple double quotes (`"""`) (`D300`)
- Do not repeat the function signature in the first line (`D402`)
- Document all parameters, and parameter names must match the signature (`D417`)

```python
def transform_point(point: np.ndarray, T: np.ndarray) -> np.ndarray:
    """Transform a 3D point using a transformation matrix.

    Args:
        point: A 3D point as a (3,) array.
        T: A 4x4 transformation matrix.

    Returns:
        The transformed 3D point.
    """
```

Test files (`tests/*`) and notebooks (`*.ipynb`) are exempt from most docstring rules.

## Type Annotations

Type annotations are required on function signatures (`ANN` rules).
Test files are exempt from `ANN001` (parameter annotations) and `ANN201` (return type).

Always use `typing` module generics for Python 3.6 compatibility:

```python
# good (Python 3.6)
from typing import Dict, List, Optional, Tuple, Union

def compute_distance(a: np.ndarray, b: np.ndarray) -> float:
    ...

def get_items(ids: List[int]) -> Dict[int, str]:
    ...

def maybe_load(path: Optional[str] = None) -> Union[np.ndarray, None]:
    ...

# bad - missing annotations
def compute_distance(a, b):
    ...
```

## Code Quality

The following rule sets catch common issues:

| Rules | What it catches | Practical guidance |
|-------|----------------|--------------------|
| `B` (bugbear) | Mutable default args, assert usage, broad exceptions | Never use `[]` or `{}` as default parameter values |
| `SIM` (simplify) | Unnecessary `if`/`else`, negated conditions, context managers | Prefer ternary expressions and `contextlib` where simpler |
| `PTH` (use-pathlib) | `os.path` / `open()` calls | Use `pathlib.Path` instead of `os.path` |
| `ERA` (eradicate) | Commented-out code | Delete dead code, don't comment it out |
| `PL` (pylint) | Complexity, too many args (max 10), too many returns (max 20) | Break up complex functions |
| `C` (complexity) | McCabe complexity | Keep functions focused and simple |
| `NPY` (numpy) | Deprecated NumPy APIs | Use modern NumPy idioms |

## Verification

Before considering Python code complete, run:

```bash
ruff check --fix <files>
ruff format <files>
```

If the project has pre-commit hooks configured, those will run both automatically on commit.
