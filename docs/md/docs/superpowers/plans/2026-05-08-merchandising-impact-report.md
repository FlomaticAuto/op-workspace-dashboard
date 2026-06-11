# Merchandising Impact Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tabbed dashboard that quantifies the sales impact of formal merchandising at Kit Kat (5 accounts, R27.8M lifetime) and Easy Build (7 accounts, R12.0M lifetime), deploy it to a new GitHub Pages repo, and add an on-demand "Regenerate" button to the workspace portal backed by a local Flask trigger service.

**Architecture:** Three deliverables: (1) a Python build script that computes YoY same-month sales metrics + auto-prose and emits a single navy-themed HTML file, deploying via `git push`; (2) a generic Flask trigger server on `localhost:8765` that exposes `/health`, `/trigger/<key>`, `/status/<job_id>` endpoints and runs at Windows login; (3) portal updates that wire a button to the trigger service with live status polling.

**Tech Stack:** Python 3 (pandas, openpyxl, Flask), Chart.js (CDN, with `barLabels` plugin), vanilla JS for portal interactivity, GitHub Pages, Windows Task Scheduler. Tests use `pytest`.

**Spec:** [`docs/superpowers/specs/2026-05-08-merchandising-impact-report-design.md`](../specs/2026-05-08-merchandising-impact-report-design.md)

---

## File Structure

| File | Responsibility |
|---|---|
| `1.Projects/AWS Data/build_merchandising_impact.py` | Main build: load sales+visits, compute metrics, render HTML, deploy |
| `1.Projects/AWS Data/tests/test_merchandising_impact.py` | Unit tests for data computation functions |
| `1.Projects/AWS Data/tests/conftest.py` | Pytest config: makes the script importable |
| `1.Projects/AWS Data/merchandising-impact/` | Git clone of the GitHub Pages repo (output dir) |
| `1.Projects/AWS Data/merchandising-impact/index.html` | Generated dashboard |
| `1.Projects/AWS Data/merchandising-impact/logo.jpg` | Brand logo, copied at build time |
| `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server.py` | Flask trigger service (generic, multi-build) |
| `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server_test.py` | Smoke tests for the Flask server |
| `C:\Users\quint\workspace-dashboard\scripts\install_trigger_task.ps1` | PowerShell script to register the Windows scheduled task |
| `C:\Users\quint\workspace-dashboard\portal.html` | Add Merchandising Impact tile + trigger JS (modify) |

---

## Task 1: Create the GitHub Pages repo and local clone

**Files:**
- Create on GitHub: `flomaticauto/olympic-paints-merchandising`
- Local clone: `1.Projects/AWS Data/merchandising-impact/`

- [ ] **Step 1: Create the repo on GitHub via gh CLI**

```powershell
$env:GH_TOKEN = (gh auth token --user FlomaticAuto)
gh repo create FlomaticAuto/olympic-paints-merchandising --public --description "Olympic Paints — Merchandising Impact Report" --homepage "https://flomaticauto.github.io/olympic-paints-merchandising/"
```

Expected: `https://github.com/FlomaticAuto/olympic-paints-merchandising` exists.

- [ ] **Step 2: Clone the repo into the AWS Data folder**

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
git clone "https://github.com/FlomaticAuto/olympic-paints-merchandising.git" merchandising-impact
```

- [ ] **Step 3: Add a placeholder `index.html` and push to seed the default branch**

Create `1.Projects/AWS Data/merchandising-impact/index.html`:

```html
<!DOCTYPE html><html><head><title>Olympic Paints — Merchandising Impact</title></head>
<body><p>Report generating — refresh in a moment.</p></body></html>
```

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\merchandising-impact"
git add index.html
git commit -m "Seed Merchandising Impact Report repo"
git push -u origin main
```

- [ ] **Step 4: Enable GitHub Pages on the repo**

```powershell
gh api -X POST "repos/FlomaticAuto/olympic-paints-merchandising/pages" -f "source[branch]=main" -f "source[path]=/"
```

Expected: HTTPS Pages URL `https://flomaticauto.github.io/olympic-paints-merchandising/` becomes live (may take 1–2 min).

- [ ] **Step 5: Verify Pages URL responds**

```powershell
curl -I https://flomaticauto.github.io/olympic-paints-merchandising/
```

Expected: `HTTP/2 200`.

---

## Task 2: Set up build script skeleton, constants, and test scaffold

**Files:**
- Create: `1.Projects/AWS Data/build_merchandising_impact.py`
- Create: `1.Projects/AWS Data/tests/conftest.py`
- Create: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the test scaffold (failing import)**

Create `1.Projects/AWS Data/tests/conftest.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

Create `1.Projects/AWS Data/tests/test_merchandising_impact.py`:

```python
def test_module_imports():
    import build_merchandising_impact  # noqa: F401
```

- [ ] **Step 2: Run the test to verify it fails**

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'build_merchandising_impact'`.

- [ ] **Step 3: Create the build script skeleton with constants**

Create `1.Projects/AWS Data/build_merchandising_impact.py`:

```python
"""
build_merchandising_impact.py
Olympic Paints — Merchandising Impact Report.
Quantifies sales-growth correlation with formal merchandising visits at
Kit Kat and Easy Build group stores. Deploys to GitHub Pages.
"""
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import openpyxl

# ── PATHS ────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
OUT_DIR      = BASE_DIR / "merchandising-impact"
PARQUET_PATH = BASE_DIR.parent.parent / "3.Resources" / "16.Sales and Other data" / "Sales_Invoices_All.parquet"
VISITS_PATH  = BASE_DIR.parent.parent / "2.Areas" / "3. Merchandising" / "2. Merchandiser Visits" / "Merchandising_Visits_Log.xlsx"
LOGO_SRC     = BASE_DIR.parent.parent / "3.Resources" / "9. Brand Assets & Images" / "Misc Pictures" / "Olympic Paints Logo Digital.jpg"

# ── ACCOUNT FAMILIES ─────────────────────────────────────────────────────────
KIT_KAT_ACCOUNTS   = ["KK021", "KK021/1", "KK021/2", "KK021/4", "KK022"]
EASY_BUILD_ACCOUNTS = ["KE005", "KE005/1", "KE008", "KE009", "KE010", "KE012", "KE023"]
# Sub-accounts merged into parent — display row shows "consolidated <date> into <parent>"
CONSOLIDATED = {
    "KK021/1": ("KK021", "Feb 2025"),
    "KK021/2": ("KK021", "Feb 2025"),
    "KK021/4": ("KK021", "Feb 2025"),
    "KE005/1": ("KE005", "Jan 2025"),
}

GROUPS = {
    "kitkat":    {"label": "Kit Kat",    "accounts": KIT_KAT_ACCOUNTS,   "name_patterns": [r"\bKIT\s*KAT\b", r"\bKITKAT\b"]},
    "easybuild": {"label": "Easy Build", "accounts": EASY_BUILD_ACCOUNTS, "name_patterns": [r"\bEASY\s*BUILD\b", r"\bEASYBUILD\b"]},
}

# ── FILTER THRESHOLDS ────────────────────────────────────────────────────────
ACTIVE_RECENT_MONTHS = 6
ACTIVE_MIN_AVG_PER_MONTH = 20_000  # R20K/month lifetime average

# ── STATUS BADGE THRESHOLDS ──────────────────────────────────────────────────
STATUS_STRONG_PCT   = 0.15   # ≥ +15%
STATUS_DECLINED_PCT = -0.05  # < -5%


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Building Merchandising Impact Report...")
    # implementation tasks below


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add "1.Projects/AWS Data/build_merchandising_impact.py" "1.Projects/AWS Data/tests/conftest.py" "1.Projects/AWS Data/tests/test_merchandising_impact.py"
git commit -m "Scaffold build_merchandising_impact.py with constants and pytest setup"
```

(Note: this folder is non-git per CLAUDE.md, so git commands are no-op outside the merchandising-impact subfolder. Skip step 5 if `git status` returns "fatal: not a git repository".)

---

## Task 3: Sub-account-aware sales loader

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_merchandising_impact.py`:

```python
import pandas as pd
from build_merchandising_impact import load_sales_for_group, KIT_KAT_ACCOUNTS, EASY_BUILD_ACCOUNTS

def test_load_sales_kitkat_includes_all_subaccounts():
    df = load_sales_for_group(KIT_KAT_ACCOUNTS)
    accs = set(df["accno"].unique())
    assert accs == set(KIT_KAT_ACCOUNTS), f"Got {accs}"
    # Sub-accounts only have rows in the historical period
    sub_df = df[df["accno"] == "KK021/1"]
    assert sub_df["trandate"].max().year <= 2025
    # Total Kit Kat revenue (all 5 accounts) ~ R27.8M as of 2026-05-07
    assert df["ivnett"].sum() > 27_000_000

def test_load_sales_easybuild_excludes_KE035():
    df = load_sales_for_group(EASY_BUILD_ACCOUNTS)
    assert "KE035" not in df["accno"].unique()
    assert "KE005/1" in df["accno"].unique()
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_load_sales_kitkat_includes_all_subaccounts -v
```

Expected: FAIL with `ImportError: cannot import name 'load_sales_for_group'`.

- [ ] **Step 3: Implement `load_sales_for_group`**

Add to `build_merchandising_impact.py` after the constants block:

```python
# ── DATA LOADERS ─────────────────────────────────────────────────────────────

def load_sales_for_group(account_list):
    """Return invoice rows for the given account family. Includes sub-accounts."""
    df = pd.read_parquet(PARQUET_PATH)
    out = df[df["accno"].isin(account_list)].copy()
    out["trandate"] = pd.to_datetime(out["trandate"])
    return out


