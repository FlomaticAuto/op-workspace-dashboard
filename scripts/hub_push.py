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

HUB_DIR = next(p for p in [Path(r"C:\Users\Administrator\workspace-dashboard"), Path(r"C:\Users\quint\workspace-dashboard")] if p.exists())


def _scrub(text: str) -> str:
    """Redact any 'AUTHORIZATION: basic <base64>' header that may have leaked in."""
    import re
    return re.sub(
        r"(AUTHORIZATION:\s*basic\s+)[A-Za-z0-9+/=]+",
        r"\1<redacted>",
        text,
        flags=re.IGNORECASE,
    )


def push_to_hub(subfolder: str, message: str | None = None) -> bool:
    """Stage subfolder changes in the hub repo and push to origin/master."""
    if message is None:
        message = f"{subfolder} update — {datetime.now():%Y-%m-%d %H:%M}"

    def run(cmd):
        r = subprocess.run(cmd, cwd=str(HUB_DIR), capture_output=True, text=True)
        if r.returncode != 0:
            # Mask the Authorization header in BOTH the echoed cmd and stderr —
            # otherwise the FlomaticAuto PAT (passed via -c http.extraheader=...)
            # gets printed plaintext, lands in run_job.py's stderr_tail, and ships
            # to Telegram on the failure alert.
            print(f"  ! {_scrub(' '.join(cmd))}: {_scrub(r.stderr.strip())}")
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

    # Remove stale index lock if left over from a prior crash
    lock_file = HUB_DIR / ".git" / "index.lock"
    if lock_file.exists():
        lock_file.unlink()
        print("  ! Removed stale .git/index.lock")

    # Ensure we're on master — if the repo drifted to main (e.g. after a manual
    # checkout), git push origin master would push the wrong content.
    run(["git", "checkout", "master"])

    # Stash any unstaged changes so pull --rebase doesn't fail, then restore them
    stashed = run(["git", "stash", "--include-untracked"])

    # Pull before push to avoid conflicts
    if token:
        auth_header = "basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        run(["git", "-c", f"http.extraheader=AUTHORIZATION: {auth_header}", "pull", "--rebase", "origin", "master"])
    else:
        run(["git", "pull", "--rebase", "origin", "master"])

    if stashed:
        run(["git", "stash", "pop"])

    run(["git", "add", subfolder])
    run(["git", "commit", "-m", message])

    if token:
        auth_header = "basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
        # master:main uses --force because the scheduled-tasks agent pushes to main
        # independently; master is the authoritative branch, main must always mirror it
        ok = run(["git", "-c", f"http.extraheader=AUTHORIZATION: {auth_header}",
                  "push", "origin", "master", "+master:main"])
    else:
        ok = run(["git", "push", "origin", "master", "+master:main"])

    if ok:
        # ASCII-safe print — cp1252 console can't handle ✓ / →
        msg = f"  OK Pushed {subfolder}/ to hub (master + main) -> Vercel will auto-deploy"
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", "replace").decode())
    return ok
