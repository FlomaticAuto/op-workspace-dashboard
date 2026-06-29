"""Universal wrapper for Olympic Paints scheduled tasks.

Usage:
    python run_job.py <job-id> --agent <AGENT> -- <command> [args...]

The wrapper times the wrapped command, captures stdout/stderr, writes a
heartbeat to %OLYMPIC_HEARTBEAT_ROOT% (default C:\\Users\\quint\\.claude\\heartbeats\\),
and on non-zero exit pings Telegram.

Exit code propagates from the wrapped command.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

# Support both `python run_job.py` (direct) and `python -m scripts.olympic_platform.run_job`.
# Relative imports only work in the latter mode; add a sys.path shim so the direct
# invocation (used in tests and Task Scheduler) also resolves the sibling modules.
try:
    from . import heartbeat, notify
except ImportError:
    _pkg_root = Path(__file__).resolve().parents[2]  # workspace-dashboard root
    if str(_pkg_root) not in sys.path:
        sys.path.insert(0, str(_pkg_root))
    from scripts.olympic_platform import heartbeat, notify  # type: ignore

_DEFAULT_HEARTBEATS = Path(r"C:\Users\Administrator\.claude\heartbeats")
_DEFAULT_LOGS = Path(r"C:\Users\Administrator\.claude\logs")


def _now_iso() -> str:
    # SAST is UTC+2; this machine is set to that locally.
    return _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=2))).isoformat(timespec="seconds")


def _heartbeat_root() -> Path:
    return Path(os.environ.get("OLYMPIC_HEARTBEAT_ROOT", str(_DEFAULT_HEARTBEATS)))


def _log_root() -> Path:
    return Path(os.environ.get("OLYMPIC_LOG_ROOT", str(_DEFAULT_LOGS)))


def _tail_lines(text: str, n: int = 50) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-n:])


def main(argv: list[str] | None = None) -> int:
    # argparse REMAINDER swallows options after a positional, so we parse in two
    # passes: first pull the known flags (--agent), then split on '--' for the cmd.
    parser = argparse.ArgumentParser(description="Olympic Paints job wrapper")
    parser.add_argument("job_id", help="Kebab-case job identifier")
    parser.add_argument("--agent", required=True, help="Owning agent (PULSE, HAVEN, ...)")
    args, remainder = parser.parse_known_args(argv)

    # remainder is everything after job_id and --agent <val>; strip leading '--'
    cmd = remainder
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        print("run_job.py: missing command after --", file=sys.stderr)
        return 2

    hb_root = _heartbeat_root()
    log_root = _log_root() / args.job_id
    log_root.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_root / f"{stamp}.log"

    started_at = _now_iso()
    t0 = _dt.datetime.now()

    launch_error: str | None = None
    stdout = ""
    stderr = ""

    # .cmd / .bat files are not PE executables — Windows CreateProcess rejects them
    # with ERROR_BAD_EXE_FORMAT (WinError 193) unless routed through cmd.exe.
    if cmd and Path(cmd[0]).suffix.lower() in {".cmd", ".bat"}:
        cmd = ["cmd.exe", "/c"] + cmd

    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as log_fh:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
            )
            stdout, stderr = proc.communicate()
            log_fh.write("=== STDOUT ===\n")
            log_fh.write(stdout or "")
            log_fh.write("\n=== STDERR ===\n")
            log_fh.write(stderr or "")
        exit_code = proc.returncode
    except (OSError, FileNotFoundError) as e:
        # Popen failed before the wrapped process started (missing executable,
        # permission denied, etc.). Record the failure as a heartbeat so the
        # control tower sees it instead of a silent void.
        launch_error = f"run_job.py: failed to launch wrapped command: {e}"
        stderr = launch_error
        exit_code = 127
        try:
            with open(log_path, "w", encoding="utf-8", errors="replace") as log_fh:
                log_fh.write("=== LAUNCH ERROR ===\n")
                log_fh.write(launch_error)
        except OSError:
            pass

    finished_at = _now_iso()
    duration = (_dt.datetime.now() - t0).total_seconds()

    summary = heartbeat.consume_summary(args.job_id, root=hb_root)

    record = {
        "job_id": args.job_id,
        "agent": args.agent,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(duration, 3),
        "exit_code": exit_code,
        "ok": exit_code == 0,
        "stdout_tail": _tail_lines(stdout, 50),
        "stderr_tail": _tail_lines(stderr, 50),
        "log_path": str(log_path),
    }
    if summary is not None:
        record["summary"] = summary

    heartbeat.write_latest(record, root=hb_root)
    heartbeat.append_history(record, root=hb_root)

    if not record["ok"] and os.environ.get("OLYMPIC_DISABLE_NOTIFY") != "1":
        notify.send_failure_alert(
            job_id=args.job_id,
            agent=args.agent,
            exit_code=exit_code,
            stderr_tail=record["stderr_tail"],
            log_path=str(log_path),
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
