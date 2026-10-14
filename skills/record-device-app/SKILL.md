---
name: record-device-app
description: >
  Runs a SEA.AI product on a remote device from a recording (`make run` or `worker.py`),
  opens its web app in a browser (headless or visible) and screen-records the live stream
  to an mp4, with two partner subagents (Device, Viewer) that report after every step so
  problems surface early. Used when asked to record, capture, or film the app or stream
  running on a device or from a recording.
license: MIT
---

# Record Device App

Two partner agents, one lead. Each agent does **one step**, reports, and stops; the lead continues it
with `SendMessage`. Every step ends with a report, so problems show up where they happen.

## Inputs (ask only if missing)

| Param | Meaning |
|---|---|
| `HOST` | `user@<device-ip>` |
| `URL` | the web app; `http://<device-ip>/` unless the user says otherwise |
| `DATA_DIR` | absolute path to the recording folder on the device (no `~`) |
| `PRODUCT` | **usually omit.** Only needed when `~/POWER_Const` has no `hardwareVersion`/`module_info`; preflight says so |
| `WORKER_DIR` | only if preflight can't find the worker; relative to the device home (write it without `~`), or absolute; ignored when `~/Makefile` exists |
| `SECS` | take length; must fit in the clip (Flow step 1) and in the Viewer's timeout (its agent file) |
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

**Device conventions** the scripts rely on (defined in `device.sh`; this list mirrors them. They may change,
so if a step fails, check these first):
- device: Linux with `bash`, `tmux`, `curl`, `python3`, `pgrep` (`ffprobe` optional); env from `~/.bashrc`
- worker: `~/Makefile`, or `worker.py` in `~/Worker` (usual) or `~/Core-Backend/Worker`; either way a process with `worker.py`
  in its command line must start; product inferred from `~/POWER_Const/hardwareVersion*`/`module_info*`
- registration bypass: `~/POWER_Const/system_successfully_registered`
- streaming: MediaMTX API on the device, WebRTC paths named `*_webrtc`
- end of clip: the worker logs `End-of-stream`
- one run per device at a time

Scripts live next to this file. Call them with absolute paths:
- `device.sh` (bash, on the local machine; talks to the device over ssh; on Windows use Git Bash)
- `rec.py`, run as `uv run rec.py ...` (dependencies are declared inline)

