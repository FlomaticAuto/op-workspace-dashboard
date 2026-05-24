#!/usr/bin/env python3
"""
Kaizen Implement Poller — Olympic Paints

Queries the Notion Tasks DB for tasks at `Kaizen Status = Impliment` (sic —
the option in Notion is misspelled; the poller MUST match it verbatim) that
are still in the Kaizen Action State and not yet archived. If any are found,
invokes the existing /kaizen-implement skill via the local `claude` CLI to
apply the changes end-to-end (agent memory edits, hub-file sync, Notion
archive, Telegram summary). Logs counts; sends a separate Telegram if there
was nothing to action so the run is still visible.

Designed to run twice weekly (Wed + Sun 12:00) via Task Scheduler.

Run:
    python kaizen_implement_poller.py            # full run
    python kaizen_implement_poller.py --dry-run  # query Notion only; no Claude invocation, no edits
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(os.environ["USERPROFILE"]) / "OneDrive" / "1.Projects" / "1.Olympic Paints"
ENV_FILE     = PROJECT_ROOT / ".env"
LOG_DIR      = Path(__file__).resolve().parent.parent  # workspace-dashboard root
LOG_FILE     = LOG_DIR / "kaizen_implement_log.json"

# Notion Tasks DB — the database ID for the "TASK DATABASE" inline database
# from the Tasks page (https://www.notion.so/Tasks-248ff48d2bb18004b830eb997a3f6ff4).
# The Notion REST API queries databases, not data sources, so use this ID
# (NOT the data-source ID 247ff48d… which is for the SDK schema lookup).
NOTION_DATABASE_ID = "248ff48d-2bb1-8051-ad51-de704b9a6871"

# Two Action-State pages count as "in Kaizen" (from the Kaizen board view's filter).
KAIZEN_ACTION_STATE_IDS = [
    "363ff48d-2bb1-8179-8422-dbbbaf591c86",
    "363ff48d-2bb1-80c4-94df-da801fc56c4e",
]

# Verbatim spelling from Notion. DO NOT "fix" this — the option is literally
# named "Impliment" in the user's database. Changing it here would silently
# match zero tasks.
KAIZEN_STATUS_IMPLEMENT = "Impliment"

# Telegram — same chat as the rest of the Kaizen pipeline.
TELEGRAM_BOT_TOKEN = "8606179788:AAHZB7-WV44YCi3GqvnuCvEdyywQ_ommukg"
TELEGRAM_CHAT_ID   = "8042233389"

# Hard cap on how long /kaizen-implement is allowed to run end-to-end.
CLAUDE_MAX_SECONDS = 600  # 10 min — generous; the skill touches multiple files


# ── Env loader ────────────────────────────────────────────────────────
def load_env(path: Path) -> dict:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ── Notion API ────────────────────────────────────────────────────────
def notion_query_implement_tasks(token: str) -> list[dict]:
    """
    Query the Tasks DB for tasks at Kaizen Status=Impliment, in the Kaizen
    Action State, and not Archived. Returns the raw `results` array from the
    Notion API (each item is a Notion page object with `id`, `properties`, …).
    """
    # Notion's 2025-09-03 API uses /v1/data_sources/{id}/query for multi-source
    # databases. Fall back to /v1/databases/{id}/query for older accounts.
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Kaizen Status",
                    "select": {"equals": KAIZEN_STATUS_IMPLEMENT},
                },
                {
                    "property": "Archive",
                    "checkbox": {"does_not_equal": True},
                },
                {
                    "or": [
                        {
                            "property": "Action State",
                            "relation": {"contains": rid},
                        }
                        for rid in KAIZEN_ACTION_STATE_IDS
                    ],
                },
            ]
        },
        "page_size": 50,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    body = json.dumps(payload).encode("utf-8")
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data.get("results", [])
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"Notion API {e.code}: {err_body}") from e


def task_title(page: dict) -> str:
    props = page.get("properties", {})
    title_prop = props.get("Name", {}).get("title", [])
    return "".join(t.get("plain_text", "") for t in title_prop) or "(untitled)"


# ── Telegram ──────────────────────────────────────────────────────────
def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
            return r.status == 200
    except Exception as e:
        print(f"  Telegram error: {e}", file=sys.stderr)
        return False


# ── Claude CLI (slash-command-enabled) ────────────────────────────────
def invoke_kaizen_implement_skill() -> tuple[bool, str]:
    """
    Run `claude -p /kaizen-implement` so the existing skill does the actual
    implementation work. Unlike claude_cli_helper.py, slash commands are NOT
    disabled here — that's the whole point of this poller.

    Returns (ok, stdout_or_error).
    """
    cmd = [
        "claude",
        "-p", "/kaizen-implement",
        "--output-format", "text",
        # Permission mode left default so writes to memory/hub files prompt
        # only if the host setup hasn't pre-allowed them. On the Task
        # Scheduler box, settings.local.json should allow Edit/Bash for
        # the kaizen-implement skill's targets.
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=CLAUDE_MAX_SECONDS,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"claude CLI timed out after {CLAUDE_MAX_SECONDS}s"
    except FileNotFoundError:
        return False, "`claude` CLI not found on PATH"

    if proc.returncode != 0:
        return False, f"claude exited {proc.returncode}: {proc.stderr.strip()[:500]}"

    return True, (proc.stdout or "").strip()


# ── Log ───────────────────────────────────────────────────────────────
def append_log(entry: dict) -> None:
    log: list[dict] = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            if not isinstance(log, list):
                log = []
        except json.JSONDecodeError:
            log = []
    log.append(entry)
    # Keep the last 200 runs only — file stays small.
    log = log[-200:]
    LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Notion Kaizen Implement poller")
    ap.add_argument("--dry-run", action="store_true",
                    help="Query Notion + print results; do NOT invoke Claude.")
    args = ap.parse_args()

    env = load_env(ENV_FILE)
    token = env.get("NOTION_API_TOKEN") or os.environ.get("NOTION_API_TOKEN")
    if not token:
        print(f"ERROR: NOTION_API_TOKEN missing from {ENV_FILE} and environment", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    print(f"Kaizen Implement poller — {now.isoformat()}")
    print(f"  dry_run={args.dry_run}")

    try:
        tasks = notion_query_implement_tasks(token)
    except Exception as e:
        msg = f"Notion query failed: {e}"
        print(f"  {msg}", file=sys.stderr)
        send_telegram(f"❌ <b>Kaizen Implement poller</b>\n{msg}")
        append_log({"ts": now.isoformat(), "ok": False, "error": str(e),
                    "matched": 0, "dry_run": args.dry_run})
        return 1

    titles = [task_title(t) for t in tasks]
    matched = len(tasks)
    print(f"  Matched {matched} task(s) at Kaizen Status='{KAIZEN_STATUS_IMPLEMENT}'")
    for t in titles:
        print(f"    - {t}")

    if matched == 0:
        send_telegram(
            "🔧 <b>Kaizen Implement — nothing to action</b>\n"
            f"<i>{now.strftime('%a %d %b %H:%M UTC')}</i> · "
            f"No Notion tasks at <code>Kaizen Status = {KAIZEN_STATUS_IMPLEMENT}</code>."
        )
        append_log({"ts": now.isoformat(), "ok": True, "matched": 0,
                    "tasks": [], "dry_run": args.dry_run, "invoked": False})
        return 0

    if args.dry_run:
        send_telegram(
            f"🧪 <b>Kaizen Implement — dry run</b>\n"
            f"Would action <b>{matched}</b> task(s):\n"
            + "\n".join(f"• {t}" for t in titles[:10])
        )
        append_log({"ts": now.isoformat(), "ok": True, "matched": matched,
                    "tasks": titles, "dry_run": True, "invoked": False})
        return 0

    print("  Invoking /kaizen-implement via `claude` CLI…")
    ok, output = invoke_kaizen_implement_skill()
    print(f"  invocation ok={ok}; output length={len(output)} chars")

    summary = (
        f"{'✅' if ok else '❌'} <b>Kaizen Implement — auto-run</b>\n"
        f"<i>{now.strftime('%a %d %b %H:%M UTC')}</i>\n"
        f"Tasks matched: <b>{matched}</b>\n"
        f"Tasks listed:\n" + "\n".join(f"• {t}" for t in titles[:10])
    )
    if not ok:
        summary += f"\n\n<b>Error:</b> <code>{output[:300]}</code>"
    send_telegram(summary)

    append_log({
        "ts": now.isoformat(), "ok": ok, "matched": matched,
        "tasks": titles, "dry_run": False, "invoked": True,
        "output_tail": output[-1500:],
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
