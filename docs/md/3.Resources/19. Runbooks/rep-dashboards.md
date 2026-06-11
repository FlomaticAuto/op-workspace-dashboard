# Runbook — Rep Dashboards Builder

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — five per-rep dashboards

---

## Purpose

Builds one dashboard per rep (AC/AP/BV/NP/BM). Tabs include Overview (with Monthly Diagnostic Panel), Monthly Revenue (calendar-year framed), Activity, and a daily meetings heatmap that mounts on both Activity AND Monthly tabs.

---

## How it runs

- **Trigger:** Weekly / on-demand
- **Entry point:** `1.Projects/AWS Data/build_rep_dashboards.py`
- **Invocation:** `python build_rep_dashboards.py --auto-compute`   ← **flag is mandatory**

---

## Inputs

| Source | Path |
|---|---|
| Sales parquet | per-rep revenue |
| Meetings parquet | activity heatmap |
| KPI scorecard data | for Monthly Diagnostic Panel (radio A/B/C/E/F; D excluded — rolling-12 lookback) |

---

## Outputs

| Destination | Notes |
|---|---|
| 5 dashboards | per-rep |

---

## Known failure modes

1. **Symptom:** Chart series stuck on old values despite new data.
   **Cause:** Ran without `--auto-compute` → chart series came from stale hardcoded `REPS` dict.
   **Fix:** Always pass `--auto-compute`. See [[feedback_rep_dashboards_auto_compute]].

2. **Symptom:** Monthly Revenue chart shows fiscal-year axis (Apr–Mar).
   **Cause:** Reverted from calendar-year framing.
   **Fix:** Must be Jan–Dec, series labels '2025' and '2026', uses `_cy_month_array`. See [[feedback_rep_dashboard_calendar_year]].

3. **Symptom:** Heatmap updates on Activity tab but Monthly tab stale.
   **Cause:** Dual-mount classes broken.
   **Fix:** Both tabs need `.js-hm-grid` and `.js-hm-pills`, renderer uses `querySelectorAll`. See [[feedback_rep_heatmap_dual_mount]].

4. **Symptom:** Rep revenue totals look 2× too high.
   **Cause:** CRNOTE rows summed unsigned.
   **Fix:** `net = ivnett × {INVOICE:1, CRNOTE:-1}`. See [[feedback_rep_ivnett_signed_by_ivtype]].

5. **Symptom:** Monthly Diagnostic Panel missing category D.
   **Cause:** Not a bug — D is excluded by design (rolling-12 lookback). A/B/C/E/F only.
   **Fix:** See [[reference_kpi_monthly_diagnostic_panel]].

---

## Logs

- Console output.

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python build_rep_dashboards.py --auto-compute
```

---

## Recent incidents

- **2026-05-21** — Monthly Diagnostic Panel added to Overview tab.

---

## Related

- Memory: [[feedback_rep_dashboards_auto_compute]], [[feedback_rep_dashboard_calendar_year]], [[feedback_rep_heatmap_dual_mount]], [[feedback_rep_ivnett_signed_by_ivtype]], [[reference_kpi_monthly_diagnostic_panel]]
- Sister: [[rep-account-health]]
