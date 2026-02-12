---
name: react-best-practices
description: >
  React and Next.js performance optimization guidelines from Vercel.
  Covers eliminating waterfalls, bundle size optimization, server-side performance,
  client-side data fetching, re-render optimization, rendering performance,
  JavaScript performance, and advanced patterns. Use when writing, reviewing,
  or refactoring React/Next.js code.
license: MIT
---

# React Best Practices

This skill wraps the [Vercel React Best Practices](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md) skill and fetches it at runtime so you always get the latest version.

## Instructions

When this skill is invoked, fetch the latest guidelines from the upstream source:

1. Use `WebFetch` to retrieve the content from:
   ```
   https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/react-best-practices/SKILL.md
   ```
2. Apply the fetched guidelines to the current task.
3. If the fetch fails, inform the user and suggest they check the [upstream repo](https://github.com/vercel-labs/agent-skills) directly.

## Source

- **Upstream**: https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md
- **License**: MIT (Vercel Labs)
