---
name: generate-claude-md
description: >
  Analyze a codebase to generate or update the root CLAUDE.md file with project
  conventions, architecture, and dev workflows. Use when initializing a project
  or when config files have changed.
---

# Generate CLAUDE.md

Analyze this codebase to generate or update the root `CLAUDE.md` for guiding AI coding agents.

## Step 1: Detect

Run glob searches for:

**Config files:**
- `**/pyproject.toml`, `**/ruff.toml`, `**/.ruff.toml`, `**/.clang-format`, `**/.pre-commit-config.yaml`
- `**/tsconfig.json`, `**/.eslintrc*`, `**/package.json`
- `**/meson.build`, `**/CMakeLists.txt`, `**/Makefile`

**Existing AI instruction files:**
- `**/{CLAUDE.md,AGENTS.md,.github/copilot-instructions.md,.cursorrules,.windsurfrules,README.md,CONTRIBUTING.md,CODING_STANDARDS.md}`

Read every file found. If a root `CLAUDE.md` already exists, read it — you will merge into it later.

## Step 2: Analyze

### Architecture

- Identify primary language(s) and framework(s)
- Map major components/modules from the directory structure
- Note service boundaries and key design decisions

### Development Workflows

Extract from config files:
- Build commands (Makefile, meson.build, CMakeLists.txt, package.json scripts)
- Test commands (pyproject.toml pytest config, package.json scripts)
- Lint/format commands (pre-commit, ruff, eslint)

Only include commands that aren't obvious from file inspection alone.

### Coding Conventions (3-Tier)

**From config** `✅`
- Line length, indentation, quote style
- Enabled/disabled linter rules
- Docstring convention (e.g. ruff `pydocstyle.convention`)
- Python/Node version requirements
- Excluded/ignored paths
- Test file naming patterns

**Default standard (fallback)** `📚`
Only when config is sparse:
- PEP 8 / PEP 257 for Python
- C++ Core Guidelines for C++
- Standard JS/TS conventions

**Mark every convention with its source emoji.**

### Project-Specific Overrides

If the project is **Core-Backend**, **always** add these Python 3.6 compatibility rules — regardless of what `python_requires` says in pyproject.toml. The deployment target requires Python 3.6 compatibility:
- No walrus operator `:=` (3.8+)
- No `X | Y` union syntax (3.10+) — use `Union[X, Y]` / `Optional[X]` from `typing`
- No `f"{x=}"` debug format strings (3.8+)
- No `dict1 | dict2` merge operator (3.9+)
- No `dataclasses` (3.7+)
- No positional-only parameters with `/` (3.8+)

## Step 3: Present Findings

Before writing anything, present a structured summary to the user:
- Architecture overview
- Detected workflows
- Conventions (grouped by tier with emoji markers)
- Project-specific overrides (if any)

**Ask the user to confirm or adjust before proceeding.**

## Step 4: Generate or Update

### New file (no CLAUDE.md exists)

Write root `CLAUDE.md` with these sections:

```
# Project Overview
# Architecture
# Development Workflows
# Coding Conventions
# Testing
```

### Update (CLAUDE.md already exists)

- Preserve manually written sections
- Update or add detected conventions
- Do not remove content the user added manually
- Show the user a diff of what changed

## General Rules

Always include these in the generated CLAUDE.md:

### Docstrings

- Minimal — only when the function isn't self-explanatory
- Do not pollute code with unnecessary docstrings
- Prefer clean, self-documenting names over docstrings
- If a docstring convention is detected from config, include one short example:

```python
# Example (if google style detected from config):
def calculate_offset(index, base):
    """Calculate memory offset from index.

    Args:
        index: Zero-based element index.
        base: Starting memory address.

    Returns:
        Absolute memory offset.
    """
```

### Testing (pytest)

- Tests are first-class code — treat them with the same priority and care as production code
- Every test must be meaningful. Never generate random test cases just to hit coverage numbers
- Keep tests small, focused, and modular — each test should test one behavior
- Avoid large mock setups — if heavy mocking is needed, the code likely needs refactoring
- Prefer fixtures over inline setup
- Test names should describe the behavior being tested
