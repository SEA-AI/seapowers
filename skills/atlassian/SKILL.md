---
name: atlassian
description: >
  Use when creating, updating, searching, or triaging Jira tickets or reading/
  writing Confluence pages on the SEA.AI Atlassian workspace
  (sea-team.atlassian.net). Covers task and backlog management as well as
  knowledge sharing across all teams. Provides instance config, issue types,
  custom fields, DoR gates, JQL patterns, and Confluence conventions.
---

# SEA.AI Jira & Confluence Reference

## Instance

| | |
|---|---|
| **Jira** | `sea-team.atlassian.net` |
| **Confluence** | `sea-team.atlassian.net/wiki` |
| **Main project** | `SEA` (project ID `11797`) |
| **DoR page** | `/wiki/x/aQBDDw` |

---

## Two Teams, One Project, Two Boards

The SEA project is shared by two teams, each with their own sprint board:

| Board | Team | Focus |
|-------|------|-------|
| Dev Board | Dev Team | SW/product: streaming, frontend, backend, CI/CD, radar |
| AI Board | AI Team | CNN training, datasets, trackers |

When creating or filtering tickets, always set `customfield_10001` (Team) to distinguish ownership. Use `lookupJiraAccountId` to resolve team UUIDs at runtime — never hardcode them.

---

## Jira

### Issue Types

| Name | ID | When to use |
|------|----|-------------|
| Story | 10004 | User-facing feature (As a / I want / So that) |
| Task | 10092 | Technical / internal work |
| Bug | 10095 | Defect with repro steps |
| Spike | 11817 | Time-boxed investigation |
| Epic | 10000 | Collection of related work |
| Support | 11818 | Service / operational request |
| Sub-task | 10093 | Child of a Task/Story — avoid unless explicitly requested |

### Statuses

| Status | ID | Category |
|--------|----|----------|
| To Do | 10090 | new |
| In Progress | 3 | indeterminate |
| Pull Request | 12298 | indeterminate |
| Awaiting Review | 12332 | indeterminate |
| On Hold | 12264 | indeterminate |
| Done | 10092 | done |
| Discarded | 10307 | done — use for rejected/cancelled items |

### Priorities

| Priority | Notes |
|----------|-------|
| Hotfix | Bugs requiring immediate attention |
| Essential | Higher urgency |
| Medium | Default |
| Optional | Lower urgency |

### Custom Fields

| Field | Jira ID | Format |
|-------|---------|--------|
| Team | `customfield_10001` | Plain string (team UUID — resolve at runtime) |
| Product(s) | `customfield_12044` | Array of `{"id": "..."}` objects |
| Sprint | `customfield_10020` | Sprint ID — always fetch fresh with `sprint in openSprints()` |
| Story Points | `customfield_10031` | Number (`customfield_10016` is a legacy field on older tickets) |
| Acceptance Criteria | `customfield_10310` | ADF (Atlassian Document Format) — always fill on create/edit |
| Labels | `labels` | Array of strings |

#### Product IDs

| Product | ID |
|---------|-----|
| Oceanus | `12582` |
| Watchkeeper | `12583` |
| Sentry | `12584` |

### Issue Link Types

| Name | ID | inward | outward |
|------|----|--------|---------|
| Blocks | 10000 | is blocked by | blocks |
| Duplicate | 10002 | is duplicated by | duplicates |
| Relates | 10003 | relates to | relates to |

> Call `getIssueLinkTypes` to discover additional types. If it returns "No approval received", fall back to the IDs above.

### Estimation

| Type | Method |
|------|--------|
| Story / Task / Bug | Story points (`customfield_10031`) |
| Spike | Timebox in days — written in description body |

### Definition of Ready

**Gate A — backlog entry:** Title · description · issue type · epic/parent (if known) · product(s) · reporter

**Gate B — before sprint:** Acceptance criteria · dependencies linked · story points set · priority set · peer-checked

### Writing Style