Prereqs on the local machine: ssh key access to the device, `uv`, Google Chrome (not Playwright's bundled
Chromium; see `rec.py`), `ffmpeg` with libx264 and `ffprobe`. Once, the lead runs `uv run rec.py install` (Playwright's
video recorder; if it's missing, `rec.py` reports an `ERROR`).

## Roles

| Role | Agent type | Owns | May message |
|---|---|---|---|
| **Device** | `record-device` | ssh; runs `device.sh` | replies to whoever asked |
| **Viewer** | `record-viewer` | the browser; runs `rec.py`, reads every screenshot | Device, for `status` only |
| **Lead** | you | params, decisions, every `start`; the only one who talks to the user | everyone |

The agents are defined in `../../agents/` (the plugin may prefix them, e.g. `seapowers:record-device`).
If they're missing, spawn `general-purpose` agents and start the prompt with the agent file's text.

Spawn each once per run. Each prompt: the step, the params, the script path, and for the Viewer the Device's
address. Post one short line to the user per event.

Device events: `PREFLIGHT_OK`, `PREFLIGHT_FAIL <why>`, `WARN <why>`, `RUN_CMD <cmd>`, `CLIP_SECONDS <n|unknown>`,
`STARTED`, `READY`, `RUNNING`, `ENDED`, `CRASH <log tail>`, `STOPPED`.

Viewer events: `VIEWPORT`, `GATE registration|connection_failed|terms|unknown`, `STREAMING <png>`,
`CONTROL`, `CLICKED`, `CLICK_FAIL` (explore), `ACTION`, `ACTION_FAIL`, `PROGRESS`, `FROZEN`, `NO_CONNECTION`,
`ERROR`, `DONE <webm>` (deleted once `MP4` checks out), `MP4 <path> <secs>` (without ffprobe: no secs, webm kept), `MP4_SKIPPED`, `MP4_FAIL`, `BAD_ARGS`.
`rec.py` exit codes are in its docstring.

| Event (exit code) | Lead does |
|---|---|
| `PREFLIGHT_FAIL`, `CRASH` | stop and show the user why |
| `WARN` | tell the user (a missing registration bypass means a registration gate is likely) |
| `READY` | next step |
| `GATE registration` "transient?", `GATE connection_failed` | nothing, `rec.py` reloads |
| persistent `GATE registration` (3) | show the screenshot, ask the user |
| `GATE unknown` (3) | Device `status` first (a dead worker or ended clip looks the same); if `RUNNING`, show the screenshot and ask the user |
| `FROZEN` (4), `NO_CONNECTION` (5) | the Viewer asks the Device for `status`; act on its answer: `ENDED` clip ran out (restart, shorter take) · `CRASH` show the log tail · `RUNNING` app issue, show the screenshot · `STOPPED` worker not running, `start` and retry |
| `ERROR` (1) | show the message (often Chrome or the video recorder missing, see Prereqs) and ask the user |
| `CLICK_FAIL`, `ACTION_FAIL` | show the screenshot; re-find the target with `explore` |
| `BAD_ARGS` (2) | fix the call and rerun |
| `MP4` | check one late frame, hand over the file |
| `MP4_SKIPPED`, `MP4_FAIL` | install ffmpeg if missing, then convert the webm by hand with the arguments in `rec.py`'s `to_mp4` |

## UI hints and actions

The lead speaks in intent ("show RGB, then thermal, then map"). The Viewer turns it into clicks.

- `references/app-ui.md` explains the app in general terms. The Viewer reads it, finds the actual targets
  with `explore`, and confirms each by screenshot.
- For a take, the Viewer proposes a schedule (`SECONDS=TARGET` args, seconds after `STREAMING`) before recording.

## Hands-on takes

In a visible run the user can also use the app during the take; everything the page shows is recorded.
The video then has two cursors: the script's (red core) and the user's (blue core), each with its own
click ripple. Headless runs only show the script's cursor.

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
3. Findings live in `<OUT>/notes.md` for this run only. Agents and the lead never edit the skill's files;
   the references hold general concepts on purpose, because specific selectors drift as the app evolves.

## Flow

1. **Device: preflight.** `CLIP_SECONDS` is an estimate (longest video file); if it's `unknown` or the
   recording is split into segments, ask the user. The clip starts playing at `start`, so the take has to
   finish before the clip does: clip length minus startup, gates, and a margin. Warn if it doesn't fit.
2. **Device: start.**
3. **Viewer: gates** (or `explore` for targets the references cover). Proves the live view works before a take
   uses up clip time.
4. **Device: start again**, requested by the lead right before step 5, never through the Viewer. Step 3 used
   up part of the clip, and a take on a stale clip ends in `FROZEN` and a lost-connection page.
5. **Viewer: record SECS.** The lead gets one report when the take ends; handle its events per the event table.
6. **Lead: finish.** `OUT/take.mp4` starts with the page loading, so it runs a bit longer than SECS. Copy it
   where the user wants it.
7. **Device: stop** unless the user wants it left running.
8. **Lead: lessons.** Summarise anything unexpected in one line. Suggest a skill change only for general
   lessons (a new gate type, a navigation concept), never a product-specific selector.

## Known gates and pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| "Register to SEA.AI" briefly after start | worker not answering yet | `rec.py` reloads; gate only if it persists |
| "Register to SEA.AI" persists | device not registered | ask the user; with their OK the lead runs `ssh HOST 'touch ~/POWER_Const/system_successfully_registered'` itself (persistent change) |
| Terms of Use page ("Agree & Continue") | fresh browser profile every run | `rec.py` clicks it |
| Gates never recognised | UI language or gate texts changed | `rec.py` pins `en-US`; if texts changed, ask the user |
| "Connection failed" / "…connection was lost" | worker not up yet, or the clip ended | wait for `READY`; `rec.py` reloads; mid-take, see the event table |
| Tracebacks or warnings in a CRASH log tail | many are caught and harmless | usually not the cause; a crash means the worker process is gone |
| Stream stops, worker hangs in shutdown | clip hit end-of-stream | Flow step 4; keep `SECS` under the clip |
| `CRASH MediaMTX API unreachable` / no webrtc bytes | streaming config differs from the conventions above | ask the user how the stream is served |

Security: if device dotfiles or logs show tokens, flag them to the user and advise rotation. Never copy them.
