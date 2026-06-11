# CLAUDE.md — Quick Reference Index

Navigation hub for Olympic Paints automation documentation. Use this to find what you need fast.

---

## ⚡ Strategic Intelligence — ALWAYS CHECK FIRST

**Before producing any analysis, strategy, report, or recommendation, read the relevant files in [`3.Resources/17. Strategic Intelligence/`](./3.Resources/17.%20Strategic%20Intelligence/).**

These files contain accumulated business intelligence that must inform all work. Do not start from scratch — build on what is already known.

| File | Contains |
|---|---|
| [`product-intelligence.md`](./3.Resources/17.%20Strategic%20Intelligence/product-intelligence.md) | Enamel tier structure, SKU data, list prices, rock bottom floors, open product questions |
| [`pricing-intelligence.md`](./3.Resources/17.%20Strategic%20Intelligence/pricing-intelligence.md) | Rock bottom performance, actual selling prices, discount patterns, governance rules |
| [`customer-intelligence.md`](./3.Resources/17.%20Strategic%20Intelligence/customer-intelligence.md) | Problem accounts, active leads, lost accounts, segment notes |
| [`market-intelligence.md`](./3.Resources/17.%20Strategic%20Intelligence/market-intelligence.md) | Competitors, geographic traction, channel conditions, market feedback |
| [`rep-performance.md`](./3.Resources/17.%20Strategic%20Intelligence/rep-performance.md) | Rep roster, KPI targets, discount patterns, activity log |
| [`strategy-decisions.md`](./3.Resources/17.%20Strategic%20Intelligence/strategy-decisions.md) | Decisions made, open questions, things tried and abandoned |

**How to add new intelligence:** Either tell me directly ("add this to customer intelligence: ...") or drop raw notes/files into `0.Inbox/` and ask me to process them. I will extract insights and file them in the correct location.

**Coverage:** Currently seeded with enamel range analysis (May 2026). Expand to other product ranges and business areas as intelligence is gathered.

---

## Agent Roster — APEX, HAVEN, PRISM, STRIKER, SIGMA, BLAZE, VAULT

**→ See [`agents/README.md`](./agents/README.md)**

- Full agent roster with domains and routing cheat sheet
- Per-agent profiles: owned systems, scripts, runbooks, critical rules
- Routing: not sure who handles it? Start here.

**System of record & health:**

- `workspace-dashboard/data/schedule_manifest.json` — **source of truth** for the task list + live health. Auto-generated hourly by the Olympic Platform (`op-workspace-dashboard/scripts/olympic_platform/build_schedule_manifest.py`). Never hand-edited.
- [`agents/apex_health_monitor.py`](./agents/apex_health_monitor.py) — APEX daily digest. `python agents/apex_health_monitor.py --dry-run` answers "what ran / what failed?". Runs Mon–Fri 09:30 + 18:00; no 09:30 message (or a >2h-stale manifest) = box is down.
- [`agents/job_criticality.json`](./agents/job_criticality.json) — curated criticality overlay (the only hand-maintained job metadata).
- [`PLATFORM_SERVICES.md`](./PLATFORM_SERVICES.md) — shared WhatsApp / Telegram / email / Supabase / publishing + the job platform (not owned by any one agent).

---

## For Designers & Frontend Developers

**→ See [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md)**

- Theme system (Light, Dark, Brand, Navy)
- CSS token blocks and custom properties
- Typography scale (Barlow Condensed / Barlow)
- Logo SVG specs and usage
- Report layout templates (KPI, clocking, management)
- WCAG compliance rules
- Critical HTML rules (no frameworks, theme toggle required, inline SVG only)

---

## For Operations & Runbook Procedures

**→ See [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md)**

- Repository structure (PARA folders: 0.Inbox, 1.Projects, 2.Areas, 3.Resources)
- Clocking pipeline setup and deployment
- KPI dashboard weekly update checklist
- Data flow diagrams
- Troubleshooting guides
- Employer split rules (Olympic Paints / Primeserve)
- Backup and archival procedures

---

## For Developers Running Scripts

**→ See [`SCRIPTS_REFERENCE.md`](./SCRIPTS_REFERENCE.md)**

- Script command reference (build_report.py, process_inbox.py, gen_dashboard.py, haven_watcher.py, haven_dashboard_check.py)
- How to run each script and what flags are required
- Critical rules (--master flag, 45-min break deduction, employer IDs)
- Email and Telegram notification setup
- Key paths and output destinations
- Rep codes and GitHub Pages URLs

---

## Quick Links

