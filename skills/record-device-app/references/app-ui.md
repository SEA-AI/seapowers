# SEA.AI web app: how to find your way around

General concepts shared by the SEA.AI products. Layout, labels and icons move as the app evolves:
read this as "what to look for", then confirm on a screenshot. Nothing here is a selector to trust blindly.

## Layout (typical)
- **Main view:** live camera video with detection labels, or a map. Often a heading/compass strip on top;
  marks on it are detected objects.
- **Status bar:** text about the alarm state and current view.
- **Side column, top:** operating **modes** (large labelled buttons). They change detection and alarms and persist on the device: only when asked.
- **Side column, below:** **view icons**, then panels, then **settings** (usually last).
- **Other edges:** alarm sound/mute, alarm or target list, camera selector, expand/collapse,
  markers pointing to targets outside the field of view.
- **Smaller windows:** the layout compacts (fewer modes shown, extra items behind a menu icon).
  Positions change with the browser size, so resolve targets at the size you record with.

## Icons (by meaning, not looks)
| Icon idea | Meaning |
|---|---|
| sun / day | colour (RGB) camera, usually the default view |
| moon / night | IR / thermal camera (greyscale) |
| map | top-down map with range rings around own vessel |
| two panes | split view; the second pane picks one of the views |
| gauge | instruments panel (heading, readouts; empty without sensor data) |
| wrench / gear | **settings**: only when the user asks |
| large labelled buttons | operating modes: only when the user asks |

The selected button looks different from the others. Icons may have no text or aria-label. Find them with
`explore` (the CONTROL list gives text, aria, class and position). Prefer text/aria selectors; otherwise
`xy=` resolved in the same run and same browser size. Class names are often generated per build:
treat a class-based selector as valid for this build only. Confirm every target by screenshot before a take.

## Navigating
- View switches apply at once. Some views may stop decoding video; that's not necessarily a fault
  (`rec.py` only reports FROZEN after 30 s flat).
- Panels (split, instruments) tend to stay open across view switches; clicking the same icon again closes them.
- Every run uses a fresh browser profile, so a reload returns to the default view. Easiest reset before a take.
- Anything that opens a dialog you didn't expect: close it, screenshot, report.

## When unsure
1. Screenshot first, then reason from the layout above (what region, what icon meaning).
2. Don't guess-click around. Ask the user with the screenshot and one concrete question.
3. If the user approves exploring: one `explore` run, a few candidate clicks, Read every screenshot.
4. Never touch modes, settings or anything that persists on the device without an explicit ask.
