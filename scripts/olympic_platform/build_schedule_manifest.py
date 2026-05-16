"""Builds schedule_manifest.json from Task Scheduler state + heartbeats.

The COM enumeration (Windows-only) is isolated in enumerate_tasks_from_com().
The pure function assemble_manifest() is unit-testable.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
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
            # Task Scheduler's own record of the last run — useful for "missing"
            # tasks where no heartbeat exists, so the UI can still show "TS last
            # attempted this at X, but nothing wrote a heartbeat."
            "scheduler_last_run_time": t.get("last_run_time"),
            "scheduler_last_task_result": t.get("last_task_result"),
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


_NEVER_RUN_RESULT = 0x00041303  # 267011 — SCHED_S_TASK_HAS_NOT_RUN
_LOCAL_TZ_SUFFIX = "+02:00"     # SAST; this machine is fixed at UTC+2 (no DST)


def _coerce_scheduler_time(value: Any) -> Optional[str]:
    """pywin32 str()'s Task Scheduler datetimes with a bogus '+00:00' suffix
    even though the numeric value is the machine's LOCAL time. Replace with
    the real local offset. Drop sentinel 'never run' times (1899-12-30,
    1999-11-30) so callers don't compare against meaningless 100-year-old
    timestamps.
    """
    if value is None:
        return None
    s = str(value)
    if s.startswith(("1899", "1999")):
        return None
    if s.endswith("+00:00"):
        s = s[:-6] + _LOCAL_TZ_SUFFIX
    return s


def enumerate_tasks_from_com() -> List[Dict[str, Any]]:
    """Windows-only. Reads \\Olympic Paints\\* via Schedule.Service COM."""
    import pythoncom  # noqa: F401
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

        last_result = int(task.LastTaskResult)
        last_run_time = _coerce_scheduler_time(task.LastRunTime)
        # SCHED_S_TASK_HAS_NOT_RUN: scheduler has a sentinel timestamp; ignore it.
        if last_result == _NEVER_RUN_RESULT:
            last_run_time = None

        out.append({
            "job_id": job_id,
            "name": name,
            "agent": agent,
            "task_path": task.Path,
            "enabled": bool(defn.Settings.Enabled),
            "schedule_summary": schedule_summary,
            "next_run": _coerce_scheduler_time(task.NextRunTime),
            "last_run_time": last_run_time,
            "last_task_result": last_result,
        })
    return out


def _slug(name: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "unnamed"


def main() -> int:
    hb_root = Path(os.environ.get("OLYMPIC_HEARTBEAT_ROOT", str(DEFAULT_HEARTBEATS)))
    tasks = enumerate_tasks_from_com()
    manifest = assemble_manifest(tasks, heartbeats_root=hb_root)
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest['tasks'])} tasks to {DEFAULT_OUTPUT}")

    # Push the manifest to the hub so Vercel/GitHub Pages serve fresh data.
    # Best-effort: if hub_push isn't importable or fails, the local write still
    # succeeded — we just don't propagate this run.
    try:
        from scripts.hub_push import push_to_hub
        push_to_hub(
            subfolder="data",
            message=f"Schedule manifest — {manifest['generated_at']}",
        )
    except Exception as e:
        print(f"  ! hub push skipped: {e}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
