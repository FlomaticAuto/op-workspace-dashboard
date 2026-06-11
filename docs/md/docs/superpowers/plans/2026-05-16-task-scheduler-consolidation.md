# Task Scheduler Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every Olympic-related scheduled task under `\Olympic Paints\<AGENT>\` in Windows Task Scheduler, instrument every run with a heartbeat (timing + exit + optional summary), Telegram-alert on failure, and publish a `schedule_manifest.json` for the eventual control-tower UI.

**Architecture:** A Python wrapper (`run_job.py`) is prepended to every Task Scheduler action. It records start/end/exit code, captures a tail of stdout/stderr, picks up an optional summary file written by the wrapped script, writes one latest-run heartbeat and appends to a rolling 100-entry history. On failure it pings Telegram. A separate manifest builder reads tasks under `\Olympic Paints\` via the `Schedule.Service` COM API, joins with heartbeats, and writes the manifest JSON consumed by sub-project #3.

**Tech Stack:** Python 3.11+, pytest, PowerShell 5.1 + `Schedule.Service` COM, standard library only (`subprocess`, `json`, `pathlib`, `urllib.request`, `datetime`, `os`, `argparse`). No third-party Python deps beyond `truststore` (already required on this machine).

**Source layout:** All scripts live in the workspace-dashboard git repo at `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\`. Heartbeats, logs, and migration backups live under `C:\Users\quint\.claude\` (outside OneDrive, per the "logs outside OneDrive" rule).

---

## File Structure

**Create:**

- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\__init__.py`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\heartbeat.py` — schema, write, history rotation
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\notify.py` — Telegram alert
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py` — wrapper CLI
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\build_schedule_manifest.py`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\migrate_tasks.ps1`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\restore_tasks.ps1`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\agent_mapping.json` — script-path → agent classification
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\README.md` — operator guide
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\tests\__init__.py`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\tests\test_heartbeat.py`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\tests\test_run_job.py`
- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\tests\test_build_schedule_manifest.py`

**Modify:**

- `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\` is new — nothing else is modified by code tasks. The migration tasks edit Task Scheduler state, not files.

**Output files produced at runtime:**

- `C:\Users\quint\.claude\heartbeats\<job-id>.json` — latest run
- `C:\Users\quint\.claude\heartbeats\<job-id>.history.jsonl` — rolling last 100
- `C:\Users\quint\.claude\heartbeats\_summary\<job-id>.json` — optional input, consumed by wrapper
- `C:\Users\quint\.claude\heartbeats\_migration-backups\<timestamp>\*.xml` — pre-migration task XML
- `C:\Users\quint\.claude\logs\<job-id>\<YYYY-MM-DD_HH-MM-SS>.log` — full stdout+stderr of each run
- `C:\Users\quint\workspace-dashboard\data\schedule_manifest.json` — final consolidated manifest

---

## Section A — Foundation Code

### Task 1: Project bootstrap

**Files:**
- Create: `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\__init__.py`
- Create: `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\tests\__init__.py`
- Create: `C:\Users\quint\workspace-dashboard\scripts\olympic_platform\agent_mapping.json`

- [ ] **Step 1: Create package directories**

Run from `C:\Users\quint\workspace-dashboard\`:

```powershell
New-Item -ItemType Directory -Force scripts\olympic_platform\tests | Out-Null
New-Item -ItemType File -Force scripts\olympic_platform\__init__.py | Out-Null
New-Item -ItemType File -Force scripts\olympic_platform\tests\__init__.py | Out-Null
```

- [ ] **Step 2: Create agent_mapping.json**

Write to `scripts/olympic_platform/agent_mapping.json`:

```json
{
  "_comment": "Maps script path substrings (case-insensitive) to the owning agent. First match wins. Order matters.",
  "rules": [
    { "pattern": "pulse",                "agent": "PULSE"   },
    { "pattern": "haven",                "agent": "HAVEN"   },
    { "pattern": "clocking",             "agent": "HAVEN"   },
    { "pattern": "prism",                "agent": "PRISM"   },
    { "pattern": "weekly_health",        "agent": "PRISM"   },
    { "pattern": "vault",                "agent": "VAULT"   },
    { "pattern": "claude_todos",         "agent": "VAULT"   },
    { "pattern": "meeting_extract",      "agent": "VAULT"   },
    { "pattern": "striker",              "agent": "STRIKER" },
    { "pattern": "sigma",                "agent": "SIGMA"   },
    { "pattern": "blaze",                "agent": "BLAZE"   },
    { "pattern": "flash",                "agent": "FLASH"   },
    { "pattern": "kpi_dashboard",        "agent": "PRISM"   },
    { "pattern": "geo_map",              "agent": "PRISM"   },
    { "pattern": "ecommerce",            "agent": "FLASH"   },
    { "pattern": "merchandising",        "agent": "STRIKER" },
    { "pattern": "store_health",         "agent": "STRIKER" },
    { "pattern": "returns",              "agent": "SIGMA"   },
    { "pattern": "cso_insights",         "agent": "PRISM"   },
    { "pattern": "zoho_meetings",        "agent": "STRIKER" }
  ],
  "fallback_agent": "MISC"
}
```

- [ ] **Step 3: Create heartbeat output directories**

```powershell
New-Item -ItemType Directory -Force C:\Users\quint\.claude\heartbeats\_summary | Out-Null
New-Item -ItemType Directory -Force C:\Users\quint\.claude\heartbeats\_migration-backups | Out-Null
New-Item -ItemType Directory -Force C:\Users\quint\.claude\logs | Out-Null
```

- [ ] **Step 4: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/__init__.py scripts/olympic_platform/tests/__init__.py scripts/olympic_platform/agent_mapping.json
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): scaffold package + agent mapping"
```

---

### Task 2: Heartbeat module — schema and atomic write

**Files:**
- Create: `scripts/olympic_platform/heartbeat.py`
- Test:   `scripts/olympic_platform/tests/test_heartbeat.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/olympic_platform/tests/test_heartbeat.py`:

