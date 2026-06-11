# Runbook — SIGMA Vehicle Fleet Dashboard

> **Last verified:** 2026-05-28
> **Owner:** Quintus
> **Criticality:** medium   *(operations-facing; silence = stale dashboard but no customer impact)*

---

## Purpose

Downloads the weekly Netstar GPS trip report emailed by `vigilcloud@netstar.co.za` every Monday, consolidates it with biometric clocking data from HAVEN, and publishes the Fleet Dashboard to GitHub Pages. The dashboard is proxied at `https://olympic-paints-portal.vercel.app/d/vehicles` for authorised staff.

If this job stops running for a week, the fleet dashboard goes stale and the Monday Telegram health check will flag it as overdue.

---

## How it runs

Three staggered tasks run every **Monday morning** under `\Olympic Paints\SIGMA\` in Task Scheduler:

| Time  | Task name | Script |
|-------|-----------|--------|
| 08:00 | Fetch Netstar Email | `fetch_netstar_email.py` |
| 08:05 | Process and Publish Vehicle Dashboard | `run_vehicle_reports.bat` |
| 08:15 | Vehicle Health Check | `striker_vehicle_health_check.py` |

- **Host machine:** Administrator box (this machine)
- **Entry point directory:** `2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts\`
- **Python:** `C:\Python313\python.exe`
- **Register / update tasks:** run `register_sigma_vehicle_tasks.ps1` once as Administrator

---

## Inputs

| Source | Path | Format | Refresh cadence |
|---|---|---|---|
| Netstar email attachment | Downloaded to `2.Areas\9. Supply Chain\Logisitics\Inbox\` | `.xls` | Weekly (Monday) |
| HAVEN Clocking YTD | `2.Areas\11. HR\Clocking Reports\Output\Clocking Report YTD.xlsx` | Excel | Daily (process_inbox.py) |
| GPS VehicleInOut master | `OP Track & Driver Analitics\Output\VehicleInOut_*.xlsx` | Excel | Updated manually when Netstar sends GPS extract |

---

## Outputs

| Destination | Path / URL | Format | Consumer |
|---|---|---|---|
| Consolidated trip master | `Logistics\Inbox\Vehicle In Out Report.xlsx` | Excel | Manual review |
| Fleet Dashboard HTML | `OP Track & Driver Analitics\Dashboard\index.html` | HTML | GitHub Pages |
| GitHub Pages live URL | `https://flomaticauto.github.io/olympic-paints-vehicles/` | HTML | Staff portal `/d/vehicles` |
| Excel Crew & Hours sheet | Injected into `VehicleInOut_*.xlsx` | Excel sheet | Ops manager review |
| Telegram health alert | Chat `8042233389` | Text | Quintus (Mon 08:15) |

---

## Pipeline detail

### Stage 1 — `fetch_netstar_email.py` (08:00)

Connects to Outlook via `win32com`, opens `quintusl@olympicpaints.co.za`, scans the Inbox for emails matching:
- **Sender:** `vigilcloud@netstar.co.za`
- **Subject contains:** `weekly trip report`

