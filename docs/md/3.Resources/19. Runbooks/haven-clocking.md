# Runbook — HAVEN Clocking Pipeline

> **Last verified:** 2026-06-02
> **Owner:** Quintus / HAVEN
> **Criticality:** high — payroll uses YTD totals; missed clock-outs cost the company money

---

## Purpose

Automatically fetches the daily Advius biometric export from Outlook, processes it into the YTD master workbook, and emails the daily missed clock-out report to accounts. Without it, payroll has no source of truth for hours worked.

---

## How it runs — automated pipeline (Mon–Fri)

Four scheduled tasks run in sequence on the Administrator machine every weekday morning:

| Time | Task | Script | What it does |
|---|---|---|---|
| 07:15 | `HAVEN Fetch Clocking Email` | `fetch_clocking_email.py` | Downloads the Advius `.xlsx` attachment from Outlook (`Reporting/HR` folder) into `Inbox/` |
| 07:30 | `Daily Process Inbox` | `process_inbox.py` | Processes every `.xlsx` in `Inbox/`, updates YTD master, regenerates dashboard, sends emails, archives input |
| 17:00 | `End-of-Day Clocking Check` | `haven_eod_check.py` | Sends Telegram summary of missed clock-outs for the day |
| Mon 08:00 | `Weekly Dashboard Check` | `haven_dashboard_check.py` | Regenerates dashboard, sends Telegram + WhatsApp weekly summary |

**Host:** Administrator machine (DESKTOP-I0292P0). **Python:** `C:\Python313\python.exe`

**Log files:**
- Fetch: `C:\Users\Administrator\.claude\logs\haven-clocking-fetch\fetch.log`
- EOD check: `C:\Users\Administrator\.claude\logs\haven\eod_check.log`
- Weekly dashboard: `C:\Users\Administrator\.claude\logs\haven\dashboard_check.log`
- Process Inbox: Task Scheduler "Last Run Result" only (no log file)

---

## Daily verification checklist

HAVEN runs this check each working day to confirm the pipeline completed. Step through in order — each depends on the previous.

### Step 1 — Fetch ran (07:15)

Open the fetch log:
```
C:\Users\Administrator\.claude\logs\haven-clocking-fetch\fetch.log
```

**Pass:** Last entry says `Done. Scanned X matching emails. Saved 1.` OR `Skipped 1 (already present)` — either means the file was already in Inbox or was downloaded fresh.

**Fail:** Last entry says `Saved 0` with no "already present" note, or an error. The Advius email may not have arrived yet — check `quintusl@olympicpaints.co.za / Reporting / HR` folder in Outlook. If no email by 08:30, contact Advius.

---

### Step 2 — Inbox processed (07:30)

Check Task Scheduler:
```powershell
schtasks /query /tn "\Olympic Paints\HAVEN\Daily Process Inbox" /fo LIST | Select-String "Last Run|Last Result"
```

**Pass:** `Last Result: 0`

**Fail:** Any non-zero result. Check that:
- An `.xlsx` file was actually in `Inbox/` at 07:30 (Step 1 passed)
- `Output\Clocking Report YTD.xlsx` exists and is not locked by Excel
- The YTD master file is not open in Excel

To run manually:
```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts"
C:\Python313\python.exe process_inbox.py
```

---

### Step 3 — Emails sent

**Confirm in Outlook Sent Items** (quintusl@olympicpaints.co.za) — two emails should be present with today's date:

1. **YTD Excel email** — subject `Clocking Report YTD - DD Month YYYY`, attachment present
   - To: `accounts@olympicpaints.co.za`, `quintusl@olympicpaints.co.za`, `megan@advius.co.za`

2. **Missed clock-outs email** — subject `[DD Month YYYY] Missed Clockings — N employees | Olympic Paints`
   - To: same recipients
   - Check the figures look plausible — typical range is 5–25 missed per day

**Fail:** If emails are missing, `process_inbox.py` either failed (Step 2) or the Outlook `Send()` stuck in Outbox. Open Outlook manually and check the Outbox — if items are there, click Send/Receive to flush them.

---

### Step 4 — YTD master updated

Open `Output\Clocking Report YTD.xlsx` and confirm:
- The **Summary by Date** sheet shows today's date (or the most recent working day) in the last data row
- The row count in **Clocking Report** is larger than it was before this run

**If the YTD looks wrong (hours halved or doubled):** Stop — do not run again. Restore from OneDrive version history before proceeding. See Failure Mode 1 below.

---

### Step 5 — EOD Telegram received (17:00)

Check Telegram chat `8042233389` for a message starting `HAVEN — End-of-Day Clocking` sent at approximately 17:00.

