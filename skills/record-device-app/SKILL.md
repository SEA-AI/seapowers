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

Two partner agents, one lead. Each agent does **one short step**, reports, and stops; the lead continues
it with `SendMessage`. No step runs long without reporting, so problems show up where they happen.

## Inputs (ask only if missing)

| Param | Meaning |
|---|---|
| `HOST` | `user@<device-ip>`; the web app is served on the same IP |
| `DATA_DIR` | absolute path to the recording folder on the device |
| `PRODUCT` | **usually omit.** Only needed when `~/POWER_Const` has no `hardwareVersion`/`module_info`; preflight says so |
| `WORKER_DIR` | only if preflight can't find the worker; relative to the device home, or absolute |
| `SECS` | take length; must fit in the clip (see preflight) |
| `OUT` | a new dir in the scratchpad |
| `HEADED` | visible browser or headless (see below) |
| `VIEWPORT` | optional `WxH` override of the browser size |

**Ask once per session, before step 1:** "Watch the browser on screen, or run headless?"
(AskUserQuestion, two options, headless first as default). Reuse the answer for every later run in
this session; don't ask again unless the user brings it up. If visible, the Viewer prefixes every `rec.py`
call with `HEADED=1`.

- Headless: 1920x1080. Visible: a Chrome app window (no tabs or address bar) filling the screen, capped at
  1920x1080; needs a local display. `VIEWPORT=WxH` overrides either.
- Click targets depend on the size (`VIEWPORT` event): explore and record with the same settings.

Run command: `make run` if `~/Makefile` exists, otherwise `python3 worker.py` in the worker folder.
Preflight reports the choice as `RUN_CMD`.

**Device conventions** the scripts rely on (they may change; if a step fails, check these first):
- device: Linux with `bash`, `tmux`, `curl`, `python3` (`ffprobe` optional); env from `~/.bashrc`
- worker: `~/Makefile`, or `worker.py` in `~/Worker` (usual) or `~/Core-Backend/Worker`; product inferred from `~/POWER_Const/hardwareVersion*`/`module_info*`
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
Windows: `device.sh` runs in Git Bash, which Claude Code on Windows already requires.

## Roles

| Role | Agent type | Owns |
|---|---|---|
| **Device** | `record-device` (Bash only, Haiku) | ssh; runs `device.sh`: `preflight`, `start` (blocks until `READY`), `status`, `stop` |
| **Viewer** | `record-viewer` (Bash/Read/Write, Sonnet) | the browser; runs `rec.py`, reads every screenshot |
| **Lead** | you | params, decisions, the only one who talks to the user |

The agents are defined in `../../agents/` (in seapowers: `seapowers:record-device`, `seapowers:record-viewer`).
If they're missing, spawn `general-purpose` agents and start the prompt with the agent file's text.

Spawn each once per run. Each prompt: the step, the params, the script path, and for the Viewer the Device's
address, so it can ask for `start`/`status` itself. Post one short line to the user per event.

Device events: `PREFLIGHT_OK`, `PREFLIGHT_FAIL <why>`, `WARN <why>`, `RUN_CMD <cmd>`, `CLIP_SECONDS <n|unknown>`,
`STARTED`, `READY`, `RUNNING`, `ENDED`, `CRASH <log tail>`, `STOPPED`.

Viewer events: `VIEWPORT`, `GATE registration|connection_failed|terms|unknown`, `STREAMING <png>`,
`CONTROL`, `CLICKED`, `CLICK_FAIL` (explore), `ACTION`, `ACTION_FAIL`, `PROGRESS`, `FROZEN`, `NO_CONNECTION`,
`ERROR`, `DONE <webm>`, `MP4 <path> <secs>`, `MP4_SKIPPED`, `MP4_FAIL`, `BAD_ARGS`.
`rec.py` exit codes: 0 ok, 1 unexpected error, 2 bad arguments, 3 gate needs a human, 4 stream frozen, 5 app never connected.

| Event | Lead does |
|---|---|
| `PREFLIGHT_FAIL`, `CRASH` | stop and show the user why (log tail for a crash) |
| `READY` | go to the next step |
| `GATE unknown` / persistent `registration` | show the screenshot, ask the user |
| `FROZEN`, `NO_CONNECTION` | ask the Device for `status` |
| `MP4` | check one late frame, hand over the file |

## UI hints and actions

The lead speaks in intent ("show RGB, then thermal, then map"). The Viewer turns it into clicks.

