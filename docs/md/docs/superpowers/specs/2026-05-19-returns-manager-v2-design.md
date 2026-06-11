# Returns Manager v2 — Design Spec
**Date:** 2026-05-19  
**Author:** Quintus Lategan / Claude Code  
**Status:** Draft — awaiting user approval

---

## 1. Context & Motivation

The current Returns Manager is a local Streamlit app (`returns_app.py`) that can only be accessed from Quintus's PC. Jagdish (the sole data-entry operator) is on the factory floor with a phone/tablet and cannot reach a local app, so he is currently handing paper forms to someone else to key in — adding lag and errors.

The migration replaces the Streamlit app with three components:
- **Form (existing, already live):** Mobile-first Vercel form for Jagdish to log returns on the spot.
- **Builder (new):** Local Python script that pulls Supabase submissions and produces an Excel workbook + static HTML dashboard + HTML supervisor email.
- **Dashboard (new):** Static HTML page hosted on GitHub Pages for Quintus to monitor.

Supervisors are view-only — they receive an HTML email and have no dashboard login.

---

## 2. Architecture

```
Jagdish (phone/tablet)
    │
    ▼
ReturnIntakeForm (Vercel — olympic-paints-forms-admin)
    │  POST /api/submit/[form_id]
    ▼
Supabase — form_submissions table
    │  data JSONB + metadata JSONB
    │
    ├──► Telegram notification → 8042233389  (fires on each submission)
    │
    ▼
build_returns_dashboard.py  (Quintus's PC — on demand or Task Scheduler)
    │
    ├──► Returns_Database_v2.xlsx         (Excel workbook with 4 sheets)
    ├──► Output/index.html                (static dashboard → GitHub Pages)
    └──► HTML email → supervisor_config   (Outlook win32com, force-flush)
    
GitHub Pages — FlomaticAuto/olympic-paints-returns
    index.html  (built and pushed by builder)
```

**Key constraint:** The builder runs locally (same pattern as `build_kpi_dashboard.py`). It is the only component that touches Supabase — the dashboard is a static HTML file with no live Supabase queries.

---

## 3. Form Changes (olympic-paints-forms-admin)

Two fields are added to `ReturnIntakeForm.tsx`. Both are added in a new section between the product block and the supervisor block.

### 3.1 Return Type (required, dropdown)
- Field name in submitted data: `return_type`
- Options: `Rework`, `Inventory`, `Inv+Rework`, `Written Off`
- UI: `<select>` with the same styling as existing selects, shown immediately (not conditionally)
- Validation: required

### 3.2 Batch Number (required, text input)
- Field name in submitted data: `batch_no`
- UI: `<input type="text">` placeholder `"e.g. BT-2026-001"`, same styling as existing inputs
- Validation: required
- Note: Free text — Jagdish reads the batch number from the can/label

### 3.3 Updated `data` payload (after change)
```json
{
  "report_ref":  "RET-260519-4321",
  "date":        "2026-05-19",
  "category":    "Enamel — Mid Range",
  "product":     "High Gloss Enamel",
  "colour":      "White",
  "size":        "5L",
  "qty":         "3",
  "return_type": "Rework",
  "batch_no":    "BT-2026-041",
  "supervisor":  "Mukesh",
  "notes":       ""
}
```

### 3.4 Telegram notification update
The `/api/returns-notify` route currently sends the `data` object. After adding the two new fields they are automatically included — no change needed to the notification route.

---

## 4. Supabase Schema

No schema changes required. All form submissions land in the existing `form_submissions` table:

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | PK |
| `form_id` | text | Identifies which form |
| `data` | jsonb | Full field payload (see 3.3) |
| `metadata` | jsonb | `{"form_type": "returns_intake", "report_ref": "..."}` |
| `submitted_at` | timestamptz | UTC insert time |

The builder queries with:
```sql
SELECT data, submitted_at
FROM form_submissions
WHERE metadata->>'form_type' = 'returns_intake'
ORDER BY submitted_at ASC;
```

---

## 5. Builder Script — build_returns_dashboard.py

**Location:** `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py`  
**Run:** `python build_returns_dashboard.py` (no flags needed)

