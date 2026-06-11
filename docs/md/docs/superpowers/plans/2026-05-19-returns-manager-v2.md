# Returns Manager v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Olympic Paints Returns Manager from local Streamlit app to a form → Supabase → Python builder → static GitHub Pages dashboard pipeline, with supervisor HTML email notifications.

**Architecture:** Jagdish submits returns via a mobile Vercel form (already live); a local Python builder pulls all submissions from Supabase, writes an Excel workbook, generates a static HTML dashboard pushed to GitHub Pages, and emails supervisors via Outlook. No Streamlit, no file-watcher, no PDF scanning.

**Tech Stack:** Next.js/TypeScript (form), Python 3.x, `supabase-py`, `openpyxl`, `python-dotenv`, `truststore`, `win32com` (Outlook), `subprocess`/`gh` CLI (GitHub Pages push), Chart.js (dashboard charts).

---

## File Map

| File | Role |
|---|---|
| `C:\Users\quint\olympic-paints-forms-admin\src\components\ReturnIntakeForm.tsx` | Add `return_type` + `batch_no` fields |
| `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\supervisor_config.json` | Add Piyush + Jagdish entries |
| `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts\build_returns_dashboard.py` | Main builder — Supabase pull → Excel → HTML → email → GitHub push |
| `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\.env` | SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (create, do not commit) |
| `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Output\` | Git repo for GitHub Pages (index.html + logo.jpg) |

---

## Task 1: Update supervisor_config.json

**Files:**
- Modify: `1.Projects/Returns KPI System/supervisor_config.json`

- [ ] **Step 1: Open the file and confirm current contents**

  ```
  C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\supervisor_config.json
  ```

  Current content (3 keys: MASINGITA, MUKESH, RAVI — all pointing to `quintusl@olympicpaints.co.za`).

- [ ] **Step 2: Add Piyush and Jagdish**

  Replace the entire file with:
  ```json
  {
    "MASINGITA": {"email": "quintusl@olympicpaints.co.za", "display_name": "Masingita"},
    "MUKESH":    {"email": "quintusl@olympicpaints.co.za", "display_name": "Mukesh"},
    "RAVI":      {"email": "quintusl@olympicpaints.co.za", "display_name": "Ravi"},
    "PIYUSH":    {"email": "quintusl@olympicpaints.co.za", "display_name": "Piyush"},
    "JAGDISH":   {"email": "quintusl@olympicpaints.co.za", "display_name": "Jagdish"}
  }
  ```

- [ ] **Step 3: Verify JSON is valid**

  ```powershell
  python -c "import json; json.load(open(r'C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\supervisor_config.json')); print('OK')"
  ```
  Expected: `OK`

- [ ] **Step 4: Commit**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/Returns KPI System/supervisor_config.json"
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: add Piyush and Jagdish to supervisor_config"
  ```

---

## Task 2: Add return_type and batch_no to the form

**Files:**
- Modify: `C:\Users\quint\olympic-paints-forms-admin\src\components\ReturnIntakeForm.tsx`

- [ ] **Step 1: Add state variables**

  In `ReturnIntakeForm.tsx`, find the block of `useState` declarations (lines 26–35). Add two new ones immediately after `const [supervisor, setSupervisor] = useState('');`:

  ```tsx
  const [returnType, setReturnType] = useState('');
  const [batchNo,    setBatchNo]    = useState('');
  ```

- [ ] **Step 2: Add fields to the data payload**

  Find the `const data = { ... }` block inside `onSubmit` (around line 63). Add the two new fields:

  ```tsx
  const data = {
    report_ref:  reportRef,
    date,
    category,
    product,
    colour,
    size,
    qty,
    return_type: returnType,
    batch_no:    batchNo,
    supervisor,
    notes,
  };
  ```

- [ ] **Step 3: Add the UI — Return Type dropdown and Batch No input**

  Find the `<div className="ri-divider" />` that sits between the product/size/qty block and the supervisor block (around line 231). Insert the following JSX immediately **after** that divider and **before** the supervisor `<label>`:

  ```tsx
  {/* Return details */}
  <div className="ri-step-label">Return Details</div>
  <label className="ri-field">
    <span className="ri-label">Return Type *</span>
    <select
      value={returnType}
      onChange={(e) => setReturnType(e.target.value)}
      required
    >
      <option value="">— select return type —</option>
      <option value="Rework">Rework</option>
      <option value="Inventory">Inventory</option>
      <option value="Inv+Rework">Inv+Rework</option>
      <option value="Written Off">Written Off</option>
    </select>
  </label>

  <label className="ri-field">
    <span className="ri-label">Batch Number *</span>
    <input
      type="text"
      value={batchNo}
      onChange={(e) => setBatchNo(e.target.value)}
      placeholder="e.g. BT-2026-001"
      required
    />
  </label>

  <div className="ri-divider" />
  ```