def monthly_sales(df):
    """Aggregate to year-month totals. Returns DataFrame with cols [year, month, ivnett, period]."""
    grp = df.groupby([df["trandate"].dt.year.rename("year"),
                      df["trandate"].dt.month.rename("month")])["ivnett"].sum().reset_index()
    grp["period"] = pd.to_datetime(grp["year"].astype(str) + "-" + grp["month"].astype(str).str.zfill(2) + "-01")
    return grp.sort_values("period").reset_index(drop=True)
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit (in the git repos that exist)**

If applicable; otherwise skip.

---

## Task 4: Visit-log loader with name-based group matching

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
def test_load_visits_kitkat():
    visits = load_visits_for_group("kitkat")
    # Per the data: 33 Kit Kat visits as of 2026-05-07
    assert len(visits) >= 30, f"Got {len(visits)} visits"
    # Every visit's store name must match the kitkat pattern
    import re
    pat = re.compile(r"\bKIT\s*KAT\b|\bKITKAT\b", re.IGNORECASE)
    for v in visits:
        assert pat.search(str(v["store_name"])), f"Bad match: {v['store_name']}"

def test_load_visits_easybuild():
    visits = load_visits_for_group("easybuild")
    assert len(visits) >= 15, f"Got {len(visits)} visits"

def test_visit_dates_parse():
    visits = load_visits_for_group("kitkat")
    for v in visits:
        assert v["visit_date"] is not None, f"Date didn't parse: {v}"
        assert v["visit_date"].year >= 2025
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_load_visits_kitkat -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `load_visits_for_group`**

Add to `build_merchandising_impact.py`:

```python
# ── VISIT LOG ────────────────────────────────────────────────────────────────

VISIT_DATE_RE = re.compile(
    r"(?P<weekday>\w+),\s+(?P<month>\w+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})"
    r"(?:\s+(?P<hour>\d{1,2}):(?P<min>\d{2}))?"
)
MONTH_NAME_TO_NUM = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June",
     "July","August","September","October","November","December"], start=1)}


def parse_visit_datetime(s):
    """Parse strings like 'Thursday, April 30, 2026 09:30' → datetime, or None."""
    if not s:
        return None
    m = VISIT_DATE_RE.search(str(s))
    if not m:
        return None
    month_num = MONTH_NAME_TO_NUM.get(m.group("month").title())
    if not month_num:
        return None
    return datetime(int(m.group("year")), month_num, int(m.group("day")),
                    int(m.group("hour") or 0), int(m.group("min") or 0))


MERCH_ITEM_COLS = ["Floor Vinyls", "Vertical Colour Chart", "Horizontal Colour Chart",
                   "Shelf Wobblers", "Big Colour Chart", "Pricing Boards"]


def load_visits_for_group(group_key):
    """Read Merchandising_Visits_Log.xlsx and return visits for the named group.
    Each visit dict has: store_name, visit_date, duration_min, items_total, source."""
    g = GROUPS[group_key]
    patterns = [re.compile(p, re.IGNORECASE) for p in g["name_patterns"]]
    wb = openpyxl.load_workbook(VISITS_PATH, data_only=True)
    ws = wb["Merchandising Visits"]
    headers = [c.value for c in ws[1]]

    visits = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        rec = dict(zip(headers, row))
        store = str(rec.get("Store Name") or "")
        if not any(p.search(store) for p in patterns):
            continue
        visit_date = parse_visit_datetime(rec.get("Date Time Checked In"))
        if visit_date is None:
            continue
        # duration
        dur = rec.get("Visit Duration") or ""
        dur_min = 0
        if isinstance(dur, str) and ":" in dur:
            try:
                h, m = dur.split(":")
                dur_min = int(h) * 60 + int(m)
            except ValueError:
                dur_min = 0
        # merch items
        items_total = sum(int(rec.get(c) or 0) for c in MERCH_ITEM_COLS)
        visits.append({
            "store_name": store,
            "visit_date": visit_date,
            "duration_min": dur_min,
            "items_total": items_total,
            "source": rec.get("Source"),
        })
    return visits
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 5: Detect merchandising-era boundary per group

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
def test_merch_era_kitkat_starts_oct_2025():
    visits = load_visits_for_group("kitkat")
    start = merch_era_start(visits)
    assert start.year == 2025 and start.month == 10, f"Got {start}"

def test_merch_era_easybuild_starts_nov_2025():
    visits = load_visits_for_group("easybuild")
    start = merch_era_start(visits)
    assert start.year == 2025 and start.month == 11, f"Got {start}"
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_merch_era_kitkat_starts_oct_2025 -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `merch_era_start`**

Add to `build_merchandising_impact.py`:

```python
def merch_era_start(visits):
    """Return the first day of the calendar month containing the first visit."""
    if not visits:
        return None
    first = min(v["visit_date"] for v in visits)
    return datetime(first.year, first.month, 1)
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 6: YoY same-month comparison

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
import pandas as pd
from datetime import datetime

def _make_monthly(rows):
    df = pd.DataFrame(rows, columns=["year","month","ivnett"])
    df["period"] = pd.to_datetime(df["year"].astype(str)+"-"+df["month"].astype(str).str.zfill(2)+"-01")
    return df

def test_yoy_basic():
    monthly = _make_monthly([
        (2024, 10, 1_000_000),
        (2024, 11, 800_000),
        (2024, 12, 1_500_000),
        (2025, 10, 750_000),
        (2025, 11, 1_500_000),
        (2025, 12, 1_700_000),
    ])
    era_start = datetime(2025, 10, 1)
    yoy = compute_yoy(monthly, era_start)
    # 3 post-merch months
    assert len(yoy) == 3
    # First entry: Oct 2025 vs Oct 2024
    assert yoy[0]["post_period"] == datetime(2025, 10, 1)
    assert yoy[0]["prev_period"] == datetime(2024, 10, 1)
    assert yoy[0]["post_value"] == 750_000
    assert yoy[0]["prev_value"] == 1_000_000
    assert yoy[0]["pct"] == -0.25
    # Second entry: Nov 2025 vs Nov 2024 = +87.5%
    assert abs(yoy[1]["pct"] - 0.875) < 0.001

def test_yoy_real_data_kitkat_avg_positive():
    """Sanity check on real data — avg YoY for Kit Kat should be modestly positive."""
    df = load_sales_for_group(KIT_KAT_ACCOUNTS)
    monthly = monthly_sales(df)
    yoy = compute_yoy(monthly, datetime(2025, 10, 1))
    avg = sum(y["pct"] for y in yoy if y["prev_value"]) / len([y for y in yoy if y["prev_value"]])
    assert avg > 0.05, f"Expected modest YoY growth, got {avg:.1%}"
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_yoy_basic -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `compute_yoy`**

Add to `build_merchandising_impact.py`:

```python
def compute_yoy(monthly, era_start, today=None):
    """Compare each post-merch month to the same calendar month one year prior.
    Returns list of dicts: {post_period, prev_period, post_value, prev_value, pct}."""
    today = today or datetime.now()
    # Cut off the in-progress current month — incomplete data
    cutoff_month = datetime(today.year, today.month, 1)

    out = []
    by_period = {row["period"].to_pydatetime(): row["ivnett"]
                 for _, row in monthly.iterrows()}
    cursor = era_start
    while cursor < cutoff_month:
        prev = datetime(cursor.year - 1, cursor.month, 1)
        post_v = by_period.get(cursor, 0.0)
        prev_v = by_period.get(prev, 0.0)
        pct = ((post_v - prev_v) / prev_v) if prev_v else None
        out.append({
            "post_period": cursor,
            "prev_period": prev,
            "post_value":  post_v,
            "prev_value":  prev_v,
            "pct":         pct,
        })
        # advance one month
        if cursor.month == 12:
            cursor = datetime(cursor.year + 1, 1, 1)
        else:
            cursor = datetime(cursor.year, cursor.month + 1, 1)
    return out
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 7: Per-store filter and aggregation

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
def test_per_store_kitkat_includes_all_actives_and_subaccount_marker():
    df = load_sales_for_group(KIT_KAT_ACCOUNTS)
    rows = per_store_breakdown(df, era_start=datetime(2025, 10, 1), today=datetime(2026, 5, 8))
    accnos = [r["accno"] for r in rows]
    # Active accounts (KK021, KK022) must be present
    assert "KK021" in accnos
    assert "KK022" in accnos
    # Sub-accounts present with consolidated marker
    sub = next(r for r in rows if r["accno"] == "KK021/1")
    assert sub["consolidated_into"] == "KK021"
    # KK021 should be 'strong' (>15% growth post-merch)
    parent = next(r for r in rows if r["accno"] == "KK021")
    assert parent["status"] in ("strong", "mixed")  # data-dependent

def test_per_store_filter_excludes_dormant():
    """A synthetic test: a store with no recent sales must be filtered."""
    rows_in = pd.DataFrame([
        {"accno":"X1","trandate":pd.Timestamp("2024-03-15"),"ivnett":50_000},
        {"accno":"X1","trandate":pd.Timestamp("2024-04-15"),"ivnett":50_000},
        # No invoices in last 6 months
    ])
    rows = per_store_breakdown(rows_in,
                               era_start=datetime(2025, 10, 1),
                               today=datetime(2026, 5, 8))
    assert len(rows) == 0, "Dormant store should be filtered"
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_per_store_kitkat_includes_all_actives_and_subaccount_marker -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `per_store_breakdown`**

Add to `build_merchandising_impact.py`:

```python
def _months_between(d1, d2):
    """Number of calendar months between two datetimes (inclusive)."""
    return (d2.year - d1.year) * 12 + (d2.month - d1.month) + 1


