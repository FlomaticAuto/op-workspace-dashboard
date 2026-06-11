# Runbook — E-Commerce Dashboard Builder

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — reference dashboard for OneDayOnly / WooCommerce activity

---

## Purpose

Builds the full WooCommerce dashboard (orders, sales, products, provinces). Published to GitHub Pages. Consumed by the morning digest (operational-health subset only).

---

## How it runs

- **Trigger:** Manual or scheduled (verify with `Get-ScheduledTask`)
- **Entry point:** `1.Projects/AWS Data/build_ecommerce_dashboard.py`
- **Invocation:** `python build_ecommerce_dashboard.py`
- **Fetch step:** `fetch_woocommerce_transactions.py` (pulls fresh data via WC REST API)

---

## Inputs

| Source | Path / Notes |
|---|---|
| WooCommerce API | requires `WC_URL`, `WC_KEY`, `WC_SECRET` in `.env` |
| CSV fallback | uses existing CSV if creds missing |

---

## Outputs

| Destination | URL |
|---|---|
| Dashboard | `https://flomaticauto.github.io/olympic-paints-ecommerce` |

---

## Known failure modes

1. **Symptom:** Stale numbers despite fresh run.
   **Cause:** `fetch_woocommerce_transactions.py` failed silently and fell back to CSV.
   **Fix:** Run fetch script explicitly first, check it produced fresh CSV before build.

2. **Symptom:** Build error on FY-frame.
   **Cause:** Calendar-YTD vs FY date logic mismatch.
   **Fix:** Currently FY2026 calendar-YTD (Jan onward).

3. **Symptom:** Push to `olympic-paints-ecommerce` repo fails.
   **Cause:** Token / remote issue.
   **Fix:** See [[feedback_git_push_flomaticauto_safe]].

---

## Logs

- `C:\Users\quint\.claude\logs\ecommerce-dashboard\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"

# Fetch fresh data
python fetch_woocommerce_transactions.py

# Build + deploy
python build_ecommerce_dashboard.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_ecommerce_dashboard]], [[reference_ecommerce_woocommerce_fetch]]
- Downstream: [[ecommerce-email-digest]]
