# SEA.AI Frontend

For web UI, HTML/CSS, and software interfaces. The product runs on ship bridges in
low-light environments — dark backgrounds are the standard here, unlike all other
SEA.AI output types which use white.

> These UI surface colors are ONLY for the software product. They are NOT brand
> colors. Do not use them in documents, diagrams, or presentations.

## Themes

Apply via `data-theme` on the root element — token names stay the same, values change:

```html
<html data-theme="DARK">  <!-- LIGHT / DARK / NIGHT -->
```

| Theme | When to use |
|---|---|
| `DARK` | Default for the product UI |
| `LIGHT` | Daytime / well-lit contexts |
| `NIGHT` | Bridge at night — preserves night vision |

Neutral surfaces and text per theme:

| Token | LIGHT | DARK | NIGHT |
|---|---|---|---|
| `--surface-neutral-1` (shell) | `#B9BDC1` | `#101214` | `#000000` |
| `--surface-neutral-2` | `#CBCED1` | `#181B1E` | `#08090A` |
| `--surface-neutral-3` (panels) | `#DCDEE0` | `#202428` | `#101214` |
| `--surface-neutral-4` (cards) | `#EEEFF0` | `#292E33` | `#181B1E` |
| `--surface-neutral-5` (elevated) | `#FFFFFF` | `#31373D` | `#202428` |
| `--content-neutral-1` (dim) | `#747C84` | `#747C84` | `#747C84` |
| `--content-neutral-2` (secondary) | `#414951` | `#B9BDC1` | `#A8ADB2` |
| `--content-neutral-3` (primary) | `#202428` | `#FFFFFF` | `#DCDEE0` |

Signal colors are identical in DARK and LIGHT; NIGHT shifts one step darker:

| Signal | LIGHT / DARK | NIGHT |
|---|---|---|
| `--surface-primary-3` | `#0A67C2` | `#084C91` |
| `--surface-danger-3` | `#C20A20` | `#910818` |
| `--surface-warning-3` | `#F1B80D` | `#C2940A` |

Text on colored surfaces and accent tokens (same across all themes):

```css
--content-primary-2: #CFE5FC;  /* text on primary blue */
--content-danger-1:  #FA9EA9;  /* text on danger red */
--content-warning-1: #FAE39E;  /* text on warning amber */
--accent-primary-2:  #0A67C2;  /* focus rings, borders */
--accent-danger-2:   #C20A20;  /* error outlines */
```

## Typography

> The product UI uses **Saira Condensed**. Other output types (documents, slides,
> diagrams) may use a different brand font — check the relevant reference file.

```css
font-family: 'Saira Condensed', 'Arial Narrow', Arial, sans-serif;
```

Classes are scoped to the `.typography` base, e.g. `<p class="typography main-title-l">`:

```css
/* main-* classes: sentence case, prose */
.typography.main-title-l  { font-size: 2.5rem;  font-weight: 500; line-height: 3rem; }   /* 40/48 */
.typography.main-title-m  { font-size: 1.5rem;  font-weight: 500; line-height: 2rem; }   /* 24/32 */
.typography.main-body-m   { font-size: 1.25rem; font-weight: 400; line-height: 1.75rem; } /* 20/28 */
.typography.main-body-s   { font-size: 1rem;    font-weight: 400; line-height: 1.5rem; }  /* 16/24 */

/* card-* classes: UPPERCASE, data labels */
.typography.card-title-m  { font-size: 1.5rem; font-weight: 400; line-height: 2rem; letter-spacing: 0.02em; text-transform: uppercase; }
.typography.card-label-s  { font-size: 1rem;   font-weight: 500; line-height: 100%; text-transform: uppercase; }
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

## Semantic Color — 3 Roles

| Color | Signal | Use |
|-------|--------|-----|
| Primary blue | Active / selected / in progress | Running state, active tab |
| Danger red | Error / critical / destructive | Alert, failure, expiry |
| Warning amber | Caution / near limit | Pending, near-threshold |

Neutral grey is the surface system, not a semantic role — use it for idle, secondary, and dividers.

**Color communicates state. Never for visual emphasis alone.**

## Border Radius

> Note: the upstream tokens.css ships these as `--radious-*` (misspelled). Use the
> corrected `--radius-*` names in new code and alias them to the upstream tokens
> at the theme root.

```css
--radius-xs: 2px;   /* hairline */
--radius-s:  4px;   /* chips, tags, tight controls */
--radius-m:  8px;   /* buttons, cards, panels */
--radius-l:  16px;  /* modals, large surfaces */
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
--space-component-xs:  4px;   /* tight icon gaps */
--space-component-s:   8px;   /* inline element gaps */
--space-component-m:   12px;  /* standard gap between controls */
--space-component-l:   16px;  /* padding inside components */
--space-component-xl:  20px;
--space-component-2xl: 24px;  /* between sections */
--space-component-3xl: 32px;  /* panel internal padding */
--space-component-4xl: 48px;
```

Layout-scale spacing (`--space-layout-xs` … `--space-layout-3xl`, 64px → 512px) is also available for page-level gutters.

Minimum interactive target height: **40px**.

## Example Component

```jsx
export default function SeaAICard({ title, value }) {
  return (
    <div style={{
      background: 'var(--surface-neutral-4)',
      borderRadius: 'var(--radius-m)',
      padding: '16px',
      border: 'none',
    }}>
      <span style={{ color: 'var(--content-neutral-1)', fontSize: 'var(--typography-font-size-xs)', textTransform: 'uppercase',
        letterSpacing: '0.02em', fontFamily: "'Saira Condensed', 'Arial Narrow'" }}>
        {title}
      </span>
      <div style={{ color: 'var(--content-neutral-3)', fontSize: 'var(--typography-font-size-l)', fontWeight: 500, marginTop: 4 }}>
        {value}
      </div>
    </div>
  );
}
```

## Key Rules

```
✅ DARK theme by default (surface-neutral-1 outermost)
✅ Depth from background contrast only — no shadows, no borders
✅ Color = state (only 3 semantic colors)
✅ Saira Condensed for UI typography
✅ Minimum 40px touch targets
❌ No decorative shadows or borders
❌ No entrance animations
❌ No color for emphasis — only for state
```

---

## Components

| Component | Use |
|-----------|-----|
| Button | Primary/secondary/danger actions |
| Toggle | On/off switch |
| Checkbox | Multi-select option |
| Input | Text entry |
| Progress Bar | Linear progress |
| Pill | Connection/status badge |
| Typography | Text hierarchy |

### Button

```html
<button class="btn btn--primary">Action</button>
<button class="btn btn--secondary">Cancel</button>
<button class="btn btn--ghost">Ghost</button>
<button class="btn btn--danger">Delete</button>
<button class="btn btn--primary" disabled>Disabled</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  min-width: 80px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-m);
  font-family: 'Saira Condensed', Arial, sans-serif;
  font-size: var(--typography-font-size-s);
  cursor: pointer;
  transition: 0.2s;
  gap: 8px;
}