Write tickets like a teammate would, not like a formal spec. Use plain, direct language.

**Description:**
- Say what the problem is and why we care, then what needs to be done
- Use `**bold headers**` to split parts if the ticket has multiple concerns
- No bullet-point walls, no corporate jargon

**Acceptance criteria (`customfield_10310`):**
- Always fill this field — it is required for every create/edit
- Must be ADF format (not markdown string) — pass as a JSON object
- Each item = one clear, testable outcome written as a present-tense statement
- Use a **checkbox list** (`taskList`), not bullet points

```json
"customfield_10310": {
  "type": "doc", "version": 1,
  "content": [{"type": "taskList", "attrs": {"localId": "ac"}, "content": [
    {"type": "taskItem", "attrs": {"localId": "1", "state": "TODO"}, "content": [{"type": "text", "text": "Inference runs automatically after export and images are uploaded to W&B"}]},
    {"type": "taskItem", "attrs": {"localId": "2", "state": "TODO"}, "content": [{"type": "text", "text": "The right inference path is used per model type (YOLO / AHOY / DAN)"}]}
  ]}]
}
```

### Description Formatting

Always pass `contentFormat: "markdown"` on every create and edit call — plain strings produce literal `\n` in the UI.

### JQL Quick Reference

```jql
-- Current sprint
project = SEA AND sprint in openSprints()

-- Epic's children
project = SEA AND parent = SEA-XXX

-- Orphaned tickets (no epic)
project = SEA AND "Epic Link" is EMPTY AND issuetype not in (Epic)

-- Open tickets matching keyword
project = SEA AND statusCategory != Done AND text ~ "keyword"
```

### Workflow Patterns

- **Check before creating** — search by keywords before opening new tickets to avoid duplicates.
- **Re-parent orphans** — if a search surfaces tickets with no parent epic, re-parent them.
- **Team field** — pass as a plain string, not an object wrapper.
- **Product field** — pass as an array of `{"id": "..."}` objects.
- **Sprint field** — always fetch the current sprint ID fresh; never hardcode it.
- **Sub-tasks** — require a parent Task/Story (not an Epic).
- **`fetch` tool** — only works with ARIs; use `getJiraIssue` / `getConfluencePage` for regular fetches.

---

## Confluence

### Spaces

| Key | Name | Primary use |
|-----|------|-------------|
| `SD` | Software Development | SW team docs, guidelines, retrospectives, sprint reviews |
| `CV` | AI Team | AI/ML team docs, sprint reviews *(webui URL: `/spaces/AI`)* |
| `PD` | Product Development | Product specs, roadmap, demand process |

### Key Pages

| Page | Path |
|------|------|
| Definition of Ready | `/wiki/x/aQBDDw` |

### When to use Confluence vs Jira

| Confluence | Jira |
|---|---|
| Decisions, RFCs, runbooks, specs | Actionable work items |
| Meeting notes, retrospectives | Bug reports, feature requests |
| Team knowledge, onboarding | Sprint planning, backlog |

### Authoring Patterns

- Link Confluence specs to their Jira Epic/Story via smart links.
- Store detailed narratives in Confluence; keep Jira tickets concise.
- Use the `atlassian:spec-to-backlog` skill to convert specs into tickets.

---

## Tools Quick Reference

| Tool | When to use |
|------|-------------|
| `search` (Rovo) | Cross-system discovery (Jira + Confluence at once) |
| `searchJiraIssuesUsingJql` | Targeted Jira queries |
| `searchConfluenceUsingCql` | Targeted Confluence queries |
| `lookupJiraAccountId` | Resolve a name to account ID at runtime |
| `getIssueLinkTypes` | Discover link type IDs before creating links |
| `createIssueLink` | Link two tickets |
| `createConfluencePage` | Create a new Confluence page |
| `updateConfluencePage` | Edit an existing Confluence page |
| `transitionJiraIssue` | Move a ticket to a new status |
