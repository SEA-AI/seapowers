# SEA.AI Presentations (PPTX)

For board decks, investor presentations, sales decks. Uses pptxgenjs via Node.js.

## Slide Types

### Title / Cover Slide — split Night Blue / photo, logo top-LEFT

Logo sits top-**left** here specifically because the photo occupies the right panel — this is
the photo-legibility exception, not a "Night Blue slides use top-left" rule. A solid Night Blue
divider slide with no photo (see Section Divider below) keeps the logo top-right like everything
else. Confirmed against a real production deck.
```javascript
// Left ~48%: Night Blue panel. Right ~52%: full-bleed photo.
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 4.8, h: 5.63,
  fill: { color: "0B1731" }, line: { color: "0B1731" } });
slide.addImage({ path: "assets/logo_white.png",
  x: 0.5, y: 0.4, w: 1.6, h: 0.215 });  // logo ratio is ~7.4:1, never stretch  // top-LEFT on this slide type only
slide.addText([
  { text: "Click to edit\n", options: { color: "FFFFFF" } },
  { text: "Click to edit.", options: { color: "CB0D00" } },
], { x: 0.5, y: 2.3, w: 4, h: 1.2, fontSize: 32, fontFace: "Barlow Semi Condensed" });
slide.addText("Company Presentation\nLinz, Jan 2026", { x: 0.5, y: 4.6, w: 4, h: 0.6,
  color: "FFFFFF", fontSize: 12, fontFace: "Barlow Semi Condensed" });
slide.addImage({ path: "photo.jpg", x: 4.8, y: 0, w: 5.2, h: 5.63 });
```
Two-line headline convention: first line white, second line **Focus Red** — this pattern (a
white line followed by a red line, or a red keyword/clause inline within one sentence) recurs
throughout the deck as the standard way to add emphasis to any headline. Prefer it over bolding.

### Section Divider — solid Night Blue, no photo, logo top-right

Confirmed from a real production deck: a full Night Blue background with no photo keeps the logo
top-right, same as a white content slide. Don't apply the title-slide's top-left placement here —
that placement was about the photo, not the color.
```javascript
slide.background = { color: "0B1731" };
slide.addImage({ path: "assets/logo_white.png", x: 7.9, y: 0.35, w: 1.6, h: 0.215 });  // top-right, white
slide.addText("OTHER MARKETING INFOS", { x: 0.5, y: 3.5, w: 8, h: 0.5,
  color: "CB0D00", fontSize: 20, fontFace: "Barlow Semi Condensed", charSpacing: 1 });
slide.addText("Supporting body copy in white.", { x: 0.5, y: 4.2, w: 8, h: 0.8,
  color: "FFFFFF", fontSize: 14, fontFace: "Barlow Semi Condensed" });
```

### Content Slide — White background, logo top-right

```javascript
slide.background = { color: "FFFFFF" };
// Section label top-left: ALL CAPS Focus Red (sentence-case "Headline" placeholder also seen —
// either ALL CAPS label or a short red kicker phrase is acceptable, not both stacked)
slide.addText("THE SECTION LABEL", { x: 0.5, y: 0.2, w: 6, h: 0.25,
  color: "CB0D00", fontSize: 9, fontFace: "Barlow Semi Condensed Medium", charSpacing: 1 });
// Logo top-right (black on white)
slide.addImage({ path: "assets/logo_black.png",
  x: 8.4, y: 0.22, w: 1.1, h: 0.148 });
// Main heading — put the emphasized clause in Focus Red inline, not the whole line
slide.addText([
  { text: "Lorem ipsum dolor ", options: { color: "000000" } },
  { text: "sit amet.", options: { color: "CB0D00" } },
], { x: 0.5, y: 0.65, w: 9, h: 0.6, fontSize: 24, fontFace: "Barlow Semi Condensed" });
// Page number bottom-right: small, black, not Focus Red (page numbers are red only on dark slides)
slide.addText("12", { x: 9.0, y: 5.35, w: 0.5, h: 0.25,
  color: "000000", fontSize: 9, align: "right" });
```

### Agenda Slide

