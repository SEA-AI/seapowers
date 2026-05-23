# python-best-practices skill

Modern Python best practices for AI agents. 20 rules across 6 categories, prioritized by impact.

## Categories

| # | Category | Rules | Impact |
|---|----------|-------|--------|
| 1 | Project Setup (uv) | 3 | CRITICAL |
| 2 | Design Decisions | 4 | HIGH |
| 3 | Testing with pytest | 5 | HIGH |
| 4 | Type Safety | 3 | HIGH |
| 5 | Python Idioms | 3 | MEDIUM |
| 6 | Async Patterns | 3 | MEDIUM |

## Files

- `SKILL.md` — skill entrypoint with category index and quick reference
- `AGENTS.md` — all rules compiled into a single document
- `rules/` — individual rule files (one per best practice)
- `metadata.json` — version and reference metadata

## Adding a Rule

1. Copy `rules/_template.md` to `rules/<prefix>-<slug>.md`
2. Fill in frontmatter (`title`, `impact`, `tags`) and body
3. Add an entry to the relevant section in `SKILL.md` Quick Reference
4. Add the rule to `AGENTS.md` under the correct section
5. Bump `version` in `metadata.json` and `SKILL.md` frontmatter

## Rule File Naming

`<section-prefix>-<descriptive-slug>.md`

| Prefix | Section |
|--------|---------|
| `setup-` | Project Setup |
| `design-` | Design Decisions |
| `test-` | Testing |
| `types-` | Type Safety |
| `idiom-` | Python Idioms |
| `async-` | Async Patterns |