```python
import json
from pathlib import Path

from scripts.olympic_platform import heartbeat


def test_write_latest_creates_json_file(tmp_path):
    record = {
        "job_id": "demo-job",
        "agent": "PULSE",
        "started_at": "2026-05-16T06:00:00+02:00",
        "finished_at": "2026-05-16T06:00:05+02:00",
        "duration_seconds": 5,
        "exit_code": 0,
        "ok": True,
        "stdout_tail": "done",
        "stderr_tail": "",
        "summary": {"emails_sent": 4},
    }
    heartbeat.write_latest(record, root=tmp_path)
    out = tmp_path / "demo-job.json"
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8")) == record
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
cd C:\Users\quint\workspace-dashboard
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py::test_write_latest_creates_json_file -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.olympic_platform.heartbeat'` (or similar — module doesn't exist yet).

- [ ] **Step 3: Implement heartbeat.write_latest**

Create `scripts/olympic_platform/heartbeat.py`:

```python
"""Heartbeat schema + atomic writes for the Olympic Paints job wrapper."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

DEFAULT_ROOT = Path(r"C:\Users\quint\.claude\heartbeats")
HISTORY_LIMIT = 100


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_latest(record: Dict[str, Any], root: Path = DEFAULT_ROOT) -> Path:
    """Write the latest-run heartbeat to <root>/<job_id>.json atomically."""
    job_id = record["job_id"]
    out = Path(root) / f"{job_id}.json"
    _atomic_write_json(out, record)
    return out
```

- [ ] **Step 4: Verify the test passes**

```powershell
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Add the failing history-rotation test**

Append to `test_heartbeat.py`:

```python
def test_append_history_keeps_last_100(tmp_path):
    job_id = "rotate-test"
    # Pre-fill 100 entries
    for i in range(100):
        heartbeat.append_history(
            {"job_id": job_id, "n": i}, root=tmp_path
        )
    # Add one more — should evict the oldest
    heartbeat.append_history({"job_id": job_id, "n": 100}, root=tmp_path)

    lines = (tmp_path / f"{job_id}.history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 100
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["n"] == 1     # oldest (n=0) was evicted
    assert parsed[-1]["n"] == 100  # newest is appended
```

- [ ] **Step 6: Verify the new test fails**

```powershell
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py::test_append_history_keeps_last_100 -v
```

Expected: `AttributeError: module 'scripts.olympic_platform.heartbeat' has no attribute 'append_history'`.

- [ ] **Step 7: Implement append_history**

Append to `heartbeat.py`:

```python
def append_history(record: Dict[str, Any], root: Path = DEFAULT_ROOT) -> Path:
    """Append record to <root>/<job_id>.history.jsonl, truncating to HISTORY_LIMIT entries."""
    job_id = record["job_id"]
    out = Path(root) / f"{job_id}.history.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)

    existing: List[str] = []
    if out.exists():
        existing = out.read_text(encoding="utf-8").splitlines()

    existing.append(json.dumps(record, ensure_ascii=False))
    trimmed = existing[-HISTORY_LIMIT:]

    fd, tmp = tempfile.mkstemp(
        prefix=out.name + ".",
        suffix=".tmp",
        dir=str(out.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("\n".join(trimmed) + "\n")
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    return out
```

- [ ] **Step 8: Verify both tests pass**

```powershell
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py -v
```

Expected: 2 passed.

- [ ] **Step 9: Add the failing summary-consumption test**

Append to `test_heartbeat.py`:

```python
def test_consume_summary_returns_and_deletes(tmp_path):
    summary_dir = tmp_path / "_summary"
    summary_dir.mkdir()
    (summary_dir / "demo.json").write_text(
        '{"rows": 42}', encoding="utf-8"
    )
    result = heartbeat.consume_summary("demo", root=tmp_path)
    assert result == {"rows": 42}
    assert not (summary_dir / "demo.json").exists()


def test_consume_summary_missing_returns_none(tmp_path):
    (tmp_path / "_summary").mkdir()
    assert heartbeat.consume_summary("nope", root=tmp_path) is None


def test_consume_summary_malformed_returns_none(tmp_path):
    summary_dir = tmp_path / "_summary"
    summary_dir.mkdir()
    (summary_dir / "broken.json").write_text("{not json", encoding="utf-8")
    assert heartbeat.consume_summary("broken", root=tmp_path) is None
    # Malformed file is still removed so it can't poison the next run
    assert not (summary_dir / "broken.json").exists()
```

- [ ] **Step 10: Verify the new tests fail**

```powershell
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py -v
```

Expected: 3 new tests fail with `AttributeError: ... 'consume_summary'`.

- [ ] **Step 11: Implement consume_summary**

Append to `heartbeat.py`:

```python
def consume_summary(job_id: str, root: Path = DEFAULT_ROOT) -> Dict[str, Any] | None:
    """Read and delete <root>/_summary/<job_id>.json. Returns dict or None.

    Malformed JSON is logged via return value (None) and the file is still
    removed so it cannot poison the next run.
    """
    path = Path(root) / "_summary" / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = None
    except json.JSONDecodeError:
        data = None
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return data
```

- [ ] **Step 12: Verify all tests pass**

```powershell
python -m pytest scripts/olympic_platform/tests/test_heartbeat.py -v
```

Expected: 5 passed.

- [ ] **Step 13: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/heartbeat.py scripts/olympic_platform/tests/test_heartbeat.py
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): heartbeat schema, atomic write, history rotation, summary ingestion"
```

---

### Task 3: Telegram notify module

**Files:**
- Create: `scripts/olympic_platform/notify.py`

This module is intentionally small and integration-tested via run_job.py. No unit tests for it directly — it's a 30-line wrapper around `urllib.request`.

- [ ] **Step 1: Write notify.py**

```python
"""Telegram alert for failed jobs.

Reads TELEGRAM_BOT_TOKEN from environment. If absent, calls become no-ops
so the wrapper still records heartbeats in environments without Telegram.

Chat ID is fixed to Quintus's bot chat (8042233389) per project memory.
"""

from __future__ import annotations

import json
import os
import ssl
import urllib.parse
import urllib.request

try:
    import truststore  # local CA inspection — required on this machine
    truststore.inject_into_ssl()
except Exception:
    pass

CHAT_ID = "8042233389"
API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def send_failure_alert(
    job_id: str,
    agent: str,
    exit_code: int,
    stderr_tail: str,
    log_path: str,
) -> bool:
    """Send a failure alert to Telegram. Returns True on success, False otherwise.

    Never raises — failure to notify must not mask the original job failure.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False

    body_lines = [
        f"❌ <b>{agent} — {job_id}</b> failed",
        f"exit_code: <code>{exit_code}</code>",
        f"log: <code>{log_path}</code>",
    ]
    if stderr_tail.strip():
        tail = stderr_tail.strip()
        if len(tail) > 800:
            tail = "…" + tail[-800:]
        body_lines.append("<pre>" + _html_escape(tail) + "</pre>")

    payload = urllib.parse.urlencode(
        {
            "chat_id": CHAT_ID,
            "text": "\n".join(body_lines),
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        API_BASE.format(token=token),
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as resp:
            return resp.status == 200
    except Exception:
        return False


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
```

- [ ] **Step 2: Smoke-test by setting a fake token and confirming graceful failure**

```powershell
cd C:\Users\quint\workspace-dashboard
$env:TELEGRAM_BOT_TOKEN = "0:invalid"
python -c "from scripts.olympic_platform.notify import send_failure_alert; print(send_failure_alert('test', 'PULSE', 1, 'boom', 'C:\\tmp\\x.log'))"
Remove-Item Env:TELEGRAM_BOT_TOKEN
```

Expected: prints `False` (invalid token rejected by Telegram) but does not raise.

- [ ] **Step 3: Smoke-test the no-token path**

```powershell
python -c "from scripts.olympic_platform.notify import send_failure_alert; print(send_failure_alert('test', 'PULSE', 1, 'boom', 'C:\\tmp\\x.log'))"
```

Expected: prints `False` (no token → no-op).

- [ ] **Step 4: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/notify.py
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): Telegram failure alert helper"
```

---

### Task 4: `run_job.py` — happy path

**Files:**
- Create: `scripts/olympic_platform/run_job.py`
- Test:   `scripts/olympic_platform/tests/test_run_job.py`

- [ ] **Step 1: Write the failing happy-path test**

Create `scripts/olympic_platform/tests/test_run_job.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]   # workspace-dashboard root
RUN_JOB = REPO / "scripts" / "olympic_platform" / "run_job.py"


def _invoke(job_id, agent, cmd, tmp_path, env_extra=None):
    env = {
        "OLYMPIC_HEARTBEAT_ROOT": str(tmp_path / "heartbeats"),
        "OLYMPIC_LOG_ROOT":       str(tmp_path / "logs"),
        "OLYMPIC_DISABLE_NOTIFY": "1",
        "PATH":                   __import__("os").environ.get("PATH", ""),
        "SYSTEMROOT":             __import__("os").environ.get("SYSTEMROOT", r"C:\Windows"),
    }
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(RUN_JOB), job_id, "--agent", agent, "--"] + cmd,
        capture_output=True,
        text=True,
        env=env,
    )


def test_happy_path_writes_heartbeat(tmp_path):
    result = _invoke(
        "happy", "PULSE",
        [sys.executable, "-c", "print('hello')"],
        tmp_path,
    )
    assert result.returncode == 0

    hb = json.loads((tmp_path / "heartbeats" / "happy.json").read_text(encoding="utf-8"))
    assert hb["job_id"] == "happy"
    assert hb["agent"] == "PULSE"
    assert hb["exit_code"] == 0
    assert hb["ok"] is True
    assert "hello" in hb["stdout_tail"]
    assert hb["stderr_tail"] == ""
    assert hb["duration_seconds"] >= 0
    assert "started_at" in hb and "finished_at" in hb
