---
name: sea-ai-brand
description: "SEA.AI brand identity (Brand Book 2026): colors, Barlow Semi Condensed typography, logo assets and rules, tables, heading hierarchy, and layout patterns. Use this skill for ANY output that carries the SEA.AI brand, even if the user doesn't say \"brand\": Word documents, PDFs, one-pagers, spec sheets, reports, PowerPoint decks (general and Defence segment), diagrams, charts, infographics, video titles and subtitles, social media posts and banners, email banners, web/HTML/JS/TS UI, press releases, or any marketing or technical material for SEA.AI. Also use it when converting, restyling or \"making official\" an existing document, deck or screenshot into SEA.AI style. Skip when working inside the Core-Frontend repo.\n"
license: MIT
---

# SEA.AI Brand Skill

Source of truth: **SEA.AI Brand Book 2026**, cross-checked against production flyers, the catalogue, and the general and Defence PowerPoint templates (June 2026).

## 🧭 Quick Router — Find Your Reference File

**What are you building?** Find your row, open the reference file, then read the full guide:

| Output type | Reference file | Technology |
|---|---|---|
| 📊 Diagram / chart / infographic | `references/diagrams.md` | Python / Pillow |
| 📄 PDF document | `references/documents.md` | WeasyPrint / ReportLab |
| 📄 Word document (.docx) | `references/documents.md` | python-docx |
| 📄 Excel spreadsheet (.xlsx) | `references/documents.md` | openpyxl |
| 🎤 Presentation (.pptx) | `references/presentations-pptx.md` | pptxgenjs |
| 🎖️ Defence-segment presentation | `references/presentations-pptx.md` + Defence Content section below | pptxgenjs |
| 💻 Web / frontend component | `references/frontend.md` | HTML / CSS / JS / TS |
| 🎬 Video (titles, lower-thirds, subtitles, outro) | `references/video.md` | Editing guidance |
| 📱 Social media (posts, stories, banners) | `references/social.md` | HTML / Pillow |

**⚠️ Before you start:** Read the relevant reference file + the "Core Brand" section below (colors, fonts, rules).

---

## Core Brand — The Non-Negotiables

### 7 Official Colors (Brand Book 2026, p.16)

```
Primary
  FOCUS RED    #CB0D00   RGB 203/13/0     CMYK 12/100/100/0   Pantone 186   ← primary accent
  BLACK        #000000   RGB 0/0/0        CMYK 100/0/0/0                    ← body text on light backgrounds
  WHITE        #FFFFFF   RGB 255/255/255  CMYK 0/0/0/0                      ← standard content background

Secondary
  NIGHT BLUE   #0B1731   RGB 11/23/45     CMYK 95/85/40/70    Pantone 289   ← dark backgrounds
  OCEAN GREEN  #06404C   RGB 6/64/76      CMYK 100/83/68/0    Pantone 548   ← product/secondary (visually a dark teal, NOT a green)
  SKY GREY     #7B9194   RGB 123/145/148  CMYK 59/37/37/0     Pantone 443  ← muted text, captions
  FOG WHITE    #DFDED9   RGB 223/222/217  CMYK 15/11/15/0     Pantone Cool Gray 1C ← warm backgrounds
```

**Any other color is off-brand. No exceptions.**
Banned colors from old templates: `#0099CC`, `#FDBE00`, `#A8C652`, `#F26B43`.

### Color Usage Rules

```
FOCUS RED (#CB0D00)
  ✅ Section labels (ALL CAPS), accent lines, CTA buttons, alert states, page numbers on dark
  ❌ Never as large background fill, never behind the logo

NIGHT BLUE (#0B1731)
  ✅ Title slide backgrounds, section dividers, dark panel halves, table header rows,
     solid color-blocking areas behind text/logo on social assets
  ❌ Not for body text backgrounds on content slides
  ❌ The only color permitted for color-blocking (never use another brand color to block an area)

OCEAN GREEN (#06404C)  — visually a dark teal
  ✅ Table header rows, secondary label backgrounds, brand card tables
  ❌ Not for primary headings or body text
  ❌ Never describe or use as "green" in output — it is a dark teal/navy tone

SKY GREY (#7B9194)
  ✅ Captions, footer text, muted secondary labels
  ❌ Not for main body text (too low contrast)

WHITE (#FFFFFF) — default content background
BLACK (#000000) — default body text
```

### Typography

**Font: Barlow Semi Condensed** (Google Fonts)
- Files: `assets/BarlowSemiCondensed-Medium.ttf`, `assets/BarlowSemiCondensed-Regular.ttf`, `assets/BarlowSemiCondensed-Light.ttf`
- Web: `https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@300;400;500&display=swap`
- Fallback for code/PPTX: `Arial Narrow`
- Fallback for system rendering: `DejaVu Sans Condensed`

