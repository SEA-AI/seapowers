# /// script
# requires-python = ">=3.11"
# dependencies = ["asyncssh>=2.14"]
# ///
"""Device side of record-device-app: controls the worker on a remote device over ssh. Prints one-line events.

  HOST=user@ip DATA_DIR=<abs recording dir> [PRODUCT=<product>] [WORKER_DIR=<dir>] \\
    uv run device.py preflight|start|wait-ready|status|stop

PRODUCT is the exception: only needed when ~/POWER_Const has no hardwareVersion/module_info.
WORKER_DIR: relative to the device home, or absolute. The commands that run on the device live in device-remote.sh.
ssh settings (user, keys, agent, ProxyJump, known hosts) come from ~/.ssh/config as usual.
Settings (whole seconds, env): READY_TIMEOUT_S, KILL_GRACE_S, SSH_TIMEOUT_S; defaults in parse_args().
Exit codes: 0 ok, 1 not ready / crash / unreachable, 2 bad arguments.
"""

import asyncio
import io
import json
import os
import shlex
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import NoReturn

import asyncssh

if isinstance(sys.stdout, io.TextIOWrapper):  # Windows pipes default to cp1252; logs may not be ASCII
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REMOTE = (Path(__file__).parent / "device-remote.sh").read_text()
MARK = "== record-device-app ==\n"  # device-remote.sh prints it first; anything before is login-shell noise
SSH_ERRORS = (OSError, asyncssh.Error)


class Command(StrEnum):
    PREFLIGHT = "preflight"
    START = "start"
    WAIT_READY = "wait-ready"
    STATUS = "status"
    STOP = "stop"


class Remote(StrEnum):
    """The functions device-remote.sh dispatches to."""

    PREFLIGHT = "preflight"
    LAUNCH = "launch"
    PROBE = "probe"
    STATUS = "status"
    STOP = "stop"
    LOGTAIL = "logtail"
    CAMERAS = "cameras"


class State(StrEnum):
    """What device-remote.sh's status prints."""

    RUNNING = "RUNNING"
    LAUNCHING = "LAUNCHING"  # a session without a worker that was never seen: still starting (building?)
    GONE = "GONE"  # this run's worker exited while the launcher hangs on
    ENDED = "ENDED"
    STOPPED = "STOPPED"
    CRASH = "CRASH"


@dataclass(frozen=True)
class Config:
    """One validated invocation."""

    command: Command
    host: str
    data_dir: str
    product: str
    worker_dir: str
    ready_timeout_s: int  # wait for the worker to start and every camera's stream to flow
    kill_grace_s: int  # after asking the old worker to stop, before force-killing it
    ssh_timeout_s: int  # connect timeout and keepalive; raise over VPN or mobile links


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


def parse_args(argv: list[str]) -> Config:
    try:
        (command,) = map(Command, argv)
    except ValueError:
        bad_args("usage: device.py " + "|".join(Command))
    data_dir = os.environ.get("DATA_DIR", "")
    if command in (Command.PREFLIGHT, Command.START) and not data_dir.startswith("/"):
        bad_args("DATA_DIR must be an absolute path on the device")
    return Config(
        command=command,
        host=os.environ.get("HOST") or bad_args("HOST is required"),
        data_dir=data_dir,
        product=os.environ.get("PRODUCT", ""),
        worker_dir=os.environ.get("WORKER_DIR", "").removeprefix("~/"),  # "~/Worker" means "Worker" (device home)
        ready_timeout_s=setting("READY_TIMEOUT_S", 270),
        kill_grace_s=setting("KILL_GRACE_S", 3),
        ssh_timeout_s=setting("SSH_TIMEOUT_S", 5),
    )


def now() -> str:
    return time.strftime("%H:%M:%S%z")


async def connect(cfg: Config) -> asyncssh.SSHClientConnection:
    user, _, host = cfg.host.rpartition("@")
    # keepalive: a link that drops mid-command fails within ~2x ssh_timeout_s instead of hanging
    return await asyncssh.connect(
        host,
        **({"username": user} if user else {}),
        connect_timeout=cfg.ssh_timeout_s,
        keepalive_interval=cfg.ssh_timeout_s,
        keepalive_count_max=2,
    )


async def sh(conn: asyncssh.SSHClientConnection, fn: Remote, *args: str) -> tuple[int, str]:
    """Run one device-remote.sh command: the script goes over stdin, the args as $1..."""
    r = await conn.run("bash -s -- " + shlex.join([fn, *args]), input=REMOTE, check=False, errors="replace")
    out = str(r.stdout).rpartition(MARK)[2]
    return 255 if r.exit_status is None else r.exit_status, out  # exit None: killed by a signal


async def tail(conn: asyncssh.SSHClientConnection) -> str:
    _, log = await sh(conn, Remote.LOGTAIL)
    return " ".join(log.split())  # one line, so the event stays one line


async def probe(conn: asyncssh.SSHClientConnection) -> tuple[State, tuple[dict[str, int], dict[str, int]] | None]:
    """The device state, plus two *_webrtc byte counts as {path: bytes}, or None while the MediaMTX API doesn't
    answer. Bytes, not open ports or MediaMTX's "ready" flag: those can be stale from a previous run."""
    _, out = await sh(conn, Remote.PROBE)
    first, _, rest = out.partition("\n")
    try:
        before, after = (
            {
                p["name"]: p.get("inboundBytes", p.get("bytesReceived", 0))
                for p in json.loads(s)["items"]
                if p["name"].endswith("_webrtc")
            }
            for s in rest.split("\n---\n", 1)
        )
    except (ValueError, KeyError, TypeError):  # ValueError also covers a missing second sample
        return state(first), None
    return state(first), (before, after)