```

- [ ] **Step 2: Verify the test fails**

```powershell
cd C:\Users\quint\workspace-dashboard
python -m pytest scripts/olympic_platform/tests/test_run_job.py -v
```

Expected: `FileNotFoundError` — run_job.py doesn't exist yet.

- [ ] **Step 3: Implement run_job.py (happy path only)**

Create `scripts/olympic_platform/run_job.py`:

```python
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

from . import heartbeat, notify

_DEFAULT_HEARTBEATS = Path(r"C:\Users\quint\.claude\heartbeats")
_DEFAULT_LOGS = Path(r"C:\Users\quint\.claude\logs")


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
    parser = argparse.ArgumentParser(description="Olympic Paints job wrapper")
    parser.add_argument("job_id", help="Kebab-case job identifier")
    parser.add_argument("--agent", required=True, help="Owning agent (PULSE, HAVEN, ...)")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Wrapped command (after --)")
    args = parser.parse_args(argv)

    cmd = args.cmd
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

    finished_at = _now_iso()
    duration = (_dt.datetime.now() - t0).total_seconds()
    exit_code = proc.returncode

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
```

- [ ] **Step 4: Verify the happy-path test passes**

```powershell
python -m pytest scripts/olympic_platform/tests/test_run_job.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/run_job.py scripts/olympic_platform/tests/test_run_job.py
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): run_job.py wrapper, happy path with heartbeat"
```

---

### Task 5: `run_job.py` — failure path, summary ingestion, history

**Files:**
- Modify: `scripts/olympic_platform/tests/test_run_job.py` (add tests)

The implementation in Task 4 already covers these. These tests prove the behaviors.

- [ ] **Step 1: Add the failure-path test**

Append to `test_run_job.py`:

```python
def test_failure_path_writes_heartbeat_ok_false(tmp_path):
    result = _invoke(
        "boom", "PULSE",
        [sys.executable, "-c", "import sys; sys.stderr.write('crash'); sys.exit(7)"],
        tmp_path,
    )
    assert result.returncode == 7

    hb = json.loads((tmp_path / "heartbeats" / "boom.json").read_text(encoding="utf-8"))
    assert hb["exit_code"] == 7
    assert hb["ok"] is False
    assert "crash" in hb["stderr_tail"]
```

- [ ] **Step 2: Add the summary-ingestion test**

Append to `test_run_job.py`:

```python
def test_summary_file_is_picked_up(tmp_path):
    summary_dir = tmp_path / "heartbeats" / "_summary"
    summary_dir.mkdir(parents=True)
    (summary_dir / "rich.json").write_text('{"rows": 17}', encoding="utf-8")

    result = _invoke(
        "rich", "PRISM",
        [sys.executable, "-c", "print('ok')"],
        tmp_path,
    )
    assert result.returncode == 0

    hb = json.loads((tmp_path / "heartbeats" / "rich.json").read_text(encoding="utf-8"))
    assert hb["summary"] == {"rows": 17}
    # Summary file is consumed (deleted) so it cannot leak to the next run.
    assert not (summary_dir / "rich.json").exists()