.btn--primary   { background: var(--surface-primary-3); color: var(--content-primary-3); }
.btn--secondary { background: var(--surface-neutral-4); color: var(--content-neutral-3); }
.btn--danger    { background: var(--surface-danger-3);  color: #fff; }
.btn--ghost     { background: transparent; color: var(--content-neutral-3); border: var(--stroke-thin) solid var(--surface-neutral-4); }
.btn:disabled   { opacity: var(--opacity-disabled); pointer-events: none; }
```

### Toggle

```html
<label class="toggle">
  <input type="checkbox" />
  <span class="track"><span class="thumb"></span></span>
</label>
```

```css
.toggle { display: inline-flex; align-items: center; cursor: pointer; }
.toggle input { display: none; }

.track {
  width: 40px; height: 25px;
  border-radius: 20px;
  background: var(--surface-neutral-3);
  position: relative;
  transition: background 0.2s;
}

.thumb {
  position: absolute;
  top: 2px; left: 2px;
  width: 21px; height: 21px;
  border-radius: 50%;
  background: var(--content-neutral-2);
  transition: left 0.2s, background 0.2s;
}

.toggle input:checked ~ .track           { background: var(--surface-neutral-5); }
.toggle input:checked ~ .track .thumb   { left: 17px; background: var(--surface-primary-3); }
```

### Checkbox

```html
<label class="checkbox">
  <input type="checkbox" />
  <span class="box"></span>
  <span>Enable feature</span>
</label>
```

```css
.checkbox { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.checkbox input { display: none; }

.box {
  width: 18px; height: 18px;
  border-radius: var(--radius-s);
  border: var(--stroke-normal) solid var(--surface-neutral-5);
  background: var(--surface-neutral-4);
  transition: 0.2s;
}

.checkbox input:checked ~ .box { background: var(--surface-primary-3); border-color: var(--surface-primary-3); }
```

### Input

```html
<input class="input" type="text" placeholder="Enter value" />
<input class="input error" type="text" placeholder="Error state" />
```

```css
.input {
  width: 100%; height: 48px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-xs);
  background: var(--surface-neutral-4);
  color: var(--content-neutral-3);
  font-family: 'Saira Condensed', Arial, sans-serif;
  font-size: var(--typography-font-size-s);
}

.input::placeholder { color: var(--content-neutral-1); }
.input:disabled     { opacity: var(--opacity-disabled); }
.input.error        { outline: var(--stroke-thin) solid var(--accent-danger-2); outline-offset: -1px; }
```

### Progress Bar

```html
<div class="progress">
  <div class="progress-fill" style="width: 65%"></div>
</div>
```

```css
.progress { width: 100%; height: 8px; background: var(--surface-neutral-4); border-radius: var(--radius-s); overflow: hidden; }
.progress-fill { height: 100%; background: var(--surface-primary-3); transition: width 0.4s ease-in-out; }
```

### Pill

```html
<span class="pill pill--disconnected">Not Connected</span>
<span class="pill pill--connecting">Connecting</span>
```

```css
.pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--radius-s);
  font-family: 'Saira Condensed', Arial, sans-serif;
  font-size: 13px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pill--disconnected { background: var(--surface-danger-3);  color: #fff; }
.pill--connecting   { background: var(--surface-warning-3); color: #000; }
```

### Typography

Use the `.typography.*` classes defined in the Typography section above:

```html
<p class="typography main-title-l">Page Title</p>
<p class="typography main-title-m">Section Title</p>
<p class="typography main-body-m">Body text</p>
<p class="typography main-body-s">Caption text</p>
<p class="typography card-label-s">STATUS LABEL</p>
```

Default text color is `var(--content-neutral-3)`; override per-context as needed.
