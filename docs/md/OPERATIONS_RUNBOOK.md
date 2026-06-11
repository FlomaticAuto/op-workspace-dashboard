# Olympic Paints Operations Runbook

Repository structure, deployment procedures, and operational guidelines for the Olympic Paints automation system.

---

## Repository Structure

This is a PARA-organised business operations repository for Olympic Paints (Limpopo, SA). It is not a software project — it is a collection of automation scripts, dashboards, and business documents organised as:

- `0.Inbox/` — incoming files awaiting processing
- `1.Projects/` — active projects (AWS data, automation builds)
- `2.Areas/` — ongoing operational areas (HR, Sales, Supply Chain, Marketing, etc.)
- `3.Resources/` — reference material (SOPs, product info, meeting minutes)

Code lives in two main locations:
- `1.Projects/AWS Data/` — ~~KPI sales dashboard~~ (deprecated 2026-05-25; raw data archive only)
- `2.Areas/11. HR/Clocking Reports/scripts/` — HAVEN HR clocking pipeline

---

## Clocking Pipeline Deployment

### Architecture overview

> **Canonical pipeline definition lives in [`agents/HAVEN.md`](./agents/HAVEN.md) and [`agents/jobs.yaml`](./agents/jobs.yaml).** This section must stay consistent with them.

Hik-Connect biometric system emails a daily `Olympic Paints.xlsx` from `service@mail.hik-partner.com` into the Outlook account `quintusl@olympicpaints.co.za`, folder `Reporting/HR` (Outlook rule), at ~06:00 every morning. A chain of scheduled tasks runs Mon–Fri to pull, process, and publish:

| Time | Task | Script |
|---|---|---|
| 07:00 | Pull Hik-Connect email attachments into Inbox, then process | `extract_hik_connect_emails.py` → `process_inbox.py` |
| 07:30 | Process Inbox (standalone safety net) → YTD master → email → dashboard | `process_inbox.py` → `gen_dashboard.py` |
| 08:45 | Daily dashboard refresh (even if no new file) | `gen_dashboard.py` standalone |
| 08:00 Mon | Weekly Telegram summary + dashboard health check | `haven_dashboard_check.py` |
| 17:00 | End-of-day missed clock-out Telegram summary | `haven_eod_check.py` |

> ⚠️ A second extractor, `fetch_clocking_email.py` (invoked by `Fetch Clocking Email.bat`), duplicates the 07:00 extract job. Only one should be enabled in Task Scheduler — see the OPEN ITEM note in [`agents/HAVEN.md`](./agents/HAVEN.md).

**Dashboard URL:** `https://olympic-paints-portal.vercel.app/d/clocking`
The portal proxies the GitHub Pages dashboard (`https://flomaticauto.github.io/olympic-paints-clocking/`). It fetches fresh on every load — there is only one dashboard, just two access paths.

### Setup & initialization
1. Ensure `Output/` folder exists with `Clocking Report YTD.xlsx` as the master accumulator
2. Ensure `Inbox/` and `Inbox/Archived/` folders exist
3. Configure Outlook win32com for email delivery (Windows only)
4. Set `TELEGRAM_BOT_TOKEN` environment variable; chat ID `8042233389` is hardcoded
5. Run all four `register_*.ps1` scripts once as Administrator to install the scheduled tasks

### Scheduled task registration (run once)

```powershell
cd "...\2.Areas\11. HR\Clocking Reports\scripts"
powershell -ExecutionPolicy Bypass -File register_haven_extractor.ps1
powershell -ExecutionPolicy Bypass -File register_haven_daily_dashboard.ps1
```