```

- [ ] **Step 3: Add the history-rotation integration test**

Append to `test_run_job.py`:

```python
def test_history_appends_each_run(tmp_path):
    for _ in range(3):
        _invoke(
            "rotate", "PULSE",
            [sys.executable, "-c", "pass"],
            tmp_path,
        )
    lines = (tmp_path / "heartbeats" / "rotate.history.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(lines) == 3
```

- [ ] **Step 4: Run the new tests**

```powershell
python -m pytest scripts/olympic_platform/tests/test_run_job.py -v
```

Expected: 4 passed (1 from Task 4 + 3 new).

- [ ] **Step 5: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/tests/test_run_job.py
git -C C:\Users\quint\workspace-dashboard commit -m "test(olympic-platform): cover failure path, summary ingestion, history"
```

---

### Task 6: `run_job.py` — missing-command and missing-agent guard rails

**Files:**
- Modify: `scripts/olympic_platform/tests/test_run_job.py`

- [ ] **Step 1: Add error-path tests**

Append to `test_run_job.py`:

```python
def test_missing_command_returns_2(tmp_path):
    result = _invoke("noop", "PULSE", [], tmp_path)
    assert result.returncode == 2
    assert "missing command" in result.stderr.lower()


def test_missing_agent_fails_argparse(tmp_path):
    # bypass _invoke helper to omit --agent
    result = subprocess.run(
        [sys.executable, str(RUN_JOB), "x", "--", sys.executable, "-c", "pass"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "--agent" in result.stderr
```

- [ ] **Step 2: Run the tests**

```powershell
python -m pytest scripts/olympic_platform/tests/test_run_job.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/tests/test_run_job.py
git -C C:\Users\quint\workspace-dashboard commit -m "test(olympic-platform): guard rails for missing --agent and command"
```

---

## Section B — Pilot Deployment (Phase 1)

### Task 7: Pilot — wrap `Olympic — Sync Claude TODOs`

This is a one-time manual migration of a single, low-risk task. It validates the wrapper in production before any bulk migration code runs.

**Files:**
- None (Task Scheduler state only)

- [ ] **Step 1: Inspect the current task**

```powershell
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()
$folder = $svc.GetFolder("\")
$task   = $folder.GetTask("Olympic — Sync Claude TODOs")
$task.Definition.Actions | ForEach-Object { "{0} | {1} | {2}" -f $_.Path, $_.Arguments, $_.WorkingDirectory }
```

Expected output: prints the current Python interpreter, the script path, and the working directory.

Write all three values down. You'll need them in Step 3.

- [ ] **Step 2: Export the current XML as a backup**

```powershell
$backupDir = "C:\Users\quint\.claude\heartbeats\_migration-backups\pilot-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss")
New-Item -ItemType Directory -Force $backupDir | Out-Null
schtasks /Query /TN "Olympic — Sync Claude TODOs" /XML > "$backupDir\sync-claude-todos.xml"
"Backup written to: $backupDir"
```

Expected: the backup XML file exists and the directory path is printed.

- [ ] **Step 3: Create the new wrapped task under \Olympic Paints\VAULT\ via XML round-trip**

Round-tripping through XML preserves every trigger and setting detail. Edit only the action.

```powershell
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()

# 3a. Ensure the agent folder tree exists (idempotent)
try { $svc.GetFolder('\').CreateFolder('Olympic Paints') | Out-Null } catch {}
try { $svc.GetFolder('\Olympic Paints').CreateFolder('VAULT') | Out-Null } catch {}

# 3b. Read the original task's XML
$xml = [xml](schtasks /Query /TN "Olympic — Sync Claude TODOs" /XML)
$ns  = New-Object Xml.XmlNamespaceManager $xml.NameTable
$ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')

# 3c. Read the original action values
$execNode  = $xml.SelectSingleNode('//t:Exec', $ns)
$origPath  = $execNode.SelectSingleNode('t:Command',          $ns).InnerText
$origArgs  = $execNode.SelectSingleNode('t:Arguments',        $ns).InnerText
$origWd    = $execNode.SelectSingleNode('t:WorkingDirectory', $ns).InnerText

# 3d. Rewrite the action to wrap with run_job.py
$wrapper = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py'
$execNode.SelectSingleNode('t:Command',   $ns).InnerText = 'python'
$execNode.SelectSingleNode('t:Arguments', $ns).InnerText = "`"$wrapper`" sync-claude-todos --agent VAULT -- `"$origPath`" $origArgs"
# WorkingDirectory left untouched

# 3e. Write the modified XML to a temp file and register under the new path
$tmp = New-TemporaryFile
$xml.Save($tmp.FullName)
schtasks /Create /XML $tmp.FullName /TN "Olympic Paints\VAULT\Sync Claude TODOs" /F
Remove-Item $tmp.FullName

'Registered: \Olympic Paints\VAULT\Sync Claude TODOs'
```

Expected: `SUCCESS: The scheduled task "Olympic Paints\VAULT\Sync Claude TODOs" has successfully been created.`

- [ ] **Step 4: Verify the new task exists and is correct**

```powershell
$svc.GetFolder("\Olympic Paints\VAULT").GetTask("Sync Claude TODOs").Definition.Actions | ForEach-Object {
    "{0} | {1}" -f $_.Path, $_.Arguments
}
```

Expected: prints `python | "C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py" sync-claude-todos --agent VAULT -- ...`.

- [ ] **Step 5: Run the new task once manually**

```powershell
Start-ScheduledTask -TaskPath "\Olympic Paints\VAULT\" -TaskName "Sync Claude TODOs"
Start-Sleep 30
Get-Content "C:\Users\quint\.claude\heartbeats\sync-claude-todos.json"
```

Expected: a JSON heartbeat with `"ok": true` (assuming the underlying script succeeds).

- [ ] **Step 6: Delete the old root-level task**

```powershell
$svc.GetFolder("\").DeleteTask("Olympic — Sync Claude TODOs", 0)
"Deleted old task."
```

- [ ] **Step 7: Add the pilot to docs**

Create `scripts/olympic_platform/README.md`:

```markdown
# Olympic Platform — Operator Guide

## Concepts

- Every Olympic-related scheduled task lives at `\Olympic Paints\<AGENT>\<Name>` in Task Scheduler.
- Every task is wrapped by `run_job.py`, which writes a heartbeat after each run.
- Failures ping Telegram immediately. There is no daily success digest.
- A separate manifest builder publishes `schedule_manifest.json` for the control-tower UI.

## Locations

- Wrapper:    `scripts/olympic_platform/run_job.py`
- Heartbeats: `C:\Users\quint\.claude\heartbeats\<job-id>.json` (+ `.history.jsonl`)
- Logs:       `C:\Users\quint\.claude\logs\<job-id>\<timestamp>.log`
- Manifest:   `C:\Users\quint\workspace-dashboard\data\schedule_manifest.json`

## Pilot

The pilot task is `\Olympic Paints\VAULT\Sync Claude TODOs`. Migrated <DATE>.

## Adding a new wrapped task

Use `migrate_tasks.ps1` for existing tasks. For new ones, follow the action format:

```
python "C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py" <job-id> --agent <AGENT> -- <original command>
```
```

Replace `<DATE>` with today's date.

- [ ] **Step 8: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/README.md
git -C C:\Users\quint\workspace-dashboard commit -m "docs(olympic-platform): operator guide + pilot record"
```

- [ ] **Step 9: 3-day soak gate**

Do not proceed to Task 8 until at least 3 successful pilot runs have produced heartbeats. To check:

```powershell
Get-Content "C:\Users\quint\.claude\heartbeats\sync-claude-todos.history.jsonl"
```

Expected: at least 3 lines, each with `"ok": true`.

- [ ] **Step 10: Forced-failure verification**

Force one failure and verify Telegram fires. We make the wrapper invoke a guaranteed-failing command by registering a temporary override task.

```powershell
# Register a one-off task that uses the wrapper to run a script that exits 1.
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()
$folder = $svc.GetFolder('\Olympic Paints\VAULT')

$def = $svc.NewTask(0)
$def.RegistrationInfo.Description = 'Forced-failure smoke test for run_job.py'
$trig = $def.Triggers.Create(1)            # TASK_TRIGGER_TIME — one-shot
$trig.StartBoundary = (Get-Date).AddSeconds(10).ToString('yyyy-MM-ddTHH:mm:ss')
$trig.Enabled = $true

$act = $def.Actions.Create(0)
$act.Path = 'python'
$wrapper = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py'
$act.Arguments = "`"$wrapper`" forced-failure-test --agent VAULT -- python -c `"import sys; sys.exit(1)`""
$folder.RegisterTaskDefinition('Forced Failure Test', $def, 6, $null, $null, 3) | Out-Null

Start-Sleep 15

# Check heartbeat
Get-Content C:\Users\quint\.claude\heartbeats\forced-failure-test.json

# Clean up
$folder.DeleteTask('Forced Failure Test', 0)
```

Expected:
1. Heartbeat shows `"ok": false`, `"exit_code": 1`.
2. A Telegram message arrives on chat `8042233389` within ~10s of the run.

If the Telegram message does NOT arrive: check `TELEGRAM_BOT_TOKEN` is present in the environment the scheduled task runs in. Setting per-task env requires editing the XML; simpler is to set it once at user scope: `[Environment]::SetEnvironmentVariable('TELEGRAM_BOT_TOKEN', '<token>', 'User')`. Use the bot token from `1.Projects/PULSE — Sales & Ops Manager/.env` (per `feedback_telegram_token_source.md`).

Document the result in the README under a "Pilot Verification" section before moving on.

---

## Section C — Migration Tooling

### Task 8: `migrate_tasks.ps1` — dry-run inventory

**Files:**
- Create: `scripts/olympic_platform/migrate_tasks.ps1`

- [ ] **Step 1: Write the dry-run skeleton**

Create `scripts/olympic_platform/migrate_tasks.ps1`:

```powershell
<#
.SYNOPSIS
    Migrate Olympic-related scheduled tasks into \Olympic Paints\<AGENT>\,
    wrapping each action with run_job.py.

.PARAMETER DryRun
    Default. Prints the migration plan without changing Task Scheduler.

.PARAMETER Apply
    Performs the migration. Backs up each task's XML first.

.PARAMETER OnlyAgent
    Limit migration to a single agent (e.g. PULSE). Useful for phased rollout.
#>
[CmdletBinding(DefaultParameterSetName = 'DryRun')]
param(
    [Parameter(ParameterSetName = 'DryRun')]  [switch]$DryRun = $true,
    [Parameter(ParameterSetName = 'Apply')]   [switch]$Apply,
    [string]$OnlyAgent
)

$ErrorActionPreference = 'Stop'

# ---------- Config ----------
$WrapperPath  = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py'
$MappingPath  = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\agent_mapping.json'
$BackupRoot   = 'C:\Users\quint\.claude\heartbeats\_migration-backups'
$InScopePaths = @(
    'OneDrive\1.Projects\1.Olympic Paints',
    'workspace-dashboard',
    'olympic-paints-'
)

# ---------- Helpers ----------
function Get-AgentForCommand {
    param([string]$CommandText)
    $mapping = Get-Content $MappingPath -Raw | ConvertFrom-Json
    $lower   = $CommandText.ToLower()
    foreach ($rule in $mapping.rules) {
        if ($lower.Contains($rule.pattern.ToLower())) {
            return $rule.agent
        }
    }
    return $mapping.fallback_agent
}

function ConvertTo-JobId {
    param([string]$TaskName)
    $slug = $TaskName.ToLower()
    $slug = $slug -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    return $slug
}

function Test-InScope {
    param([string]$CommandText)
    foreach ($p in $InScopePaths) {
        if ($CommandText -like "*$p*") { return $true }
    }
    return $false
}

# ---------- Walk every task in the tree ----------
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()

function Walk-Folder {
    param($Folder, [System.Collections.Generic.List[object]]$Acc)
    foreach ($t in $Folder.GetTasks(0)) { $Acc.Add($t) }
    foreach ($sub in $Folder.GetFolders(0)) { Walk-Folder -Folder $sub -Acc $Acc }
}
$all = New-Object System.Collections.Generic.List[object]
Walk-Folder -Folder $svc.GetFolder('\') -Acc $all

# ---------- Build the plan ----------
$plan = @()
foreach ($task in $all) {
    if ($task.Path -like '\Microsoft\*') { continue }
    if ($task.Path -like '\Olympic Paints\*') { continue }  # already migrated

    $def = $task.Definition
    if ($def.Actions.Count -eq 0) { continue }

    $action = $def.Actions.Item(1)
    $cmdText = "$($action.Path) $($action.Arguments)"
    if (-not (Test-InScope $cmdText)) { continue }

    $agent = Get-AgentForCommand $cmdText
    if ($OnlyAgent -and ($agent -ne $OnlyAgent)) { continue }

    $name   = Split-Path $task.Path -Leaf
    $jobId  = ConvertTo-JobId -TaskName $name

    $plan += [pscustomobject]@{
        OldPath = $task.Path
        NewPath = "\Olympic Paints\$agent\$name"
        Agent   = $agent
        JobId   = $jobId
        Action  = $cmdText
    }
}

# ---------- Print or apply ----------
if ($plan.Count -eq 0) {
    Write-Host 'No in-scope tasks found.' -ForegroundColor Yellow
    return
}

Write-Host ("Migration plan: {0} task(s)" -f $plan.Count) -ForegroundColor Cyan
$plan | Format-Table OldPath, NewPath, Agent, JobId -AutoSize

if ($Apply) {
    Write-Host 'Apply mode is not yet implemented in this task — see Task 9.' -ForegroundColor Red
    exit 1
} else {
    Write-Host 'Dry run only. Re-run with -Apply to migrate.' -ForegroundColor Green
}
```

- [ ] **Step 2: Run the dry-run**

```powershell
cd C:\Users\quint\workspace-dashboard
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1
```

Expected: a table of in-scope tasks with their proposed new paths and agents. The pilot task (`\Olympic Paints\VAULT\Sync Claude TODOs`) should NOT appear because it's already under `\Olympic Paints\`.

If any task shows `Agent: MISC`, that means the classifier couldn't decide. Either:
- Add a rule to `agent_mapping.json`, or
- Plan to migrate that task manually later.

- [ ] **Step 3: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/migrate_tasks.ps1
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): migrate_tasks.ps1 dry-run inventory"
```

---

### Task 9: `migrate_tasks.ps1` — apply mode

**Files:**
- Modify: `scripts/olympic_platform/migrate_tasks.ps1`

- [ ] **Step 1: Replace the apply block**

In `migrate_tasks.ps1`, replace the `if ($Apply)` / `else` block at the bottom with:

```powershell
if (-not $Apply) {
    Write-Host 'Dry run only. Re-run with -Apply to migrate.' -ForegroundColor Green
    return
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Force $backupDir | Out-Null
Write-Host "Backups -> $backupDir" -ForegroundColor Cyan

# Ensure \Olympic Paints\<AGENT> folders exist
$opRoot = $svc.GetFolder('\')
try { $opRoot.CreateFolder('Olympic Paints') | Out-Null } catch {}
$op = $svc.GetFolder('\Olympic Paints')
foreach ($agent in ($plan | Select-Object -ExpandProperty Agent -Unique)) {
    try { $op.CreateFolder($agent) | Out-Null } catch {}
}

foreach ($item in $plan) {
    Write-Host ("=> {0}  ->  {1}" -f $item.OldPath, $item.NewPath) -ForegroundColor Yellow

    # 1. Resolve old task and back up XML
    $oldFolderPath = Split-Path $item.OldPath -Parent
    if ([string]::IsNullOrEmpty($oldFolderPath)) { $oldFolderPath = '\' }
    $oldFolder = $svc.GetFolder($oldFolderPath)
    $oldName   = Split-Path $item.OldPath -Leaf
    $oldTask   = $oldFolder.GetTask($oldName)

    $safeName  = ($oldName -replace '[\\/:*?"<>|]', '_')
    $xmlPath   = Join-Path $backupDir "$safeName.xml"
    schtasks /Query /TN $item.OldPath.TrimStart('\') /XML | Out-File -Encoding utf8 $xmlPath

    # 2. Clone definition and rewrite the action
    $oldDef  = $oldTask.Definition
    $newDef  = $svc.NewTask(0)
    $newDef.RegistrationInfo.Description = $oldDef.RegistrationInfo.Description
    $newDef.Principal.UserId   = $oldDef.Principal.UserId
    $newDef.Principal.LogonType = $oldDef.Principal.LogonType
    $newDef.Principal.RunLevel  = $oldDef.Principal.RunLevel
    $newDef.Settings.Enabled    = $oldDef.Settings.Enabled
    $newDef.Settings.MultipleInstances = $oldDef.Settings.MultipleInstances
    $newDef.Settings.StartWhenAvailable = $oldDef.Settings.StartWhenAvailable
    $newDef.Settings.StopIfGoingOnBatteries = $oldDef.Settings.StopIfGoingOnBatteries
    $newDef.Settings.DisallowStartIfOnBatteries = $oldDef.Settings.DisallowStartIfOnBatteries

    foreach ($t in $oldDef.Triggers) {
        $clone = $newDef.Triggers.Create($t.Type)
        $clone.StartBoundary = $t.StartBoundary
        $clone.Enabled       = $t.Enabled
        if ($t.Repetition) {
            $clone.Repetition.Interval = $t.Repetition.Interval
            $clone.Repetition.Duration = $t.Repetition.Duration
        }
    }

    $oldAction = $oldDef.Actions.Item(1)
    $origPath  = $oldAction.Path
    $origArgs  = $oldAction.Arguments
    $origWd    = $oldAction.WorkingDirectory

    $newAction = $newDef.Actions.Create(0)
    $newAction.Path = 'python'
    $newAction.Arguments = "`"$WrapperPath`" $($item.JobId) --agent $($item.Agent) -- `"$origPath`" $origArgs"
    $newAction.WorkingDirectory = $origWd

    # 3. Register at new path
    $targetFolder = $svc.GetFolder("\Olympic Paints\$($item.Agent)")
    $targetFolder.RegisterTaskDefinition(
        $oldName,
        $newDef,
        6,        # TASK_CREATE_OR_UPDATE
        $null, $null, 3
    ) | Out-Null

    # 4. Verify
    $verify = $targetFolder.GetTask($oldName)
    if (-not $verify) {
        throw "Verification failed: new task not found at $($item.NewPath)"
    }

    # 5. Delete old
    $oldFolder.DeleteTask($oldName, 0)
    Write-Host '   migrated.' -ForegroundColor Green
}

Write-Host ("Done. {0} tasks migrated. Backups: {1}" -f $plan.Count, $backupDir) -ForegroundColor Cyan
```

- [ ] **Step 2: Validate the dry-run still works**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1
```

Expected: same dry-run plan as before. No changes made.

- [ ] **Step 3: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/migrate_tasks.ps1
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): migrate_tasks.ps1 apply mode with backup + verify"
```

---

### Task 10: `restore_tasks.ps1`

**Files:**
- Create: `scripts/olympic_platform/restore_tasks.ps1`

- [ ] **Step 1: Write the restore script**

```powershell
<#
.SYNOPSIS
    Restore scheduled tasks from a migration backup directory.
    Use this only to roll back a migration.

.PARAMETER BackupDir
    Required. The timestamped folder under
    C:\Users\quint\.claude\heartbeats\_migration-backups\
#>
param(
    [Parameter(Mandatory = $true)] [string]$BackupDir,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $BackupDir)) {
    throw "Backup directory not found: $BackupDir"
}

