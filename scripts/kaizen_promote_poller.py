#!/usr/bin/env python3
"""
Kaizen Promote Poller — Olympic Paints

The missing automation in the Kaizen pipeline. Reads each agent's
"## Accumulated Learnings" section from the local Claude Code memory dir,
and for every entry that has a real SUGGESTION and is NOT already marked
[TRIAGED], creates a Notion task in the Tasks DB at:

    Action State  = Kaizen (relation)
    Kaizen Status = Review (select)
    Area          = Olympic (select)
    Name (title)  = "[Agent Improvement] <AGENT>: <suggestion>"
    Description   = full TASK / FRICTION / SUGGESTION block + hub-file pointer

After a successful Notion create, marks the memory entry [TRIAGED] in
place so the next run does not duplicate it. Sends a Telegram summary.

Designed to run weekly (Mondays 08:30) on the box where the local Claude
Code memory dir actually has the agent_*.md profile files (i.e. quint's
box). On any other host it gracefully no-ops with a "no memory files
found" message rather than guessing or failing loudly.

Run:
    python kaizen_promote_poller.py            # full run
    python kaizen_promote_poller.py --dry-run  # parse memory + show what would be created; no Notion writes
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(os.environ["USERPROFILE"]) / "OneDrive" / "1.Projects" / "1.Olympic Paints"
ENV_FILE     = PROJECT_ROOT / ".env"
LOG_DIR      = Path(__file__).resolve().parent.parent  # workspace-dashboard root
LOG_FILE     = LOG_DIR / "kaizen_promote_log.json"

# Notion Tasks DB — same multi-source data source as the implement poller.
NOTION_DATA_SOURCE_ID = "247ff48d-2bb1-8098-bcd4-000b93931ee2"
NOTION_API_VERSION    = "2025-09-03"

# The "Kaizen" Action State page (relation target).
KAIZEN_ACTION_STATE_PAGE_ID = "363ff48d-2bb1-8179-8422-dbbbaf591c86"

# Verbatim option names from Notion. Do NOT correct — the data is canonical.
KAIZEN_STATUS_REVIEW = "Review"
AREA_OLYMPIC          = "Olympic"

# Telegram
TELEGRAM_BOT_TOKEN = "8606179788:AAHZB7-WV44YCi3GqvnuCvEdyywQ_ommukg"
TELEGRAM_CHAT_ID   = "8042233389"

# Per-agent hub file path (kept in OneDrive so it's portable across boxes).
HUB_DIR = PROJECT_ROOT / "olympic-paints-hub" / "agents"
HUB_FILES = {
    "HAVEN":   HUB_DIR / "haven.md",
    "PRISM":   HUB_DIR / "prism.md",
    "STRIKER": HUB_DIR / "striker.md",
    "SIGMA":   HUB_DIR / "sigma.md",
    "BLAZE":   HUB_DIR / "blaze.md",
    "VAULT":   HUB_DIR / "vault.md",
    # FLASH / PULSE have no hub file — Kaizen tasks for them still get created.
}

AGENT_FILES = {
    "HAVEN":   "agent_haven.md",
    "PRISM":   "agent_prism.md",
    "STRIKER": "agent_striker.md",
    "SIGMA":   "agent_sigma.md",
    "BLAZE":   "agent_blaze.md",
    "VAULT":   "agent_vault.md",
}


# ── Helpers ───────────────────────────────────────────────────────────
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


def resolve_memory_dir() -> Path | None:
    """
    Same per-machine resolution as generate_kaizen_status.py. Returns the
    memory dir that actually has agent_*.md files, or None on this host.
    """
    home = Path.home()
    candidates = sorted(
        (home / ".claude" / "projects").glob("[Cc]--Users-*-OneDrive-*Olympic-Paints")
    )
    with_data = [c / "memory" for c in candidates
                 if (c / "memory").is_dir() and any((c / "memory").glob("agent_*.md"))]
    if with_data:
        return with_data[0]
    # No memory files locally — no work to do.
    return None


# Parses each entry block out of "## Accumulated Learnings". Each entry is
# three lines: [YYYY-MM-DD] TASK: ... / FRICTION: ... / SUGGESTION: ...
ENTRY_RE = re.compile(
    r"\[(?P<date>\d{4}-\d{2}-\d{2})\]\s+TASK:\s+(?P<task>.+?)\n"
    r"\s+FRICTION:\s+(?P<friction>.+?)\n"
    r"\s+SUGGESTION:\s+(?P<suggestion>.+?)(?=\n\[|\n<!--|\Z)",
    re.DOTALL,
)


def parse_pending_entries(filepath: Path) -> list[dict]:
    """
    Return the entries from `## Accumulated Learnings` that:
      - Do NOT end with [TRIAGED]
      - Have a SUGGESTION value that is not 'none' (case-insensitive) and not empty
    Each item dict carries .date / .task / .friction / .suggestion / .raw_block
    so the caller can re-locate it in the file to mark it triaged.
    """
    if not filepath.exists():
        return []
    content = filepath.read_text(encoding="utf-8")
    m = re.search(r"## Accumulated Learnings\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return []
    section = m.group(1)

    pending = []
    for em in ENTRY_RE.finditer(section):
        suggestion = em.group("suggestion").strip()
        if "[TRIAGED]" in suggestion:
            continue
        clean_sugg = suggestion.replace("[TRIAGED]", "").strip()
        if not clean_sugg or clean_sugg.lower() in ("none", "n/a", "-"):
            continue
        pending.append({
            "date": em.group("date").strip(),
            "task": em.group("task").strip(),
            "friction": em.group("friction").strip(),
            "suggestion": clean_sugg,
            "raw_block": em.group(0),
        })
    return pending


def mark_entry_triaged(filepath: Path, raw_block: str) -> bool:
    """
    Append " [TRIAGED]" to the SUGGESTION line of `raw_block` inside `filepath`.
    Returns True on success.
    """
    content = filepath.read_text(encoding="utf-8")
    if raw_block not in content:
        # Block boundaries may have shifted (file edited between read + write).
        # Fall back to matching just the SUGGESTION line.
        suggestion_line = next(
            (ln for ln in raw_block.splitlines() if ln.lstrip().startswith("SUGGESTION:")),
            None,
        )
        if not suggestion_line or suggestion_line not in content:
            return False
        new = content.replace(suggestion_line, suggestion_line.rstrip() + " [TRIAGED]", 1)
    else:
        # Rewrite the whole block so we don't add [TRIAGED] twice if the line
        # already had trailing whitespace.
        last_line = raw_block.rstrip().splitlines()[-1]
        new_last = last_line.rstrip() + " [TRIAGED]"
        new_block = raw_block.rstrip().rsplit(last_line, 1)[0] + new_last
        new = content.replace(raw_block, new_block, 1)
    filepath.write_text(new, encoding="utf-8")
    return True


# ── Notion ────────────────────────────────────────────────────────────
def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def create_notion_task(token: str, agent: str, entry: dict) -> tuple[bool, str]:
    """
    POST /v1/pages — create a new page in the Tasks data source. Returns
    (ok, page_url_or_error).
    """
    title = f"[Agent Improvement] {agent}: {entry['suggestion']}"
    # Notion's title field cap is 2000 chars; clip generously here.
    title = title[:2000]

    notes_lines = [
        f"[{entry['date']}] TASK: {entry['task']}",
        f"  FRICTION: {entry['friction']}",
        f"  SUGGESTION: {entry['suggestion']}",
    ]
    hub = HUB_FILES.get(agent)
    if hub and hub.exists():
        notes_lines.append("")
        notes_lines.append(f"Hub file: {hub} — apply the same rule change here when this task is accepted.")
    description = "\n".join(notes_lines)

    body = {
        "parent": {"type": "data_source_id", "data_source_id": NOTION_DATA_SOURCE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Area": {"select": {"name": AREA_OLYMPIC}},
            "Kaizen Status": {"select": {"name": KAIZEN_STATUS_REVIEW}},
            "Action State": {"relation": [{"id": KAIZEN_ACTION_STATE_PAGE_ID}]},
            "Description": {"rich_text": [{"text": {"content": description[:2000]}}]},
        },
    }
    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=json.dumps(body).encode("utf-8"),
        headers=_notion_headers(token),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
            return True, data.get("url", data.get("id", ""))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", "replace")[:400]
        return False, f"HTTP {e.code}: {err_body}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


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
    log = log[-200:]
    LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Kaizen Promote poller (memory -> Notion)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse memory + show what would be promoted; no Notion writes, no memory edits.")
    args = ap.parse_args()

    env = load_env(ENV_FILE)
    token = env.get("NOTION_API_TOKEN") or os.environ.get("NOTION_API_TOKEN")
    if not token:
        print(f"ERROR: NOTION_API_TOKEN missing from {ENV_FILE} and environment", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    print(f"Kaizen Promote poller — {now.isoformat()}")
    print(f"  dry_run={args.dry_run}")

    memory_dir = resolve_memory_dir()
    if memory_dir is None:
        # Silent no-op — this host doesn't carry the Claude memory dir, which
        # is expected on every machine except the one that runs the daily
        # kaizen_sync. Don't ping Telegram every Monday for that.
        msg = ("No local Claude Code memory dir with agent_*.md files. "
               "This host has no Kaizen data to promote.")
        print(f"  {msg}")
        append_log({"ts": now.isoformat(), "ok": True, "skipped": True,
                    "reason": "no_memory_dir", "dry_run": args.dry_run})
        return 0

    print(f"  memory_dir={memory_dir}")

    # Collect pending entries per agent.
    by_agent: dict[str, list[dict]] = {}
    for agent, fname in AGENT_FILES.items():
        pending = parse_pending_entries(memory_dir / fname)
        if pending:
            by_agent[agent] = pending
            print(f"  {agent}: {len(pending)} pending")

    total = sum(len(v) for v in by_agent.values())
    if total == 0:
        send_telegram(
            "🔧 <b>Kaizen Promote — nothing to action</b>\n"
            f"<i>{now.strftime('%a %d %b %H:%M UTC')}</i> · "
            "No un-triaged suggestions across the 6 agent memory files."
        )
        append_log({"ts": now.isoformat(), "ok": True, "matched": 0,
                    "dry_run": args.dry_run})
        return 0

    if args.dry_run:
        lines = [f"<b>Dry-run — would create {total} task(s)</b>"]
        for agent, items in by_agent.items():
            lines.append(f"\n<b>{agent}</b> ({len(items)})")
            for it in items[:5]:
                lines.append(f"  • [{it['date']}] {it['suggestion'][:90]}")
        send_telegram("🧪 <b>Kaizen Promote — dry run</b>\n\n" + "\n".join(lines))
        append_log({"ts": now.isoformat(), "ok": True, "matched": total,
                    "by_agent": {a: len(v) for a, v in by_agent.items()},
                    "dry_run": True, "created": 0})
        return 0

    # Live mode: create Notion tasks one at a time, mark TRIAGED on success.
    created = 0
    failed: list[str] = []
    created_titles: list[str] = []
    for agent, items in by_agent.items():
        fpath = memory_dir / AGENT_FILES[agent]
        for it in items:
            ok, msg = create_notion_task(token, agent, it)
            if not ok:
                failed.append(f"{agent}/{it['date']}: {msg[:200]}")
                print(f"  FAIL {agent} {it['date']}: {msg[:200]}")
                continue
            created += 1
            title = f"[Agent Improvement] {agent}: {it['suggestion'][:80]}"
            created_titles.append(title)
            print(f"  OK   {agent} {it['date']} -> {msg}")
            # Mark triaged immediately so a retry/crash doesn't dup the task.
            if not mark_entry_triaged(fpath, it["raw_block"]):
                # Worth flagging — Notion task exists but memory wasn't marked,
                # so next run will create a duplicate unless this is fixed.
                failed.append(f"{agent}/{it['date']}: triage-mark failed (Notion task DID create)")

    # Telegram summary
    summary_lines = [
        f"{'✅' if not failed else '⚠️'} <b>Kaizen Promote — {now.strftime('%a %d %b')}</b>",
        f"Created: <b>{created}</b> of {total} Notion task(s)",
    ]
    if created_titles:
        summary_lines.append("\nNew tasks:")
        summary_lines.extend(f"• {t}" for t in created_titles[:10])
    if failed:
        summary_lines.append(f"\n<b>Failures ({len(failed)}):</b>")
        summary_lines.extend(f"• <code>{f[:200]}</code>" for f in failed[:5])
    send_telegram("\n".join(summary_lines))

    append_log({
        "ts": now.isoformat(), "ok": not failed,
        "matched": total, "created": created,
        "by_agent": {a: len(v) for a, v in by_agent.items()},
        "failures": failed, "dry_run": False,
    })
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
