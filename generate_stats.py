#!/usr/bin/env python3
"""
Olympic Paints Workspace Dashboard — Stats Generator
Queries Notion databases and writes stats.json for the GitHub Pages dashboard.
Runs daily via GitHub Actions at 06:00 UTC (08:00 SAST).

Required environment variable:
    NOTION_API_TOKEN — Notion integration token
"""

import os
import json
import sys
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────

NOTION_TOKEN = os.environ.get("NOTION_API_TOKEN")
if not NOTION_TOKEN:
    print("ERROR: NOTION_API_TOKEN not set")
    sys.exit(1)

NOTION_API_URL     = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

MEETING_DB  = "247ff48d2bb18009979bd25bac9fe72e"
TASK_DB     = "247ff48d2bb1800ca00aca3b59f789eb"
DOCUMENT_DB = "254ff48d2bb1809eb980c080b74c7a7b"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_API_VERSION,
    "Content-Type": "application/json",
}

# ─── Notion Helpers ───────────────────────────────────────────────────────────

def query_db(db_id: str, filter_dict: dict = None) -> list:
    results, cursor = [], None
    while True:
        body = {"page_size": 100}
        if filter_dict:
            body["filter"] = filter_dict
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(
                f"{NOTION_API_URL}/databases/{db_id}/query",
                headers=HEADERS,
                json=body,
                timeout=30,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"  WARNING: API error querying {db_id}: {e}")
            break
        data = r.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results


def prop_select(page: dict, field: str) -> str:
    f = page.get("properties", {}).get(field, {})
    sel = f.get("select")
    return sel.get("name", "") if sel else ""


def prop_date(page: dict, field: str) -> str:
    f = page.get("properties", {}).get(field, {})
    d = f.get("date")
    return d.get("start", "") if d else ""


# ─── Stats Collection ─────────────────────────────────────────────────────────

def collect_stats() -> dict:
    now = datetime.now(timezone.utc)
    week_ago   = (now - timedelta(days=7)).isoformat()
    month_ago  = (now - timedelta(days=30)).isoformat()

    print("Querying Task Database...")
    tasks = query_db(TASK_DB)
    total_tasks = len(tasks)
    tasks_by_area: dict[str, int] = {}
    for t in tasks:
        area = prop_select(t, "Area") or "Unassigned"
        tasks_by_area[area] = tasks_by_area.get(area, 0) + 1

    tasks_this_week = sum(
        1 for t in tasks
        if t.get("created_time", "") >= week_ago
    )
    print(f"  Tasks: {total_tasks} total, {tasks_this_week} this week")

    print("Querying Meeting Database...")
    meetings = query_db(MEETING_DB)
    total_meetings = len(meetings)
    meetings_this_month = sum(
        1 for m in meetings
        if m.get("created_time", "") >= month_ago
    )
    print(f"  Meetings: {total_meetings} total, {meetings_this_month} this month")

    print("Querying Document Database...")
    docs = query_db(DOCUMENT_DB)
    total_docs = len(docs)
    print(f"  Documents: {total_docs} total")

    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "generated_at_iso": now.isoformat(),
        "total_tasks": total_tasks,
        "tasks_this_week": tasks_this_week,
        "tasks_by_area": tasks_by_area,
        "total_meetings": total_meetings,
        "meetings_this_month": meetings_this_month,
        "total_docs": total_docs,
        "agents": 6,
        "automations": 3,
        "integrations": 12,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Olympic Paints Dashboard — Stats Generator")
    print(f"Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    stats = collect_stats()

    output_path = os.path.join(os.path.dirname(__file__), "stats.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"\nWrote {output_path}")
    print("=" * 50)
    print("Summary:")
    print(f"  Tasks:     {stats['total_tasks']} ({stats['tasks_this_week']} this week)")
    print(f"  Meetings:  {stats['total_meetings']}")
    print(f"  Documents: {stats['total_docs']}")
    for area, count in sorted(stats["tasks_by_area"].items()):
        print(f"    {area}: {count}")
    print("=" * 50)
