# Safety & Housekeeping Audit + H&S KPI Targets

Proactive counterpart to the reactive **H&S Non-Conformance Report** form.
Where the NCR form captures one-off incidents as they happen, the **Safety
Audit** form captures a scheduled walkthrough of one zone, scored for
compliance, with every failed check logged as a non-conformance.

## Forms — who does what

| Form | Trigger | Cadence | Creator script |
|---|---|---|---|
| H&S Non-Conformance Report | Reactive — an event/injury/near-miss | Ad-hoc | `create_ncr_form.py` |
| **Weekly / Monthly Safety & Housekeeping Audit** | Proactive — scheduled floor walk | Weekly + monthly | `create_safety_audit_form.py` |

## Audit form

- **Header:** audit date · auditor · audit type (Weekly walkthrough / Monthly compliance) · zone
- **Zones:** Production · Resin Plant · Dispatch · Warehouse/Storage · Yard/External · Office
- **Checklist:** 20 checks across 5 categories — Housekeeping & 5S, PPE, Fire & Emergency,
  Chemical & Flammable, Equipment. Each is **Pass / Fail / N-A** with an optional note.
- **Score:** `% compliant = passes / (passes + fails)` — N/A excluded.
- **Photos:** the forms-admin schema has no photo field; for a fail needing photo
  evidence, raise an NCR (which supports upload) and reference the audit ID.

### Pipeline
1. `python create_safety_audit_form.py` — one-shot, creates the live form, writes `safety_audit_form_id.json`.
2. `python poll_safety_audit.py` — on a schedule. For each new audit:
   scores it → appends to `safety_audit_scores.json` → spawns a Notion
   Non-Compliance row per fail (tagged `Audit Finding`) → Telegram summary.
   `--reprocess` rescores/re-logs everything.

## KPI targets

| KPI | Target | Amber | Red |
|---|---|---|---|
| Housekeeping compliance (audit score) | ≥ 90% per zone/week | 75–89% | < 75% |
| NC corrective-action SLA | 100% closed ≤ 14 days | 1+ overdue | 3+ overdue |
| Critical / High open NCs | 0 | 1–2 | 3+ |
| Repeat findings (month-on-month) | Declining | Flat | Increasing |

Targets live in two places, keep them in sync:
- `poll_safety_audit.py` → `HOUSEKEEPING_TARGET_PCT`
- the dashboard **Audit & KPIs** tab in `rebuild_hs_report.py` (to be added)

## Dashboard (planned next step)

A new first tab **Audit & KPIs** on `/health-safety` showing the four KPIs as
big value-vs-target cards (green/amber/red), a weekly compliance trend, a
per-zone latest-score table, and the overdue-NC list. Reads
`safety_audit_scores.json` plus the existing Notion register. Not yet built —
form goes live and collects data first.
