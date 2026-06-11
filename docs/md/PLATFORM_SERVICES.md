# Platform Services — the shared layer beneath the agents

Some capabilities are used by almost every agent: WhatsApp, Telegram, email, Supabase, and
GitHub Pages publishing. Historically these lived *inside* one agent's profile (mostly
STRIKER), which created false ownership — PRISM's PULSE cards depend on "STRIKER's"
WhatsApp infra, SIGMA and HAVEN both push to GitHub Pages, everyone Telegrams the same chat.

**These are services, not domains.** No single agent owns them. Agents *call* them. This file
is the one place their configuration lives. When a credential, webhook, or token changes,
change it here and every agent inherits it.

Machine-readable copy of this lives under `services:` in [`agents/jobs.yaml`](./agents/jobs.yaml).

---

## 1. WhatsApp (outbound)

All WhatsApp sends — PULSE daily cards, CI reminders, store-health summaries — go through a
single Make scenario. Do not add second paths.

| Detail | Value |
|---|---|
| Scenario | "Claude Send WhatsApp" (ID 9301106) |
| Webhook URL | `https://hook.eu2.make.com/og4xli5ljkagkuas1om2oragzy2xxpm2` |
| Hook ID | 4158647 |
| Sending number | Flomatic (+27 60 272 8236) |
| Client module | `3.Resources/17. Strategic Intelligence/_verification/whatsapp_client.py` |

**Two send modes** (the Make scenario routes on `image_url` presence):

- Image + caption: `send_whatsapp_image(image_url, caption, to="...")`
- Plain text: `send_whatsapp(message, to="...")`

`to` is international format, no `+` (e.g. `27835889057`). The retired n8n webhook
(`neil2007.app.n8n.cloud`) returns 404 — never use it.

**Rep numbers** (also in `pulse_config.json` `"whatsapp"`):

| Code | Name | WhatsApp |
|---|---|---|
| AC | Aboo Cassim | 27835889057 |
| AP | Amit Patel | 27828991825 |
| BV | Bhadresh Vallabh | 27826173879 |
| NP | Nikhil Panchal | 27828991826 |
| BM | Byron Minnie | 27604987117 |

> Consumers: STRIKER (CI, store health, PULSE cards), PRISM (PULSE data), HAVEN (weekly summary).

---

## 2. Telegram (notifications)

Every job notification and the APEX health monitor post to one chat.

| Detail | Value |
|---|---|
| Ops chat ID | `8042233389` |
| Token source | env `TELEGRAM_BOT_TOKEN`, falling back to `1.Projects/PULSE v2 — Sales & Ops Manager/.env` |
| Send pattern | stdlib `urllib` POST to `https://api.telegram.org/bot<token>/sendMessage` |

**Rules:**
- Never hardcode the token in a script — read it from env/.env. (Some legacy scripts still
  inline it; migrate them when touched.)
- Send **plain text**, not Markdown, unless you escape — job names and file paths contain
  `_` and `.` that break Telegram's legacy Markdown and silently fail the send.

> Consumers: all agents.

---

## 3. Email (Outlook win32com)

| Detail | Value |
|---|---|
| Account | `quintusl@olympicpaints.co.za` |
| Mechanism | `win32com` automation — **Outlook must be running** on the box |
| Critical | Force-flush the Outbox after `mail.Send()` (it only queues) |
| Inbound routing | Hik-Connect → `Reporting/HR`; Netstar → `Inbox`; ODO → routed by Quintus |

Gmail MCP is used only when explicitly requested. If Outlook is closed, every email-dependent
job (HAVEN clocking, e-commerce digest, CI emails) fails silently — this is a top dead-man's
switch trigger.

> Consumers: HAVEN, PRISM, STRIKER, SIGMA.

---

## 4. Supabase (state + storage)

The closest thing the system has to a shared database. Use it as the operational state store
going forward rather than inventing new JSON/markdown ledgers.

| Use | Where |
|---|---|
| Form submissions | `form_submissions` (store health, CI verification, H&S NCR, returns) |
| CI WhatsApp dedupe | `ci_whatsapp_batch` — unique `(rep_code, form_id)` |
| Image hosting | Storage buckets `form-uploads/pulse-cards`, `store-health/`, CI cards |
| Returns | Vercel form → Supabase → GitHub Pages dashboard |

> Consumers: STRIKER, SIGMA, PRISM.

---

## 5. Publishing (GitHub Pages → Vercel portal)

Dashboards are static HTML pushed to `FlomaticAuto/*` GitHub Pages repos, proxied by the
Vercel portal.

| Detail | Value |
|---|---|
| Portal | `https://portal.olympicpaints.co.za` |
| Push auth | ephemeral `http.extraheader` from `gh auth token --user FlomaticAuto` — never embed token in remote URL |
| Deploy | portal does **not** auto-deploy on push — run `deploy.ps1` (see OPERATIONS_RUNBOOK.md) |

Live dashboards: clocking, vehicles, store-health-feedback, returns, rock-bottom.

> Consumers: HAVEN, SIGMA, STRIKER, PRISM.

---

## 6. Job platform (scheduling, heartbeats, health)

The backbone every scheduled task runs on. Lives in the **`op-workspace-dashboard`** repo
(`~/workspace-dashboard`), *not* in this OneDrive folder.

| Piece | Path | Role |
|---|---|---|
| Wrapper | `scripts/olympic_platform/run_job.py` | Wraps each task: `python run_job.py <job-id> --agent <AGENT> -- <cmd>`. Writes a heartbeat (ok/exit/duration) per run; Telegrams immediately on failure. |
| Heartbeat helper | `scripts/olympic_platform/heartbeat.py` | Atomic writes to `~/.claude/heartbeats/<job-id>.json` (+ `.history.jsonl`). |
| Manifest builder | `scripts/olympic_platform/build_schedule_manifest.py` | Hourly (`PRISM \ Build Schedule Manifest`). Enumerates every `\Olympic Paints\*` task via COM, merges heartbeats → `data/schedule_manifest.json`. |
| Daily digest | `agents/apex_health_monitor.py` (this repo) | Reads the manifest, sends the daily green/red roll-up + dead-man's switch. |
| Migration | `scripts/olympic_platform/migrate_tasks.ps1` / `restore_tasks.ps1` | Wrap/unwrap existing tasks; XML round-trip with backups. |

**Conventions:** every task lives at `\Olympic Paints\<AGENT>\<Name>`; heartbeats and logs live
under `~/.claude/` (never OneDrive). Operator guide: `scripts/olympic_platform/README.md`.

> Consumers: all agents. This is the layer `jobs.yaml`/`agents/heartbeat.py` used to duplicate
> before they were retired (2026-06-03).

---

## Why this matters

Pulling these out of agent profiles fixes the boundary leaks the assessment flagged:

- PULSE (PRISM) no longer "borrows" STRIKER's WhatsApp — both call the WhatsApp service.
- One place to rotate the Make webhook, Telegram token, or `gh` auth.
- New agents/jobs wire into existing services instead of copying snippets.

When you build a new job: pick its **owner agent** for the domain logic, but call these shared
services for delivery. Record the job in `agents/jobs.yaml`.

---

## Related

- Manifest: [`agents/jobs.yaml`](./agents/jobs.yaml)
- Agent roster: [`agents/README.md`](./agents/README.md)
- Supervisor: [`agents/APEX.md`](./agents/APEX.md)
- Deployment specifics: [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md)