def state(text: str) -> State:
    try:
        return State(text.strip())
    except ValueError:  # device-remote.sh printed something unexpected: treat it like a crash, with the log
        return State.CRASH


def flowing(before: dict[str, int], after: dict[str, int]) -> list[str]:
    """Camera paths whose bytes rose between the two samples."""
    return [k for k in before if after.get(k, 0) > before[k]]


async def report(conn: asyncssh.SSHClientConnection, st: State) -> int:
    """Print the event for a device state; returns the exit code."""
    match st:
        case State.RUNNING | State.ENDED | State.STOPPED:
            ev(st)
            return 0
        case State.LAUNCHING:
            ev("NOT_READY", f"launcher running, no worker process yet: {await tail(conn)}")
        case State.GONE:
            ev("CRASH", f"worker exited, launcher still running: {await tail(conn)}")
        case State.CRASH:
            ev("CRASH", await tail(conn))
    return 1


async def wait_ready(conn: asyncssh.SSHClientConnection, cfg: Config) -> int:
    reconnected: list[asyncssh.SSHClientConnection] = []
    try:
        return await poll_ready(conn, cfg, reconnected)
    finally:
        for c in reconnected:
            c.close()


async def poll_ready(
    first: asyncssh.SSHClientConnection, cfg: Config, reconnected: list[asyncssh.SSHClientConnection]
) -> int:
    # Keeps waiting while the worker is RUNNING or still LAUNCHING: slow is not a crash. Any other state (launcher
    # or this run's worker gone) is final: STOPPED, ENDED or CRASH (the log has harmless tracebacks), exit 1.
    # READY: at least one rising *_webrtc path per video file in the recording, so a camera without a stream
    # blocks it and leftover paths from an earlier recording don't. No DATA_DIR or no files: every listed path.
    cameras = 0
    if cfg.data_dir:
        _, out = await sh(first, Remote.CAMERAS, cfg.data_dir)
        cameras = int(out) if out.strip().isdigit() else 0
    conn: asyncssh.SSHClientConnection | None = first
    end, st, counts, rising = time.monotonic() + cfg.ready_timeout_s, None, None, []
    while time.monotonic() < end:
        try:
            if conn is None:
                conn = await connect(cfg)
                reconnected.append(conn)
            st, counts = await probe(conn)
        except SSH_ERRORS:  # a hiccup isn't a crash: reconnect on the next round
            if conn:
                conn.close()
            conn, st = None, None
            await asyncio.sleep(1)
            continue
        if st not in (State.RUNNING, State.LAUNCHING):
            return await report(conn, st) or 1  # ENDED/STOPPED before READY is no success for start
        before, after = counts or ({}, {})  # None while MediaMTX isn't up yet: keep waiting
        rising = flowing(before, after)
        if cameras:
            ready = len(rising) >= cameras
        else:
            ready = bool(before) and before.keys() == after.keys() and len(rising) == len(before)
        if ready:
            ev("READY", f"{now()} {len(rising)} camera streams flowing")
            return 0
        await asyncio.sleep(1)
    if st is None:
        why = "device unreachable over ssh"
    elif st == State.LAUNCHING:
        why = "no worker process yet, launcher still running (building?)"
    else:
        why = (
            "MediaMTX API unreachable"
            if counts is None
            else f"{len(rising)}/{cameras or len(counts[0])} camera streams"
        )
    try:
        log = await tail(conn) if conn else ""
    except SSH_ERRORS:
        log = ""
    ev("NOT_READY", f"{why} after {cfg.ready_timeout_s}s. Run wait-ready again, or check: {log}")
    return 1


async def run(conn: asyncssh.SSHClientConnection, cfg: Config) -> int:
    match cfg.command:
        case Command.PREFLIGHT:
            code, out = await sh(conn, Remote.PREFLIGHT, cfg.data_dir, cfg.product, cfg.worker_dir)
            print(out, end="", flush=True)
            if code:
                return code
            st, counts = await probe(conn)
            if counts is None:
                ev("WARN", "MediaMTX API not reachable yet (fine if the worker starts it)")
            elif st in (State.STOPPED, State.ENDED, State.CRASH) and flowing(*counts):
                # streaming without our worker would make READY meaningless
                ev("WARN", "video is already streaming without this skill's worker; stop it first or READY may mislead")
            ev("PREFLIGHT_OK")
            return 0
        case Command.START:
            code, _ = await sh(conn, Remote.LAUNCH, cfg.data_dir, cfg.product, cfg.worker_dir, str(cfg.kill_grace_s))
            if code:
                ev("CRASH", "no ~/Makefile and no worker.py found" if code == 3 else "tmux could not start the worker")
                return 1
            ev("STARTED", now())
            return await wait_ready(conn, cfg)  # the old worker is gone, so flowing bytes mean the new one
        case Command.WAIT_READY:
            return await wait_ready(conn, cfg)
        case Command.STATUS:
            _, out = await sh(conn, Remote.STATUS)
            return await report(conn, state(out))
        case Command.STOP:
            await sh(conn, Remote.STOP, str(cfg.kill_grace_s))
            ev("STOPPED")
            return 0


async def main(cfg: Config) -> int:
    try:
        async with await connect(cfg) as conn:
            return await run(conn, cfg)
    except SSH_ERRORS as e:
        ev("UNREACHABLE", f"ssh to {cfg.host} failed: {e.__class__.__name__} {e}".strip())
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(parse_args(sys.argv[1:]))))
