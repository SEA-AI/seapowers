# SEA.AI Documents (PDF, Word, Excel)

For one-pagers, spec sheets, reports, technical documents. PDF via WeasyPrint or ReportLab; Word
(.docx) via docx-js (see the docx skill for the npm `docx` package's own gotchas — page size,
table widths, numbering, etc. — this file covers SEA.AI brand styling specifically).

## Setup — Required HTML Boilerplate

**Tested and confirmed:** WeasyPrint mangles ✓, –, °, and other special characters into mojibake
(`â€"`, `âœ"`) without an explicit UTF-8 declaration. Always include it:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>/* ... */</style>
</head>
```

## Word Output: Fonts Are Referenced, Not Embedded

A `.docx` only stores the font *name* Barlow Semi Condensed / Barlow Semi Condensed Medium —
never the font file. On a machine that has the font installed it renders correctly; on one that
doesn't, Word silently substitutes a fallback (often a generic serif), and any styling that
depends on the font's own weight distinction (Medium vs Regular) disappears. Two consequences:
- Design heading hierarchies so they survive this (see Heading Hierarchy below) — color and case
  differences hold up under font substitution, weight-only differences don't.
- If a document needs to look right on machines without the font, that requires embedding fonts
  from within actual Microsoft Word (File → Options → Save → "Embed fonts in the file") — the
  `docx` npm package used to generate these files has no font-embedding capability, so this step
  can't be done at generation time.

## Logo in Documents (right-aligned, real image)

Use the transparent PNG from `assets/`, never text. In Word, put it in the page header, aligned to
the right margin:
```javascript
const logo = fs.readFileSync("assets/logo_black.png");           // ratio ~7.4:1
new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  children: [new ImageRun({ data: logo, transformation: { width: 104, height: 14 }, type: "png" })] })] })
```
In WeasyPrint/HTML: `<img src="assets/logo_black.png" style="height:5mm; float:right">` (set height only,
so the ratio is preserved). Pillow: `img.paste(logo, (x, y), logo)` after resizing with `thumbnail`.

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ SEA.AI [logo top-right]              PAGE NUMBER (red)│
├─────────────────────────────────────────────────────┤
│ SECTION LABEL (all caps, Focus Red)                  │
│                                                      │
│ Main Heading (sentence case, Black, Medium, 24-32pt) │
│ ─────────────────────── (red accent line, visible weight) │
│                                                      │
│ Body text (Black, Regular, 10-11pt, compact leading) │
│                                                      │
├─────────────────────────────────────────────────────┤
│ Footer: document name left | SEA.AI CONFIDENTIAL right│
└─────────────────────────────────────────────────────┘
```

## Color Application

- Page background: **White** (`#FFFFFF`)
- Section label text: **Focus Red** (`#CB0D00`)
- Body / heading text: **Black** (`#000000`)
- Tables: three distinct styles by content type — see Tables section below. Not a single
  universal rule; Night Blue fill is correct for Brand Card tables only, not comparison or
  spec-strip tables.
- Captions / footer: **Sky Grey** (`#7B9194`)
- Accent line under title: **Focus Red**, 1pt, ~85–90% of the title text width (never full width)

## Heading Hierarchy (H1–H4)

