# SEA.AI Presentations (PPTX)

For board decks, investor presentations, sales decks. Uses pptxgenjs via Node.js.

## Slide Types

### Title / Section Divider Slide — Night Blue background
```javascript
// Full Night Blue background, white text, logo top-right
slide.background = { color: "0B1731" };
slide.addText("S E A . A I", { x: 7.5, y: 0.15, w: 2.2, h: 0.3,
  color: "FFFFFF", fontSize: 12, bold: true, charSpacing: 4 });
slide.addText("SECTION NAME", { x: 0.5, y: 4.0, w: 9, h: 0.5,
  color: "7B9194", fontSize: 10, bold: true, charSpacing: 2 });
slide.addText("Heading Text", { x: 0.5, y: 4.6, w: 7, h: 1.0,
  color: "FFFFFF", fontSize: 32, bold: false });
```

### Content Slide — White background
```javascript
slide.background = { color: "FFFFFF" };
// Section label top-left: ALL CAPS Focus Red
slide.addText("THE SECTION LABEL", { x: 0.5, y: 0.2, w: 6, h: 0.25,
  color: "CB0D00", fontSize: 9, bold: true, charSpacing: 1 });
// Page number top-right: Focus Red
slide.addText("12", { x: 9.0, y: 0.2, w: 0.5, h: 0.25,
  color: "CB0D00", fontSize: 10, bold: true, align: "right" });
// Logo
slide.addImage({ path: "assets/Logo SEA.AI black RGB.jpg",
  x: 7.5, y: 0.12, w: 1.4, h: 0.22 });
// Red accent line below header
slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 0.52, w: 9.5, h: 0.01,
  fill: { color: "CB0D00" }, line: { color: "CB0D00" } });
// Main heading
slide.addText("Main Heading", { x: 0.5, y: 0.65, w: 9, h: 0.6,
  color: "000000", fontSize: 24, bold: true });
```

### Split Layout — Left white / Right Night Blue
```javascript
// Left half
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 5, h: 5.63,
  fill: { color: "FFFFFF" }, line: { color: "FFFFFF" } });
slide.addText("VISION", { x: 0.5, y: 0.3, w: 4, h: 0.25,
  color: "CB0D00", fontSize: 9, bold: true });
slide.addText("Content on white side.", { x: 0.5, y: 1.0, w: 4, h: 3,
  color: "000000", fontSize: 16 });
// Right half
slide.addShape(pptx.ShapeType.rect, { x: 5, y: 0, w: 5, h: 5.63,
  fill: { color: "0B1731" }, line: { color: "0B1731" } });
slide.addText("MISSION", { x: 5.5, y: 0.3, w: 4, h: 0.25,
  color: "CB0D00", fontSize: 9, bold: true });
slide.addText("Content on dark side.", { x: 5.5, y: 1.0, w: 4, h: 3,
  color: "FFFFFF", fontSize: 16 });
```

## Typography in pptxgenjs

| Element | fontSize | bold | color | charSpacing |
|---------|----------|------|-------|-------------|
| Section label | 9–10 | true | CB0D00 | 1–2 |
| Page heading | 24–32 | true | 000000 / FFFFFF | 0 |
| Subheading | 14–16 | true | 000000 / FFFFFF | 0 |
| Body text | 10–11 | false | 000000 / FFFFFF | 0 |
| Footer | 8 | false | 7B9194 | 0 |

**Font:** pptxgenjs uses the system font by name. Set `fontFace: "Barlow Semi Condensed"` (requires font installed on system); fallback: `"Arial Narrow"`.

## Table Styles

```javascript
// Brand Card table: Red header, Ocean Teal product rows (#06404C), Fog White relations
// Note: Brand Book calls this "Ocean Green" but it is a dark teal — NOT a green
const tableData = [
  [{ text: "Claims", options: { fill: "CB0D00", color: "FFFFFF", bold: true }},
   { text: "Content...", options: { color: "000000" }}],
  [{ text: "Product", options: { fill: "06404C", color: "FFFFFF", bold: true }},
   { text: "Content...", options: { color: "000000" }}],
  [{ text: "Relations", options: { fill: "DFDED9", color: "000000", bold: true }},
   { text: "Content...", options: { color: "000000" }}],
];
slide.addTable(tableData, {
  x: 0.5, y: 1.2, w: 9.5,
  border: { type: "solid", pt: 0.5, color: "DFDED9" },
  fontFace: "Barlow Semi Condensed", fontSize: 10
});
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

## Checklist

- [ ] Night Blue for title and section dividers only
- [ ] White for all content slides
- [ ] Logo top-right on every slide (black on white, white on dark)
- [ ] Section label: ALL CAPS Focus Red top-left
- [ ] Page number: Focus Red top-right
- [ ] Red accent line below header area
- [ ] Footer on every content slide
- [ ] No non-brand colors
- [ ] No gradients or shadows
- [ ] Font: Barlow Semi Condensed (install on system for pptxgenjs; fallback Arial Narrow)