```javascript
// Numbered items: small red-outlined circle with number, item text to the right
const items = ["Lorem ipsum Lorem ipsum", "Lorem ipsum Lorem ipsum", /* ... */];
items.forEach((item, i) => {
  const y = 1.2 + i * 0.55;
  slide.addShape(pptx.ShapeType.ellipse, { x: 0.5, y, w: 0.35, h: 0.35,
    fill: { type: "none" }, line: { color: "CB0D00", width: 1 } });
  slide.addText(String(i + 1).padStart(2, "0"), { x: 0.5, y, w: 0.35, h: 0.35,
    color: "CB0D00", fontSize: 10, align: "center", valign: "middle" });
  slide.addText(item, { x: 1.0, y, w: 8, h: 0.35, color: "000000", fontSize: 13, valign: "middle" });
});
```

### Numbered Feature Card Grid (3 or 4 columns)

Night Blue cards in a row, big white number, thin red underline, title, body, ALL CAPS caption
at the card's bottom edge.

**⚠️ Alignment gotcha, tested and confirmed:** pptxgenjs text boxes carry a default internal
margin/inset (~0.1in), but shapes (rectangles, lines) don't. Put a text box and a shape at the
same `x` and their *visible* left edges won't match — the text sits noticeably right of the
shape. This showed up exactly here: the red underline (a shape) didn't line up with the number
and title above/below it (text boxes) despite identical `x` values. Fix: set `margin: [0,0,0,0]`
on every text box that needs to align with a shape.

```javascript
const NOMARGIN = [0, 0, 0, 0];
const cards = [{ n: "01", title: "Threat Detection", body: "...", caption: "HIGH-PERFORMANCE AUTOMATED LOOKOUT." }, /* ... */];
const cardW = 9.0 / cards.length;
cards.forEach((c, i) => {
  const x = 0.5 + i * cardW;
  const textX = x + 0.2; // shared left edge for the number, the rule, and the title below
  slide.addShape(pptx.ShapeType.rect, { x: x, y: 1.4, w: cardW - 0.15, h: 3.8,
    fill: { color: "0B1731" }, line: { color: "0B1731" } });
  slide.addText(c.n, { x: textX, y: 1.6, w: cardW - 0.4, h: 0.7,
    color: "FFFFFF", fontSize: 36, fontFace: "Barlow Semi Condensed", margin: NOMARGIN });
  slide.addShape(pptx.ShapeType.rect, { x: textX, y: 2.35, w: 0.35, h: 0.02, fill: { color: "CB0D00" } });
  slide.addText(c.title, { x: textX, y: 2.5, w: cardW - 0.4, h: 0.35,
    color: "FFFFFF", fontSize: 14, fontFace: "Barlow Semi Condensed Medium", margin: NOMARGIN });
  slide.addText(c.body, { x: textX, y: 2.9, w: cardW - 0.4, h: 1.4,
    color: "FFFFFF", fontSize: 10, fontFace: "Barlow Semi Condensed", margin: NOMARGIN });
  slide.addText(c.caption, { x: textX, y: 4.9, w: cardW - 0.4, h: 0.4,
    color: "FFFFFF", fontSize: 9, fontFace: "Barlow Semi Condensed Medium", charSpacing: 1, margin: NOMARGIN });
});
```

### Split Content Slide — photo left / vertical-red-line list right

```javascript
slide.addImage({ path: "photo.jpg", x: 0, y: 0, w: 4.8, h: 5.63 });
// Each list item: a red vertical rule to the left of a Medium-weight title + regular text
const items = [{ title: "Title", text: "Text" }, /* up to 4 */];
items.forEach((it, i) => {
  const y = 2.2 + i * 0.75;
  slide.addShape(pptx.ShapeType.rect, { x: 4.8, y: y, w: 0.03, h: 0.6, fill: { color: "CB0D00" } });
  slide.addText(it.title, { x: 5.0, y: y, w: 4, h: 0.3, color: "000000", fontSize: 13, fontFace: "Barlow Semi Condensed Medium" });
  slide.addText(it.text, { x: 5.0, y: y + 0.3, w: 4, h: 0.3, color: "000000", fontSize: 11 });
});
// CTA button bottom-right — primary style (see Buttons section)
```