- [ ] **Step 4: Build and test locally**

  ```powershell
  cd C:\Users\quint\olympic-paints-forms-admin
  npm run build
  ```
  Expected: build completes with no TypeScript errors.

- [ ] **Step 5: Run dev server and manually verify the form**

  ```powershell
  npm run dev
  ```
  Open `http://localhost:3000` → navigate to the Returns Intake form. Verify:
  - "Return Type" dropdown appears with 4 options after the product/size/qty section
  - "Batch Number" text input appears below it
  - Both are required (submitting without them shows browser validation)
  - Submission still succeeds (check Supabase → `form_submissions` for a test row with `return_type` and `batch_no` populated)

- [ ] **Step 6: Commit**

  ```powershell
  cd C:\Users\quint\olympic-paints-forms-admin
  git add src/components/ReturnIntakeForm.tsx
  git commit -m "feat: add return_type and batch_no fields to Returns Intake form"
  ```

- [ ] **Step 7: Deploy to Vercel**

  ```powershell
  git push origin main
  ```
  Vercel auto-deploys on push. Confirm deployment succeeds in the Vercel dashboard.

---

## Task 3: Create .env for the builder

**Files:**
- Create: `1.Projects/Returns KPI System/.env`

- [ ] **Step 1: Get the Supabase project URL and service role key**

  Log in to [supabase.com](https://supabase.com) → your project → Settings → API.
  Copy: **Project URL** and **service_role** key (not the anon key).

- [ ] **Step 2: Create the .env file**

  Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\.env` with:
  ```
  SUPABASE_URL=https://<your-project-ref>.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
  ```

- [ ] **Step 3: Verify .env is not tracked by git**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" check-ignore -v "1.Projects/Returns KPI System/.env"
  ```
  If nothing is printed, add it to `.gitignore`:
  ```powershell
  Add-Content "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\.gitignore" "`n1.Projects/Returns KPI System/.env"
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add .gitignore
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "chore: ignore Returns KPI System .env"
  ```

---

## Task 4: Create the GitHub Pages repo for the dashboard

- [ ] **Step 1: Create the repo under FlomaticAuto**

  ```powershell
  gh repo create FlomaticAuto/olympic-paints-returns --public --description "Olympic Paints Returns Dashboard (GitHub Pages)"
  ```

- [ ] **Step 2: Clone it and set up the gh-pages branch**

  ```powershell
  $token = gh auth token --user FlomaticAuto
  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("x-access-token:$token"))
  git clone --branch gh-pages https://github.com/FlomaticAuto/olympic-paints-returns.git "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Output"
  ```

  If clone fails because gh-pages doesn't exist yet:
  ```powershell
  mkdir "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Output"
  cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Output"
  git init
  git checkout -b gh-pages
  git remote add origin https://github.com/FlomaticAuto/olympic-paints-returns.git
  # Create a placeholder so we can push
  "placeholder" | Out-File index.html -Encoding utf8
  $token = gh auth token --user FlomaticAuto
  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("x-access-token:$token"))
  git add index.html
  git commit -m "init: gh-pages branch"
  git -c "http.extraheader=AUTHORIZATION: basic $b64" push -u origin gh-pages
  ```

- [ ] **Step 3: Enable GitHub Pages in repo settings**

  ```powershell
  gh api repos/FlomaticAuto/olympic-paints-returns/pages --method POST --field source='{"branch":"gh-pages","path":"/"}'
  ```
  Expected: JSON response with `"status": "queued"` or similar.

- [ ] **Step 4: Confirm Output directory is ready**

  ```powershell
  git -C "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Output" status
  ```
  Expected: `On branch gh-pages`, clean working tree.

---

## Task 5: Write build_returns_dashboard.py — Supabase pull + Excel

**Files:**
- Create: `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py`

- [ ] **Step 1: Install dependencies**

  ```powershell
  pip install supabase python-dotenv truststore openpyxl
  ```

- [ ] **Step 2: Write the script skeleton and Supabase pull function**

  Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts\build_returns_dashboard.py`:

  ```python
  """
  build_returns_dashboard.py — Olympic Paints Returns Manager v2
  Pulls form_submissions from Supabase → Excel workbook + static HTML dashboard + supervisor emails.

  Run: python build_returns_dashboard.py
  """
  import base64
  import json
  import shutil
  import subprocess
  import sys
  from collections import defaultdict
  from datetime import datetime, timezone
  from pathlib import Path

  import truststore
  truststore.inject_into_ssl()

  from dotenv import load_dotenv
  import os
  from supabase import create_client
  import openpyxl
  from openpyxl.styles import Font, PatternFill, Alignment
  from openpyxl.utils import get_column_letter

  # ── Paths ──────────────────────────────────────────────────────────────────────
  SCRIPT_DIR   = Path(__file__).parent
  PROJECT_DIR  = SCRIPT_DIR.parent
  OUTPUT_DIR   = PROJECT_DIR / "Output"
  DB_PATH      = PROJECT_DIR / "Returns_Database_v2.xlsx"
  CONFIG_PATH  = PROJECT_DIR / "supervisor_config.json"
  LOGO_SRC     = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\9. Brand Assets & Images\Misc Pictures\Olympic Paints Logo Digital.jpg")

  load_dotenv(PROJECT_DIR / ".env")

  SUPERVISOR_NORM = {
      "masangita": "MASINGITA",
      "masingita": "MASINGITA",
      "mukesh":    "MUKESH",
      "ravi":      "RAVI",
      "piyush":    "PIYUSH",
      "jagdish":   "JAGDISH",
  }

  def normalise_supervisor(name: str) -> str:
      return SUPERVISOR_NORM.get(name.strip().lower(), name.strip().upper())

  def pull_submissions() -> list[dict]:
      """Pull all returns_intake rows from Supabase, sorted by submitted_at."""
      url = os.environ["SUPABASE_URL"]
      key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
      client = create_client(url, key)
      res = (
          client.table("form_submissions")
          .select("data, submitted_at")
          .eq("metadata->>form_type", "returns_intake")
          .order("submitted_at")
          .execute()
      )
      rows = []
      for r in res.data:
          d = r["data"]
          d["_submitted_at"] = r["submitted_at"]
          rows.append(d)
      print(f"  Pulled {len(rows)} submissions from Supabase")
      return rows
  ```

