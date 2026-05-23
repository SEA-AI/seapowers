---
title: Use uv for All Project and Dependency Management
impact: CRITICAL
impactDescription: Reproducible environments, 10-100× faster installs
tags: setup, uv, dependencies, tooling
---

## Use uv for All Project and Dependency Management

`uv` replaces `pip`, `venv`, `pip-tools`, and `poetry` in one fast tool. Never use `pip install` directly in a project — it bypasses the lockfile and breaks reproducibility.

**Core commands:**

```bash
uv init my-project          # create new project with pyproject.toml + .venv
uv add requests             # add runtime dependency (updates pyproject.toml + uv.lock)
uv add --dev pytest ruff    # add dev-only dependency
uv remove requests          # remove dependency
uv sync                     # install all deps from lockfile (CI / fresh clone)
uv run pytest               # run command inside the managed environment
uv run python script.py     # run a script without activating venv manually
uv lock --upgrade            # upgrade all deps and regenerate lockfile
```

**Never do this:**

```bash
pip install requests        # bypasses uv lockfile
python -m venv .venv && pip install -r requirements.txt  # manual venv workflow
```

Commit both `pyproject.toml` and `uv.lock`. The lockfile pins exact versions for reproducible installs across machines.

Reference: [uv Projects guide](https://docs.astral.sh/uv/guides/projects/)
