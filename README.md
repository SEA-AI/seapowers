# superpowers

[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-7c3aed?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQyIDAtOC0zLjU4LTgtOHMzLjU4LTggOC04IDggMy41OCA4IDgtMy41OCA4LTggOHoiLz48L3N2Zz4=&style=flat-square)](https://docs.anthropic.com/en/docs/claude-code/skills)
[![Skills](https://img.shields.io/badge/Skills-2-blue?style=flat-square)](#available-skills)
[![Upstream Sync](https://img.shields.io/github/actions/workflow/status/SEA-AI/superpowers/sync-upstream-skills.yml?label=Upstream%20Sync&style=flat-square)](https://github.com/SEA-AI/superpowers/actions/workflows/sync-upstream-skills.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

✨ **Shared Claude Code skills, prompts, and workflows for the SEA.AI team** ✨

## 🧩 Available Skills

| Skill | Description | Source |
|-------|-------------|--------|
| 📝 `pull-request` | SEA.AI PR template with What/Why/How/Testing sections | Internal |
| ⚛️ `react-best-practices` | React & Next.js performance optimization (57 rules across 8 categories) | [Vercel Labs](https://github.com/vercel-labs/agent-skills) |

## 💡 What are Skills?

Claude Code skills are reusable prompt-based instructions that standardize how AI assists with common development tasks — think of them as muscle memory for your AI pair programmer. Instead of every developer explaining the same context over and over, skills encode team knowledge once and share it everywhere.

## 📁 Repository Structure

```
superpowers/
├── .claude-plugin/
│   ├── marketplace.json              # Makes it installable
│   └── plugin.json                   # Plugin metadata
├── .github/
│   └── workflows/
│       └── sync-upstream-skills.yml  # Weekly upstream sync
├── skills/
│   └── my-skill/
│       └── SKILL.md
├── upstream-skills.json              # Manifest of vendored upstream skills
└── README.md
```

## 🚀 Installation

### Install globally (all projects)

Run these commands inside Claude Code:

```
/plugin marketplace add sea-ai/superpowers
/plugin install superpowers@sea-ai-superpowers
```

> [!TIP]
> After installing, run `/plugin marketplace` and enable **auto-update** for the `sea-ai-superpowers` marketplace so you automatically get new skills as they're added.

This writes the following to your `~/.claude/settings.json` — you can also add it manually:

```json
{
  "extraKnownMarketplaces": {
    "sea-ai-superpowers": {
      "source": {
        "source": "github",
        "repo": "SEA-AI/superpowers"
      }
    }
  },
  "enabledPlugins": {
    "superpowers@sea-ai-superpowers": true
  }
}
```

### Install per-project

Add this to your **project's** `.claude/settings.json` so every team member gets the skills automatically when working in that repo:

```json
{
  "extraKnownMarketplaces": {
    "sea-ai-superpowers": {
      "source": {
        "source": "github",
        "repo": "SEA-AI/superpowers"
      }
    }
  },
  "enabledPlugins": {
    "superpowers@sea-ai-superpowers": true
  }
}
```

### Enable only specific skills

If you only need certain skills, pass an array of skill names instead of `true` (works in both global and project settings):

```json
{
  "enabledPlugins": {
    "superpowers@sea-ai-superpowers": ["react-best-practices"]
  }
}
```

## 🔄 Upstream Syncing

Some skills are vendored from external repos. Instead of fetching at runtime, we keep a local copy that's automatically synced via a weekly GitHub Action.

The manifest lives in `upstream-skills.json` and supports two entry types:

**Directory entry** — syncs an entire directory from an upstream repo using a tarball download + rsync:

```json
{
  "name": "react-best-practices",
  "type": "directory",
  "repo": "vercel-labs/agent-skills",
  "branch": "main",
  "src": "skills/react-best-practices",
  "dest": "skills/react-best-practices",
  "license": "MIT",
  "upstream_repo": "https://github.com/vercel-labs/agent-skills"
}
```

**File entry** — syncs a single file via its raw URL (the default when `type` is omitted):

```json
{
  "name": "my-skill",
  "url": "https://raw.githubusercontent.com/owner/repo/main/path/to/SKILL.md",
  "dest": "skills/my-skill/SKILL.md",
  "license": "MIT",
  "upstream_repo": "https://github.com/owner/repo"
}
```

The [sync workflow](.github/workflows/sync-upstream-skills.yml) runs weekly and opens a PR when upstream content changes. To add a new upstream skill, append an entry to the manifest using the appropriate format.

## 🤝 Contributing

### Adding a Skill

1. Create a new directory in `skills/` with a `SKILL.md` file
2. Follow the [skill format](https://docs.anthropic.com/en/docs/claude-code/skills) from the Claude Code docs
3. Open a PR and let the team review

Got a workflow that saves you time? A prompt pattern that keeps Claude on track? Ship it! The bar is low — if it helped you twice, it'll help someone else too.

## 🤷 Why?

Because nobody should have to explain our deploy process to Claude from scratch every Monday morning.
