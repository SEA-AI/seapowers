---
name: record-device-app
description: >
  Run a SEA.AI product on a remote device from a recording (`make run` or `worker.py`),
  open its web app in a browser (headless or visible) and screen-record the live stream
  to an mp4. Uses two partner subagents (Device, Viewer) that report after every step so
  problems surface early. Use when asked to record, capture, or film the app/stream
  running on a device or from a recording.
license: MIT
---

# Record Device App

Two partner agents, one lead. Each agent does **one short step**, reports, and stops.
The lead continues the same agent with `SendMessage` (context intact). Nobody runs
a long blind job: every step ends with an event the lead can act on or show the user.

## Inputs (ask only if missing)

| Param | Meaning |
|---|---|
| `HOST` | `user@<device-ip>`; the web app is served on the same IP |
| `DATA_DIR` | absolute path to the recording folder on the device |
| `PRODUCT` | **usually omit.** Only needed when `~/POWER_Const` has no `hardwareVersion`/`module_info`; preflight says so |
| `WORKER_DIR` | only if there is no `~/Makefile` and the worker isn't in `~/Core-Backend/Worker`; relative to the device home, or absolute |
| `SECS` | take length; must fit in the clip (see preflight) |
| `OUT` | a new dir in the scratchpad |
| `HEADED` | visible browser or headless (see below) |
| `VIEWPORT` | optional `WxH` override of the browser size |

**Ask once per session, before step 1:** "Watch the browser on screen, or run headless?"
(AskUserQuestion, two options, headless first as default). Reuse the answer for every later run in
this session; don't ask again unless the user brings it up. Visible → prefix every Viewer `rec.py`
call with `HEADED=1`.

Visible mode needs a local display (not over ssh / headless Linux).
Browser size: headless 1920x1080. Headed opens a Chrome app window (no tabs or address bar) that fills
the usable screen, capped at 1920x1080, pinned top-left. `VIEWPORT=WxH` overrides both. The `VIEWPORT` event reports the size;
the video is that size, and xy TARGETs only hold for it: explore and record with the same settings.

Run command (picked by `device.sh`): `~/Makefile` present → `make run`; otherwise
`cd ~ && cd $WORKER_DIR && python3 worker.py` (default `Core-Backend/Worker`). Same env vars either way.

**Device conventions** the scripts rely on (they may change; if a step fails, check these first):
- device: Linux with `bash`, `tmux`, `curl`, `python3` (`ffprobe` optional); env from `~/.bashrc`
- worker: `~/Makefile` or `~/Core-Backend/Worker/worker.py`; product inferred from `~/POWER_Const/hardwareVersion*`/`module_info*`
- registration bypass: `~/POWER_Const/system_successfully_registered`
- streaming: MediaMTX API at `localhost:9997/v3`, WebRTC paths named `*_webrtc`
- end of clip: the worker logs `End-of-stream`
- UI gate texts (English): "Register to SEA.AI", "Agree & Continue", "Connection failed" / "Your connection was lost"
- one run per device at a time (fixed tmux session `rda` and `/tmp` paths)

Scripts live next to this file. Call them with absolute paths:
- `device.sh` (bash, on the local machine; talks to the device over ssh)
- `rec.py`, run as `uv run rec.py ...` (dependencies are declared inline)

Prereqs on the local machine: ssh key access to the device, `uv`, Google Chrome (the bundled Chromium
lacks H.264 for the stream), `ffmpeg` with libx264 and `ffprobe`.
First run: `uv run --with playwright playwright install ffmpeg`.
Windows: `device.sh` runs in Git Bash, which Claude Code on Windows already requires.

## Roles

| Role | Agent type | Owns |
|---|---|---|
| **Device** | `record-device` (Bash only, Haiku) | ssh; runs `device.sh`: `preflight`, `start` (blocks until `READY`), `status`, `stop` |
| **Viewer** | `record-viewer` (Bash/Read/Write, Sonnet) | the browser; runs `rec.py`, reads every screenshot |
| **Lead** | you | params, decisions, the only one who talks to the user |

The agent definitions live in `../../agents/` relative to this file (in the seapowers plugin they are
`seapowers:record-device` / `seapowers:record-viewer`). If those types aren't available in the session,
spawn `general-purpose` agents with the matching agent file's body as the start of the prompt.

Spawn each once per run and continue it with `SendMessage`. Each prompt: the step, the params, the absolute
script path, and (for the Viewer) the Device's address so it can ask for `start`/`status` directly.
After each event, post one short line to the user (with the screenshot path when there is one).

Device events: `PREFLIGHT_OK`, `PREFLIGHT_FAIL <why>`, `WARN <why>`, `RUN_CMD <cmd>`, `CLIP_SECONDS <n|unknown>`,
`STARTED`, `READY`, `RUNNING`, `ENDED`, `CRASH <log tail>`, `STOPPED`.

