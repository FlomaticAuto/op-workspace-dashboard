# Runbook — Weekly Sales Report Notion Mirror

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — internal note system; mirror outage doesn't lose data (notes still on disk)

---

## Purpose

Mirrors weekly sales notes from the local folder watcher into the Notion "Weekly Sales Notes" database. New notes are pushed on save; a sweep every 5 minutes retries pending mirrors that failed (network, rate limit, etc).

---

## How it runs

- **Folder watcher:** `1.Projects/Weekly Sales Report/weekly/folder_watcher.py`
- **Notion mirror:** `1.Projects/Weekly Sales Report/weekly/notion_mirror.py`
- **Retry sweep:** `1.Projects/Weekly Sales Report/weekly/notion_retry.py` — every **5 minutes**
- **Telegram listener:** `telegram_listener.py` (incoming voice/text notes)

---

## Inputs

| Source | Path |
|---|---|
| New notes folder | per-week directory `1.Projects/Weekly Sales Report/2026-WNN/` |
| Telegram messages | via listener |
| Classifier | `weekly/classifier.py` — Claude intent classification + theme clustering |

---

## Outputs

| Destination | Notes |
|---|---|
| Notion Weekly Sales Notes DB | parent must be `data_source_id`, media URLs comma-joined |
| Compiled weekly report | `compile_report.py` |
| Email send | `send_weekly_email.py` |

---

## Known failure modes

1. **Symptom:** Notion mirror fails with `parent.database_id` error.
   **Cause:** Notion API 2025-09-03 requires `data_source_id`.
   **Fix:** Already corrected on 2025-09-03 (see commit `b3ad53c`). Confirm `parent.data_source_id` used and media URLs comma-joined. See [[feedback_notion_api_2025_data_source]].

2. **Symptom:** Notes never make it to Notion.
   **Cause:** Mirror watcher down OR retry sweep not running.
   **Fix:** Restart both. The retry sweep (`notion_retry.py` every 5 min) is the safety net — re-registers failed mirrors. See commit `3ad4577`.

3. **Symptom:** Classifier crashes on KeyError.
   **Cause:** Missing key in classifier response.
   **Fix:** Fixed in commit `1e3327c` — constants, `ClassifierError`, KeyError guard.

4. **Symptom:** Duplicate Notion rows.
   **Cause:** Debounce window too short; same note saved twice.
   **Fix:** `weekly/debounce.py` controls window — verify it's active.

---

## Logs

- `C:\Users\quint\.claude\logs\weekly-sales\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Weekly Sales Report"

# Start the watcher
python -m weekly.folder_watcher

# Force a one-shot mirror of pending notes
python -m weekly.notion_retry

# Compile + send the weekly report
python -m weekly.compile_report
python -m weekly.send_weekly_email

# Init a new week folder
python -m weekly.init_new_week
```

---

## Recent incidents

- **2025-09-03** — Notion API 2025-09-03 cutover: `data_source_id` + comma-joined media URLs.
- **Recent** — `notion_retry.py` added as 5-min sweep for stuck pending mirrors.

---

## Related

- Memory: [[feedback_notion_api_2025_data_source]], [[reference_notion_task_database]]