### Data flow (automated, daily Mon–Fri)
1. **07:00** — `extract_hik_connect_emails.py` opens Outlook, finds all emails from `service@mail.hik-partner.com`, saves each attachment as `Olympic Paints (DD.MM.YYYY).xlsx` in `Inbox/` (skips if already archived). Then calls `process_inbox.py`.
2. `process_inbox.py` validates each file (must have Sheet0 with data rows from row 5), runs `build_report.py --master` per file, renames dated output back to `Clocking Report YTD.xlsx`, archives input.
3. `build_report.py` applies 45-min break deduction per shift, accumulates into YTD master.
4. Email sent: YTD Excel to `accounts@olympicpaints.co.za`, `quintusl@olympicpaints.co.za`, `megan@advius.co.za`.
5. Daily missed clock-out HTML email sent to same recipients.
6. Long-shift Telegram alert fired if any employee worked > 9h net.
7. `gen_dashboard.py` rebuilds `index.html` (320 KB standalone) and pushes to GitHub Pages.
8. **08:45** — `gen_dashboard.py` standalone run keeps the Yesterday tab current even on days with no new file.

### Manual catch-up (missed days or backlog)

```powershell
# Step 1: pull all unprocessed Hik-Connect emails from Outlook
C:\Python313\python.exe extract_hik_connect_emails.py

# Step 2: if files were already saved to Inbox manually, just run the processor
C:\Python313\python.exe process_inbox.py

# Step 3: rebuild dashboard only (no new data)
C:\Python313\python.exe gen_dashboard.py
```

### Yesterday tab — behaviour by mode

| Situation | Tab shows |
|---|---|
| Previous day was Saturday or Sunday | Blue "Weekend — no clocking records expected" panel, dash instead of % |
| Calendar yesterday has data | Normal: compliance %, missed clock-out table |
| Working day but file not yet received | Amber warning "Data for [date] not yet received" + most recent available day |
| No data at all | Neutral "No clocking data available yet" panel |