| What | Where | How |
|---|---|---|
| Check what's running / what failed today? | agents/apex_health_monitor.py | `python agents/apex_health_monitor.py --dry-run` — reads schedule_manifest.json, shows green/red per job |
| Add, retire, or reschedule a job? | Task Scheduler + olympic_platform | Register/wrap the task (platform `run_job.py`); it appears in schedule_manifest.json automatically. Set importance in agents/job_criticality.json. Then re-run export_schtasks.ps1. |
| Look up a product colour / RGB / HEX code? | 3.Resources/1. Products Related Information/product-colour-coding.md | 62 products, 815 SKUs, 1,050 Colorworks swatches with R/G/B and HEX |
| Add market/product/customer intelligence? | 3.Resources/17. Strategic Intelligence/ | Tell me the insight and which file it belongs to, or drop raw notes in 0.Inbox/ |
| Drop a competitor price list or field intel? | 3.Resources/17. Strategic Intelligence/_field-intake/ | Drop PDF/image there; note which competitor it covers |
| Run competitor verification forms? | 3.Resources/17. Strategic Intelligence/_verification/ | `send_verification_emails.py --day enamel\|pva\|waterproofing` |
| Need to generate HTML? | DESIGN_SYSTEM.md | Copy the boilerplate, use CSS tokens, include theme toggle |
| Process new clocking data? | OPERATIONS_RUNBOOK.md | Run `process_inbox.py`, check troubleshooting section |
| Run e-comm logistics-cost ingest / monthly report? | 2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/ | `python -m _scripts.ingest_logistics_invoices` to ingest, `python -m _scripts.logistics_cost_monthly` for the monthly table |
| ~~Update KPI dashboard?~~ | ~~OPERATIONS_RUNBOOK.md + SCRIPTS_REFERENCE.md~~ | ⚠️ **DEPRECATED 2026-05-25** — workflow discontinued, do not run |
| Write a Python script? | SCRIPTS_REFERENCE.md | Check script reference table, follow employer classification rules |
| Design a dashboard? | DESIGN_SYSTEM.md | Pick a report layout template, use theme tokens |
| Need to know Telegram chat ID? | SCRIPTS_REFERENCE.md | Chat ID is `8042233389` |
| Employee classification? | SCRIPTS_REFERENCE.md or OPERATIONS_RUNBOOK.md | SD prefix = Primeserve, all others = Olympic Paints |

---

## Repository at a glance

```
Olympic Paints (PARA structure)
├── 0.Inbox/               ← incoming files, new Advius exports
├── 1.Projects/
│   ├── AWS Data/          ← KPI dashboard scripts
│   └── KPI Report/        ← PDF source data
├── 2.Areas/
│   └── 11. HR/
│       └── Clocking Reports/
│           ├── scripts/   ← haven_* scripts, build_report.py
│           └── Output/    ← Clocking Report YTD.xlsx, index.html
└── 3.Resources/
    ├── 17. Strategic Intelligence/  ← ⚡ ALL competitor intelligence (TDS/MSDS, workbooks, price lists, verification system, field intake) + strategic knowledge base (.md files)
    └── (other resources)            ← SOPs, product info, meeting minutes
```

---

## Key facts (TL;DR)

- **Master files:** `Clocking Report YTD.xlsx` in `2.Areas/11. HR/Clocking Reports/Output/`
- **45-minute break:** Applied per shift, every employee, no exceptions
- **Employers:** Primeserve (SD*), Olympic Paints (all others). Always split reporting.
- **KPI data:** Manually extracted from QuickSight PDFs, updated weekly
- **Telegram chat:** `8042233389` for all notifications
- **GitHub Pages:** Clocking at `https://flomaticauto.github.io/olympic-paints-clocking/`, KPI at `https://flomaticauto.github.io/olympic-paints-kpi/`
- **Design:** Barlow Condensed (display) + Barlow (body). Four themes. Always use CSS tokens, never hardcode hex.
- **No frameworks:** Vanilla CSS, vanilla JS. Chart.js from CDN only if asked.

---

## Document locations

| File | Purpose |
|---|---|
| [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) | CSS tokens, theme system, logo, typography, WCAG rules |
| [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) | Repo structure, deployment, procedures, troubleshooting |
| [`SCRIPTS_REFERENCE.md`](./SCRIPTS_REFERENCE.md) | Script reference table, command syntax, paths, notification setup |
| [`3.Resources/17. Strategic Intelligence/`](./3.Resources/17.%20Strategic%20Intelligence/) | ⚡ All competitor intelligence + business knowledge base — TDS/MSDS catalogues, comparison workbooks, price lists, verification system, .md knowledge files |
| **CLAUDE.md** (this file) | Navigation hub & quick reference |

---

# Coding Behavior Guidelines (Karpathy-inspired)

> Source: [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) — behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.
>
> **Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
