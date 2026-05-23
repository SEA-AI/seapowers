---
name: python-best-practices
description: >
  Modern Python best practices. Use when writing, reviewing, or refactoring Python code,
  setting up a project, choosing between design patterns (dataclasses vs Pydantic,
  functions vs classes), writing tests, or working with async code.
license: MIT
---

# Python Best Practices

## Working in an Existing Codebase

When you spot something that violates these guidelines, **flag it and explain why, but do not change it without explicit permission**. Unsolicited refactors break working code, inflate diffs, and waste review time. State the issue, the impact, and stop there.

## The Zen of Python

Run `python -m this`. The most actionable lines:

> Explicit is better than implicit. Simple is better than complex. Flat is better than nested. Readability counts. Errors should never pass silently. There should be one — and preferably only one — obvious way to do it.

When in doubt, ask which option reads most clearly six months from now.

## Project Setup — use the Astral stack

```bash
uv init my-project           # pyproject.toml + uv.lock + .venv
uv add httpx                 # runtime dep
uv add --dev pytest ruff ty  # dev deps
uv sync                      # install from lockfile (CI / fresh clone)
uv run pytest                # run inside managed env
```

Commit both `pyproject.toml` and `uv.lock`. Never run bare `pip install`.

`uvx` (`uv tool run`) runs a tool in a temporary isolated environment without installing it permanently — useful for one-off or CI invocations: `uvx ruff check`, `uvx ruff format`, `uvx ty check`.

**Linting & formatting — ruff:** keep config in a dedicated `ruff.toml` at the project root. Rules reference: [docs.astral.sh/ruff/rules](https://docs.astral.sh/ruff/rules/).

**Type checking — ty** (Astral, Rust-based, 10-100× faster than mypy): `uvx ty check`. Still in beta (0.0.x) — fall back to `mypy --strict` if you need plugins (Django ORM, SQLAlchemy). Rules reference: [docs.astral.sh/ty/rules](https://docs.astral.sh/ty/rules/).

## Project Layout

Both layouts are valid — ask the user which they prefer when setting up a new project:

```
my-project/
├── my_package/   ← flat (package named after project, simpler)
│   or src/       ← src layout (extra wrapper, prevents accidental imports without install)
├── tests/
├── pyproject.toml
├── ruff.toml
└── uv.lock
```

Tests always live outside the package directory.

## Design Decisions

Follow existing codebase conventions first. Introduce a different pattern only when it clearly reduces complexity — and flag it rather than applying it silently.

**Dataclasses vs Pydantic** — ask: *has this data been validated yet?*
- **No** (HTTP body, config file, env vars, anything external) → `pydantic.BaseModel`
- **Yes** (internal domain objects, data that came from your own code) → `@dataclass`

Use `frozen=True` on value objects (coordinates, IDs, measurements).

**Functions vs classes** — default to functions. Add a class only when you need shared state across calls, a concrete interface implementation, or lifecycle management (`__enter__`/`__exit__`).

**Composition over inheritance** — build behaviour by combining small focused pieces rather than extending base classes. Inherit only for genuine "is-a" relationships with shared implementation; keep hierarchies shallow.

**Return early.** Handle error/edge cases at the top with guard clauses. Keep the happy path at the bottom, unnested.

## Testing — pytest only

Stick to pytest idioms throughout. Do **not** mix in `unittest.TestCase`, `self.assert*`, or `setUp`/`tearDown` — pytest fixtures replace all of that cleanly.

Structure every test: Arrange → Act → Assert, one behaviour per test. Use fixtures for shared setup, `@pytest.mark.parametrize` for input variations, and mock all external I/O. Mark slow tests `@pytest.mark.slow`.

**Avoid:**
- Testing implementation details — test observable behaviour, not internal state; tests that mirror the implementation break on every refactor
- Over-mocking — mock at boundaries (HTTP, DB, filesystem), not deep inside your own code; excessive mocks test the mocks, not the logic
- `if` / `for` inside test bodies — a conditional assertion that never executes is a silent false positive

## Prefer Existing Libraries

Python's ecosystem is large. Before writing custom code, check if a well-maintained library already solves the problem. Prefer libraries that are:
- Part of the **stdlib** first
- Widely adopted (high download count, active maintenance, good issue tracker hygiene)
- Battle-tested over time — be cautious of libraries under a year old or with very low usage

Common reliable choices: `httpx` (HTTP), `pydantic` (validation), `click`/`typer` (CLI), `structlog` (logging), `tenacity` (retries), `rich` (terminal output), `polars`/`pandas` (data). Don't reimplement what these do well.

## Idioms

- Prefer comprehensions over `map`/`filter`; use generator expressions when you only iterate once
- Always use `with` for resources (files, connections, locks)
- Unpack tuples by name (`x, y = point`) instead of indexing (`point[0]`)
- Annotate every function signature — it documents intent and enables static analysis

## Async

- Use `async`/`await` only for I/O-bound work. CPU-bound work belongs in a `ProcessPoolExecutor`
- Run independent I/O concurrently: `asyncio.TaskGroup` (Python 3.11+, preferred) or `asyncio.gather`
- Never call blocking code inside an async function — use async equivalents or `loop.run_in_executor`
