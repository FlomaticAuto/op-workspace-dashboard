# Runbook — Notion ↔ todos.md Sync

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** low — convenience mirror, not a system of record

---

## Purpose

Bidirectional sync between Claude's `memory/todos.md` and the Notion Task DB. Pushes Claude entries with Area=Olympic / State=Committed. Pulls Notion tasks (Area=Olympic, ≥2026-01-01, state∈{Committed, Thinking, Waiting}). Drop-outs (tasks no longer matching the filter) move to an `# Archived` section.

---

## How it runs

- **Trigger:** Task Scheduler `Olympic — Sync Claude TODOs`
- **Schedule:** Every **2 hours**
- **Entry point:** `sync_claude_todos.py` (project root)
- **Env:** `NOTION_API_TOKEN` (User-scope env var + project `.env`)

---

## Inputs

| Source | Notes |
|---|---|
| Claude memory | `memory/todos.md` |
| Notion Task DB | per [[reference_notion_task_database]] |

---

## Outputs

| Destination | Notes |
|---|---|
| Claude `todos.md` | refreshed with current Notion state |
| Notion Task DB | Claude entries pushed with Area=Olympic, State=Committed |
| Archived section | `# Archived` heading inside `todos.md` |

---

## Known failure modes

1. **Symptom:** Sync fails with 401.
   **Cause:** Notion integration not shared with TASK DATABASE + Action/State DB.
   **Fix:** Share "Olympic Paints Automations" integration with both DBs.

2. **Symptom:** Page create fails with `parent.database_id` error.
   **Cause:** Notion API 2025-09-03 requires `data_source_id`.
   **Fix:** Use `parent.data_source_id` for create; `/data_sources/{id}/query` for reads. See [[feedback_notion_api_2025_data_source]].

3. **Symptom:** "Document database" lookup hit container page instead of DB.
   **Cause:** Targeting parent page instead of `data_source_id`.
   **Fix:** See [[feedback_notion_document_database_target]].

4. **Symptom:** TLS fail on Notion API.
   **Fix:** `truststore.inject_into_ssl()`. See [[feedback_python_truststore_for_https]].

---

## Logs

- `C:\Users\quint\.claude\logs\notion-todos-sync\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
python sync_claude_todos.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_claude_todos_sync]], [[reference_notion_task_database]], [[feedback_notion_api_2025_data_source]]
