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


def test_append_history_keeps_last_100(tmp_path):
    job_id = "rotate-test"
    for i in range(100):
        heartbeat.append_history(
            {"job_id": job_id, "n": i}, root=tmp_path
        )
    heartbeat.append_history({"job_id": job_id, "n": 100}, root=tmp_path)

    lines = (tmp_path / f"{job_id}.history.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 100
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["n"] == 1
    assert parsed[-1]["n"] == 100


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
    assert not (summary_dir / "broken.json").exists()
