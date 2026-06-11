# Olympic Paints Scripts Reference

Automation scripts for Olympic Paints HR clocking pipeline and KPI dashboards.

---

## Clocking Report Pipeline (HAVEN)

**Flow:** Advius biometric export → `build_report.py` → `Clocking Report YTD.xlsx` → `gen_dashboard.py` → `index.html` → GitHub Pages

### Key scripts

| Script | Purpose | How to run |
|---|---|---|
| `build_report.py` | Processes raw Advius punch export into YTD Excel workbook | `python build_report.py --input <Transaction*.xlsx> --master <YTD.xlsx> --output <folder>` |
| `process_inbox.py` | One-shot batch processor: scans Inbox, calls `build_report.py`, renames output to YTD master, emails result | `python process_inbox.py` |
| `gen_dashboard.py` | Reads `Clocking Report YTD.xlsx`, builds standalone HTML dashboard, pushes to GitHub Pages | `python gen_dashboard.py` |
| `haven_watcher.py` | File-system watcher (watchdog): auto-triggers `build_report.py` when a new `.xlsx` lands in Inbox | `python haven_watcher.py` (runs continuously) |
| `haven_dashboard_check.py` | Weekly scheduled check: regenerates dashboard, sends Telegram summary to Quintus | `python haven_dashboard_check.py` (run via Task Scheduler, Mondays 08:00) |

### Critical rules
- **Always pass `--master`** to `build_report.py`. Never run in standalone mode — it must accumulate against the existing YTD master.
- **45-minute break deduction** (`BREAK_DEDUCTION_MINS = 45`) is applied to every worked shift for every employee, no exceptions.
- **Employer classification:** Employee IDs starting with `SD` → Primeserve; all others → Olympic Paints.
- The YTD master file is always named `Clocking Report YTD.xlsx` and lives in `Output/`. Dated outputs (e.g. `Clocking Report (01.05.2026).xlsx`) are transient and must be renamed to the YTD master after processing.

### Key paths
```
Output/Clocking Report YTD.xlsx        ← master accumulator (input + output for build_report.py)
Output/index.html                      ← GitHub Pages source (git repo at Output/)
Inbox/                                 ← drop zone for new Advius exports
Inbox/Archived/                        ← processed inputs moved here automatically
```

### Email
`process_inbox.py` sends two emails via Outlook (win32com) after every successful run:
1. YTD Excel attached → `accounts@olympicpaints.co.za`, `quintusl@olympicpaints.co.za`
2. Daily missed clock-out HTML email → same recipients

### Telegram notifications
`haven_dashboard_check.py` sends to bot token in script, chat ID `8042233389`.

### Dashboard (GitHub Pages)
Live URL: `https://flomaticauto.github.io/olympic-paints-clocking/`
Tabs: Overview · Yesterday · Daily Attendance · Departments · Weekly Hours · Missing Clock Out

The **Yesterday tab** shows the most recent working day's missed clock-outs. It is data-driven from `miss_table` filtered to the latest date.

---

## ~~KPI Sales Dashboard~~ ⚠️ DEPRECATED (2026-05-25)

> This workflow has been discontinued. Do not run this script. See `1.Projects/AWS Data/DEPRECATED.md`.

**Location:** `1.Projects/AWS Data/build_kpi_dashboard.py`
**Run:** ~~`python build_kpi_dashboard.py`~~
**Live URL:** ~~`https://flomaticauto.github.io/olympic-paints-kpi/`~~ (no longer active)

### Data model
All figures are **manually entered** at the top of `build_kpi_dashboard.py` from QuickSight-generated PDFs. QuickSight renders charts as images so text extraction is not possible — the data block must be updated by hand each week.

**Data source:** `1.Projects/KPI Report/Weekly Progress/Weekly_Sales_Report__*.pdf` only.
**Ignore:** `Daily_Sales_Report_P_*.pdf` — this is a debtor aging view for accounts, not a KPI data source.

