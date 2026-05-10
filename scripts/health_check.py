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

Pushes both to the op-workspace-dashboard repo on GitHub Pages.
Live URL: https://flomaticauto.github.io/op-workspace-dashboard/updates.html
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path(r"C:\Users\quint\workspace-dashboard")
LOGO_LOCAL = WORKSPACE / "logo.jpg"
OUT_HTML = WORKSPACE / "updates.html"
OUT_JSON = WORKSPACE / "updates_status.json"

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
        "dashboard_url": "https://flomaticauto.github.io/op-workspace-dashboard/health-report.html",
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


# ── HTML rendering ───────────────────────────────────────────────────────────

CSS_BLOCK = """
:root{
  --_y50:#FEF9E0;--_y100:#FDF0A0;--_y200:#FAE04D;--_y400:#F5C400;--_y600:#D4A800;--_y800:#A88000;--_y900:#6A5000;
  --_n50:#E8EFF8;--_n100:#B8CCE8;--_n300:#6B9ED0;--_n500:#2D6BA8;--_n700:#1A3D6E;--_n900:#0D2040;--_n950:#071022;
  --_g0:#FFFFFF;--_g50:#F7F6F3;--_g100:#E8E7E2;--_g200:#C8C7C0;--_g400:#949390;--_g600:#5C5B58;--_g800:#2E2E2C;--_g900:#1A1A18;--_g950:#0D0D0B;
  --_teal:#2D8C7A;--_teal-light:#C8EDE7;--_coral:#E86060;--_coral-light:#FDDCDC;
  --font-display:'Barlow Condensed',sans-serif;--font-body:'Barlow',sans-serif;
  --r-sm:4px;--r-md:8px;--r-lg:12px;--r-xl:16px;--r-pill:50px;
}
.theme-light{color-scheme:light;--color-surface-page:var(--_g50);--color-surface-base:var(--_g0);--color-surface-elevated:var(--_g0);--color-surface-sunken:var(--_g100);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g950);--color-text-secondary:var(--_g600);--color-text-tertiary:var(--_g400);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-subtle:var(--_g100);--color-border-default:var(--_g200);--color-success-bg:#EDF7F5;--color-success-fg:#1a5c50;--color-success-bd:var(--_teal);--color-warning-bg:var(--_y50);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y600);--color-danger-bg:#FEF2F2;--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--shadow-md:0 4px 12px rgba(0,0,0,0.08);--shadow-lg:0 10px 30px rgba(0,0,0,0.10);}
.theme-dark{color-scheme:dark;--color-surface-page:var(--_g950);--color-surface-base:var(--_g900);--color-surface-elevated:var(--_g800);--color-surface-sunken:var(--_g950);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g100);--color-text-secondary:var(--_g400);--color-text-tertiary:var(--_g600);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-subtle:rgba(255,255,255,.06);--color-border-default:rgba(255,255,255,.10);--color-success-bg:rgba(45,140,122,.12);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,.30);--color-warning-bg:rgba(245,196,0,.10);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,.25);--color-danger-bg:rgba(232,96,96,.12);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,.30);--shadow-md:0 4px 12px rgba(0,0,0,.40);--shadow-lg:0 10px 30px rgba(0,0,0,.50);}
.theme-brand{color-scheme:light;--color-surface-page:var(--_y400);--color-surface-base:var(--_y200);--color-surface-elevated:var(--_y50);--color-surface-sunken:var(--_y600);--color-surface-secondary:var(--_g950);--color-text-primary:var(--_g950);--color-text-secondary:var(--_y900);--color-text-tertiary:var(--_y800);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_g950);--color-border-subtle:rgba(0,0,0,.08);--color-border-default:rgba(0,0,0,.14);--color-success-bg:rgba(45,140,122,.12);--color-success-fg:#1a5c50;--color-success-bd:var(--_teal);--color-warning-bg:rgba(0,0,0,.08);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y900);--color-danger-bg:rgba(232,96,96,.12);--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--shadow-md:0 4px 12px rgba(0,0,0,.14);--shadow-lg:0 10px 30px rgba(0,0,0,.18);}
.theme-navy{color-scheme:dark;--color-surface-page:var(--_n950);--color-surface-base:var(--_n900);--color-surface-elevated:var(--_n700);--color-surface-sunken:var(--_n950);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g0);--color-text-secondary:var(--_n100);--color-text-tertiary:var(--_n300);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-subtle:rgba(107,158,208,.12);--color-border-default:rgba(107,158,208,.20);--color-success-bg:rgba(45,140,122,.15);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,.35);--color-warning-bg:rgba(245,196,0,.12);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,.30);--color-danger-bg:rgba(232,96,96,.14);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,.35);--shadow-md:0 4px 12px rgba(0,0,0,.50);--shadow-lg:0 10px 30px rgba(0,0,0,.60);}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font-body);background:var(--color-surface-page);color:var(--color-text-primary);}
.theme-bar{display:flex;gap:4px;padding:8px 16px;background:var(--color-surface-secondary);}
.theme-bar button{font-family:var(--font-display);font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:11px;padding:6px 14px;border:1px solid rgba(255,255,255,.2);background:transparent;color:var(--color-text-on-navy);cursor:pointer;border-radius:var(--r-sm);}
.theme-bar button.active{background:var(--color-brand-primary);color:#000;border-color:var(--color-brand-primary);}
.header{display:flex;align-items:center;gap:16px;padding:24px 32px;border-bottom:1px solid var(--color-border-subtle);background:var(--color-surface-base);}
.logo-wrap{width:48px;height:48px;border-radius:50%;overflow:hidden;flex-shrink:0;}
.logo-wrap img{display:block;width:100%;height:100%;object-fit:cover;}
.h-titles h1{font-family:var(--font-display);font-weight:900;font-size:32px;letter-spacing:.02em;text-transform:uppercase;margin:0;line-height:1;}
.h-titles .sub{font-family:var(--font-body);color:var(--color-text-secondary);font-size:13px;margin-top:4px;}
.header-actions{margin-left:auto;display:flex;gap:8px;align-items:center;}
.back-link{font-family:var(--font-display);font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:var(--color-text-secondary);text-decoration:none;padding:6px 12px;border:1px solid var(--color-border-default);border-radius:var(--r-sm);}
.back-link:hover{color:var(--color-brand-primary);border-color:var(--color-brand-primary);}
.summary-bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;padding:24px 32px;background:var(--color-surface-base);border-bottom:1px solid var(--color-border-subtle);}
.kpi{padding:18px 20px;background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-radius:var(--r-lg);}
.kpi .lbl{font-family:var(--font-body);font-weight:500;text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:var(--color-text-secondary);}
.kpi .val{font-family:var(--font-display);font-weight:900;font-size:36px;line-height:1.1;margin-top:4px;}
.kpi.ok .val{color:var(--_teal);}.kpi.warn .val{color:var(--_y400);}.kpi.fail .val{color:var(--_coral);}
.main{padding:24px 32px;}
.agent-section{margin-bottom:36px;}
.agent-title{font-family:var(--font-display);font-weight:800;font-size:22px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:12px;color:var(--color-text-primary);}
.agent-title::before{content:"";display:inline-block;width:6px;height:24px;background:var(--color-brand-primary);border-radius:3px;}
.job-card{background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-radius:var(--r-lg);padding:20px 24px;margin-bottom:16px;box-shadow:var(--shadow-md);}
.job-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:12px;}
.job-name{font-family:var(--font-display);font-weight:700;font-size:18px;text-transform:uppercase;letter-spacing:.02em;line-height:1.2;}
.job-meta{font-family:var(--font-body);color:var(--color-text-secondary);font-size:12px;margin-top:4px;}
.status-badge{font-family:var(--font-display);font-weight:800;text-transform:uppercase;letter-spacing:.08em;font-size:11px;padding:6px 12px;border-radius:var(--r-pill);border:1px solid;white-space:nowrap;}
.s-ok{background:var(--color-success-bg);color:var(--color-success-fg);border-color:var(--color-success-bd);}
.s-warn{background:var(--color-warning-bg);color:var(--color-warning-fg);border-color:var(--color-warning-bd);}
.s-fail{background:var(--color-danger-bg);color:var(--color-danger-fg);border-color:var(--color-danger-bd);}
.task-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 24px;padding:12px 0;border-top:1px solid var(--color-border-subtle);font-size:13px;}
.task-row .k{color:var(--color-text-tertiary);font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-family:var(--font-body);font-weight:500;}
.task-row .v{color:var(--color-text-primary);font-family:var(--font-body);font-weight:500;}
.task-row .v a{color:var(--color-brand-primary);text-decoration:none;}.task-row .v a:hover{text-decoration:underline;}
table.files{width:100%;border-collapse:collapse;margin-top:8px;font-size:12.5px;}
table.files th{text-align:left;font-family:var(--font-body);font-weight:500;text-transform:uppercase;letter-spacing:.06em;font-size:10.5px;color:var(--color-text-tertiary);padding:8px 10px;border-bottom:1px solid var(--color-border-subtle);}
table.files td{padding:10px;border-bottom:1px solid var(--color-border-subtle);color:var(--color-text-primary);vertical-align:top;}
table.files td.path{font-family:'Barlow',sans-serif;font-size:11.5px;color:var(--color-text-secondary);word-break:break-all;}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle;}
.dot.fresh{background:var(--_teal);}.dot.stale{background:var(--_y400);}.dot.old,.dot.missing{background:var(--_coral);}
.footer{padding:18px 32px;text-align:center;color:var(--color-text-tertiary);font-size:12px;border-top:1px solid var(--color-border-subtle);}
"""


