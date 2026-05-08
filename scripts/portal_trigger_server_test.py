"""Smoke tests for portal_trigger_server. Requires `pip install flask flask-cors requests`.

The fixture starts the server in a daemon thread on a free port, so tests are
isolated from any production instance running on the default 8765 (e.g. the
Windows scheduled task `OlympicPortalTriggerServer`)."""
import socket
import threading
import time

import pytest
import requests


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    from portal_trigger_server import app
    port = _free_port()
    t = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port,
                                debug=False, use_reloader=False),
        daemon=True,
    )
    t.start()
    time.sleep(1)
    yield f"http://127.0.0.1:{port}"


def test_health(server):
    r = requests.get(f"{server}/health", timeout=2)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "merchandising" in j["builds"]


def test_trigger_unknown_build(server):
    r = requests.post(f"{server}/trigger/nonexistent", timeout=2)
    assert r.status_code == 404


def test_trigger_starts_job_and_status_reflects_state(server):
    from portal_trigger_server import BUILDS
    BUILDS["test_echo"] = {"label": "test",
                            "cmd": ["python", "-c", "print('hello')"]}
    r = requests.post(f"{server}/trigger/test_echo", timeout=2)
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    for _ in range(25):
        s = requests.get(f"{server}/status/{job_id}", timeout=2).json()
        if s["state"] in ("success", "error"):
            break
        time.sleep(0.2)
    assert s["state"] == "success", f"Expected success, got {s}"
    assert any("hello" in line for line in s["log_tail"])


def test_status_unknown_job(server):
    r = requests.get(f"{server}/status/notarealjob", timeout=2)
    assert r.status_code == 404
