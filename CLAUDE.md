# Contributing to Superpowers

Quick guide for adding skills and plugins to this marketplace.

## Adding a Skill

1. Create directory: `mkdir -p skills/my-skill`
2. Create `skills/my-skill/SKILL.md` following [Claude Code skill format](https://docs.anthropic.com/en/docs/claude-code/skills)
3. Update README.md: Add to Skills table
4. Create PR: Branch `claude/add-my-skill`, bump version

## Adding a Plugin

### Local Plugin (in this repo)

1. Create directory: `mkdir -p .claude-plugin/plugins/my-plugin`
2. Add `plugin.json`:
   ```json
   {
     "name": "my-plugin",
     "description": "What it does",
     "version": "1.0.0"
   }
   ```
3. Add entry to `marketplace.json` plugins array:
   ```json
   {
     "name": "my-plugin",
     "source": "./plugins/my-plugin",
     "description": "What it does"
   }
   ```

### Remote GitHub Plugin

Add to `marketplace.json` plugins array:
```json
{
  "name": "my-plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo"
  },
  "description": "What it does"
}
```

**Important:** Use object format for GitHub, never plain URLs.

## Version Bumping

Update versions in `plugin.json` and `marketplace.json` when making changes. Use semantic versioning (MAJOR.MINOR.PATCH).

## PR Template

```markdown
## What?
Brief description of change

## Why?
Motivation or problem solved

## How?
- List of changes made
- Version bumped to X.X.X

## Testing
How to verify it works
```

## Key Files

- `.claude-plugin/marketplace.json` - Plugin catalog
- `.claude-plugin/plugin.json` - Main plugin config
- `skills/` - Skill definitions (SKILL.md files)
- `upstream-skills.json` - External skill sources

## Schema Rules

**marketplace.json required fields:** `name`, `owner` (with name)
**Plugin entry required fields:** `name`, `source` (path or object)
**Source formats:**
- Local: `"./plugins/my-plugin"`
- GitHub: `{ "source": "github", "repo": "owner/repo" }`
- Git URL: `{ "source": "url", "url": "https://..." }`

## Resources

- [Claude Code Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code Skills Format](https://docs.anthropic.com/en/docs/claude-code/skills)
