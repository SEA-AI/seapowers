---
title: Use src/ Layout for Packages, Flat Layout for Scripts
impact: HIGH
impactDescription: Prevents import confusion; ensures installed package is tested
tags: setup, layout, project-structure, imports
---

## Use src/ Layout for Packages, Flat Layout for Scripts

**src/ layout** — use when the project is an installable package or library:

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
├── pyproject.toml
└── uv.lock
```

The `src/` wrapper prevents the package from being importable without installation,
which catches "works on my machine" import bugs during testing.

**Flat layout** — acceptable for scripts, CLIs, and internal tooling not published to PyPI:

```
my-tool/
├── my_tool/
│   ├── __init__.py
│   └── main.py
├── tests/
├── pyproject.toml
└── uv.lock
```

**In both cases:** keep tests outside the package directory, never inside it.
Tests are not part of the distributed package.

Reference: [Packaging Python projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
