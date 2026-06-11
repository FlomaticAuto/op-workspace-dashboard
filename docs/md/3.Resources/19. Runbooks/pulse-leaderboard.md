# Runbook — PULSE Leaderboard

> **Last verified:** 2026-05-21
> **Owner:** Quintus
> **Criticality:** medium — gamification layer for reps; failure doesn't stop sales

---

## Purpose

Generates the running leaderboard across the 5 reps: visits, leads, plan adherence (capped at 100% — see open issue), week-cycle ranking. Published as the PULSE Leaderboard dashboard.

---

## How it runs

- **Trigger:** Windows Task Scheduler, `\PULSE v2\*`
- **Schedule:** Weekday **06:00** (build) / **06:30** (publish)
- **Entry point:** `1.Projects/PULSE v2 — Sales & Ops Manager/pulse/`
- **Invocation:** `python -m pulse.<leaderboard_module>`

---

## Inputs

| Source | Path |
|---|---|
| Meetings data | `Meetings_Report_AWS.xlsx` |
| Rep config | `pulse/data.py` |
| Hunting week declarations | weekly JotForm intake |

---

## Outputs

| Destination | URL |
|---|---|
| Leaderboard dashboard | (see [[reference_dashboards_inventory]]) |
| Workspace dashboard tile | per memory |

---

## Known failure modes

1. **Symptom:** Plan adherence > 100% or visibly absurd.
   **Cause:** Volume-vs-route-fidelity issue not yet fully fixed; currently capped at 100%.
   **Fix:** Known open issue. See [[project_pulse_plan_adherence]]. Don't "fix" without re-reading the project note.

2. **Symptom:** Week 4 ranking ignores leads.
   **Cause:** Hunting Week scoring not applied — Week 4 is lead-centric (new leads + Zoho Lead-module-linked meetings).
   **Fix:** Verify `pulse_rep_week.py` / `pulse_hunting_week.py` wired; needs `$se_module=='Leads'` filter and `config['reps'][rep]['zoho_email']`. See [[reference_pulse_hunting_week_impl]].

3. **Symptom:** Rep missing from leaderboard.
   **Cause:** Rep hasn't declared current cycle week via weekly JotForm.
   **Fix:** Chase the rep; their week defaults to undefined if not declared.

4. **Symptom:** Same as PULSE Daily Mailer — `python -m` not used, em-dash task name, OneDrive log path.
   **Fix:** See [[pulse-daily-mailer]] § Known failure modes.

---

## Logs

- `C:\Users\quint\.claude\logs\pulse\YYYY-MM-DD.log`

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE v2 — Sales & Ops Manager"
python -m pulse.<leaderboard_module>
```

*(Substitute the actual module name once verified; check `pulse/` directory for the leaderboard entry point.)*

---

## Recent incidents

- **2026-W20** — BV declared PVA cycle; AC/AP/NP still owed week-cycle declaration before Mon 2026-05-18. See [[project_pulse_cycle_confirmations_2026w20]].

---

## Related

- Memory: [[reference_pulse_system]], [[reference_pulse_task_scheduler]], [[project_pulse_plan_adherence]], [[project_pulse_hunting_week]]
- Sister job: [[pulse-daily-mailer]], [[pulse-scorecard]]
