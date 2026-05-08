"""
portal_trigger_server.py
Local Flask trigger server for the Olympic Paints workspace portal.
Runs on 127.0.0.1:8765. Exposes /health, /trigger/<key>, /status/<job_id>.
Auto-started at Windows login via Task Scheduler (see install_trigger_task.ps1).
"""
import subprocess
import threading
import uuid
from datetime import datetime
from collections import deque

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Permissive CORS so portal.html (loaded via file://) can fetch this loopback API.
CORS(app)

# Build registry — extend by adding entries here
BUILDS = {
    "merchandising": {
        "label": "Merchandising Impact Report",
        "cmd": [
            "python",
            r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\build_merchandising_impact.py",
        ],
    },
}

# In-memory job state. Restart loses history.
JOBS = {}  # job_id → {state, started_at, finished_at, log_tail (deque), build_key}


@app.route("/health")
def health():
    return jsonify(ok=True, builds=list(BUILDS.keys()))


@app.route("/trigger/<build_key>", methods=["POST"])
def trigger(build_key):
    if build_key not in BUILDS:
        return jsonify(error=f"unknown build: {build_key}"), 404
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "state": "running",
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "log_tail": deque(maxlen=20),
        "build_key": build_key,
    }
    threading.Thread(target=_run_job, args=(job_id, build_key), daemon=True).start()
    return jsonify(job_id=job_id), 202


@app.route("/status/<job_id>")
def status(job_id):
    j = JOBS.get(job_id)
    if not j:
        return jsonify(error="unknown job"), 404
    return jsonify(
        state=j["state"],
        started_at=j["started_at"],
        finished_at=j["finished_at"],
        log_tail=list(j["log_tail"]),
        build_key=j["build_key"],
    )


def _run_job(job_id, build_key):
    cmd = BUILDS[build_key]["cmd"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            JOBS[job_id]["log_tail"].append(line.rstrip())
        proc.wait()
        JOBS[job_id]["state"] = "success" if proc.returncode == 0 else "error"
    except Exception as exc:
        JOBS[job_id]["log_tail"].append(f"EXCEPTION: {exc}")
        JOBS[job_id]["state"] = "error"
    finally:
        JOBS[job_id]["finished_at"] = datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