def per_store_breakdown(df, era_start, today=None):
    """One row per account in the family. Returns list of dicts.
    Filter rule: store must be (a) active in last ACTIVE_RECENT_MONTHS months
    OR be a consolidated sub-account, AND (b) lifetime-avg ≥ ACTIVE_MIN_AVG_PER_MONTH.
    Sub-accounts always shown for completeness (with consolidated_into populated)."""
    today = today or datetime.now()
    cutoff_recent = today - timedelta(days=30 * ACTIVE_RECENT_MONTHS)
    rows = []
    for accno, sub in df.groupby("accno"):
        first = sub["trandate"].min()
        last  = sub["trandate"].max()
        total = sub["ivnett"].sum()
        months_active = max(_months_between(first, last), 1)
        avg_per_month = total / months_active
        is_consolidated = accno in CONSOLIDATED
        is_recent = last >= pd.Timestamp(cutoff_recent)
        # Filter
        if not is_consolidated and (not is_recent or avg_per_month < ACTIVE_MIN_AVG_PER_MONTH):
            continue
        # Pre/post averages
        pre  = sub[sub["trandate"] <  pd.Timestamp(era_start)]
        post = sub[sub["trandate"] >= pd.Timestamp(era_start)]
        pre_months  = max(_months_between(first, era_start - timedelta(days=1)), 1) if len(pre)  else 0
        post_months = max(_months_between(era_start, last), 1) if len(post) else 0
        pre_avg  = (pre["ivnett"].sum()  / pre_months)  if pre_months  else 0
        post_avg = (post["ivnett"].sum() / post_months) if post_months else 0
        pct = ((post_avg - pre_avg) / pre_avg) if pre_avg else None
        # Status badge
        if pct is None:
            status = "n/a"
        elif pct >= STATUS_STRONG_PCT:
            status = "strong"
        elif pct < STATUS_DECLINED_PCT:
            status = "declined"
        else:
            status = "mixed"
        # Store name: pull most-recent non-null
        name_series = sub["store_name"].dropna()
        store_name = name_series.iloc[-1] if len(name_series) else ""
        rows.append({
            "accno": accno,
            "store_name": store_name,
            "pre_avg": pre_avg,
            "post_avg": post_avg,
            "pct": pct,
            "status": status,
            "consolidated_into": CONSOLIDATED.get(accno, [None])[0],
            "consolidated_date": CONSOLIDATED.get(accno, [None, None])[1],
        })
    rows.sort(key=lambda r: -(r["post_avg"] or 0))
    return rows
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 8: Hero KPI calculator

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
def test_kpis_kitkat_shape():
    df = load_sales_for_group(KIT_KAT_ACCOUNTS)
    visits = load_visits_for_group("kitkat")
    monthly = monthly_sales(df)
    era_start = datetime(2025, 10, 1)
    kpis = compute_group_kpis(monthly, visits, era_start, today=datetime(2026, 5, 8))
    # Required keys
    for k in ("avg_yoy_pct","cumulative_extra_r","total_visits","r_per_visit",
              "post_months","unique_stores"):
        assert k in kpis, f"missing {k}"
    # Sanity bounds
    assert kpis["total_visits"] >= 30
    assert kpis["cumulative_extra_r"] != 0
    assert -0.5 < kpis["avg_yoy_pct"] < 1.0
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_kpis_kitkat_shape -v
```

Expected: FAIL.

- [ ] **Step 3: Implement `compute_group_kpis`**

Add to `build_merchandising_impact.py`:

```python
def compute_group_kpis(monthly, visits, era_start, today=None):
    """Hero metrics for one group: YoY %, cumulative incremental R, total visits, R/visit."""
    today = today or datetime.now()
    yoy = compute_yoy(monthly, era_start, today)
    valid = [y for y in yoy if y["prev_value"]]
    avg_yoy = (sum(y["pct"] for y in valid) / len(valid)) if valid else 0.0
    # Cumulative incremental: sum of (post - prev) over each YoY pair (only where prev exists)
    cumulative_extra = sum(y["post_value"] - y["prev_value"] for y in valid)
    total_visits = len(visits)
    post_months = len(yoy)
    r_per_visit = (cumulative_extra / total_visits) if total_visits else 0
    unique_stores = len({v["store_name"].strip().upper() for v in visits})
    return {
        "avg_yoy_pct": avg_yoy,
        "cumulative_extra_r": cumulative_extra,
        "total_visits": total_visits,
        "r_per_visit": r_per_visit,
        "post_months": post_months,
        "unique_stores": unique_stores,
        "yoy_rows": yoy,
    }
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 9: Auto-prose generators

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`
- Modify: `1.Projects/AWS Data/tests/test_merchandising_impact.py`

- [ ] **Step 1: Write the failing test**

```python
def test_prose_what_we_did():
    visits = [
        {"store_name":"Kitkat A","visit_date":datetime(2025,10,1),"duration_min":60,"items_total":3,"source":"x"},
        {"store_name":"Kitkat B","visit_date":datetime(2025,11,5),"duration_min":45,"items_total":5,"source":"x"},
        {"store_name":"Kitkat A","visit_date":datetime(2025,11,20),"duration_min":30,"items_total":2,"source":"x"},
    ]
    p = prose_what_we_did(visits, group_label="Kit Kat")
    assert "3 visits" in p
    assert "2 unique" in p  # 2 unique stores
    assert "Nov 2025" in p  # peak month

def test_prose_what_happened():
    yoy = [
        {"post_period": datetime(2025,10,1),"prev_period":datetime(2024,10,1),"post_value":750000,"prev_value":1000000,"pct":-0.25},
        {"post_period": datetime(2025,11,1),"prev_period":datetime(2024,11,1),"post_value":1500000,"prev_value":800000,"pct":0.875},
        {"post_period": datetime(2025,12,1),"prev_period":datetime(2024,12,1),"post_value":1700000,"prev_value":1500000,"pct":0.133},
    ]
    p = prose_what_happened(yoy)
    assert "2 of 3 months" in p  # 2 positive
    assert "+25.5%" in p or "+25.4%" in p  # avg of -0.25, +0.875, +0.133 ≈ +0.253
    assert "Nov 2025" in p  # strongest gain
```

- [ ] **Step 2: Run to verify failure**

```powershell
python -m pytest tests/test_merchandising_impact.py::test_prose_what_we_did -v
```

Expected: FAIL.

- [ ] **Step 3: Implement prose functions**

Add to `build_merchandising_impact.py`:

```python
# ── PROSE GENERATORS ─────────────────────────────────────────────────────────

def prose_what_we_did(visits, group_label):
    if not visits:
        return f"No {group_label} visits logged yet."
    visits_total = len(visits)
    unique_stores = len({v["store_name"].strip().upper() for v in visits})
    first_v = min(v["visit_date"] for v in visits)
    last_v  = max(v["visit_date"] for v in visits)
    by_month = defaultdict(int)
    for v in visits:
        by_month[(v["visit_date"].year, v["visit_date"].month)] += 1
    peak_ym, peak_count = max(by_month.items(), key=lambda kv: kv[1])
    peak_date = datetime(peak_ym[0], peak_ym[1], 1)
    avg_dur = sum(v["duration_min"] for v in visits) / visits_total
    return (
        f"{visits_total} visits across {unique_stores} unique {group_label} stores "
        f"between {first_v:%b %Y} and {last_v:%b %Y}, peaking in {peak_date:%b %Y} "
        f"with {peak_count} visits. Average visit duration {avg_dur:.0f} minutes."
    )


def prose_what_happened(yoy):
    valid = [y for y in yoy if y["prev_value"]]
    if not valid:
        return "Not enough overlapping prior-year data to compute YoY."
    positive = [y for y in valid if y["pct"] >= 0]
    avg_pct = sum(y["pct"] for y in valid) / len(valid)
    best = max(valid, key=lambda y: y["pct"])
    worst = min(valid, key=lambda y: y["pct"])
    negative_clause = (
        f"Weakest month: {worst['post_period']:%b %Y} ({worst['pct']:+.0%} vs {worst['prev_period']:%b %Y})."
        if worst["pct"] < 0
        else "All post-merch months were up YoY."
    )
    return (
        f"{len(positive)} of {len(valid)} months posted positive YoY growth, "
        f"averaging {avg_pct:+.1%}. Strongest gain: {best['post_period']:%b %Y} "
        f"({best['pct']:+.0%} vs {best['prev_period']:%b %Y}). {negative_clause}"
    )


def prose_per_store(rows):
    active = [r for r in rows if r["consolidated_into"] is None]
    if not active:
        return ""
    up = [r for r in active if r["pct"] is not None and r["pct"] > 0]
    declined = [r for r in active if r["pct"] is not None and r["pct"] < STATUS_DECLINED_PCT]
    best = max(active, key=lambda r: r["pct"] or -999)
    declined_clause = (
        f"{len(declined)} active store{'s' if len(declined)!=1 else ''} declined: "
        + ", ".join(f"{r['accno']} ({r['pct']:+.0%})" for r in declined) + "."
        if declined else "No active stores declined."
    )
    return (
        f"{len(up)} of {len(active)} active accounts are up post-merch. "
        f"Strongest mover: {best['accno']} at {best['pct']:+.0%}. "
        f"{declined_clause}"
    )
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest tests/test_merchandising_impact.py -v
```

Expected: all PASS.

---

## Task 10: HTML scaffold — boilerplate, theme tokens, theme toggle

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`

This task produces the static HTML wrapper (everything outside the tab content). No tests — visual verification only.

- [ ] **Step 1: Add the HTML render scaffold**

Append to `build_merchandising_impact.py`:

```python
# ── HTML RENDERING ───────────────────────────────────────────────────────────

CHART_PALETTE = {
    "yellow":     "#F5C400",
    "yellow_dim": "#FAE04D",
    "blue":       "#6B9ED0",
    "blue_dim":   "#1A3D6E",
    "green":      "#2D8C7A",
    "red":        "#E86060",
}


def html_head(title):
    return f"""<!DOCTYPE html>
<html lang="en" class="theme-navy">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
"""


def css_tokens():
    """Returns the full design-system token block for all four themes."""
    return """<style>
:root {
  --_y50:#FEF9E0;--_y100:#FDF0A0;--_y200:#FAE04D;--_y400:#F5C400;--_y600:#D4A800;--_y800:#A88000;--_y900:#6A5000;
  --_n50:#E8EFF8;--_n100:#B8CCE8;--_n300:#6B9ED0;--_n500:#2D6BA8;--_n700:#1A3D6E;--_n900:#0D2040;--_n950:#071022;
  --_g0:#FFFFFF;--_g50:#F7F6F3;--_g100:#E8E7E2;--_g200:#C8C7C0;--_g400:#949390;--_g600:#5C5B58;--_g800:#2E2E2C;--_g900:#1A1A18;--_g950:#0D0D0B;
  --_teal:#2D8C7A;--_teal-light:#C8EDE7;--_teal-dark:#1a5c50;--_coral:#E86060;
  --font-display:'Barlow Condensed',sans-serif;--font-body:'Barlow',sans-serif;
  --r-sm:4px;--r-md:8px;--r-lg:12px;--r-xl:16px;--r-pill:50px;
}
.theme-light{color-scheme:light;--color-surface-page:var(--_g50);--color-surface-base:var(--_g0);--color-surface-elevated:var(--_g0);--color-surface-sunken:var(--_g100);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g950);--color-text-secondary:var(--_g600);--color-text-tertiary:var(--_g400);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-default:var(--_g200);--color-border-subtle:var(--_g100);--shadow-card:0 2px 12px rgba(0,0,0,.07);}
.theme-dark{color-scheme:dark;--color-surface-page:var(--_g950);--color-surface-base:var(--_g900);--color-surface-elevated:var(--_g800);--color-surface-sunken:var(--_g950);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g100);--color-text-secondary:var(--_g400);--color-text-tertiary:var(--_g600);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-default:rgba(255,255,255,.10);--color-border-subtle:rgba(255,255,255,.06);--shadow-card:0 2px 12px rgba(0,0,0,.40);}
.theme-brand{color-scheme:light;--color-surface-page:var(--_y400);--color-surface-base:var(--_y200);--color-surface-elevated:var(--_y50);--color-surface-sunken:var(--_y600);--color-surface-secondary:var(--_g950);--color-text-primary:var(--_g950);--color-text-secondary:var(--_y900);--color-text-tertiary:var(--_y800);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_g950);--color-border-default:rgba(0,0,0,.14);--color-border-subtle:rgba(0,0,0,.08);--shadow-card:0 2px 12px rgba(0,0,0,.12);}
.theme-navy{color-scheme:dark;--color-surface-page:var(--_n950);--color-surface-base:var(--_n900);--color-surface-elevated:var(--_n700);--color-surface-sunken:var(--_n950);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g0);--color-text-secondary:var(--_n100);--color-text-tertiary:var(--_n300);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-border-default:rgba(107,158,208,.20);--color-border-subtle:rgba(107,158,208,.12);--shadow-card:0 2px 12px rgba(0,0,0,.50);}

*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-body);background:var(--color-surface-page);color:var(--color-text-primary);min-height:100vh}
.theme-bar{display:flex;gap:4px;padding:6px 40px;background:var(--color-surface-secondary);border-bottom:1px solid var(--color-border-subtle)}
.theme-bar button{background:transparent;border:1px solid transparent;color:var(--color-text-on-navy);opacity:.55;padding:4px 12px;border-radius:4px;font-family:var(--font-body);font-size:11px;font-weight:600;cursor:pointer;transition:all .15s}
.theme-bar button:hover{opacity:1}
.theme-bar button.active{opacity:1;border-color:var(--color-brand-primary);color:var(--color-brand-primary)}
.hdr{background:var(--color-surface-secondary);padding:20px 40px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--color-brand-primary);box-shadow:0 4px 20px rgba(0,0,0,.4)}
.hdr-l{display:flex;align-items:center;gap:14px}
.hdr-title{font-family:var(--font-display);font-size:24px;font-weight:900;text-transform:uppercase;letter-spacing:.05em;color:var(--color-text-on-navy)}
.hdr-sub{font-size:12px;color:rgba(255,255,255,.5);margin-top:2px}
.hdr-meta{font-size:11px;color:rgba(255,255,255,.35);text-align:right}
.tab-bar{background:var(--color-surface-sunken);padding:0 40px;display:flex;gap:2px;border-bottom:1px solid var(--color-border-subtle)}
.tab-btn{background:transparent;border:none;color:var(--color-text-secondary);padding:14px 22px;font-family:var(--font-display);font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s}
.tab-btn:hover{color:var(--color-text-primary)}
.tab-btn.active{color:var(--color-brand-primary);border-bottom-color:var(--color-brand-primary)}
.tab-panel{display:none;padding:32px 40px}
.tab-panel.active{display:block}
.hero{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.hero-card{background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-radius:var(--r-lg);padding:18px;box-shadow:var(--shadow-card)}
.hero-label{font-family:var(--font-display);font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--color-text-secondary);margin-bottom:6px}
.hero-value{font-family:var(--font-display);font-size:32px;font-weight:900;color:var(--color-brand-primary)}
.section-title{font-family:var(--font-display);font-size:20px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin:24px 0 10px}
.prose{font-size:14px;color:var(--color-text-secondary);line-height:1.5;margin-bottom:18px}
.chart-container{background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-radius:var(--r-lg);padding:16px;margin-bottom:18px}
.chart-title{font-family:var(--font-display);font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--color-text-secondary);margin-bottom:8px}
table{width:100%;border-collapse:collapse;background:var(--color-surface-elevated);border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--shadow-card)}
th{background:var(--color-surface-sunken);text-align:left;padding:10px 14px;font-family:var(--font-display);font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-secondary)}
td{padding:10px 14px;border-top:1px solid var(--color-border-subtle);font-size:14px}
.badge{display:inline-block;padding:3px 10px;border-radius:var(--r-pill);font-size:11px;font-weight:600}
.badge-strong{background:rgba(45,140,122,.15);color:var(--_teal-light);border:1px solid rgba(45,140,122,.35)}
.badge-mixed{background:rgba(245,196,0,.12);color:var(--_y200);border:1px solid rgba(245,196,0,.30)}
.badge-declined{background:rgba(232,96,96,.14);color:rgba(253,220,220,1);border:1px solid rgba(232,96,96,.35)}
details{background:var(--color-surface-elevated);border:1px solid var(--color-border-subtle);border-radius:var(--r-lg);padding:14px;margin-top:24px;font-size:13px;color:var(--color-text-secondary)}
summary{cursor:pointer;font-family:var(--font-display);font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--color-text-primary)}
</style>
"""


def html_header_bar(generated_ts):
    return f"""<div class="theme-bar">
  <button onclick="olyTheme('theme-light',this)">Light</button>
  <button onclick="olyTheme('theme-dark',this)">Dark</button>
  <button onclick="olyTheme('theme-brand',this)">Brand</button>
  <button onclick="olyTheme('theme-navy',this)" class="active">Navy</button>
</div>
<div class="hdr">
  <div class="hdr-l">
    <div style="width:48px;height:48px;border-radius:50%;overflow:hidden;flex-shrink:0;">
      <img src="logo.jpg" alt="Olympic Paints" width="48" height="48" style="display:block;width:100%;height:100%;object-fit:cover;">
    </div>
    <div>
      <div class="hdr-title">Merchandising Impact Report</div>
      <div class="hdr-sub">Kit Kat &amp; Easy Build — sales correlation with formal merchandising visits</div>
    </div>
  </div>
  <div class="hdr-meta">Generated {generated_ts}<br>Source: AWS sales · Visits log</div>
</div>"""


def html_footer_scripts():
    return """<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}
function showTab(name,btn){
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('active',p.id==='tab-'+name));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.toggle('active',b===btn));
}
// Chart.js label plugin (per design system)
const barLabels = {
  id:'barLabels',
  afterDatasetsDraw(chart){
    const {ctx} = chart;
    ctx.save();
    ctx.font='600 11px Barlow';
    chart.data.datasets.forEach((ds,di)=>{
      const meta = chart.getDatasetMeta(di);
      meta.data.forEach((bar,i)=>{
        const v = ds.data[i];
        const lbl = (chart._lblMap && chart._lblMap.get(`${di}:${i}`)) ?? null;
        if(lbl===null) return;
        const {x,y,base} = bar.getProps(['x','y','base']);
        const fits = Math.abs(base - y) > 24;
        ctx.fillStyle = fits ? '#0D2040' : '#F5C400';
        ctx.textAlign='center';
        ctx.textBaseline = fits ? 'middle' : 'bottom';
        const yy = fits ? (y+base)/2 : y-4;
        ctx.fillText(lbl, x, yy);
      });
    });
    ctx.restore();
  }
};
Chart.register(barLabels);
Chart.defaults.font.family = 'Barlow';
Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--color-text-secondary').trim() || '#B8CCE8';
</script>"""
```

- [ ] **Step 2: Smoke check — make sure the script still runs without errors**

```powershell
python build_merchandising_impact.py
```

Expected: prints `[YYYY-MM-DD HH:MM] Building Merchandising Impact Report...` and exits cleanly (no rendering yet).

