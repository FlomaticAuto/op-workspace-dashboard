# Runbook — CI Verification Tracker (Portal + Reminders)

> **Last verified:** 2026-05-27
> **Owner:** STRIKER (reports to APEX)
> **Criticality:** medium — competitive intelligence collection programme

---

## Purpose

Tracks rep completion of competitor verification forms across the 75-cell matrix (5 reps × 15 competitors). Page lives at `/ci-tracker` on `olympic-paints-portal.vercel.app`. Daily weekday reminder at 07:00 nudges reps with outstanding cells.

---

## How it runs

- **Tracker page:** `/ci-tracker` route in Olympic Portal v1 (Next.js, Vercel)
- **Dispatch log:** Supabase table `ci_dispatch_log`
- **Reminder script:** `3.Resources/17. Strategic Intelligence/_verification/send_ci_reminders.py`
- **Schedule:** Daily weekday **07:00**
- **Env:** `3.Resources/17. Strategic Intelligence/_verification/.env` → `SUPABASE_SERVICE_ROLE_KEY`

---

## Inputs

| Source | Notes |
|---|---|
| Supabase `ci_dispatch_log` | dispatched / completed state per rep × competitor |
| Form IDs | `3.Resources/17. Strategic Intelligence/_verification/output/supabase_form_ids.json` |

---

## Outputs

| Destination | Notes |
|---|---|
| Portal page `/ci-tracker` | 75-cell visual matrix |
| Reminder emails | only reps with outstanding cells |
| Telegram summary | chat `8042233389` |

---

## Known failure modes

1. **Symptom:** Reminder script can't read Supabase.
   **Cause:** `SUPABASE_SERVICE_ROLE_KEY` missing or rotated.
   **Fix:** Add/refresh in `_verification/.env`.

2. **Symptom:** Same rep gets reminded for cells they already submitted.
   **Cause:** Submit handler didn't update `ci_dispatch_log` row to `completed`.
   **Fix:** Check Supabase row state; the script filters out completed cells.

3. **Symptom:** Reminder fires Saturday/Sunday.
   **Cause:** Weekday guard missing.
   **Fix:** Reminders are weekday-only.

4. **Symptom:** Portal page shows blank matrix.
   **Cause:** Vercel build broken or RLS rejecting reads.
   **Fix:** Check Vercel deployment, verify portal's RLS policies on `ci_dispatch_log`.

---

## Logs

- `C:\Users\quint\.claude\logs\ci-tracker\YYYY-MM-DD.log`
- Vercel deployment logs for portal

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification"
python send_ci_reminders.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_ci_tracker]], [[reference_competitor_verification_forms]], [[reference_olympic_portal_v1]]
- Sister: [[competitor-verification]] (the dispatcher side), [[store-health-feedback]]
