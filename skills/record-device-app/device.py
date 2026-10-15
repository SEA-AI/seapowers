# /// script
# requires-python = ">=3.10"
# dependencies = ["asyncssh>=2.14"]
# ///
"""Device side of record-device-app: controls the worker on a remote device over ssh. Prints one-line events.

  HOST=user@ip DATA_DIR=<abs recording dir> [PRODUCT=<product>] [WORKER_DIR=<dir>] \\
    uv run device.py preflight|start|wait-ready|status|stop

PRODUCT is the exception: only needed when ~/POWER_Const has no hardwareVersion/module_info.
WORKER_DIR: relative to the device home, or absolute. The commands that run on the device live in device-remote.sh.
ssh settings (user, keys, agent, ProxyJump, known hosts) come from ~/.ssh/config as usual.
Exit codes: 0 ok, 1 not ready / crash / unreachable, 2 bad arguments.
"""

import asyncio
import io
import json
import os
import shlex
import sys
import time
from pathlib import Path
from typing import NoReturn

import asyncssh

if isinstance(sys.stdout, io.TextIOWrapper):  # Windows pipes default to cp1252; logs may not be ASCII
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REMOTE = (Path(__file__).parent / "device-remote.sh").read_text()
COMMANDS = ("preflight", "start", "wait-ready", "status", "stop")
SSH_ERRORS = (OSError, asyncssh.Error, asyncio.TimeoutError)


def ev(name: str, detail: str = "") -> None:
    print(f"{name} {detail}".strip(), flush=True)


def bad_args(why: str) -> NoReturn:
    ev("BAD_ARGS", why)
    sys.exit(2)


def setting(name: str, default: int) -> int:
    """Whole seconds, overridable per run via env."""
    v = os.environ.get(name, str(default))
    if not (v.isascii() and v.isdigit()) or int(v) < 1:
        bad_args(f"{name} must be a whole number >= 1, like {default}")
    return int(v)


READY_TIMEOUT_S = setting("READY_TIMEOUT_S", 270)  # wait for the worker to start and every camera's stream to flow
KILL_GRACE_S = setting("KILL_GRACE_S", 3)  # after asking the old worker to stop, before force-killing it
SSH_TIMEOUT_S = setting("SSH_TIMEOUT_S", 5)  # connect timeout and keepalive; raise over VPN or mobile links
cmd = sys.argv[1] if len(sys.argv) == 2 else ""
if cmd not in COMMANDS:
    bad_args("usage: device.py " + "|".join(COMMANDS))
HOST = os.environ.get("HOST") or bad_args("HOST is required")
DATA_DIR = os.environ.get("DATA_DIR", "")
if cmd in ("preflight", "start") and not DATA_DIR:
    bad_args("DATA_DIR is required")
PRODUCT = os.environ.get("PRODUCT", "")
WORKER_DIR = os.environ.get("WORKER_DIR", "").removeprefix("~/")  # "~/Worker" means "Worker" (device home)


def now() -> str:
    return time.strftime("%H:%M:%S%z")


async def connect() -> asyncssh.SSHClientConnection:
    user, _, host = HOST.rpartition("@")
    # keepalive: a link that drops mid-command fails within ~2x SSH_TIMEOUT_S instead of hanging
    return await asyncssh.connect(
        host,
        **({"username": user} if user else {}),
        connect_timeout=SSH_TIMEOUT_S,
        keepalive_interval=SSH_TIMEOUT_S,
        keepalive_count_max=2,
    )


async def sh(conn: asyncssh.SSHClientConnection, *args: str) -> tuple[int, str]:
    """Run one device-remote.sh command: the script goes over stdin, the args as $1..."""
    r = await conn.run("bash -s -- " + shlex.join(args), input=REMOTE, check=False, errors="replace")
    return 255 if r.exit_status is None else r.exit_status, str(r.stdout)  # exit None: killed by a signal


async def tail(conn: asyncssh.SSHClientConnection) -> str:
    _, log = await sh(conn, "logtail")
    return " ".join(log.split())  # one line, so the event stays one line


def samples(out: str) -> tuple[dict[str, int], dict[str, int]] | None:
    """The two *_webrtc byte counts from probe as {path: bytes} dicts, or None while the MediaMTX API doesn't answer.
    Bytes, not open ports or MediaMTX's "ready" flag: those can be stale from a previous run."""
    try:
        before, after = (
            {
                p["name"]: p.get("inboundBytes", p.get("bytesReceived", 0))
                for p in json.loads(s)["items"]
                if p["name"].endswith("_webrtc")
            }
            for s in out.split("\n---\n", 1)
        )
    except (ValueError, KeyError, TypeError):  # ValueError also covers a missing second sample
        return None
    return before, after


