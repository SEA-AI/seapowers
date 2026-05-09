# SEA.AI Diagrams & Infographics

For Python-rendered PNGs using Pillow. Read this before creating any diagram, chart, or infographic.

## Canvas Setup

```python
from PIL import Image, ImageDraw, ImageFont
import os

# Skill asset path — resolve from this script's location or use absolute
SKILL_ASSETS = "/path/to/sea-ai-brand/assets"  # update per session

# Brand colors
RED     = "#CB0D00"   # Focus Red — labels only
NAVY    = "#0B1731"   # Night Blue — dark panels
TEAL    = "#06404C"   # Ocean Teal — secondary (Brand Book: "Ocean Green" — NOT a green, dark teal)
GREY    = "#7B9194"   # Sky Grey — captions, muted
FOG     = "#DFDED9"   # Fog White — subtle backgrounds
BLACK   = "#000000"   # body text
WHITE   = "#FFFFFF"   # canvas background

# Font loader
def font(size, bold=False):
    path = os.path.join(SKILL_ASSETS,
        "BarlowSemiCondensed-Bold.ttf" if bold else "BarlowSemiCondensed-Regular.ttf")
    return ImageFont.truetype(path, size)

# Standard canvas: 1600×900 (16:9), white background
W, H = 1600, 900
img = Image.new("RGB", (W, H), WHITE)
draw = ImageDraw.Draw(img)
```

## Layout Rules

### Background
- **Always white** (`#FFFFFF`) for content diagrams
- Night Blue (`#0B1731`) only for full dark panel (e.g. a header strip or sidebar)
- Never dark-on-dark, never full dark canvas for infographics

### Section Label (top-left)
```python
# Section label: ALL CAPS, Focus Red, Bold, ~13px
draw.text((60, 28), "DIAGRAM TITLE", font=font(13, bold=True), fill=RED)
# Optional thin red line below label
draw.line([(60, 50), (W-60, 50)], fill=RED, width=1)
```

### Content Heading
```python
# Main heading: Sentence case or SHORT CAPS, Black, Bold, ~28-36px
draw.text((60, 65), "Main Heading", font=font(32, bold=True), fill=BLACK)
# Subheading: Sentence case, Sky Grey, Regular, ~16px
draw.text((60, 105), "Subtitle or description", font=font(16), fill=GREY)
```

### Body Text & Labels
```python
# Body: Black, Regular, 12–14px
draw.text((x, y), "Body text", font=font(13), fill=BLACK)
# Muted label: Sky Grey, Regular, 10–11px
draw.text((x, y), "LABEL", font=font(10, bold=True), fill=GREY)
# Red label (section): ALL CAPS, Red, Bold, 10–12px
draw.text((x, y), "SECTION", font=font(11, bold=True), fill=RED)
```

## Card / Panel Patterns

### Light card (default)
```python
# Fog White background, no border, subtle separation
draw.rounded_rectangle([x, y, x+w, y+h], radius=4, fill=FOG)
```

### Dark panel (header or accent)
```python
# Night Blue fill, white text
draw.rounded_rectangle([x, y, x+w, y+h], radius=4, fill=NAVY)
draw.text((x+16, y+12), "PANEL TITLE", font=font(13, bold=True), fill=WHITE)
```

### Red accent bar (top of card, structural — not decorative)
```python
# Thin red top bar to anchor a section
draw.rectangle([x, y, x+w, y+3], fill=RED)
```

### Table rows (like Brand Cards)
```python
# Header row: Ocean Green fill, white text
draw.rectangle([x, y, x+w, y+row_h], fill=TEAL)
draw.text((x+12, y+8), "CATEGORY", font=font(12, bold=True), fill=WHITE)

# Alternating rows: Fog White / White
draw.rectangle([x, y, x+w, y+row_h], fill=FOG if i % 2 == 0 else WHITE)
draw.text((x+12, y+8), "Content text", font=font(12), fill=BLACK)
```

## Arrows & Connectors

```python
import math

def draw_arrow(draw, x1, y1, x2, y2, color=GREY, width=2):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    angle = math.atan2(y2-y1, x2-x1)
    size = 9
    draw.polygon([
        (x2, y2),
        (x2 - size*math.cos(angle-0.4), y2 - size*math.sin(angle-0.4)),
        (x2 - size*math.cos(angle+0.4), y2 - size*math.sin(angle+0.4)),
    ], fill=color)
```

Use `BLACK` or `GREY` for neutral arrows, `RED` only for critical/alert flows.

## Range / Progress Bars

```python
BAR_BG   = FOG    # background track
BAR_FILL = NAVY   # filled portion (or TEAL for secondary)

# Background
draw.rounded_rectangle([x, y, x+bar_w, y+bar_h], radius=3, fill=BAR_BG)
# Fill
draw.rounded_rectangle([x, y, x+fill_w, y+bar_h], radius=3, fill=BAR_FILL)
# Label right of bar
draw.text((x+fill_w+8, y-1), "Label text", font=font(12, bold=True), fill=BLACK)
```

## Footer

```python
# Every diagram gets a footer
footer_y = H - 28
draw.line([(60, footer_y-6), (W-60, footer_y-6)], fill=FOG, width=1)
draw.text((60, footer_y), "SEA.AI", font=font(10, bold=True), fill=GREY)
draw.text((W-60, footer_y), "CONFIDENTIAL", font=font(10), fill=GREY,
    anchor="ra")  # right-aligned
```

## Common Mistakes to Avoid

```
❌ Dark background for the whole canvas → use WHITE
❌ Blue (#0A67C2 or similar) → not a brand color, use NAVY or remove
❌ Green (#2DA84F) or Amber (#F1B80D) → not brand colors
❌ Gradient fills → flat color only
❌ Drop shadows → none
❌ Circles/icons in blue → use NAVY or FOG
❌ Red as large background fill → red is for thin lines and labels only
❌ DejaVu or other system fonts → always use BarlowSemiCondensed-*.ttf from assets
```

## Save

```python
# Always save at 150 DPI to workspace
out = "/path/to/output/diagram_name.png"
img.save(out, "PNG", dpi=(150, 150))
```

## Checklist Before Saving

- [ ] White canvas background
- [ ] Section label: ALL CAPS, Focus Red, Barlow Semi Condensed Bold
- [ ] Body text: Black, Barlow Semi Condensed Regular
- [ ] No non-brand colors
- [ ] No gradients, no shadows
- [ ] Footer present (SEA.AI + CONFIDENTIAL in Sky Grey)
- [ ] Font loaded from `assets/BarlowSemiCondensed-*.ttf`
