# Olympic Paints — Agent Roster

Six specialist agents under APEX. Each owns a domain, a set of automated jobs, and a slice of the repo.

> **System of record:** the Olympic Platform (`op-workspace-dashboard/scripts/olympic_platform/`) auto-generates `schedule_manifest.json` — the source of truth for every job's schedule + live health. [`apex_health_monitor.py`](./apex_health_monitor.py) reads it and Telegrams a daily green/red digest + dead-man's switch; criticality is curated in [`job_criticality.json`](./job_criticality.json). Shared infra (WhatsApp, Telegram, email, Supabase, publishing, the job platform) lives in [`PLATFORM_SERVICES.md`](../PLATFORM_SERVICES.md). *(`jobs.yaml` and `heartbeat.py` here are retired — they duplicated the platform.)*

| Agent | Domain | Profile |
|---|---|---|
| **APEX** | Managing Director — routes all tasks | [APEX.md](./APEX.md) |
| **HAVEN** | HR & People | [HAVEN.md](./HAVEN.md) |
| **PRISM** | Analytics & Reporting | [PRISM.md](./PRISM.md) |
| **STRIKER** | Sales & CRM | [STRIKER.md](./STRIKER.md) |
| **SIGMA** | Operations & Supply Chain | [SIGMA.md](./SIGMA.md) |
| **BLAZE** | Marketing & Content | [BLAZE.md](./BLAZE.md) |
| **VAULT** | Admin, Filing & Documents | [VAULT.md](./VAULT.md) |

---

## Routing cheat sheet

| Task type | Agent |
|---|---|
| Clocking, payroll hours, staff dashboards | HAVEN |
| KPI numbers, charts, YoY, QuickSight data | PRISM |
| Zoho CRM, quotes, reps, stockists, ODO flash | STRIKER |
| Dispatch, factory, vehicles, supply chain | SIGMA |
| Social, copy, campaigns, product photos | BLAZE |
| New task, new doc, Notion, inbox, filing, credit apps | VAULT |
| Anything else / unclear | APEX routes it |

---

## New task? → VAULT  |  New document? → VAULT + relevant agent
