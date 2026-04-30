#!/usr/bin/env python3
"""
Meeting Minutes Notes Extractor — VAULT Agent
Olympic Paints | Daily run via Windows Task Scheduler at 07:00

Reads the full body content of each Notion meeting page (all blocks),
then uses Claude AI to extract action items and create tasks in the
Task Database. No rigid pattern matching — Claude reads the minutes
as a human would.

Usage:
    python meeting_minutes_extractor.py              # last 24 hours
    python meeting_minutes_extractor.py --backfill   # from 1 Apr 2026

Environment variables required:
    NOTION_API_TOKEN    — Notion integration token
    ANTHROPIC_API_KEY   — Anthropic API key for Claude extraction
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────

NOTION_API_TOKEN  = os.getenv("NOTION_API_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

for var, val in [("NOTION_API_TOKEN", NOTION_API_TOKEN), ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)]:
    if not val:
        print(f"ERROR: {var} environment variable not set")
        sys.exit(1)

NOTION_API_URL     = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"

MEETING_DATABASE_ID    = "247ff48d2bb18009979bd25bac9fe72e"
TASK_DATABASE_ID       = "247ff48d2bb1800ca00aca3b59f789eb"
ACTION_STATE_COMMITTED = "301ff48d2bb180af869fdc19b6f6b062"

EXTRACTION_MODEL   = "claude-haiku-4-5-20251001"
MAX_CONTENT_CHARS  = 8000   # token budget per meeting

VALID_AREAS = {"Olympic", "Timion", "Quintus", "Flomatic", "GOD"}

LOG_DIR  = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"meeting_extractor_{datetime.now().strftime('%Y-%m-%d')}.log"

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ─── Notion Client ────────────────────────────────────────────────────────────

class NotionClient:
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str) -> Dict:
        r = requests.get(f"{NOTION_API_URL}{endpoint}", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, body: Dict) -> Dict:
        r = requests.post(f"{NOTION_API_URL}{endpoint}", headers=self.headers, json=body)
        r.raise_for_status()
        return r.json()

    def query_database(self, db_id: str, filter_dict: Optional[Dict] = None) -> List[Dict]:
        results, cursor = [], None
        while True:
            body: Dict[str, Any] = {"page_size": 100}
            if filter_dict:
                body["filter"] = filter_dict
            if cursor:
                body["start_cursor"] = cursor
            data = self._post(f"/databases/{db_id}/query", body)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return results

    def get_page_content(self, page_id: str) -> str:
        """Read ALL blocks from a Notion page and return as plain text."""
        return self._read_blocks(page_id, depth=0)

    def _read_blocks(self, block_id: str, depth: int) -> str:
        parts, cursor = [], None
        while True:
            endpoint = f"/blocks/{block_id}/children"
            if cursor:
                endpoint += f"?start_cursor={cursor}"
            try:
                data = self._get(endpoint)
            except Exception as e:
                logger.warning(f"Could not fetch blocks for {block_id}: {e}")
                break
            for block in data.get("results", []):
                line = self._block_to_text(block, depth)
                if line:
                    parts.append(line)
                if block.get("has_children"):
                    child_text = self._read_blocks(block["id"], depth + 1)
                    if child_text:
                        parts.append(child_text)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return "\n".join(parts)

    @staticmethod
    def _block_to_text(block: Dict, depth: int) -> str:
        btype = block.get("type", "")
        pad   = "  " * depth

        def rich(key: str) -> str:
            return "".join(
                t.get("text", {}).get("content", "")
                for t in block.get(key, {}).get("rich_text", [])
            )

        if btype == "heading_1":   return f"{pad}# {rich('heading_1')}"
        if btype == "heading_2":   return f"{pad}## {rich('heading_2')}"
        if btype == "heading_3":   return f"{pad}### {rich('heading_3')}"
        if btype == "paragraph":
            t = rich("paragraph")
            return f"{pad}{t}" if t else ""
        if btype == "bulleted_list_item": return f"{pad}• {rich('bulleted_list_item')}"
        if btype == "numbered_list_item": return f"{pad}- {rich('numbered_list_item')}"
        if btype == "to_do":
            checked = block.get("to_do", {}).get("checked", False)
            return f"{pad}[{'x' if checked else ' '}] {rich('to_do')}"
        if btype == "quote":    return f"{pad}> {rich('quote')}"
        if btype == "callout":  return f"{pad}>> {rich('callout')}"
        if btype == "toggle":   return f"{pad}{rich('toggle')}"
        if btype == "divider":  return f"{pad}---"
        if btype == "table_row":
            cells = block.get("table_row", {}).get("cells", [])
            row = " | ".join(
                "".join(t.get("text", {}).get("content", "") for t in cell)
                for cell in cells
            )
            return f"{pad}{row}"
        return ""

    def create_meeting_task(self, meeting_title: str, meeting_id: str, area: str) -> Optional[str]:
        """Create one task per meeting. Action items are written as blocks into the page body."""
        if area not in VALID_AREAS:
            area = "Olympic"

        task_title = f"{meeting_title} — Action Items"

        properties: Dict[str, Any] = {
            "Name": {
                "title": [{"text": {"content": task_title[:200]}}]
            },
            "Area": {
                "select": {"name": area}
            },
            "MM": {
                "relation": [{"id": meeting_id}]
            },
            "Action State": {
                "relation": [{"id": ACTION_STATE_COMMITTED}]
            },
        }

        try:
            result = self._post("/pages", {
                "parent": {"database_id": TASK_DATABASE_ID},
                "properties": properties,
            })
            return result.get("id")
        except Exception as e:
            logger.error(f"Failed to create task for meeting '{meeting_title}': {e}")
            return None

    def append_action_blocks(self, task_page_id: str, meeting_title: str, action_items: List[Dict]) -> None:
        """Append a heading + to-do checkboxes for each action item into the task page body."""
        blocks: List[Dict[str, Any]] = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": f"Actions to be taken regarding {meeting_title}"}}]
                },
            }
        ]

        for item in action_items:
            label = item.get("title", "").strip()
            detail = item.get("description", "").strip()
            text = f"{label} — {detail}" if detail else label
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
                    "checked": False,
                },
            })

        # Notion allows max 100 blocks per append call
        for i in range(0, len(blocks), 100):
            try:
                self._post(f"/blocks/{task_page_id}/children", {"children": blocks[i:i+100]})
            except Exception as e:
                logger.error(f"Failed to append blocks to task {task_page_id}: {e}")


# ─── Claude Extraction ────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """\
You are extracting action items from Olympic Paints meeting minutes.

