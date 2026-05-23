---
name: python-best-practices
description: >
  Python best practices for modern projects. Use when writing, reviewing, or refactoring
  Python code to ensure correct tooling, idiomatic patterns, and sound design decisions.
  Triggers on tasks involving Python project setup (uv), testing (pytest), type annotations,
  async code, and design questions like dataclasses vs Pydantic or functions vs classes.
license: MIT
metadata:
  author: SEA.AI
  version: "1.0.0"
---

# Python Best Practices

Modern Python development guide for AI agents. Covers tooling, design decisions, testing,
types, idioms, and async — prioritized by impact to steer toward correct defaults.

## Core Philosophy

- **Explicit over implicit** — name things clearly, annotate types, avoid magic
- **Simple over clever** — the right solution is usually the boring one
- **Flat is better than nested** — early returns, small functions, no deep hierarchies
- **Boundaries get validation, internals get speed** — Pydantic at the edges, dataclasses inside

## When to Apply

Reference these guidelines when:
- Starting a new Python project or adding dependencies
- Choosing between design patterns (classes vs functions, dataclasses vs Pydantic)
- Writing or reviewing tests
- Handling async code
- Unsure about idiomatic Python

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Project Setup (uv) | CRITICAL | `setup-` |
| 2 | Design Decisions | HIGH | `design-` |
| 3 | Testing with pytest | HIGH | `test-` |
| 4 | Type Safety | HIGH | `types-` |
| 5 | Python Idioms | MEDIUM | `idiom-` |
| 6 | Async Patterns | MEDIUM | `async-` |

## Quick Reference

### 1. Project Setup with uv (CRITICAL)

- `setup-uv-commands` — Use uv for all project and dependency management
- `setup-pyproject-only` — All config lives in pyproject.toml; no requirements.txt, no setup.py
- `setup-project-layout` — Use src/ layout for installable packages; flat layout for scripts/tools

### 2. Design Decisions (HIGH)

- `design-dataclass-vs-pydantic` — Dataclasses for internal data; Pydantic at trust boundaries
- `design-functions-vs-classes` — Prefer functions; use classes only when you need shared mutable state or a clean interface
- `design-composition-over-inheritance` — Favour composition and Protocol; avoid deep class hierarchies
- `design-early-returns` — Return early to eliminate nesting; keep the happy path at the bottom

### 3. Testing with pytest (HIGH)

- `test-arrange-act-assert` — Structure every test with clear AAA sections
- `test-fixtures` — Use fixtures for shared setup; scope them correctly
- `test-parametrize` — Use `@pytest.mark.parametrize` instead of loops inside tests
- `test-no-logic` — Tests must not contain branching logic or assertions in loops
- `test-fast-and-isolated` — Tests must be fast and hermetic; mock all external I/O

### 4. Type Safety (HIGH)

- `types-always-annotate` — Annotate every function signature; skip bodies only when obvious
- `types-avoid-any` — Replace `Any` with `Unknown`, `object`, `Protocol`, or proper generics
- `types-use-protocol` — Define interfaces with `Protocol`, not base classes

### 5. Python Idioms (MEDIUM)

- `idiom-comprehensions` — Prefer comprehensions over `map`/`filter`; generator expressions for large sequences
- `idiom-context-managers` — Always use `with` for resources; write `__enter__`/`__exit__` or use `contextlib`
- `idiom-unpacking` — Use tuple unpacking and `*`-spread instead of index access

### 6. Async Patterns (MEDIUM)

- `async-io-only` — Use `async`/`await` only for I/O-bound work; use `ProcessPoolExecutor` for CPU
- `async-gather` — Use `asyncio.gather` or `TaskGroup` for concurrent independent I/O
- `async-avoid-blocking` — Never call blocking code inside an async function

## Full Compiled Document

For all rules expanded in one document: `AGENTS.md`
