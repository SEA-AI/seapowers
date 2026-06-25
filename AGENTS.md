# Contributing to Seapowers

## Adding Skills and Plugins

See the [Claude Code Plugin Marketplaces documentation](https://code.claude.com/docs/en/plugin-marketplaces) for detailed instructions.

## Quick Checklist

When adding skills, agents, or plugins:
- [ ] Create the component in the appropriate directory
- [ ] Update `README.md` with a description of what was added
- [ ] Bump version in relevant manifest files (semantic versioning):
  - `PATCH` (x.y.**Z**) — fixes, rewording, description tweaks, metadata-only changes
  - `MINOR` (x.**Y**.0) — new skills, new features, additive changes
  - `MAJOR` (**X**.0.0) — breaking changes, removed skills, incompatible API changes
- [ ] Test locally before creating a PR

## Key Files

- `.claude-plugin/marketplace.json` - Plugin marketplace catalog
- `seapowers/.claude-plugin/plugin.json` - Plugin manifest
- `seapowers/skills/` - Skill definitions (SKILL.md files)

## Resources

- [Claude Code Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - Complete guide
- [Claude Code Skills Format](https://docs.anthropic.com/en/docs/claude-code/skills) - Skills reference
