---
name: code-formatting
description: >
  SEA.AI code formatting and linting conventions. Use when writing, reviewing, or refactoring
  Python, C, C++, or CUDA code. Checks the repository for ruff and clang-format configurations
  and applies the relevant formatting standards.
---

# Code Formatting & Linting

## How to Use

Before writing or reviewing code, check the repository for formatting configurations:

- **Python (Ruff):** Look for `ruff.toml`, `.ruff.toml`, or `[tool.ruff]` in `pyproject.toml`
- **C/C++/CUDA (clang-format):** Look for `.clang-format` or `_clang-format`

Only apply the sections below that match configurations found in the current repository.

---

## Python (Ruff)

### Python 3.6 Compatibility

All code MUST be compatible with **Python 3.6**. Avoid these post-3.6 features:

- **Type hints** — use `typing` generics (`List`, `Dict`, `Optional`, `Union`, `Tuple`), not built-in generics (`list[str]`) or `X | Y` union syntax. Do not use `from __future__ import annotations`.
- **Syntax** — no walrus operator (`:=`), no `match`/`case`, no positional-only params (`/`), no `dict | dict` merge operator.
- **Stdlib** — no `TypedDict`, `Protocol`, `Literal` (use `typing_extensions` if needed), no `str.removeprefix`/`removesuffix`, no `zoneinfo` (use `pytz`).

```python
# good (Python 3.6)
from typing import Dict, List, Optional

def process(items: List[str], config: Optional[Dict[str, int]] = None) -> bool:
    ...

# bad (3.9+ / 3.10+)
def process(items: list[str], config: dict[str, int] | None = None) -> bool:
    ...
```

### Formatting

- **Line length:** 120 characters
- **Indent:** 4 spaces (no tabs)
- **Quotes:** Double quotes (`"`)
- **Trailing commas:** Keep them (magic trailing comma is respected)
- **Docstring code:** Formatted, dynamic line length

```python
# good
result = some_function(
    "argument_one",
    "argument_two",
    "argument_three",
)

# bad - single quotes, no trailing comma
result = some_function(
    'argument_one',
    'argument_two',
    'argument_three'
)
```

### Imports

Imports are sorted by **isort** (via Ruff `I` rules). Additional rules:

- **Absolute imports only** — no relative imports
- **`TYPE_CHECKING` blocks** — imports used only for type hints go inside `if TYPE_CHECKING:`
- Top-of-file import position is not enforced to allow lazy loading
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

### Naming

PEP 8 naming:

- **Functions / methods:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_CASE`
- **Dummy variables:** Prefix with `_`

Exception: single-letter matrix/tensor names (`K`, `R`, `H`, `T`, `P`, `B`, `C`, `W`, `G` and
their prefixed variants like `R_x`, `Hk_world`) are allowed for mathematical code.

### Docstrings

Google-style docstrings with triple double quotes.

**Function docstring:**

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

**Class docstring:**

```python
class CameraCalibration:
    """Handles camera intrinsic and extrinsic calibration parameters.

    Provides methods to project 3D points into image coordinates and
    undistort captured images.

    Attributes:
        K: The 3x3 intrinsic camera matrix.
        dist_coeffs: Distortion coefficients as a (5,) array.
        image_size: Tuple of (width, height) in pixels.

    Example:
        >>> calib = CameraCalibration.from_file("camera.yaml")
        >>> pixel = calib.project(point_3d)
    """
```

**Function with Raises and detailed Args:**

```python
def load_detections(
    path: str,
    min_confidence: float = 0.5,
) -> List[Dict[str, Any]]:
    """Load detection results from a JSON file.

    Reads a JSON file containing object detections, filters by confidence
    threshold, and returns the remaining detections sorted by score.

    Args:
        path: Path to the JSON detections file.
        min_confidence: Minimum confidence score to keep a detection.
            Defaults to 0.5.

    Returns:
        List of detection dictionaries, each containing keys
        ``bbox``, ``class_id``, and ``score``.

    Raises:
        FileNotFoundError: If the detections file does not exist.
        ValueError: If ``min_confidence`` is not in [0, 1].
    """
```

Test files and notebooks are exempt from most docstring rules.

### Type Annotations

Type annotations are required on function signatures.
Test files are exempt from parameter and return type annotations.

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

### Code Quality

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

### Verification

Before considering Python code complete, run:

```bash
ruff check --fix <files>
ruff format <files>
```

---

## C/C++/CUDA (clang-format)

When a `.clang-format` file is present in the repository, apply it to all C, C++, and CUDA source files.

Consult the `.clang-format` file at the repository root for the full configuration.

### Verification

```bash
clang-format -i <files>
```
