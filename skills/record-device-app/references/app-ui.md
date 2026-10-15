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
| wrench / gear | **settings** |
| large labelled buttons | operating modes |

- The selected button looks different from the others. Icons often have no text: find them with `explore`.
- Prefer text or aria selectors; otherwise `xy=`. Class names can change per build.

## Navigating
- View switches apply at once. Some views may stop decoding video; that's not necessarily a fault
  (`rec.py` warns with `STALL`, and reports FROZEN only after `STALL_ABORT_S` without new frames).
- Panels (split, instruments) tend to stay open across view switches; clicking the same icon again closes them.
- Every `rec.py` run uses a fresh browser profile, so each run starts at the default view.
- Anything that opens a dialog you didn't expect: close it, screenshot, report.
