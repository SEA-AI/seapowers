# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Viewer side of record-device-app. Prints one-line events: EVENT detail.

  rec.py URL OUT gates                             # clear gates, screenshot, exit
  rec.py URL OUT explore [TARGET ...]              # clear gates, list controls, click each TARGET in order, screenshot after each
  rec.py URL OUT record SECS [SECONDS=TARGET ...]  # clear gates, record SECS (>= 10), click TARGET at that second; writes OUT/take.mp4
  rec.py install                                   # once: Playwright's video recorder, matching this script's Playwright
SECONDS count from STREAMING; the mp4 starts earlier, with the page loading.
Timing settings (see knob() below) can be overridden per run with env vars REC_<NAME>.
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

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

USAGE = (__doc__ or "").split("Run with")[0].strip()
VIEW = {"width": 1920, "height": 1080}  # default size, also the cap for visible windows
VIDEO_FPS = 25  # Playwright's screen-recording frame rate
LOCALE = "en-US"  # gate texts in clear_gates are matched in English; pin the UI language


def knob(name, default):
    """Timing setting: a judgement call, overridable per run with env REC_<NAME> (e.g. REC_DECODE_WAIT_S=60)."""
    return type(default)(os.environ.get(f"REC_{name}", default))


PAGE_LOADS = knob("PAGE_LOADS", 6)  # page loads before giving up (NO_CONNECTION)
REG_RELOADS = knob("REG_RELOADS", 3)  # registration counts as persistent after this many sightings
GOTO_TIMEOUT_MS = knob("GOTO_TIMEOUT_MS", 30000)  # one page load
GATE_WAIT_S = knob("GATE_WAIT_S", 15)  # wait for a gate screen or playing video after a load
DECODE_WAIT_S = knob("DECODE_WAIT_S", 30)  # wait for WebRTC frames after the gates
CLICK_TIMEOUT_MS = knob("CLICK_TIMEOUT_MS", 5000)
STALL_WARN_S = knob("STALL_WARN_S", 30)  # no new frames this long: STALL (warning, keeps recording)
STALL_ABORT_S = knob("STALL_ABORT_S", 120)  # no new frames this long: FROZEN (take ends)
# Collect every RTCPeerConnection the app creates, so we can read real decode stats.
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
FRAMES = """async () => { let n = 0; for (const pc of window.__pcs || [])
  (await pc.getStats()).forEach(r => { if (r.type === 'inbound-rtp' && r.kind === 'video') n += r.framesDecoded || 0; });
  return n; }"""
# Visible clickable things with whatever names they have, plus their centre.
CONTROLS = """() => [...document.querySelectorAll('button,a,[role=button],[onclick],svg')]
  .map(e => e.closest('button,a,[role=button],[onclick]') || e).filter((e, i, a) => a.indexOf(e) === i)
  .map(e => { const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 40), aria: e.getAttribute('aria-label'),
      title: e.getAttribute('title'), cls: (e.className?.baseVal ?? e.className ?? '').toString().slice(0, 60),
      xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter(c => c.w > 8 && c.h > 8 && c.xy[0] < innerWidth && c.xy[1] < innerHeight)"""


def ev(name, detail=""):
    print(f"{name} {detail}".strip(), flush=True)


def bad_args(why):
    ev("BAD_ARGS", why)
    print(USAGE, file=sys.stderr)
    sys.exit(2)


# --- arguments: validate everything before opening a browser ---
if sys.argv[1:] == ["install"]:  # hand over to Playwright's installer in this script's own environment
    os.execv(sys.executable, [sys.executable, "-m", "playwright", "install", "ffmpeg"])
if len(sys.argv) < 4 or sys.argv[3] not in ("gates", "explore", "record"):
    bad_args("need URL OUT gates|explore|record, or install")
url, out, mode = sys.argv[1:4]
secs, actions = 0, []
if mode == "record":
    if len(sys.argv) < 5 or not sys.argv[4].isdigit() or int(sys.argv[4]) < 10:
        bad_args("record needs SECS (integer >= 10)")
    secs = int(sys.argv[4])
    for a in sys.argv[5:]:
        t, _, target = a.partition("=")
        if not t.isdigit() or not target or not 1 <= int(t) <= secs:
            bad_args(f"action {a!r} must be SECONDS=TARGET with 1 <= SECONDS <= {secs}")
        if target.startswith("xy=") and not re.fullmatch(r"xy=\d+,\d+", target):
            bad_args(f"action {a!r}: xy targets look like xy=X,Y (integers)")
        actions.append((int(t), target))
    if len({t for t, _ in actions}) < len(actions):
        bad_args("two actions at the same second")