$xmls = Get-ChildItem -Path $BackupDir -Filter *.xml
if ($xmls.Count -eq 0) { throw 'No .xml backups in that directory.' }

Write-Host ("Found {0} backed-up task XML files." -f $xmls.Count) -ForegroundColor Cyan
$xmls | ForEach-Object { Write-Host "  $($_.Name)" }

if (-not $Apply) {
    Write-Host 'Dry run only. Re-run with -Apply to restore.' -ForegroundColor Green
    return
}

foreach ($xml in $xmls) {
    $name = [IO.Path]::GetFileNameWithoutExtension($xml.Name)
    $name = $name -replace '_', ' '   # heuristic — review by hand
    Write-Host "Restoring '$name'..." -ForegroundColor Yellow
    schtasks /Create /XML $xml.FullName /TN $name /F
}
Write-Host 'Restore complete.' -ForegroundColor Cyan
```

- [ ] **Step 2: Smoke-test in dry-run mode against the pilot backup from Task 7**

```powershell
$latest = Get-ChildItem C:\Users\quint\.claude\heartbeats\_migration-backups | Sort-Object Name -Descending | Select-Object -First 1
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\restore_tasks.ps1 -BackupDir $latest.FullName
```

Expected: prints the list of XMLs that would be restored, makes no changes.

- [ ] **Step 3: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/restore_tasks.ps1
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): restore_tasks.ps1 rollback companion"
```