```
Medium (500)  → Section labels, headings, table headers, emphasis (documents, diagrams, slides)
Regular (400) → Body text, captions, descriptions; video subtitles
Light (300)   → Video titles/intros and name-plates only, ALL CAPS
```

There is no Bold weight in the current asset set — use Medium for anything that previously
called for Bold. If a design genuinely needs a heavier weight than Medium provides, flag it
rather than fabricating a synthetic bold.

**Case rules:**
- Short headlines: ALL CAPS
- Normal headlines: Sentence case (not title case)
- Section labels: ALWAYS ALL CAPS FOCUS RED
- Body: normal sentence case
- Video titles/name-plates: ALL CAPS, Light weight

### Logo

- Files (all in `assets/`): ready-to-use transparent PNGs `logo_black.png` and `logo_nightblue.png` (light bg), `logo_red.png` (light bg, accent use), `logo_white.png` (dark bg). Originals for print/vector work: `Logo SEA.AI White RGB.svg`, `Logo SEA.AI black RGB.jpg`.
- All PNGs share one aspect ratio (about 7.4:1, width:height). Always set both width and height from that ratio (e.g. 1.5in wide x 0.2in tall) so the logo is never stretched.
- **Always use the actual logo image asset. Never draw the wordmark as text (even styled,
  letter-spaced "S E A . A I") and never approximate the cursor icon with drawn shapes.** This
  applies everywhere, including quick tests and drafts — a text-drawn stand-in reliably drifts
  from the real logo (kerning, icon shape, weight) and this has been the single most repeated
  mistake building this skill. If the real asset file isn't available in the working
  environment, crop a clean instance from any existing brand PDF/deck/photo rather than
  redrawing it from scratch.
- Letter-spaced: `S E A . A I` + cursor icon `[--]` (this describes the asset's appearance for
  identification purposes only, not a way to reconstruct it)
- **Default: top-right corner, on every slide/document/PDF type** — white content slides, solid
  Night Blue dividers, everything. This was corrected after checking a real internal deck: an
  earlier version of this rule said Night Blue slides use top-left, but a solid-color Night Blue
  divider slide (no photo) in production material uses top-right like everything else.
- **The only exception: slides or assets with a full-bleed or partial photo.** There, placement
  follows the visibility of the underlying image rather than a fixed corner — e.g. the standard
  cover-slide layout (Night Blue text panel + photo panel side by side) places the logo top-left
  because that's the panel without the photo. Choose whichever corner keeps the logo legible
  against the content; keep clear space around it (see below) either way.
- Never on Focus Red background, never distorted or recolored
- May be used in a single brand color when placed on a colored background — always check contrast
- Never use another brand's colors for the SEA.AI logo in co-branded material; keep each brand in
  its own space and colors

**Clear space & minimum size**
- Keep the cursor-icon's width as clear space around the whole lockup; keep at least half the
  cursor's width as clear space around the cursor icon itself
- Minimum height: 3mm (print) / 15px (screen)