- [ ] **Step 3: Smoke-test the pull**

  ```powershell
  cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts"
  python -c "
  import sys; sys.path.insert(0,'.')
  import truststore; truststore.inject_into_ssl()
  from build_returns_dashboard import pull_submissions
  rows = pull_submissions()
  print(rows[:2])
  "
  ```
  Expected: prints list of dicts (may be empty if no real submissions yet — that is fine, empty list is valid).

- [ ] **Step 4: Add the Excel writer function**

  Append to `build_returns_dashboard.py`:

  ```python
  HEADER_FILL = PatternFill("solid", fgColor="1F3864")
  HEADER_FONT = Font(color="FFFFFF", bold=True, size=10)

  def _write_sheet(ws, headers: list[str], rows: list[list]):
      for col, h in enumerate(headers, 1):
          cell = ws.cell(row=1, column=col, value=h)
          cell.fill = HEADER_FILL
          cell.font = HEADER_FONT
          cell.alignment = Alignment(horizontal="center", vertical="center")
          ws.column_dimensions[get_column_letter(col)].width = max(len(h) * 1.4, 12)
      ws.row_dimensions[1].height = 28
      ws.freeze_panes = "A2"
      for r_idx, row in enumerate(rows, 2):
          for c_idx, val in enumerate(row, 1):
              ws.cell(row=r_idx, column=c_idx, value=val)

  def write_excel(rows: list[dict]) -> dict:
      """Write Returns_Database_v2.xlsx. Returns summary dict."""
      wb = openpyxl.Workbook()
      wb.remove(wb.active)

      # ── Line_Items sheet ───────────────────────────────────────────────────────
      li_headers = [
          "record_id", "date", "category", "product_name", "shade_colour",
          "size", "batch_no", "qty", "return_type", "supervisor_assigned",
          "notes", "submitted_at",
      ]
      li_rows = []
      for row in rows:
          li_rows.append([
              row.get("report_ref", ""),
              row.get("date", ""),
              row.get("category", ""),
              row.get("product", ""),
              row.get("colour", ""),
              row.get("size", ""),
              row.get("batch_no", ""),
              int(row.get("qty") or 0),
              row.get("return_type", ""),
              normalise_supervisor(row.get("supervisor", "")),
              row.get("notes", ""),
              row.get("_submitted_at", ""),
          ])
      ws_li = wb.create_sheet("Line_Items")
      _write_sheet(ws_li, li_headers, li_rows)

      # ── Deliveries sheet (grouped by date) ────────────────────────────────────
      by_date = defaultdict(list)
      for row in rows:
          by_date[row.get("date", "unknown")].append(row)

      del_headers = ["delivery_id", "date", "total_units_logged", "line_item_count", "supervisors"]
      del_rows = []
      for date_key in sorted(by_date.keys()):
          items = by_date[date_key]
          total_units = sum(int(r.get("qty") or 0) for r in items)
          sups = ", ".join(sorted({normalise_supervisor(r.get("supervisor", "")) for r in items}))
          del_rows.append([date_key, date_key, total_units, len(items), sups])
      ws_del = wb.create_sheet("Deliveries")
      _write_sheet(ws_del, del_headers, del_rows)

      # ── Summary sheet ─────────────────────────────────────────────────────────
      total_units   = sum(int(r.get("qty") or 0) for r in rows)
      rework_units  = sum(int(r.get("qty") or 0) for r in rows if r.get("return_type") in ("Rework", "Inv+Rework"))
      wo_units      = sum(int(r.get("qty") or 0) for r in rows if r.get("return_type") == "Written Off")
      inv_units     = sum(int(r.get("qty") or 0) for r in rows if r.get("return_type") == "Inventory")
      generated_at  = datetime.now(timezone.utc).isoformat()

      sum_headers = ["total_units", "total_line_items", "total_deliveries",
                     "rework_units", "written_off_units", "inventory_units", "generated_at"]
      sum_rows    = [[total_units, len(rows), len(by_date), rework_units, wo_units, inv_units, generated_at]]
      ws_sum = wb.create_sheet("Summary")
      _write_sheet(ws_sum, sum_headers, sum_rows)

      wb.save(DB_PATH)
      print(f"  Excel written → {DB_PATH}")
      return {
          "total_units": total_units, "total_line_items": len(rows),
          "total_deliveries": len(by_date), "rework_units": rework_units,
          "written_off_units": wo_units, "inventory_units": inv_units,
          "generated_at": generated_at, "by_date": by_date, "li_rows": li_rows,
      }
  ```