### Stat Block — light variant (white background)

Same "over N / caption" pattern documented for social, but on white with black numerals and a
thin vertical grey rule separating it from body copy on the left:
```javascript
slide.addShape(pptx.ShapeType.rect, { x: 5.2, y: 0.9, w: 0.01, h: 4.3, fill: { color: "DFDED9" } });
const stats = [{ n: "8+", label: "YEARS MARITIME AI DEVELOPMENT" }, /* ... */];
stats.forEach((s, i) => {
  const y = 1.0 + i * 1.1;
  slide.addShape(pptx.ShapeType.rect, { x: 5.6, y: y, w: 0.3, h: 0.02, fill: { color: "CB0D00" } });
  slide.addText(s.n, { x: 5.6, y: y + 0.1, w: 3, h: 0.7, color: "000000", fontSize: 36, margin: [0, 0, 0, 0] });  // Regular weight, display size
  slide.addText(s.label, { x: 5.6, y: y + 0.75, w: 3, h: 0.3,
    color: "7B9194", fontSize: 9, fontFace: "Barlow Semi Condensed Medium", charSpacing: 1, margin: [0, 0, 0, 0] });
});
```

### Photo-Grid Application Cards (2–3 columns)

Photo, then a red ALL CAPS label with a short red underline, then a Medium-weight black caption line:
```javascript
const cards = [{ photo: "navy.jpg", label: "NAVY / NAVAL FORCES", caption: "Persistent AI lookout for every naval platform" }, /* ... */];
const colW = 9.0 / cards.length;
cards.forEach((c, i) => {
  const x = 0.5 + i * colW;
  slide.addImage({ path: c.photo, x, y: 1.2, w: colW - 0.15, h: 1.8 });
  slide.addText(c.label, { x, y: 3.1, w: colW - 0.15, h: 0.25,
    color: "CB0D00", fontSize: 9, fontFace: "Barlow Semi Condensed Medium", charSpacing: 1, margin: [0, 0, 0, 0] });
  slide.addShape(pptx.ShapeType.rect, { x, y: 3.4, w: 0.35, h: 0.02, fill: { color: "CB0D00" } });
  slide.addText(c.caption, { x, y: 3.5, w: colW - 0.15, h: 0.5, color: "000000", fontSize: 12, fontFace: "Barlow Semi Condensed Medium", margin: [0, 0, 0, 0] });
});
```

### Split Layout — Left white / Right Night Blue
```javascript
// Left half
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 5, h: 5.63,
  fill: { color: "FFFFFF" }, line: { color: "FFFFFF" } });
slide.addText("VISION", { x: 0.5, y: 0.3, w: 4, h: 0.25,
  color: "CB0D00", fontSize: 9, fontFace: "Barlow Semi Condensed Medium" });
slide.addText("Content on white side.", { x: 0.5, y: 1.0, w: 4, h: 3,
  color: "000000", fontSize: 16 });
// Right half
slide.addShape(pptx.ShapeType.rect, { x: 5, y: 0, w: 5, h: 5.63,
  fill: { color: "0B1731" }, line: { color: "0B1731" } });
slide.addText("MISSION", { x: 5.5, y: 0.3, w: 4, h: 0.25,
  color: "CB0D00", fontSize: 9, fontFace: "Barlow Semi Condensed Medium" });
slide.addText("Content on dark side.", { x: 5.5, y: 1.0, w: 4, h: 3,
  color: "FFFFFF", fontSize: 16 });
```

## Typography in pptxgenjs

| Element | fontSize | fontFace | color | charSpacing |
|---------|----------|------|-------|-------------|
| Section label | 9–10 | Barlow Semi Condensed Medium | CB0D00 | 1–2 |
| Page heading | 24–32 | Barlow Semi Condensed Medium | 000000 / FFFFFF | 0 |
| Subheading | 14–16 | Barlow Semi Condensed Medium | 000000 / FFFFFF | 0 |
| Body text | 10–11 | Barlow Semi Condensed | 000000 / FFFFFF | 0 |
| Footer | 8 | Barlow Semi Condensed | 7B9194 | 0 |