def render_html(jobs):
    now = datetime.now()
    counts = {"ok": 0, "warn": 0, "fail": 0}
    for j in jobs:
        counts[j["overall"]] = counts.get(j["overall"], 0) + 1
    total = len(jobs)
    success_pct = round(counts["ok"] / total * 100) if total else 0

    by_agent = {}
    for j in jobs:
        by_agent.setdefault(j["agent"], []).append(j)
    AGENT_ORDER = ["PRISM", "STRIKER", "HAVEN", "SIGMA", "BLAZE", "VAULT"]
    ordered_agents = [a for a in AGENT_ORDER if a in by_agent] + [a for a in by_agent if a not in AGENT_ORDER]

    def status_label(s):
        return {"ok": "Operational", "warn": "Warning", "fail": "Failed"}[s]

    sections_html = []
    for agent in ordered_agents:
        rows = []
        for j in by_agent[agent]:
            input_rows = []
            if j["inputs"]:
                input_rows.append(
                    "<table class='files'><thead><tr><th>Source File</th><th>Modified</th><th>Age</th><th>Size</th><th>Path</th></tr></thead><tbody>"
                )
                for inp in j["inputs"]:
                    input_rows.append(
                        f"<tr><td><span class='dot {inp['status']}'></span>{inp['label']}<div style='color:var(--color-text-tertiary);font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;margin-top:2px;'>{inp.get('source','')}</div></td>"
                        f"<td>{inp.get('mtime_iso') or '—'}</td>"
                        f"<td>{fmt_age(inp.get('age_hours'))}</td>"
                        f"<td>{fmt_size(inp.get('size'))}</td>"
                        f"<td class='path'>{inp['path_str']}</td></tr>"
                    )
                input_rows.append("</tbody></table>")
            else:
                input_rows.append("<div style='color:var(--color-text-tertiary);font-size:12px;font-style:italic;padding:8px 0;'>No tracked input files for this job.</div>")
            output = j["output"]
            dash_link = f' · <a href=\"{j["dashboard_url"]}\" target=\"_blank\">View dashboard ↗</a>' if j["dashboard_url"] else ""
            ts = j["task_status"]
            next_run_str = ts.get("next_run_iso") or "—"
            last_result = ts.get("last_result")
            result_str = "—" if last_result is None else (f"<span style='color:var(--_teal);font-weight:600;'>0 (success)</span>" if last_result == 0 else f"<span style='color:var(--_coral);font-weight:600;'>{last_result}</span>")
            rows.append(
                f"""<div class='job-card'>
  <div class='job-head'>
    <div>
      <div class='job-name'>{j['name']}</div>
      <div class='job-meta'>{j['cadence']} · {j['task']}{dash_link}</div>
    </div>
    <span class='status-badge s-{j['overall']}'>{status_label(j['overall'])}</span>
  </div>
  <div class='task-row'>
    <div><div class='k'>Task last ran</div><div class='v'>{ts.get('last_run_iso') or 'Never'}</div></div>
    <div><div class='k'>Next run</div><div class='v'>{next_run_str}</div></div>
    <div><div class='k'>Last exit</div><div class='v'>{result_str}</div></div>
    <div><div class='k'>Output</div><div class='v'><span class='dot {output['status']}'></span>{output['label']}</div></div>
    <div><div class='k'>Output modified</div><div class='v'>{output.get('mtime_iso') or 'Missing'} ({fmt_age(output.get('age_hours'))})</div></div>
  </div>
  {''.join(input_rows)}
</div>"""
            )
        sections_html.append(f"<section class='agent-section'><h2 class='agent-title'>{agent}</h2>{''.join(rows)}</section>")

    sections = "\n".join(sections_html)
    css = CSS_BLOCK
    return f"""<!DOCTYPE html>
<html lang=\"en\" class=\"theme-navy\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Updates · Olympic Paints Health Check</title>
<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
<link href=\"https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap\" rel=\"stylesheet\">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>{css}</style>
</head>
<body>
<div class=\"theme-bar\">
  <button onclick=\"olyTheme('theme-light',this)\">Light</button>
  <button onclick=\"olyTheme('theme-dark',this)\">Dark</button>
  <button onclick=\"olyTheme('theme-brand',this)\">Brand</button>
  <button onclick=\"olyTheme('theme-navy',this)\" class=\"active\">Navy</button>
</div>
<header class=\"header\">
  <div class=\"logo-wrap\"><img src=\"logo.jpg\" alt=\"Olympic Paints\" width=\"48\" height=\"48\"></div>
  <div class=\"h-titles\">
    <h1>Updates · Health Check</h1>
    <div class=\"sub\">Every scheduled job across Olympic Paints · last refreshed {now.strftime('%a %d %b %Y · %H:%M')}</div>
  </div>
  <div class=\"header-actions\">
    <a class=\"back-link\" href=\"portal.html\">← Workspace Portal</a>
  </div>
</header>
<div class=\"summary-bar\">
  <div class=\"kpi ok\"><div class=\"lbl\">Operational</div><div class=\"val\">{counts['ok']}<span style='font-size:18px;color:var(--color-text-tertiary);font-weight:500;'> / {total}</span></div></div>
  <div class=\"kpi warn\"><div class=\"lbl\">Warning</div><div class=\"val\">{counts['warn']}</div></div>
  <div class=\"kpi fail\"><div class=\"lbl\">Failed</div><div class=\"val\">{counts['fail']}</div></div>
  <div class=\"kpi ok\"><div class=\"lbl\">Success Rate</div><div class=\"val\">{success_pct}%</div></div>
  <div class=\"kpi\"><div class=\"lbl\">Tracked Inputs</div><div class=\"val\">{sum(len(j['inputs']) for j in jobs)}</div></div>
</div>
<main class=\"main\">
{sections}
</main>
<footer class=\"footer\">Olympic Paints · Updates Health Check · auto-generated by health_check.py · last run {now.strftime('%Y-%m-%d %H:%M:%S')}</footer>
<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){{
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}}
</script>
</body></html>"""


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
        subprocess.run(["git", "-C", str(WORKSPACE), "add", "updates.html", "updates_status.json"], check=False)
        rc = subprocess.run(
            ["git", "-C", str(WORKSPACE), "commit", "-m", f"Updates health check {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            capture_output=True, text=True,
        )
        if rc.returncode != 0 and "nothing to commit" not in (rc.stdout + rc.stderr):
            print(f"[warn] commit: {rc.stdout}{rc.stderr}", file=sys.stderr)
        push = subprocess.run(
            ["git", "-C", str(WORKSPACE), "push", remote, "HEAD:master"],
            capture_output=True, text=True, timeout=60,
        )
        if push.returncode != 0:
            print(f"[warn] push failed: {push.stderr}", file=sys.stderr)
        else:
            print("[ok] updates.html pushed")
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
    OUT_HTML.write_text(render_html(jobs), encoding="utf-8")
    print(f"[ok] wrote {OUT_HTML} · {summary['ok']}/{summary['total']} green")
    if push:
        push_to_github()


if __name__ == "__main__":
    push = "--no-push" not in sys.argv
    main(push=push)