---

## Section D — Bulk Migration

### Task 11: Migrate PULSE agent (Phase 2)

**Files:**
- None (Task Scheduler state only)

- [ ] **Step 1: PULSE dry-run**

```powershell
cd C:\Users\quint\workspace-dashboard
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1 -OnlyAgent PULSE
```

Expected: a table showing all PULSE tasks with proposed new paths under `\Olympic Paints\PULSE\`.

Cross-check against memory: PULSE has 7 known scheduled tasks (per `reference_pulse_task_scheduler.md`). If the count is off, investigate before applying.

- [ ] **Step 2: Apply PULSE migration**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1 -OnlyAgent PULSE -Apply
```

Expected: prints `=> ... -> ...   migrated.` for each PULSE task. Final line: `Done. N tasks migrated. Backups: ...`.

- [ ] **Step 3: Verify PULSE tasks fire and write heartbeats**

Wait for the next scheduled trigger (or force one):

```powershell
Get-ScheduledTask -TaskPath "\Olympic Paints\PULSE\" | Select-Object TaskName, State, LastRunTime, LastTaskResult
```

After at least one run of each, check:

```powershell
Get-ChildItem C:\Users\quint\.claude\heartbeats\pulse-*.json | ForEach-Object {
    $hb = Get-Content $_.FullName -Raw | ConvertFrom-Json
    "{0,-30} ok={1} exit={2} duration={3}s" -f $hb.job_id, $hb.ok, $hb.exit_code, $hb.duration_seconds
}
```

Expected: one line per migrated PULSE task, with `ok=True`.

- [ ] **Step 4: 1-week soak gate**

Do NOT proceed to Task 12 until at least one full cycle (≥7 days) has passed with no regressions. Check the Telegram channel for any failure alerts. Review heartbeats:

```powershell
Get-ChildItem C:\Users\quint\.claude\heartbeats\pulse-*.history.jsonl | ForEach-Object {
    $name = $_.BaseName -replace '\.history$',''
    $lines = Get-Content $_.FullName
    $failures = ($lines | ForEach-Object { ($_ | ConvertFrom-Json).ok } | Where-Object { -not $_ }).Count
    "{0,-30} runs={1} failures={2}" -f $name, $lines.Count, $failures
}
```

Investigate any non-zero failures before proceeding.

---

### Task 12: Migrate remaining agents (Phase 3)

**Files:**
- None (Task Scheduler state only)

- [ ] **Step 1: Migrate per agent, in this order**

```powershell
foreach ($agent in 'HAVEN', 'PRISM', 'VAULT', 'STRIKER', 'SIGMA', 'BLAZE', 'FLASH', 'MISC') {
    Write-Host ("---- $agent ----") -ForegroundColor Cyan
    powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1 -OnlyAgent $agent
    $confirm = Read-Host "Apply $agent migration? (yes/skip)"
    if ($confirm -eq 'yes') {
        powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\migrate_tasks.ps1 -OnlyAgent $agent -Apply
    }
}
```

For each agent, review the dry-run plan before typing `yes`. Type `skip` to leave that agent for later.

- [ ] **Step 2: Resolve any MISC-classified tasks manually**

If MISC has any entries, decide for each one:

- Add a rule to `agent_mapping.json` and re-run migration, OR
- Leave at root level (out of scope), OR
- Manually re-register under the right agent folder using the pattern from Task 7.

If you update `agent_mapping.json`:

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/agent_mapping.json
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): classify <task> as <AGENT>"
```

- [ ] **Step 3: Final inventory check**

```powershell
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()
function Walk { param($f,$a) foreach ($t in $f.GetTasks(0)) { $a.Add($t) | Out-Null }; foreach ($s in $f.GetFolders(0)) { Walk $s $a } }
$all = New-Object System.Collections.ArrayList
Walk $svc.GetFolder('\Olympic Paints') $all
$all | ForEach-Object { $_.Path } | Sort-Object
```

Expected: every migrated task listed under `\Olympic Paints\<AGENT>\<name>`. No surprises.

- [ ] **Step 4: Update the README pilot section**

In `scripts/olympic_platform/README.md`, replace the "Pilot" section with:

```markdown
## Migration Status

| Agent   | Migrated date | Task count |
|---------|---------------|------------|
| VAULT   | <date>        | 1 (pilot)  |
| PULSE   | <date>        | <N>        |
| HAVEN   | <date>        | <N>        |
| PRISM   | <date>        | <N>        |
| STRIKER | <date>        | <N>        |
| SIGMA   | <date>        | <N>        |
| BLAZE   | <date>        | <N>        |
| FLASH   | <date>        | <N>        |
| MISC    | <date>        | <N>        |
```

Fill in the actual dates and counts.

- [ ] **Step 5: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/README.md
git -C C:\Users\quint\workspace-dashboard commit -m "docs(olympic-platform): bulk migration complete"
```

---

## Section E — Manifest Builder

### Task 13: `build_schedule_manifest.py` — enumerate tasks via COM

**Files:**
- Create: `scripts/olympic_platform/build_schedule_manifest.py`
- Test:   `scripts/olympic_platform/tests/test_build_schedule_manifest.py`

The COM enumeration is hard to unit-test without Windows. We split the script: a pure-Python `assemble_manifest(tasks, heartbeats_root)` function (testable), and an `enumerate_tasks_from_com()` function called only at runtime.

- [ ] **Step 1: Write the failing manifest-assembly test**

Create `scripts/olympic_platform/tests/test_build_schedule_manifest.py`:

```python
import json
from pathlib import Path

from scripts.olympic_platform import build_schedule_manifest as bsm


def test_assemble_fresh_status(tmp_path):
    # Heartbeat exists and is recent.
    (tmp_path / "demo.json").write_text(json.dumps({
        "job_id": "demo",
        "agent": "PULSE",
        "started_at": "2026-05-16T06:00:00+02:00",
        "finished_at": "2026-05-16T06:00:05+02:00",
        "duration_seconds": 5,
        "exit_code": 0,
        "ok": True,
        "stdout_tail": "ok",
        "stderr_tail": "",
        "summary": {"emails_sent": 4},
    }), encoding="utf-8")
    (tmp_path / "demo.history.jsonl").write_text("", encoding="utf-8")

    tasks = [{
        "job_id": "demo",
        "name": "Demo",
        "agent": "PULSE",
        "task_path": r"\Olympic Paints\PULSE\Demo",
        "enabled": True,
        "schedule_summary": "Weekdays 06:00",
        "next_run": "2026-05-19T06:00:00+02:00",
        "last_run_time": "2026-05-16T06:00:00+02:00",
        "last_task_result": 0,
    }]
    manifest = bsm.assemble_manifest(tasks, heartbeats_root=tmp_path,
                                     now="2026-05-16T07:00:00+02:00")
    assert "generated_at" in manifest
    assert len(manifest["tasks"]) == 1
    t = manifest["tasks"][0]
    assert t["heartbeat_status"] == "fresh"
    assert t["last_run"]["ok"] is True
    assert t["last_run"]["summary"] == {"emails_sent": 4}


def test_assemble_stale_status(tmp_path):
    # Heartbeat is older than next_run; we're 2 hours past the scheduled trigger.
    (tmp_path / "demo.json").write_text(json.dumps({
        "job_id": "demo",
        "agent": "PULSE",
        "started_at": "2026-05-15T06:00:00+02:00",
        "finished_at": "2026-05-15T06:00:05+02:00",
        "duration_seconds": 5,
        "exit_code": 0,
        "ok": True,
        "stdout_tail": "ok",
        "stderr_tail": "",
    }), encoding="utf-8")

    tasks = [{
        "job_id": "demo",
        "name": "Demo",
        "agent": "PULSE",
        "task_path": r"\Olympic Paints\PULSE\Demo",
        "enabled": True,
        "schedule_summary": "Daily 06:00",
        "next_run": "2026-05-17T06:00:00+02:00",
        "last_run_time": "2026-05-16T06:00:00+02:00",   # scheduler thinks it ran...
        "last_task_result": 0,
    }]
    manifest = bsm.assemble_manifest(tasks, heartbeats_root=tmp_path,
                                     now="2026-05-16T08:00:00+02:00")
    assert manifest["tasks"][0]["heartbeat_status"] == "stale"


def test_assemble_missing_status(tmp_path):
    # Task Scheduler claims it ran, but no heartbeat exists at all.
    tasks = [{
        "job_id": "absent",
        "name": "Absent",
        "agent": "VAULT",
        "task_path": r"\Olympic Paints\VAULT\Absent",
        "enabled": True,
        "schedule_summary": "Daily",
        "next_run": "2026-05-17T06:00:00+02:00",
        "last_run_time": "2026-05-16T06:00:00+02:00",
        "last_task_result": 0,
    }]
    manifest = bsm.assemble_manifest(tasks, heartbeats_root=tmp_path,
                                     now="2026-05-16T08:00:00+02:00")
    assert manifest["tasks"][0]["heartbeat_status"] == "missing"


def test_assemble_never_run_status(tmp_path):
    tasks = [{
        "job_id": "new",
        "name": "New",
        "agent": "PRISM",
        "task_path": r"\Olympic Paints\PRISM\New",
        "enabled": True,
        "schedule_summary": "Daily",
        "next_run": "2026-05-17T06:00:00+02:00",
        "last_run_time": None,
        "last_task_result": None,
    }]
    manifest = bsm.assemble_manifest(tasks, heartbeats_root=tmp_path,
                                     now="2026-05-16T08:00:00+02:00")
    assert manifest["tasks"][0]["heartbeat_status"] == "never_run"
```

- [ ] **Step 2: Verify the tests fail**

```powershell
python -m pytest scripts/olympic_platform/tests/test_build_schedule_manifest.py -v
```

Expected: ModuleNotFoundError — module doesn't exist yet.

- [ ] **Step 3: Implement build_schedule_manifest.py**

Create `scripts/olympic_platform/build_schedule_manifest.py`:

```python
"""Builds schedule_manifest.json from Task Scheduler state + heartbeats.

The COM enumeration (Windows-only) is isolated in enumerate_tasks_from_com().
The pure function assemble_manifest() is unit-testable.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_HEARTBEATS = Path(r"C:\Users\quint\.claude\heartbeats")
DEFAULT_OUTPUT = Path(r"C:\Users\quint\workspace-dashboard\data\schedule_manifest.json")
STALE_GRACE_MINUTES = 60


def _parse_iso(value: Optional[str]) -> Optional[_dt.datetime]:
    if not value:
        return None
    try:
        return _dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def _load_heartbeat(job_id: str, root: Path) -> Optional[Dict[str, Any]]:
    path = root / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _load_history(job_id: str, root: Path, limit: int = 10) -> List[Dict[str, Any]]:
    path = root / f"{job_id}.history.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: List[Dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _status(
    *,
    heartbeat: Optional[Dict[str, Any]],
    last_run_time: Optional[str],
    now: _dt.datetime,
) -> str:
    if heartbeat is None and last_run_time is None:
        return "never_run"
    if heartbeat is None and last_run_time is not None:
        return "missing"

    hb_finished = _parse_iso(heartbeat.get("finished_at")) if heartbeat else None
    last_run    = _parse_iso(last_run_time)

    # If Task Scheduler claims a more recent run than the heartbeat,
    # something is wrong — call it stale and require investigation.
    if last_run and hb_finished and last_run > hb_finished + _dt.timedelta(minutes=STALE_GRACE_MINUTES):
        return "stale"
    return "fresh"


def assemble_manifest(
    tasks: Iterable[Dict[str, Any]],
    heartbeats_root: Path,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    now_dt = _parse_iso(now) if now else _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=2)))

    out_tasks: List[Dict[str, Any]] = []
    for t in tasks:
        hb = _load_heartbeat(t["job_id"], Path(heartbeats_root))
        history = _load_history(t["job_id"], Path(heartbeats_root))

        record: Dict[str, Any] = {
            "job_id": t["job_id"],
            "name": t["name"],
            "agent": t["agent"],
            "task_path": t["task_path"],
            "enabled": t["enabled"],
            "schedule_summary": t.get("schedule_summary"),
            "next_run": t.get("next_run"),
            "heartbeat_status": _status(
                heartbeat=hb, last_run_time=t.get("last_run_time"), now=now_dt
            ),
            "history": history,
        }
        if hb is not None:
            record["last_run"] = {
                "started_at": hb.get("started_at"),
                "finished_at": hb.get("finished_at"),
                "duration_seconds": hb.get("duration_seconds"),
                "exit_code": hb.get("exit_code"),
                "ok": hb.get("ok"),
                "summary": hb.get("summary"),
            }
        out_tasks.append(record)

    return {
        "generated_at": now_dt.isoformat(timespec="seconds"),
        "tasks": out_tasks,
    }


def enumerate_tasks_from_com() -> List[Dict[str, Any]]:
    """Windows-only. Reads \\Olympic Paints\\* via Schedule.Service COM."""
    import pythoncom  # noqa
    import win32com.client  # type: ignore

    svc = win32com.client.Dispatch("Schedule.Service")
    svc.Connect()

    def walk(folder, acc):
        for task in folder.GetTasks(0):
            acc.append(task)
        for sub in folder.GetFolders(0):
            walk(sub, acc)

    op = svc.GetFolder(r"\Olympic Paints")
    tasks = []
    walk(op, tasks)

    out: List[Dict[str, Any]] = []
    for task in tasks:
        defn = task.Definition
        # Agent = the last folder segment (e.g. \Olympic Paints\PULSE\Daily Mailer -> PULSE)
        parts = task.Path.strip("\\").split("\\")
        agent = parts[1] if len(parts) >= 3 else "MISC"
        name = parts[-1]

        # First trigger summary
        schedule_summary = None
        if defn.Triggers.Count >= 1:
            trig = defn.Triggers.Item(1)
            schedule_summary = f"type={trig.Type} start={trig.StartBoundary}"

        job_id = _slug(name)

        out.append({
            "job_id": job_id,
            "name": name,
            "agent": agent,
            "task_path": task.Path,
            "enabled": bool(defn.Settings.Enabled),
            "schedule_summary": schedule_summary,
            "next_run": str(task.NextRunTime) if task.NextRunTime else None,
            "last_run_time": str(task.LastRunTime) if task.LastRunTime else None,
            "last_task_result": int(task.LastTaskResult),
        })
    return out


def _slug(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed"


def main() -> int:
    tasks = enumerate_tasks_from_com()
    manifest = assemble_manifest(tasks, heartbeats_root=DEFAULT_HEARTBEATS)
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest['tasks'])} tasks to {DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

- [ ] **Step 4: Verify all assemble tests pass**

```powershell
python -m pytest scripts/olympic_platform/tests/test_build_schedule_manifest.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Smoke-test against real Task Scheduler**

