# SEA.AI web app: finding your way around

Layout and icons move between builds. This says what to look for; a screenshot confirms it.

## Layout (typical)
- **Main view:** camera video with detection labels, or a map. A compass strip on top marks detections.
- **Status bar:** alarm state and current view.
- **Side column, top:** operating **modes** (large labelled buttons). They change detection and alarms
  and persist on the device: touch only when asked.
- **Side column, below:** view icons, then panels, then **settings** (usually last).
- **Other edges:** alarm mute, target list, camera selector, expand/collapse, off-screen target markers.
- **Small windows** compact the layout (fewer modes, a menu icon). Resolve targets at the recording size.

## Icons (by meaning)
| Icon | Meaning |
|---|---|
| sun | colour (RGB) camera, usually the default |
| moon | IR / thermal (greyscale) |
| map | top-down map, range rings around own vessel |
| two panes | split view; the second pane shows another view |
| gauge | instruments (empty without sensor data) |
| wrench / gear | settings |

- The selected button looks different. Icons often lack text: find them with `explore`.
- Prefer text or aria selectors, else `xy=`. Class names change per build.

## Navigating
- View switches apply at once. Some views stop decoding video; not necessarily a fault. `rec.py` warns
  with `STALL` and calls it `FROZEN` only after `STALL_ABORT_S`.
- Panels (split, instruments) stay open across view switches; click the icon again to close.
- Each `rec.py` run gets a fresh profile, so it starts at the default view.
- Unexpected dialog: close it, screenshot, report.
