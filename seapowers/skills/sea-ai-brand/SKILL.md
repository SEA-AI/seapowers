---
name: sea-ai-brand
description: >
  Use this skill for ANY output that must follow SEA.AI brand guidelines — documents,
  diagrams, infographics, PDFs, presentations (PPTX), spec sheets, one-pagers, reports,
  and UI/web code. This is the single source of truth for SEA.AI CI/CD.
  ALWAYS trigger when: creating diagrams, charts, infographics, any PDF or document,
  any PPTX slide deck, any HTML/React UI, any marketing or technical material for SEA.AI.
  Covers ALL output types — if it carries the SEA.AI brand, use this skill.
creator: Philipp Stampfl
date: 2026-05-09
release: "1.2.0"
---

# SEA.AI Brand Skill

Source of truth: **Brand Book 2025** (stored at `Brand info alt/Brand Book 2025.pdf`)

## Quick-start: Read the right reference file

| Task | Read |
|------|------|
| Diagram / infographic / chart (PNG/SVG) | `references/diagrams.md` |
| PDF document / one-pager / spec sheet | `references/documents-pdf.md` |
| PowerPoint presentation (PPTX) | `references/presentations-pptx.md` |
| Web UI / React / HTML component | `references/ui-coding.md` + `references/frontend-components.md` |

**Always read the relevant reference file before starting work.**

---

## Core Brand — The Non-Negotiables

### 7 Official Colors (Brand Book p.15)

```
FOCUS RED    #CB0D00   RGB 203/13/0    Pantone 186      ← primary accent
NIGHT BLUE   #0B1731   RGB 11/23/45    Pantone 289      ← dark backgrounds
OCEAN TEAL   #06404C   RGB 6/64/76     Pantone 548      ← product/secondary (Brand Book name: "Ocean Green" — visually a dark teal, NOT a green)
SKY GREY     #7B9194   RGB 123/145/148 Pantone 443      ← muted text, captions
FOG WHITE    #DFDED9   RGB 223/222/217 Pantone Cool Gray 1C ← warm backgrounds
BLACK        #000000   ← body text on light backgrounds
WHITE        #FFFFFF   ← standard content background
```

**Any other color is off-brand. No exceptions.**
Banned colors from old templates: `#0099CC`, `#FDBE00`, `#A8C652`, `#F26B43`.

### Color Usage Rules

```
FOCUS RED (#CB0D00)
  ✅ Section labels (ALL CAPS), thin accent lines, CTA buttons, alert states, page numbers on dark
  ❌ Never as large background fill, never behind the logo

NIGHT BLUE (#0B1731)
  ✅ Title slide backgrounds, section dividers, dark panel halves, table header rows
  ❌ Not for body text backgrounds on content slides

OCEAN TEAL (#06404C)  — Brand Book name: "Ocean Green", visually a dark teal
  ✅ Table header rows, secondary label backgrounds, brand card tables
  ❌ Not for primary headings or body text
  ❌ Never describe or use as "green" — it is a dark teal/navy tone

SKY GREY (#7B9194)
  ✅ Captions, footer text, muted secondary labels
  ❌ Not for main body text (too low contrast)

WHITE (#FFFFFF) — default content background
BLACK (#000000) — default body text
```

### Typography

**Font: Barlow Semi Condensed** (Google Fonts)
- Files: `assets/BarlowSemiCondensed-Bold.ttf`, `assets/BarlowSemiCondensed-Regular.ttf`
- Web: `https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;700&display=swap`
- Fallback for code/PPTX: `Arial Narrow`
- Fallback for system rendering: `DejaVu Sans Condensed`

```
Bold (700)   → Section labels, headings, table headers, emphasis
Regular (400) → Body text, captions, descriptions
```

**Case rules:**
- Short headlines: ALL CAPS
- Normal headlines: Sentence case (not title case)
- Section labels: ALWAYS ALL CAPS FOCUS RED
- Body: normal sentence case

### Logo

- Files: `assets/Logo SEA.AI black RGB.jpg` (light bg), `assets/Logo SEA.AI White RGB.svg` (dark bg)
- Always top-right corner on documents/slides
- Letter-spaced: `S E A . A I` + cursor icon `[--]`
- Never on Focus Red background, never distorted or recolored

### Design Principles

```
✅ White background for content (not dark unless section divider)
✅ Left-align body text and titles
✅ Generous white space — breathing room is brand
✅ Red line element to structure content (thin, purposeful)
✅ Section labels: ALL CAPS, Focus Red, Barlow Semi Condensed Bold
✅ Footer on every page: document label + "SEA.AI CONFIDENTIAL" in Sky Grey
❌ No gradients
❌ No drop shadows
❌ No decorative elements
❌ No centering body text
❌ No bold body text (bold only for labels/headers)
```

---

## Brand Messaging (quick ref)

- **Tagline:** "NOW YOU SEE."
- **Claim:** "Machine Vision for Safety & Security at Sea."
- **Vision:** "Help save lives at sea through artificial intelligence."
- **Character:** Technology Pioneer | Vigilant & Reliable | Agile & Dynamic | Collaborative & Connected

---

## Asset Paths

```
assets/BarlowSemiCondensed-Bold.ttf    ← always use for Python/Pillow rendering
assets/BarlowSemiCondensed-Regular.ttf ← always use for Python/Pillow rendering
assets/Logo SEA.AI black RGB.jpg       ← on white/light backgrounds
assets/Logo SEA.AI White RGB.svg       ← on dark backgrounds
```

Paths are relative to the skill folder. Resolve to absolute when using in scripts.
