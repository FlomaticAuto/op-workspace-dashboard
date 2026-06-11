# Runbook — Friday Sales Meeting Refresh

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** high — runs immediately before the weekly sales meeting; failure = meeting starts without data

---

## Purpose

Refreshes the data inputs (leads, meetings, sales) and rebuilds the artefacts used in the Friday sales meeting. Touches Zoho exports, parquet rebuilds, and the rep dashboards.

---

## How it runs

- **Trigger:** Manual, Friday before the meeting
- **Sequence:** Zoho exports → parquet rebuild → rep dashboards → KPI dashboard (if needed)

---

## Inputs

| Source | Notes |
|---|---|
| Zoho CSV exports | `skiprows=6`, date format `"%b %d, %Y %I:%M %p"` |
| zoho_client.py | SSL via system truststore |

---

## Outputs

| Destination | Notes |
|---|---|
| Refreshed parquets | meetings, accounts |
| Refreshed dashboards | per-rep + KPI |

---

## Known failure modes

1. **Symptom:** Leads count shows 0 across all reps.
   **Cause:** Wrong CSV date format (used old GMT UTC string instead of `"%b %d, %Y %I:%M %p"`).
   **Fix:** Verify the date parser in zoho_client. See [[feedback_friday_sales_meeting_leads]] and [[feedback_zoho_csv_format]].

2. **Symptom:** SSL handshake fails on Zoho API.
   **Cause:** Local AV TLS inspection breaking certifi-only verification.
   **Fix:** `truststore.inject_into_ssl()`. See [[feedback_python_truststore_for_https]].

3. **Symptom:** Bash check thought refresh succeeded when python failed.
   **Cause:** `python x.py | tail; echo $?` returns tail's RC, not python's.
   **Fix:** Use `python x.py >out 2>err; RC=$?` or `set -o pipefail`. See [[feedback_bash_pipe_exit_code]].

---

## Logs

- Console + per-step log under `C:\Users\quint\.claude\logs\friday-meeting\YYYY-MM-DD.log`

---

## Manual run

Sequence (refer to script-by-script — exact paths confirmed Friday-of):

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"

# 1. Refresh Zoho exports (manual download or scripted)
# 2. Rebuild parquets
python build_store_health.py    # if visits parquet stale

# 3. Rebuild rep dashboards
python build_rep_dashboards.py --auto-compute

# 4. Refresh KPI dashboard if data block was updated
python build_kpi_dashboard.py
```

---

## Recent incidents

- *(see [[feedback_friday_sales_meeting_leads]] — SSL truststore + CSV date format fix)*

---

## Related

- Memory: [[feedback_friday_sales_meeting_leads]], [[feedback_zoho_csv_format]], [[feedback_python_truststore_for_https]], [[feedback_bash_pipe_exit_code]]
- Sister: [[rep-dashboards]], [[kpi-dashboard-weekly]]