Meeting: {title}
Date: {date}
Attendees: {attendees}

--- MEETING CONTENT START ---
{content}
--- MEETING CONTENT END ---

Extract every action item, follow-up, decision requiring action, or task \
mentioned in these minutes. Read them exactly as a person would — do not \
require special formatting or labels.

Return a JSON array. Each element must have:
  "title"       — short, actionable task name (max 100 chars)
  "description" — context: who, what, why (from the minutes)
  "owner"       — first name of responsible person, or "Unassigned"
  "due_date"    — ISO date YYYY-MM-DD if a date is mentioned, otherwise null
  "area"        — one of: Olympic, Timion, Quintus, Flomatic, GOD
                  Infer from context. Default to Olympic if unclear.

Rules:
• Capture implicit tasks, not only lines labelled "Action:"
• If there are genuinely no action items, return []
• Return ONLY the raw JSON array — no markdown, no explanation

Example output:
[
  {{
    "title": "Send updated pricing sheet to Jhb stockist",
    "description": "Quintus to send the Q2 pricing by end of week after stockist review.",
    "owner": "Quintus",
    "due_date": null,
    "area": "Olympic"
  }}
]"""


def extract_with_claude(
    client: anthropic.Anthropic,
    title: str,
    date: str,
    attendees: str,
    content: str,
) -> List[Dict]:
    if not content.strip():
        return []

    prompt = EXTRACTION_PROMPT.format(
        title=title or "Untitled",
        date=date or "Unknown",
        attendees=attendees or "Unknown",
        content=content[:MAX_CONTENT_CHARS],
    )

    try:
        msg = client.messages.create(
            model=EXTRACTION_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()

        # Strip markdown fences if Claude wrapped the JSON
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")]

        items = json.loads(raw)
        logger.info(f"  Claude found {len(items)} action item(s)")
        return items

    except json.JSONDecodeError:
        logger.error("Claude returned non-JSON — skipping this meeting")
        logger.debug(f"Raw response: {raw}")
        return []
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return []


# ─── Helpers ──────────────────────────────────────────────────────────────────

def prop_text(props: Dict, name: str, ptype: str) -> str:
    f = props.get(name, {})
    if f.get("type") != ptype:
        return ""
    if ptype == "title":
        return "".join(t.get("text", {}).get("content", "") for t in f.get("title", []))
    if ptype == "rich_text":
        return "".join(t.get("text", {}).get("content", "") for t in f.get("rich_text", []))
    if ptype == "select":
        s = f.get("select")
        return s.get("name", "") if s else ""
    if ptype == "date":
        d = f.get("date")
        return d.get("start", "") if d else ""
    return ""


def query_meetings(notion: NotionClient, backfill: bool) -> List[Dict]:
    end_dt   = datetime.now(timezone.utc)
    start_dt = datetime(2026, 4, 1, tzinfo=timezone.utc) if backfill else end_dt - timedelta(days=1)
    logger.info(f"Date range: {start_dt.date()} to {end_dt.date()}")

    all_meetings = notion.query_database(MEETING_DATABASE_ID)

    filtered = []
    for m in all_meetings:
        try:
            created = datetime.fromisoformat(m["created_time"].replace("Z", "+00:00"))
            if start_dt <= created <= end_dt:
                filtered.append(m)
        except (KeyError, ValueError):
            pass

    logger.info(f"Meetings in range: {len(filtered)} of {len(all_meetings)} total")
    return filtered


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(backfill: bool = False):
    logger.info("=" * 60)
    logger.info("Meeting Minutes Notes Extractor — VAULT")
    logger.info(f"Mode: {'backfill from 1 Apr 2026' if backfill else 'last 24 hours'}")
    logger.info("=" * 60)

    notion = NotionClient(NOTION_API_TOKEN)
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    meetings = query_meetings(notion, backfill)
    if not meetings:
        logger.info("No meetings to process.")
        return

    total_tasks   = 0
    tasks_by_area: Dict[str, int] = {}

    for page in meetings:
        props      = page.get("properties", {})
        meeting_id = page["id"]

        title = (
            prop_text(props, "Document Name", "title") or
            prop_text(props, "Meeting Title",  "title") or
            prop_text(props, "Name",           "title") or
            "Untitled Meeting"
        )
        date      = prop_text(props, "Date",      "date")
        attendees = prop_text(props, "Attendees", "rich_text")

        logger.info(f"\nProcessing: {title} ({date or 'no date'})")

        # Read full page body (blocks)
        body_text = notion.get_page_content(meeting_id)

        # Append any text found directly in property fields
        notes_field = (
            prop_text(props, "Notes",         "rich_text") or
            prop_text(props, "Meeting Notes", "rich_text") or
            prop_text(props, "Description",   "rich_text")
        )
        full_content = "\n\n".join(filter(None, [notes_field, body_text])).strip()

        if not full_content:
            logger.info("  No content found — skipping")
            continue

        logger.info(f"  Content: {len(full_content)} chars")

        action_items = extract_with_claude(claude, title, date, attendees, full_content)

        if not action_items:
            logger.info("  No action items extracted")
            continue

        # Determine area from the meeting page itself; fall back to most common across items
        meeting_area = prop_text(props, "Area", "select") or prop_text(props, "area", "select")
        if meeting_area not in VALID_AREAS:
            area_counts: Dict[str, int] = {}
            for item in action_items:
                a = item.get("area", "Olympic")
                area_counts[a] = area_counts.get(a, 0) + 1
            meeting_area = max(area_counts, key=area_counts.get) if area_counts else "Olympic"
        if meeting_area not in VALID_AREAS:
            meeting_area = "Olympic"

        task_id = notion.create_meeting_task(title, meeting_id, meeting_area)
        if task_id:
            notion.append_action_blocks(task_id, title, action_items)
            tasks_by_area[meeting_area] = tasks_by_area.get(meeting_area, 0) + 1
            total_tasks += 1
            logger.info(f"  Task created [{meeting_area}] with {len(action_items)} action item(s)")

    logger.info("\n" + "=" * 60)
    logger.info(f"Done — {len(meetings)} meeting(s) processed, {total_tasks} task page(s) created")
    for area, count in sorted(tasks_by_area.items()):
        logger.info(f"  {area}: {count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run(backfill="--backfill" in sys.argv)
