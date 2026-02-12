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
├── skills/
│   └── my-skill/
│       └── SKILL.md
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

## Contributing

### Adding a Skill

1. Create a new directory in `skills/` with a `SKILL.md` file
2. Follow the [skill format](https://docs.anthropic.com/en/docs/claude-code/skills) from the Claude Code docs
3. Open a PR and let the team review

Got a workflow that saves you time? A prompt pattern that keeps Claude on track? Ship it! The bar is low — if it helped you twice, it'll help someone else too.

## Why?

Because nobody should have to explain our deploy process to Claude from scratch every Monday morning.