- [ ] **Step 5: Test Excel output with empty data**

  ```powershell
  python -c "
  import sys; sys.path.insert(0,'.')
  import truststore; truststore.inject_into_ssl()
  from build_returns_dashboard import write_excel
  summary = write_excel([])
  print('Summary:', summary)
  "
  ```
  Expected: prints summary dict with all zeros; `Returns_Database_v2.xlsx` is created with 3 sheets.

- [ ] **Step 6: Verify xlsx manually**

  Open `Returns_Database_v2.xlsx` in Excel. Confirm:
  - 3 sheets: Line_Items, Deliveries, Summary
  - Row 1 is styled (dark navy header, white bold text)
  - Freeze at A2 on each sheet

- [ ] **Step 7: Commit**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/Returns KPI System/scripts/build_returns_dashboard.py"
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: returns builder — Supabase pull + Excel writer"
  ```

---

## Task 6: Add HTML dashboard generator to builder

**Files:**
- Modify: `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py`

- [ ] **Step 1: Import the CSS from generate_reports.py**

  At the top of `build_returns_dashboard.py`, add this import after the existing imports:

  ```python
  sys.path.insert(0, str(SCRIPT_DIR))
  from generate_reports import _OLY_CSS_TOKENS, _COMPONENT_CSS
  ```

- [ ] **Step 2: Add the HTML builder function**

  Append to `build_returns_dashboard.py`:

  ```python
  RETURN_TYPE_COLOURS = {
      "Rework":     "#F5C400",
      "Inventory":  "#2D8C7A",
      "Inv+Rework": "#2D6BA8",
      "Written Off":"#E86060",
  }

  def build_html(summary: dict, rows: list[dict]) -> str:
      """Return the complete index.html string."""
      by_rt: dict[str, int] = defaultdict(int)
      for r in rows:
          by_rt[r.get("return_type", "Unknown")] += int(r.get("qty") or 0)

      by_sup: dict[str, dict] = defaultdict(lambda: {"units": 0, "count": 0, "latest": ""})
      for r in rows:
          sup = normalise_supervisor(r.get("supervisor", ""))
          by_sup[sup]["units"] += int(r.get("qty") or 0)
          by_sup[sup]["count"] += 1
          d = r.get("date", "")
          if d > by_sup[sup]["latest"]:
              by_sup[sup]["latest"] = d

      by_prod: dict[str, int] = defaultdict(int)
      for r in rows:
          by_prod[r.get("product", "Unknown")] += int(r.get("qty") or 0)
      top_products = sorted(by_prod.items(), key=lambda x: x[1], reverse=True)[:10]

      recent_30 = rows[-30:][::-1]

      # Chart data
      rt_labels = json.dumps(list(by_rt.keys()))
      rt_values = json.dumps(list(by_rt.values()))
      rt_colors = json.dumps([RETURN_TYPE_COLOURS.get(k, "#5C6B7A") for k in by_rt.keys()])
      prod_labels = json.dumps([p[0] for p in top_products])
      prod_values = json.dumps([p[1] for p in top_products])

      # Supervisor table rows
      sup_rows_html = ""
      for sup, d in sorted(by_sup.items(), key=lambda x: x[1]["units"], reverse=True):
          sup_rows_html += f"""<tr>
            <td>{sup}</td>
            <td class="center">{d['units']}</td>
            <td class="center">{d['count']}</td>
            <td class="center">{d['latest'] or '—'}</td>
          </tr>"""

      # Recent activity rows
      recent_rows_html = ""
      for r in recent_30:
          rt = r.get("return_type", "")
          badge_cls = {
              "Rework": "badge-reworked", "Written Off": "badge-written",
              "Inventory": "badge-progress", "Inv+Rework": "badge-progress",
          }.get(rt, "badge-pending")
          recent_rows_html += f"""<tr>
            <td>{r.get('date','')}</td>
            <td>{r.get('product','')}</td>
            <td>{r.get('colour','')}</td>
            <td class="center">{r.get('size','')}</td>
            <td class="center">{r.get('qty','')}</td>
            <td><span class="badge {badge_cls}">{rt}</span></td>
            <td>{r.get('batch_no','')}</td>
            <td>{normalise_supervisor(r.get('supervisor',''))}</td>
          </tr>"""

      gen_date = datetime.now().strftime("%d %b %Y %H:%M")

      return f"""<!DOCTYPE html>
<html lang="en" class="theme-dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Returns Manager — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
{_OLY_CSS_TOKENS}
{_COMPONENT_CSS}
.kpi-grid{{grid-template-columns:repeat(5,1fr)}}
@media(max-width:800px){{.kpi-grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="theme-bar">
  <button onclick="olyTheme('theme-light',this)">Light</button>
  <button onclick="olyTheme('theme-dark',this)" class="active">Dark</button>
  <button onclick="olyTheme('theme-brand',this)">Brand</button>
  <button onclick="olyTheme('theme-navy',this)">Navy</button>
</div>

<div class="page-header">
  <div class="header-brand">
    <div style="width:44px;height:44px;border-radius:50%;overflow:hidden;flex-shrink:0">
      <img src="logo.jpg" alt="Olympic Paints" width="44" height="44" style="display:block;width:100%;height:100%;object-fit:cover">
    </div>
    <div>
      <div class="header-title">Returns Manager</div>
      <div class="header-subtitle">Olympic Paints — Factory Returns Tracking</div>
    </div>
  </div>
  <div class="header-meta">
    <div class="header-date">Live Dashboard</div>
    <div class="header-gen">Generated {gen_date}</div>
  </div>
</div>

<div style="padding:28px 32px">

  <!-- KPI Row -->
  <div class="kpi-grid" style="margin-bottom:32px">
    <div class="kpi-card"><div class="kpi-label">Total Units</div><div class="kpi-value">{summary['total_units']}</div></div>
    <div class="kpi-card"><div class="kpi-label">Line Items</div><div class="kpi-value neutral">{summary['total_line_items']}</div></div>
    <div class="kpi-card"><div class="kpi-label">Deliveries</div><div class="kpi-value neutral">{summary['total_deliveries']}</div></div>
    <div class="kpi-card"><div class="kpi-label">Rework Units</div><div class="kpi-value">{summary['rework_units']}</div></div>
    <div class="kpi-card"><div class="kpi-label">Written Off</div><div class="kpi-value danger">{summary['written_off_units']}</div></div>
  </div>

  <!-- Return Type Chart -->
  <div style="background:var(--color-surface-base);border:1px solid var(--color-border-default);border-radius:12px;padding:24px;margin-bottom:24px">
    <div class="section-heading">Return Type Breakdown</div>
    <canvas id="rtChart" height="120"></canvas>
  </div>

  <!-- By Supervisor -->
  <div style="background:var(--color-surface-base);border:1px solid var(--color-border-default);border-radius:12px;padding:24px;margin-bottom:24px">
    <div class="section-heading">By Supervisor</div>
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr>
          <th>Supervisor</th><th class="center">Units</th><th class="center">Line Items</th><th class="center">Latest Date</th>
        </tr></thead>
        <tbody>{sup_rows_html}</tbody>
      </table>
    </div>
  </div>

  <!-- Top 10 Products Chart -->
  <div style="background:var(--color-surface-base);border:1px solid var(--color-border-default);border-radius:12px;padding:24px;margin-bottom:24px">
    <div class="section-heading">Top 10 Products by Units</div>
    <canvas id="prodChart" height="200"></canvas>
  </div>

  <!-- Recent Activity -->
  <div style="background:var(--color-surface-base);border:1px solid var(--color-border-default);border-radius:12px;padding:24px;margin-bottom:24px">
    <div class="section-heading">Recent Activity (last 30)</div>
    <div class="table-wrap">
      <table class="data-table">
        <thead><tr>
          <th>Date</th><th>Product</th><th>Colour</th><th class="center">Size</th>
          <th class="center">Qty</th><th>Return Type</th><th>Batch No</th><th>Supervisor</th>
        </tr></thead>
        <tbody>{recent_rows_html}</tbody>
      </table>
    </div>
  </div>

</div>

<div class="page-footer">Olympic Paints Returns Dashboard — Generated {gen_date}</div>

<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){{
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}}

Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--color-text-secondary').trim() || '#949390';

new Chart(document.getElementById('rtChart'), {{
  type: 'bar',
  data: {{
    labels: {rt_labels},
    datasets: [{{ data: {rt_values}, backgroundColor: {rt_colors}, borderRadius: 4 }}]
  }},
  options: {{ indexAxis:'y', plugins:{{legend:{{display:false}}}}, scales:{{ x:{{beginAtZero:true}} }} }}
}});

new Chart(document.getElementById('prodChart'), {{
  type: 'bar',
  data: {{
    labels: {prod_labels},
    datasets: [{{ data: {prod_values}, backgroundColor: '#F5C400', borderRadius: 4 }}]
  }},
  options: {{ indexAxis:'y', plugins:{{legend:{{display:false}}}}, scales:{{ x:{{beginAtZero:true}} }} }}
}});
</script>
</body>
</html>"""

  def write_html(summary: dict, rows: list[dict]):
      OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
      html = build_html(summary, rows)
      (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
      shutil.copy2(LOGO_SRC, OUTPUT_DIR / "logo.jpg")
      print(f"  HTML written → {OUTPUT_DIR / 'index.html'}")
  ```

- [ ] **Step 3: Test HTML generation with empty data**

  ```powershell
  python -c "
  import sys; sys.path.insert(0,'.')
  import truststore; truststore.inject_into_ssl()
  from build_returns_dashboard import write_excel, write_html
  summary = write_excel([])
  write_html(summary, [])
  print('Done')
  "
  ```
  Expected: `Output/index.html` and `Output/logo.jpg` created. Open `Output/index.html` in a browser and confirm it renders correctly: header, 5 KPI cards (all 0), empty tables, theme toggle works.

- [ ] **Step 4: Commit**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/Returns KPI System/scripts/build_returns_dashboard.py"
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: returns builder — HTML dashboard generator"
  ```

---

## Task 7: Add supervisor email to builder

**Files:**
- Modify: `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py`

- [ ] **Step 1: Add the email function**

  Append to `build_returns_dashboard.py`:

  ```python
  def send_supervisor_emails(summary: dict, rows: list[dict]):
      """Send one HTML email per supervisor with items in the dataset."""
      config = json.loads(CONFIG_PATH.read_text())

      by_sup: dict[str, list[dict]] = defaultdict(list)
      for r in rows:
          sup_key = normalise_supervisor(r.get("supervisor", ""))
          by_sup[sup_key].append(r)

      try:
          import win32com.client
          outlook = win32com.client.Dispatch("Outlook.Application")
      except Exception as e:
          print(f"  [email] Outlook not available: {e}")
          return

      today_str = datetime.now().strftime("%d %b %Y")
      sent = 0

      for sup_key, items in by_sup.items():
          if sup_key not in config:
              print(f"  [email] WARNING: {sup_key} not in supervisor_config.json — skipping")
              continue

          sup_cfg    = config[sup_key]
          to_email   = sup_cfg["email"]
          disp_name  = sup_cfg["display_name"]
          total_u    = sum(int(r.get("qty") or 0) for r in items)
          subject    = f"Returns Report — {today_str} — {total_u} units logged"

          rows_html = ""
          for r in items:
              rt = r.get("return_type", "")
              rows_html += f"""<tr style="border-bottom:1px solid rgba(255,255,255,0.06)">
                <td style="padding:8px 12px">{r.get('date','')}</td>
                <td style="padding:8px 12px">{r.get('product','')}</td>
                <td style="padding:8px 12px">{r.get('colour','')}</td>
                <td style="padding:8px 12px;text-align:center">{r.get('size','')}</td>
                <td style="padding:8px 12px;text-align:center">{r.get('qty','')}</td>
                <td style="padding:8px 12px">{rt}</td>
                <td style="padding:8px 12px">{r.get('batch_no','')}</td>
              </tr>"""

          body = f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
</head>
<body style="background:#071022;color:#fff;font-family:'Barlow',sans-serif;margin:0;padding:24px">
<div style="max-width:700px;margin:0 auto">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #F5C400">
    <img src="https://flomaticauto.github.io/olympic-paints-clocking/logo.jpg" alt="Olympic Paints" width="44" height="44" style="border-radius:50%;display:block">
    <div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:22px;text-transform:uppercase;color:#F5C400">Returns Report</div>
      <div style="font-size:12px;color:#B8CCE8">{disp_name} — {today_str}</div>
    </div>
  </div>
  <div style="display:flex;gap:16px;margin-bottom:24px">
    <div style="flex:1;background:#0D2040;border-radius:8px;padding:16px;text-align:center">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#6B9ED0;margin-bottom:6px">Total Units</div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:36px;color:#F5C400">{total_u}</div>
    </div>
    <div style="flex:1;background:#0D2040;border-radius:8px;padding:16px;text-align:center">
      <div style="font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#6B9ED0;margin-bottom:6px">Line Items</div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-weight:900;font-size:36px;color:#fff">{len(items)}</div>
    </div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <thead><tr style="background:#1A3D6E">
      <th style="padding:10px 12px;text-align:left;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Date</th>
      <th style="padding:10px 12px;text-align:left;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Product</th>
      <th style="padding:10px 12px;text-align:left;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Colour</th>
      <th style="padding:10px 12px;text-align:center;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Size</th>
      <th style="padding:10px 12px;text-align:center;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Qty</th>
      <th style="padding:10px 12px;text-align:left;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Type</th>
      <th style="padding:10px 12px;text-align:left;font-family:'Barlow Condensed',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#F5C400">Batch</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div style="margin-top:24px;font-size:11px;color:#6B9ED0;text-align:center;padding-top:16px;border-top:1px solid rgba(107,158,208,0.20)">
    Olympic Paints Returns System — {today_str}
  </div>
</div>
</body></html>"""

          mail = outlook.CreateItem(0)
          mail.To       = to_email
          mail.Subject  = subject
          mail.HTMLBody = body
          mail.Send()
          sent += 1

      # Force-flush Outbox
      try:
          ns = outlook.GetNamespace("MAPI")
          outbox = ns.GetDefaultFolder(4)  # 4 = olFolderOutbox
          for item in list(outbox.Items):
              try:
                  item.Send()
              except Exception:
                  pass
      except Exception:
          pass

      print(f"  Emails sent: {sent}")
  ```

- [ ] **Step 2: Test email (dry run — prints warning for any missing config keys)**

  ```powershell
  python -c "
  import sys; sys.path.insert(0,'.')
  import truststore; truststore.inject_into_ssl()
  from build_returns_dashboard import send_supervisor_emails
  # Fake one row so we have something to email
  fake_rows = [{'date':'2026-05-19','product':'High Gloss Enamel','colour':'White','size':'5L','qty':'3','return_type':'Rework','batch_no':'BT-001','supervisor':'Mukesh','report_ref':'RET-001','notes':''}]
  send_supervisor_emails({'total_units':3}, fake_rows)
  "
  ```
  Expected: prints `Emails sent: 1` and an email arrives at `quintusl@olympicpaints.co.za`.

---

## Task 8: Add GitHub Pages push + main() to builder

**Files:**
- Modify: `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py`

- [ ] **Step 1: Add the push function and main entrypoint**

  Append to `build_returns_dashboard.py`:

  ```python
  def push_to_github():
      """Push Output/ to FlomaticAuto/olympic-paints-returns gh-pages."""
      try:
          token = subprocess.check_output(
              ["gh", "auth", "token", "--user", "FlomaticAuto"],
              stderr=subprocess.DEVNULL,
          ).decode().strip()
      except subprocess.CalledProcessError:
          print("  [push] gh auth token failed — skipping GitHub push")
          return

      b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
      auth_header = f"AUTHORIZATION: basic {b64}"

      subprocess.run(["git", "-C", str(OUTPUT_DIR), "add", "-A"], check=True)

      diff = subprocess.run(
          ["git", "-C", str(OUTPUT_DIR), "diff", "--cached", "--quiet"],
          capture_output=True,
      )
      if diff.returncode == 0:
          print("  [push] No changes to push")
          return

      subprocess.run(
          ["git", "-C", str(OUTPUT_DIR), "commit", "-m",
           f"build: returns dashboard {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
          check=True,
      )
      subprocess.run(
          ["git", "-C", str(OUTPUT_DIR),
           "-c", f"http.extraheader={auth_header}",
           "push", "origin", "gh-pages"],
          check=True,
      )
      print("  [push] Pushed to GitHub Pages")


  def main():
      print("Returns Dashboard Builder — starting")
      rows    = pull_submissions()
      summary = write_excel(rows)
      write_html(summary, rows)
      push_to_github()
      send_supervisor_emails(summary, rows)
      print(f"\nDone. {summary['total_line_items']} line items, {summary['total_units']} total units.")


  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Run the full builder end-to-end**

  ```powershell
  cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts"
  python build_returns_dashboard.py
  ```

  Expected output:
  ```
  Returns Dashboard Builder — starting
    Pulled N submissions from Supabase
    Excel written → ...Returns_Database_v2.xlsx
    HTML written → ...Output\index.html
    [push] Pushed to GitHub Pages   (or "No changes to push" if already pushed)
    Emails sent: N
  
  Done. N line items, N total units.
  ```

- [ ] **Step 3: Verify GitHub Pages is live**

  Open `https://flomaticauto.github.io/olympic-paints-returns/` in a browser.
  Confirm dashboard renders with correct data.

- [ ] **Step 4: Commit**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/Returns KPI System/scripts/build_returns_dashboard.py"
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: returns builder — GitHub Pages push + main entrypoint"
  ```

---

## Task 9: Register Windows Task Scheduler job (optional)

- [ ] **Step 1: Create the log directory**

  ```powershell
  New-Item -ItemType Directory -Force "C:\Users\quint\.claude\logs\returns"
  ```

- [ ] **Step 2: Register the scheduled task**

  ```powershell
  $action  = New-ScheduledTaskAction `
      -Execute "python" `
      -Argument '"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts\build_returns_dashboard.py" >> "C:\Users\quint\.claude\logs\returns\build_returns_dashboard.log" 2>&1' `
      -WorkingDirectory "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\scripts"

  $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 07:00

  Register-ScheduledTask `
      -TaskName "OlympicPaints_BuildReturnsDashboard" `
      -TaskPath "\Olympic Paints\Returns\" `
      -Action $action `
      -Trigger $trigger `
      -RunLevel Highest `
      -Description "Builds Returns Dashboard from Supabase submissions daily at 07:00"
  ```

- [ ] **Step 3: Test-run the task**

  ```powershell
  Start-ScheduledTask -TaskName "\Olympic Paints\Returns\OlympicPaints_BuildReturnsDashboard"
  Start-Sleep -Seconds 10
  Get-Content "C:\Users\quint\.claude\logs\returns\build_returns_dashboard.log" -Tail 20
  ```
  Expected: log shows the builder ran successfully.

---

## Task 10: Retire old Streamlit components

- [ ] **Step 1: Verify new system is working**

  Confirm `https://flomaticauto.github.io/olympic-paints-returns/` is live with real data, and at least one email round-trip has been confirmed.

- [ ] **Step 2: Delete the .bat launcher files**

  ```powershell
  Remove-Item "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Start Returns Dashboard.bat" -ErrorAction SilentlyContinue
  Remove-Item "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Returns KPI System\Start Returns Watcher.bat" -ErrorAction SilentlyContinue
  ```

- [ ] **Step 3: Commit retirement**

  ```powershell
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add -u
  git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "chore: retire Streamlit launcher .bat files (Returns Manager v2 is live)"
  ```

---

## Self-Review

**Spec coverage check:**

| Spec section | Task(s) |
|---|---|
| §3 Form changes (return_type + batch_no) | Task 2 |
| §4 Supabase schema (no change, query pattern) | Task 5, Step 2 |
| §5.1 Builder orchestration | Task 8 (main) |
| §5.2 Delivery synthesis (group by date) | Task 5, Step 4 |
| §5.3 Excel output (3 sheets) | Task 5 |
| §6 Static dashboard HTML | Task 6 |
| §7 Supervisor email | Task 7 |
| §8 GitHub Pages push | Task 8 |
| §9 Task Scheduler | Task 9 |
| §10 Retirement | Task 10 |
| §11 Supervisor normalisation | Task 5 (normalise_supervisor defined) |
| §13 supervisor_config Piyush + Jagdish | Task 1 |

All spec sections covered. No placeholders. Types and function names are consistent across all tasks (`pull_submissions`, `write_excel`, `write_html`, `push_to_github`, `send_supervisor_emails`, `main`, `normalise_supervisor`).