### 5.1 What it does (in order)
1. Load `.env` from the script's parent directory for `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
2. Pull all `returns_intake` rows from Supabase (unbounded — all history)
3. Normalise supervisor names: lowercase → strip → title-case; map `Masangita → MASINGITA` for config lookup
4. Group rows by `data->>'date'` (local date string, NOT `submitted_at` UTC) to form delivery records
5. Write `Returns_Database_v2.xlsx` with 3 sheets: `Line_Items`, `Deliveries`, `Summary`
6. Build `Output/index.html` static dashboard (see §6)
7. Copy logo.jpg to `Output/`
8. Push `Output/` to `FlomaticAuto/olympic-paints-returns` GitHub Pages (ephemeral http header pattern — see §8)
9. Send HTML summary email to supervisors who have items in the current run (Outlook win32com, force-flush)
10. Print completion summary to stdout

### 5.2 Delivery synthesis
Since the form has one row per return item (not per truck), the builder groups by `data->>'date'` to create a synthetic delivery record per day. Fields not on the form (`truck_no`, `driver_name`, `time_arrived`) are left blank in the Excel — these can be filled in manually if needed.

### 5.3 Excel output — Returns_Database_v2.xlsx
**Sheet: Line_Items** (one row per form submission, sorted by date)

| Column | Source |
|---|---|
| `record_id` | `data->>'report_ref'` |
| `date` | `data->>'date'` |
| `category` | `data->>'category'` |
| `product_name` | `data->>'product'` |
| `shade_colour` | `data->>'colour'` |
| `size` | `data->>'size'` |
| `batch_no` | `data->>'batch_no'` |
| `qty` | `data->>'qty'` (cast int) |
| `return_type` | `data->>'return_type'` |
| `supervisor_assigned` | `data->>'supervisor'` (normalised) |
| `notes` | `data->>'notes'` |
| `submitted_at` | `submitted_at` (UTC ISO string) |

**Sheet: Deliveries** (one row per unique date)

| Column | Notes |
|---|---|
| `delivery_id` | `YYYY-MM-DD` |
| `date` | Same |
| `total_units_logged` | Sum of `qty` for that date |
| `line_item_count` | Count of rows for that date |
| `supervisors` | Comma-separated unique supervisor names for that date |

**Sheet: Summary** (one row — overall KPIs)

| Column | Notes |
|---|---|
| `total_units` | Sum of all qty |
| `total_line_items` | Count of all rows |
| `total_deliveries` | Count of unique dates |
| `rework_units` | Sum qty where return_type = Rework or Inv+Rework |
| `written_off_units` | Sum qty where return_type = Written Off |
| `inventory_units` | Sum qty where return_type = Inventory |
| `generated_at` | UTC ISO timestamp |

**Output path:** `1.Projects/Returns KPI System/Returns_Database_v2.xlsx`  
The existing `Returns_Database.xlsx` (historical Streamlit data, 19 line items) is NOT touched.

---

## 6. Static Dashboard — Output/index.html

Follows Olympic Paints HTML design standards (Barlow fonts, four-theme toggle, CSS token system, logo.jpg via `<img>` tag in circular wrapper, no frameworks).

**Sections:**
1. **Header** — logo, "Returns Manager" title, generated date, theme toggle
2. **KPI row** — Total Units · Total Line Items · Total Deliveries · Rework Units · Written Off Units
3. **Return Type breakdown** — horizontal bar chart (Chart.js): Rework / Inventory / Inv+Rework / Written Off units
4. **By Supervisor** — table: supervisor name, unit count, line item count, most recent date
5. **By Product** — top 10 products by unit count, horizontal bar chart
6. **Recent Activity** — last 30 line items as a table (date, product, colour, size, qty, return_type, batch_no, supervisor)
7. **Footer** — "Olympic Paints Returns Dashboard — Generated [date]"

All data is embedded as a `const DATA = {...}` JSON block at page build time — no live API calls from the HTML.

---

## 7. Supervisor Email

Sent after every successful builder run. One email per unique supervisor who appears in the current dataset.

