# Weekly Sales Report Builder

Single-user, week-scoped qualitative notebook for Olympic Paints sales.

See `docs/superpowers/specs/2026-05-21-weekly-sales-report-builder-design.md` for full design.

## Quick start
1. Copy `.env.example` to `.env` and fill in values.
2. `pip install -r requirements.txt`
3. Run tests: `pytest -v`
4. Register scheduled jobs: `powershell -File scheduler/register.ps1`
