---
name: record-device-app
description: >
  Runs a SEA.AI product on a remote device from a recording (`make run` or `worker.py`), opens its
  web app in a browser (headless or visible) and screen-records the live stream to an mp4, with two
  partner subagents (Device, Viewer) that report after every step. Used when asked to record, capture,
  or film the app or stream running on a device or from a recording.
license: MIT
---

# Record Device App

You lead; two partners do the work, one step at a time. Each reports and stops; continue it with
`SendMessage`. When something breaks, you know which step broke it.

## Inputs (ask only for what's missing)

| Param | Meaning |
|---|---|
| `HOST` | `user@<device-ip>` |
| `URL` | default `http://<device-ip>/` |
| `DATA_DIR` | absolute recording folder on the device (no `~`) |
| `PRODUCT` | usually omit; preflight says when it's needed |
| `WORKER_DIR` | only if preflight can't find the worker; relative to the device home, or absolute |
| `SETTINGS_OVERRIDES` | optional device JSON file, `{"<group>": {"<setting>": value}}`, deep-merged over worker settings. Write it before preflight |
| `SECS` | take length; must fit in the clip (Flow 1) |
| `OUT` | a new dir in the scratchpad |
| `HEADED`, `VIEWPORT` | visible browser, `WxH` size (below) |

**Visible or headless?** Ask once per session, before step 1 (AskUserQuestion, headless first as the
default); reuse the answer. Visible means `HEADED=1` on every `rec.py` call (needs a local display).
Targets depend on window size, so explore and record with the same settings.

## Scripts

Next to this file; call them by absolute path. `uv run device.py` sends `device-remote.sh` to the device
over ssh (`~/.ssh/config` applies). `uv run rec.py` drives Chrome and injects `page.js`. Docstrings hold
syntax, env vars and exit codes.

