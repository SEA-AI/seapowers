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

A high level description of the implemented changes. Visual aid is always preferred (diagrams, plots, tables, etc...).

## Testing

<!-- To be filled in manually. -->
```

## Instructions

- Fill in the **What?**, **Why?**, and **How?** sections based on the branch's commits and diff against the base branch.
- Keep **What?** to a maximum of 2 sentences.
- For **How?**, prefer visual aids (tables, diagrams, code snippets) when they add clarity.
- Leave the **Testing** section empty with the HTML comment — testing evidence (screenshots, videos, etc.) is added manually by the author after the PR is created.

## Writing Style

- Keep it short and precise. Focus on what matters most.
- Use simple, plain language — no jargon or overly formal wording.
- Every sentence should earn its place. If it doesn't add value, cut it.

## Large PRs

If the diff is large (e.g. 500+ lines changed, many unrelated files, or multiple independent features), suggest to the user that the PR should be split into smaller, focused PRs. Explain which changes could be grouped together and propose a split.
