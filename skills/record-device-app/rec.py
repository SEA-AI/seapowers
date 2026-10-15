# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Viewer side of record-device-app. Prints one-line events: EVENT detail.

  rec.py URL OUT explore [TARGET ...]              # clear gates, list controls, click each TARGET in order, screenshot after each
  rec.py URL OUT record SECS [SECONDS=TARGET ...]  # clear gates, record SECS, click TARGET at that second; writes OUT/take.mp4
  rec.py install                                   # once: Playwright's video recorder, matching this script's Playwright
SECONDS count from STREAMING; the mp4 starts earlier, with the page loading.
Timing settings (see knob() below) can be overridden per run with env vars REC_<NAME> (e.g. REC_DECODE_WAIT_S=60).
Run with: [HEADED=1] [VIEWPORT=WxH] uv run rec.py ...
  HEADED=1: visible browser window. Viewport: VIEWPORT if set, else 1920x1080 (headed: fit to screen, capped at 1920x1080).
TARGET: a Playwright selector (text=..., [aria-label=...], css=... >> nth=N) or xy=X,Y (viewport pixels, see VIEWPORT event).
Exit codes: 0 ok, 1 unexpected error, 2 bad arguments, 3 gate needs a human (see screenshot), 4 stream frozen, 5 app never connected.
"""

import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from playwright.sync_api import BrowserContext, Page, Playwright, ViewportSize, sync_playwright
from playwright.sync_api import Error as PlaywrightError

VIEW: ViewportSize = {"width": 1920, "height": 1080}  # default size, also the cap for visible windows
GLIDE_MS = 600  # drawn cursor's glide to a click target, so viewers can follow it
SAMPLE_S = 2  # gap between two framesDecoded reads when checking that video decodes
# channel="chrome": installed Google Chrome, because Playwright's bundled Chromium lacks H.264 for the WebRTC stream.
ARGS = ["--autoplay-policy=no-user-gesture-required", "--window-position=0,0"]


def knob(name: str, default: int) -> int:
    try:
        v = int(os.environ.get(f"REC_{name}", default))
    except ValueError:
        v = 0
    if v < 1:
        print(f"BAD_ARGS REC_{name} must be a whole number >= 1, like {default}", flush=True)
        sys.exit(2)
    return v


PAGE_LOADS = knob("PAGE_LOADS", 6)  # page loads before giving up (NO_CONNECTION)
REG_RELOADS = knob("REG_RELOADS", 3)  # registration counts as persistent after this many sightings
GOTO_TIMEOUT_MS = knob("GOTO_TIMEOUT_MS", 30000)
GATE_WAIT_S = knob("GATE_WAIT_S", 15)  # wait for a gate screen or playing video after a load
DECODE_WAIT_S = knob("DECODE_WAIT_S", 30)  # wait for WebRTC frames after the gates
CLICK_TIMEOUT_MS = knob("CLICK_TIMEOUT_MS", 5000)
RELOAD_WAIT_S = knob("RELOAD_WAIT_S", 5)  # pause before reloading after a lost connection
REG_WAIT_S = knob("REG_WAIT_S", 10)  # pause before reloading while the registration screen shows
SETTLE_S = knob("SETTLE_S", 3)  # after an explore click, before the screenshot
STALL_WARN_S = knob("STALL_WARN_S", 30)  # no new frames this long: STALL (warning, keeps recording)
STALL_ABORT_S = knob("STALL_ABORT_S", 120)  # no new frames this long: FROZEN (take ends)
# Track every RTCPeerConnection the app creates, for its decode stats.
HOOK = """(() => { const O = window.RTCPeerConnection; window.__pcs = [];
  window.RTCPeerConnection = function (...a) { const pc = new O(...a); window.__pcs.push(pc); return pc; };
  window.RTCPeerConnection.prototype = O.prototype; })()"""
# Playwright videos show no OS cursor, so draw two: the script's (red core, moved by rec.py) and the user's
# (blue core, follows the mouse). rec.py marks its own clicks so they don't move the user cursor.
CURSOR = """(() => {
  const dot = (css) => { const d = document.createElement('div');
    Object.assign(d.style, { position: 'fixed', borderRadius: '50%', pointerEvents: 'none', zIndex: 2147483647 }, css);
    document.documentElement.appendChild(d); return d; };
  // SEA.AI brand colours. The core is a hard-edged radial fill, not a soft gradient; no shadows.
  const RED = '#CB0D00', BLUE = '#0B1731';
  const style = (core) => ({ width: '22px', height: '22px', margin: '-11px 0 0 -11px', boxSizing: 'border-box',
    border: '2px solid #fff', background: `radial-gradient(circle, ${core} 0 4px, rgba(11,23,49,.35) 4.5px)` });
  const ripple = (x, y, color) => { const r = dot({ left: x + 'px', top: y + 'px', width: '22px', height: '22px',
      margin: '-11px 0 0 -11px', boxSizing: 'border-box', border: `2px solid ${color}`,
      transition: 'transform .7s ease-out, opacity .7s ease-out' });
    r.getBoundingClientRect(); r.style.transform = 'scale(2.6)'; r.style.opacity = '0'; setTimeout(() => r.remove(), 800); };
  const keep = (get) => { let el = null; return () => el && el.isConnected ? el : (el = get()); };
  const script = keep(() => dot({ left: innerWidth / 2 + 'px', top: innerHeight / 2 + 'px', ...style(RED) }));
  const user = keep(() => dot({ ...style(BLUE) }));
  window.__recMove = (x, y, ms) => { const d = script(); d.getBoundingClientRect();
    d.style.transition = `left ${ms}ms ease-in-out, top ${ms}ms ease-in-out`; d.style.left = x + 'px'; d.style.top = y + 'px'; };
  window.__recClick = (x, y) => ripple(x, y, RED);
  addEventListener('mousemove', e => { if (window.__recScripted) return;
    const d = user(); d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', e => { if (!window.__recScripted) ripple(e.clientX, e.clientY, BLUE); }, true);
})()"""
FRAMES = """async () => { let n = 0; for (const pc of window.__pcs || []) try {
  (await pc.getStats()).forEach(r => { if (r.type === 'inbound-rtp' && r.kind === 'video') n += r.framesDecoded || 0; });
  } catch (e) {} return n; }"""  # per connection, so one closed connection can't hide the others
# Visible clickable things with whatever names they have, plus their centre.
CONTROLS = """() => [...document.querySelectorAll('button,a,[role=button],[onclick],svg')]
  .map(e => e.closest('button,a,[role=button],[onclick]') || e).filter((e, i, a) => a.indexOf(e) === i)
  .map(e => { const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40), aria: e.getAttribute('aria-label'),
      title: e.getAttribute('title'), cls: (e.className?.baseVal ?? e.className ?? '').toString().slice(0, 60),
      xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter(c => c.w > 8 && c.h > 8 && c.xy[0] < innerWidth && c.xy[1] < innerHeight)"""


def ev(name: str, detail: object = "") -> None:
    print(f"{name} {detail}".strip(), flush=True)


def bad_args(why: str) -> NoReturn:
    ev("BAD_ARGS", why)
    sys.exit(2)


@dataclass(frozen=True)
class Run:
    """One validated invocation."""

    url: str
    out: str
    mode: str  # explore | record
    secs: int  # record only
    actions: dict[int, str]  # record: second -> target
    targets: list[str]  # explore: targets in order
    headed: bool  # HEADED=1: visible window the user can watch (needs a local display); records either way
    viewport: ViewportSize | None  # VIEWPORT=WxH, wins over the default and the screen fit


def parse_args(argv: list[str]) -> Run:
    """Validate everything before opening a browser."""
    if len(argv) < 3 or argv[2] not in ("explore", "record"):
        bad_args("need URL OUT explore|record, or install")
    url, out, mode = argv[:3]
    secs, actions = 0, []
    if mode == "record":
        if len(argv) < 4 or not argv[3].isdigit() or int(argv[3]) < 1:
            bad_args("record needs SECS (a positive integer)")
        secs = int(argv[3])
        for a in argv[4:]:
            t, _, target = a.partition("=")
            if not t.isdigit() or not target or not 1 <= int(t) <= secs:
                bad_args(f"action {a!r} must be SECONDS=TARGET with 1 <= SECONDS <= {secs}")
            actions.append((int(t), target))
        if len({t for t, _ in actions}) < len(actions):
            bad_args("two actions at the same second")
        if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
            bad_args("record needs ffmpeg and ffprobe on PATH (for the mp4)")
    targets = [t for _, t in actions] if mode == "record" else argv[3:]
    for target in targets:
        if target.startswith("xy=") and not re.fullmatch(r"xy=\d+,\d+", target):
            bad_args(f"target {target!r}: xy targets look like xy=X,Y (integers)")
    viewport: ViewportSize | None = None
    if os.environ.get("VIEWPORT"):
        m = re.fullmatch(r"(\d+)x(\d+)", os.environ["VIEWPORT"].lower())
        if not m or min(map(int, m.groups())) < 100:
            bad_args("VIEWPORT must look like 1920x1080")
        viewport = {"width": int(m[1]) // 2 * 2, "height": int(m[2]) // 2 * 2}
    return Run(url, out, mode, secs, dict(actions), targets, os.environ.get("HEADED") == "1", viewport)


def frames(page: Page, default: int = 0) -> int:
    """Total WebRTC frames decoded, or default while the app navigates (the read fails mid-reload)."""
    try:
        return page.evaluate(FRAMES)
    except PlaywrightError:
        return default


def click(page: Page, target: str) -> None:
    """Glide the drawn cursor to the target, show a ripple, then click."""
    if target.startswith("xy="):
        x, y = map(int, target[3:].split(","))
    else:
        box = page.locator(target).first.bounding_box(timeout=CLICK_TIMEOUT_MS)
        if not box:
            raise RuntimeError("target not visible")
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.evaluate("([x, y, ms]) => window.__recMove && window.__recMove(x, y, ms)", [x, y, GLIDE_MS])
    page.wait_for_timeout(GLIDE_MS + 50)
    page.evaluate("([x, y]) => { window.__recScripted = true; window.__recClick && window.__recClick(x, y); }", [x, y])
    try:
        page.mouse.click(x, y)  # returns after the page handled the events, so the flag covers them
    finally:
        page.evaluate("() => { window.__recScripted = false; }")


def wait_decoding(page: Page, timeout_s: int = DECODE_WAIT_S) -> bool:
    """True once WebRTC framesDecoded is increasing."""
    last = frames(page)
    for _ in range(max(1, timeout_s // SAMPLE_S)):
        page.wait_for_timeout(SAMPLE_S * 1000)
        now = frames(page)
        if now > last > 0:
            return True
        last = now
    return False


def clear_gates(page: Page, run: Run) -> int:
    """Clear the page gates (matched by their current UI texts).
    Returns an exit code: 0 streaming, 3 gate needs a human, 5 no connection."""
    agree = page.get_by_role("button", name="Agree & Continue").first
    failed = page.get_by_text(re.compile("Connection failed|connection was lost", re.IGNORECASE)).first
    register = page.get_by_text("Register to SEA.AI").first
    url, out, tag = run.url, run.out, run.mode
    reg_seen = 0
    for attempt in range(PAGE_LOADS):
        try:
            page.goto(url, timeout=GOTO_TIMEOUT_MS)
        except PlaywrightError as e:  # refused or unreachable: same as a failed load
            ev("GATE connection_failed", f"{e.__class__.__name__}, reload {attempt + 1}/{PAGE_LOADS}")
            page.wait_for_timeout(RELOAD_WAIT_S * 1000)
            continue
        # wait for a gate screen, or stop early once video plays (not every product shows a gate)
        for _ in range(GATE_WAIT_S):
            if agree.or_(failed).or_(register).first.is_visible() or frames(page) > 0:
                break
            page.wait_for_timeout(1000)
        if register.is_visible():
            # shows briefly while the worker starts; only a gate if it persists
            reg_seen += 1
            if reg_seen < REG_RELOADS:
                ev("GATE registration", f"transient? reload {reg_seen}/{REG_RELOADS}")
                page.wait_for_timeout(REG_WAIT_S * 1000)
                continue
            page.screenshot(path=f"{out}/{tag}_gate.png")
            ev("GATE registration", f"persistent; {out}/{tag}_gate.png")
            return 3
        if failed.is_visible():
            ev("GATE connection_failed", f"reload {attempt + 1}/{PAGE_LOADS}")
            page.wait_for_timeout(RELOAD_WAIT_S * 1000)
            continue
        if agree.is_visible():
            agree.click()
            ev("GATE terms", "accepted")
        if not wait_decoding(page):
            page.screenshot(path=f"{out}/{tag}_gate.png")
            ev("GATE unknown", f"no WebRTC frames decoding; {out}/{tag}_gate.png")
            return 3
        page.screenshot(path=f"{out}/{tag}_ready.png")
        ev("STREAMING", f"{frames(page)} frames decoded; {out}/{tag}_ready.png")
        return 0
    ev("NO_CONNECTION", "app never connected; ask Device for status")
    return 5


def to_mp4(webm: Path, out: str, length_s: float) -> None:
    """Transcode the raw webm (loading screen included) to OUT/take.mp4, reporting CONVERTING progress.
    The webm is deleted once the mp4 checks out."""
    mp4 = f"{out}/take.mp4"
    args = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        webm,
        "-c:v",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "fast",
        "-pix_fmt",
        "yuv420p",
        # keyframe every second (Playwright records at 25 fps) for precise seeking;
        # faststart puts the index first, so playback starts before the download ends
        "-g",
        "25",
        "-movflags",
        "+faststart",
        "-progress",
        "pipe:1",
        "-nostats",
        mp4,
    ]
    with tempfile.TemporaryFile("w+") as err:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=err, text=True)
        shown = 0
        assert proc.stdout is not None  # stdout=PIPE above
        for line in proc.stdout:  # ffmpeg's progress lines: out_time_us=<microseconds encoded>
            if line.startswith("out_time_us=") and line[12:].strip().isdigit() and length_s > 0:
                pct = min(99, int(int(line[12:]) / 1e6 / length_s * 100))
                if pct >= shown + 10:
                    shown = pct - pct % 10
                    ev("CONVERTING", f"{shown}%")
        proc.wait()
        err.seek(0)
        error = err.read().strip()[-200:]
    if proc.returncode:
        if os.path.exists(mp4):
            os.remove(mp4)  # half-written: never hand it over
        ev("MP4_FAIL", error or f"ffmpeg exit {proc.returncode}")
        return
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not re.fullmatch(r"[0-9.]+", dur) or float(dur) <= 0:  # exit 0 doesn't prove a playable file
        os.remove(mp4)
        ev("MP4_FAIL", "mp4 has no readable duration; webm kept")
        return
    os.remove(webm)
    ev("MP4", f"{mp4} {dur}s")


def open_browser(p: Playwright, run: Run, view: ViewportSize, profile: str) -> tuple[BrowserContext, Page]:
    """Fresh throwaway profile per run. Visible: Chrome app mode (no tabs/address bar), pinned top-left."""
    video = run.mode == "record"
    ctx = p.chromium.launch_persistent_context(
        profile,
        channel="chrome",
        headless=not run.headed,
        chromium_sandbox=True,  # sandbox off shows a warning bar
        args=ARGS + ([f"--app={run.url}"] if run.headed else []),
        viewport=view,
        locale="en-US",  # gate texts in clear_gates are matched in English
        record_video_dir=run.out if video else None,
        record_video_size=view if video else None,
    )
    ctx.add_init_script(HOOK)
    ctx.add_init_script(CURSOR)
    # app mode may already show the URL without our scripts; clear_gates loads it again, which applies them
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page


def screen_fit(p: Playwright, profile: str) -> ViewportSize:
    """Largest viewport (capped at VIEW) that fits the usable screen in an app-mode window."""
    # about:blank ignores --app (opens a normal window), so probe with a tiny real page
    ctx = p.chromium.launch_persistent_context(
        profile,
        channel="chrome",
        headless=False,
        chromium_sandbox=True,
        args=ARGS + ["--app=data:text/html,<title>probe</title>"],
        no_viewport=True,
    )
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    sw, sh, bars = pg.evaluate("[screen.availWidth, screen.availHeight, outerHeight - innerHeight]")
    ctx.close()
    # even sizes for the encoder
    return {"width": min(VIEW["width"], sw) // 2 * 2, "height": min(VIEW["height"], sh - bars) // 2 * 2}


def take(page: Page, run: Run) -> int:
    """Record SECS after the gates; returns 0, or 4 when the stream froze."""
    secs, actions = run.secs, run.actions
    every = max(10, secs // 30)  # PROGRESS + screenshot interval: about 30 per take, at least every 10 s
    last, flat_s, t0 = frames(page), 0, time.monotonic()
    for t in range(1, secs + 1):
        # wait until second t of the take, so clicks and screenshots don't push the schedule later
        page.wait_for_timeout(max(0, (t0 + t - time.monotonic()) * 1000))
        if t in actions:
            try:
                click(page, actions[t])
                ev("ACTION", f"{t}s {actions[t]}")
            except (PlaywrightError, RuntimeError) as e:
                ev("ACTION_FAIL", f"{t}s {actions[t]}: {e.__class__.__name__}")
        # some views pause video: warn first, end the take only after a long stall
        now = frames(page, last)  # a failed read (app reloading) counts as no new frames
        flat_s = flat_s + 1 if now == last else 0
        last = now
        if flat_s >= STALL_ABORT_S:
            ev("FROZEN", f"at {t}s, no new WebRTC frames for {flat_s}s; take ended")
            return 4
        if flat_s == STALL_WARN_S:  # once per stall
            ev("STALL", f"at {t}s, no new WebRTC frames for {flat_s}s; still recording")
        if t % every == 0 or t == secs:
            page.screenshot(path=f"{run.out}/t{t:05d}.png")
            ev("PROGRESS", f"{t}/{secs}s frames={now}")
    return 0


def explore(page: Page, run: Run) -> int:
    for c in page.evaluate(CONTROLS):
        ev("CONTROL", c)
    for i, target in enumerate(run.targets, 1):
        try:
            click(page, target)
        except (PlaywrightError, RuntimeError) as e:
            ev("CLICK_FAIL", f"{target}: {e.__class__.__name__}")
            continue
        page.wait_for_timeout(SETTLE_S * 1000)
        shot = f"{run.out}/explore_{i:02d}.png"
        page.screenshot(path=shot)
        ev("CLICKED", f"{target} -> {shot} frames={frames(page)}")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["install"]:  # hand over to Playwright's installer in this script's own environment
        os.execv(sys.executable, [sys.executable, "-m", "playwright", "install", "ffmpeg"])
    run = parse_args(argv)
    os.makedirs(run.out, exist_ok=True)
    code = 1
    try:
        # one throwaway profile dir per run, removed after the browser has exited
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp, sync_playwright() as p:
            if run.viewport:
                view, how = run.viewport, "from VIEWPORT"
            elif run.headed:
                view, how = screen_fit(p, f"{tmp}/probe"), "screen fit"  # xy targets then differ from headless
            else:
                view, how = VIEW, "headless default"
            ev("VIEWPORT", f"{view['width']}x{view['height']} ({how})")
            ctx, page = open_browser(p, run, view, f"{tmp}/run")
            video_t0 = time.monotonic()  # the video starts with the page
            try:
                code = clear_gates(page, run)
                if not code:
                    code = 1  # stays 1 if the take raises: no mp4 from a crashed take
                    code = take(page, run) if run.mode == "record" else explore(page, run)
            finally:
                video = page.video.path() if page.video else None
                with contextlib.suppress(PlaywrightError):  # browser already gone: the webm may still be usable
                    ctx.close()  # finalizes the webm
                if video:
                    ev("DONE", video)
                    if code in (0, 4):  # a frozen take is still worth keeping
                        to_mp4(video, run.out, time.monotonic() - video_t0)
    except (PlaywrightError, OSError) as e:  # e.g. Chrome or the recorder missing: report it as an event
        ev("ERROR", f"{e.__class__.__name__}: {str(e)[:300]}")
        return 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
