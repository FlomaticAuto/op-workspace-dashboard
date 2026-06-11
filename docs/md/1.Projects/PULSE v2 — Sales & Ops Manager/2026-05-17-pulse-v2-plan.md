# PULSE v2 — Re-engineering Plan

**Author:** Claude (with Quintus) · **Date:** 2026-05-17 · **Status:** Approved scope, awaiting scaffold go-ahead

---

## Why we're rebuilding

Old PULSE has three problems:

1. **Data accuracy** — not the math (`pulse_data.py` uses `smref`/`ivnett` NET correctly and computes targets dynamically) but the **renderer drift**: two parallel HTML generators (`render_daily_mailer_email` and `render_daily_mailer`) share zero code. Fix one, the other silently goes stale. A daily email is currently 1,555 lines of HTML; `pulse_render.py` is 1,825 lines.
2. **Architecture** — 9 scripts, 8 scheduled Task Scheduler jobs, 2,699 lines across orchestrators. Cycle-label code silently falls back to `?` on join failure (line 33-49 of `pulse_daily.py`). No single entry point.
3. **No human gate** — emails dispatch unattended at 09:00. Quintus only catches errors after reps complain.

## Design principles

- **One template tree, two parents.** Jinja2 `{% extends %}` — `daily.html.j2` extends either `base_email.html.j2` (inline styles) or `base_browser.html.j2` (CSS tokens). One source, two outputs. Drift becomes structurally impossible.
- **One CLI, one config.** Drop the script-per-job model. `python -m pulse <command>` is the only entry point. Task Scheduler jobs become one-line wrappers.
- **Preview gate by default.** Soft gate: render at 09:00 → Telegram preview link → auto-send 09:30 unless Quintus vetoes.
- **Keep the data layer.** `pulse_data.py` is correct. Copy it across, do not rewrite.
- **Side-by-side rollout.** New folder, AC migrated first, old PULSE keeps the other 4 reps running until each cuts over.

## Folder structure

```
1.Projects/PULSE v2 — Sales & Ops Manager/
├── pulse/
│   ├── __init__.py
│   ├── cli.py                  # python -m pulse <cmd>
│   ├── data.py                 # = old pulse_data.py (verbatim copy)
│   ├── payload.py              # build_daily_payload, build_scorecard_payload
│   ├── render.py               # Jinja2 env, filters (money, pct, dates)
│   ├── send.py                 # Outlook send + force-flush, Telegram, GH Pages publish
│   ├── preview_server.py       # Flask :8765 — soft gate
│   └── templates/
│       ├── base_email.html.j2          # inline styles, hardcoded navy
│       ├── base_browser.html.j2        # CSS tokens, theme toggle
│       ├── daily.html.j2               # extends one of the two bases
│       ├── scorecard.html.j2
│       ├── leaderboard.html.j2
│       ├── preview_index.html.j2       # the gate UI
│       └── partials/
│           ├── kpi_card.html.j2
│           ├── store_row.html.j2
│           ├── week_plan.html.j2
│           ├── debtors_panel.html.j2
│           └── recovery_panel.html.j2
├── pulse_config.json           # copied + reduced from old config
├── scheduler/
│   ├── register.ps1            # 5 tasks instead of 8
│   └── unregister.ps1
├── tests/
│   ├── test_payload.py         # data math contracts
│   └── test_render_golden.py   # golden-file diffs so future edits can't drift
├── output/
│   ├── daily/<date>/<rep>.html
│   ├── previews/<date>/        # what the preview server serves
│   ├── approvals.json          # {date: {rep: "approved" | "vetoed" | "auto-sent"}}
│   └── send_log.json           # append-only audit
├── data/                       # planned_week.json, pulse_cycle.parquet
├── pyproject.toml
├── requirements.txt
└── 2026-05-17-pulse-v2-plan.md # this file
```

## CLI surface

```
python -m pulse render-daily [--date YYYY-MM-DD] [--reps AC,AP]
python -m pulse preview                              # start Flask on :8765
python -m pulse send [--rep AC] [--all-approved]    # dispatch approved emails
python -m pulse render-leaderboard
python -m pulse publish-leaderboard
python -m pulse render-scorecard
python -m pulse publish-web                          # JSON snapshots for Vercel app
python -m pulse refresh-cycle                        # weekly cycle parquet rebuild
python -m pulse build-plan                           # weekly planned_week.json
python -m pulse check-acks                           # 17:15 escalation
```

