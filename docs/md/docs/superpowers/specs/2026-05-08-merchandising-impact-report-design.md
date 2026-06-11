# Merchandising Impact Report — Design

**Status:** Approved 2026-05-08
**Owner:** Quintus / PRISM
**Audience:** Olympic Paints management

## Goal

Prove (or disprove) that the formal merchandising program — running since
October/November 2025 at Kit Kat and Easy Build group stores — has produced
measurable sales growth.

The report is a one-shot management deliverable, regenerated on demand from
existing data sources. No manual data entry.

## Scope

### In scope

Two product-group families, both serviced exclusively by rep NP (Nikhil):

**Kit Kat family — 5 accounts, R27.8M lifetime revenue**

| accno | Store | Lifetime sales | Active range |
|---|---|---|---|
| `KK021` | Kit Kat Group (Pty) Ltd | R16,728,070 | 2024-03 → present |
| `KK021/1` | (sub-account, consolidated Feb 2025) | R2,188,443 | 2024-03 → 2025-02 |
| `KK021/2` | (sub-account, consolidated Feb 2025) | R2,211,882 | 2024-03 → 2025-02 |
| `KK021/4` | (sub-account, consolidated Feb 2025) | R2,157,412 | 2024-03 → 2025-02 |
| `KK022` | Kit Kat Group (Pty) Ltd | R4,536,304 | 2024-03 → present |

**Easy Build family — 7 accounts, R12.0M lifetime revenue**

| accno | Store | Lifetime sales | Active range |
|---|---|---|---|
| `KE005` | Easy Build Hardware | R4,752,317 | 2024-03 → present |
| `KE005/1` | (sub-account, consolidated Jan 2025) | R518,661 | 2024-03 → 2025-01 |
| `KE008` | Easy Build | R1,729,944 | 2024-03 → present |
| `KE009` | Easy Build | R1,369,551 | 2024-03 → present |
| `KE010` | Easy Build Soweto | R694,318 | 2024-03 → present |
| `KE012` | Easy Build Hardware | R879,213 | 2024-03 → present |
| `KE023` | Easy Build Hardware Jubilee | R1,523,522 | 2024-03 → present |

Sub-accounts (`KK021/1`, `/2`, `/4` and `KE005/1`) were consolidated into their
parents in Jan/Feb 2025. Their pre-merchandising revenue must be added to the
parent's pre-merchandising totals so YoY comparisons remain apples-to-apples.

### Out of scope

- `KE035` (Easytile & Sanware) — different customer despite KE prefix
- All other product groups
- Other reps' merchandising activity
- Training & rep-coaching attribution

## Analytical method

| Choice | Decision |
|---|---|
| Merchandising era boundary | First visit logged per group: **Oct 2025 (Kit Kat)**, **Nov 2025 (Easy Build)**. The formal log is the authority — informal pre-log effort is not credited. |
| Effort metric | **Visit count per month**, sourced from `Merchandising_Visits_Log.xlsx`. |
| Seasonality control | **Year-over-year same-month comparison.** Each post-merch month is benchmarked against the same calendar month one year earlier. Controls for the December spike. |
| Hero KPI | Three numbers shown together: <br>1. **% YoY growth** (avg over post-merch months) <br>2. **Cumulative incremental revenue** (R) <br>3. **Sales per visit** (R) |
| Per-store filter | Show stores that are **active in the last 6 months (relative to report generation date) AND have lifetime avg ≥ R20K/month** (lifetime avg = total revenue ÷ number of months between first and last invoice). Sub-accounts always shown for completeness with a "consolidated" note. |

## Architecture

### Build pipeline

**Script:** `1.Projects/AWS Data/build_merchandising_impact.py`

Mirrors the existing `build_kpi_dashboard.py` / `build_ecommerce_dashboard.py`
pattern. Reads, computes, renders, deploys — all in one process.