---

## Task 11: HTML render — Overview tab

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`

- [ ] **Step 1: Add `render_overview_tab` function**

Append:

```python
def fmt_r(val):
    if val is None: return "—"
    sign = "-" if val < 0 else ""
    v = abs(val)
    if v >= 1_000_000: return f"{sign}R{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{sign}R{v/1_000:.0f}K"
    return f"{sign}R{v:.0f}"


def fmt_pct(val):
    if val is None: return "—"
    return f"{val:+.1%}"


def render_overview_tab(kk_kpis, eb_kpis, era_summary):
    """era_summary: e.g. 'Oct 2025 → present (7 months)'"""
    # Combined headline
    total_visits = kk_kpis["total_visits"] + eb_kpis["total_visits"]
    total_extra  = kk_kpis["cumulative_extra_r"] + eb_kpis["cumulative_extra_r"]
    # Average YoY weighted by post-period revenue
    kk_w = kk_kpis["cumulative_extra_r"] + (kk_kpis.get("post_total_revenue") or 1)
    eb_w = eb_kpis["cumulative_extra_r"] + (eb_kpis.get("post_total_revenue") or 1)
    if (kk_w + eb_w) > 0:
        combined_yoy = (kk_kpis["avg_yoy_pct"] * kk_w + eb_kpis["avg_yoy_pct"] * eb_w) / (kk_w + eb_w)
    else:
        combined_yoy = (kk_kpis["avg_yoy_pct"] + eb_kpis["avg_yoy_pct"]) / 2
    r_per_visit = (total_extra / total_visits) if total_visits else 0

    exec_summary = (
        f"Since formal merchandising began in {era_summary}, Kit Kat revenue is "
        f"{fmt_pct(kk_kpis['avg_yoy_pct'])} YoY and Easy Build is "
        f"{fmt_pct(eb_kpis['avg_yoy_pct'])} YoY — a combined {fmt_r(total_extra)} "
        f"of incremental revenue across {total_visits} logged visits. The data "
        f"{'supports' if combined_yoy > 0 else 'does not yet support'} continued investment in the program."
    )

    return f"""<div id="tab-overview" class="tab-panel active">
  <div class="hero">
    <div class="hero-card"><div class="hero-label">Reporting Window</div><div class="hero-value" style="font-size:18px;">{era_summary}</div></div>
    <div class="hero-card"><div class="hero-label">Combined YoY</div><div class="hero-value">{fmt_pct(combined_yoy)}</div></div>
    <div class="hero-card"><div class="hero-label">Extra Revenue</div><div class="hero-value">{fmt_r(total_extra)}</div></div>
    <div class="hero-card"><div class="hero-label">{total_visits} Visits · {fmt_r(r_per_visit)}/visit</div><div class="hero-value" style="font-size:18px;">all rep NP</div></div>
  </div>
  <div class="section-title">Executive Summary</div>
  <p class="prose">{exec_summary}</p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px;">
    <div class="chart-container">
      <div class="chart-title">Kit Kat — at a glance</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;">
        <div><strong style="color:var(--color-brand-primary);font-size:18px;">{fmt_pct(kk_kpis['avg_yoy_pct'])}</strong><br>YoY growth</div>
        <div><strong style="color:var(--color-brand-primary);font-size:18px;">{fmt_r(kk_kpis['cumulative_extra_r'])}</strong><br>extra revenue</div>
        <div><strong>{kk_kpis['total_visits']}</strong> visits</div>
        <div><strong>{fmt_r(kk_kpis['r_per_visit'])}</strong>/visit</div>
      </div>
      <div style="margin-top:10px;"><a href="#" onclick="document.querySelectorAll('.tab-btn')[1].click();return false;" style="color:var(--color-brand-primary);font-weight:600;">View full Kit Kat report →</a></div>
    </div>
    <div class="chart-container">
      <div class="chart-title">Easy Build — at a glance</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;">
        <div><strong style="color:var(--color-brand-primary);font-size:18px;">{fmt_pct(eb_kpis['avg_yoy_pct'])}</strong><br>YoY growth</div>
        <div><strong style="color:var(--color-brand-primary);font-size:18px;">{fmt_r(eb_kpis['cumulative_extra_r'])}</strong><br>extra revenue</div>
        <div><strong>{eb_kpis['total_visits']}</strong> visits</div>
        <div><strong>{fmt_r(eb_kpis['r_per_visit'])}</strong>/visit</div>
      </div>
      <div style="margin-top:10px;"><a href="#" onclick="document.querySelectorAll('.tab-btn')[2].click();return false;" style="color:var(--color-brand-primary);font-weight:600;">View full Easy Build report →</a></div>
    </div>
  </div>
  {render_methodology_footnote()}
</div>"""


def render_methodology_footnote():
    return """<details>
<summary>Methodology &amp; Caveats</summary>
<ul style="margin-top:10px;padding-left:18px;line-height:1.6;">
<li><strong>Account list (Kit Kat):</strong> KK021, KK021/1, KK021/2, KK021/4, KK022. Sub-accounts (/1, /2, /4) consolidated into KK021 in Feb 2025.</li>
<li><strong>Account list (Easy Build):</strong> KE005, KE005/1, KE008, KE009, KE010, KE012, KE023. KE005/1 consolidated into KE005 in Jan 2025.</li>
<li><strong>Excluded:</strong> KE035 (Easytile &amp; Sanware — different customer).</li>
<li><strong>Sales source:</strong> <code>Sales_Invoices_All.parquet</code> — accno-based filter.</li>
<li><strong>Visits source:</strong> <code>Merchandising_Visits_Log.xlsx</code> — store-name regex match.</li>
<li><strong>Comparison method:</strong> Year-over-year same-month comparison, post-merchandising months only.</li>
<li><strong>Caveat:</strong> April 2026 visit data may be incomplete (known Zoho export gap).</li>
<li><strong>Caveat:</strong> Correlation, not causation. Other factors (macro, pricing, rep effort) may contribute.</li>
</ul>
</details>"""
```

- [ ] **Step 2: Smoke check the script still runs**

```powershell
python build_merchandising_impact.py
```

Expected: clean exit.

---

## Task 12: HTML render — group tab (shared template)

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`

- [ ] **Step 1: Add `render_group_tab` function**

```python
def render_group_tab(group_key, group_label, kpis, prose1, prose2, prose3, store_rows,
                     monthly_sales_df, visits, yoy_rows, era_start, is_active=False):
    # Prepare data for charts
    sales_labels = [p.strftime('%b %y') for p in monthly_sales_df["period"]]
    sales_values = monthly_sales_df["ivnett"].tolist()
    pre_post = ['pre' if p.to_pydatetime() < era_start else 'post' for p in monthly_sales_df["period"]]
    bar_colors = [CHART_PALETTE['blue'] if pp == 'pre' else CHART_PALETTE['yellow'] for pp in pre_post]
    # Visits per month (post-merch only)
    from collections import defaultdict as dd
    by_month = dd(int)
    for v in visits:
        by_month[(v["visit_date"].year, v["visit_date"].month)] += 1
    visit_values = []
    for p in monthly_sales_df["period"]:
        ym = (p.year, p.month)
        visit_values.append(by_month.get(ym, 0))
    # YoY
    yoy_labels = [y["post_period"].strftime('%b %y') for y in yoy_rows]
    yoy_values = [(y["pct"] or 0) * 100 for y in yoy_rows]
    yoy_colors = [CHART_PALETTE['green'] if v >= 0 else CHART_PALETTE['red'] for v in yoy_values]

    # Per-store table rows
    table_rows = []
    for r in store_rows:
        if r["consolidated_into"]:
            post_cell = f"<em style='color:var(--color-text-tertiary);font-size:12px;'>consolidated {r['consolidated_date']} into {r['consolidated_into']}</em>"
            pct_cell = "—"
            badge = ""
            visits_cell = "—"
        else:
            post_cell = fmt_r(r["post_avg"])
            pct_cell = fmt_pct(r["pct"])
            badge_class = {"strong":"badge-strong","mixed":"badge-mixed","declined":"badge-declined","n/a":"badge-mixed"}[r["status"]]
            badge_label = {"strong":"🟢 Strong","mixed":"🟡 Mixed","declined":"🔴 Declined","n/a":"n/a"}[r["status"]]
            badge = f"<span class='badge {badge_class}'>{badge_label}</span>"
            visits_for_store = sum(1 for v in visits if r["store_name"] and r["store_name"].split()[0].upper() in v["store_name"].upper())
            visits_cell = str(visits_for_store)
        table_rows.append(
            f"<tr><td><code>{r['accno']}</code></td>"
            f"<td>{r['store_name'] or '—'}</td>"
            f"<td>{fmt_r(r['pre_avg'])}</td>"
            f"<td>{post_cell}</td>"
            f"<td>{pct_cell}</td>"
            f"<td>{visits_cell}</td>"
            f"<td>{badge}</td></tr>"
        )
    table_html = "\n".join(table_rows)

    panel_class = "tab-panel active" if is_active else "tab-panel"
    cid = group_key  # canvas-id prefix

    return f"""<div id="tab-{group_key}" class="{panel_class}">
  <div class="hero">
    <div class="hero-card"><div class="hero-label">YoY Growth</div><div class="hero-value">{fmt_pct(kpis['avg_yoy_pct'])}</div></div>
    <div class="hero-card"><div class="hero-label">Cumulative Extra</div><div class="hero-value">{fmt_r(kpis['cumulative_extra_r'])}</div></div>
    <div class="hero-card"><div class="hero-label">Visits</div><div class="hero-value">{kpis['total_visits']}</div></div>
    <div class="hero-card"><div class="hero-label">R per Visit</div><div class="hero-value">{fmt_r(kpis['r_per_visit'])}</div></div>
  </div>

  <div class="section-title">1 — What we did</div>
  <p class="prose">{prose1}</p>
  <div class="chart-container">
    <div class="chart-title">Visits per Month — {group_label}</div>
    <canvas id="{cid}-visits" height="80"></canvas>
  </div>

  <div class="section-title">2 — What happened</div>
  <p class="prose">{prose2}</p>
  <div class="chart-container">
    <div class="chart-title">Monthly Sales — {group_label} (yellow = merchandising era)</div>
    <canvas id="{cid}-sales" height="100"></canvas>
  </div>
  <div class="chart-container">
    <div class="chart-title">YoY Same-Month % — {group_label}</div>
    <canvas id="{cid}-yoy" height="80"></canvas>
  </div>

  <div class="section-title">3 — Per-store breakdown</div>
  <p class="prose">{prose3}</p>
  <table>
    <thead>
      <tr><th>Acc#</th><th>Store</th><th>Pre-merch avg/mo</th><th>Post-merch avg/mo</th><th>%∆</th><th>Visits</th><th>Status</th></tr>
    </thead>
    <tbody>
      {table_html}
    </tbody>
  </table>

  {render_methodology_footnote()}

  <script>
  (function() {{
    new Chart(document.getElementById('{cid}-sales'),{{
      type:'bar',
      data:{{ labels:{sales_labels!r}, datasets:[{{label:'Sales',data:{sales_values!r},backgroundColor:{bar_colors!r}}}]}},
      options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>'R'+(v/1e6).toFixed(1)+'M'}}}}}}}}
    }});
    new Chart(document.getElementById('{cid}-visits'),{{
      type:'bar',
      data:{{ labels:{sales_labels!r}, datasets:[{{label:'Visits',data:{visit_values!r},backgroundColor:'{CHART_PALETTE['yellow_dim']}'}}]}},
      options:{{plugins:{{legend:{{display:false}}}}}}
    }});
    new Chart(document.getElementById('{cid}-yoy'),{{
      type:'bar',
      data:{{ labels:{yoy_labels!r}, datasets:[{{label:'YoY %',data:{yoy_values!r},backgroundColor:{yoy_colors!r}}}]}},
      options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>v.toFixed(0)+'%'}}}}}}}}
    }});
  }})();
  </script>
</div>"""
```

