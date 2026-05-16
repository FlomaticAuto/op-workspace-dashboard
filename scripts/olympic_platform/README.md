# Olympic Platform — Operator Guide

## Concepts

- Every Olympic-related scheduled task lives at `\Olympic Paints\<AGENT>\<Name>` in Task Scheduler.
- Every task is wrapped by `run_job.py`, which writes a heartbeat after each run.
- Failures ping Telegram immediately. There is no daily success digest.
- A separate manifest builder publishes `schedule_manifest.json` for the control-tower UI.

## Locations

- Wrapper:    `scripts/olympic_platform/run_job.py`
- Heartbeats: `C:\Users\quint\.claude\heartbeats\<job-id>.json` (+ `.history.jsonl`)
- Logs:       `C:\Users\quint\.claude\logs\<job-id>\<timestamp>.log`
- Manifest:   `C:\Users\quint\workspace-dashboard\data\schedule_manifest.json`
- Backups:    `C:\Users\quint\.claude\heartbeats\_migration-backups\<timestamp>\`

## Migration Status (bulk migration: 2026-05-16)

| Agent   | Tasks | Notes |
|---------|-------|-------|
| FLASH   | 1 | EmailEcommerce Dashboard |
| HAVEN   | 1 | Clocking Report Daily |
| PRISM   | 5 | KPI Update, Sales Dashboard, Workspace Health, CSO Intelligence, **Build Schedule Manifest (hourly)** |
| SIGMA   | 2 | Vehicle Report Weekly, Portal Trigger Server |
| STRIKER | 4 | Zoho Meetings Pull, Friday Sales Meeting, Zoho Leads Pull, Vehicle Report Health Check |
| VAULT   | 3 | Sync Claude TODOs (pilot), Kaizen Daily Sync, Meeting Extraction Daily |

**Total migrated: 16 tasks. Manifest builder runs hourly.**

## Stragglers requiring elevation

Three root-level tasks were created originally by an elevated process and cannot be deleted or modified by the current (non-admin) user. Each surfaces in the manifest as `agent: MISC` or as a `\` (root) entry. Resolve via Task Scheduler GUI run as Administrator, or run PowerShell as Administrator and re-execute the migration helper.

| Task | Action needed |
|---|---|
| `\Vehicle Report Weekly` | Delete (clean wrapped copy already at `\Olympic Paints\SIGMA\Vehicle Report Weekly`) |
| `\VAULT Meeting Extraction Daily` | Delete (clean wrapped copy already at `\Olympic Paints\VAULT\VAULT Meeting Extraction Daily`) |
| `\Olympic Paints\Olympic Paints - Meeting Minutes Extractor` | Migrate to `\Olympic Paints\VAULT\Meeting Minutes Extractor` (no wrapped copy exists yet — needs admin elevation to perform the round-trip) |

All three failed with `Access is denied. (Exception from HRESULT: 0x80070005 (E_ACCESSDENIED))` during automated migration.

## Pilot verification (2026-05-16)

| Check                              | Result | Heartbeat |
|------------------------------------|--------|-----------|
| Migrate via XML round-trip         | pass   | `sync-claude-todos.json` |
| Manual run, heartbeat written      | pass   | `ok: true`, duration 7.6s |
| Forced-failure heartbeat written   | pass   | `ok: false`, exit_code 1 |
| Telegram alert fires on failure    | _verified by user via inbox_ | — |

Backup of the pre-migration XML: `_migration-backups/pilot-20260516-131340/`.

## Adding a new wrapped task

Use `migrate_tasks.ps1` for existing tasks. For new ones, the action format is:

```
Path:      python
Arguments: "C:\Users\quint\workspace-dashboard\scripts\olympic_platform\run_job.py" <job-id> --agent <AGENT> -- <original command>
WorkDir:   <original working directory>
```

## Common operations

**See last 5 runs of a job:**

```powershell
Get-Content C:\Users\quint\.claude\heartbeats\<job-id>.history.jsonl | Select-Object -Last 5
```

**Manually fire a wrapped task:**

```powershell
Start-ScheduledTask -TaskPath '\Olympic Paints\<AGENT>\' -TaskName '<Name>'
```

**Disable without deleting:**

```powershell
Disable-ScheduledTask -TaskPath '\Olympic Paints\<AGENT>\' -TaskName '<Name>'
```

**Roll back a migration batch:**

```powershell
powershell -File scripts\olympic_platform\restore_tasks.ps1 -BackupDir <path> -Apply
```

**Regenerate the manifest:**

```powershell
python -m scripts.olympic_platform.build_schedule_manifest
```

## Environment variables

- `TELEGRAM_BOT_TOKEN` — Required for failure alerts. Set at user scope so Task Scheduler inherits it. Source: `1.Projects/PULSE — Sales & Ops Manager/.env`.
- `OLYMPIC_HEARTBEAT_ROOT` — Override the default heartbeat directory (default: `C:\Users\quint\.claude\heartbeats`).
- `OLYMPIC_LOG_ROOT` — Override the default log directory (default: `C:\Users\quint\.claude\logs`).
- `OLYMPIC_DISABLE_NOTIFY` — Set to `1` to suppress Telegram (used by tests).