**Watermarking on off-platform imagery** (SEA.AI photos/images used somewhere SEA.AI doesn't own):

| Platform | Logo height | Placement |
|---|---|---|
| Social media | min 40px | bottom right |
| Email newsletter | min 15px | bottom right |
| Website | min 15px | bottom right |
| Print (magazines, etc.) | no logo — photo credit instead: "© SEA.AI \| Photographer Name" | under photo |

### Design Principles

```
✅ White background for content (not dark unless section divider)
✅ Left-align body text and titles
✅ Generous white space — breathing room is brand
✅ Red line element to structure content — purposeful, NOT a hairline (give it visible weight)
✅ Emphasize part of a headline with an inline Focus Red clause or keyword (or a second line in
   red) rather than bolding — this is the standard emphasis device across decks, docs, and social
✅ Section labels: ALL CAPS, Focus Red, Barlow Semi Condensed Medium
✅ Footer on every page: document label + "SEA.AI CONFIDENTIAL" in Sky Grey
❌ No em dashes in any copy (headlines, body text, captions, video titles, social copy) — use a
   period, comma, or colon instead
❌ No gradients
❌ No drop shadows
❌ No decorative elements
❌ No centering body text
❌ No heavy/bold body text (Medium only for labels/headers)
```

### Detection Box (product-mark component)

The bounding box that marks a detected object in product screenshots/mockups:
- Night Blue or Focus Red rounded rectangle label pill, dashed corner-bracket variant below it
- Optional label inside: warning icon + distance (e.g. "320m")
- Use Focus Red for the highlighted/primary detection, Night Blue for secondary detections in the
  same scene — never more than one Focus Red box per scene
- **On very dark or low-light photography** (night, thermal, heavy overcast): drop the filled
  pill and use plain white dashed corner-brackets with no label — a solid red/navy pill reads as
  too heavy against dark imagery. Use this outline-only variant whenever the underlying photo is
  predominantly dark.
- Templates available on request from the design team; don't freehand new icon styles

### Buttons

- Primary: Focus Red fill, white ALL CAPS label — for strong-attention CTAs (newsletters, web, ads)
- Secondary: Focus Red outline, Focus Red ALL CAPS label, transparent/white fill

---

## Brand Messaging (quick ref)

- **Tagline:** "NOW YOU SEE."
- **Claim:** "Machine Vision for Safety & Security at Sea."
- **Vision:** "Help save lives at sea through artificial intelligence."
- **Mission:** "Develop and deploy AI systems that improve safety and security at sea."
- **Character:** Technology Pioneer | Vigilant & Reliable | Agile & Dynamic | Collaborative & Connected
  (Security/Commercial/Recreational segment messaging also includes "Sea Enthusiast" — check with
  Marketing before using segment-specific character/claims copy, since it varies by market segment)

### Name usage

- Spoken: pronounce in English, do not say "dot" — spell it out as "Sea dot AI" if needed
- Written: always "SEA.AI" — always the dot, always capital letters

### Writing style

- **No em dashes** in any SEA.AI content — documents, slides, diagrams, video, social, web copy.
  Rewrite with a period, comma, colon, or separate sentence instead.

---

## Defence Content

Defence-segment material (naval, coast guard, USV, border/perimeter security, government) uses a
**separate PPTX template** — `SEA_AI_Defence_Template_Presentation` — rather than the general
`SEA_AI_Template_Slides` deck. Same core brand system (colors, type, logo rules) applies; the
differences are in messaging framing and a couple of visual variants confirmed from the template.

### Messaging framing

Defence content follows the Defence market-segment brand framework (Brand Book 2026, p.9), not
the general claims used elsewhere:
- **Purpose:** Help Save Lives at Sea | Enable Safer Operations | Empower Smarter Decision-Making
  | Extend Human Awareness
- **Character:** Technology Pioneer | Vigilant & Reliable | Agile & Dynamic | Collaborative &
  Connected (no "Sea Enthusiast" trait — that's Security/Commercial/Recreational only)
- **Claims:** "NOW YOU SEE." | "Machine Vision for Safety & Security at Sea." | "Enhanced
  Situational Awareness."
- Positions against radar/AIS explicitly — this segment's material leans on the comparison table
  and "where radar and AIS stop" framing more than other segments do

### Confirmed patterns specific to this deck

- **Numbered capability cards** (01/02/03 on Night Blue) and **photo-grid application cards**
  (NAVY / PATROL VESSELS / USV etc., red ALL CAPS label + bold caption) appear repeatedly — see
  `references/presentations-pptx.md` for the exact patterns
- **Use-case slides**: photo left, white right with a red "USE CASE — [SEGMENT]" kicker, a
  headline with one word/clause in Focus Red, and a vertical-red-line bullet list going deep on
  one scenario (e.g. counter-USV, search & rescue)
- **Stat block, light variant**: same "big number + red dash + Sky Grey caption" pattern as
  elsewhere, but on white background with black numerals (not the dark full-bleed band used in
  social/print)
- **Detection-box overlays on this deck's imagery are frequently the low-light/outline variant**
  (see Detection Box section above) since defence photography skews toward night/thermal/overcast
  conditions

### A note on claims

Defence-segment copy leans more heavily on capability and readiness claims (detection ranges,
"NATO countries and allied partners," ISR/MDA terminology) than other segments. Per the
Restricted Topics policy, any regulatory, export-control, or compliance-sensitive claim in this
content needs the same legal review as elsewhere — the brand skill governs how it looks, not
whether a specific technical or compliance claim is accurate to make.

---

## Asset Paths

```
assets/BarlowSemiCondensed-Medium.ttf   ← headings, labels, table headers (docs/diagrams/slides)
assets/BarlowSemiCondensed-Regular.ttf  ← body text, captions, video subtitles
assets/BarlowSemiCondensed-Light.ttf    ← video titles/name-plates (ALL CAPS) only
assets/logo_black.png                   ← on white/light backgrounds (default)
assets/logo_nightblue.png               ← on light backgrounds, softer alternative
assets/logo_red.png                     ← on white/light backgrounds, accent use only
assets/logo_white.png                   ← on dark (Night Blue / photo) backgrounds
assets/Logo SEA.AI White RGB.svg        ← original vector (print, large format)
assets/Logo SEA.AI black RGB.jpg        ← original raster (2001px wide)
```

Paths are relative to the skill folder. Resolve to absolute when using in scripts.
