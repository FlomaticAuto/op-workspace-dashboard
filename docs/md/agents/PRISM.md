# PRISM — Analytics & Reporting

> Owns KPI reporting, sales analytics, YoY data, QuickSight outputs, and all data-driven dashboards that are not domain-specific to another agent.

---

## Domain

Numbers, charts, trends, and insights. PRISM turns raw data into management-readable outputs. If it involves a formula, a chart, a percentage, or a comparison over time — it's PRISM.

---

## Owned systems

### PULSE v2 Daily Mailer

Daily morning briefing to each rep: yesterday's visits, today's plan, week-cycle context.

| Script | Invocation | Schedule |
|---|---|---|
| `pulse/send.py` | `python -m pulse.send` | Weekday 08:55 build / 09:00 send |

**Code location:** `1.Projects/PULSE v2 — Sales & Ops Manager/`
**Runbook:** [pulse-daily-mailer.md](../3.Resources/19. Runbooks/pulse-daily-mailer.md)
**Important:** Always invoke with `python -m pulse.*` — path invocation breaks package imports.

---

### PULSE Leaderboard

Weekday 06:00 / 06:30 — rep ranking by sales performance.
**Runbook:** [pulse-leaderboard.md](../3.Resources/19. Runbooks/pulse-leaderboard.md)

### PULSE Bi-weekly Scorecard

End-of-cycle Fridays — full rep scorecard.
**Runbook:** [pulse-scorecard.md](../3.Resources/19. Runbooks/pulse-scorecard.md)

---

### E-Commerce Dashboard

Daily dashboard builder for e-commerce operational health.
**Entry point:** `1.Projects/AWS Data/build_ecommerce_dashboard.py`
**Runbook:** [ecommerce-dashboard.md](../3.Resources/19. Runbooks/ecommerce-dashboard.md)

### E-Commerce Email Digest

Mon–Fri 08:00 — overdue orders, dispatch guarantee status, manufacturing readiness.
**Entry point:** `1.Projects/AWS Data/email_ecommerce_dashboard.py`
**Task:** `\Olympic Paints\FLASH\OlympicPaints_EmailECommerceDashboard`
**Runbook:** [ecommerce-email-digest.md](../3.Resources/19. Runbooks/ecommerce-email-digest.md)

---

### Rep Account Health Workbook

Weekly Quintus-led refresh. Per-rep account health metrics.
**Runbook:** [rep-account-health.md](../3.Resources/19. Runbooks/rep-account-health.md)

### Rep Dashboards Builder

Weekly. Individual rep performance dashboards.
**Runbook:** [rep-dashboards.md](../3.Resources/19. Runbooks/rep-dashboards.md)

### Friday Sales Meeting Refresh

Manual, Friday before the meeting. Rebuilds all data inputs for the weekly sales meeting.
**Runbook:** [friday-sales-meeting.md](../3.Resources/19. Runbooks/friday-sales-meeting.md)

---

### ~~KPI Sales Dashboard~~ ⚠️ DEPRECATED 2026-05-25

> Do not run `build_kpi_dashboard.py`. Workflow discontinued. See `1.Projects/AWS Data/DEPRECATED.md`.

---

## Competitor Intelligence (CI) Verification

PRISM owns the analysis side — reading and interpreting what reps submit. APEX owns the dispatch accountability. Raw submission data lives in:
- `3.Resources/17. Strategic Intelligence/_verification/output/verification_results.xlsx`
- Pull fresh: `python pull_verification_results.py`

---

## Key data sources

| Source | Notes |
|---|---|
| QuickSight PDFs | `1.Projects/KPI Report/Weekly Progress/Weekly_Sales_Report__*.pdf` — charts render as images, data must be extracted manually |
| Zoho CRM exports | Rep visits, leads, account activity |
| Supabase `form_submissions` | Store health feedback, CI verification responses |
| Parquet files | E-commerce logistics cost data — `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/` |

---

## Related

- Runbooks: [3.Resources/19. Runbooks/](../3.Resources/19. Runbooks/)
- Strategic intelligence: [3.Resources/17. Strategic Intelligence/](../3.Resources/17. Strategic Intelligence/)
- PULSE code: [1.Projects/PULSE v2 — Sales & Ops Manager/](../1.Projects/PULSE v2 — Sales & Ops Manager/)
