# Project Layout

Two layouts are in common use. `uv init` defaults to **flat**. Ask the user which they prefer
when starting a new project — both are valid, but the choice is hard to reverse later.

## Flat layout (uv default)

```text
my-project/
├── my_package/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── pyproject.toml
├── ruff.toml
├── ty.toml
└── uv.lock
```

The package directory sits at the root, named after the project. Simple and requires no
special installation step to run code locally.

**Best for:** internal tools, scripts, applications, most day-to-day projects.

**Watch out for:** Python includes the current working directory as the first item on the
import path. Running code from the project root can accidentally import the local source
instead of the installed package, which can hide packaging bugs.
([source](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/))

## src layout

```text
my-project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
├── pyproject.toml
├── ruff.toml
├── ty.toml
└── uv.lock
```

The package lives inside a `src/` wrapper. The project **must** be installed before the
package is importable (`uv sync` handles this automatically via editable install).

**Best for:** libraries and packages published to PyPI, projects where you want a hard
guarantee that tests run against the installed package, not the raw source tree.

**Key benefit:** keeps import packages in a directory separate from the root, ensuring the
installed copy is always used — not the raw source tree.
([source](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/))

## Rules that apply to both

- Tests always live **outside** the package directory — they are not part of the distributed package
- Keep scripts, notebooks, and tooling at the root — not inside the package