Saves the `.xls`/`.xlsx` attachment to `Logistics\Inbox\` using the original Netstar filename (e.g. `Weekly Trip Report 24052026 Multi Vehicles Trip Report.xls`). Skips files already present — safe to re-run.

### Stage 2 — `run_vehicle_reports.bat` (08:05)

Runs two Python scripts in sequence:

1. **`process_vehicle_reports.py`** — scans `Inbox\` for files named `*trip report*.xls*`, consolidates all found into a single `Vehicle In Out Report.xlsx` master, archives source files to `Inbox\Archived\`.
2. **`gen_vehicle_dashboard.py`** — reads the GPS VehicleInOut master from `Output\VehicleInOut_*.xlsx`, cross-references HAVEN clocking data, builds the HTML dashboard, and pushes to GitHub Pages via git.

Also appends a timestamped line to `Inbox\vehicle_report_log.txt` after each stage.

### Stage 3 — `striker_vehicle_health_check.py` (08:15)

Reads `vehicle_report_log.txt` to check:
- Last run was within 7 days (flags `OVERDUE` if not)
- An XLS file exists in `Inbox\`
- The run happened **after** the data file arrived (flags `WARNING — new data arrived but report not re-run` if not)

Sends result to Telegram chat `8042233389`.

---

## Known failure modes

1. **Symptom:** Telegram health check says "Log file not found" or "No .xls/.xlsx files found in Inbox"
   **Cause:** Netstar email did not arrive, or `fetch_netstar_email.py` could not connect to Outlook (Outlook not running, account not loaded).
   **Fix:** Open Outlook, confirm the email from `vigilcloud@netstar.co.za` arrived. If it did, run `fetch_netstar_email.py --days 14` manually to re-scan. If Outlook was closed, ensure it is open before 08:00 on Mondays.

2. **Symptom:** Health check says "WARNING — new data arrived but report not re-run"
   **Cause:** `fetch_netstar_email.py` (08:00) saved the file, but `run_vehicle_reports.bat` (08:05) failed or did not pick it up.
   **Fix:** Run `run_vehicle_reports.bat` manually (see Manual run section).

3. **Symptom:** Dashboard on GitHub Pages shows stale dates / missing months
   **Cause:** `gen_vehicle_dashboard.py` reads from `Output\VehicleInOut_*.xlsx` — the consolidated GPS extract produced by `generate_report.py`. If new weekly XLS files have arrived but `generate_report.py` has not been re-run, the Output file will be stale.
   **Fix:** Run `generate_report.py` against all archived XLS files to rebuild the Output file, then re-run `gen_vehicle_dashboard.py`:
   ```powershell
   cd "...\Scripts"
   # Pass all archived XLS files to regenerate the full dataset:
   C:\Python313\python.exe generate_report.py `
     "...\Inbox\Archived\Weekly Trip Report 10052026 Multi Vehicles Trip Report.xls" `
     "...\Inbox\Archived\Weekly Trip Report 17052026 Multi Vehicles Trip Report.xls"
     # (add any other archived files as arguments)
   # Output saved automatically to Output\VehicleInOut_<dates>.xlsx
   C:\Python313\python.exe gen_vehicle_dashboard.py
   ```
   Note: `generate_report.py` saves its output directly to the `Output\` folder using a date-ranged filename like `VehicleInOut_Mar2026_May2026.xlsx`.

4. **Symptom:** `process_vehicle_reports.py` exits with `UnicodeEncodeError: 'charmap'`
   **Cause:** A `✓`/`✗` Unicode character in a print statement running under Windows cp1252 console (Task Scheduler). Fixed in 2026-05-28 — replace with ASCII `OK`/`ERR` if it reappears in `generate_report.py`.
   **Fix:** Search both scripts for `✓` and `✗` in print statements, replace with plain ASCII.

5. **Symptom:** `fetch_netstar_email.py` saves nothing; no error
   **Cause:** The attachment file was already present in `Inbox\` or `Inbox\Archived\` (duplicate filename from Netstar).
   **Fix:** Check `Inbox\Archived\` for the file. If found, the data was already processed. No action needed.

6. **Symptom:** XLS files accumulate in root `Logisitics\` folder, not processed
   **Cause:** File was manually saved to the wrong folder (parent, not `Inbox\`). `process_vehicle_reports.py` only scans `Inbox\`.
   **Fix:** Move files from `Logisitics\` root into `Logisitics\Inbox\`, then re-run the bat.

7. **Symptom:** Git push in `gen_vehicle_dashboard.py` fails with auth error
   **Cause:** GitHub push credential expired. Push to `FlomaticAuto/olympic-paints-vehicles` uses the git credential store.
   **Fix:** Run `gh auth login --user FlomaticAuto` or `git -C "<Dashboard dir>" push` manually and re-authenticate.

---

## Logs

- **Fetch log:** `C:\Users\Administrator\.claude\logs\sigma-netstar-fetch\fetch_YYYYMMDD_HHMMSS.log`
- **Pipeline log:** `C:\Users\Administrator\.claude\logs\sigma-vehicle\vehicle_reports.log`
- **Health check log:** `C:\Users\Administrator\.claude\logs\sigma-vehicle\health_check.log`
- **Vehicle run log:** `2.Areas\9. Supply Chain\Logisitics\Inbox\vehicle_report_log.txt` (timestamped entries)
- **Task Scheduler last run:** `Get-ScheduledTask -TaskPath "\Olympic Paints\SIGMA\" | Get-ScheduledTaskInfo`

