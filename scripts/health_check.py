"""
health_check.py — Olympic Paints Updates / Health Dashboard
============================================================
Runs after every scheduled job. For each job in MANIFEST:
  - queries Task Scheduler for last run / next run / last result
  - checks every input file's mtime against expected freshness window
  - checks the output file/dashboard mtime
  - computes an overall PASS / WARN / FAIL

Writes:
  C:\\Users\\quint\\workspace-dashboard\\updates.html       (the live page)
  C:\\Users\\quint\\workspace-dashboard\\updates_status.json (machine-readable summary)

Pushes both to the op-workspace-dashboard repo. Vercel auto-deploys from
the GitHub repo on push (GitHub Pages mirror was disabled 2026-05-17).
Live URL: https://op-workspace-dashboard.vercel.app/updates
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Local AV inspects TLS — use system CA store so Telegram API HTTPS works.
try:
    import truststore  # type: ignore
    truststore.inject_into_ssl()
except Exception:
    pass

WORKSPACE = Path(r"C:\Users\quint\workspace-dashboard")
# The Updates tab on index.html consumes this file via fetch('updates_status.json').
# Standalone updates.html was deprecated 2026-05-17 — only JSON now.
OUT_JSON = WORKSPACE / "updates_status.json"
ALERT_STATE = WORKSPACE / "updates_alert_state.json"

PULSE_BASE = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE — Sales & Ops Manager")
PULSE_OUTPUT = PULSE_BASE / "output" / "site"
PULSE_DATA = PULSE_BASE / "data"

OP_BASE = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
SALES_BASE = OP_BASE / "3.Resources" / "16.Sales and Other data"
AWS_BASE = OP_BASE / "1.Projects" / "AWS Data"
HR_BASE = OP_BASE / "2.Areas" / "11. HR" / "Clocking Reports"
LOGISTICS_BASE = OP_BASE / "2.Areas" / "9. Supply Chain" / "Logisitics" / "OP Track & Driver Analitics"

# ── MANIFEST ─────────────────────────────────────────────────────────────────
# Cadence labels are descriptive; max_age_hours drives staleness logic.
MANIFEST = [
    {
        "id": "sales_dashboard",
        "agent": "PRISM",
        "name": "Sales Performance Dashboard",
        "task": "OlympicPaints_Sales_Dashboard_Refresh",
        "cadence": "Daily · 07:15",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Sales Invoices (parquet)",   "path": SALES_BASE / "Sales_Invoices_All.parquet",                              "max_age_hours": "business_day", "source": "Daily ledger build"},
            {"label": "Debtors Age Analysis",       "path": SALES_BASE / "Pad" / "debtors_age_analysis.csv",                        "max_age_hours": "business_day", "source": "PAD daily export"},
            {"label": "Sales Orders Outstanding",   "path": SALES_BASE / "Pad" / "sales_order_outstanding.csv",                     "max_age_hours": "business_day", "source": "PAD daily export"},
            {"label": "Zoho Meetings",              "path": SALES_BASE / "Zoho" / "Meetings_Report_AWS.xlsx",                       "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Zoho Lead Tracking",         "path": SALES_BASE / "Zoho" / "OP_Lead_Tracking.csv",                       "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Merchandising Visits",       "path": SALES_BASE / "Zoho" / "Meetings_Report_AWS_Merchandising.xlsx",         "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Delivery Details",           "path": SALES_BASE / "Manual" / "Delivery Details_Updated_2304.xlsx",           "max_age_hours": None, "source": "Manual reference"},
            {"label": "Product Categories",         "path": SALES_BASE / "Manual" / "Product Categories_05052026.xlsx",             "max_age_hours": None, "source": "Manual reference"},
            {"label": "New Stores Q1/2026",         "path": SALES_BASE / "Manual" / "New Stores Added By Reps_Quater1_2026.xlsx",   "max_age_hours": None, "source": "Manual quarterly"},
        ],
        "output": {"label": "Sales Dashboard index.html", "path": SALES_BASE / "Sales Dashboard" / "index.html", "max_age_hours": 30},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-sales/",
    },
    {
        "id": "kpi_rep_dashboards",
        "agent": "PRISM",
        "name": "Per-Rep KPI Dashboards (AC · AP · BV · NP · BM)",
        "task": "OlympicPaints_KPI_Dashboard_Update",
        "cadence": "Daily · 07:00",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Sales Invoices (parquet)",   "path": SALES_BASE / "Sales_Invoices_All.parquet", "max_age_hours": "business_day", "source": "Daily ledger build"},
        ],
        "output": {"label": "KPI Dashboard.html", "path": AWS_BASE / "index.html", "max_age_hours": 30},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-kpi-ac/",
    },
    {
        "id": "ecommerce_dashboard",
        "agent": "PRISM",
        "name": "E-Commerce Dashboard",
        "task": "OlympicPaints_Ecommerce_Dashboard_Refresh",
        "cadence": "Daily · 08:15",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Woocommerce_Transactions.csv", "path": SALES_BASE / "Manual" / "Woocommerce_Transactions.csv", "max_age_hours": 30, "source": "WooCommerce export"},
        ],
        "output": {"label": "build_ecommerce_dashboard.py", "path": AWS_BASE / "build_ecommerce_dashboard.py", "max_age_hours": None},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-ecommerce/",
    },
    {
        "id": "ecommerce_email",
        "agent": "PRISM",
        "name": "E-Commerce Email Digest",
        "task": "OlympicPaints_EmailECommerceDashboard",
        "cadence": "Daily morning",
        "max_age_hours": 30,
        "inputs": [],
        "output": {"label": "run_email_ecommerce.bat", "path": AWS_BASE / "run_email_ecommerce.bat", "max_age_hours": None},
        "dashboard_url": None,
    },
    {
        "id": "haven_clocking",
        "agent": "HAVEN",
        "name": "HAVEN Clocking Report (Process Inbox)",
        "task": "HAVEN Clocking Report Daily",
        "cadence": "Daily · 07:30",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Inbox folder",       "path": HR_BASE / "Inbox", "max_age_hours": None, "source": "Advius drop"},
        ],
        "output": {"label": "Clocking Report YTD.xlsx", "path": HR_BASE / "Output" / "Clocking Report YTD.xlsx", "max_age_hours": 30},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-clocking/",
    },
    {
        "id": "haven_dashboard_check",
        "agent": "HAVEN",
        "name": "HAVEN Dashboard Check (regenerate + Telegram)",
        "task": "HAVEN — Daily Clocking Dashboard Check",
        "cadence": "Daily · 08:00",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Clocking Report YTD.xlsx", "path": HR_BASE / "Output" / "Clocking Report YTD.xlsx", "max_age_hours": 30, "source": "build_report.py"},
        ],
        "output": {"label": "index.html (clocking)", "path": HR_BASE / "Output" / "index.html", "max_age_hours": 30},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-clocking/",
    },
    {
        "id": "vehicle_report",
        "agent": "SIGMA",
        "name": "Vehicle In-Out Report",
        "task": "Vehicle Report Weekly",
        "cadence": "Weekly · Mon",
        "max_age_hours": 192,
        "inputs": [],
        "output": {"label": "gen_vehicle_dashboard.py", "path": LOGISTICS_BASE / "Scripts" / "gen_vehicle_dashboard.py", "max_age_hours": None},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-vehicles/",
    },
    {
        "id": "vehicle_health",
        "agent": "STRIKER",
        "name": "STRIKER Vehicle Report Health Check",
        "task": "STRIKER — Vehicle Report Health Check",
        "cadence": "Weekly · Mon",
        "max_age_hours": 192,
        "inputs": [],
        "output": {"label": "striker_vehicle_health_check.py", "path": LOGISTICS_BASE / "Scripts" / "striker_vehicle_health_check.py", "max_age_hours": None},
        "dashboard_url": None,
    },
    {
        "id": "kaizen_sync",
        "agent": "VAULT",
        "name": "Kaizen Daily Sync",
        "task": "Olympic Paints - Kaizen Daily Sync",
        "cadence": "Daily · 07:30",
        "max_age_hours": 30,
        "inputs": [],
        "output": {"label": "kaizen_status_log.json", "path": WORKSPACE / "kaizen_status_log.json", "max_age_hours": 36},
        "dashboard_url": None,
    },
    {
        "id": "workspace_health",
        "agent": "PRISM",
        "name": "Workspace Weekly Health Report",
        "task": "OlympicPaints_Workspace_Health_Report",
        "cadence": "Weekly · Fri 16:00",
        "max_age_hours": 192,
        "inputs": [],
        "output": {"label": "health-report.html", "path": WORKSPACE / "health-report.html", "max_age_hours": 192},
        "dashboard_url": "https://op-workspace-dashboard.vercel.app/health-report",
    },
    {
        "id": "friday_sales_meeting",
        "agent": "STRIKER",
        "name": "Friday Sales Meeting Pack",
        "task": "OlympicPaints_Friday_Sales_Meeting",
        "cadence": "Weekly · Fri",
        "max_age_hours": 192,
        "inputs": [],
        "output": {"label": "run_friday_sales_meeting.bat", "path": SALES_BASE / "run_friday_sales_meeting.bat", "max_age_hours": None},
        "dashboard_url": None,
    },
    {
        "id": "meeting_extractor",
        "agent": "VAULT",
        "name": "Meeting Minutes Extractor",
        "task": "Olympic Paints - Meeting Minutes Extractor",
        "cadence": "Daily · 07:00",
        "max_age_hours": 30,
        "inputs": [],
        "output": {"label": "logs folder (most recent)", "path": OP_BASE / "logs", "max_age_hours": 30},
        "dashboard_url": None,
    },
    {
        "id": "vault_meeting_extraction",
        "agent": "VAULT",
        "name": "VAULT Meeting Extraction (Notion tasks)",
        "task": "VAULT Meeting Extraction Daily",
        "cadence": "Daily · 07:00",
        "max_age_hours": 30,
        "inputs": [],
        "output": {"label": "logs folder (most recent)", "path": OP_BASE / "logs", "max_age_hours": 30},
        "dashboard_url": None,
    },
    {
        "id": "cso_intelligence",
        "agent": "PRISM",
        "name": "CSO Strategic Intelligence Build",
        "task": "CSO-Intelligence-Data",
        "cadence": "Daily morning",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Sales Invoices (parquet)", "path": SALES_BASE / "Sales_Invoices_All.parquet", "max_age_hours": "business_day", "source": "Daily ledger build"},
        ],
        "output": {"label": "intelligence_data.json", "path": Path(r"C:\Users\quint\olympic-paints-cso-insights\intelligence_data.json"), "max_age_hours": 30},
        "dashboard_url": "https://flomaticauto.github.io/olympic-paints-cso-insights/",
    },
    {
        "id": "portal_trigger_server",
        "agent": "VAULT",
        "name": "Portal Trigger Server (localhost:8765)",
        "task": "OlympicPortalTriggerServer",
        "cadence": "Continuous",
        "max_age_hours": None,
        "inputs": [],
        "output": {"label": "portal_trigger_server.py", "path": WORKSPACE / "scripts" / "portal_trigger_server.py", "max_age_hours": None},
        "dashboard_url": None,
    },
    # ── PULSE — Sales & Ops Manager (8 weekday/weekly tasks) ────────────────
    # All read the same shared data: Meetings_Report_AWS.xlsx + planned_week.json + pulse_cycle.parquet.
    # Outputs vary per job (see each entry).
    {
        "id": "pulse_daily_mailer",
        "agent": "PULSE",
        "name": "PULSE Daily Mailer (per-rep brief + Telegram)",
        "task": "PULSE — Daily Mailer",
        "cadence": "Daily · Mon-Fri 09:00",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Zoho Meetings",      "path": SALES_BASE / "Zoho" / "Meetings_Report_AWS.xlsx",   "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Planned week",       "path": PULSE_DATA / "planned_week.json",                   "max_age_hours": 192,            "source": "PULSE planner"},
            {"label": "Cycle parquet",      "path": PULSE_DATA / "pulse_cycle.parquet",                 "max_age_hours": None,           "source": "PULSE cycle loader"},
        ],
        "output": {"label": "output/site/daily/<date>/<rep>.html", "path": PULSE_OUTPUT / "daily", "max_age_hours": 30},
        "dashboard_url": "https://olympic-paints-pulse-web.vercel.app/",
    },
    {
        "id": "pulse_leaderboard",
        "agent": "PULSE",
        "name": "PULSE Leaderboard (weekday refresh)",
        "task": "PULSE — Leaderboard",
        "cadence": "Daily · Mon-Fri 09:15",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Zoho Meetings",      "path": SALES_BASE / "Zoho" / "Meetings_Report_AWS.xlsx",   "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Planned week",       "path": PULSE_DATA / "planned_week.json",                   "max_age_hours": 192,            "source": "PULSE planner"},
        ],
        "output": {"label": "output/site/index.html (leaderboard)", "path": PULSE_OUTPUT / "index.html", "max_age_hours": 30},
        "dashboard_url": "https://olympic-paints-pulse-web.vercel.app/",
    },
    {
        "id": "pulse_web_snapshots",
        "agent": "PULSE",
        "name": "PULSE Web Snapshots (Vercel push)",
        "task": "PULSE — Web Snapshots",
        "cadence": "Daily · Mon-Fri 09:20",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Daily site folder",  "path": PULSE_OUTPUT / "daily",                              "max_age_hours": 30,             "source": "pulse_daily.py"},
            {"label": "Scorecard folder",   "path": PULSE_OUTPUT / "scorecard",                          "max_age_hours": 384,            "source": "pulse_scorecard.py"},
        ],
        "output": {"label": "output/site (committed to Vercel)", "path": PULSE_OUTPUT, "max_age_hours": 30},
        "dashboard_url": "https://olympic-paints-pulse-web.vercel.app/",
    },
    {
        "id": "pulse_ack_escalation",
        "agent": "PULSE",
        "name": "PULSE Ack Escalation (afternoon nudge)",
        "task": "PULSE — Ack Escalation",
        "cadence": "Daily · Mon-Fri 17:15",
        "max_age_hours": 30,
        "inputs": [
            {"label": "Daily site folder",  "path": PULSE_OUTPUT / "daily",                              "max_age_hours": 30,             "source": "pulse_daily.py"},
        ],
        "output": {"label": "pulse_escalation.py", "path": PULSE_BASE / "scripts" / "pulse_escalation.py", "max_age_hours": None},
        "dashboard_url": None,
    },
    {
        "id": "pulse_intake_escalation",
        "agent": "PULSE",
        "name": "PULSE Intake Escalation (Fri morning)",
        "task": "PULSE — Intake Escalation",
        "cadence": "Weekly · Fri 09:00",
        "max_age_hours": 192,
        "inputs": [
            {"label": "Planned week",       "path": PULSE_DATA / "planned_week.json",                   "max_age_hours": 192,            "source": "PULSE planner"},
        ],
        "output": {"label": "pulse_intake_escalation.py", "path": PULSE_BASE / "scripts" / "pulse_intake_escalation.py", "max_age_hours": None},
        "dashboard_url": None,
    },
    {
        "id": "pulse_scorecard",
        "agent": "PULSE",
        "name": "PULSE Bi-Weekly Scorecard",
        "task": "PULSE — Scorecard",
        "cadence": "Weekly · Mon 07:00",
        "max_age_hours": 192,
        "inputs": [
            {"label": "Zoho Meetings",      "path": SALES_BASE / "Zoho" / "Meetings_Report_AWS.xlsx",   "max_age_hours": "business_day", "source": "Zoho export"},
            {"label": "Cycle parquet",      "path": PULSE_DATA / "pulse_cycle.parquet",                 "max_age_hours": None,           "source": "PULSE cycle loader"},
        ],
        "output": {"label": "output/site/scorecard/index.html", "path": PULSE_OUTPUT / "scorecard" / "index.html", "max_age_hours": 192},
        "dashboard_url": "https://olympic-paints-pulse-web.vercel.app/scorecard/",
    },
    {
        "id": "pulse_cycle_loader",
        "agent": "PULSE",
        "name": "PULSE Cycle Loader (Sunday)",
        "task": "PULSE — Cycle Loader",
        "cadence": "Weekly · Sun 18:00",
        "max_age_hours": 192,
        "inputs": [
            {"label": "Sales Invoices (parquet)", "path": SALES_BASE / "Sales_Invoices_All.parquet",     "max_age_hours": "business_day", "source": "Daily ledger build"},
        ],
        "output": {"label": "pulse_cycle.parquet", "path": PULSE_DATA / "pulse_cycle.parquet", "max_age_hours": 192},
        "dashboard_url": None,
    },
    {
        "id": "pulse_planner",
        "agent": "PULSE",
        "name": "PULSE Planner (Sun evening — sets next week)",
        "task": "PULSE — Planner",
        "cadence": "Weekly · Sun 19:00",
        "max_age_hours": 192,
        "inputs": [
            {"label": "Cycle parquet",      "path": PULSE_DATA / "pulse_cycle.parquet",                 "max_age_hours": 192,            "source": "PULSE cycle loader"},
        ],
        "output": {"label": "planned_week.json", "path": PULSE_DATA / "planned_week.json", "max_age_hours": 192},
        "dashboard_url": None,
    },
]


# ── Task Scheduler query ─────────────────────────────────────────────────────

def query_task_scheduler():
    """Return dict of {task_name: {state, last_run, next_run, last_result}} via PowerShell."""
    ps = (
        r"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        r"Get-ScheduledTask | ForEach-Object { "
        r"  $i = Get-ScheduledTaskInfo $_; "
        r"  $lr = if ($i.LastRunTime -and $i.LastRunTime.Year -gt 1999) { $i.LastRunTime.ToString('yyyy-MM-ddTHH:mm:ss') } else { $null }; "
        r"  $nr = if ($i.NextRunTime -and $i.NextRunTime.Year -gt 1999) { $i.NextRunTime.ToString('yyyy-MM-ddTHH:mm:ss') } else { $null }; "
        r"  [PSCustomObject]@{ "
        r"    Name = $_.TaskName; "
        r"    State = $_.State.ToString(); "
        r"    LastRun = $lr; "
        r"    NextRun = $nr; "
        r"    LastResult = $i.LastTaskResult "
        r"  } "
        r"} | ConvertTo-Json -Depth 3 -Compress"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=30, encoding="utf-8",
        )
        data = json.loads(r.stdout)
        if isinstance(data, dict):
            data = [data]
        return {row["Name"]: row for row in data if row.get("Name")}
    except Exception as e:
        print(f"[warn] task scheduler query failed: {e}", file=sys.stderr)
        return {}


# ── Weekend-aware staleness ──────────────────────────────────────────────────

def business_day_max_age_hours() -> float:
    """Return max_age_hours for files that are only updated Mon–Fri.

    Rules:
      - Sat / Sun: data was last written on Friday — allow up to end-of-day
        Sunday (i.e. how many hours since Friday 08:00).
      - Mon–Fri: must have been written since the *previous* business day 08:00.
        (Mon: since Fri 08:00; Tue–Fri: since yesterday 08:00.)
    """
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon … 6=Sun
    if weekday == 5:  # Saturday — deadline = last Friday 08:00
        days_back = 1
    elif weekday == 6:  # Sunday — deadline = last Friday 08:00
        days_back = 2
    elif weekday == 0:  # Monday — deadline = last Friday 08:00
        days_back = 3
    else:              # Tue–Fri — deadline = yesterday 08:00
        days_back = 1
    deadline = (now - timedelta(days=days_back)).replace(hour=8, minute=0, second=0, microsecond=0)
    return (now - deadline).total_seconds() / 3600


# ── File status ──────────────────────────────────────────────────────────────

def file_status(path: Path, max_age_hours):
    """Return {exists, mtime_iso, age_hours, status}.

    max_age_hours may be None (no check), a number, or the sentinel
    string "business_day" (Mon–Fri: prev business day; Sat–Sun: lenient).
    """
    if max_age_hours == "business_day":
        max_age_hours = business_day_max_age_hours()
    if not path.exists():
        return {"exists": False, "mtime_iso": None, "age_hours": None, "status": "missing", "size": 0}
    if path.is_dir():
        # Use the most recent file inside the folder
        files = [f for f in path.rglob("*") if f.is_file()]
        if not files:
            return {"exists": True, "mtime_iso": None, "age_hours": None, "status": "missing", "size": 0}
        latest = max(files, key=lambda p: p.stat().st_mtime)
        mtime = latest.stat().st_mtime
        size = latest.stat().st_size
    else:
        mtime = path.stat().st_mtime
        size = path.stat().st_size
    age_hours = (datetime.now().timestamp() - mtime) / 3600
    if max_age_hours is None:
        status = "fresh"
    elif age_hours <= max_age_hours:
        status = "fresh"
    elif age_hours <= max_age_hours * 1.5:
        status = "stale"
    else:
        status = "old"
    return {
        "exists": True,
        "mtime_iso": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
        "age_hours": round(age_hours, 1),
        "status": status,
        "size": size,
    }


def fmt_age(hours):
    if hours is None:
        return "—"
    if hours < 1:
        return f"{int(hours*60)}m ago"
    if hours < 48:
        return f"{hours:.1f}h ago"
    return f"{hours/24:.1f}d ago"


def fmt_size(b):
    if not b:
        return "—"
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


# ── Job evaluation ───────────────────────────────────────────────────────────

WORST = {"fresh": 0, "ok": 0, "stale": 1, "warn": 1, "old": 1, "missing": 2, "fail": 2, "never": 2}


def task_run_status(task_info, max_age_hours):
    """Translate Task Scheduler info into status."""
    if max_age_hours == "business_day":
        max_age_hours = business_day_max_age_hours()
    if not task_info:
        return {"status": "missing", "label": "Not found in Task Scheduler", "last_run_iso": None, "next_run_iso": None, "last_result": None}
    last_run = task_info.get("LastRun")
    next_run = task_info.get("NextRun")
    last_result = task_info.get("LastResult")
    # Detect "never run" placeholder year
    if not last_run or last_run.startswith("1999"):
        return {"status": "never", "label": "Never run", "last_run_iso": None, "next_run_iso": next_run, "last_result": last_result}
    try:
        last_dt = datetime.strptime(last_run, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return {"status": "warn", "label": f"Unparseable last run: {last_run}", "last_run_iso": last_run, "next_run_iso": next_run, "last_result": last_result}
    age_hours = (datetime.now() - last_dt).total_seconds() / 3600
    # Result codes: 0 = success; 267009/267011/267014 = task is currently running / starting / finishing — treat as ok
    running_codes = {267009, 267011, 267014, 267015}
    if last_result == 0 or last_result in running_codes:
        result_ok = True
    else:
        result_ok = False
    if max_age_hours is None:
        st = "ok" if result_ok else "fail"
    elif age_hours > max_age_hours * 1.5:
        st = "old"
    elif age_hours > max_age_hours:
        st = "stale"
    elif not result_ok:
        st = "fail"
    else:
        st = "ok"
    label = f"Ran {fmt_age(age_hours)}" + (f" · exit {last_result}" if not result_ok else "")
    return {"status": st, "label": label, "last_run_iso": last_run, "next_run_iso": next_run, "last_result": last_result, "age_hours": round(age_hours, 1)}


def evaluate_job(job, ts_lookup):
    info = ts_lookup.get(job["task"])
    is_continuous = job.get("cadence", "").lower().startswith("continuous")
    if is_continuous and info:
        # For long-running services, "ok" if currently running, else "fail"
        running = info.get("State", "").lower() in {"running"}
        task_st = {
            "status": "ok" if running else "fail",
            "label": "Service running" if running else "Service stopped",
            "last_run_iso": info.get("LastRun"),
            "next_run_iso": info.get("NextRun"),
            "last_result": info.get("LastResult"),
            "age_hours": None,
        }
    else:
        task_st = task_run_status(info, job.get("max_age_hours"))
    inputs = []
    for inp in job["inputs"]:
        fs = file_status(inp["path"], inp.get("max_age_hours"))
        inputs.append({**inp, "path_str": str(inp["path"]), **fs})
    out_max = job["output"].get("max_age_hours", job.get("max_age_hours"))
    out_fs = file_status(job["output"]["path"], out_max)
    output = {**job["output"], "path_str": str(job["output"]["path"]), **out_fs}
    # Overall = worst of task, inputs, output
    statuses = [task_st["status"]] + [i["status"] for i in inputs] + [output["status"]]
    overall_score = max(WORST.get(s, 0) for s in statuses)
    overall = ["ok", "warn", "fail"][overall_score]
    return {
        "id": job["id"],
        "agent": job["agent"],
        "name": job["name"],
        "task": job["task"],
        "cadence": job["cadence"],
        "max_age_hours": job.get("max_age_hours"),
        "task_status": task_st,
        "inputs": inputs,
        "output": output,
        "dashboard_url": job.get("dashboard_url"),
        "overall": overall,
    }



# ── Telegram alert (deduped) ────────────────────────────────────────────────
#
# Replaces the old Outlook email path (deprecated 2026-05-17). Reasons:
#   1. health_check.py runs after every scheduled job → email fired every time.
#   2. Quintus already monitors Telegram chat 8042233389 — no new channel needed.
#
# Dedup rules:
#   - Hash the set of {fail+warn job ids}; only send if hash changes
#     OR last send was >12h ago (so a persistent failure pings once a day).
#   - State stored in updates_alert_state.json next to updates.html.

TELEGRAM_CHAT_ID = "8042233389"
TELEGRAM_REPING_HOURS = 12


def _telegram_token() -> str | None:
    env_path = PULSE_BASE / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    return None


def _alert_signature(problem_jobs) -> str:
    """Stable fingerprint of the current failure set — order-independent."""
    return "|".join(sorted(f"{j['id']}:{j['overall']}" for j in problem_jobs))


def _load_alert_state() -> dict:
    if not ALERT_STATE.exists():
        return {}
    try:
        return json.loads(ALERT_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_alert_state(state: dict) -> None:
    ALERT_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _build_telegram_message(problem_jobs, fail_count, warn_count, generated_at) -> str:
    header = f"*Updates Health Check*  ·  {generated_at[:16].replace('T', ' ')}"
    tag_parts = []
    if fail_count:
        tag_parts.append(f"❌ {fail_count} failed")
    if warn_count:
        tag_parts.append(f"⚠️ {warn_count} warning{'s' if warn_count > 1 else ''}")
    tag = "  ·  ".join(tag_parts)

    lines = [header, tag, ""]
    for j in problem_jobs:
        icon = "❌" if j["overall"] == "fail" else "⚠️"
        ts = j["task_status"]
        last_result = ts.get("last_result")
        last_run = ts.get("last_run_iso") or "never"
        if last_result not in (None, 0, 267009, 267011, 267014, 267015):
            detail = f"exit {last_result}"
        elif ts.get("status") in ("old", "stale"):
            detail = f"stale {fmt_age(ts.get('age_hours'))}"
        elif j["output"].get("status") in ("old", "stale", "missing"):
            detail = f"output {j['output']['status']}"
        else:
            detail = ts.get("label", "")
        lines.append(f"{icon}  *{j['agent']}* · {j['name']}\n    {last_run[-8:] if last_run != 'never' else 'never'}  ·  {detail}")
    lines.append("")
    lines.append("[Open Workspace Dashboard → Updates](https://op-workspace-dashboard.vercel.app/)")
    return "\n".join(lines)


def send_alert_telegram(jobs, generated_at: str) -> None:
    problem_jobs = [j for j in jobs if j["overall"] in ("fail", "warn")]
    state = _load_alert_state()
    if not problem_jobs:
        # All green — record recovery, send a single "recovered" if we were previously alerting
        if state.get("last_signature"):
            try:
                _send_telegram_raw("✅  *Updates Health Check*  ·  all jobs operational")
            except Exception as e:
                print(f"[warn] telegram recovery send failed: {e}", file=sys.stderr)
            _save_alert_state({})
        return

    signature = _alert_signature(problem_jobs)
    last_signature = state.get("last_signature")
    last_sent = state.get("last_sent_iso")
    now = datetime.now()

    should_send = signature != last_signature
    if not should_send and last_sent:
        try:
            elapsed = (now - datetime.fromisoformat(last_sent)).total_seconds() / 3600
            should_send = elapsed >= TELEGRAM_REPING_HOURS
        except Exception:
            should_send = True

    if not should_send:
        print(f"[ok] telegram alert suppressed (dedup) · signature unchanged")
        return

    fail_count = sum(1 for j in problem_jobs if j["overall"] == "fail")
    warn_count = sum(1 for j in problem_jobs if j["overall"] == "warn")
    message = _build_telegram_message(problem_jobs, fail_count, warn_count, generated_at)

    try:
        _send_telegram_raw(message)
        _save_alert_state({"last_signature": signature, "last_sent_iso": now.isoformat(timespec="seconds")})
        parts = []
        if fail_count: parts.append(f"{fail_count} failed")
        if warn_count: parts.append(f"{warn_count} warning{'s' if warn_count > 1 else ''}")
        print(f"[ok] telegram alert sent ({', '.join(parts)})")
    except Exception as e:
        print(f"[warn] telegram alert failed: {e}", file=sys.stderr)


def _send_telegram_raw(text: str) -> None:
    import urllib.request, urllib.parse
    token = _telegram_token()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not found in PULSE .env")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read()
        if resp.status >= 400:
            raise RuntimeError(f"telegram api {resp.status}: {body!r}")


# ── (removed) Email alert ──────────────────────────────────────────────────
# The old Outlook-based send_alert_email() and _build_alert_html() were
# deprecated 2026-05-17 in favour of deduped Telegram alerts above.

# ── Git push ────────────────────────────────────────────────────────────────

def push_to_github():
    try:
        token_proc = subprocess.run(
            ["gh", "auth", "token", "--user", "FlomaticAuto"],
            capture_output=True, text=True, timeout=20,
        )
        token = token_proc.stdout.strip()
        if not token:
            print("[warn] no FlomaticAuto token; skipping push", file=sys.stderr)
            return
        remote = f"https://FlomaticAuto:{token}@github.com/FlomaticAuto/op-workspace-dashboard.git"
        subprocess.run(["git", "-C", str(WORKSPACE), "add", "updates_status.json"], check=False)
        rc = subprocess.run(
            ["git", "-C", str(WORKSPACE), "commit", "-m", f"Updates health check {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            capture_output=True, text=True,
        )
        if rc.returncode != 0 and "nothing to commit" not in (rc.stdout + rc.stderr):
            print(f"[warn] commit: {rc.stdout}{rc.stderr}", file=sys.stderr)
        # Vercel production target is 'main', so push to both refs.
        push = subprocess.run(
            ["git", "-C", str(WORKSPACE), "push", remote, "HEAD:master", "HEAD:main"],
            capture_output=True, text=True, timeout=60,
        )
        if push.returncode != 0:
            print(f"[warn] push failed: {push.stderr}", file=sys.stderr)
        else:
            print("[ok] updates_status.json pushed to master + main")
    except Exception as e:
        print(f"[warn] push error: {e}", file=sys.stderr)


# ── Main ────────────────────────────────────────────────────────────────────

def main(push=True):
    ts = query_task_scheduler()
    jobs = [evaluate_job(j, ts) for j in MANIFEST]
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(jobs),
        "ok": sum(1 for j in jobs if j["overall"] == "ok"),
        "warn": sum(1 for j in jobs if j["overall"] == "warn"),
        "fail": sum(1 for j in jobs if j["overall"] == "fail"),
        "jobs": [{
            "id": j["id"], "agent": j["agent"], "name": j["name"], "task": j["task"],
            "cadence": j["cadence"], "overall": j["overall"],
            "task_last_run": j["task_status"].get("last_run_iso"),
            "task_last_result": j["task_status"].get("last_result"),
        } for j in jobs],
    }
    summary["success_pct"] = round(summary["ok"] / summary["total"] * 100) if summary["total"] else 0
    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"[ok] wrote {OUT_JSON} · {summary['ok']}/{summary['total']} green (Updates tab on dashboard reads this)")
    send_alert_telegram(jobs, summary["generated_at"])
    if push:
        push_to_github()


if __name__ == "__main__":
    push = "--no-push" not in sys.argv
    main(push=push)
