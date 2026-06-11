# Runbook — Competitor Verification Forms Dispatcher

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — drives the CI data collection programme

---

## Purpose

Dispatches per-rep, per-day batches of competitor verification forms. 15 self-hosted Supabase forms at `/f/[form_id]` on `olympic-paints-forms-admin.vercel.app`. Submit-once enforced by `rep_code`. Results aggregated to `output/verification_results.xlsx`.

---

## How it runs

- **Trigger:** Manual, per "day" (each "day" = a product category batch)
- **Entry point:** `3.Resources/17. Strategic Intelligence/_verification/send_verification_emails.py`
- **Invocation:** `python send_verification_emails.py --day enamel|pva|waterproofing`
- **Form IDs:** `output/supabase_form_ids.json`
- **Results:** `python pull_verification_results.py` aggregates into `output/verification_results.xlsx`

---

## Inputs

| Source | Path |
|---|---|
| Form IDs map | `_verification/output/supabase_form_ids.json` |
| Rep roster | `_verification/.env` or config |
| Email template | inside dispatcher |

---

## Outputs

| Destination | Notes |
|---|---|
| Email per rep | with form links for that day's category |
| Telegram dispatch confirm | chat `8042233389` |
| Aggregated results | `output/verification_results.xlsx` |

---

## Known failure modes

1. **Symptom:** Rep submitted but form rejects duplicate.
   **Cause:** Submit-once is by `rep_code`; expected behaviour if they already submitted.
   **Fix:** Not a bug. Confirm in Supabase that row exists for that rep_code+form_id.

2. **Symptom:** Form link 404s.
   **Cause:** `supabase_form_ids.json` stale; form was rebuilt with new ID.
   **Fix:** Re-run `build_supabase_forms.py` and regenerate the IDs file.

3. **Symptom:** Telegram leaked PAT token.
   **Cause:** Dispatcher logged the `AUTHORIZATION: basic <b64>` header on push failure.
   **Fix:** Verify token redaction is in place. See [[feedback_hub_push_token_redaction]].

4. **Symptom:** Reps emailed Kishan/Sejal on CC.
   **Cause:** Old one-off CC list got reused.
   **Fix:** Default CC is **empty**. See [[feedback_rep_email_cc]].

---

## Logs

- `C:\Users\quint\.claude\logs\competitor-verification\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification"

# Dispatch one day's batch
python send_verification_emails.py --day enamel
python send_verification_emails.py --day pva
python send_verification_emails.py --day waterproofing

# Pull aggregated results
python pull_verification_results.py
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_competitor_verification_forms]], [[feedback_rep_email_cc]]
- Sister: [[ci-verification-tracker]]
