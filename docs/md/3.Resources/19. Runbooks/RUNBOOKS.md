# Olympic Paints — Runbooks Index

One markdown file per automated job. Open the relevant runbook when something didn't fire, produced wrong output, or you need to invoke it manually.

**New job?** Copy [`_template.md`](./_template.md) → `your-job.md` → add a row to the table below.

---

## How to use this index

1. **Incident at 07:00** → scan the table, find the job, click the link, jump to **Known failure modes** or **Manual run**.
2. **New automation built** → copy `_template.md`, fill it in same day as the script lands, add to this index.
3. **Weekly drift check** (Mon 06:30) — audit script compares each runbook's `Last verified` date against the git mtime of the script it documents. Stale runbooks (>30 days behind their script) → Telegram alert to `8042233389`.

---

## Conventions

- **Logs live outside OneDrive** for scheduled Python jobs. Use `C:\Users\quint\.claude\logs\<job>\` — OneDrive sync hangs network calls and Task Scheduler kills the process with `STATUS_CONTROL_C_EXIT` (-1073741510).
- **Telegram bot token** comes from `1.Projects/PULSE v2 — Sales & Ops Manager/.env` → `TELEGRAM_BOT_TOKEN`. Never hardcode.
- **PULSE scripts** are invoked with `python -m scripts.<name>` — package imports break when invoked by path.
- **Email goes via Outlook win32com** by default. Force-flush the Outbox after `mail.Send()` (queues only). Gmail MCP only when explicitly requested.
- **GitHub pushes** to `FlomaticAuto/*` repos use an ephemeral `http.extraheader` from `gh auth token --user FlomaticAuto`. Never embed the token in the remote URL.
- **op-workspace-dashboard** Vercel production branch is `main`. After every commit also push to `master:main`.

---

## Index

| # | Job | Schedule | Criticality | Runbook |
|---|---|---|---|---|
| 1 | HAVEN Clocking pipeline | Mon–Fri 07:00 extract → 07:30 process → 08:45 dashboard → 17:00 EOD; Mon 08:00 weekly check | high | [haven-clocking.md](./haven-clocking.md) |
| 2 | ~~KPI Sales Dashboard~~ ⚠️ DEPRECATED 2026-05-25 | — (discontinued) | — | [kpi-dashboard-weekly.md](./kpi-dashboard-weekly.md) |
| 3 | PULSE v2 Daily Mailer | Weekday 08:55 | high | [pulse-daily-mailer.md](./pulse-daily-mailer.md) |
| 4 | PULSE Leaderboard | Weekday 06:00 / 06:30 | medium | [pulse-leaderboard.md](./pulse-leaderboard.md) |
| 5 | PULSE Bi-weekly Scorecard | Fri end-of-cycle | medium | [pulse-scorecard.md](./pulse-scorecard.md) |
| 6 | Store Health Feedback dispatcher | Weekday + 07:00 reminder | high | [store-health-feedback.md](./store-health-feedback.md) |
| 7 | CI Verification Tracker reminders | Weekday 07:00 | medium | [ci-verification-tracker.md](./ci-verification-tracker.md) |
| 8 | Competitor Verification Forms dispatcher | Manual per day (enamel/pva/waterproofing) | medium | [competitor-verification.md](./competitor-verification.md) |
| 9 | E-Commerce Email Digest | Mon–Fri 08:00 | medium | [ecommerce-email-digest.md](./ecommerce-email-digest.md) |
| 10 | E-Commerce Dashboard builder | Daily / on-demand | medium | [ecommerce-dashboard.md](./ecommerce-dashboard.md) |
| 11 | Credit App Completions dashboard | Weekly | low | [credit-apps-dashboard.md](./credit-apps-dashboard.md) |
| 12 | Merchandising Plan heatmap rebuild | Weekly | medium | [merchandising-plan.md](./merchandising-plan.md) |
| 13 | CSO Insights HTML + email pages | On-demand | medium | [cso-insights.md](./cso-insights.md) |
| 14 | Health & Safety NCR form poller | Continuous / interval | high | [hs-ncr-poller.md](./hs-ncr-poller.md) |
| 15 | Returns Manager folder watcher | Continuous | medium | [returns-watcher.md](./returns-watcher.md) |
| 16 | Rep Account Health workbook refresh | Weekly (Quintus-led) | medium | [rep-account-health.md](./rep-account-health.md) |
| 17 | Rep Dashboards builder | Weekly | medium | [rep-dashboards.md](./rep-dashboards.md) |
| 18 | Notion ↔ todos.md sync | Every 2h | low | [notion-todos-sync.md](./notion-todos-sync.md) |
| 19 | Friday Sales Meeting refresh | Fri before meeting | high | [friday-sales-meeting.md](./friday-sales-meeting.md) |
| 20 | Weekly Sales Report Notion mirror | Continuous + 5-min sweep | medium | [weekly-sales-report-notion.md](./weekly-sales-report-notion.md) |
| 21 | SIGMA Vehicle Fleet Dashboard | Mon 08:00–08:15 | medium | [sigma-vehicle-dashboard.md](./sigma-vehicle-dashboard.md) |
| 22 | APEX System Health Monitor (watchdog over all jobs) | Mon–Fri 09:30 + 18:00 | high | [apex-health-monitor.md](./apex-health-monitor.md) |

---

## See also

- [`_template.md`](./_template.md) — canonical structure every new runbook uses
- [`../../OPERATIONS_RUNBOOK.md`](../../OPERATIONS_RUNBOOK.md) — repo-wide deployment overview (separate from per-job runbooks)
- [`../../CLAUDE.md`](../../CLAUDE.md) — navigation hub
