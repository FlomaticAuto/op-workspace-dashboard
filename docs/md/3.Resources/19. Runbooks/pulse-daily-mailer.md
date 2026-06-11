# Runbook — PULSE v2 Daily Mailer

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** high — five reps depend on it for daily acknowledgement; silence = no plan for the day

---

## Purpose

Builds and sends each rep's daily morning briefing: yesterday's visits, today's plan, week-cycle context. Mobile-first email rendered with Jinja2 templates. Lives on Vercel as `olympic-paints-pulse-v2.vercel.app` with local preview at `:8770` gating before send.

---

## How it runs

- **Trigger:** Windows Task Scheduler, path `\PULSE v2\*`
- **Schedule:** Weekday **08:55** (build) / **08:58** (preview gate) / **09:00** (send)
- **Entry point:** `1.Projects/PULSE v2 — Sales & Ops Manager/pulse/`
- **Invocation:** `python -m pulse.send` *(must use `-m`; path invocation breaks package imports — see [[feedback_pulse_scripts_python_m]])*
- **Env:** `1.Projects/PULSE v2 — Sales & Ops Manager/.env` (TELEGRAM_BOT_TOKEN, SMTP creds, Zoho keys)

---

## Inputs

| Source | Path | Notes |
|---|---|---|
| Meetings data | `Meetings_Report_AWS.xlsx` | consumed at runtime |
| Rep config | `pulse/data.py` / `config.json` | per-rep zoho_email, current cycle week |
| Templates | `pulse/render.py` + Jinja2 templates | mobile-first |

---

## Outputs

| Destination | Notes |
|---|---|
| Email to each rep | per-rep address, single column ≤768px, ≥16px body |
| Preview gate | `http://localhost:8770` — manual approve before send |
| Vercel app | `olympic-paints-pulse-v2.vercel.app` — web archive |
| Telegram confirm | chat `8042233389` |

---

## Known failure modes

1. **Symptom:** Task Scheduler shows green but no email arrived.
   **Cause:** Script ran from path (e.g. `python pulse/send.py`) and silently failed on imports.
   **Fix:** Verify task command uses `python -m pulse.send`. See [[feedback_pulse_scripts_python_m]].

2. **Symptom:** schtasks /change by name fails silently.
   **Cause:** Task names contain em-dash (U+2014), not hyphen.
   **Fix:** Use Schedule.Service COM for edits, not schtasks. See [[feedback_pulse_task_names_em_dash]].

3. **Symptom:** "Yesterday" section shows plan-adherence %, not total visits.
   **Cause:** Regression — section must list every store visited with green ✓, repeats marked `(×N)`.
   **Fix:** See [[feedback_pulse_total_visits_not_plan_adherence]].

4. **Symptom:** Email renders broken on phone.
   **Cause:** Lost mobile-first invariants (single column, 16px body, 44px tap targets, viewport-fit=cover).
   **Fix:** See [[feedback_pulse_v2_mobile_first]].

5. **Symptom:** Telegram token error.
   **Cause:** Hardcoded token from memory used instead of `.env`.
   **Fix:** Always read from `1.Projects/PULSE v2 — Sales & Ops Manager/.env` → `TELEGRAM_BOT_TOKEN`. See [[feedback_telegram_token_source]].

6. **Symptom:** Logs missing / job killed with -1073741510.
   **Cause:** Logs written to OneDrive path; OneDrive sync hangs network calls.
   **Fix:** Log to `C:\Users\quint\.claude\logs\pulse\`. See [[feedback_schtasks_logs_outside_onedrive]].

---

## Logs

- `C:\Users\quint\.claude\logs\pulse\YYYY-MM-DD.log`
- Vercel build logs: `olympic-paints-pulse-v2` project

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE v2 — Sales & Ops Manager"

# Build today's payload + preview
python -m pulse.payload
python -m pulse.preview_server   # opens :8770

# Send for real (after preview OK)
python -m pulse.send

# Specific rep only
python -m pulse.send --rep BV
```

---

## Recent incidents

- **2026-05-17** — Cutover from PULSE v1 to v2 for all 5 reps. v1 scheduler disabled, v2 scheduler at `\PULSE v2\*` weekday 08:55/08:58/09:00.

---

## Related

- Memory: [[reference_pulse_v2]], [[reference_pulse_system]], [[reference_pulse_task_scheduler]], [[feedback_pulse_v2_mobile_first]]
- Sister job: [[pulse-leaderboard]]
- Cycle context: [[reference_pulse_hunting_week_impl]]