The mode is computed in `gen_dashboard.py` Python section (~line 241) using the actual calendar date, not just the last row in the spreadsheet.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Extractor finds 0 emails | Outlook not running or sender filter wrong | Open Outlook, verify sender is `service@mail.hik-partner.com` |
| Files skipped — "Sheet0 has no data rows" | Hik-Connect sent an empty export | Normal — system exports even on days with no punches; these are safely ignored |
| Files named `Olympic Paints (date).xlsx` but no date match | Data date ≠ email received date (by design — Hik sends previous day's data at 06:00) | No action needed; extractor reads the data date from inside the file |
| `already processed` skip for a date | File is in `Inbox/Archived/` from a prior run | No action; extractor is idempotent |
| Dashboard not updating | `gen_dashboard.py` push failed | Check git credentials in the clocking GitHub Pages repo at `Output/` |
| Yesterday tab shows wrong date | 08:45 daily task not registered | Run `register_haven_daily_dashboard.ps1` as Administrator |
| Email not sent | Outlook win32com unavailable | Ensure Outlook is open and `pywin32` installed (`pip install pywin32`) |
| Wrong break deduction | `BREAK_DEDUCTION_MINS` changed | Must be `45` in `build_report.py` — never change without payroll sign-off |
| Duplicate records in YTD | Same file processed twice | `build_report.py --master` deduplicates by employee+date; no manual fix needed |

---

## Portal Deployment (portal.olympicpaints.co.za)

**Location:** `C:\Users\Administrator\olympic-paints-portal` (also synced to `C:\Users\quint\olympic-paints-portal` on the quint box)
**Repo:** `https://github.com/FlomaticAuto/olympic-paints-portal` (private)
**Live URL:** `https://portal.olympicpaints.co.za`
**Vercel project:** `olympic-paints-portal` — team `flomaticautos-projects`
**Vercel project ID:** `prj_XJDVs83Ajb4zzixTR6czZT94PTIV`

### ⚠️ Critical: GitHub pushes do NOT auto-deploy

The portal project is **not connected to the Vercel GitHub integration**. Pushing to `origin/main` updates GitHub but does **not** deploy to the live portal. You must explicitly trigger a Vercel build after every push. This is by design until the one-time GitHub Actions secret is configured (see below).

---

### Standard deployment procedure (use this every time)

```powershell
cd "C:\Users\Administrator\olympic-paints-portal"
.\deploy.ps1 -Message "your commit message"
```

`deploy.ps1` does both steps atomically:
1. Commits any local changes and pushes to GitHub (`origin/main`)
2. Runs `vercel deploy --prod --yes` to build and deploy to `portal.olympicpaints.co.za`

If nothing needs committing (just want to redeploy current `HEAD`):
```powershell
.\deploy.ps1 -SkipPush
```

---

### One-time setup: fix auto-deploy via GitHub Actions

Once this secret is set, every push to `main` from **any machine** will auto-deploy — no manual `vercel deploy` needed.

**Steps (do once from any browser):**

1. Generate a Vercel token:
   - Go to `https://vercel.com/account/tokens`
   - Click **Create** → name it `github-actions-portal` → set no expiry → copy the token

2. Add it to GitHub:
   - Go to `https://github.com/FlomaticAuto/olympic-paints-portal/settings/secrets/actions`
   - Click **New repository secret**
   - Name: `VERCEL_TOKEN`
   - Value: paste the token from step 1

3. Push any commit to `main` — GitHub Actions will deploy automatically via `.github/workflows/deploy.yml`

Once active, the `deploy.ps1` script remains useful for local changes (it still commits + pushes), but the Vercel deploy step will be handled by GitHub Actions automatically.

---

### Prerequisites per machine (one-time)

| Requirement | Install command |
|---|---|
| Node.js | Download from nodejs.org |
| Vercel CLI | `npm install -g vercel` |
| Vercel auth | `vercel login` (opens browser) |
| Project link | `cd portal-dir && vercel link` → select `flomaticautos-projects / olympic-paints-portal` |
| gh CLI | `winget install GitHub.cli` |
| gh auth | `gh auth login --web --hostname github.com` |

---

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Portal shows old version after push | GitHub→Vercel integration not connected | Run `.\deploy.ps1 -SkipPush` from portal dir |
| `vercel deploy` fails with auth error | Vercel CLI not logged in | Run `vercel login` in portal dir |
| `vercel deploy` fails with project error | Project not linked | Run `vercel link` in portal dir, select `flomaticautos-projects / olympic-paints-portal` |
| Push fails (no auth) | gh token expired | Run `gh auth login --web` |
| GitHub Actions "secret not found" | `VERCEL_TOKEN` secret not set | Follow one-time setup steps above |

---

## Vehicle Fleet Dashboard (SIGMA)

**Location:** `2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts\`
**Live URL:** `https://olympic-paints-portal.vercel.app/d/vehicles` (proxied from `https://flomaticauto.github.io/olympic-paints-vehicles/`)

### Data sources
- **Netstar GPS** — weekly `.xls` email from `vigilcloud@netstar.co.za` (Monday mornings)
- **HAVEN clocking** — `2.Areas\11. HR\Clocking Reports\Output\Clocking Report YTD.xlsx`

### Automated pipeline (runs every Monday via Task Scheduler)
1. **08:00** — `fetch_netstar_email.py` connects to Outlook (`quintusl@olympicpaints.co.za` / Inbox), saves the XLS attachment to `Logistics\Inbox\`
2. **08:05** — `run_vehicle_reports.bat` runs `process_vehicle_reports.py` (consolidates XLS into master) then `gen_vehicle_dashboard.py` (rebuilds HTML, pushes to GitHub Pages)
3. **08:15** — `striker_vehicle_health_check.py` checks pipeline health and sends Telegram alert

### Manual catch-up (missed weeks)
```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\2.Areas\9. Supply Chain\Logisitics\OP Track & Driver Analitics\Scripts"
# Step 1: fetch any missing emails (adjust --days as needed)
C:\Python313\python.exe fetch_netstar_email.py --days 30
# Step 2: rebuild consolidated VehicleInOut Excel from all archived files
C:\Python313\python.exe generate_report.py "...\Inbox\Archived\WeeklyTripReport1.xls" "...\Inbox\Archived\WeeklyTripReport2.xls"
# Step 3: regenerate and publish dashboard
C:\Python313\python.exe gen_vehicle_dashboard.py
```

### Critical notes
- `OUTLOOK_FOLDER_PATH = ["Inbox"]` must be set in `fetch_netstar_email.py` — empty list `[]` silently scans the account root (0 items).
- `gen_vehicle_dashboard.py` reads from `Output\VehicleInOut_*.xlsx`, NOT `Inbox\Vehicle In Out Report.xlsx`. Regenerate the Output file with `generate_report.py` if it is stale.
- Full failure mode reference: `3.Resources\19. Runbooks\sigma-vehicle-dashboard.md`

---

## ~~KPI Dashboard Deployment~~ ⚠️ DEPRECATED (2026-05-25)

> This workflow has been discontinued. Do not run `build_kpi_dashboard.py`. See `1.Projects/AWS Data/DEPRECATED.md`.

### Setup & initialization
1. Verify `1.Projects/KPI Report/Weekly Progress/` exists and contains latest `Weekly_Sales_Report__*.pdf`
2. Set GitHub Pages repo URL in `build_kpi_dashboard.py`
3. Configure workspace dashboard output path for `kpi_status.json` (default: `C:\Users\quint\workspace-dashboard\`)

### Weekly update procedure
1. **Export new PDF from QuickSight:** Download latest `Weekly_Sales_Report__*.pdf` into `1.Projects/KPI Report/Weekly Progress/`
2. **Extract data manually:** Open PDF, identify these fields:
   - Week number and date
   - MTD sales, target, and % of target
   - Total debtors, 90-day debtors, % overdue > 60 days
   - % above rock-bottom average
   - Rep-level sales, targets, and % (for AC, AP, BV, NP, BM)
   - YoY monthly actuals (add current month only)
   - Product group rock-bottom percentages
3. **Update `build_kpi_dashboard.py`:** Edit the data block at the top with extracted values
4. **Run:** `python build_kpi_dashboard.py`
5. **Verify:** Check `index.html` generated and pushed to GitHub Pages at `https://flomaticauto.github.io/olympic-paints-kpi/`
6. **Confirm workspace dashboard:** Check `kpi_status.json` written to workspace output folder

### Output destinations
- GitHub Pages: `https://flomaticauto.github.io/olympic-paints-kpi/`
- Workspace dashboard: `C:\Users\quint\workspace-dashboard\kpi_status.json`
- Repository: `1.Projects/AWS Data/index.html`

### Troubleshooting
- **PDF text extraction fails**: QuickSight renders as images — manual entry is the only option
- **Dashboard not live**: Verify GitHub repo is public and Pages is enabled
- **Wrong rep codes**: Always use AC, AP, BV, NP, BM (see SCRIPTS_REFERENCE.md for full names)
- **Historical data missing**: Ensure `YOY` list includes all months (add only current month each week, keep past months intact)

---

## General operational guidelines

### Notifications
All agent task completions send a Telegram message to chat ID `8042233389`. Individual scripts may send richer summaries.

### Employer splits
Two legal entities share workforce data:
- **Olympic Paints** — 74 employees (employee IDs not starting with `SD`)
- **Primeserve** — 28 employees (employee IDs starting with `SD`)

All dashboards, reports, and analyses split metrics by employer. Do not aggregate across employers without explicit approval.

### Data quality checks
Before processing biometric data:
- Verify all employee IDs are present in the master roster
- Check for duplicate punches or illogical clock patterns
- Ensure date ranges are continuous (no missing weeks)
- Flag any employees with zero hours or excessive hours (>60/week)

### Backup and archival
- Keep dated outputs (e.g. `Clocking Report (01.05.2026).xlsx`) in archive for 6 months
- Git commit message format: `[YTD] Clocking Report — [date] — [employee count]`
- Maintain separate branches for staging and production GitHub Pages repos
