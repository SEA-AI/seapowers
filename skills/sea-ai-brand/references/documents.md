# SEA.AI Documents (PDF, Word, Excel)

For one-pagers, spec sheets, reports, technical documents rendered with WeasyPrint or ReportLab.

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ SEA.AI [logo top-right]              PAGE NUMBER (red)│
├─────────────────────────────────────────────────────┤
│ SECTION LABEL (all caps, Focus Red)                  │
│                                                      │
│ Main Heading (sentence case, Black, Bold, 24-32pt)   │
│ ─────────────────────── (thin red line)              │
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
- Table header rows: **Night Blue** (`#0B1731`) fill, white text
- Table alt rows: **Fog White** (`#DFDED9`) and White alternating
- Captions / footer: **Sky Grey** (`#7B9194`)
- Accent line under title: **Focus Red**, 1pt, full width

## Typography Scale

| Element | Weight | Size | Case |
|---------|--------|------|------|
| Section label | Bold | 10pt | ALL CAPS |
| Page heading | Bold | 24–32pt | Sentence / SHORT CAPS |
| Subheading | Bold | 14–16pt | Sentence case |
| Body text | Regular | 10–11pt | Normal |
| Table header | Bold | 10pt | ALL CAPS |
| Caption / footer | Regular | 8–9pt | Normal |

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

## Tables (Brand Card style)

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
.label.fog   { background: #DFDED9; color: #000; font-weight: bold; }
td { border: 0.5pt solid #DFDED9; padding: 3mm 4mm; font-family: 'Barlow Semi Condensed', 'Arial Narrow'; }
```

## WeasyPrint CSS Base

```css
@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;700&display=swap');

body {
  font-family: 'Barlow Semi Condensed', 'Arial Narrow', Arial, sans-serif;
  font-size: 10.5pt;
  color: #000000;
  background: #ffffff;
  margin: 14mm;
  line-height: 1.3;
}

h1, h2, h3 { font-weight: bold; color: #000000; }
.section-label { color: #CB0D00; font-weight: bold; font-size: 9pt; text-transform: uppercase; letter-spacing: 0.08em; }
.red-line { border: none; border-top: 1pt solid #CB0D00; margin: 3mm 0; }
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

pdfmetrics.registerFont(TTFont('Barlow-Bold', 'assets/BarlowSemiCondensed-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Barlow', 'assets/BarlowSemiCondensed-Regular.ttf'))

canvas.setFont("Barlow-Bold", 9)
canvas.setFillColor(FOCUS_RED)
canvas.drawString(14*mm, y, "SECTION LABEL")
```

## Checklist

- [ ] White page background
- [ ] Logo top-right (black version on white)
- [ ] Section labels: ALL CAPS, Focus Red, Bold
- [ ] Main heading: Sentence case, Black, Bold
- [ ] Red accent line under title
- [ ] Footer: document name + CONFIDENTIAL in Sky Grey
- [ ] Barlow Semi Condensed font loaded from assets (or Google Fonts CDN)
- [ ] No non-brand colors (UI surface colors like #101214 are product-only)
- [ ] No gradients or shadows