```
INPUTS
  ├─ 3.Resources/16.Sales and Other data/Sales_Invoices_All.parquet
  └─ 2.Areas/3. Merchandising/2. Merchandiser Visits/Merchandising_Visits_Log.xlsx

OUTPUTS
  ├─ 1.Projects/AWS Data/merchandising-impact/index.html
  ├─ 1.Projects/AWS Data/merchandising-impact/logo.jpg  (copied from brand assets)
  └─ git push → flomaticauto/olympic-paints-merchandising
        └─ live: https://flomaticauto.github.io/olympic-paints-merchandising/
```

**Auth for git push:** `gh auth token --user FlomaticAuto`, embedded in the
remote URL (per existing pattern in memory `reference_github_auth_pattern`).

**Cadence:** On-demand only. No cron, no scheduler. Triggered from the portal
page (see Trigger Service below).

### Trigger service

**Script:** `C:\Users\quint\workspace-dashboard\scripts\portal_trigger_server.py`

Generic Flask server, not Merchandising-specific — designed to host other
on-demand builds in future (returns/refunds, ad-hoc weekly health, etc.).

**Bind:** `127.0.0.1:8765` (loopback only — no external access).

**Endpoints**

| Method | Path | Behaviour |
|---|---|---|
| `GET` | `/health` | `{ok: true, builds: ["merchandising"]}` — used by portal to detect service is running |
| `POST` | `/trigger/<key>` | Spawns the build in a background thread, returns `{job_id}` |
| `GET` | `/status/<job_id>` | Returns `{state, started_at, finished_at, log_tail}` where state is `running\|success\|error` |

**Build registry**

```python
BUILDS = {
  "merchandising": {
    "label": "Merchandising Impact Report",
    "cmd": ["python",
            r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\build_merchandising_impact.py"],
  },
}
```

The build script is responsible for its own deployment (git push). The trigger
server only invokes the script and surfaces logs.

**Auto-start:** Windows Task Scheduler entry `OlympicPortalTriggerServer` —
runs at user login, restarts on failure. Manual start command available in the
portal's "Scripts" tab for cases where it has stopped.

### Portal integration

**File:** `C:\Users\quint\workspace-dashboard\portal.html`

Add a new tile under the **Sales** tab (and ensure it surfaces in **All Reports**) labelled "Merchandising Impact Report", with:

- "Open Report" link to the GitHub Pages URL
- "Regenerate" button that triggers the local build and shows live status
- Health-dot indicator: green if trigger service is up, grey if not

**Button states:**

| State | Display |
|---|---|
| Idle, service up | `[Regenerate ↻]` (yellow accent) |
| Idle, service down | `[Regenerate ↻]` greyed out, tooltip "Trigger service offline" |
| In progress | `[Generating… 🔄]` with spinner |
| Just succeeded | `[✓ Updated just now]` for 30s, then back to idle |
| Failed | `[⚠ Failed — see log]`, tooltip shows last 5 log lines |

**Polling:** Every 2 seconds while a job is `running`.

## Report content

**Theme:** Navy executive (per design system default for management reports).
Real `Olympic Paints Logo Digital.jpg` in `border-radius:50%` wrapper. Barlow
Condensed / Barlow fonts. All four theme toggles present at top.

**Charts:** Chart.js from CDN with the mandatory `barLabels` plugin per the
design system. Single-axis charts only.

### Tab 1 — Overview

Single screen, no scroll on a typical laptop:

1. **Hero KPI band** — combined headline:
   - Reporting window (Oct 2025 → present, N months)
   - Combined % YoY growth
   - Combined cumulative incremental revenue
   - Total visits, Avg R/visit
2. **Exec summary** — auto-prose paragraph (~3 sentences) summarising both
   groups
3. **Two side-by-side cards** — one per group, each with: % YoY, R extra,
   visit count, R/visit, sparkline trend, "View full report →" link to the
   group's tab
4. **Methodology footnote** — collapsible `<details>` block

### Tabs 2 & 3 — Kit Kat / Easy Build (shared anatomy)

Three numbered story sections:

**Section 1 — "What we did"**

- 4 stat chips: Total visits · Avg duration · Unique stores visited · Total
  merch items deployed (sum of `Floor Vinyls`, `Vertical Colour Chart`,
  `Horizontal Colour Chart`, `Shelf Wobblers`, `Big Colour Chart`,
  `Pricing Boards` columns from the visit log)