**Font:** pptxgenjs uses the system font by name. There is no Bold weight available, so never set
`bold: true` (it triggers OS-level faux-bold synthesis on an unhinted weight). Install
`Barlow Semi Condensed` (Regular) and `Barlow Semi Condensed Medium` as two separate font families
on the rendering system, and select emphasis via `fontFace: "Barlow Semi Condensed Medium"` instead
of the bold flag. Fallback: `"Arial Narrow"`.

## Table Styles

Two styles are used in decks — pick by content, same as documents/diagrams:

**⚠️ pptxgenjs border quirk (found via testing):** an empty `{}` for a border side does **not**
mean "no border" — it falls back to a visible default line. Always specify `{ type: "none" }`
explicitly for every side you don't want, or borders will show up where they shouldn't.

```javascript
// Brand Card table: Red header, Ocean Teal product rows (#06404C), Fog White relations
// Note: Brand Book calls this "Ocean Green" but it is a dark teal — NOT a green
const tableData = [
  [{ text: "Claims", options: { fill: "CB0D00", color: "FFFFFF", fontFace: "Barlow Semi Condensed Medium" }},
   { text: "Content...", options: { color: "000000" }}],
  [{ text: "Product", options: { fill: "06404C", color: "FFFFFF", fontFace: "Barlow Semi Condensed Medium" }},
   { text: "Content...", options: { color: "000000" }}],
  [{ text: "Relations", options: { fill: "DFDED9", color: "000000", fontFace: "Barlow Semi Condensed Medium" }},
   { text: "Content...", options: { color: "000000" }}],
];
slide.addTable(tableData, {
  x: 0.5, y: 1.2, w: 9.5,
  border: { type: "solid", pt: 0.5, color: "DFDED9" },
  fontFace: "Barlow Semi Condensed", fontSize: 10
});
```

**Comparison table (tested, matches the real flyer/catalogue pattern)** — no fill on the header
row, a thin red rule above and below it instead, one red "hero" column, thin Fog White row
dividers, no vertical borders anywhere:
```javascript
const none = { type: "none" };
const rows = [
  ["SEA.AI vs. conventional assistance systems", "AIS", "RADAR", "SEA.AI"],
  ["Detecting persons in water / floating objects", "–", "–", "check"],
  // ...
];
const tableRows = rows.map((r, ri) => r.map((cell, ci) => {
  const isHeader = ri === 0, isHero = ci === 3;
  const text = cell === "check" ? "✓" : cell;  // pptxgenjs/LibreOffice DOES render ✓ correctly
                                                 // (unlike Pillow — see diagrams.md)
  const color = isHero ? "CB0D00" : (cell === "–" ? "7B9194" : "000000");
  return { text, options: {
    align: ci === 0 ? "left" : "center",
    color, fontFace: isHeader ? "Barlow Semi Condensed Medium" : "Barlow Semi Condensed",
    fontSize: isHeader ? 11 : 10,
    valign: "middle", // tested: pptxgenjs table cells default to top-aligned, always set this explicitly
    border: isHeader
      ? [{ type: "solid", color: "CB0D00", pt: 1 }, none, { type: "solid", color: "CB0D00", pt: 1 }, none]
      : [none, none, { type: "solid", color: "DFDED9", pt: 0.5 }, none],
    fill: { color: "FFFFFF" },
  }};
}));
slide.addTable(tableRows, { x: 0.5, y: 1.3, w: 9, colW: [4.5, 1.5, 1.5, 1.5], rowH: 0.4 });
```

## Buttons

```javascript
// Primary — filled Focus Red, white ALL CAPS label
slide.addShape(pptx.ShapeType.roundRect, { x: 4.0, y: 4.5, w: 2.0, h: 0.5,
  fill: { color: "CB0D00" }, line: { type: "none" }, rectRadius: 0.08 });
slide.addText("LEARN MORE", { x: 4.0, y: 4.5, w: 2.0, h: 0.5,
  color: "FFFFFF", fontSize: 12, fontFace: "Barlow Semi Condensed Medium", align: "center", valign: "middle" });

// Secondary — Focus Red outline, Focus Red ALL CAPS label
slide.addShape(pptx.ShapeType.roundRect, { x: 4.0, y: 5.05, w: 2.0, h: 0.5,
  fill: { type: "none" }, line: { color: "CB0D00", width: 1.5 }, rectRadius: 0.08 });
slide.addText("LEARN MORE", { x: 4.0, y: 5.05, w: 2.0, h: 0.5,
  color: "CB0D00", fontSize: 12, fontFace: "Barlow Semi Condensed Medium", align: "center", valign: "middle" });
```

