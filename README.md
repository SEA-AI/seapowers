# ai-skills

> _Teaching our AI assistants to sail the SEA.AI way._

A shared collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills, prompts, and workflows used across the SEA.AI organization — distributed as a Claude Code plugin.

## What are Skills?

Claude Code skills are reusable prompt-based instructions that standardize how AI assists with common development tasks — think of them as muscle memory for your AI pair programmer. Instead of every developer explaining the same context over and over, skills encode team knowledge once and share it everywhere.

## Repository Structure

```
ai-skills/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # Makes it installable
├── .github/
│   └── workflows/
│       └── sync-upstream-skills.yml  # Weekly upstream sync
├── skills/
│   └── my-skill/
│       └── SKILL.md
├── upstream-skills.json     # Manifest of vendored upstream skills
└── README.md
```

## Installation

### One-time setup

Add the marketplace and install the plugin:

```
/plugin marketplace add SEA-AI/ai-skills
/plugin install ai-skills@sea-ai-skills
```

### Pre-configure for a project

Add this to your project's `.claude/settings.json` so every team member gets the skills automatically:

```json
{
  "extraKnownMarketplaces": {
    "sea-ai-skills": {
      "source": {
        "source": "github",
        "repo": "SEA-AI/ai-skills"
      }
    }
  },
  "enabledPlugins": {
    "ai-skills@sea-ai-skills": true
  }
}
```

### Enable only specific skills

If you only need certain skills in a project, pass an array of skill names instead of `true`:

```json
{
  "enabledPlugins": {
    "ai-skills@sea-ai-skills": ["react-best-practices"]
  }
}
```

## Available Skills

| Skill | Description | Source |
|-------|-------------|--------|
| `pull-request` | SEA.AI PR template with What/Why/How/Testing sections | Internal |
| `react-best-practices` | React & Next.js performance optimization (57 rules across 8 categories) | [Vercel Labs](https://github.com/vercel-labs/agent-skills) |

## Upstream Syncing

Some skills are vendored from external repos. Instead of fetching at runtime, we keep a local copy that's automatically synced via a weekly GitHub Action.

The manifest lives in `upstream-skills.json`:

```json
[
  {
    "name": "react-best-practices",
    "url": "https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/react-best-practices/SKILL.md",
    "dest": "skills/react-best-practices/SKILL.md",
    "license": "MIT",
    "upstream_repo": "https://github.com/vercel-labs/agent-skills"
  }
]
```

To add a new upstream skill, append an entry with the raw URL and local destination. The [sync workflow](.github/workflows/sync-upstream-skills.yml) runs weekly and opens a PR when upstream content changes.

## Contributing

### Adding a Skill

1. Create a new directory in `skills/` with a `SKILL.md` file
2. Follow the [skill format](https://docs.anthropic.com/en/docs/claude-code/skills) from the Claude Code docs
3. Open a PR and let the team review

Got a workflow that saves you time? A prompt pattern that keeps Claude on track? Ship it! The bar is low — if it helped you twice, it'll help someone else too.

## Why?

Because nobody should have to explain our deploy process to Claude from scratch every Monday morning.
