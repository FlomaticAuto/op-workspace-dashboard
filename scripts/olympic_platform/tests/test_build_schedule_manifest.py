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
    # Heartbeat is older than Task Scheduler's LastRunTime by more than the grace window.
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
        "last_run_time": "2026-05-16T06:00:00+02:00",
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


def test_coerce_scheduler_time_replaces_bogus_utc():
    # pywin32 emits '+00:00' even though the underlying value is local SAST.
    assert bsm._coerce_scheduler_time("2026-05-16 13:13:53+00:00") == "2026-05-16 13:13:53+02:00"


def test_coerce_scheduler_time_drops_sentinels():
    assert bsm._coerce_scheduler_time("1899-12-30 00:00:00+00:00") is None
    assert bsm._coerce_scheduler_time("1999-11-30 00:00:00+00:00") is None
    assert bsm._coerce_scheduler_time(None) is None


def test_assemble_fresh_when_scheduler_time_now_matches_heartbeat(tmp_path):
    # Regression: before the TZ fix, scheduler '+00:00' on local time made
    # heartbeats look 2 hours stale.
    (tmp_path / "demo.json").write_text(json.dumps({
        "job_id": "demo",
        "agent": "VAULT",
        "started_at": "2026-05-16T13:13:54+02:00",
        "finished_at": "2026-05-16T13:14:02+02:00",
        "duration_seconds": 8,
        "exit_code": 0,
        "ok": True,
        "stdout_tail": "",
        "stderr_tail": "",
    }), encoding="utf-8")

    tasks = [{
        "job_id": "demo",
        "name": "Demo",
        "agent": "VAULT",
        "task_path": r"\Olympic Paints\VAULT\Demo",
        "enabled": True,
        "schedule_summary": "Daily",
        "next_run": "2026-05-16T16:15:00+02:00",
        # AFTER _coerce_scheduler_time has been applied — same TZ as heartbeat.
        "last_run_time": "2026-05-16 13:13:53+02:00",
        "last_task_result": 0,
    }]
    manifest = bsm.assemble_manifest(tasks, heartbeats_root=tmp_path,
                                     now="2026-05-16T13:30:00+02:00")
    assert manifest["tasks"][0]["heartbeat_status"] == "fresh"