Viewer events: `VIEWPORT`, `GATE registration|connection_failed|terms|unknown`, `STREAMING <png>`,
`CONTROL`, `CLICKED`, `CLICK_FAIL` (explore), `ACTION`, `ACTION_FAIL`, `PROGRESS`, `FROZEN`, `NO_CONNECTION`,
`ERROR`, `DONE <webm>`, `MP4 <path> <secs>`, `MP4_SKIPPED`, `MP4_FAIL`, `BAD_ARGS`.
`rec.py` exit codes: 0 ok, 1 unexpected error, 2 bad arguments, 3 gate needs a human, 4 stream frozen, 5 app never connected.

## UI hints and actions

The lead speaks in intent ("show RGB, then thermal, then map"). The Viewer turns it into clicks.

- Reference: `references/app-ui.md`, the general app concept (regions, icon meanings, where settings live,
  how to navigate, what to do when unsure). Viewer reads it first and resolves concrete TARGETs at runtime,
  confirming each by screenshot (`explore`) before a take.
- For a take, Viewer proposes a schedule as `SECONDS=TARGET` args and states it in its report before recording.
- Explore uses clip time; restart the worker before the take.

## When the request isn't covered

New view, control, gate or product the references don't cover, or a reference that turns out wrong:

1. **Stop and ask the user.** Show the screenshot, say what's unclear in one line, and offer options
   (e.g. "explore the right column", "skip this view", "you tell me where it is"). The user usually knows faster.
2. Only if the user says so: Viewer runs `rec.py ... explore [TARGET ...]` guided by `references/app-ui.md`,
   Reads every screenshot, and reports back before using anything it found.
   Never touch settings, modes or anything persistent unless the user asked.
3. Findings live in `<OUT>/notes.md` for this run only. Agents and the lead never edit the skill's files;
   the references hold general concepts on purpose, because specific selectors drift as the app evolves.

## Flow

1. **Device: preflight.** `PREFLIGHT_FAIL` → stop, tell the user. `CLIP_SECONDS` is an estimate (longest single
   video file); `unknown`, or a segmented/unusual recording → ask the user for the clip length.
   Budget: the clip starts playing at `start`, so `SECS ≤ CLIP_SECONDS − (STARTED→READY time from step 2
   + gate time + margin)`. Warn the user if their duration doesn't fit.
2. **Device: start.** `CRASH` → show the log tail to the user, stop.
3. **Viewer: gates** (or `explore` when targets need resolving). Proves the page reaches the live view
   before burning a take. `GATE unknown`/persistent `registration` → show the screenshot, fix (see table), back to 3.
4. **Device: start again** (fresh clip; step 3 used some of it). The lead does this itself, right before step 5;
   don't leave it to the Viewer. A take on a stale clip ends in `FROZEN` and a lost-connection page.
5. **Viewer: record SECS.** Lead relays `PROGRESS` sparsely (every ~30 s is enough).
   `FROZEN`/`NO_CONNECTION` → Device `status`: `ENDED` → SECS too long for the clip;
   `CRASH` → report; `RUNNING` → frontend issue, show screenshot.
6. **Lead: finish.** `rec.py` writes `OUT/take.mp4` (`MP4` event). It starts with the page loading, so it runs
   a bit longer than SECS. Look at one late frame, copy the mp4 where the user wants it, give the path.
   `MP4_SKIPPED`/`MP4_FAIL` → convert the webm by hand:
   `ffmpeg -v error -i <webm> -c:v libx264 -crf 23 -preset fast -pix_fmt yuv420p -g 25 -movflags +faststart <dest>.mp4`
   (`-g 25` = a keyframe every second at Playwright's 25 fps, for precise seeking).
7. **Device: stop** unless the user wants it left running.
8. **Lead: lessons.** Anything unexpected → one-line summary to the user. If it looks general (a new gate type,
   a navigation concept), suggest it to the user as a skill improvement; never a product-specific selector.

## Known gates and pitfalls

Something new? Ask the user (see above); note it in the run's `notes.md`.

| Symptom | Cause | Fix |
|---|---|---|
| "Register to SEA.AI" for a few seconds after start | worker not answering yet | `rec.py` reloads; gate only if it persists |
| "Register to SEA.AI" persists | device not registered | ask the user; with their OK, `touch ~/POWER_Const/system_successfully_registered` (persistent change) |
| "Terms of Use" page | fresh browser profile every run | `rec.py` clicks "Agree & Continue" |
| Gates never recognised | UI language or gate texts changed | `rec.py` pins `en-US`; if texts changed, ask the user |
| "Connection failed" / "Your connection was lost" | worker not up yet, or the clip ended | wait for `READY`; `rec.py` reloads; mid-take → Device `status` |
| Tracebacks or `sudo ... timed out` in a CRASH log tail | many are caught and harmless | not necessarily the cause; the worker process being gone is |
| Stream stops, worker hangs in shutdown | clip hit end-of-stream | restart before every take; keep `SECS` under the clip |
| `CRASH MediaMTX API unreachable` / no webrtc bytes | streaming config differs from the conventions above | ask the user how the stream is served |

Security: if device dotfiles or logs show tokens, flag them to the user and advise rotation. Never copy them.
