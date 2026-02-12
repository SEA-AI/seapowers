# ai-skills

> _Teaching our AI assistants to sail the SEA.AI way._

A shared collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills, prompts, and workflows used across the SEA.AI organization.

## What are Skills?

Claude Code skills are reusable prompt-based instructions that standardize how AI assists with common development tasks — think of them as muscle memory for your AI pair programmer. Instead of every developer explaining the same context over and over, skills encode team knowledge once and share it everywhere.

## Repository Structure

```
ai-skills/
├── .claude/
│   └── skills/               # Claude Code auto-discovers skills here
│       └── my-skill/
│           └── SKILL.md
└── README.md
```

## Usage

### Adding a Skill

1. Create a new directory in `.claude/skills/` with a `SKILL.md` file
2. Follow the [skill format](https://docs.anthropic.com/en/docs/claude-code/skills) from the Claude Code docs
3. Open a PR and let the team review

### Using Skills in Claude Code

Clone this repo and launch Claude Code with `--add-dir`:

```bash
git clone git@github.com:SEA-AI/ai-skills.git
claude --add-dir /path/to/ai-skills
```

Claude Code automatically discovers all skills in `.claude/skills/` of added directories.

## Contributing

Got a workflow that saves you time? A prompt pattern that keeps Claude on track? Ship it! The bar is low — if it helped you twice, it'll help someone else too.

## Why?

Because nobody should have to explain our deploy process to Claude from scratch every Monday morning.