## Preview server contract (soft gate)

```
GET  /                               → index: card per rep + approve buttons
GET  /preview/<rep>?mode=email       → exact HTML the rep would receive
GET  /preview/<rep>?mode=web         → browser-themed version
POST /approve/<rep>                  → marks rep approved in approvals.json
POST /veto/<rep>                     → marks vetoed (won't auto-send)
POST /send-now                       → dispatches all approved immediately
GET  /status                         → JSON: which reps approved/vetoed/pending
```

**Auto-send timer:** when `preview_server.py` starts, it schedules a 30-min background job. At T+30:
- Reps marked `approved` or unmarked (default soft-pass) → dispatch via Outlook.
- Reps marked `vetoed` → skipped; Telegram alert to Quintus with the veto count.
- All outcomes appended to `send_log.json`.

## Scheduler footprint (collapses from 8 to 5)

| Task | Schedule | Command |
|---|---|---|
| PULSE v2 — Morning Render + Preview | weekday 09:00 | `python -m pulse render-daily && python -m pulse preview` |
| PULSE v2 — Leaderboard | weekday 09:15 | `python -m pulse render-leaderboard && python -m pulse publish-leaderboard` |
| PULSE v2 — Web Snapshots | weekday 09:20 | `python -m pulse publish-web` |
| PULSE v2 — Ack Escalation | weekday 17:15 | `python -m pulse check-acks` |
| PULSE v2 — Weekly Plan Refresh | Sun 18:00 | `python -m pulse refresh-cycle && python -m pulse build-plan` |

Bi-weekly scorecard: triggered from the weekly job on alt-Mondays (self-gates on ISO week parity), not a separate Task Scheduler entry.

## Content changes

- **Trim daily email** from 1,555 lines to ≤400. Strategy:
  - Recovery accounts: keep top 3 inline, link to web app for the rest.
  - Week plan: keep today's stores in full detail, condense other days to count + total names.
  - Debtors panel: keep totals + sparkline; drop redundant rep-level table (already in web app).
- **Subject line upgrade**: `PULSE [{rep}] — Rank #{n}/5 · {pct}% of target · {today_count} visits today`
- **Wire Vercel app to real data**: `pulse publish-web` writes `data/daily-<date>.json` to the `olympic-paints-pulse-web` repo. `app/lib/data.ts` rewritten to read from those JSON files. Mock removed.
- **Subject `[TEST]` prefix** when sent to qlategan@gmail.com (i.e. not in `go_live_reps`). Inbox-scanning clarity.

## Migration sequence

1. Scaffold `pulse_v2/` with **AC only**.
2. Run pulse_v2 in `--dry-run` mode for 3 weekdays — preview server starts, nothing dispatches.
3. Cut AC live on pulse_v2; modify old `pulse_daily.py` to skip AC.
4. Migrate AP, BV, NP, BM one at a time (one per week). Each migration = remove from old config, add to new config.
5. When all 5 reps are on pulse_v2, archive `1.Projects/PULSE — Sales & Ops Manager/` to `4.Archive/`.

## Tests

- `tests/test_payload.py` — same shape as existing PULSE tests; assert MTD, target, rank correctness against fixture parquet.
- `tests/test_render_golden.py` — render every template against a fixture payload, diff against `tests/fixtures/golden_<template>.html`. Future template edits require regenerating goldens deliberately. **This is the drift-prevention test.**

## Out of scope (deliberate)

- Bi-weekly scorecard redesign — port template as-is, defer redesign.
- JotForm replacement — keep using existing forms 261282305303042 + 261282828010047.
- Telegram bot rewiring — `pulse_telegram.py` is small (~50 LOC), copy it verbatim.
- Plan-adherence percentage — remains capped at 100% per existing memory `project_pulse_plan_adherence.md`.

## Open questions (none blocking — addressed in chat or above)

All scope questions answered 2026-05-17. Ready to scaffold on go-ahead.