**To:** looked up from `supervisor_config.json` (currently all → `quintusl@olympicpaints.co.za`)  
**Subject:** `Returns Report — [date] — [N] units logged`  
**Body:** HTML email (Navy theme), containing:
- Header: logo + "Returns Report" + date
- KPI summary: total units, by return type breakdown
- Table of line items attributed to that supervisor
- Footer

**Transport:** Outlook win32com + force-flush (same pattern as other report emails).  
**Not Word .docx.** Output is HTML-only.

---

## 8. GitHub Pages Deployment

**Repo:** `FlomaticAuto/olympic-paints-returns`  
**Branch:** `gh-pages`  
**Live URL:** `https://flomaticauto.github.io/olympic-paints-returns/`

The builder pushes `Output/index.html` + `Output/logo.jpg` using the ephemeral http header pattern:
```python
token = subprocess.check_output(["gh", "auth", "token", "--user", "FlomaticAuto"]).decode().strip()
b64 = base64.b64encode(f"x-access-token:{token}".encode()).decode()
subprocess.run([
    "git", "-C", str(OUTPUT_DIR),
    "-c", f"http.extraheader=AUTHORIZATION: basic {b64}",
    "push", "origin", "gh-pages"
], check=True)
```

The `Output/` directory is an independent git repo (same pattern as the clocking and KPI dashboard repos).

---

## 9. Windows Task Scheduler (optional)

The builder can be run manually (on demand) OR registered as a Task Scheduler job.

**If scheduled:**
- Task name: `\Olympic Paints\Returns\OlympicPaints_BuildReturnsDashboard`
- Trigger: Daily, weekdays, 07:00
- Log path: `C:\Users\quint\.claude\logs\returns\build_returns_dashboard.log`  
  (NOT in OneDrive — avoids STATUS_CONTROL_C_EXIT kills)

---

## 10. Retirement Plan

Once the builder is live and validated:
- `Start Returns Dashboard.bat` → deleted
- `Start Returns Watcher.bat` → deleted  
- `returns_watcher.py` → retired (no more PDF scans)
- `ingest_returns_scan.py` → retired
- The existing `Returns_Database.xlsx` is kept as a historical archive — never overwritten

---

## 11. Supervisor Name Normalisation

The form uses `Masangita` (form spelling). `supervisor_config.json` uses `MASINGITA`. The builder normalises at pull time:

```python
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
```

If a supervisor name is not in `supervisor_config.json`, the email for that supervisor is skipped with a warning printed to stdout.

---

## 12. Out of Scope

- No batch lifecycle tracking (Pending → Completed) in v2 — the Streamlit Batch Tracker page is not replicated. This was Streamlit-only logic that required interactive input; the new system is reporting-only.
- No Jagdish daily KPI compliance log (Daily_KPI sheet) — retired with the Streamlit app.
- No interactive corrections library — the form data is treated as authoritative.
- No login/auth — the dashboard is public GitHub Pages (read-only, no sensitive data beyond volume figures).

---

## 13. File Manifest

| File | Action |
|---|---|
| `olympic-paints-forms-admin/src/components/ReturnIntakeForm.tsx` | ADD `return_type` dropdown + `batch_no` input |
| `olympic-paints-forms-admin/src/lib/returnProductData.ts` | No change |
| `1.Projects/Returns KPI System/scripts/build_returns_dashboard.py` | CREATE |
| `1.Projects/Returns KPI System/Returns_Database_v2.xlsx` | CREATED by builder |
| `1.Projects/Returns KPI System/Output/index.html` | CREATED by builder |
| `1.Projects/Returns KPI System/Output/logo.jpg` | COPIED by builder |
| `FlomaticAuto/olympic-paints-returns` (GitHub repo) | CREATE |
| `supervisor_config.json` | ADD Piyush + Jagdish entries |

---

## 14. Success Criteria

1. Jagdish can submit a return from his phone in under 60 seconds.
2. Builder pulls all submissions and produces Excel + HTML with no manual data entry.
3. `Returns_Database_v2.xlsx` has correct `return_type` and `batch_no` on every row.
4. Static dashboard is live at `https://flomaticauto.github.io/olympic-paints-returns/`.
5. Supervisor email arrives in Outlook with correct unit counts.
6. Historical `Returns_Database.xlsx` is untouched.
