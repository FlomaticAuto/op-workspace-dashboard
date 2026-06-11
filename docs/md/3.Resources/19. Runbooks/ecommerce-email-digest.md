# Runbook — E-Commerce Email Digest

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — daily ops nudge; framed for operational health, not vanity metrics

---

## Purpose

Mon–Fri 08:00 digest covering overdue orders, dispatch guarantee status, and manufacturing readiness. Deliberately **excludes** total orders, total sales, and product/province tables — those go on the dashboard, not in the digest.

---

## How it runs

- **Trigger:** Task Scheduler `\Olympic Paints\FLASH\OlympicPaints_EmailECommerceDashboard`
- **Schedule:** Mon–Fri **08:00**
- **Entry point:** `1.Projects/AWS Data/email_ecommerce_dashboard.py`
- **Invocation:** `python email_ecommerce_dashboard.py`

---

## Inputs

| Source | Path |
|---|---|
| WooCommerce orders | pulled via WC REST API by `fetch_woocommerce_transactions.py`, falls back to existing CSV if `WC_*` creds missing |
| Dashboard data | reused from `build_ecommerce_dashboard.py` outputs |

---

## Outputs

| Destination | Notes |
|---|---|
| Email | operational-health framed: overdue / dispatch guarantee / manufacturing |
| FY-frame | FY2026 calendar-YTD |
| Telegram confirm | chat `8042233389` |

---

## Known failure modes

1. **Symptom:** Digest includes total orders + total sales tables.
   **Cause:** Regression — those are deliberately excluded.
   **Fix:** Strip back to operational-health framing only. See [[reference_ecommerce_email_digest]].

2. **Symptom:** WooCommerce data stale.
   **Cause:** `WC_*` creds missing → fallback to old CSV.
   **Fix:** Verify `.env` has `WC_URL`, `WC_KEY`, `WC_SECRET`. Set `NODE_OPTIONS=--use-system-ca` if TLS errors. See [[feedback_node_use_system_ca]].

3. **Symptom:** Job killed with -1073741510.
   **Cause:** OneDrive log path.
   **Fix:** Log to `C:\Users\quint\.claude\logs\ecommerce-digest\`. See [[feedback_schtasks_logs_outside_onedrive]].

4. **Symptom:** Python TLS fails on HTTPS to WC.
   **Cause:** Local AV does TLS inspection; certifi-only fails.
   **Fix:** `truststore.inject_into_ssl()` at top of script. See [[feedback_python_truststore_for_https]].

---

## Logs

- `C:\Users\quint\.claude\logs\ecommerce-digest\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python email_ecommerce_dashboard.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_ecommerce_email_digest]], [[reference_ecommerce_dashboard]], [[reference_ecommerce_woocommerce_fetch]]
- Upstream: [[ecommerce-dashboard]]
