# SIGMA SOP: Vehicle In-Out Report Generation

## Overview
Automatically consolidate Trip Report XLS files dropped into the Supply Chain Logistics Inbox and maintain a single master "Vehicle In Out Report.xlsx" file.

## Trigger
Files are dropped into:
```
2.Areas\9. Supply Chain\Logisitics\Inbox\
```

## Process

### Step 1: Run the Consolidation Workflow
When Trip Report files appear in the Inbox, execute:

```bash
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\Inbox"
python process_vehicle_reports.py
```

### Step 2: Workflow Automation (What Happens)

The script automatically:

1. **Scans** for Trip Report files across **both** `Inbox/` and `Inbox/Archived/`
   — the report is rebuilt from the full history every run, not just the latest week.
2. **De-duplicates** legs (`drop_duplicates`): identical legs from overlapping
   exports (e.g. a monthly file plus a weekly file covering the same days) are
   collapsed, while complementary legs from partial-day exports are kept — so no
   day is double-counted and no day is lost.
3. **Filters** to the 7 tracked fleet plates and **consolidates** using the
   generate_report logic (summary sheet + per-vehicle tabs + 6 analytics sheets).
4. **Saves** the canonical, period-named workbook to
   `OP Track & Driver Analitics/Output/VehicleInOut_<MonYYYY>_<MonYYYY>.xlsx`
   — **this is the file `gen_vehicle_dashboard.py` reads.**
5. **Refreshes** the Inbox copy `Vehicle In Out Report.xlsx` with the same full content.
6. **Archives** this week's new source Trip Report files to `Inbox/Archived/`.
7. **Cleans up** any stray non-master XLS files from the Inbox folder.

> ⚠️ The dashboard reads `Output/VehicleInOut_*.xlsx` (newest by mtime). Earlier
> period files are left in place as history — `find_latest_excel()` always selects
> the most recent. Do **not** point the dashboard at the Inbox copy.

### Step 3: Output Location
- **Dashboard source (canonical):** `OP Track & Driver Analitics/Output/VehicleInOut_<period>.xlsx`
- **Inbox copy (same content):** `Inbox/Vehicle In Out Report.xlsx`

## Folder Structure

```
Inbox/
├── process_vehicle_reports.py          (this workflow script)
├── Vehicle In Out Report.xlsx          (master output — always one file)
└── Archived/
    ├── TripReport_Jan2026.xlsx         (processed source files)
    └── TripReport_Feb2026.xlsx
```

## Notes

- **Only one output file** exists at any time: `Vehicle In Out Report.xlsx`
- Source Trip Report files are automatically moved to `Archived/` after processing
- The master file is **always updated** — previous versions are replaced
- The script requires Python and pandas (ensure environment is set up)
- Address mappings and the core generate_report module live in:
  ```
  OP Track & Driver Analitics/Scripts/
  ```

## Automation (Live — Monday 08:00)

Three Task Scheduler tasks run every Monday under `\Olympic Paints\SIGMA\`:

| Time  | Task | Script |
|-------|------|--------|
| 08:00 | Fetch Netstar Email | `fetch_netstar_email.py` — scans `quintusl@olympicpaints.co.za` Outlook for emails from `vigilcloud@netstar.co.za` with subject "Weekly Trip Report", saves `.xls` attachment to `Inbox/` |
| 08:05 | Process and Publish | `run_vehicle_reports.bat` — consolidates XLS → master Excel, rebuilds Fleet Dashboard, pushes to GitHub Pages |
| 08:15 | Vehicle Health Check | `striker_vehicle_health_check.py` — validates run freshness and data sync, sends Telegram alert to `8042233389` |

To register or update the tasks:
```powershell
# Run as Administrator
.\register_sigma_vehicle_tasks.ps1
```

To trigger the fetch manually:
```powershell
Start-ScheduledTask -TaskPath "\Olympic Paints\SIGMA\" -TaskName "Fetch Netstar Email"
```
