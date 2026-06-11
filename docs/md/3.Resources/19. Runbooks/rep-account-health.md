# Runbook — Rep Account Health Workbook Refresh

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — Quintus's working sales document; moving target

---

## Purpose

Per-rep workbook (AC/AP/BV/NP/BM) with Customer Number, velocity, health, YoY, visits, and Notes column. Treated as a **live document** — Quintus annotates Notes as he reviews accounts. Canonical baseline: `Output/Rep_Account_Health_2026-05-15_pre_notes.xlsx`.

---

## How it runs

- **Entry points:**
  - `1.Projects/AWS Data/build_rep_account_health.py`
  - `1.Projects/AWS Data/build_rep_account_health_v2.py` (newer)
- **Trigger:** Weekly / on Quintus's request

---

## Inputs

| Source | Notes |
|---|---|
| Sales parquet | velocity, YoY |
| Meetings parquet | visits per account |
| Account_Site join | per [[reference_zoho_account_site]] |
| Prior workbook | preserves Notes column when updating |

---

## Outputs

| Destination | Path |
|---|---|
| Workbook | `Output/Rep_Account_Health_<date>_*.xlsx` |
| Baseline | `Output/Rep_Account_Health_2026-05-15_pre_notes.xlsx` |

---

## Known failure modes

1. **Symptom:** Notes column wiped on refresh.
   **Cause:** Refresh script overwrote workbook without preserving annotations.
   **Fix:** Always merge Notes from prior workbook before writing new file. Workbook is a moving target.

2. **Symptom:** Rep attribution wrong on account.
   **Cause:** Joined by name not `Account_Site` → `accno`.
   **Fix:** Use `Account_Site` join. See [[reference_zoho_account_site]].

3. **Symptom:** YoY numbers off for FY2024 customers.
   **Cause:** FY2024 needs `accno→curef` fallback (no delno).
   **Fix:** See [[feedback_sales_rep_attribution]].

---

## Logs

- Console output.

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"

# Use v2 (preferred)
python build_rep_account_health_v2.py

# Legacy
python build_rep_account_health.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_rep_account_health]], [[reference_zoho_account_site]], [[feedback_sales_rep_attribution]]
- Sister: [[rep-dashboards]]