```powershell
cd C:\Users\quint\workspace-dashboard
python -m scripts.olympic_platform.build_schedule_manifest
Get-Content data\schedule_manifest.json | Select-Object -First 60
```

Expected: prints `Wrote N tasks to ...`. The JSON file contains every migrated task with `heartbeat_status` set.

If you see `ModuleNotFoundError: No module named 'win32com'`:

```powershell
pip install pywin32
```

- [ ] **Step 6: Commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/build_schedule_manifest.py scripts/olympic_platform/tests/test_build_schedule_manifest.py
git -C C:\Users\quint\workspace-dashboard commit -m "feat(olympic-platform): schedule_manifest.json builder with status logic"
```

---

### Task 14: Schedule the manifest builder (Phase 4)

**Files:**
- None (Task Scheduler state only)

- [ ] **Step 1: Register the manifest builder as an hourly task**

```powershell
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()
try { $svc.GetFolder('\').CreateFolder('Olympic Paints') | Out-Null } catch {}
try { $svc.GetFolder('\Olympic Paints').CreateFolder('PRISM') | Out-Null } catch {}
$folder = $svc.GetFolder('\Olympic Paints\PRISM')

$wrapper = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py'
$target  = 'C:\Users\quint\workspace-dashboard\scripts\olympic_platform\build_schedule_manifest.py'

$def = $svc.NewTask(0)
$def.RegistrationInfo.Description = 'Builds schedule_manifest.json from Task Scheduler state + heartbeats.'

$trig = $def.Triggers.Create(8)                # TASK_TRIGGER_DAILY
$trig.StartBoundary = (Get-Date).Date.AddHours(6).ToString('yyyy-MM-ddTHH:mm:ss')
$trig.Repetition.Interval = 'PT1H'             # hourly
$trig.Repetition.Duration = 'P1D'              # for 24h
$trig.Enabled = $true

$act = $def.Actions.Create(0)
$act.Path = 'python'
$act.Arguments = "`"$wrapper`" build-schedule-manifest --agent PRISM -- `"$target`""
$act.WorkingDirectory = 'C:\Users\quint\workspace-dashboard'

$folder.RegisterTaskDefinition('Build Schedule Manifest', $def, 6, $null, $null, 3) | Out-Null
'Registered: \Olympic Paints\PRISM\Build Schedule Manifest'
```

- [ ] **Step 2: Force a run and verify**

```powershell
Start-ScheduledTask -TaskPath '\Olympic Paints\PRISM\' -TaskName 'Build Schedule Manifest'
Start-Sleep 20
Get-Content C:\Users\quint\.claude\heartbeats\build-schedule-manifest.json
Get-Content C:\Users\quint\workspace-dashboard\data\schedule_manifest.json | Select-Object -First 30
```

Expected: heartbeat with `ok: true`; manifest JSON listing every task under `\Olympic Paints\`.

---

## Section F — Final Verification

### Task 15: End-to-end verification

**Files:**
- Modify: `scripts/olympic_platform/README.md`

- [ ] **Step 1: Inventory check**

```powershell
$svc = New-Object -ComObject Schedule.Service; $svc.Connect()
function W { param($f,$a) foreach ($t in $f.GetTasks(0)) { $a.Add($t)|Out-Null }; foreach ($s in $f.GetFolders(0)) { W $s $a } }
$all = New-Object System.Collections.ArrayList
W $svc.GetFolder('\Olympic Paints') $all
"Total tasks under \Olympic Paints\: $($all.Count)"
$all | Group-Object { ($_.Path -split '\\')[2] } | Sort-Object Name | ForEach-Object {
    "  {0,-10} {1}" -f $_.Name, $_.Count
}
```

Confirm: every expected agent has the expected number of tasks (cross-reference your migration status table from Task 12 Step 4).

- [ ] **Step 2: Heartbeat coverage check**

```powershell
$svc = New-Object -ComObject Schedule.Service; $svc.Connect()
function W { param($f,$a) foreach ($t in $f.GetTasks(0)) { $a.Add($t)|Out-Null }; foreach ($s in $f.GetFolders(0)) { W $s $a } }
$all = New-Object System.Collections.ArrayList
W $svc.GetFolder('\Olympic Paints') $all

$missing = @()
foreach ($t in $all) {
    $name = ($t.Path -split '\\')[-1]
    $slug = ($name.ToLower() -replace '[^a-z0-9]+','-').Trim('-')
    $hb = "C:\Users\quint\.claude\heartbeats\$slug.json"
    if (-not (Test-Path $hb)) { $missing += $t.Path }
}
if ($missing.Count -eq 0) {
    'All tasks have heartbeats.'
} else {
    "Tasks without heartbeat (have they run yet?):"
    $missing
}
```

Any task without a heartbeat either hasn't fired yet or has a slug mismatch. Investigate before declaring done.

- [ ] **Step 3: Forced-failure end-to-end**

Pick the least disruptive task (the manifest builder is a safe candidate) and force a failure to verify the alert pipeline.

```powershell
# Temporarily rename build_schedule_manifest.py so the wrapper finds nothing to run.
Rename-Item scripts\olympic_platform\build_schedule_manifest.py build_schedule_manifest.py.bak
Start-ScheduledTask -TaskPath '\Olympic Paints\PRISM\' -TaskName 'Build Schedule Manifest'
Start-Sleep 15
# Check heartbeat
Get-Content C:\Users\quint\.claude\heartbeats\build-schedule-manifest.json
# Restore
Rename-Item scripts\olympic_platform\build_schedule_manifest.py.bak build_schedule_manifest.py
```

Expected: heartbeat shows `ok: false`, a non-zero `exit_code`, and a Telegram message arrives on chat `8042233389`.

- [ ] **Step 4: Update README with verification record**

In `scripts/olympic_platform/README.md`, append:

```markdown
## Verification (sub-project #1 complete)

| Check                              | Date | Result |
|------------------------------------|------|--------|
| Pilot 3-day soak                   | <d>  | pass   |
| PULSE 1-week soak                  | <d>  | pass   |
| All agents migrated                | <d>  | <N> tasks |
| Manifest builder hourly            | <d>  | pass   |
| Forced-failure Telegram alert      | <d>  | pass   |
```

- [ ] **Step 5: Final commit**

```powershell
git -C C:\Users\quint\workspace-dashboard add scripts/olympic_platform/README.md
git -C C:\Users\quint\workspace-dashboard commit -m "docs(olympic-platform): sub-project #1 verification complete"
```

- [ ] **Step 6: Hand-off note**

At this point sub-project #1 is complete. Sub-project #2 (Agent Registry) will consume:

- `C:\Users\quint\workspace-dashboard\data\schedule_manifest.json` (this sub-project's output)
- The agent-folder hierarchy under `\Olympic Paints\` (also this sub-project's output)

It will produce `agents_manifest.json` and an updated `agent_mapping.json` shared with this sub-project.

Sub-project #3 (Control Tower UI) will render both manifests into a single page.

---

## Appendix — Common operations

**Force a heartbeat refresh manually:**

```powershell
Start-ScheduledTask -TaskPath '\Olympic Paints\PRISM\' -TaskName 'Build Schedule Manifest'
```

**See the last 5 runs of a job:**

```powershell
Get-Content C:\Users\quint\.claude\heartbeats\<job-id>.history.jsonl | Select-Object -Last 5
```

**Disable a task without deleting it:**

```powershell
Disable-ScheduledTask -TaskPath '\Olympic Paints\<AGENT>\' -TaskName '<Name>'
```

**Roll back a migration batch:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\olympic_platform\restore_tasks.ps1 -BackupDir <path> -Apply
```