### Weekly update procedure
1. Drop new `Weekly_Sales_Report__*.pdf` files into `1.Projects/KPI Report/Weekly Progress/`
2. Open the PDFs and update the data block at the top of `build_kpi_dashboard.py`:
   - `REPORT_WEEK`, `REPORT_DATE`
   - `MTD_SALES`, `MTD_TARGET`, `MTD_PCT_TARGET`
   - `DEBTORS_TOTAL`, `DEBTORS_90D`, `OVERDUE_60D_PCT`
   - `ABOVE_RB_AVG`
   - `REPS` list (sales, target, pct per rep)
   - `YOY` list (update current month's actual)
   - `RB_BY_PRODUCT` list (rock bottom % per product group)
3. Run `python build_kpi_dashboard.py` — it writes `index.html` and pushes to GitHub

### Rep codes
`AC` = Aboo Cassim · `AP` = Amit Patel · `BV` = Bhadresh Vallabh · `NP` = Nikhil Panchal · `BM` = Byron Minnie

### Output
- `index.html` pushed to the KPI GitHub Pages repo
- `kpi_status.json` written to `C:\Users\quint\workspace-dashboard\` for the workspace dashboard

---

## Vehicle Fleet Pipeline (SIGMA)

**Flow:** Netstar email (Outlook) → `fetch_netstar_email.py` → `Inbox\*.xls` → `generate_report.py` → `Output\VehicleInOut_*.xlsx` → `gen_vehicle_dashboard.py` → GitHub Pages → portal `/d/vehicles`

**Location:** `2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts\`

### Key scripts

| Script | Purpose | How to run |
|---|---|---|
| `fetch_netstar_email.py` | Connects to Outlook via win32com; saves weekly XLS attachments from `vigilcloud@netstar.co.za` to `Logistics\Inbox\` | `python fetch_netstar_email.py` (scans last 8 days) or `--days 30` / `--all` |
| `generate_report.py` | Consolidates one or more Netstar XLS files into a canonical `VehicleInOut_<dates>.xlsx` workbook in `Output\` | `python generate_report.py file1.xls file2.xls ...` |
| `process_vehicle_reports.py` | Wrapper: scans `Inbox\` for trip XLS files, calls `generate_report` logic, saves `Vehicle In Out Report.xlsx` to `Inbox\`, archives source files | `python process_vehicle_reports.py` |
| `gen_vehicle_dashboard.py` | Reads `Output\VehicleInOut_*.xlsx`, cross-references HAVEN clocking, builds HTML dashboard, pushes to GitHub Pages | `python gen_vehicle_dashboard.py` |
| `run_vehicle_reports.bat` | Full pipeline wrapper: runs `process_vehicle_reports.py` then `gen_vehicle_dashboard.py` | `.\run_vehicle_reports.bat` |
| `striker_vehicle_health_check.py` | Reads `vehicle_report_log.txt`, sends Telegram alert if pipeline is overdue | `python striker_vehicle_health_check.py` (Mon 08:15 via Task Scheduler) |

### Critical rules
- **`OUTLOOK_FOLDER_PATH = ["Inbox"]`** must be set in `fetch_netstar_email.py` — if set to `[]` it navigates to the account store root (0 items) and saves nothing silently.
- **`generate_report.py` is the canonical VehicleInOut builder** — always pass all archived XLS files as arguments when rebuilding for missed months. It saves to `Output\VehicleInOut_<dates>.xlsx` automatically.
- **`gen_vehicle_dashboard.py` reads `Output\VehicleInOut_*.xlsx`** — not the `Vehicle In Out Report.xlsx` in Inbox. If the Output file is stale, re-run `generate_report.py` first.
- The trailing `UnicodeEncodeError` on `→` in `generate_report.py` is benign — the workbook is saved before that line. Ignore it.
- Shaun Fazile (MJ35FPGP driver) has no HAVEN biometric match — this is expected and will show as unmatched in the dashboard crew tab.

### Key paths
```
2.Areas\9. Supply Chain\Logisitics\Inbox\                        <- drop zone for new Netstar XLS
2.Areas\9. Supply Chain\Logisitics\Inbox\Archived\               <- processed source files
OP Track & Driver Analitics\Output\VehicleInOut_*.xlsx           <- dashboard data source
OP Track & Driver Analitics\Dashboard\index.html                 <- published HTML
OP Track & Driver Analitics\Scripts\address_mappings.json        <- factory address normalisation rules
```

### Scheduled tasks (Task Scheduler — `\Olympic Paints\SIGMA\`)
| Time (Monday) | Task | Script |
|---|---|---|
| 08:00 | Fetch Netstar Email | `fetch_netstar_email.py` |
| 08:05 | Process and Publish Vehicle Dashboard | `run_vehicle_reports.bat` |
| 08:15 | Vehicle Health Check | `striker_vehicle_health_check.py` |

### Dashboard
- **GitHub Pages:** `https://flomaticauto.github.io/olympic-paints-vehicles/`
- **Portal proxy:** `https://olympic-paints-portal.vercel.app/d/vehicles`

### Full runbook
See `3.Resources\19. Runbooks\sigma-vehicle-dashboard.md` for failure modes, manual run procedures, and incident history.

---

## Notifications
All agent task completions send a Telegram message to chat ID `8042233389`. The Stop hook in Claude Code settings handles baseline notifications; individual scripts may send richer summaries directly.

## Employers
Two legal entities share the same workforce:
- **Olympic Paints** — 74 employees (IDs not starting with SD)
- **Primeserve** — 28 employees (IDs starting with SD)

All reporting, dashboards, and emails split metrics by employer.