---

## Manual run

### Re-fetch this week's Netstar email
```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts"
C:\Python313\python.exe fetch_netstar_email.py
# Scan further back if email arrived last week:
C:\Python313\python.exe fetch_netstar_email.py --days 14
```

### Re-run full pipeline (consolidate + publish)
```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts"
.\run_vehicle_reports.bat
```

### Re-run individual stages
```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts"
# Stage 1 — consolidate trip reports only
C:\Python313\python.exe process_vehicle_reports.py

# Stage 2 — rebuild and publish dashboard only
C:\Python313\python.exe gen_vehicle_dashboard.py

# Stage 3 — send health check Telegram
C:\Python313\python.exe striker_vehicle_health_check.py
```

### Trigger via Task Scheduler (without waiting for Monday)
```powershell
Start-ScheduledTask -TaskPath "\Olympic Paints\SIGMA\" -TaskName "Fetch Netstar Email"
Start-ScheduledTask -TaskPath "\Olympic Paints\SIGMA\" -TaskName "Process and Publish Vehicle Dashboard"
Start-ScheduledTask -TaskPath "\Olympic Paints\SIGMA\" -TaskName "Vehicle Health Check"
```

### Re-register tasks (after editing the register script)
```powershell
# Run as Administrator
C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts\register_sigma_vehicle_tasks.ps1
```

---

## Recent incidents

- **2026-05-28** — Dashboard had not updated since April. Root cause: `fetch_netstar_email.py` had `OUTLOOK_FOLDER_PATH = []`, causing it to navigate to the account store root (0 items) instead of the `Inbox` subfolder — so all automated fetches silently found nothing. Fixed to `OUTLOOK_FOLDER_PATH = ["Inbox"]`. Fetched the two missing May weekly XLS files (10 May, 17 May), ran `generate_report.py` against all 7 archived files (Mar–May 2026) to produce `VehicleInOut_Mar2026_May2026.xlsx`, then republished dashboard. Also noted: `generate_report.py` throws a benign `UnicodeEncodeError` on the final `→` print character under cp1252 console — workbook is saved correctly before this line; safe to ignore.

---

## Related

- Code: [`fetch_netstar_email.py`](../../../2.Areas/9.%20Supply%20Chain/Logisitics/OP%20Track%20%26%20Driver%20Analitics/Scripts/fetch_netstar_email.py)
- Code: [`run_vehicle_reports.bat`](../../../2.Areas/9.%20Supply%20Chain/Logisitics/OP%20Track%20%26%20Driver%20Analitics/Scripts/run_vehicle_reports.bat)
- Code: [`gen_vehicle_dashboard.py`](../../../2.Areas/9.%20Supply%20Chain/Logisitics/OP%20Track%20%26%20Driver%20Analitics/Scripts/gen_vehicle_dashboard.py)
- Code: [`register_sigma_vehicle_tasks.ps1`](../../../2.Areas/9.%20Supply%20Chain/Logisitics/OP%20Track%20%26%20Driver%20Analitics/Scripts/register_sigma_vehicle_tasks.ps1)
- Agent profile: [`agents/SIGMA.md`](../../../agents/SIGMA.md)
- SOP: [`SIGMA_VEHICLE_REPORT_SOP.md`](../../../2.Areas/9.%20Supply%20Chain/Logisitics/SIGMA_VEHICLE_REPORT_SOP.md)
- Portal proxy: [`/d/vehicles`](https://olympic-paints-portal.vercel.app/d/vehicles) — served via `app/d/[slug]/route.ts`
- Upstream job: [haven-clocking.md](./haven-clocking.md) — provides the clocking YTD data consumed by `gen_vehicle_dashboard.py`
