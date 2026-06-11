# HAVEN — HR & People

> Owns the clocking pipeline, employee dashboards, payroll data integrity, and all HR-adjacent automation.

---

## Domain

Everything that touches employee time, attendance, and HR reporting. HAVEN is the source of truth for hours worked — payroll depends on it.

---

## Owned systems

### Clocking Pipeline (primary)

> **Verified ground truth — 2026-06-03.** This block is the canonical description of the
> clocking pipeline. `OPERATIONS_RUNBOOK.md` and `3.Resources/19. Runbooks/RUNBOOKS.md`
> must match it. Source of truth is `agents/jobs.yaml`.

**Source:** The Hik-Connect biometric system emails `Olympic Paints.xlsx` from
`service@mail.hik-partner.com` into the Outlook account `quintusl@olympicpaints.co.za`,
folder `Reporting/HR` (routed there by an Outlook rule). *Not* Advius — Advius is the
HR vendor copied on the output email, not the source of the punches.

**Flow (fully automated, Mon–Fri):**
Hik-Connect email → extractor → `Inbox/` → `process_inbox.py` → `build_report.py --master` → `Clocking Report YTD.xlsx` + emails sent → dashboard published → EOD Telegram at 17:00

| Script | Purpose | Scheduled task | When |
|---|---|---|---|
| `extract_hik_connect_emails.py` | Pulls Hik-Connect `.xlsx` from Outlook `Reporting/HR` into `Inbox/`, then calls `process_inbox.py` | `HAVEN - Daily Hik-Connect Extract` | Mon–Fri 07:00 |
| `process_inbox.py` | Validates Inbox files → `build_report.py --master` → updates YTD master → emails → archives input → regenerates dashboard | `\Olympic Paints\HAVEN\Daily Process Inbox` | Mon–Fri 07:30 |
| `build_report.py` | Merges punches into YTD master, applies 45-min break deduction (called by `process_inbox.py`) | — | — |
| `gen_dashboard.py` | Regenerates HTML dashboard from YTD master and pushes to GitHub Pages | `HAVEN - Daily Dashboard Refresh` | Mon–Fri 08:45 |
| `haven_dashboard_check.py` | Dashboard health check + Telegram/WhatsApp weekly summary | `\Olympic Paints\HAVEN\Weekly Dashboard Check` | Mon 08:00 |
| `haven_eod_check.py` | Telegram summary of missed clock-outs for the day | `\Olympic Paints\HAVEN\End-of-Day Clocking Check` | Mon–Fri 17:00 |

**Code location:** `2.Areas/11. HR/Clocking Reports/scripts/`

> ⚠️ **OPEN ITEM — duplicate extractor CONFIRMED (2026-06-03 schtasks export).**
> Both extractor tasks are **Ready** on the Administrator box, so the Hik-Connect mail is
> fetched twice every morning:
> - `HAVEN - Daily Hik-Connect Extract` (root path) — **Ready** — `extract_hik_connect_emails.py` @ 07:00
> - `\Olympic Paints\HAVEN\HAVEN Fetch Clocking Email` — **Ready** — `fetch_clocking_email.py` @ 07:15
>
> (Two dashboard-check tasks — `HAVEN — Daily Clocking Dashboard Check` and
> `HAVEN Clocking Report Daily` — are already correctly **Disabled**.)
>
> **Action:** disable ONE extractor. Recommended: keep the conventionally-pathed
> `\Olympic Paints\HAVEN\HAVEN Fetch Clocking Email` (07:15) + `Daily Process Inbox` (07:30),
> and disable the loose root-path `HAVEN - Daily Hik-Connect Extract` (it is one of the
> mid-session root duplicates noted in MACHINE_SETUP §7). Confirm the two scripts behave
> identically first, since `extract_hik_connect_emails.py` also calls `process_inbox.py`
> internally. Double-processing is currently harmless (`build_report.py --master` dedupes by
> employee+date) but wastes a run and an Outlook session.
>
> ```powershell
> Disable-ScheduledTask -TaskName "HAVEN - Daily Hik-Connect Extract" -TaskPath "\"
> ```
> Then re-run `export_schtasks.ps1` and delete this note.

**Runbook:** [haven-clocking.md](../3.Resources/19. Runbooks/haven-clocking.md)

---

## Critical rules — never violate

1. **Always pass `--master`** to `build_report.py`. Standalone mode wipes the accumulator.
2. **45-minute break deduction** (`BREAK_DEDUCTION_MINS = 45`) — every shift, every employee, no exceptions. Applied in `build_report.py`, never in the dashboard.
3. **Employer classification** — `SD` prefix = Primeserve (28 staff); all others = Olympic Paints (74 staff). Always split reporting by employer.
4. The YTD master is always `Output/Clocking Report YTD.xlsx`. Dated transient outputs must be renamed to it after processing.

---

## Key paths

```
2.Areas/11. HR/Clocking Reports/
├── Inbox/                          ← drop zone for Advius exports
├── Inbox/Archived/                 ← processed inputs moved here
├── Output/Clocking Report YTD.xlsx ← master accumulator
├── Output/index.html               ← dashboard source
└── scripts/                        ← all HAVEN scripts
```

---

## Outputs

| Destination | Consumer |
|---|---|
| `Output/Clocking Report YTD.xlsx` | Payroll |
| `https://flomaticauto.github.io/olympic-paints-clocking/` | Management |
| Email: YTD Excel + missed clock-outs → `accounts@`, `quintusl@olympicpaints.co.za`, `megan@advius.co.za` | Accounts |
| Telegram chat `8042233389` (EOD + weekly) | Quintus |

---

## Employers

| Entity | Employee count | ID pattern |
|---|---|---|
| Olympic Paints | 74 | Any ID not starting with `SD` |
| Primeserve | 28 | IDs starting with `SD` |

---

## Related

- Runbook: [3.Resources/19. Runbooks/haven-clocking.md](../3.Resources/19. Runbooks/haven-clocking.md)
- Scripts: [2.Areas/11. HR/Clocking Reports/scripts/](../2.Areas/11. HR/Clocking Reports/scripts/)
- Dashboard: `https://flomaticauto.github.io/olympic-paints-clocking/`
