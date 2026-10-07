# SEA.AI Diagrams & Infographics

For Python-rendered PNGs using Pillow. Read this before creating any diagram, chart, or infographic.

## Canvas Setup

```python
from PIL import Image, ImageDraw, ImageFont
import os

# Skill asset path — resolve from this script's location or use absolute
SKILL_ASSETS = "/path/to/sea-ai-brand/assets"  # update per session

# Brand colors
RED     = "#CB0D00"   # Focus Red — labels, filled buttons, primary detection box, accent rules
NAVY    = "#0B1731"   # Night Blue — dark panels
TEAL    = "#06404C"   # Ocean Teal — secondary (Brand Book: "Ocean Green" — NOT a green, dark teal)
GREY    = "#7B9194"   # Sky Grey — captions, muted
FOG     = "#DFDED9"   # Fog White — subtle backgrounds
BLACK   = "#000000"   # body text
WHITE   = "#FFFFFF"   # canvas background

# Font loader — no Bold weight available; use Medium for emphasis, Regular for body
def font(size, medium=False):
    path = os.path.join(SKILL_ASSETS,
        "BarlowSemiCondensed-Medium.ttf" if medium else "BarlowSemiCondensed-Regular.ttf")
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
# Section label: ALL CAPS, Focus Red, Medium, ~13px
draw.text((60, 28), "DIAGRAM TITLE", font=font(13, medium=True), fill=RED)
# Optional thin red line below label
draw.line([(60, 50), (W-60, 50)], fill=RED, width=1)
```

### Content Heading
```python
# Main heading: Sentence case or SHORT CAPS, Black, Medium, ~28-36px
draw.text((60, 65), "Main Heading", font=font(32, medium=True), fill=BLACK)
# Subheading: Sentence case, Sky Grey, Regular, ~16px
draw.text((60, 105), "Subtitle or description", font=font(16), fill=GREY)
```

### Body Text & Labels
```python
# Body: Black, Regular, 12–14px
draw.text((x, y), "Body text", font=font(13), fill=BLACK)
# Muted label: Sky Grey, Regular, 10–11px
draw.text((x, y), "LABEL", font=font(10, medium=True), fill=GREY)
# Red label (section): ALL CAPS, Red, Medium, 10–12px
draw.text((x, y), "SECTION", font=font(11, medium=True), fill=RED)
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
draw.text((x+16, y+12), "PANEL TITLE", font=font(13, medium=True), fill=WHITE)
```

### Red accent line (structural — not decorative)
```python
# Give the line visible weight — it should NOT read as a hairline.
# Length is variable to fit context; color is always RED.
draw.rectangle([x, y, x+w, y+3], fill=RED)
```

### Detection box (product-mark component)
```python
# Marks a detected object in a product screenshot/mockup.
# Focus Red = the highlighted/primary detection (use at most once per scene).
# Night Blue = secondary detections in the same scene.
# On dark/low-light photography, use low_light=True: white outline brackets, no filled pill —
# a solid red/navy pill is too heavy against dark imagery.
def draw_detection_box(draw, x, y, box_w, box_h, label=None, primary=False, low_light=False):
    color = WHITE if low_light else (RED if primary else NAVY)
    if label and not low_light:
        draw.rounded_rectangle([x, y-28, x+70, y], radius=4, fill=color)
        draw.text((x+10, y-22), label, font=font(12, medium=True), fill=WHITE)
    # Dashed corner brackets at all four corners of the detected object's bounds
    bracket = 14
    corners = [(x, y, 1, 1), (x+box_w, y, -1, 1), (x, y+box_h, 1, -1), (x+box_w, y+box_h, -1, -1)]
    for cx, cy, dx, dy in corners:
        for off in range(0, bracket, 6):
            end = min(off + 3, bracket)
            draw.line([(cx+dx*off, cy), (cx+dx*end, cy)], fill=color, width=2)
            draw.line([(cx, cy+dy*off), (cx, cy+dy*end)], fill=color, width=2)
```
Never use more than one Focus Red detection box in the same scene — additional detections use Night Blue.

### Buttons
```python
# Primary — filled Focus Red, white ALL CAPS label
draw.rounded_rectangle([x, y, x+w, y+h], radius=6, fill=RED)
draw.text((x+w/2, y+h/2), "LEARN MORE", font=font(13, medium=True), fill=WHITE, anchor="mm")

# Secondary — Focus Red outline, Focus Red ALL CAPS label, transparent/white fill
draw.rounded_rectangle([x, y, x+w, y+h], radius=6, outline=RED, width=2)
draw.text((x+w/2, y+h/2), "LEARN MORE", font=font(13, medium=True), fill=RED, anchor="mm")
```

### Checkmarks — draw them, don't rely on the ✓ character

**Tested and confirmed broken:** Barlow Semi Condensed has no ✓ glyph — Pillow renders a tofu box
instead (no automatic font fallback, unlike browsers/WeasyPrint). Draw checkmarks as two line
segments instead of using the Unicode character:
```python
def draw_check(draw, x, y, size=12, color=BLACK):
    draw.line([(x, y+size*0.5), (x+size*0.35, y+size*0.8), (x+size, y)], fill=color, width=2, joint="curve")
```
Use `draw_check()` everywhere a checkmark is needed in Pillow output (comparison tables, feature
checklists). This doesn't apply to HTML/CSS output (`documents.md`) — browsers and WeasyPrint do
font fallback automatically, so the ✓ character is fine there.

