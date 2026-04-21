---
name: atlassian
description: >
  Use when creating, updating, searching, or triaging Jira tickets or reading/
  writing Confluence pages on the SEA.AI Atlassian workspace
  (sea-team.atlassian.net). Covers task and backlog management as well as
  knowledge sharing across all teams. Provides instance config, hierarchy,
  issue types, statuses, priorities, custom fields, DoR gates, issue templates,
  JQL patterns, API gotchas, and Confluence space conventions.
---

# SEA.AI Jira & Confluence Reference

## Instance

| | |
|---|---|
| **Jira** | `sea-team.atlassian.net` |
| **Confluence** | `sea-team.atlassian.net/wiki` |
| **Main project** | `SEA` (project ID `11797`) |
| **DoR page** | `/wiki/x/aQBDDw` |
| **Demand process** | `/wiki/spaces/PD/pages/687898625` |
| **AI team Jira project** | `CV` (project key) |

> **Authentication:** A fresh session must call `mcp__plugin_atlassian_atlassian__authenticate` before any tools are available.

---

## Work Hierarchy

```
Demand  (strategic level — tracked in roadmap/backlog projects)
  └─ Epic  (SEA or CV project, one per team)
       └─ Story / Task / Bug / Spike  (SEA project, sprint-level)
            └─ Sub-task  (avoid unless explicitly requested)
```

---

## Jira

### Teams in the SEA Project

Both teams share the same SEA project and sprint board. Always set `customfield_10001` to distinguish ownership.

| Team | Focus |
|------|-------|
| Dev Team | SW/product: streaming, frontend, backend, CI/CD, radar |
| AI Team | CNN training, datasets, trackers |

> Team UUIDs and account IDs change as the org evolves — always resolve them at runtime using `lookupJiraAccountId`. Never hardcode UUIDs.

### Issue Types

| Name | ID | When to use |
|------|----|-------------|
| Story | 10004 | User-facing feature (As a / I want / So that) |
| Task | 10092 | Technical / internal work |
| Bug | 10095 | Defect with repro steps |
| Spike | 11817 | Time-boxed investigation |
| Epic | 10000 | Collection of related work |
| Support | 11818 | Service / operational request |
| Sub-task | 10093 | Child of a Task/Story (hierarchyLevel -1) — avoid unless explicitly requested; parent must be a Task/Story, not an Epic |

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

| Priority | ID | Notes |
|----------|----|-------|
| Medium | 3 | Default for most tickets |
| Essential | *(look up)* | Higher urgency than Medium |
| Optional | *(look up)* | Lower urgency than Medium |
| Hotfix | 10001 | Bugs requiring immediate attention |

### Custom Fields

| Field | Jira ID | Format |
|-------|---------|--------|
| Team | `customfield_10001` | Plain string (team UUID) |
| Product(s) | `customfield_12044` | Array of `{"id": "..."}` objects |
| Sprint | `customfield_10020` | Sprint ID integer — fetch fresh with `sprint in openSprints()` each time |
| Story Points | `customfield_10016` | Number |
| Labels | `labels` | Array of strings |

#### Product IDs

| Product | ID |
|---------|-----|
| Oceanus | `12582` |
| Watchkeeper | `12583` |
| Sentry | `12584` |

#### Common labels
`backend` · `frontend` · `ci-cd` · `estimation-needed` · `magic-estimated`

### Issue Link Types

| Name | ID | inward | outward |
|------|----|--------|---------|
| Blocks | 10000 | is blocked by | blocks |
| Duplicate | 10002 | is duplicated by | duplicates |
| Relates | 10003 | relates to | relates to |

> Call `getIssueLinkTypes` to discover additional types (e.g. Clones, Polaris). If it returns "No approval received", fall back to the IDs above.

### Estimation