**If no message arrived**, check the log:
```
C:\Users\Administrator\.claude\logs\haven\eod_check.log
```
Common cause: `TELEGRAM_BOT_TOKEN` not set — verify the system env var is present:
```powershell
[System.Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "Machine")
```
Should return the bot token. If blank, re-run:
```powershell
[System.Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "8596362314:AAGvGY-szeXm8YxIiWvLhkLxeeOvv6eWwfM", "Machine")
```

---

## Inputs

| Source | Path | Format | Cadence |
|---|---|---|---|
| Advius export (auto-fetched) | `Inbox/` (fetched from Outlook `Reporting/HR`) | `.xlsx` | Daily weekdays, emailed by Advius |
| YTD master | `Output/Clocking Report YTD.xlsx` | `.xlsx` | Accumulator — updated each run |

---

## Outputs

| Destination | Consumer |
|---|---|
| `Output/Clocking Report YTD.xlsx` (updated in place) | Payroll |
| Email: YTD Excel attached → `accounts@`, `quintusl@`, `megan@advius.co.za` | Accounts |
| Email: missed clock-out list → same | Accounts / HR |
| Telegram chat `8042233389` — EOD summary + weekly Telegram/WhatsApp | Quintus |
| Dashboard: `https://op-workspace-dashboard.vercel.app/clocking` | Management |

---

## Known failure modes

1. **Symptom:** Hours look halved or doubled in YTD.
   **Cause:** `build_report.py` ran without `--master` (standalone mode wipes accumulator).
   **Fix:** Restore `Output/Clocking Report YTD.xlsx` from OneDrive version history. Re-run `process_inbox.py` only after restoring.

2. **Symptom:** All employees show as "Olympic Paints" or all as "Primeserve".
   **Cause:** Employer classification broken — `SD` prefix = Primeserve (28), all others = Olympic Paints (74).
   **Fix:** Check `EMPLOYER_*` constants in `build_report.py`. Never remove the SD prefix rule.

3. **Symptom:** Shift hours look ~45 min too high.
   **Cause:** `BREAK_DEDUCTION_MINS = 45` not applied, or applied twice.
   **Fix:** Break deduction is applied once per shift in `build_report.py` — never in the dashboard. Verify the constant is set and not duplicated.

4. **Symptom:** Inbox is empty at 07:30 — `process_inbox.py` exits with "Nothing to do."
   **Cause:** Advius email had no attachment, or fetch ran before the email arrived.
   **Fix:** Check Outlook `Reporting/HR` manually and download the attachment to `Inbox/`. Then run `process_inbox.py` manually.

5. **Symptom:** Email went to Outbox but never sent.
   **Cause:** Outlook `Send()` queues only; `process_inbox.py` force-flushes the Outbox, but Outlook must be running.
   **Fix:** Open Outlook and click Send/Receive. `process_inbox.py` already iterates Outbox items after Send — if it keeps failing, check that Outlook is not prompting for a password.

6. **Symptom:** Telegram not received at 17:00.
   **Cause:** `TELEGRAM_BOT_TOKEN` not set as a system environment variable.
   **Fix:** See Step 5 of the daily checklist above.

---

## Manual run

```powershell
# Navigate to scripts folder
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts"

# Full pipeline (fetch + process + email)
C:\Python313\python.exe fetch_clocking_email.py
C:\Python313\python.exe process_inbox.py

# Just rebuild dashboard from existing YTD (no email)
C:\Python313\python.exe gen_dashboard.py

# Process a specific input file manually
C:\Python313\python.exe build_report.py `
  --input  "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\Inbox\Olympic Paints.xlsx" `
  --master "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\Output\Clocking Report YTD.xlsx" `
  --output "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\Output"
```

---

## Scheduled tasks — quick reference

```powershell
# Check all HAVEN task statuses
schtasks /query /fo LIST /v | Select-String "TaskName|Status|Last Run|Last Result" | Select-String -Context 0,0 "HAVEN|haven"

# Run a task manually
Start-ScheduledTask -TaskPath "\Olympic Paints\HAVEN\" -TaskName "Daily Process Inbox"
Start-ScheduledTask -TaskPath "\Olympic Paints\HAVEN\" -TaskName "HAVEN Fetch Clocking Email"
```

---

## Recent incidents

- **2026-06-02:** Two stale tasks (`\HAVEN — Daily Clocking Dashboard Check` and `\HAVEN Clocking Report Daily`) were interfering — killed and disabled. `TELEGRAM_BOT_TOKEN` was not set as a system env var — fixed. `haven_dashboard_check.py` had a duplicate `if __name__ == "__main__":` block — removed.

---

## Related

- Code: `2.Areas/11. HR/Clocking Reports/scripts/`
- Agent profile: `agents/HAVEN.md`
- Old manual runbook (superseded): `2.Areas/11. HR/Clocking Reports/HAVEN - Daily Clocking Report Task.md`
