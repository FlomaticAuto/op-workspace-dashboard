#!/usr/bin/env python3
"""
Olympic Paints Workspace Dashboard — Kaizen Status Generator
Reads Accumulated Learnings from all 6 agent profile .md files,
parses entries, and writes kaizen_status.json for the dashboard.

Run manually after /kaizen, or as part of your regular stats refresh.
"""

import json
import os
import re
from datetime import datetime, timezone

MEMORY_DIR = r"C:\Users\quint\.claude\projects\C--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory"

AGENT_FILES = {
    "HAVEN":   "agent_haven.md",
    "PRISM":   "agent_prism.md",
    "STRIKER": "agent_striker.md",
    "SIGMA":   "agent_sigma.md",
    "BLAZE":   "agent_blaze.md",
    "VAULT":   "agent_vault.md",
}

AGENT_COLORS = {
    "HAVEN":   "#2ECC71",
    "PRISM":   "#9B59B6",
    "STRIKER": "#E74C3C",
    "SIGMA":   "#E67E22",
    "BLAZE":   "#F5C200",
    "VAULT":   "#3498DB",
}

SKILLS = [
    {
        "name": "kaizen",
        "invoke": "/kaizen",
        "owner": "VAULT",
        "description": "Weekly improvement triage — reads all agent Accumulated Learnings, creates Notion tasks tagged [Agent Improvement], sends Telegram summary, marks entries [TRIAGED].",
        "cadence": "Weekly — Mondays 08:30",
        "file": ".claude/skills/kaizen.md",
    },
    {
        "name": "retrospective",
        "invoke": "/retrospective",
        "owner": "VAULT",
        "description": "Cross-agent retrospective — reads last 30 days of learnings, identifies patterns, delivers structured report to Telegram + Notion Document DB.",
        "cadence": "Monthly or after major incident",
        "file": ".claude/skills/retrospective.md",
    },
    {
        "name": "improve",
        "invoke": "/improve <agent> \"<suggestion>\"",
        "owner": "VAULT",
        "description": "Apply an approved improvement — edits the agent profile, marks the Notion task complete, sends Telegram confirmation. Requires Quintus approval first.",
        "cadence": "On-demand (after /kaizen review)",
        "file": ".claude/skills/improve.md",
    },
]


def parse_learnings(filepath: str) -> list[dict]:
    """Parse ## Accumulated Learnings entries from an agent profile .md file."""
    if not os.path.exists(filepath):
        print(f"  WARNING: {filepath} not found")
        return []

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Find the Accumulated Learnings section
    m = re.search(r"## Accumulated Learnings\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return []

    section = m.group(1)
    entries = []

    # Match each entry block: [YYYY-MM-DD] TASK: ...
    # followed by FRICTION: and SUGGESTION: lines
    pattern = re.compile(
        r"\[(\d{4}-\d{2}-\d{2})\]\s+TASK:\s+(.+?)\n"
        r"\s+FRICTION:\s+(.+?)\n"
        r"\s+SUGGESTION:\s+(.+?)(?=\n\[|\n<!--|\Z)",
        re.DOTALL
    )

    for match in pattern.finditer(section):
        date_str = match.group(1).strip()
        task = match.group(2).strip()
        friction = match.group(3).strip()
        suggestion_raw = match.group(4).strip()

        triaged = "[TRIAGED]" in suggestion_raw
        suggestion = suggestion_raw.replace("[TRIAGED]", "").strip()

        entries.append({
            "date": date_str,
            "task": task,
            "friction": friction,
            "suggestion": suggestion,
            "triaged": triaged,
            "has_suggestion": suggestion.lower() not in ("none", ""),
        })

    return entries


def collect_kaizen_status() -> dict:
    now = datetime.now(timezone.utc)

    agents_data = []
    total_entries = 0
    total_pending = 0
    total_triaged = 0

    for agent_name, filename in AGENT_FILES.items():
        filepath = os.path.join(MEMORY_DIR, filename)
        print(f"  Reading {agent_name} ({filename})...")
        entries = parse_learnings(filepath)

        pending = [e for e in entries if not e["triaged"] and e["has_suggestion"]]
        triaged = [e for e in entries if e["triaged"]]
        no_suggestion = [e for e in entries if not e["has_suggestion"]]

        total_entries += len(entries)
        total_pending += len(pending)
        total_triaged += len(triaged)

        print(f"    Entries: {len(entries)} total, {len(pending)} pending, {len(triaged)} triaged")

        agents_data.append({
            "agent": agent_name,
            "color": AGENT_COLORS[agent_name],
            "total_entries": len(entries),
            "pending_count": len(pending),
            "triaged_count": len(triaged),
            "entries": entries,
        })

    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "generated_at_iso": now.isoformat(),
        "summary": {
            "total_entries": total_entries,
            "total_pending": total_pending,
            "total_triaged": total_triaged,
            "agents_with_entries": sum(1 for a in agents_data if a["total_entries"] > 0),
        },
        "skills": SKILLS,
        "agents": agents_data,
    }


if __name__ == "__main__":
    print("=" * 50)
    print("Olympic Paints — Kaizen Status Generator")
    print(f"Run at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    status = collect_kaizen_status()

    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "kaizen_status.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    print(f"\nWrote {out}")
    print("=" * 50)
    print(f"  Total entries:  {status['summary']['total_entries']}")
    print(f"  Pending triage: {status['summary']['total_pending']}")
    print(f"  Triaged:        {status['summary']['total_triaged']}")
    print("=" * 50)
