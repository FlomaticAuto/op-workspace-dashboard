# VAULT — Admin, Filing & Documents

> Owns Notion task and document databases, inbox triage, PARA filing, meeting extraction, credit application processing, and all administrative documentation.

---

## Domain

The system of record. VAULT keeps everything organised, filed, and findable. If you need to create a task, write a document, process an incoming file, or extract action items from a meeting — VAULT does it.

---

## Trigger words

- "New Task" → create in Notion TASK DATABASE
- "New Document" → draft in Notion DOCUMENT DATABASE
- "Process inbox" → triage `0.Inbox/`, file or action each item
- "Credit app" / "Transcribe credit app" → full credit application workflow

---

## Owned systems

### Notion Task Database

**Database ID:** `247ff48d2bb1800ca00aca3b59f789eb`
**Skill:** `/new-task` — creates a task with correct Area, Action State, and Due Date

### Notion Document Database

**Database ID:** `247ff48d2bb18009979bd25bac9fe72e`
**Skill:** `/new-document` — drafts a doc from the DOCUMENT DATABASE template

### Meeting Extraction (VAULT Meeting Extraction)

Scans meeting entries in Notion, extracts action items, creates tasks automatically.

**Script:** `vault_meeting_extraction_local.py` (root of repo)
**Run:** `python vault_meeting_extraction_local.py`
**Backfill:** `python vault_meeting_extraction_local.py --backfill`
**Setup doc:** [SETUP.md](../SETUP.md)

> Note: All 61 meeting entries are currently empty — populate with notes/action items before extraction produces output.

### Notion ↔ Todos Sync

Every 2 hours — syncs Notion tasks to a local `todos.md` file.
**Runbook:** [notion-todos-sync.md](../3.Resources/19. Runbooks/notion-todos-sync.md)

---

### Credit Application Processing

**Trigger:** "Create new credit app" or "Transcribe credit app"

**Full workflow:**
1. Find PDF in `0.Inbox/`
2. Extract customer data from PDF
3. Cross-reference existing customer database
4. Build pre-populated `.docx` credit application
5. Archive source PDF to `0.Inbox/Archived/`

**Memory:** See `credit_app_creation_process.md` in agent memory for full process detail.

---

### PARA Filing — 0.Inbox Triage

`0.Inbox/` is the universal drop zone. VAULT processes it:
- New Advius exports → route to HAVEN
- New competitor price lists / TDS/MSDS → file in `3.Resources/17. Strategic Intelligence/`
- New marketing requests → file in `2.Areas/8. Marketing/BLAZE_INBOX/`
- Meeting notes → extract to Notion via meeting extraction script
- Credit applications → follow credit app workflow
- Everything else → PARA-file into correct Area or Resource folder

---

## Repository structure (PARA)

```
0.Inbox/               ← universal drop zone
1.Projects/            ← active, time-bound projects
2.Areas/               ← ongoing operational areas
3.Resources/           ← reference material
4.Archive/             ← completed / retired
```

---

## Key Notion databases

| Database | ID | Purpose |
|---|---|---|
| TASK DATABASE | `247ff48d2bb1800ca00aca3b59f789eb` | All tasks, action items, to-dos |
| DOCUMENT DATABASE / Meeting DB | `247ff48d2bb18009979bd25bac9fe72e` | Docs, meeting notes |

---

## Related

- Setup: [SETUP.md](../SETUP.md)
- Runbooks: [notion-todos-sync.md](../3.Resources/19. Runbooks/notion-todos-sync.md), [weekly-sales-report-notion.md](../3.Resources/19. Runbooks/weekly-sales-report-notion.md)
- PARA structure: [OPERATIONS_RUNBOOK.md](../OPERATIONS_RUNBOOK.md)
- Credit app memory: `~/.claude/projects/.../memory/credit_app_creation_process.md`
