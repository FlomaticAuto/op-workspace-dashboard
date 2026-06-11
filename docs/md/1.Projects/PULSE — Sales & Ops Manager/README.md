# PULSE — Sales & Operations Manager

Daily push system for Olympic Paints sales reps. See the [design spec](./2026-05-09-pulse-design.md) and [implementation plan](./2026-05-09-pulse-implementation-plan.md).

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in keys.
3. Verify Resend domain (see spec §18).
4. Run `python scripts/pulse_jotform.py --create-forms` once to create JotForms; commit updated `pulse_config.json`.
5. Run `python scripts/pulse_cycle_loader.py` once to seed `data/pulse_cycle.parquet`.
6. Register Task Scheduler entries: `powershell -ExecutionPolicy Bypass -File scheduler/register.ps1`

## Daily flow
- 06:00 weekday: `pulse_daily.py` — per-rep email + Telegram
- 06:30 weekday: `pulse_leaderboard.py` — refreshes GitHub Pages
- 17:15 weekday: `pulse_escalation.py` — Telegrams Quintus if any rep hasn't acked
- Sun 18:00: `pulse_cycle_loader.py` — refreshes cycle parquet
- Sun 19:00: `pulse_planner.py` — builds next week's plan
- Fri 09:00: `pulse_intake_escalation.py` — Telegrams Quintus if any rep skipped intake
- Alt Mon 07:00: `pulse_scorecard.py` — bi-weekly scorecard

## Tests
`python -m pytest tests/ -v`
