# ~~Runbook — KPI Sales Dashboard (Weekly)~~

> ⚠️ **DEPRECATED — 2026-05-25.** This workflow has been discontinued. The dashboard is no longer published or maintained. This runbook is retained for historical reference only.

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** ~~high~~ **DEPRECATED**

---

## Purpose

The single weekly snapshot of sales performance vs target, by rep and product group. QuickSight renders the underlying charts as images so text extraction is impossible — the data block at the top of `build_kpi_dashboard.py` is **manually maintained from the PDFs** each week.

---

## How it runs

- **Trigger:** Manual — Quintus runs after the new `Weekly_Sales_Report__*.pdf` lands.
- **Entry point:** `1.Projects/AWS Data/build_kpi_dashboard.py`
- **Invocation:** `python build_kpi_dashboard.py`

Output is written to `index.html` and pushed to the KPI GitHub Pages repo. `kpi_status.json` is also written to `C:\Users\quint\workspace-dashboard\` for the workspace dashboard tile.

---

## Inputs

| Source | Path | Format |
|---|---|---|
| Weekly PDF | `1.Projects/KPI Report/Weekly Progress/Weekly_Sales_Report__*.pdf` | PDF (manually read) |
| Hardcoded data block | top of `build_kpi_dashboard.py` | Python literals |

**Ignore:** `Daily_Sales_Report_P_*.pdf` — that's a debtor aging view, not a KPI source.

---

## Outputs

| Destination | URL |
|---|---|
| KPI dashboard | `https://flomaticauto.github.io/olympic-paints-kpi/` |
| Workspace dashboard tile | `C:\Users\quint\workspace-dashboard\kpi_status.json` |

---

## Known failure modes

1. **Symptom:** Rep targets all show 0 or last week's numbers.
   **Cause:** Forgot to update the `REPS` list or `MTD_*` constants before running.
   **Fix:** Open `build_kpi_dashboard.py`, scroll to data block, update from PDF, re-run.

2. **Symptom:** `git push` to `olympic-paints-kpi` rejected.
   **Cause:** Token rotation or wrong remote.
   **Fix:** Use `gh auth token --user FlomaticAuto` and the ephemeral header pattern. See [[feedback_git_push_flomaticauto_safe]].

3. **Symptom:** YoY chart shows a flat current month.
   **Cause:** Updated `MTD_SALES` but forgot to overwrite the matching month in `YOY` list.
   **Fix:** Update YoY current-month entry alongside MTD figures.

4. **Symptom:** Dashboard pushed but workspace tile still stale.
   **Cause:** `kpi_status.json` write path no longer exists (e.g., workspace-dashboard moved).
   **Fix:** Verify path `C:\Users\quint\workspace-dashboard\` still exists, recreate if missing.

---

## Logs

- Script prints to stdout; no persistent log.
- Git push output confirms deploy.

---

## Manual run

```powershell
# 1. Drop new PDF into 1.Projects/KPI Report/Weekly Progress/
# 2. Open the PDF, read the numbers
# 3. Edit the data block at top of build_kpi_dashboard.py:
#    REPORT_WEEK, REPORT_DATE
#    MTD_SALES, MTD_TARGET, MTD_PCT_TARGET
#    DEBTORS_TOTAL, DEBTORS_90D, OVERDUE_60D_PCT
#    ABOVE_RB_AVG
#    REPS list (AC/AP/BV/NP/BM)
#    YOY list (current month actual)
#    RB_BY_PRODUCT list

cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python build_kpi_dashboard.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Live: `https://flomaticauto.github.io/olympic-paints-kpi/`
- Memory: [[reference_dashboards_inventory]]
- Rep codes: AC=Aboo, AP=Amit, BV=Bhadresh, NP=Nikhil, BM=Byron
