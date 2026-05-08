"""Smoke tests for portal_trigger_server. Requires `pip install flask requests`.
Run while the server is NOT running; the test starts it itself in a thread."""
import threading
import time
import requests
import pytest

@pytest.fixture(scope="module")
def server():
    from portal_trigger_server import app
    t = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8765, debug=False, use_reloader=False), daemon=True)
    t.start()
    time.sleep(1)
    yield "http://127.0.0.1:8765"

def test_health(server):
    r = requests.get(f"{server}/health", timeout=2)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "merchandising" in j["builds"]
