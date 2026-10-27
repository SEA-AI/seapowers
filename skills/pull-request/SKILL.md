---
name: pull-request
description: >
  SEA.AI pull request template. Enforces a consistent PR format with
  What/Why/How/Testing sections. Use when creating pull requests.
license: MIT
---

# Pull Request Format

When creating a pull request, use the following format for the PR body:

```markdown
## What?

Briefly describe the changes introduced by this PR. Highlight the difference between the state before and after the changes. Max 2 sentences.

## Why?

Why are these changes necessary? Is there a specific stakeholder (PM, service, QA, devs, sales) who is driving the motivation for these changes?

## How?

A high level description of the implemented changes. Prefer a small diagram over text-only explanations; use plots or tables for numbers.

## Testing

How the change was validated before merge: tests, benchmarks, screenshots, videos, manual checks, etc.
```

## Instructions

- Use the **complete diff** against the base branch as the source of truth.
- Describe the **impact of the change**, not the implementation history.
- Focus on user-visible, behavioral, or architectural changes. Skip mechanical details unless they matter for review.
- Fill **Testing** with **pre-merge** evidence you produced (test results, screenshots, videos). Attach local images and videos with `gh pr create --attach <file>` or `gh pr edit --attach <file>`; reference them in the body as `![alt](./file.png)`. If `gh pr create --help` does not list `--attach`, suggest upgrading `gh`.
- List any validation you could not run so the author can add it.

## Writing Style

- **Be concise and precise**: write only what helps the reader understand the change.
- **Use simple, plain language**. Avoid jargon and unnecessary formality.
- **Make PRs easy to scan**. Prefer tables, diagrams, and code snippets over long paragraphs when they improve clarity.

## Diagrams

Use a `mermaid` code block (GitHub renders it). Keep it small (about 10 nodes or fewer), show only the part the PR changes, and skip it for trivial changes.

| The change is about… | Use |
|---|---|
| Control or data flow, pipelines, decision logic | `flowchart` |
| Calls between services or components, request/response order | `sequenceDiagram` |
| Modes or lifecycle (e.g. alarm or connection states) | `stateDiagram-v2` |
| Module or class structure, new interfaces | `classDiagram` |
| Database schema | `erDiagram` |
| Before/after numbers (performance, metrics) | Table or plot, not a diagram |

## Large PRs

If the diff is large (e.g. 500+ lines changed, many unrelated files, or multiple independent features), suggest to the user that the PR should be split into smaller, focused PRs. Explain which changes could be grouped together and propose a split.
