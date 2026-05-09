---
File: sea-ai-brand
Description: Core Frontend UI Component Library Reference
Creator: Claude
Date: 2026-05-09
---

# Frontend Components

HTML + CSS snippets to match the SEA.AI UI look & feel. All use design tokens from `ui-coding.md`.

## Component Index

| Component | Use |
|-----------|-----|
| Button | Primary/secondary actions |
| Toggle | On/off switch |
| Checkbox | Multi-select option |
| Input | Text entry |
| Progress Bar | Linear progress |
| Circular Progress | Radial progress |
| Pill | Connection/status badge |
| Typography | Text hierarchy |

---

## Button

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
  font-family: 'Barlow Semi Condensed', Arial, sans-serif;
  font-size: 16px;
  cursor: pointer;
  transition: 0.2s;
  gap: 8px;
}

.btn--primary   { background: var(--surface-primary-3); color: var(--content-primary-3); }
.btn--secondary { background: var(--surface-neutral-4); color: var(--content-neutral-3); }
.btn--danger    { background: var(--surface-danger-3);  color: #fff; }
.btn--ghost     { background: transparent; color: var(--content-neutral-3); border: 1px solid var(--surface-neutral-4); }

.btn:disabled   { opacity: 0.3; pointer-events: none; }
```

---

## Toggle

```html
<!-- unchecked -->
<label class="toggle">
  <input type="checkbox" />
  <span class="track"><span class="thumb"></span></span>
</label>

<!-- checked -->
<label class="toggle">
  <input type="checkbox" checked />
  <span class="track"><span class="thumb"></span></span>
</label>
```

```css
.toggle { display: inline-flex; align-items: center; cursor: pointer; }
.toggle input { display: none; }

.track {
  width: 40px;
  height: 25px;
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

.toggle input:checked ~ .track              { background: var(--surface-neutral-5); }
.toggle input:checked ~ .track .thumb      { left: 17px; background: var(--surface-primary-3); }
```

---

## Checkbox

```html
<label class="checkbox">
  <input type="checkbox" />
  <span class="box"></span>
  <span class="checkbox-label">Enable feature</span>
</label>
```

```css
.checkbox { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.checkbox input { display: none; }

.box {
  width: 18px; height: 18px;
  border-radius: var(--radius-s);
  border: 1.5px solid var(--surface-neutral-5);
  background: var(--surface-neutral-4);
  transition: 0.2s;
}

.checkbox input:checked ~ .box {
  background: var(--surface-primary-3);
  border-color: var(--surface-primary-3);
}

.checkbox-label {
  font-family: 'Barlow Semi Condensed', Arial, sans-serif;
  font-size: 16px;
  color: var(--content-neutral-3);
}
```

---

## Input

```html
<input class="input" type="text" placeholder="Enter value" />
<input class="input error" type="text" placeholder="Error state" />
```

```css
.input {
  width: 100%;
  height: 48px;
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-xs);
  background: var(--surface-neutral-4);
  color: var(--content-neutral-3);
  font-family: 'Barlow Semi Condensed', Arial, sans-serif;
  font-size: 16px;
}

.input::placeholder { color: var(--content-neutral-1); }
.input:disabled     { opacity: 0.3; }
.input.error        { outline: 1px solid var(--accent-danger-2); outline-offset: -1px; }
```

---

## Progress Bar

```html
<div class="progress">
  <div class="progress-fill" style="width: 65%"></div>
</div>
```

```css
.progress {
  width: 100%;
  height: 8px;
  background: var(--surface-neutral-4);
  border-radius: var(--radius-s);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--surface-primary-3);
  border-radius: inherit;
  transition: width 0.4s ease-in-out;
}
```

---

## Pill (Status Badge)

```html
<span class="pill pill--connected">Connected</span>
<span class="pill pill--disconnected">Not Connected</span>
<span class="pill pill--connecting">Connecting</span>
```

```css
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-s);
  font-family: 'Barlow Semi Condensed', Arial, sans-serif;
  font-size: 13px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pill--connected    { background: var(--surface-success-3);  color: #fff; }
.pill--disconnected { background: var(--surface-danger-3);   color: #fff; }
.pill--connecting   { background: var(--surface-warning-3);  color: #000; }
```

---

## Typography

```html
<p class="text-title-l">Page Title</p>
<p class="text-title-m">Section Title</p>
<p class="text-body-m">Body text for descriptions and content.</p>
<p class="text-body-s">Small body text for captions.</p>
<p class="text-label">STATUS LABEL</p>
```

```css
.text-title-l, .text-title-m, .text-body-m, .text-body-s, .text-label {
  font-family: 'Barlow Semi Condensed', Arial, sans-serif;
  color: var(--content-neutral-3);
  margin: 0;
}

.text-title-l { font-size: 40px; font-weight: 500; line-height: 48px; }
.text-title-m { font-size: 24px; font-weight: 500; line-height: 32px; }
.text-body-m  { font-size: 20px; font-weight: 400; line-height: 28px; }
.text-body-s  { font-size: 16px; font-weight: 400; line-height: 24px; }
.text-label   { font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; color: var(--content-neutral-2); }
```