### Tables — three distinct styles, pick by content (not one default)

**1. Brand Card table** (category/label rows — Claims/Product/Relations pattern):
```python
# Header row: Ocean Green fill, white text
draw.rectangle([x, y, x+w, y+row_h], fill=TEAL)
draw.text((x+12, y+8), "CATEGORY", font=font(12, medium=True), fill=WHITE)

# Alternating rows: Fog White / White
draw.rectangle([x, y, x+w, y+row_h], fill=FOG if i % 2 == 0 else WHITE)
draw.text((x+12, y+8), "Content text", font=font(12), fill=BLACK)
```

**2. Comparison table** (feature-vs-competitor — the real pattern used in flyers/catalogue):
No header fill — a thin red rule above and below the header row is the only accent. Highlight at
most one "hero" column (the product being sold): its checkmarks are red, every other column
(competitors) stays black/grey. Never fill this header row with a background color.
```python
def draw_comparison_row(draw, x, y, w, row_h, cells, hero_col=None, is_header=False):
    if is_header:
        draw.line([(x, y), (x+w, y)], fill=RED, width=1)
        draw.line([(x, y+row_h), (x+w, y+row_h)], fill=RED, width=1)
    else:
        draw.line([(x, y+row_h), (x+w, y+row_h)], fill=FOG, width=1)
    col_w = w / len(cells)
    for i, cell in enumerate(cells):
        cx, cy = x + i*col_w + 8, y+8
        if cell == "check":
            draw_check(draw, cx, cy+2, size=12, color=RED if i == hero_col else BLACK)
        else:
            color = RED if (i == hero_col and not is_header) else (GREY if cell == "–" else BLACK)
            draw.text((cx, cy), cell, font=font(12, medium=is_header), fill=color)
```

**3. Detection-range / spec-strip table**: only the first label cell is Night Blue-filled — every
other header cell is plain white with an icon + label, not a filled row.
```python
draw.rectangle([x, y, x+label_w, y+row_h], fill=NAVY)
draw.text((x+10, y+8), "Type of object", font=font(11, medium=True), fill=WHITE)
# Remaining header cells: no fill, icon + label on white
draw.text((x+label_w+10, y+8), "Buoy, Person", font=font(11), fill=BLACK)
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
draw.text((x+fill_w+8, y-1), "Label text", font=font(12, medium=True), fill=BLACK)
```

## Feature Panel (flyer spec-sheet pattern)

Right third of canvas: solid Fog White panel, full height. Red ALL CAPS heading, then a plain
checklist with black checkmark bullets and black body text — no card borders.
```python
def draw_feature_panel(draw, x, y, w, h, title, items):
    draw.rectangle([x, y, x+w, y+h], fill=FOG)
    draw.text((x+20, y+20), title, font=font(14, medium=True), fill=RED)
    iy = y + 60
    for item in items:
        draw_check(draw, x+20, iy+4, size=13, color=BLACK)
        draw.text((x+40, iy), item, font=font(13), fill=BLACK)
        iy += 32
```
Left side of the same layout: 2–4 sections, each a Focus Red ALL CAPS mini-heading directly
followed by a plain black paragraph — no box, no border around it.

## Full-Bleed Stat Band

Full-width Night Blue band with a giant stat number — display type, not a label, so use Regular
weight (or Light if available) at large size, not Medium.
```python
def draw_stat_band(draw, x, y, w, h, over_label, number, caption):
    draw.rectangle([x, y, x+w, y+h], fill=NAVY)
    draw.text((x+40, y+30), over_label.upper(), font=font(10, medium=True), fill=WHITE)
    draw.text((x+40, y+50), number, font=font(56), fill=WHITE)  # Regular, large — display type
    draw.text((x+40, y+120), caption.upper(), font=font(10, medium=True), fill=WHITE)
```

## Footer

```python
# Every diagram gets a footer
footer_y = H - 28
draw.line([(60, footer_y-6), (W-60, footer_y-6)], fill=FOG, width=1)
draw.text((60, footer_y), "SEA.AI", font=font(10, medium=True), fill=GREY)
draw.text((W-60, footer_y), "CONFIDENTIAL", font=font(10), fill=GREY,
    anchor="ra")  # right-aligned
```

## Common Mistakes to Avoid

```
❌ Dark background for the whole canvas → use WHITE
❌ Blue (#0A67C2 or similar) → not a brand color, use NAVY or remove
❌ Green (#2DA84F) or Amber (#F1B80D) → not brand colors
❌ UI surface colors (#101214, #181B1E etc.) → product UI only, never in diagrams
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
- [ ] Section label: ALL CAPS, Focus Red, Barlow Semi Condensed Medium
- [ ] Body text: Black, Barlow Semi Condensed Regular
- [ ] No non-brand colors
- [ ] No gradients, no shadows
- [ ] Footer present (SEA.AI + CONFIDENTIAL in Sky Grey)
- [ ] Font loaded from `assets/BarlowSemiCondensed-*.ttf`
- [ ] Checkmarks drawn with `draw_check()`, never the raw "✓" character (missing glyph → tofu box)
- [ ] No em dashes in any copy/text
