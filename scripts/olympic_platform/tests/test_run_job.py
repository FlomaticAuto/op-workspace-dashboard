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
    assert not (summary_dir / "rich.json").exists()


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


def test_unlaunchable_command_writes_failure_heartbeat(tmp_path):
    # Missing/typoed executable in a Task Scheduler action must still produce
    # a heartbeat — otherwise the control tower can't see the failure.
    result = _invoke(
        "missing-exe", "PULSE",
        ["totally-nonexistent-command-xyz-12345"],
        tmp_path,
    )
    assert result.returncode == 127

    hb = json.loads((tmp_path / "heartbeats" / "missing-exe.json").read_text(encoding="utf-8"))
    assert hb["ok"] is False
    assert hb["exit_code"] == 127
    assert "failed to launch" in hb["stderr_tail"]
