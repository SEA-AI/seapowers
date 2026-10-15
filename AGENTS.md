# Contributing to Seapowers

## Adding Skills and Plugins

See the [Claude Code Plugin Marketplaces documentation](https://code.claude.com/docs/en/plugin-marketplaces) for detailed instructions.

## Quick Checklist

When adding skills, agents, or plugins:
- [ ] Create the component in the appropriate directory
- [ ] Update `README.md` with a description of what was added
- [ ] Bump `version` in `.claude-plugin/plugin.json`, the only version in the repo (semantic versioning):
  - `PATCH` (x.y.**Z**) — fixes, rewording, description tweaks, metadata-only changes
  - `MINOR` (x.**Y**.0) — new skills, new features, additive changes
  - `MAJOR` (**X**.0.0) — breaking changes, removed skills, incompatible API changes
- [ ] Don't add a `version` to `.claude-plugin/marketplace.json`; Claude Code reads it from `plugin.json` (CI enforces this)
- [ ] Test locally before creating a PR

## Skills That Ship Code

- Python scripts declare dependencies inline (PEP 723) and run with `uv run`; follow the `python-best-practices` skill.
- Before committing: `uvx ruff format`, `uvx ruff check`, and type-check each script against its own environment:
  `uv sync --script s.py && uvx ty check --python "$(uv python find --script s.py)" s.py`
  (until ty resolves PEP 723 dependencies on its own). `bash -n` for shell scripts.
- Scripts used by agents validate input up front and fail with a clear message and exit code, never a traceback.
- Comments explain what the code can't; no history of how it got there.
- Keep skill content generic (no product names, IPs or UI selectors); when a request isn't covered, stop and ask.
- Never copy secrets found in logs or files; flag them and advise rotation.
- Before the PR: run the skill end to end, including its failure paths, then a `/code-review` pass.

## Key Files

- `.claude-plugin/marketplace.json` - Plugin marketplace catalog
- `.claude-plugin/plugin.json` - Plugin manifest
- `skills/` - Skill definitions (SKILL.md files)

## Resources

- [Claude Code Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - Complete guide
- [Claude Code Skills Format](https://docs.anthropic.com/en/docs/claude-code/skills) - Skills reference