actions = dict(actions)
override = None
if os.environ.get("VIEWPORT"):
    try:
        w, h = map(int, os.environ["VIEWPORT"].lower().split("x"))
    except ValueError:
        bad_args("VIEWPORT must look like 1920x1080")
    override = {"width": w // 2 * 2, "height": h // 2 * 2}


def frames(page):
    return page.evaluate(FRAMES)


def click(page, target):
    """Glide the drawn cursor to the target, show a ripple, then click."""
    if target.startswith("xy="):
        x, y = map(int, target[3:].split(","))
    else:
        box = page.locator(target).first.bounding_box(timeout=CLICK_TIMEOUT_MS)
        if not box:
            raise RuntimeError("target not visible")
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.evaluate("([x, y]) => window.__recMove && window.__recMove(x, y, 600)", [x, y])
    page.wait_for_timeout(650)
    page.evaluate("([x, y]) => { window.__recScripted = true; window.__recClick && window.__recClick(x, y); }", [x, y])
    try:
        page.mouse.click(x, y)  # returns after the page handled the events, so the flag covers them
    finally:
        page.evaluate("() => { window.__recScripted = false; }")


def wait_decoding(page, timeout_s=DECODE_WAIT_S):
    """True once WebRTC framesDecoded is increasing."""
    last = frames(page)
    for _ in range(timeout_s // 2):
        page.wait_for_timeout(2000)
        now = frames(page)
        if now > last > 0:
            return True
        last = now
    return False


def clear_gates(page, tag):
    """Clear the page gates. The texts below are the current UI strings (SKILL.md mirrors them).
    Returns an exit code: 0 streaming, 3 gate needs a human, 5 no connection."""
    agree = page.get_by_role("button", name="Agree & Continue").first
    failed = page.get_by_text(re.compile("Connection failed|connection was lost", re.IGNORECASE)).first
    register = page.get_by_text("Register to SEA.AI").first
    reg_seen = 0
    for attempt in range(PAGE_LOADS):
        try:
            page.goto(url, timeout=GOTO_TIMEOUT_MS)
        except PlaywrightError as e:  # refused or unreachable: same as a failed load
            ev("GATE connection_failed", f"{e.__class__.__name__}, reload {attempt + 1}/{PAGE_LOADS}")
            page.wait_for_timeout(5000)
            continue
        # wait for a gate screen, or stop early once video plays (not every product shows a gate)
        start_frames = frames(page)
        for _ in range(GATE_WAIT_S):
            if agree.or_(failed).or_(register).first.is_visible() or frames(page) > start_frames > 0:
                break
            page.wait_for_timeout(1000)
        if register.is_visible():
            # shows briefly while the worker starts; only a gate if it persists
            reg_seen += 1
            if reg_seen < REG_RELOADS:
                ev("GATE registration", f"transient? reload {reg_seen}/{REG_RELOADS}")
                page.wait_for_timeout(10000)
                continue
            page.screenshot(path=f"{out}/{tag}_gate.png")
            ev("GATE registration", f"persistent; {out}/{tag}_gate.png")
            return 3
        if failed.is_visible():
            ev("GATE connection_failed", f"reload {attempt + 1}/{PAGE_LOADS}")
            page.wait_for_timeout(5000)
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


def to_mp4(webm, length_s):
    """Transcode the raw webm (loading screen included) to OUT/take.mp4, reporting CONVERTING progress.
    No deadline: speed depends on the machine; the progress events show it is moving. The webm is
    deleted once the mp4 checks out."""
    if not shutil.which("ffmpeg"):
        ev("MP4_SKIPPED", "ffmpeg not found; webm is in DONE")
        return
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
        # keyframe every second (VIDEO_FPS frames) so players can seek precisely;
        # faststart puts the index first, the usual setting for shareable mp4s
        "-g",
        str(VIDEO_FPS),
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
    if not shutil.which("ffprobe"):
        ev("MP4", f"{mp4} (duration unknown: no ffprobe; webm kept)")
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


def open_browser(p, view, video):
    """Fresh throwaway profile per run. Visible: Chrome app mode (no tabs/address bar), pinned top-left."""
    profile = tempfile.mkdtemp(prefix="rec-profile-")
    kw = {
        "channel": "chrome",
        "headless": not headed,
        "chromium_sandbox": True,  # sandbox off shows a warning bar
        "args": ARGS + ([f"--app={url}"] if headed else []),
        "viewport": view,
        "locale": LOCALE,
    }
    if video:
        kw.update(record_video_dir=out, record_video_size=view)
    ctx = p.chromium.launch_persistent_context(profile, **kw)
    ctx.add_init_script(HOOK)
    ctx.add_init_script(CURSOR)
    # app mode may already show the URL without our scripts; clear_gates loads it again, which applies them
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return ctx, page, profile


def screen_fit(p):
    """Largest viewport (capped at VIEW) that fits the usable screen in an app-mode window."""
    profile = tempfile.mkdtemp(prefix="rec-probe-")
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
    shutil.rmtree(profile, ignore_errors=True)
    view = {
        "width": min(VIEW["width"], sw) // 2 * 2,
        "height": min(VIEW["height"], sh - bars) // 2 * 2,
    }  # even sizes for the encoder
    ev("VIEWPORT", f"{view['width']}x{view['height']} (screen {sw}x{sh}, window bar {bars})")
    return view


def record(p, view):
    ctx, page, profile = open_browser(p, view, video=True)
    video_t0 = time.monotonic()  # the video starts with the page
    every = max(10, secs // 30)  # PROGRESS + screenshot interval: about 30 per take, at least every 10 s
    width = max(3, len(str(secs)))  # t010.png … t3600.png sort correctly
    code = 0
    try:
        code = clear_gates(page, "rec")
        if code:
            return code
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
            if t % every and t != secs:
                continue
            page.screenshot(path=f"{out}/t{t:0{width}d}.png")
            now = frames(page)
            ev("PROGRESS", f"{t}/{secs}s decoded~{(now - last) / every:.0f}/s (approx., all streams)")
            # some views pause video: warn first, end the take only after a long stall
            flat_s = flat_s + every if now == last else 0
            last = now
            if flat_s >= STALL_ABORT_S:
                ev("FROZEN", f"at {t}s, no new WebRTC frames for {flat_s}s; take ended")
                code = 4
                break
            if flat_s >= STALL_WARN_S:
                ev("STALL", f"at {t}s, no new WebRTC frames for {flat_s}s; still recording, ask Device for status")
    except (PlaywrightError, OSError) as e:  # page or browser crash: still finalize the video and report it
        ev("ERROR", f"{e.__class__.__name__}: {str(e)[:200]}")
        code = code or 1
    finally:
        video = page.video.path()
        with contextlib.suppress(PlaywrightError):  # browser already gone: the webm may still be usable
            ctx.close()  # finalizes the webm
        shutil.rmtree(profile, ignore_errors=True)
        ev("DONE", video)
        if not code or code == 4:  # a frozen take is still worth keeping
            to_mp4(video, time.monotonic() - video_t0)
    return code


os.makedirs(out, exist_ok=True)
# HEADED=1 shows the browser so the user can watch (needs a local display); recording works either way.
# channel="chrome": installed Google Chrome, because Playwright's bundled Chromium lacks H.264 for the WebRTC stream.
headed = os.environ.get("HEADED") == "1"
ARGS = ["--autoplay-policy=no-user-gesture-required", "--window-position=0,0"]
code = 1
try:
    with sync_playwright() as p:
        if override:  # explicit VIEWPORT=WxH wins
            VIEW = override
            ev("VIEWPORT", f"{VIEW['width']}x{VIEW['height']} (from VIEWPORT)")
        elif headed:
            # fit the screen; xy targets then differ from headless
            VIEW = screen_fit(p)
        else:
            ev("VIEWPORT", f"{VIEW['width']}x{VIEW['height']} (headless default)")

        if mode == "record":
            code = record(p, VIEW)
        else:
            ctx, page, profile = open_browser(p, VIEW, video=False)
            try:
                code = clear_gates(page, mode)
                if mode == "explore" and not code:
                    for c in page.evaluate(CONTROLS):
                        ev("CONTROL", c)
                    for i, target in enumerate(sys.argv[4:], 1):
                        try:
                            click(page, target)
                        except (PlaywrightError, RuntimeError) as e:
                            ev("CLICK_FAIL", f"{target}: {e.__class__.__name__}")
                            continue
                        page.wait_for_timeout(3000)
                        shot = f"{out}/explore_{i:02d}.png"
                        page.screenshot(path=shot)
                        ev("CLICKED", f"{target} -> {shot} frames={frames(page)}")
            finally:
                with contextlib.suppress(PlaywrightError):  # browser already gone
                    ctx.close()
                shutil.rmtree(profile, ignore_errors=True)
except (PlaywrightError, OSError) as e:  # e.g. Chrome or the recorder missing: report it as an event
    ev("ERROR", f"{e.__class__.__name__}: {str(e)[:300]}")
    code = 1
sys.exit(code)
