---
File: sea-ai-brand
Description: SEA.AI Brand Skill — Single source of truth for brand-compliant outputs across all media.
Creator: Philipp Stampfl
Date: 2025-04-30
Release: 2.0
---

# SEA.AI Web UI & Coding

For React components, HTML/CSS, and software interfaces. The SEA.AI product UI uses
a distinct DARK theme — this is the one place where dark backgrounds are the standard.

> Note: The product UI (software interfaces, dashboards, detection overlays) uses
> the DARK theme by default. Print/document outputs use WHITE. This is intentional —
> the product runs on ship bridges in low-light environments.

## Theme Tokens

```css
/* DARK theme (default for UI) */
--surface-neutral-1: #101214;  /* outermost shell */
--surface-neutral-2: #181B1E;  /* panels */
--surface-neutral-3: #202428;  /* cards */
--surface-neutral-4: #292E33;  /* inputs, recessed */
--surface-neutral-5: #31373D;  /* elevated elements */

/* Signal colors — same in DARK and LIGHT */
--surface-primary-3:  #0A67C2;  /* active/selected/in-progress */
--surface-danger-3:   #C20A20;  /* error/critical/alert */
--surface-warning-3:  #F1B80D;  /* caution/approaching limit */
--surface-success-3:  #2DA84F;  /* complete/confirmed/nominal (implied) */

/* Text on colored surfaces */
--content-primary-2:  #CFE5FC;
--content-danger-1:   #FA9EA9;
--content-warning-1:  #FAE39E;

/* Accent (borders, focus rings) */
--accent-primary-2: #0A67C2;
--accent-danger-2:  #C20A20;
```

> These UI surface colors (`#101214` etc.) are ONLY for the software product.
> They are NOT the brand colors. Do not use them in documents, diagrams or presentations.

## Typography for UI

```css
font-family: 'Barlow Semi Condensed', 'Arial Narrow', Arial, sans-serif;
```

Condensed letterform for clarity at all sizes — instrument-panel readouts and dashboards benefit from the letterform density.

```css
/* main-* classes: sentence case, prose */
.main-title-l  { font-size: 40px; font-weight: 500; line-height: 48px; }
.main-title-m  { font-size: 24px; font-weight: 500; line-height: 32px; }
.main-body-m   { font-size: 20px; font-weight: 400; line-height: 28px; }
.main-body-s   { font-size: 16px; font-weight: 400; line-height: 24px; }

/* card-* classes: UPPERCASE, data labels */
.card-title-m  { font-size: 24px; font-weight: 400; letter-spacing: 0.02em; text-transform: uppercase; }
.card-label-s  { font-size: 16px; font-weight: 500; text-transform: uppercase; }
```

## Flat Surface System

Depth comes from surface value contrast only — no shadows, no borders:

```css
.shell  { background: var(--surface-neutral-1); }   /* outermost */
.panel  { background: var(--surface-neutral-3); }   /* content panel */
.card   { background: var(--surface-neutral-4); }   /* card/item */
.input  { background: var(--surface-neutral-5); }   /* form input */
```

```css
/* No visible borders in default state */
.card { border: none; border-radius: 8px; background: var(--surface-neutral-4); }
/* Dividers via background showing through gaps (not actual borders) */
.grid { gap: 8px; padding: 16px; background: var(--surface-neutral-3); }
```

## Semantic Color — 4 Roles Only

| Color | Signal | Use |
|-------|--------|-----|
| Primary blue | Active / selected / in progress | Running state, active tab |
| Danger red | Error / critical / destructive | Alert, failure, expiry |
| Warning amber | Caution / near limit | Pending, near-threshold |
| Success green | Complete / confirmed | Done, connected |
| Neutral grey | Inactive / secondary | Idle, secondary, dividers |

**Color communicates state. Never for visual emphasis alone.**

## Border Radius

```css
--radious-s: 4px;   /* chips, tags, tight controls */
--radious-m: 8px;   /* buttons, cards, panels */
--radious-l: 16px;  /* modals, large surfaces */
```

Adjacent components share edges (radius → 0 on shared side):
```css
.panel-left  { border-radius: 0 8px 8px 0; }
.panel-right { border-radius: 8px 0 0 8px; }
```

## Motion

```css
/* Functional only — never decorative */
transition: all 0.4s ease-in-out;   /* state changes */
transition: all 0.4s linear;         /* continuous indicators */
/* No entrance/exit animations on content */
```

## Spacing Tokens

```css
--space-xs:  4px;   /* tight icon gaps */
--space-s:   8px;   /* inline element gaps */
--space-m:   12px;  /* standard gap between controls */
--space-l:   16px;  /* padding inside components */
--space-2xl: 24px;  /* between sections */
--space-3xl: 32px;  /* panel internal padding */
```

Minimum interactive target height: **40px**.

## React Template

```jsx
export default function SeaAICard({ title, value, status }) {
  return (
    <div style={{
      background: 'var(--surface-neutral-4)',
      borderRadius: 'var(--radious-m)',
      padding: '16px',
      border: 'none',
    }}>
      <span style={{ color: '#7B9194', fontSize: 12, textTransform: 'uppercase',
        letterSpacing: '0.02em', fontFamily: "'Barlow Semi Condensed', 'Arial Narrow'" }}>
        {title}
      </span>
      <div style={{ color: '#F0F2F4', fontSize: 24, fontWeight: 500, marginTop: 4 }}>
        {value}
      </div>
    </div>
  );
}
```

## Key Rules for UI

```
✅ DARK theme by default (surface-neutral-1 outermost)
✅ Depth from background contrast only — no shadows, no borders
✅ Color = state (only 4 semantic colors)
✅ Barlow Semi Condensed for UI typography
✅ Minimum 40px touch targets
❌ No decorative shadows or borders
❌ No entrance animations
❌ No color for emphasis — only for state
❌ Do not use UI surface colors (#101214 etc.) in documents/diagrams
```
