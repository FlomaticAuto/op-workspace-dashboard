"""
hub_push.py — shared git-push helper for all Olympic Paints dashboard scripts.

Usage in any build script:
    from scripts.hub_push import push_to_hub
    push_to_hub(subfolder="store-health", message="Store Health — 2026-05-15")

The hub repo is op-workspace-dashboard at C:\\Users\\quint\\workspace-dashboard.
Vercel production branch is 'main'; we push master:master and master:main in a
single call so both branches always stay in sync and Vercel always gets the latest.
"""

import subprocess
from datetime import datetime
from pathlib import Path

HUB_DIR = Path(r"C:\Users\quint\workspace-dashboard")


def push_to_hub(subfolder: str, message: str | None = None) -> bool:
    """Stage subfolder changes in the hub repo and push to origin/master."""
    if message is None:
        message = f"{subfolder} update — {datetime.now():%Y-%m-%d %H:%M}"

    def run(cmd):
        r = subprocess.run(cmd, cwd=str(HUB_DIR), capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ! {' '.join(cmd)}: {r.stderr.strip()}")
        return r.returncode == 0

    import os, base64
    token = None
    try:
        result = subprocess.run(
            ["gh", "auth", "token", "--user", "FlomaticAuto"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            token = result.stdout.strip()
    except FileNotFoundError:
        pass

    run(["git", "config", "user.email", "auto@olympic-paints.local"])
    run(["git", "config", "user.name", "Olympic Paints Hub Bot"])

    # Pull before push to avoid conflicts
    if token:
        auth_header = "basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        run(["git", "-c", f"http.extraheader=AUTHORIZATION: {auth_header}", "pull", "--rebase", "origin", "master"])
    else:
        run(["git", "pull", "--rebase", "origin", "master"])

    run(["git", "add", subfolder])
    run(["git", "commit", "-m", message])

    if token:
        auth_header = "basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        ok = run(["git", "-c", f"http.extraheader=AUTHORIZATION: {auth_header}",
                  "push", "origin", "master", "master:main"])
    else:
        ok = run(["git", "push", "origin", "master", "master:main"])

    if ok:
        print(f"  ✓ Pushed {subfolder}/ to hub (master + main) → Vercel will auto-deploy")
    return ok
