# Runbook — Merchandising Plan Heatmap Rebuild

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — visible to reps and management

---

## Purpose

Builds the **REP × DATE daily activity heatmap** — the canonical visual for any "Merchandising Plan". Bands: 1 / 2 / 3 / 4+. Colour ramp: navy → yellow. Newest date column first (today is leftmost). Cell value = total day activity (visits + leads). Green overlay = lead share of that total.

---

## How it runs

- **Trigger:** Manual / weekly
- **Entry points:**
  - `2.Areas/3. Merchandising/build_merchandising_calendar.py` — Phase 1 merchandising calendar
  - `1.Projects/AWS Data/build_merchandising_impact.py` — impact report

---

## Inputs

| Source | Path |
|---|---|
| Meetings parquet | `zoho_meetings/data/meetings.parquet` (disjoint visits + leads, no double-count) |

---

## Outputs

| Destination | Notes |
|---|---|
| Static merchandising calendar | rep-facing |
| Impact report | management |

---

## Known failure modes

1. **Symptom:** Dot-grid cycle view instead of REP × DATE heatmap.
   **Cause:** Wrong renderer used.
   **Fix:** Canonical visual is the heatmap. See [[feedback_merchandising_plan_format]].

2. **Symptom:** Today appears rightmost / dates in chronological order.
   **Cause:** Date columns not reversed.
   **Fix:** Reverse so newest is leftmost. Same rule for Store Visits AND Merchandising Visits. See [[feedback_heatmap_newest_first]].

3. **Symptom:** Cell shows visits only, no green overlay.
   **Cause:** Lead share not calculated.
   **Fix:** Cell = visits + leads = total. Green bar fills `leads/total × 100`. Future dates gate on Week 4 only. See [[feedback_lead_visit_green_overlay]].

4. **Symptom:** Heatmap on Activity tab updates, Monthly tab stale.
   **Cause:** Dual-mount classes broken — both tabs need `.js-hm-grid` / `.js-hm-pills`, renderer uses `querySelectorAll`.
   **Fix:** Verify both mount points present. See [[feedback_rep_heatmap_dual_mount]].

---

## Logs

- Console output.

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\3. Merchandising"
python build_merchandising_calendar.py

cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python build_merchandising_impact.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[feedback_merchandising_plan_format]], [[feedback_heatmap_newest_first]], [[feedback_lead_visit_green_overlay]], [[feedback_rep_heatmap_dual_mount]]