Tested and confirmed on a real multi-section document: differentiating heading levels by size
and weight alone ("Medium" at 15pt vs 12pt) is not enough to read as a clear hierarchy at a
glance, and it gets worse in Word specifically — a `.docx` generated with python-docx only
*references* a font by name (Word can embed fonts, but generated files don't), so on a machine
without Barlow Semi Condensed installed, Word silently substitutes a fallback font and every
"Medium" vs "Regular" distinction disappears, leaving nothing
but a small size difference between levels.

The fix: differentiate on **size, color, and case together**, not size alone. Color survives font
substitution completely (it's not a font property); size and ALL CAPS mostly do too. Weight names
don't.

| Level | Weight | Size | Color | Case | Use |
|---|---|---|---|---|---|
| **H1** | display (Regular, large) | 24–32pt | Black | Sentence case | Document title only. Pair with a Focus Red ALL CAPS kicker line above and a red accent rule below (see Line Element) |
| **H2** | Medium | 16–18pt | Black | Sentence case | Major sections. Same color as body — size and generous space-before (≥24pt) do the work of marking a new section |
| **H3** | Medium | 12–13pt | **Night Blue** | Sentence case | Subsections. Color is the primary differentiator from H2, not size — this is what makes it survive font substitution |
| **H4** | Medium | 9–10pt | **Sky Grey** | ALL CAPS, letter-spaced | Minor run-in headings inside a subsection. Reads as a quiet label, clearly the smallest tier |

Section label (a kicker line above H1, or a standalone eyebrow) is a fifth, non-heading role:
Medium, 9–10pt, Focus Red, ALL CAPS, letter-spaced — reserve Focus Red for this and for the H1
rule/kicker pair specifically, so it keeps signaling "top of hierarchy" rather than being diluted
across multiple heading levels.

Other text roles, unchanged:

| Element | Weight | Size | Case |
|---------|--------|------|------|
| Body text | Regular | 10–11pt | Normal |
| Table header | Medium | 10pt | ALL CAPS |
| Caption / footer | Regular | 8–9pt | Normal |

## Line Element (Accent Rule)

Per the brand book: **length is variable, not full-width.** It reads as an accent under a
heading or label, not a page-spanning divider. A good default: a bit shorter than the text it
sits under (roughly 85–90% of that text's rendered width), never stretched to the full content
width margin-to-margin — a full-width rule reads as a section divider, which is a different,
unrelated design element.

**⚠️ docx-js gotcha, tested and confirmed:** a `Paragraph`'s `border.bottom` does not reliably
render at the paragraph's actual width in Word/LibreOffice — it was observed stopping well short
of even the intended width, seemingly sized to the border-drawing's own minimal box rather than
the paragraph. Don't use a paragraph border for this. Use a shaded 1×1 table row instead, which
has an explicit, reliable width:
```javascript
function redRule(width = 3100) { // DXA; size to ~85-90% of the heading's own text width
  return new Table({
    width: { size: width, type: WidthType.DXA },
    columnWidths: [width],
    rows: [new TableRow({
      height: { value: 60, rule: "exact" },
      children: [new TableCell({
        width: { size: width, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: "CB0D00" },
        margins: { top: 0, bottom: 0, left: 0, right: 0 },
        borders: { top: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                   bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                   left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
                   right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
        children: [new Paragraph({ children: [new TextRun({ text: "", size: 2 })] })],
      })],
    })],
  });
}
```
A table has no paragraph `spacing` of its own — wrap it with empty spacer paragraphs before/after
if you need controlled vertical gaps.

## Page Margins

- Top / bottom: 14mm
- Left / right: 14mm
- Footer height: 8mm from bottom

## Split Layout (common pattern)

Half white / half Night Blue — used for Vision/Mission, Claims pages:
```
Left (white):  heading + body text in Black
Right (navy):  same content in White on #0B1731 background
Divider:       hard vertical cut at 50%, no gap
```

## Tables

Three distinct table styles are in production use — pick the one that matches the content, don't default to one for everything.

### 1. Brand Card table (category/label rows)

For structured reference tables like Claims/Product/Relations (Brand Book p.30 pattern):

```html
<!-- BRAND section: Focus Red fill, white text -->
<tr class="brand-row"><td class="label red">Claims</td><td>Content...</td></tr>

<!-- PRODUCT section: Ocean Teal fill, white text (Brand Book: "Ocean Green" — dark teal, not a green) -->
<tr class="product-row"><td class="label teal">Product</td><td>Content...</td></tr>

<!-- RELATIONS section: Fog White fill, black text -->
<tr class="relations-row"><td class="label fog">Topics</td><td>Content...</td></tr>
```

CSS:
```css
.label.red   { background: #CB0D00; color: #fff; }
.label.teal  { background: #06404C; color: #fff; }  /* Ocean Teal — NOT a green */
.label.fog   { background: #DFDED9; color: #000; font-weight: 500; }
td { border: 0.5pt solid #DFDED9; padding: 3mm 4mm; font-family: 'Barlow Semi Condensed', 'Arial Narrow'; }
```

### 2. Comparison table (feature-vs-competitor)

This is what SEA.AI's actual flyers and catalogue use for "SEA.AI vs. AIS/Radar" tables —
**no header fill at all**, just a thin red rule:

```html
<table class="comparison">
  <thead>
    <tr><th>SEA.AI vs. conventional assistance systems</th><th>AIS</th><th>RADAR</th><th class="hero">SEA.AI</th></tr>
  </thead>
  <tbody>
    <tr><td>Detecting persons in water / floating objects</td><td class="dash">–</td><td class="dash">–</td><td class="check hero">✓</td></tr>
  </tbody>
</table>
```

```css
.comparison thead th { font-weight: 500; color: #000; border-top: 1pt solid #CB0D00; border-bottom: 1pt solid #CB0D00; padding: 2mm 3mm; text-align: left; }
.comparison thead th.hero { color: #CB0D00; }  /* the product's own column, if this table has one */
.comparison tbody td { border-bottom: 0.5pt solid #DFDED9; padding: 2mm 3mm; }
.comparison td.check { color: #000; }
.comparison td.check.hero { color: #CB0D00; }  /* hero column checkmarks in red, all others black */
.comparison td.dash { color: #7B9194; }
```
Highlight at most one column as the "hero" (the product being sold) — checkmarks in that column go red, every other column (competitors, other systems) stays black/grey. Never fill the header row with a background color for this table type.

**⚠️ Don't reach for Brand Card's colors here.** A real mistake made building this skill: content
that is a genuine 3-column parallel comparison (e.g. three sequential funnel stages like
Lead/MQL/SQL, not "us vs. competitors") got styled by giving each column header its own Brand
Card color — Focus Red / Ocean Teal / Fog White fills side by side. That combination doesn't
exist anywhere in the source material. Brand Card's colored fills are documented for a
**label-column** layout (a category name in a colored cell, its content beside it — see pattern
1 above), not for parallel column headers. Any table with several *parallel* columns of the same
kind of thing (funnel stages, product tiers, plan levels) is a Comparison table and gets the thin
red rule treatment above, not colored header fills — even when there's no "hero" column to
highlight in red.

### 3. Detection-range / spec-strip table

A horizontal legend row, not a full grid — only the leftmost label cell gets a fill:

```html
<table class="spec-strip">
  <tr>
    <td class="label">Type of object</td>
    <td>Buoy, Person</td><td>Dinghy, RIB, Inflatable</td><td>Motorboat, Sailboat</td><td>Large Vessel</td>
  </tr>
  <tr>
    <td>Sentry</td><td>up to 700m</td><td>up to 3,000m</td><td>up to 7,500m</td><td>up to horizon</td>
  </tr>
</table>
```

```css
.spec-strip td.label { background: #0B1731; color: #fff; font-weight: 500; padding: 2mm 3mm; }
.spec-strip td { padding: 2mm 3mm; color: #000; }
.spec-strip tr:last-child { border-top: 0.5pt solid #000; }
```
Only the "Type of object" (or equivalent) cell is Night Blue — every other header cell stays unfilled white with an icon + label.

## Feature Panel Layout

The standard flyer spec-sheet pattern (used on every product flyer, page 3):
- Page splits roughly 2/3 white (left) / 1/3 Fog White (right), full page height
- Right panel: "FEATURES" in Focus Red ALL CAPS, then a plain checklist — black checkmark bullets, black body text, no card borders
- Left side: 2–4 sub-sections, each a Focus Red ALL CAPS mini-heading followed directly by a plain black paragraph (no box, no border)

```css
.spec-page { display: flex; }
.spec-page .content   { flex: 2; padding: 14mm; }
.spec-page .features  { flex: 1; background: #DFDED9; padding: 14mm; }
.feature-heading { color: #CB0D00; text-transform: uppercase; font-weight: 500; font-size: 11pt; margin-bottom: 2mm; }
.checklist li { color: #000; }
.checklist li::marker { content: "✓  "; color: #000; }  /* black checkmark, not red */
```

## Full-Bleed Stat Band

For a "by the numbers" moment inside a document (Catalogue "1 billion / 18 million" pattern):
full-width Night Blue band, giant stat number, small-caps label above and caption below.

```html
<div class="stat-band">
  <div class="stat"><span class="over">over</span> <span class="number">1 billion</span>
    <div class="caption">recorded real-life images</div></div>
</div>
```

```css
.stat-band { background: #0B1731; padding: 14mm; }
.stat .over { color: #fff; font-size: 9pt; text-transform: uppercase; vertical-align: super; }
.stat .number { color: #fff; font-weight: 400; font-size: 48pt; }  /* Regular/Light weight, not Medium — this is display type */
.stat .caption { color: #fff; font-size: 9pt; font-weight: 500; text-transform: uppercase; }
```

## WeasyPrint CSS Base

```css
@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@300;400;500&display=swap');

body {
  font-family: 'Barlow Semi Condensed', 'Arial Narrow', Arial, sans-serif;
  font-size: 10.5pt;
  color: #000000;
  background: #ffffff;
  margin: 14mm;
  line-height: 1.3;
}

h1 { font-weight: 400; color: #000000; font-size: 28pt; }   /* 24–32pt, Regular display */
h2 { font-weight: 500; color: #000000; font-size: 17pt; }   /* 16–18pt, Medium — no Bold weight available */
h3 { font-weight: 500; color: #0B1731; font-size: 12.5pt; } /* 12–13pt */
h4 { font-weight: 500; color: #7B9194; font-size: 9.5pt; text-transform: uppercase; letter-spacing: 0.08em; }
.section-label { color: #CB0D00; font-weight: 500; font-size: 9pt; text-transform: uppercase; letter-spacing: 0.08em; }
.red-line { border: none; border-top: 1pt solid #CB0D00; margin: 3mm 0; width: 60mm; }  /* set to ~85–90% of the heading text width */
.footer { color: #7B9194; font-size: 8pt; border-top: 0.5pt solid #DFDED9; padding-top: 2mm; }
```

## ReportLab Patterns (for Python)

```python
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

FOCUS_RED   = HexColor("#CB0D00")
NIGHT_BLUE  = HexColor("#0B1731")
OCEAN_TEAL  = HexColor("#06404C")  # Brand Book: "Ocean Green" — visually dark teal, NOT green
SKY_GREY    = HexColor("#7B9194")
FOG_WHITE   = HexColor("#DFDED9")

# Section label
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont('Barlow-Medium', 'assets/BarlowSemiCondensed-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Barlow', 'assets/BarlowSemiCondensed-Regular.ttf'))

canvas.setFont("Barlow-Medium", 9)
canvas.setFillColor(FOCUS_RED)
canvas.drawString(14*mm, y, "SECTION LABEL")
```

## Checklist

- [ ] White page background
- [ ] Logo top-right — the real image asset, never drawn as text
- [ ] Section labels: ALL CAPS, Focus Red, Medium
- [ ] Main heading (H1): Sentence case, Black, display weight
- [ ] H2/H3/H4 differentiated by color and case, not size/weight alone (Black / Night Blue / Sky
      Grey ALL CAPS) — survives font substitution, see Heading Hierarchy
- [ ] Red accent line under title: shorter than the title text, not full content width
- [ ] Footer: document name + CONFIDENTIAL in Sky Grey
- [ ] Barlow Semi Condensed font loaded from assets (or Google Fonts CDN)
- [ ] `<meta charset="utf-8">` present — otherwise ✓/–/° render as mojibake
- [ ] Table style matches content: Brand Card (label-column, category rows) / Comparison (parallel
      columns, no header fill, red rule) / Spec-strip (only label cell filled) — never Brand
      Card's colors applied to parallel column headers
- [ ] Colors from brand palette only: Focus Red, Night Blue, Ocean Teal, Sky Grey, Fog White, Black, White
- [ ] No gradients or shadows
- [ ] No em dashes in any copy text