## Footer

```javascript
// Every content slide
slide.addText("Watchmaster Pre-Project", { x: 0.5, y: 5.35, w: 5, h: 0.2,
  color: "7B9194", fontSize: 8 });
slide.addText("SEA.AI CONFIDENTIAL", { x: 5.5, y: 5.35, w: 4, h: 0.2,
  color: "7B9194", fontSize: 8, align: "right" });
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 5.3, w: 9.5, h: 0.005,
  fill: { color: "DFDED9" } });
```

## Slide Count Rule

- Title + Section dividers: Night Blue
- All content slides: White
- No "grey slides" or mixed-theme content slides

## Header Row: Label and Logo Share One Center Line

A section label on the left and the logo on the right must be centered on the same horizontal
line, and the logo should stay modest next to 9pt label text (about 1.0in wide on a 10in slide).
Compute one shared center and derive both positions from it; use a tight, zero-margin label box
so different renderers (LibreOffice vs PowerPoint) have no slack to disagree on centering.
```javascript
const HEADER_CENTER = 0.2 + 0.25 / 2;         // one shared center line
const LOGO_W = 1.0, LOGO_H = 0.135;           // keeps the ~7.4:1 logo ratio
slide.addImage({ path: "assets/logo_black.png", x: 8.55, y: HEADER_CENTER - LOGO_H / 2, w: LOGO_W, h: LOGO_H });
slide.addText("SECTION LABEL", { x: 0.5, y: HEADER_CENTER - 0.07, w: 6, h: 0.14,
  color: "CB0D00", fontSize: 9, fontFace: "Barlow Semi Condensed Medium", charSpacing: 1,
  valign: "middle", margin: [0, 0, 0, 0] });
```

## Comparison Tables: Center the Indicator Columns

In tables with a long description column plus short indicator columns (check marks, dashes, product
names such as AIS / RADAR / SEA.AI), keep the description column left-aligned and center both the
header text and the symbols of every indicator column (`align: "center"` on those cells), so each
sign sits directly under its column header.

## Checklist

- [ ] Night Blue for title and section dividers only
- [ ] White for all content slides
- [ ] Logo is the real image asset (`addImage`), never drawn as text + shapes
- [ ] Logo top-right by default — white content slides AND solid Night Blue dividers alike
- [ ] Logo top-left ONLY on slides where a photo occupies the opposite panel (e.g. the cover
      slide layout) — this is a photo-legibility exception, not a Night-Blue-background rule
- [ ] Section label: ALL CAPS Focus Red top-left, or a short red kicker phrase — not both stacked
- [ ] Page number: bottom-right, black, small — not Focus Red (red page numbers only appeared on
      dark/title slides in the real deck)
- [ ] Headline emphasis via an inline Focus Red clause/keyword or a second red line — not bold
- [ ] Indicator columns (checks/dashes) centered under their headers; description column left
- [ ] Header label and logo centered on one shared line
- [ ] Table cells: `valign: "middle"` set explicitly — pptxgenjs defaults to top-aligned
- [ ] Any shape (rule, underline) meant to align with a text box's left edge: the text box has
      `margin: [0,0,0,0]` — otherwise the text box's default inset shifts it right of the shape
- [ ] Footer on every content slide
- [ ] No non-brand colors
- [ ] No gradients or shadows
- [ ] Font: Barlow Semi Condensed + Barlow Semi Condensed Medium installed as separate families (fallback Arial Narrow)
- [ ] No `bold: true` used anywhere — emphasis via `fontFace: "Barlow Semi Condensed Medium"`
- [ ] No em dashes in any slide copy