| Level | Method | Notes |
|-------|--------|-------|
| Story / Task / Bug (dev & AI teams) | **Story points** | `customfield_10016`; used in sprint planning |
| Spike | **Timebox in days** | Written in description body — no dedicated field |
| Demand (strategic level) | **T-Shirt Sizing** | XS / S / M / L / XL; reverse-engineered from historic velocity |
| Batch of stories (refinement) | **Magic Estimation** | Fast relative sizing across many stories at once |
| Demand scoping session | **Three Amigos** | PO + Engineering + QA/Design together |

### Sprint Cadence

- ~2-week sprints; naming convention may vary per team
- Use JQL `sprint in openSprints()` to get the current sprint ID before assigning — sprint IDs change each sprint, never hardcode them

### Definition of Ready

#### Story/Task — Gate A (backlog entry)
Title · description · issue type · epic/parent (if known) · product(s) · reporter

#### Story/Task — Gate B (before sprint)
Acceptance criteria · dependencies linked · **story points set** · priority set · peer-checked

#### Demand-level DoR
Title · use-case · user value · business value · success metrics · risk assessment · rating/ranking · t-shirt size · assigned teams

### Demand Lifecycle States

`New` → `Accepted` / `Rejected` → `Estimated` → `Prioritized` → `In Specification` → `Ready for Impl.` → `In Progress` → `In Review` → `Done`

### Key Roles

| Acronym | Role |
|---------|------|
| PO | Product Owner |
| QA | Quality Assurance |
| SM | Scrum Master |

### Issue Templates

**Story**
```
**As a** [role], **I want** [feature], **So that** [benefit]

**Context**
...

**Customer Impact**
...

**Acceptance Criteria**
- [ ] ...
```

**Bug**
```
**Problem**
...

**Reproduction Steps**
1. ...

**Expected vs Actual**
- Expected: ...
- Actual: ...

**Workaround**
...

**Customer Impact**
...

**Acceptance Criteria**
- [ ] ...
```

**Spike**
```
**Description**
...

**Questions to Answer**
- ...

**Timebox**
X days

**Expected Deliverables**
- ...
```

### JQL Quick Reference

```jql
-- Current sprint
project = SEA AND sprint in openSprints()

-- Epic's children
project = SEA AND parent = SEA-XXX

-- Orphaned tickets (no epic)
project = SEA AND "Epic Link" is EMPTY AND issuetype not in (Epic)

-- A specific team's backlog (replace TEAM-UUID with the resolved UUID)
project = SEA AND statusCategory = "To Do" AND team = "TEAM-UUID"

-- Open tickets matching keyword
project = SEA AND statusCategory != Done AND text ~ "keyword"

-- PIR action items (check Incident Response page for current parent ticket key)
project = SEA AND parent = SEA-XXX
```

### Description Formatting

**Always** pass `contentFormat: "markdown"` on every create and edit call.  
Plain string descriptions with `\n` produce literal `\n` in the Jira UI.

### Workflow Patterns & API Gotchas

- **Check before creating** — search by keywords and check the parent field before opening new tickets to avoid duplicates.
- **Re-parent orphans** — if a search surfaces tickets with no parent epic, re-parent them.
- **Team field** — pass as a plain string, not an object wrapper.
- **Product field** — pass as an array of `{"id": "..."}` objects.
- **Sprint field** — fetch the current sprint ID fresh each time with `sprint in openSprints()`; never hardcode it.
- **Sub-tasks** — require a parent Task/Story (not an Epic); don't confuse with child-of-epic parenting.
- **Discarded vs Done** — Discarded (10307) is for rejected/cancelled work; Done (10092) is for completed work.
- **`fetch` tool** — only works with ARIs (Atlassian Resource Identifiers); use `getJiraIssue` / `getConfluencePage` for regular fetches.

---

## Confluence

### Spaces

