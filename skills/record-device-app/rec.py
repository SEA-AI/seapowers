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
Run with: [HEADED=1] [VIEWPORT=WxH] uv run rec.py ...
  HEADED=1: visible browser window. Viewport: VIEWPORT if set, else 1920x1080 (headed: fit to screen, capped at 1920x1080).
TARGET: a Playwright selector (text=..., [aria-label=...], css=... >> nth=N) or xy=X,Y (viewport pixels, see VIEWPORT event).
Exit codes: 0 ok, 1 unexpected error, 2 bad arguments, 3 gate needs a human (see screenshot), 4 stream frozen, 5 app never connected.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

USAGE = (__doc__ or "").split("Run with")[0].strip()
VIEW = {"width": 1920, "height": 1080}  # default size, also the cap for visible windows
VIDEO_FPS = 25  # Playwright's screen-recording frame rate
LOCALE = "en-US"  # gate texts in clear_gates are matched in English; pin the UI language
# Timing knobs: judgement calls, raise them for slow devices.
PAGE_LOADS = 6        # page loads before giving up (NO_CONNECTION)
REG_RELOADS = 3       # registration screen counts as persistent after this many sightings
DECODE_WAIT_S = 30    # wait for WebRTC frames after the page loads
CLICK_TIMEOUT_MS = 5000
PROGRESS_EVERY_S = 10  # PROGRESS event and screenshot interval
FROZEN_AFTER = 3       # flat PROGRESS intervals in a row before FROZEN
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
    failed = page.get_by_text(re.compile("Connection failed|connection was lost", re.I)).first
    register = page.get_by_text("Register to SEA.AI").first
    reg_seen = 0
    for attempt in range(PAGE_LOADS):
        try:
            page.goto(url)
        except Exception as e:  # refused or unreachable: same as a failed load
            ev("GATE connection_failed", f"{e.__class__.__name__}, reload {attempt + 1}/{PAGE_LOADS}")
            page.wait_for_timeout(5000)
            continue
        try:
            agree.or_(failed).or_(register).first.wait_for(timeout=15000)
        except Exception:
            pass
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


def to_mp4(webm):
    """Transcode the raw webm (loading screen included) to OUT/take.mp4; the webm is deleted once the mp4 checks out."""
    if not shutil.which("ffmpeg"):
        ev("MP4_SKIPPED", "ffmpeg not found; webm is in DONE")
        return
    mp4 = f"{out}/take.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", webm, "-c:v", "libx264",
                        "-crf", "23", "-preset", "fast", "-pix_fmt", "yuv420p",
                        # keyframe every second (VIDEO_FPS frames) so players can seek precisely;
                        # faststart puts the index first, the usual setting for shareable mp4s
                        "-g", str(VIDEO_FPS), "-movflags", "+faststart", mp4],
                       capture_output=True, text=True)
    if r.returncode:
        ev("MP4_FAIL", r.stderr.strip()[-200:])
        return
    if not shutil.which("ffprobe"):
        ev("MP4", f"{mp4} (duration unknown: no ffprobe; webm kept)")
        return
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                         capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r"[0-9.]+", dur) or float(dur) <= 0:  # exit 0 doesn't prove a playable file
        ev("MP4_FAIL", f"{mp4} has no readable duration; webm kept")
        return
    os.remove(webm)
    ev("MP4", f"{mp4} {dur}s")


def open_browser(p, view, video):
    """Fresh throwaway profile per run. Visible: Chrome app mode (no tabs/address bar), pinned top-left."""
    profile = tempfile.mkdtemp(prefix="rec-profile-")
    kw = dict(channel="chrome", headless=not headed, chromium_sandbox=True,  # sandbox off shows a warning bar
              args=ARGS + ([f"--app={url}"] if headed else []),
              viewport=view, locale=LOCALE)
    if video:
        kw.update(record_video_dir=out, record_video_size=view)
    ctx = p.chromium.launch_persistent_context(profile, **kw)
    ctx.add_init_script(HOOK)
    ctx.add_init_script(CURSOR)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if page.url not in ("about:blank", ""):  # app mode opens the page before our scripts exist: reload once
        page.reload()
    return ctx, page, profile


def screen_fit(p):
    """Largest viewport (capped at VIEW) that fits the usable screen in an app-mode window."""
    profile = tempfile.mkdtemp(prefix="rec-probe-")
    # about:blank ignores --app (opens a normal window), so probe with a tiny real page
    ctx = p.chromium.launch_persistent_context(profile, channel="chrome", headless=False, chromium_sandbox=True,
                                               args=ARGS + ["--app=data:text/html,<title>probe</title>"], no_viewport=True)
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    sw, sh, bars = pg.evaluate("[screen.availWidth, screen.availHeight, outerHeight - innerHeight]")
    ctx.close()
    shutil.rmtree(profile, ignore_errors=True)
    view = {"width": min(VIEW["width"], sw) // 2 * 2, "height": min(VIEW["height"], sh - bars) // 2 * 2}  # even sizes for the encoder
    ev("VIEWPORT", f"{view['width']}x{view['height']} (screen {sw}x{sh}, window bar {bars})")
    return view


def record(p, view):
    ctx, page, profile = open_browser(p, view, video=True)
    code = 0
    try:
        code = clear_gates(page, "rec")
        if code:
            return code
        last, flat = frames(page), 0
        for t in range(1, secs + 1):
            page.wait_for_timeout(1000)
            if t in actions:
                try:
                    click(page, actions[t])
                    ev("ACTION", f"{t}s {actions[t]}")
                except Exception as e:
                    ev("ACTION_FAIL", f"{t}s {actions[t]}: {e.__class__.__name__}")
            if t % PROGRESS_EVERY_S:
                continue
            page.screenshot(path=f"{out}/t{t:03d}.png")
            now = frames(page)
            ev("PROGRESS", f"{t}/{secs}s decoded~{(now - last) / PROGRESS_EVERY_S:.0f}/s (approx., all streams)")
            # some views may pause video, so only give up after several flat intervals
            flat = flat + 1 if now == last else 0
            last = now
            if flat >= FROZEN_AFTER:
                ev("FROZEN", f"at {t}s, no new WebRTC frames for {flat * PROGRESS_EVERY_S}s; ask Device for status")
                code = 4
                break
    except Exception as e:  # page crash etc.: still finalize the video
        ev("ERROR", f"{e.__class__.__name__}: {str(e)[:200]}")
        code = code or 1
    finally:
        video = page.video.path()
        ctx.close()  # finalizes the webm
        shutil.rmtree(profile, ignore_errors=True)
        ev("DONE", video)
        if not code or code == 4:  # a frozen take is still worth keeping
            to_mp4(video)
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
            code = clear_gates(page, mode)
            if mode == "explore" and not code:
                for c in page.evaluate(CONTROLS):
                    ev("CONTROL", c)
                for i, target in enumerate(sys.argv[4:], 1):
                    try:
                        click(page, target)
                    except Exception as e:
                        ev("CLICK_FAIL", f"{target}: {e.__class__.__name__}")
                        continue
                    page.wait_for_timeout(3000)
                    shot = f"{out}/explore_{i:02d}.png"
                    page.screenshot(path=shot)
                    ev("CLICKED", f"{target} -> {shot} frames={frames(page)}")
            ctx.close()
            shutil.rmtree(profile, ignore_errors=True)
except Exception as e:  # e.g. Chrome or Playwright's recorder missing: report it as an event
    ev("ERROR", f"{e.__class__.__name__}: {str(e)[:300]}")
    code = 1
sys.exit(code)