def flowing(before: dict[str, int], after: dict[str, int]) -> list[str]:
    """Camera paths whose bytes rose between the two samples."""
    return [k for k in before if after.get(k, 0) > before[k]]


async def report(conn: asyncssh.SSHClientConnection, state: str) -> int:
    """Print the event for a state from device-remote.sh's status; returns the exit code."""
    if state in ("RUNNING", "ENDED", "STOPPED"):
        ev(state)
        return 0
    if state == "LAUNCHING":  # a session without a worker that was never seen: still starting (building?)
        ev("NOT_READY", f"launcher running, no worker process yet: {await tail(conn)}")
    else:  # GONE: this run's worker exited while the launcher hangs on
        ev("CRASH", ("worker exited, launcher still running: " if state == "GONE" else "") + await tail(conn))
    return 1


async def wait_ready(conn: asyncssh.SSHClientConnection | None) -> int:
    # Keeps waiting while the worker is RUNNING or still LAUNCHING (building?): slow is not a crash. Any other
    # state (launcher or this run's worker gone) is final: STOPPED, ENDED or CRASH (the log has harmless tracebacks).
    end, state, s = time.monotonic() + READY_TIMEOUT_S, "UNREACHABLE", None
    while time.monotonic() < end:
        try:
            conn = conn or await connect()
            _, out = await sh(conn, "probe")
        except SSH_ERRORS:  # a hiccup isn't a crash: reconnect on the next round
            if conn:
                conn.close()
            conn, state = None, "UNREACHABLE"
            await asyncio.sleep(1)
            continue
        state, _, out = out.partition("\n")
        if state not in ("RUNNING", "LAUNCHING"):
            return await report(conn, state)
        s = samples(out)  # None while MediaMTX isn't up yet: keep waiting
        before, after = s or ({}, {})
        if before and before.keys() == after.keys() and len(flowing(before, after)) == len(before):
            ev("READY", f"{now()} all {len(before)} camera streams flowing")
            return 0
        await asyncio.sleep(1)
    why = {
        "UNREACHABLE": "device unreachable over ssh",
        "LAUNCHING": "no worker process yet, launcher still running (building?)",
    }.get(state) or ("MediaMTX API unreachable" if s is None else "not every camera streams")
    try:
        log = await tail(conn) if conn else ""
    except SSH_ERRORS:
        log = ""
    ev("NOT_READY", f"{why} after {READY_TIMEOUT_S}s. Run wait-ready again, or check: {log}")
    return 1


async def run(conn: asyncssh.SSHClientConnection) -> int:
    if cmd == "preflight":
        code, out = await sh(conn, "preflight", DATA_DIR, PRODUCT, WORKER_DIR)
        print(out, end="", flush=True)
        if code:
            return code
        _, out = await sh(conn, "probe")
        state, _, out = out.partition("\n")
        if (s := samples(out)) is None:
            ev("WARN", "MediaMTX API not reachable yet (fine if the worker starts it)")
        elif state in ("STOPPED", "ENDED", "CRASH") and flowing(
            *s
        ):  # streaming without our worker would make READY meaningless
            ev(
                "WARN",
                "video is already streaming without this skill's worker; stop it first or READY may be misleading",
            )
        ev("PREFLIGHT_OK")
        return 0
    if cmd == "start":
        code, _ = await sh(conn, "launch", DATA_DIR, PRODUCT, WORKER_DIR, str(KILL_GRACE_S))
        if code:
            ev("CRASH", "no ~/Makefile and no worker.py found" if code == 3 else "tmux could not start the worker")
            return 1
        ev("STARTED", now())
        return await wait_ready(conn)  # the old worker is gone, so flowing bytes mean the new one
    if cmd == "wait-ready":
        return await wait_ready(conn)
    if cmd == "status":
        _, state = await sh(conn, "status")
        return await report(conn, state.strip())
    await sh(conn, "stop", str(KILL_GRACE_S))
    ev("STOPPED")
    return 0


async def main() -> int:
    try:
        async with await connect() as conn:
            return await run(conn)
    except SSH_ERRORS as e:
        ev("UNREACHABLE", f"ssh to {HOST} failed: {e.__class__.__name__} {e}".strip())
    return 1


sys.exit(asyncio.run(main()))
