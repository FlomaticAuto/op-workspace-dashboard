# Runbook — Health & Safety NCR Form Poller

> **Last verified:** 2026-06-03
> **Owner:** Quintus (Albertina is the form user)
> **Criticality:** high — legal/compliance trail; missed NCRs are a liability

---

## Purpose

Polls submissions from Albertina's H&S Non-Conformance Report form (live Supabase form, 14 fields, ID `796c234d-51f0-43f7-a8c5-a1642415bf71`). New submissions land in the Notion H&S database and a Telegram alert fires.

---

## How it runs

- **Poller:** `2.Areas/12. Health and Safety/poll_ncr_submissions.py`
- **Refresh:** `weekly_hs_refresh.py` (weekly aggregation)
- **Report rebuild:** `rebuild_hs_report.py` — generates 8-tab navy HTML on demand via Control Tower Manual Executions

---

## Inputs

| Source | Notes |
|---|---|
| Supabase form | ID `796c234d-51f0-43f7-a8c5-a1642415bf71`, 14 fields |
| Albertina emails | parsed by `download_albertina_emails.py` |

---

## Outputs

| Destination | Notes |
|---|---|
| Notion H&S DB | data source `f8bc92c4-...` under DB `1c65caba811b41a88cd83b92ad156ebd` |
| Telegram alert | chat `8042233389` |
| HTML report | `2.Areas/12. Health and Safety/Output/index.html` (on demand) |

---

## Known failure modes

1. **Symptom:** Form submitted but no Notion row.
   **Cause:** Notion API rejected `parent.database_id` instead of `data_source_id` (2025-09-03 API rules).
   **Fix:** Use `parent.data_source_id` on `/pages` create; integration must be shared with the H&S DB. See [[feedback_notion_api_2025_data_source]].

2. **Symptom:** Telegram alert never fired.
   **Cause:** Token from memory used instead of `.env`.
   **Fix:** Read from PULSE `.env`. See [[feedback_telegram_token_source]].

3. **Symptom:** Albertina's emails not appearing.
   **Cause:** `download_albertina_emails.py` Outlook session lost.
   **Fix:** Restart Outlook; verify win32com session.

---

## Logs

- `C:\Users\quint\.claude\logs\hs-ncr\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\12. Health and Safety"

# Poll for new submissions
python poll_ncr_submissions.py

# Download Albertina's emails
python download_albertina_emails.py

# Rebuild HTML report
python rebuild_hs_report.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_ncr_form]], [[reference_health_safety_tracker]]
