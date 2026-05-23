# Project Layout

Two layouts are in common use. `uv init` defaults to **flat**. Ask the user which they prefer
when starting a new project — both are valid, but the choice is hard to reverse later.

## Flat layout (uv default)

```
my-project/
├── my_package/
│   ├── __init__.py
│   └── core.py
├── tests/
│   ├── conftest.py
│   └── test_core.py
├── pyproject.toml
├── ruff.toml
└── uv.lock
```

The package directory sits at the root, named after the project. Simple and requires no
special installation step to run code locally.

**Best for:** internal tools, scripts, applications, most day-to-day projects.

**Watch out for:** Python adds the current working directory to the import path, so running
code from the project root can accidentally import the local source instead of the installed
package. For most projects this doesn't matter, but it can hide packaging bugs.

## src layout

```
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── core.py
├── tests/
│   ├── conftest.py
│   └── test_core.py
├── pyproject.toml
├── ruff.toml
└── uv.lock
```

The package lives inside a `src/` wrapper. The project **must** be installed before the
package is importable (`uv sync` handles this automatically via editable install).

**Best for:** libraries and packages published to PyPI, projects where you want a hard
guarantee that tests run against the installed package, not the raw source tree.

**Key benefit:** eliminates the entire class of "works locally but fails after install" bugs
because the import path never includes the raw source.

## Rules that apply to both

- Tests always live **outside** the package directory — they are not part of the distributed package
- `conftest.py` goes in `tests/` for project-wide fixtures; add nested `conftest.py` files
  in subdirectories only for fixtures scoped to that subdirectory
- Keep scripts, notebooks, and tooling at the root — not inside the package
