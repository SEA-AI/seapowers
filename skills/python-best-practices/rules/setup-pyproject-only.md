---
title: All Config in pyproject.toml — No requirements.txt or setup.py
impact: CRITICAL
impactDescription: Single source of truth for deps, tools, and metadata
tags: setup, pyproject, configuration, tooling
---

## All Config in pyproject.toml — No requirements.txt or setup.py

`pyproject.toml` is the modern standard (PEP 517/518/621). All dependency declarations, tool
configuration (ruff, mypy, pytest), and package metadata live here. Adding `requirements.txt`
or `setup.py` alongside it creates a second source of truth that drifts.

**Incorrect (legacy split config):**

```
requirements.txt
requirements-dev.txt
setup.py
.flake8
mypy.ini
pytest.ini
```

**Correct (single file):**

```toml
# pyproject.toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27"]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.4", "mypy>=1.10"]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Configure ruff, mypy, and pytest in `pyproject.toml`, not in separate files.

Reference: [pyproject.toml spec](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
