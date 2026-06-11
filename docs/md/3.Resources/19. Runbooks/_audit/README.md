# Runbook drift audit

Weekly check that compares each runbook's `Last verified:` date against the most recent change to the scripts it documents. If a script has moved on more than 30 days ahead of its runbook, a Telegram alert fires.

## Files

- `audit_runbooks.py` — the audit script. Self-contained, stdlib + truststore.
- This README.

## What it does

1. Reads every `*.md` in `3.Resources/19. Runbooks/` (except `_*` and `RUNBOOKS.md`).
2. Looks up each runbook in the `RUNBOOK_SCRIPTS` map (inside the script).
3. For each mapped script, gets the most recent commit date via `git log -1 --format=%cI`. Falls back to filesystem mtime if the file is untracked.
4. Compares `worst_script_mtime - last_verified` per runbook.
5. If drift > **30 days** → flag stale → Telegram alert → exit 1.
6. If clean → exit 0, silent.
7. Always writes a daily log to `C:\Users\quint\.claude\logs\runbook-audit\YYYY-MM-DD.log`.

## Verified behaviour

- Clean run: `audit complete: 0 stale, 0 warnings, 20 runbooks checked` → exit 0
- Stale run (forced by backdating a `Last verified:` line): Telegram fires, exit 1
- TLS: uses `truststore.inject_into_ssl()` — required on this machine because AV does TLS inspection (see memory `feedback_python_truststore_for_https`)

## When you add a new runbook

1. Write the runbook in `3.Resources/19. Runbooks/`.
2. Add it to the `RUNBOOK_SCRIPTS` dict in `audit_runbooks.py` with the list of scripts it documents.
3. Add a row to `RUNBOOKS.md`.

If you forget step 2, the next audit will warn `runbook on disk but not in RUNBOOK_SCRIPTS map: <file>` — visible in the log but doesn't fail the run.

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\19. Runbooks\_audit"
python audit_runbooks.py
```

## Register the weekly Task Scheduler job

**Schedule:** Mon 06:30 SAST.

PowerShell — register the task (run once, as your normal user; **no admin elevation needed** since it runs as you):

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "audit_runbooks.py" `
  -WorkingDirectory "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\19. Runbooks\_audit"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 06:30

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
  -TaskName "Runbook Drift Audit" `
  -TaskPath "\Olympic Paints\" `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Description "Weekly drift check: flags runbooks more than 30 days behind their underlying scripts."
```

Unregister later:

```powershell
Unregister-ScheduledTask -TaskName "Runbook Drift Audit" -TaskPath "\Olympic Paints\" -Confirm:$false
```

Inspect last run:

```powershell
Get-ScheduledTask -TaskName "Runbook Drift Audit" -TaskPath "\Olympic Paints\" | Get-ScheduledTaskInfo
```

## Convention notes that bit during development

- **Telegram token lives in `1.Projects/PULSE — Sales & Ops Manager/.env`**, NOT `PULSE v2`. The v2 folder has no `.env`. Memory `feedback_telegram_token_source` is stale on the v2 detail — verified 2026-05-21.
- **`truststore.inject_into_ssl()` is mandatory** for any HTTPS call from this machine (Telegram, Notion, Zoho). Without it: `SSL: CERTIFICATE_VERIFY_FAILED: Basic Constraints of CA cert not marked critical`. See `feedback_python_truststore_for_https`.
- **Logs MUST live outside OneDrive.** `C:\Users\quint\.claude\logs\runbook-audit\`. See `feedback_schtasks_logs_outside_onedrive`.
- **Exit codes are load-bearing.** Task Scheduler "Last Run Result" surfaces them — non-zero on stale or crash means the tile in Task Scheduler shows red and you notice. Don't swallow exceptions.
