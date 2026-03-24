# Contributing to Superpowers

Guidelines for adding skills, plugins, and agents to the superpowers marketplace.

## Adding a Skill

Skills are reusable prompt-based instructions that Claude Code uses for common development tasks.

### Steps

1. **Create the skill directory and file:**
   ```bash
   mkdir -p skills/my-skill
   touch skills/my-skill/SKILL.md
   ```

2. **Write the skill** following the [Claude Code skill format](https://docs.anthropic.com/en/docs/claude-code/skills)

3. **Update README.md:**
   Add your skill to the Skills table in the "Available Skills and Plugins" section

4. **Create a PR:**
   - Create a new branch: `git checkout -b claude/add-my-skill`
   - Commit with message: `Add my-skill`
   - Create a PR with description of what the skill does and when to use it

## Adding a Plugin

Plugins integrate external tools and services with Claude Code. There are three types:

### Local Plugin (Bundled in this repo)

1. **Create plugin files** in `.claude-plugin/` directory alongside the marketplace.json

2. **Update marketplace.json:**
   ```json
   {
     "name": "my-plugin",
     "source": "./.claude-plugin/",
     "description": "What this plugin does",
     "version": "1.0.0",
     "author": { "name": "Author Name" },
     "license": "MIT",
     "keywords": ["keyword1", "keyword2"]
   }
   ```

3. **Update plugin.json** with plugin metadata

4. **Update README.md** with the new plugin in the Plugins table

### Remote GitHub Plugin

1. **Update marketplace.json** with proper GitHub object format:
   ```json
   {
     "name": "my-plugin",
     "source": {
       "source": "github",
       "repo": "owner/repo-name"
     },
     "description": "What this plugin does",
     "version": "1.0.0",
     "author": { "name": "Author Name" },
     "license": "MIT",
     "keywords": ["keyword1", "keyword2"]
   }
   ```

2. **Update README.md** with the new plugin

3. **Important:** Always use the object format (`{ "source": "github", "repo": "..." }`) for remote plugins, not string URLs. The marketplace schema does not accept full URLs.

### Upstream/Vendored Plugin

For plugins that should be synced from external repositories:

1. **Add entry to upstream-skills.json:**
   ```json
   {
     "name": "plugin-name",
     "type": "directory",
     "repo": "owner/repo",
     "branch": "main",
     "src": "path/in/repo",
     "dest": "skills/plugin-name",
     "license": "MIT",
     "upstream_repo": "https://github.com/owner/repo"
   }
   ```

2. **The sync workflow** will automatically pull and update this content weekly

## Version Bumping

When making changes:

1. **Update version numbers** in:
   - `.claude-plugin/plugin.json` (for the main superpowers plugin)
   - `.claude-plugin/marketplace.json` (for the plugin entry and marketplace metadata)
   - Any individual plugin's version field

2. **Use semantic versioning:**
   - `MAJOR.MINOR.PATCH` (e.g., 1.0.1)
   - PATCH: bug fixes
   - MINOR: new features, backwards compatible
   - MAJOR: breaking changes

3. **Include version bump in your commit:**
   ```bash
   git commit -m "Add feature and bump version to 1.0.2"
   ```

## PR Requirements

Every PR should include:

1. **Clear title** describing the change
2. **What section:** Explain what was added/changed
3. **Why section:** Explain the motivation
4. **How section:** Describe the implementation
5. **Testing section:** How to verify the change works
6. **Version bump** (if adding new features/fixes)

### Example PR

```markdown
## What?
Adds my-skill for faster development workflow

## Why?
Saves 10 minutes per deployment by automating the common steps

## How?
- Created skills/my-skill/SKILL.md
- Updated README.md with new skill in table
- Bumped version from 1.0.0 to 1.0.1

## Testing
Run `/my-skill` in Claude Code to see it in action
```

## Marketplace Schema Validation

The marketplace.json file has strict schema validation. Key rules:

- **Source field formats:**
  - Local: `"source": "./.claude-plugin/"`
  - GitHub: `"source": { "source": "github", "repo": "owner/repo" }`
  - URL: `"source": { "source": "url", "url": "https://..." }`
  - ❌ Do NOT use: `"source": "https://github.com/owner/repo"` (plain string URLs fail)

- **Required fields per plugin:**
  - `name`: unique identifier
  - `source`: where to find the plugin
  - `description`: what it does
  - `version`: semantic version
  - `author`: who created it
  - `license`: license type
  - `keywords`: search terms

## Common Pitfalls

1. **Wrong source format:** Use object format `{ "source": "github", "repo": "..." }` for GitHub, not string URLs
2. **Forgetting to update versions:** Always bump versions when making changes
3. **Missing README updates:** Add new skills/plugins to the README table
4. **Incomplete PR descriptions:** Use the What/Why/How/Testing format

## Directory Structure

```
superpowers/
├── .claude-plugin/
│   ├── marketplace.json          # Plugin definitions & marketplace metadata
│   ├── plugin.json               # Main superpowers plugin config
│   └── (plugin files)
├── .github/
│   └── workflows/
│       └── sync-upstream-skills.yml
├── skills/
│   └── skill-name/
│       └── SKILL.md              # Skill definition
├── upstream-skills.json          # External skill sources
├── CLAUDE.md                      # This file
└── README.md
```

## Questions?

- Check the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- Review existing skills/plugins in this repo for examples
- Ask the team in a PR review