- [ ] **Step 2: Smoke check**

```powershell
python build_merchandising_impact.py
```

Expected: clean exit.

---

## Task 13: Build orchestration — `build_html()` and main loop

**Files:**
- Modify: `1.Projects/AWS Data/build_merchandising_impact.py`

- [ ] **Step 1: Add `build_html()` and update `main()`**

```python
def build_html():
    """Top-level: load data for both groups, compute, render full HTML."""
    today = datetime.now()
    # Load both groups
    kk_df    = load_sales_for_group(KIT_KAT_ACCOUNTS)
    eb_df    = load_sales_for_group(EASY_BUILD_ACCOUNTS)
    kk_visits = load_visits_for_group("kitkat")
    eb_visits = load_visits_for_group("easybuild")
    kk_monthly = monthly_sales(kk_df)
    eb_monthly = monthly_sales(eb_df)
    kk_era = merch_era_start(kk_visits)
    eb_era = merch_era_start(eb_visits)

    kk_kpis = compute_group_kpis(kk_monthly, kk_visits, kk_era, today)
    eb_kpis = compute_group_kpis(eb_monthly, eb_visits, eb_era, today)
    # Append post_total_revenue for overview weighting
    kk_kpis["post_total_revenue"] = kk_monthly[kk_monthly["period"] >= pd.Timestamp(kk_era)]["ivnett"].sum()
    eb_kpis["post_total_revenue"] = eb_monthly[eb_monthly["period"] >= pd.Timestamp(eb_era)]["ivnett"].sum()

    kk_stores = per_store_breakdown(kk_df, kk_era, today)
    eb_stores = per_store_breakdown(eb_df, eb_era, today)

    kk_p1 = prose_what_we_did(kk_visits, "Kit Kat")
    kk_p2 = prose_what_happened(kk_kpis["yoy_rows"])
    kk_p3 = prose_per_store(kk_stores)
    eb_p1 = prose_what_we_did(eb_visits, "Easy Build")
    eb_p2 = prose_what_happened(eb_kpis["yoy_rows"])
    eb_p3 = prose_per_store(eb_stores)

    era_summary = f"{kk_era:%b %Y} → present ({kk_kpis['post_months']} months)"
    generated_ts = today.strftime("%Y-%m-%d %H:%M")

    overview = render_overview_tab(kk_kpis, eb_kpis, era_summary)
    kk_tab   = render_group_tab("kitkat",   "Kit Kat",   kk_kpis, kk_p1, kk_p2, kk_p3, kk_stores, kk_monthly, kk_visits, kk_kpis["yoy_rows"], kk_era)
    eb_tab   = render_group_tab("easybuild","Easy Build", eb_kpis, eb_p1, eb_p2, eb_p3, eb_stores, eb_monthly, eb_visits, eb_kpis["yoy_rows"], eb_era)

    return f"""{html_head("Merchandising Impact Report")}
{css_tokens()}
</head>
<body>
{html_header_bar(generated_ts)}
<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab('overview',this)">Overview</button>
  <button class="tab-btn" onclick="showTab('kitkat',this)">Kit Kat</button>
  <button class="tab-btn" onclick="showTab('easybuild',this)">Easy Build</button>
</div>
{overview}
{kk_tab}
{eb_tab}
{html_footer_scripts()}
</body></html>"""


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] Building Merchandising Impact Report...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Copy logo
    shutil.copy2(LOGO_SRC, OUT_DIR / "logo.jpg")
    # Render
    html = build_html()
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"  OK Written: {OUT_DIR/'index.html'}")
    # Deploy
    git_push(OUT_DIR)
    print("  Done.")
```

- [ ] **Step 2: Add the `git_push` function (copied pattern from build_kpi_dashboard.py)**

```python
def _flomatic_token():
    """Retrieve the FlomaticAuto PAT from the GitHub CLI keyring."""
    try:
        r = subprocess.run(["gh","auth","token","--user","FlomaticAuto"],
                           capture_output=True, text=True, shell=True)
        token = r.stdout.strip()
        if r.returncode == 0 and token.startswith("gho_"):
            return token
    except Exception as e:
        print(f"  [WARN] could not get FlomaticAuto token: {e}")
    return None


def git_push(path: Path):
    cwd = str(path)
    msg = f"Merchandising Impact Report — {datetime.now():%Y-%m-%d %H:%M}"
    token = _flomatic_token()

    def run(cmd):
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if r.returncode != 0:
            err = r.stderr.strip()
            if token: err = err.replace(token, "***")
            print(f"  [WARN] {' '.join(cmd)}: {err}")
        return r.returncode == 0

    run(["git", "config", "user.email", "auto@olympic-paints.local"])
    run(["git", "config", "user.name",  "Olympic Merchandising Bot"])
    run(["git", "add", "index.html"])
    run(["git", "add", "logo.jpg"])
    run(["git", "commit", "-m", msg])

    push_cmd = ["git", "push", "origin", "main"]
    if token:
        authed = f"https://FlomaticAuto:{token}@github.com/FlomaticAuto/olympic-paints-merchandising.git"
        push_cmd = ["git", "push", authed, "main"]
    ok = run(push_cmd)
    if ok:
        print(f"  ✓ Pushed to GitHub")
```

- [ ] **Step 3: Run end-to-end**

```powershell
python build_merchandising_impact.py
```

Expected: builds, writes `merchandising-impact/index.html`, pushes to GitHub. Open `https://flomaticauto.github.io/olympic-paints-merchandising/` in browser — should display the dashboard within 1–2 minutes of push.

- [ ] **Step 4: Visual smoke test in browser**

Open the live URL in a browser. Verify:
- Header with logo and title renders
- Three tabs work (Overview, Kit Kat, Easy Build)
- Hero KPI band shows non-zero values
- All four theme toggles (Light/Dark/Brand/Navy) work
- Charts render
- Per-store table populated with rows for both KK021/KK022 and the 6+ Easy Build stores

If anything's wrong: fix and re-run.

---

## Task 14: Trigger service skeleton with `/health`

**Files:**
- Create: `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server.py`
- Create: `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server_test.py`

- [ ] **Step 1: Write the failing test**

Create `scripts/portal_trigger_server_test.py`:

```python
"""Smoke tests for portal_trigger_server. Requires `pip install flask requests`.
Run while the server is NOT running; the test starts it itself in a thread."""
import threading
import time
import requests
import pytest

@pytest.fixture(scope="module")
def server():
    from portal_trigger_server import app
    t = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8765, debug=False, use_reloader=False), daemon=True)
    t.start()
    time.sleep(1)
    yield "http://127.0.0.1:8765"

def test_health(server):
    r = requests.get(f"{server}/health", timeout=2)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "merchandising" in j["builds"]
```

- [ ] **Step 2: Run to verify failure**

```powershell
cd C:\Users\quint\workspace-dashboard\scripts
python -m pytest portal_trigger_server_test.py -v
```

Expected: FAIL (`ImportError`).

- [ ] **Step 3: Create the trigger server**

Create `scripts/portal_trigger_server.py`:

```python
"""
portal_trigger_server.py
Local Flask trigger server for the Olympic Paints workspace portal.
Runs on 127.0.0.1:8765. Exposes /health, /trigger/<key>, /status/<job_id>.
Auto-started at Windows login via Task Scheduler (see install_trigger_task.ps1).
"""
import subprocess
import threading
import uuid
from datetime import datetime
from collections import deque

from flask import Flask, jsonify, request

app = Flask(__name__)

# Build registry — extend by adding entries here
BUILDS = {
    "merchandising": {
        "label": "Merchandising Impact Report",
        "cmd": [
            "python",
            r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\build_merchandising_impact.py",
        ],
    },
}

# In-memory job state. Restart loses history.
JOBS = {}  # job_id → {state, started_at, finished_at, log_tail (deque), build_key}


@app.route("/health")
def health():
    return jsonify(ok=True, builds=list(BUILDS.keys()))


@app.route("/trigger/<build_key>", methods=["POST"])
def trigger(build_key):
    if build_key not in BUILDS:
        return jsonify(error=f"unknown build: {build_key}"), 404
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "state": "running",
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "log_tail": deque(maxlen=20),
        "build_key": build_key,
    }
    threading.Thread(target=_run_job, args=(job_id, build_key), daemon=True).start()
    return jsonify(job_id=job_id), 202


@app.route("/status/<job_id>")
def status(job_id):
    j = JOBS.get(job_id)
    if not j:
        return jsonify(error="unknown job"), 404
    return jsonify(
        state=j["state"],
        started_at=j["started_at"],
        finished_at=j["finished_at"],
        log_tail=list(j["log_tail"]),
        build_key=j["build_key"],
    )


def _run_job(job_id, build_key):
    cmd = BUILDS[build_key]["cmd"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            JOBS[job_id]["log_tail"].append(line.rstrip())
        proc.wait()
        JOBS[job_id]["state"] = "success" if proc.returncode == 0 else "error"
    except Exception as exc:
        JOBS[job_id]["log_tail"].append(f"EXCEPTION: {exc}")
        JOBS[job_id]["state"] = "error"
    finally:
        JOBS[job_id]["finished_at"] = datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
```

- [ ] **Step 4: Run to verify pass**

```powershell
python -m pytest portal_trigger_server_test.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit (in workspace-dashboard repo, which IS git)**

```powershell
cd C:\Users\quint\workspace-dashboard
git add scripts/portal_trigger_server.py scripts/portal_trigger_server_test.py
git commit -m "Add portal trigger server (Flask, /health endpoint)"
```

---

## Task 15: Trigger service — `/trigger` and `/status` end-to-end

**Files:**
- Modify: `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server_test.py`

- [ ] **Step 1: Add tests for the trigger and status endpoints**

```python
def test_trigger_unknown_build(server):
    r = requests.post(f"{server}/trigger/nonexistent", timeout=2)
    assert r.status_code == 404

def test_trigger_starts_job_and_status_reflects_state(server, monkeypatch):
    # Override the build registry to use a quick echo command, not the real builder
    from portal_trigger_server import BUILDS
    BUILDS["test_echo"] = {"label":"test","cmd":["python","-c","print('hello')"]}
    r = requests.post(f"{server}/trigger/test_echo", timeout=2)
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    # Poll until done (max 5s)
    import time
    for _ in range(25):
        s = requests.get(f"{server}/status/{job_id}", timeout=2).json()
        if s["state"] in ("success","error"):
            break
        time.sleep(0.2)
    assert s["state"] == "success", f"Expected success, got {s}"
    assert any("hello" in line for line in s["log_tail"])

def test_status_unknown_job(server):
    r = requests.get(f"{server}/status/notarealjob", timeout=2)
    assert r.status_code == 404
```

- [ ] **Step 2: Run to verify pass**

```powershell
python -m pytest portal_trigger_server_test.py -v
```

Expected: 4 PASS (health + 3 new).

- [ ] **Step 3: Manual smoke test against the real merchandising build**

Start the server:

```powershell
python scripts/portal_trigger_server.py
```

In a separate terminal:

```powershell
curl -X POST http://127.0.0.1:8765/trigger/merchandising
# capture the job_id from the response, then:
curl http://127.0.0.1:8765/status/<job_id>
```

Expected: state cycles `running` → `success` over ~30–60s. Log tail shows build script output. The live GitHub Pages URL refreshes after the push completes.

- [ ] **Step 4: Commit**

```powershell
git add scripts/portal_trigger_server_test.py
git commit -m "Add trigger & status endpoints with end-to-end tests"
```

---

## Task 16: Portal — add Merchandising Impact tile (HTML)

**Files:**
- Modify: `C:\Users\quint\workspace-dashboard\portal.html`

The portal uses a "report card" pattern. Find an existing card (e.g. the Sales Performance Dashboard) and copy its structure, then customise.

- [ ] **Step 1: Find the existing Sales tab content block**

```powershell
grep -n "olympic-paints-sales" C:\Users\quint\workspace-dashboard\portal.html | head -5
```

Locate the first occurrence inside the **"All Reports"** tab section (around line 386 per earlier inspection) and the duplicate inside the **"Sales"** tab (around line 606).

- [ ] **Step 2: Add a new tile under both sections**

Just **after** the existing "Sales Performance Dashboard" card in **both** the All Reports section AND the Sales section, insert:

```html
<div class="report-card">
  <div class="card-header">
    <span class="report-icon">📈</span>
    <span class="report-cat cat-sales">SALES</span>
  </div>
  <div class="report-title">Merchandising Impact Report</div>
  <div class="report-desc">Quantifies sales-growth correlation with formal merchandising at Kit Kat and Easy Build group stores. YoY same-month comparison, per-store breakdown, navy executive theme. On-demand regeneration.</div>
  <div class="report-meta">
    <span class="meta-item"><span class="health-dot" data-build="merchandising"></span><span class="health-text" data-build="merchandising">Service offline</span></span>
    <span class="meta-item">On-demand</span>
  </div>
  <div class="card-actions">
    <a class="open-btn btn-sales" href="https://flomaticauto.github.io/olympic-paints-merchandising/" target="_blank" rel="noopener">Open Report ↗</a>
    <button class="regen-btn" data-build="merchandising">Regenerate ↻</button>
  </div>
