# Runbook — PULSE Bi-weekly Scorecard

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — biweekly performance review document

---

## Purpose

End-of-cycle deep-dive scorecard per rep: visits, leads, plan vs actual, week-cycle compliance, lead conversion. Produced at the close of each 2-week cycle for review with each rep.

---

## How it runs

- **Trigger:** Manual or Task Scheduler at cycle end (Friday week 2)
- **Entry point:** `1.Projects/PULSE v2 — Sales & Ops Manager/pulse/`
- **Invocation:** `python -m pulse.<scorecard_module>`

---

## Inputs

| Source | Path |
|---|---|
| Meetings data | `Meetings_Report_AWS.xlsx` |
| Rep config | `pulse/data.py` |
| Daily mailer history | for visit reconstruction |

---

## Outputs

| Destination | Notes |
|---|---|
| Per-rep scorecard PDF/HTML | shared with each rep |
| Quintus summary | management overview |

---

## Known failure modes

1. **Symptom:** Cycle boundary off by a week.
   **Cause:** Rep's hunting-week declaration not captured for the period.
   **Fix:** Verify cycle declarations for the period before running.

2. **Symptom:** Same PULSE invocation issues as the mailer.
   **Fix:** See [[pulse-daily-mailer]] § Known failure modes.

---

## Logs

- `C:\Users\quint\.claude\logs\pulse\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE v2 — Sales & Ops Manager"
python -m pulse.<scorecard_module>
```

---

## Recent incidents

- *(none recorded yet)*

---

## Related

- Memory: [[reference_pulse_system]]
- Sister: [[pulse-daily-mailer]], [[pulse-leaderboard]]