- Visits-by-month bar chart (post-merch window only)
- Auto-prose paragraph

**Section 2 — "What happened"**

- **Stacked panels chart** (the approved layout):
  - Top panel: monthly sales bars, full timeline (Mar 2024 → present), pre-merch
    in muted blue, post-merch in yellow, dashed vertical line at "program start"
  - Bottom panel: visit count bars, same x-axis, only post-merch months
    populated
  - Single x-axis below both panels
- YoY same-month bar chart underneath:
  - Each post-merch month vs same month one year earlier
  - Red bars = down YoY, green bars = up YoY
  - Value labels via `barLabels` plugin
- Auto-prose paragraph

**Section 3 — "Per-store breakdown"**

- Sortable table, one row per active account (per the filter rule):
  - Columns: accno · Store name · Pre-merch monthly avg · Post-merch monthly
    avg · % change · Visits in post-merch window · Status badge
  - Status badge: 🟢 strong (≥ +15%) · 🟡 mixed (-5% to +15%) · 🔴 declined (< -5%)
  - Consolidated sub-accounts shown with "consolidated [date] into [parent]"
    in the post-merch column
- Auto-prose paragraph

### Auto-prose templates

Deterministic Python f-strings. No LLM. Same approach as PRISM dashboards.

```python
# Section 1
WHAT_WE_DID = (
  "{visits_total} visits across {unique_stores} unique {group} stores between "
  "{first_visit:%b %Y} and {last_visit:%b %Y}, peaking in {peak_month:%b %Y} "
  "with {peak_count} visits. Average visit duration {avg_duration_min:.0f} minutes."
)

# Section 2
WHAT_HAPPENED = (
  "{positive_yoy} of {total_yoy_months} months posted positive YoY growth, "
  "averaging {avg_yoy:+.1%}. Strongest gain: {best_month:%b %Y} "
  "({best_yoy:+.0%} vs {best_month_prev:%b %Y}). "
  "{negative_clause}"
)

# Section 3
PER_STORE = (
  "{up_count} of {total_active} active accounts are up post-merch. "
  "Strongest mover: {best_store} at {best_store_pct:+.0%}. "
  "{declined_clause}"
)
```

## Methodology footnote (rendered in every tab)

Collapsible `<details>` block containing:

- Account list (parent accnos + sub-account note)
- Visit source: `Merchandising_Visits_Log.xlsx` — store-name regex match
  (visits do not carry account numbers)
- Sales source: `Sales_Invoices_All.parquet` — accno-based filter
- Comparison method: YoY same-month, post-merch months only
- Caveats:
  - Sub-accounts consolidated Jan/Feb 2025 — pre-merch totals include them
  - April 2026 visit data may be incomplete (known Zoho export gap, see memory
    note `reference_merchandising_kpi`)
  - Correlation, not causation. Other factors (macro conditions, pricing,
    seasonal effects beyond YoY, rep-effort changes) may contribute.

## Implementation checkpoints

1. **Repo creation** — `flomaticauto/olympic-paints-merchandising` on GitHub,
   Pages enabled on `main` branch root
2. **Build script** — `build_merchandising_impact.py`:
   - Data loading + sub-account-aware aggregation
   - Visit log matching (store-name regex)
   - YoY computation with seasonality control
   - Per-store filter
   - HTML rendering with Chart.js, navy theme, all four theme toggles
   - Auto-prose generation
   - Git auto-deploy
3. **Trigger server** — `portal_trigger_server.py`:
   - Flask app with the three endpoints
   - Background-thread job runner
   - Job state in memory dict (no persistence — restart loses history)
4. **Portal updates** — `portal.html`:
   - New tile under Sales tab
   - Health-check + button JS
5. **Task Scheduler entry** — auto-start the trigger server at login

## Out-of-scope (explicit non-goals)

- Statistical significance testing (n is small, would mislead more than inform)
- Forecasting / projecting future incremental revenue
- Per-rep attribution (this is a group-level study; all visits are NP's anyway)
- Live-refresh / auto-update on every sales data change
- Mobile-first layout (management reads this on a laptop)
