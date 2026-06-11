# Runbook — Credit App Completions Dashboard

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** low — sales rep metric, not customer-facing

---

## Purpose

Per-rep metric: signed credit applications vs customers with credit limit > 0. Surfaces which reps are letting accounts trade on credit without paperwork.

---

## How it runs

- **Trigger:** Manual / weekly
- **Entry point:** `1.Projects/AWS Data/build_credit_apps_dashboard.py`
- **Invocation:** `python build_credit_apps_dashboard.py`

---

## Inputs

| Source | Notes |
|---|---|
| Zoho accounts | credit limit field |
| Signed apps register | source TBD — verify |

---

## Outputs

| Destination | URL |
|---|---|
| Dashboard | `https://flomaticauto.github.io/olympic-paints-credit-apps/` |
| Linked from | Sales Reports section |

---

## Known failure modes

1. **Symptom:** Rep attribution wrong.
   **Cause:** Grouping by `smno` or `accno` instead of via delivery number.
   **Fix:** Use `delno→dlref→smref` primary; `accno→curef` fallback FY2024 only. See [[feedback_sales_rep_attribution]].

2. **Symptom:** Push fails.
   **Cause:** Token / remote.
   **Fix:** See [[feedback_git_push_flomaticauto_safe]].

---

## Logs

- Console output; no persistent log.

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python build_credit_apps_dashboard.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_credit_apps_dashboard]]