Local prereqs: ssh key access (host in `known_hosts`), `uv`, Google Chrome (not Playwright's Chromium),
`ffmpeg` with libx264, `ffprobe`.

Timings default to a LAN. Override per run: `READY_TIMEOUT_S`, `KILL_GRACE_S`, `SSH_TIMEOUT_S`
(device.py), `REC_<NAME>` per `knob()` (rec.py). Partner commands die at 600 s: keep `READY_TIMEOUT_S` and
a whole `explore` (default ~360 s, plus ~9 s per target) under ~550 s.

**Device conventions.** Preflight checks tools and paths. When a step still fails, suspect these:
- `make run` if `~/Makefile` exists, else `python3 worker.py` in `~/Worker` or `~/Core-Backend/Worker`. A
  process with `worker.py` as an argument must start under that launcher (not docker or systemd). It runs
  in its own session (`setsid`) with env from `~/.bashrc`.
- Streaming: MediaMTX API at `localhost:9997`, one `*_webrtc` path per camera that flows with no viewer.
  The page plays them over WebRTC.
- One video file per camera (`.mp4`, `.avi`, `.mkv`); the clip lasts as long as the shortest (length from
  `gst-discoverer-1.0`, else `ffprobe`). At the end the worker logs `End-of-stream`.
- One run per device at a time.

## Roles

| Role | Agent type | Owns | May message |
|---|---|---|---|
| **Device** | `record-device` | ssh, `device.py` | whoever asked |
| **Viewer** | `record-viewer` | the browser, `rec.py`, screenshots | Device, for `status` only |
| **Lead** | you | params, decisions, every `start`, the user, user-approved one-off writes on the device (overrides file, registration bypass) | everyone |

Agent files: `../../agents/` (a plugin may prefix them, e.g. `seapowers:record-device`). Missing? Spawn
`general-purpose` agents with the file's text atop the prompt. Spawn each once per run with the step,
params, script path, and for the Viewer the Device's address. Clicks on modes or settings persist on the device: only with the user's OK, and restore them afterwards. Speak in intent ("show RGB, then thermal, then map"); the Viewer proposes the schedule.

## Events

One short line to the user per event. Unlisted events need nothing more.

| Event (exit) | You do |
|---|---|
| `READY` | next step |
| `WARN video is already streaming` | `READY` can't be trusted: ask the user before stopping that stream |
| `WARN registration bypass file missing` | tell the user a registration gate is likely |
| other `WARN`, `STALL`, `GATE registration` "transient?", `GATE connection_failed` | nothing beyond the line (`rec.py` reloads); mention `STALL` with the result |
| `PREFLIGHT_FAIL`, `CRASH` | stop, show the user why |
| `start`/`wait-ready` ends `ENDED` or `STOPPED` | died before `READY` (`ENDED`: clip shorter than startup); ask the user |
| `NOT_READY` | slow, not dead: `wait-ready` again (or raise `READY_TIMEOUT_S`) |
| `UNREACHABLE` | ssh failed, not a crash: retry (raise `SSH_TIMEOUT_S` on slow links) |
| persistent `GATE registration` (3) | show the screenshot, ask the user |
| `GATE unknown` (3), `FROZEN` (4), `NO_CONNECTION` (5) | the Viewer got the Device's `status`. `ENDED`: restart, shorter take · `CRASH`: show the log tail · `RUNNING`: app issue, show the screenshot, ask · `STOPPED`: `start`, retry · `NOT_READY`: `wait-ready` · `UNREACHABLE`: retry |
| `CLICK_FAIL`, `ACTION_FAIL` | show the last screenshot before it; re-find the target with `explore` |
| `ERROR` (1), `BAD_ARGS` (2) | fix the call and rerun. Setup missing (Chrome, ffmpeg, `rec.py install`): show the message and ask before installing anything |
| `MP4` | check one late frame, hand over the file |
| `MP4_FAIL` (1) | convert the webm by hand with `rec.py`'s `to_mp4` arguments |

## Flow

1. **Device: preflight.** Meanwhile run `uv run rec.py install` (instant if done). The clip starts at
   `start`, so `SECS` + startup + gates + margin must fit in `CLIP_SECONDS`; warn if not, ask if `unknown`.
2. **Takes that click: Device `start`, Viewer `explore`** to find targets. That burns clip, so step 3 restarts.
3. **Device: start.** Always requested by you, never the Viewer.
4. **Viewer: record SECS.** Runs in the background, clears gates, and exits before the take if one needs a human.
5. **Finish.** `OUT/take.mp4` includes the page load, so it outlasts SECS. Copy it where the user wants.
6. **Device: stop**, unless the user wants it running.
7. **Lessons.** One line on surprises. Suggest a skill change only for general ones (new gate type, navigation concept).

## Hands-on takes

In a visible run the user can drive the app mid-take. The video shows two cursors: script (red core),
user (blue core). Ask who does what.
- Fully hands-on: `record SECS`, no actions. Mixed: schedule only the script's part and tell the user
  which controls to leave alone.
- Start when the user is ready, and say when the window opens.
- "Stop" / "done": run `pkill -f '^[^ ]*python[^ ]* .*rec\.py .*<OUT>'` (only the recorder, not `uv` or a waiting shell). `rec.py` prints `TAKE_STOPPED` and keeps what it recorded.

## When the request isn't covered

New view, control, gate or product, or a wrong reference:
1. **Ask the user first.** Screenshot, one line on what's unclear, options ("explore the right column",
   "skip this view", "you tell me where it is"). They usually know faster.
2. Only if they say so: the Viewer explores the unknown UI. (Flow step 2, finding known targets, needs no OK.)
3. Findings go to `<OUT>/notes.md`. Nobody edits the skill's files: selectors drift, so the references
   stay general on purpose.

## Known gates and pitfalls

| Symptom | Fix |
|---|---|
| "Register to SEA.AI" persists | device unregistered. With the user's OK, run `ssh HOST 'touch ~/POWER_Const/system_successfully_registered'` yourself (persistent) |
| Gates never recognised | `rec.py` pins `en-US`; if the gate texts changed, ask the user |
| Tracebacks in a `CRASH` log tail | mostly harmless; the crash is that the worker is gone |
| `NOT_READY MediaMTX API unreachable`, no webrtc bytes | streaming breaks the conventions; ask the user how it's served |

Security: if device dotfiles or logs show tokens, flag them and advise rotation. Never copy them.