</div>
```

- [ ] **Step 3: Add CSS for the new button and health dot**

Locate the `<style>` block in `portal.html` and append:

```css
.regen-btn{background:transparent;border:1px solid var(--color-brand-primary);color:var(--color-brand-primary);padding:6px 14px;border-radius:var(--r-md);font-family:var(--font-body);font-size:12px;font-weight:600;cursor:pointer;margin-left:8px;transition:all .15s}
.regen-btn:hover:not(:disabled){background:var(--color-brand-primary);color:var(--color-surface-page)}
.regen-btn:disabled{opacity:.4;cursor:not-allowed}
.regen-btn.is-running{background:var(--color-brand-primary);color:var(--color-surface-page);}
.regen-btn.is-running::after{content:'';display:inline-block;width:8px;height:8px;border:1.5px solid currentColor;border-top-color:transparent;border-radius:50%;margin-left:6px;animation:spin 1s linear infinite;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg)}}
.regen-btn.is-success{background:#2D8C7A;border-color:#2D8C7A;color:#fff}
.regen-btn.is-error{background:#E86060;border-color:#E86060;color:#fff}
.health-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#5C5B58;margin-right:6px;vertical-align:middle}
.health-dot.is-up{background:#2D8C7A;box-shadow:0 0 0 2px rgba(45,140,122,.25)}
.card-actions{display:flex;align-items:center;margin-top:12px}
```

- [ ] **Step 4: Visual smoke test**

Open `portal.html` in browser. Expect:
- New tile appears in both "All Reports" and "Sales" sections
- Health dot is grey (server not yet running)
- "Regenerate" button visible but does nothing yet (JS in next task)

- [ ] **Step 5: Commit**

```powershell
cd C:\Users\quint\workspace-dashboard
git add portal.html
git commit -m "Add Merchandising Impact tile to portal (HTML + CSS)"
```

---

## Task 17: Portal — JS for health check + trigger button + polling

**Files:**
- Modify: `C:\Users\quint\workspace-dashboard\portal.html`

- [ ] **Step 1: Add the JS at the bottom of the existing `<script>` block**

Locate the closing `</script>` tag near the end of `portal.html`, and insert this code **before** the closing `</script>`:

```javascript
// ── PORTAL TRIGGER WIRING ────────────────────────────────────────────────
const TRIGGER_BASE = 'http://127.0.0.1:8765';

async function pollHealth() {
  try {
    const r = await fetch(`${TRIGGER_BASE}/health`, {cache:'no-store'});
    if (!r.ok) throw 0;
    const j = await r.json();
    document.querySelectorAll('.health-dot').forEach(d => {
      const k = d.dataset.build;
      const up = j.builds.includes(k);
      d.classList.toggle('is-up', up);
      const txt = d.parentElement.querySelector('.health-text');
      if (txt) txt.textContent = up ? 'Service online' : 'Build not registered';
      const btn = document.querySelector(`.regen-btn[data-build="${k}"]`);
      if (btn) btn.disabled = !up;
    });
  } catch(e) {
    document.querySelectorAll('.health-dot').forEach(d => d.classList.remove('is-up'));
    document.querySelectorAll('.health-text').forEach(t => t.textContent = 'Service offline');
    document.querySelectorAll('.regen-btn').forEach(b => b.disabled = true);
  }
}

async function triggerBuild(btn) {
  const key = btn.dataset.build;
  btn.classList.remove('is-success','is-error');
  btn.classList.add('is-running');
  btn.textContent = 'Generating';
  try {
    const r = await fetch(`${TRIGGER_BASE}/trigger/${key}`, {method:'POST'});
    if (!r.ok) throw new Error(`trigger failed: ${r.status}`);
    const {job_id} = await r.json();
    await pollJob(btn, job_id);
  } catch(e) {
    btn.classList.remove('is-running');
    btn.classList.add('is-error');
    btn.textContent = 'Failed';
    btn.title = String(e);
    setTimeout(() => { btn.classList.remove('is-error'); btn.textContent = 'Regenerate ↻'; }, 5000);
  }
}

async function pollJob(btn, jobId) {
  for (let i=0; i<150; i++) {     // 150 × 2s = 5 min cap
    await new Promise(r => setTimeout(r, 2000));
    const r = await fetch(`${TRIGGER_BASE}/status/${jobId}`, {cache:'no-store'});
    if (!r.ok) continue;
    const s = await r.json();
    if (s.state === 'success') {
      btn.classList.remove('is-running');
      btn.classList.add('is-success');
      btn.textContent = '✓ Updated';
      btn.title = '';
      setTimeout(() => { btn.classList.remove('is-success'); btn.textContent = 'Regenerate ↻'; }, 30000);
      return;
    }
    if (s.state === 'error') {
      btn.classList.remove('is-running');
      btn.classList.add('is-error');
      btn.textContent = '⚠ Failed';
      btn.title = (s.log_tail || []).slice(-5).join('\n');
      setTimeout(() => { btn.classList.remove('is-error'); btn.textContent = 'Regenerate ↻'; }, 5000);
      return;
    }
  }
  // Timed out
  btn.classList.remove('is-running');
  btn.classList.add('is-error');
  btn.textContent = '⚠ Timeout';
  setTimeout(() => { btn.classList.remove('is-error'); btn.textContent = 'Regenerate ↻'; }, 5000);
}

// Wire up buttons
document.querySelectorAll('.regen-btn').forEach(b => b.addEventListener('click', () => triggerBuild(b)));
// Initial + periodic health checks
pollHealth();
setInterval(pollHealth, 30000);
```

- [ ] **Step 2: End-to-end manual test**

1. Start the trigger server: `python C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server.py`
2. Open `C:\Users\quint\workspace-dashboard\portal.html` in browser
3. Wait 2s — health dot should turn green; "Regenerate" button enabled
4. Click "Regenerate" → button shows "Generating" with spinner
5. Wait ~30–60s → button shows "✓ Updated"
6. Open the GitHub Pages URL and confirm the report rebuilt with a fresh "Generated" timestamp

- [ ] **Step 3: Commit**

```powershell
cd C:\Users\quint\workspace-dashboard
git add portal.html
git commit -m "Wire portal regenerate button with health-check + status polling"
```

---

## Task 18: Auto-start trigger server via Windows Task Scheduler

**Files:**
- Create: `C:\Users\quint\workspace-dashboard\scripts\install_trigger_task.ps1`

- [ ] **Step 1: Write the install script**

Create `scripts/install_trigger_task.ps1`:

```powershell
# Registers the Olympic Paints Portal Trigger Server as a logon-time scheduled task.
# Run once as the user (no admin needed for user-scope task).

$TaskName  = "OlympicPortalTriggerServer"
$ScriptDir = "C:\Users\quint\workspace-dashboard\scripts"
$Python    = (Get-Command python).Source
$Script    = Join-Path $ScriptDir "portal_trigger_server.py"

# Action: run python on the trigger server, no console window
$Action = New-ScheduledTaskAction `
  -Execute $Python `
  -Argument "`"$Script`"" `
  -WorkingDirectory $ScriptDir

# Trigger: at user logon
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: restart on failure, don't run on battery suppression
$Settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -DontStopIfGoingOnBatteries `
  -AllowStartIfOnBatteries `
  -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Principal: run as current user, no elevation
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register (replaces any existing task of the same name)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Settings $Settings `
  -Principal $Principal `
  -Description "Local Flask trigger server for Olympic Paints workspace portal (regenerate-button backend)."

Write-Host "Registered task: $TaskName"
Write-Host "To start now without re-logging in, run:"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
```

- [ ] **Step 2: Run the install script**

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\quint\workspace-dashboard\scripts\install_trigger_task.ps1
```

Expected: prints "Registered task: OlympicPortalTriggerServer".

- [ ] **Step 3: Start the task immediately (don't wait for re-logon)**

```powershell
Start-ScheduledTask -TaskName OlympicPortalTriggerServer
```

- [ ] **Step 4: Verify the server is running**

```powershell
curl http://127.0.0.1:8765/health
```

Expected: `{"ok":true,"builds":["merchandising"]}`.

- [ ] **Step 5: Commit**

```powershell
cd C:\Users\quint\workspace-dashboard
git add scripts/install_trigger_task.ps1
git commit -m "Add scheduled-task installer for portal trigger server"
git push
```

---

## Task 19: End-to-end smoke test and memory update

- [ ] **Step 1: Full lap test**

1. Reboot or log out / log in to confirm the scheduled task auto-starts the trigger server
2. Open `portal.html` — health dot green within 2s
3. Click "Regenerate" on the Merchandising Impact tile
4. Wait for "✓ Updated"
5. Click "Open Report ↗" → live dashboard shows the just-generated content
6. Toggle each of the four themes (Light/Dark/Brand/Navy) → all render correctly
7. All three tabs (Overview/Kit Kat/Easy Build) populate

- [ ] **Step 2: Capture a memory of the new system**

Create `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\reference_merchandising_impact.md`:

```markdown
---
name: Merchandising Impact Report — repo, paths, and trigger flow
description: New on-demand dashboard quantifying the sales impact of formal merchandising at Kit Kat (5 accts) and Easy Build (7 accts). YoY same-month comparison, navy executive theme, regen via portal button.
type: reference
---
# Merchandising Impact Report

## Live URL
https://flomaticauto.github.io/olympic-paints-merchandising/

## Build script
`1.Projects/AWS Data/build_merchandising_impact.py`
Run manually: `python build_merchandising_impact.py`
Or via the portal "Regenerate" button (preferred).

## Account families
- **Kit Kat:** KK021, KK021/1, KK021/2, KK021/4, KK022 (sub-accounts consolidated Feb 2025)
- **Easy Build:** KE005, KE005/1, KE008, KE009, KE010, KE012, KE023 (KE005/1 consolidated Jan 2025)
- **Excluded:** KE035 (Easytile & Sanware — different customer)

## Trigger service
`C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server.py`
Auto-starts at user login via Task Scheduler (`OlympicPortalTriggerServer`).
Endpoints on `127.0.0.1:8765`: `/health`, `/trigger/<key>`, `/status/<job_id>`.
To restart: `Start-ScheduledTask -TaskName OlympicPortalTriggerServer`.

## Adding new on-demand reports
Append a new entry to the `BUILDS` dict in `portal_trigger_server.py`, then add a card+button in `portal.html` with `data-build="<key>"`.
```

Also append to `memory/MEMORY.md`:

```markdown
## Merchandising Impact Report

- [Merchandising Impact Report — repo, paths, trigger flow](reference_merchandising_impact.md) — On-demand dashboard, YoY comparison, navy theme, regen via portal button (Flask trigger on localhost:8765)
```

- [ ] **Step 3: Final commit**

If any uncommitted changes remain, commit them.

---

## Self-Review

**Spec coverage check:**

| Spec section | Plan task |
|---|---|
| Goal & scope (account families) | Task 2 (constants) + tests in Task 3 |
| Account family verification (sub-accounts) | Task 3 |
| Excluded KE035 | Task 3 (test asserts) |
| Merch era boundary (Oct/Nov 2025) | Task 5 |
| YoY same-month comparison | Task 6 |
| Per-store filter (active 6mo + R20K avg) | Task 7 |
| Hero KPI (3 numbers) | Task 8 + 11 (overview) + 12 (group tab) |
| Auto-prose templates | Task 9 |
| Theme system + design tokens | Task 10 |
| Overview tab | Task 11 |
| Group tab anatomy (3 sections) | Task 12 |
| Stacked panels chart | Task 12 |
| YoY bar chart (red/green) | Task 12 |
| Per-store table with status badge | Task 12 |
| Methodology footnote | Task 11 (helper) |
| Build orchestration + git push | Task 13 |
| Trigger server (Flask, /health, /trigger, /status) | Tasks 14, 15 |
| Build registry | Task 14 |
| Portal tile + button | Task 16 |
| Portal JS: health, trigger, polling | Task 17 |
| Windows Task Scheduler auto-start | Task 18 |
| End-to-end smoke test | Task 19 |
| Memory update | Task 19 |

All spec sections covered.

**Placeholder scan:** No `TBD` / `TODO` / "implement later" remain. All code blocks are complete.

**Type consistency:**
- `load_sales_for_group(account_list)` returns DataFrame — used consistently in Tasks 3, 7, 13
- `monthly_sales(df)` returns DataFrame with columns `[year, month, ivnett, period]` — used in Tasks 6, 8, 12, 13
- `merch_era_start(visits)` returns datetime — used in Tasks 5, 7, 8, 13
- `compute_yoy(monthly, era_start, today=None)` returns list of dicts with keys `post_period, prev_period, post_value, prev_value, pct` — referenced in Tasks 8, 9, 12
- `compute_group_kpis()` returns dict with `avg_yoy_pct, cumulative_extra_r, total_visits, r_per_visit, post_months, unique_stores, yoy_rows` — referenced in Tasks 11, 12, 13
- `per_store_breakdown()` returns list of dicts with `accno, store_name, pre_avg, post_avg, pct, status, consolidated_into, consolidated_date` — referenced in Tasks 12, 13
- `prose_*` functions return strings — referenced in Task 13
- Build registry key `"merchandising"` consistent across Tasks 14, 16, 17, 19

All consistent.