| Key | Name | Primary use |
|-----|------|-------------|
| `SD` | Software Development | SW team docs, guidelines, retrospectives, sprint reviews, incident response |
| `CV` | AI Team | AI/ML team docs, sprint reviews, research pages *(legacy key from "Computer Vision"; webui URL uses `/spaces/AI` alias)* |
| `PD` | Product Development | Demand backlog process, product specs, roadmap |
| `TLO` | Technological Leadership Organization | Company policies, approved tools, AI usage policy |
| `QMS` | Quality Management System - SEA.AI | SOPs, formal development process |
| `PS` | Product Space | Architecture decisions, hardware/software design |
| `HD` | Hardware Development | Hardware engineering docs and specs |
| `RD` | R&D | R&D team general information and guidelines |
| `PSVC` | Professional Services | Customer experience, support, education, and technology advocacy docs |
| `seatocaro` | SEA.AI <> TOCAROBLUE | Technical documentation for the SEA.AI + TOCAROBLUE collaboration |


### Key Confluence Pages

| Page | Path | Purpose |
|------|------|---------|
| Definition of Ready | `/wiki/x/aQBDDw` | Authoritative DoR checklist — reference before sprint |
| Demand Process | `/wiki/spaces/PD/pages/687898625` | Full demand lifecycle and tooling guide |
| Technical Sustainability Review | `/wiki/spaces/SD/pages/704741386` | Quarterly session → SEA backlog items; whiteboard child page per session |
| Incident Response | `/wiki/spaces/SD/pages/660537345` | SEV1/2/3 definitions, incident lead, MS Teams alert channel |
| PIR Template | `/wiki/spaces/SD/pages/659750915` | Post-incident review template; check Incident Response page for current PIR parent ticket |

### Incident Severity Reference

| Level | Definition |
|-------|-----------|
| SEV1 | App down / data loss / blocked business processes — PIR mandatory |
| SEV2 | Functional degradation, workaround exists — PIR mandatory |
| SEV3 | Minor / cosmetic, low urgency — PIR optional if learnings exist |

See the Incident Response page for the current incident lead and backup assignments.  
Updates via MS Teams → "Alerts" channel in R&D group.

### When to use Confluence vs Jira

| Use Confluence for | Use Jira for |
|---|---|
| Decisions, RFCs, runbooks, how-tos | Actionable work items with owners |
| Meeting notes, ADRs, retrospectives | Bug reports and feature requests |
| Onboarding and team knowledge | Sprint planning and backlog grooming |
| Long-form specs and demand background | Concise acceptance criteria on tickets |
| Risk catalogs, process documentation | Lifecycle tracking (New → Done) |

### Authoring Patterns

- Link Confluence specs to their Jira Demand/Epic/Story via Jira smart links.
- Keep concise, decision-relevant information in Jira; store detailed narratives in Confluence referenced via links.
- Prefer creating pages inside the relevant team space rather than the root.
- When converting a Confluence spec into Jira tickets, use the `atlassian:spec-to-backlog` skill.
- The DoR page is the authoritative checklist for ticket quality — reference it when reviewing a ticket before sprint.

---

## Available Tools Quick Reference

| Tool | When to use |
|------|-------------|
| `search` (Rovo) | Best for cross-system discovery when you don't know if something is in Jira or Confluence |
| `searchJiraIssuesUsingJql` | Targeted Jira queries |
| `searchConfluenceUsingCql` | Targeted Confluence queries — e.g. `space = SD AND title ~ "DoR"` |
| `createConfluencePage` | Create a new Confluence page |
| `updateConfluencePage` | Edit an existing Confluence page |
| `lookupJiraAccountId` | Resolve a person's name to accountId at runtime — prefer over hardcoding |
| `getIssueLinkTypes` | Discover all link type IDs before creating links |
| `createIssueLink` | Link two tickets (inwardIssue = blocker, outwardIssue = blocked) |
| `getJiraIssue` | Fetch a single issue by key |
| `getConfluencePage` | Fetch a page by ID or tiny link |
| `getConfluenceSpaces` | List all spaces with their keys |
| `addWorklogToJiraIssue` | Log time on a ticket |
| `transitionJiraIssue` | Move a ticket to a new status |
