# Runbook — Store Health Feedback (Dispatcher + Reminder + Dashboard)

> **Last verified:** 2026-05-27
> **Owner:** STRIKER (reports to APEX)
> **Criticality:** high — customer-facing feedback loop; gates rep activity

---

## Purpose

Sends Daily Account Intel forms to reps, **5 per rep per day, tier-gated**: At Risk accounts must be completed for that rep before any Churning or Good forms go out. Includes `dispatched` (not just `pending`) entries in the gate so submitting forms unlocks the next tier. Reminder digest fires weekdays at 07:00.

---

## How it runs

- **Dispatcher:** `1.Projects/AWS Data/build_store_health_feedback.py` + `build_account_health_forms.py`
- **Reminder:** `send_account_health_reminders.py` — weekday 07:00
- **Poller:** `poll_account_health_forms.py` — pulls submissions
- **Queue file:** `1.Projects/AWS Data/account_health_queue.json`
- **Dashboard:** `https://flomaticauto.github.io/olympic-paints-store-health-feedback/`

---

## Inputs

| Source | Path |
|---|---|
| Sales parquet | velocity / health calculations |
| Zoho accounts | `Account_Site` join key |
| Meetings parquet | `zoho_meetings/data/meetings.parquet` |
| Queue state | `account_health_queue.json` |

---

## Outputs

| Destination | Notes |
|---|---|
| Form dispatch emails | per rep, tier-gated |
| 07:00 reminder digest | only on weekdays |
| Submissions → DB | feeds dashboard |
| Dashboard | live URL above |

---

## Known failure modes

1. **Symptom:** Rep got Good forms before completing At Risk.
   **Cause:** Tier gate didn't include `dispatched` state — submitting (not just dispatching) is what unlocks tiers.
   **Fix:** Verify gate logic in dispatcher includes both `pending` AND `dispatched` for the At Risk tier.

2. **Symptom:** Reminders fired on Saturday.
   **Cause:** Weekday filter missing or wrong.
   **Fix:** Reminders are weekday-only; verify schedule and script `if weekday()` guard.

3. **Symptom:** Visits look stale.
   **Cause:** Reading old xlsx instead of parquet.
   **Fix:** Source is now `zoho_meetings/data/meetings.parquet` (migrated 2026-05-14). See [[reference_store_health]].

4. **Symptom:** Forms reference customer-by-name and mismatch sales data.
   **Cause:** Not joining via `Account_Site`.
   **Fix:** Use `meeting.What_Id_id → accounts.id → Account_Site → invoice.accno`. See [[reference_zoho_account_site]].

---

## Logs

- `C:\Users\quint\.claude\logs\store-health-feedback\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"

# Dispatch today's batch
python build_store_health_feedback.py

# Fire reminder digest manually
python send_account_health_reminders.py

# Poll submissions
python poll_account_health_forms.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_store_health_feedback]], [[reference_store_health]], [[reference_zoho_account_site]]
- Sister: [[ci-verification-tracker]] (different system, similar reminder pattern)