- `references/app-ui.md` explains the app in general terms. The Viewer reads it, finds the actual targets
  with `explore`, and confirms each by screenshot.
- For a take, the Viewer proposes a schedule (`SECONDS=TARGET` args) before recording.
- Explore uses clip time; restart the worker before the take.

## Hands-on takes

In a visible run the user can also use the app during the take; everything the page shows is recorded.
The video then has two cursors: the script's (Focus Red core) and the user's (Night Blue core), each with
its own click ripple. Headless runs only show the script's cursor.

- Ask which parts the user will do and which the script does. Fully hands-on: `record SECS` with no actions.
- Mixed: schedule only the script's part, and tell the user where not to click (e.g. the controls the
  script uses) so the two don't fight. The Viewer still reports what each screenshot shows.
- Start the take only when the user is ready; say when the window will open.

## When the request isn't covered

New view, control, gate or product the references don't cover, or a reference that turns out wrong:

1. **Stop and ask the user.** Show the screenshot, say what's unclear in one line, and offer options
   (e.g. "explore the right column", "skip this view", "you tell me where it is"). The user usually knows faster.
2. Only if the user says so: Viewer runs `rec.py ... explore [TARGET ...]` guided by `references/app-ui.md`,
   Reads every screenshot, and reports back before using anything it found.
   Touch settings, modes or anything persistent only when the user asked for it.
3. Findings live in `<OUT>/notes.md` for this run only. Agents and the lead never edit the skill's files;
   the references hold general concepts on purpose, because specific selectors drift as the app evolves.

## Flow

1. **Device: preflight.** `CLIP_SECONDS` is an estimate (longest video file); if it's `unknown` or the
   recording is split into segments, ask the user. The clip starts playing at `start`, so the take has to
   finish before the clip does: clip length minus startup, gates, and a margin. Warn if it doesn't fit.
2. **Device: start.**
3. **Viewer: gates** (or `explore` when targets need finding). Proves the live view works before a take
   uses up clip time.
4. **Device: start again** (fresh clip; step 3 used some of it). The lead does this itself, right before step 5;
   don't leave it to the Viewer. A take on a stale clip ends in `FROZEN` and a lost-connection page.
5. **Viewer: record SECS.** Relay `PROGRESS` about every 30 s. If the stream freezes, Device `status` says why:
   `ENDED` (take too long for the clip), `CRASH`, or `RUNNING` (an app issue: show the screenshot).
6. **Lead: finish.** `OUT/take.mp4` starts with the page loading, so it runs a bit longer than SECS. Copy it
   where the user wants it. If `MP4_SKIPPED`/`MP4_FAIL`, convert the webm by hand:
   `ffmpeg -v error -i <webm> -c:v libx264 -crf 23 -preset fast -pix_fmt yuv420p -g 25 -movflags +faststart <dest>.mp4`
   (`-g 25` = a keyframe every second at Playwright's 25 fps, for precise seeking).
7. **Device: stop** unless the user wants it left running.
8. **Lead: lessons.** Summarise anything unexpected in one line. Suggest a skill change only for general
   lessons (a new gate type, a navigation concept), never a product-specific selector.

## Known gates and pitfalls

Something new? Ask the user (see above); note it in the run's `notes.md`.

| Symptom | Cause | Fix |
|---|---|---|
| "Register to SEA.AI" for a few seconds after start | worker not answering yet | `rec.py` reloads; gate only if it persists |
| "Register to SEA.AI" persists | device not registered | ask the user; with their OK, `touch ~/POWER_Const/system_successfully_registered` (persistent change) |
| "Terms of Use" page | fresh browser profile every run | `rec.py` clicks "Agree & Continue" |
| Gates never recognised | UI language or gate texts changed | `rec.py` pins `en-US`; if texts changed, ask the user |
| "Connection failed" / "Your connection was lost" | worker not up yet, or the clip ended | wait for `READY`; `rec.py` reloads; mid-take → Device `status` |
| Tracebacks or `sudo ... timed out` in a CRASH log tail | many are caught and harmless | usually not the cause; a crash means the worker process is gone |
| Stream stops, worker hangs in shutdown | clip hit end-of-stream | restart before every take; keep `SECS` under the clip |
| `CRASH MediaMTX API unreachable` / no webrtc bytes | streaming config differs from the conventions above | ask the user how the stream is served |

Security: if device dotfiles or logs show tokens, flag them to the user and advise rotation. Never copy them.
