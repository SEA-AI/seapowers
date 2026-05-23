---
name: python-best-practices
description: >
  Modern Python best practices. Use when writing, reviewing, or refactoring Python code,
  setting up a project, choosing between design patterns (dataclasses vs Pydantic,
  functions vs classes), writing tests, or working with async code.
license: MIT
---

# Python Best Practices

## Project Setup — always use uv

```bash
uv init my-project          # new project (creates pyproject.toml + uv.lock + .venv)
uv add httpx                # add runtime dep
uv add --dev pytest ruff mypy  # add dev deps
uv sync                     # install from lockfile (CI / fresh clone)
uv run pytest               # run inside managed env
```

- Never run bare `pip install`. Commit both `pyproject.toml` **and** `uv.lock`.
- All tool config (ruff, mypy, pytest) goes in `pyproject.toml` — no separate `.flake8`, `mypy.ini`, `pytest.ini`.
- Use `src/` layout for installable packages; flat layout is fine for internal tools.

## Design Decisions

**Dataclasses vs Pydantic** — ask: *has this data been validated yet?*
- **No** (external input: HTTP body, config file, env vars) → `pydantic.BaseModel` — it validates and coerces
- **Yes** (internal domain objects, already-clean data) → `@dataclass` — fast, zero overhead, works with mypy

Use `frozen=True` on dataclasses that represent value objects (coordinates, IDs, measurements).

**Functions vs Classes** — default to functions. Add a class only when you need:
1. Shared mutable state across multiple calls
2. A concrete implementation of a `Protocol`
3. Lifecycle management (`__enter__`/`__exit__`)

**Composition over inheritance** — define interfaces with `typing.Protocol` (structural typing, no coupling). Avoid deep class hierarchies; cap inheritance at one level.

**Return early** — handle error/edge cases at the top with guard clauses. Keep the happy path at the bottom, unnested.

## Testing — pytest

- Structure every test: **Arrange → Act → Assert**, one behaviour per test.
- Name tests after behaviour: `test_<what>_when_<condition>_returns_<expected>`.
- Use **fixtures** for shared setup; scope them (`function` / `module` / `session`) to avoid recreating expensive objects.
- Use `@pytest.mark.parametrize` for input variations — never loop inside a test.
- No `if` or `for` inside test bodies. A conditional assertion that never runs is a silent false positive.
- Mock all external I/O (`monkeypatch` or `unittest.mock`). Mark slow tests `@pytest.mark.slow`.

## Type Safety

- Annotate every function signature (parameters + return type). Run `mypy --strict`.
- Avoid `Any` — it silently disables type checking for everything it touches. Use `object`, a `Protocol`, or a `TypedDict` instead.
- Use `typing.Protocol` to define interfaces; it requires no imports in implementing classes and makes test doubles trivial.

## Python Idioms

- Prefer list/dict/set comprehensions over `map`/`filter`. Use generator expressions (`sum(x for x in ...)`) when you only iterate once.
- Always use `with` for resources (files, connections, locks). Use `contextlib.contextmanager` to write your own.
- Unpack tuples by name (`x, y = point`) instead of indexing (`point[0]`).

## Async

- Use `async`/`await` only for **I/O-bound** work. For CPU-bound work use `ProcessPoolExecutor`.
- Run independent I/O concurrently: `asyncio.TaskGroup` (Python 3.11+, preferred) or `asyncio.gather`.
- Never call blocking code inside an async function (`time.sleep`, `requests.get`, synchronous file I/O). Use async equivalents or `loop.run_in_executor`.
