# Runbook — CSO Insights HTML + Email Pages

> **Last verified:** 2026-06-02
> **Owner:** Quintus
> **Criticality:** medium — strategic comms artefact

---

## Purpose

Static analysis pages and accompanying email-ready HTML for each strategic insight. Every page has a paired `email_*.html`. Lives in its own repo and is published to GitHub Pages.

---

## How it runs

- **Trigger:** On-demand
- **Entry point:** `1.Projects/AWS Data/build_cso_insights.py`
- **Invocation:** `python build_cso_insights.py`
- **Email send:** `send_cso_email.py --page <name>`

---

## Inputs

| Source | Notes |
|---|---|
| INSIGHTS array | embedded in build script — JSON parse, filter, reinject (never regex-remove entries) |
| Zoho CSV exports | `skiprows=6`, date format `"%b %d, %Y %I:%M %p"` |

---

## Outputs

| Destination | URL |
|---|---|
| Static site | `https://flomaticauto.github.io/olympic-paints-cso-insights/` |
| Per-page email HTML | `email_<page>.html` |
| Repo | `github.com/FlomaticAuto/olympic-paints-cso-insights` |

---

## Known failure modes

1. **Symptom:** INSIGHTS array corrupted after edit.
   **Cause:** Regex used to remove an entry — regex stops at first `}` in nested objects.
   **Fix:** Always JSON parse → filter → reinject. See [[feedback_cso_insights_inject]].

2. **Symptom:** Page updated but email_*.html stale.
   **Cause:** `refresh_html()` not called for both.
   **Fix:** `refresh_html()` must update both. See [[feedback_cso_email_static_pages]].

3. **Symptom:** All date-filtered KPIs show 0.
   **Cause:** Wrong Zoho CSV date format or wrong `skiprows`.
   **Fix:** `skiprows=6` and `"%b %d, %Y %I:%M %p"`. See [[feedback_zoho_csv_format]].

4. **Symptom:** Charts blank in proxy view.
   **Cause:** CSS `url()` rewrite was case-insensitive and matched JS `URL.createObjectURL()`.
   **Fix:** Make rewrite case-sensitive. See [[feedback_proxy_url_case_sensitive]].

---

## Logs

- Console; no persistent log.

---

## Manual run

```powershell
cd "C:\Users\Administrator\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"

# Rebuild all pages
python build_cso_insights.py
```

> Note: `send_cso_email.py` referenced above has not been implemented yet.

---

## Recent incidents

- **2026-06-02:** Task was registered pointing to non-existent `build_cso_intelligence.py` at `C:\Users\Administrator\olympic-paints-cso-insights\` — fixed to correct path. Rep performance panel was sourcing stale data from deprecated `build_kpi_dashboard.py` — replaced with live parquet computation (30% YoY growth target baseline).

---

## Related

- Memory: [[reference_cso_insights]], [[feedback_cso_email_static_pages]], [[feedback_cso_insights_inject]], [[feedback_zoho_csv_format]]
