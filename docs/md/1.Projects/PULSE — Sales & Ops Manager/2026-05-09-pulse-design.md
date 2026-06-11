# PULSE — Sales & Ops Manager
## Design Spec — 2026-05-09

> **Status:** Draft pending user review.
> **Author:** Claude Code (brainstormed with Quintus).
> **Owner once live:** Quintus (APEX) → PULSE agent.
> **Implementation phases:** All built at once (no phased rollout).

---

## 1. Purpose

PULSE is a new Sales & Operations Manager agent for Olympic Paints. Its sole job is to **push sales reps daily** on activity, sales position, and KPI commitments — and to surface accountability gaps to Quintus before they fester.

PULSE owns the **daily rhythm** of sales execution. It does not own analytics depth (PRISM), staff/HR (HAVEN), CRM hygiene (STRIKER), or factory ops (SIGMA), but it **coordinates** with all of them so their work feeds into the rep-facing rhythm.

## 2. Agent identity

| Field | Value |
|---|---|
| Name | **PULSE** |
| Role | Sales & Operations Manager |
| Model | Sonnet |
| Slash command | `/pulse` |
| Reports to | APEX (Quintus) |
| Memory namespace | `agent_pulse_*.md` in user memory |
| Notification channel | Telegram chat `8042233389` |

## 3. Reps in scope

All five sales reps, all running on a 4-week cycle:

| Code | Name | Cycle codes |
|---|---|---|
| AC | Aboo Cassim | AC1, AC2, AC3, AC4 |
| AP | Amit Patel | AP1, AP2, AP3, AP4 |
| BV | Bhadresh Vallabh | BV1, BV2, BV3, BV4 |
| NP | Nikhil Panchal | NP1, NP2, NP3, NP4 |
| BM | Byron Minnie | BM1, BM2, BM3, BM4 |

A "cycle" = the rep's full territory rotation. One full pass takes 4 weeks. Each cycle week has its own designated set of customers/towns.

## 4. Sources of truth

| Data | Source | Already exists? |
|---|---|---|
| Cycle membership (rep × cycle week × customer) | `1.Projects\AWS Data\Delivery Details_Updated_13032026.xlsx` → `consolidated` tab → `arref` column | ✅ |
| Sales (rep × day × customer × value) | Sales parquet (`reference_sales_parquet.md`) | ✅ |
| Per-rep targets | `build_kpi_dashboard.py` data block | ✅ |
| Leads logged | Sales activity files (Zoho daily CSVs) | ✅ |
| Merchandising visits | Zoho Meetings export | ✅ |
| Daily ack + commitment + new stores + product dev | **PULSE Daily JotForm (new — PULSE builds)** | ❌ build |
| Next-week cycle declaration | **PULSE Weekly Intake JotForm (new — PULSE builds)** | ❌ build |
| Customer master (names, towns) | Sales parquet + Delivery Details consolidated | ✅ |

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       PULSE PIPELINE                             │
└─────────────────────────────────────────────────────────────────┘

PLAN SIDE
─────────
Delivery Details_Updated.xlsx
  └─ consolidated tab, arref column
       │
       ▼
pulse_cycle_loader.py     (Sun 18:00, Task Scheduler)
  └─ writes pulse_cycle.parquet  (rep × cycle_week × curef × town)

PULSE Weekly Intake JotForm
  └─ rep declares next week's cycle (AC1/AC2/AC3/AC4) + deviations
  └─ deadline: Thursday 16:00
       │
       ▼
pulse_planner.py          (Sun 19:00)
  └─ joins declared cycle ⨝ pulse_cycle.parquet
  └─ writes planned_week.json  (rep × date → list of planned visits)

ACTUAL SIDE
───────────
Daily 06:00 (weekdays):
  pulse_daily.py
    ├─ Pull yesterday from sales parquet
    ├─ Pull yesterday's logged visits (Zoho meetings)
    ├─ Pull yesterday's leads (sales activity)
    ├─ Pull yesterday's PULSE Daily JotForm submissions
    ├─ Compute MTD sales vs target per rep
    ├─ Compute plan adherence (planned ⨝ actual visits)
    ├─ Render rep-specific HTML mini-mailer (Navy theme, mobile-first)
    ├─ Generate unique JotForm ack URL per rep
    │     ?rep=AC&date=2026-05-13
    └─ Send via Resend API (from pulse@olympicpaints.co.za)
         + Telegram (per rep chat)
         + Resend webhook captures open/bounce events

Daily 17:15 (weekdays):
  pulse_escalation.py
    ├─ Read today's Daily JotForm submissions
    ├─ Identify reps who haven't submitted
    └─ Telegram → Quintus: "AC, NP not acked"

Friday 09:00:
  pulse_intake_escalation.py
    ├─ Read this week's Weekly Intake submissions
    ├─ Identify reps who haven't submitted
    └─ Telegram → Quintus + reminder DM to rep
    └─ If still no submission by Sun 18:00, planner uses default cycle

BI-WEEKLY SCORECARD
───────────────────
Every 2nd Monday 07:00:
  pulse_scorecard.py
    ├─ Aggregate last 14 days from all sources
    ├─ Rank reps on each KPI
    ├─ Render full HTML scorecard (Navy theme)
    ├─ Push to GitHub Pages (private leaderboard URL)
    ├─ Email to all 5 reps + Quintus
    └─ Telegram digest to Quintus

LIVE LEADERBOARD
────────────────
Daily 06:30 (weekdays), after pulse_daily.py:
  pulse_leaderboard.py
    ├─ Render leaderboard HTML (live updated each weekday)
    ├─ Push to GitHub Pages: olympic-paints-pulse-leaderboard
    └─ URL embedded in every daily mailer for rep self-check
```

## 6. The daily mini-mailer

**Cadence:** Every weekday 06:00.
**Channel:** Resend (HTML email from `pulse@olympicpaints.co.za`) + Telegram (text summary).
**Theme:** Navy (executive default).
**Form factor:** Mobile-first, ~3 phone screens long.

**Sections (top to bottom):**

1. **Header strip** — Logo, "PULSE Daily — {rep}", date, current cycle code (e.g. "Cycle AC1, Day 2/5").
2. **YOU ARE** — MTD sales (R + % of target), team rank, plan adherence MTD %.
3. **TODAY'S PLAN** — Planned visits today (from cycle ⨝ planner). List of customer name + town. ~3–8 items.
4. **YESTERDAY** — Planned vs actual visits (✓ / ✗ per customer). Yesterday's sales R-value, yesterday's leads, yesterday's new stores logged.
5. **ACKNOWLEDGE BY 17:00** — Big yellow button → unique JotForm URL. Wording: "Submit today's plan + ack".
6. **Footer** — Link to live leaderboard, link to bi-weekly scorecard URL, "Reply with questions to Quintus".

## 7. The bi-weekly scorecard

**Cadence:** Every 2nd Monday 07:00.
**Channel:** Resend (HTML email from `pulse@olympicpaints.co.za`) + Telegram digest to Quintus + GitHub Pages push.
**Theme:** Navy.
**Distribution:** All 5 reps + Quintus.

**Sections:**

1. **Executive summary** — Team MTD, vs target %, total visits planned/actual, total acks, team plan adherence.
2. **Rep ranking table** — sorted by MTD %target descending. Columns: Rep / Sales / %Tgt / Visits / Plan% / Leads / NewStores / Ack%. Bottom 2 reps flagged ⚠.
3. **Monthly merchandising plan** — One grid per rep (collapsible). 4 cycle weeks × 5 weekdays = 20 cells per customer/town row. Cells coloured: green (visited), amber (overdue), red (missed), grey (not yet due).
4. **Activity log** — Per-rep table, last 14 days. Columns: Date / Cycle Week / Plan(visits) / Actual / Variance / Sales / Ack ✓✗.
5. **New stores & product dev rollup** — Aggregated from daily JotForm submissions, per rep, last 14 days. Customer names listed verbatim.
6. **Footer** — Generated timestamp, link to leaderboard, link to per-rep daily archive.

## 8. The live leaderboard

**Cadence:** Refreshed every weekday 06:30 (after `pulse_daily.py`).
**Channel:** GitHub Pages — new repo `olympic-paints-pulse-leaderboard`.
**Theme:** Navy.
**Audience:** All 5 reps (peer-pressure mechanism) + Quintus.
**Mobile-first.**

**Sections:**

1. Big header: today's date, current cycle week marker per rep.
2. Live ranking table (5 reps, sorted by MTD %target). Three KPI columns visible at a glance: Sales %Tgt / Plan adherence / Ack streak (consecutive days).
3. Visual sparkline: each rep's daily plan-adherence over last 14 days.
4. "Last updated" timestamp.

URL embedded as a button in every daily mailer ("See full leaderboard →").

## 9. JotForms (PULSE builds)

**PULSE creates and owns exactly two JotForms** (not per-rep) via the Jotform MCP server. Both forms are rep-agnostic in their UI — rep identity is carried in the URL param (`?rep=AC`). Cycle weeks are presented as a numeric radio (1/2/3/4) and the rep code is concatenated in storage (e.g. submission row stores `AC` + `2` = `AC2`). Form IDs are stored in `pulse_config.json` and read by all PULSE scripts.

### 9.1 PULSE Daily Ack Form

| Field | Type | Notes |
|---|---|---|
| Rep | hidden | pre-filled from `?rep=AC` URL param |
| Date | hidden | pre-filled from `?date=2026-05-13` |
| Acknowledge yesterday's numbers | required checkbox | "I have read yesterday's results" |
| Today's commitment — calls | required number | |
| Today's commitment — visits | required number | |
| Today's commitment — orders | required number | |
| New stores prospected today (count) | required number | |
| New stores — names/towns | optional text | |
| Product dev conversations (count) | required number | |
| Product dev — notes | optional text | |
| Anything blocking you? | optional text | |
| Submit | button | |

**Deadline:** 17:00 same day. Escalation at 17:15.

### 9.2 PULSE Weekly Intake Form

| Field | Type | Notes |
|---|---|---|
| Rep | hidden | pre-filled |
| Week starting | hidden | next Monday's date |
| Cycle running next week | required radio | 1 / 2 / 3 / 4 (rep code is prefixed from URL param in storage) |
| Deviations from default cycle | optional text | "skipping Phalaborwa, conf in JHB Mon" |
| Special targets for the week | optional text | |
| Submit | button | |

**Deadline:** Thursday 16:00. Escalation Friday 09:00. If still missing Sun 18:00, planner assumes default cycle (next sequential).

## 10. Escalation rules

| Trigger | Action |
|---|---|
| Daily ack not submitted by 17:00 | Telegram to Quintus listing reps who haven't acked. No action against rep directly — Quintus owns confrontation. |
| Weekly intake not submitted by Thursday 16:00 | Telegram to Quintus + Telegram DM to rep ("Reminder: weekly intake due"). |
| Weekly intake still missing Friday 09:00 | Second Telegram to Quintus, escalated wording. |
| Weekly intake still missing Sun 18:00 | Planner assumes default cycle (= next sequential after last submitted). System keeps running. |
| Plan adherence drops below 60% MTD for a rep | Bi-weekly scorecard flags rep ⚠. No mid-cycle alert. |

## 11. Files & paths

```
1.Projects\PULSE — Sales & Ops Manager\
├── 2026-05-09-pulse-design.md       ← this file
├── pulse_config.json                 ← JotForm IDs, rep emails, telegram chat IDs, paths
├── scripts\
│   ├── pulse_cycle_loader.py        ← reads arref → pulse_cycle.parquet
│   ├── pulse_planner.py             ← Sun 19:00, builds planned_week.json
│   ├── pulse_daily.py               ← weekday 06:00, mini-mailer + Telegram
│   ├── pulse_leaderboard.py         ← weekday 06:30, GitHub Pages live leaderboard
│   ├── pulse_escalation.py          ← weekday 17:15, ack escalation
│   ├── pulse_intake_escalation.py   ← Fri 09:00, intake escalation
│   ├── pulse_scorecard.py           ← alt-Mon 07:00, full HTML scorecard
│   └── pulse_render.py              ← shared HTML rendering helpers
├── data\
│   ├── pulse_cycle.parquet          ← rep × cycle_week × curef × town
│   ├── planned_week.json            ← rep × date → planned visits
│   └── archive\                      ← past mailers, scorecards, JotForm dumps
└── output\
    ├── daily\YYYY-MM-DD\<rep>.html  ← per-rep daily mailers
    ├── leaderboard\index.html       ← GitHub Pages source
    └── scorecard\YYYY-MM-DD.html    ← bi-weekly scorecard
```

GitHub Pages repos:
- **Leaderboard:** `flomaticauto/olympic-paints-pulse-leaderboard` (new — to be created)
- **Scorecard archive:** same repo, `/scorecard/YYYY-MM-DD.html` paths

## 12. Design system compliance

All HTML output (daily mini-mailer, scorecard, leaderboard) MUST follow `DESIGN_SYSTEM.md`:
- Default theme: `theme-navy` on `<html>` (executive theme — see memory: `feedback_sales_dashboard_theme.md`).
- Four-button theme toggle on every HTML page.
- Barlow Condensed (display) + Barlow (body) from Google Fonts.
- Official `Olympic Paints Logo Digital.jpg` in `border-radius:50%;overflow:hidden` wrapper. Build scripts copy `LOGO_SRC` to output dir.
- All colours via `--color-*` tokens. Never hardcode hex.
- Chart.js with `barLabels` plugin if charts are used.
- WCAG AA contrast everywhere.

## 13. Notifications

- **Telegram** chat ID `8042233389` for all Quintus-facing alerts.
- **Resend API** for all rep emails. Send from `pulse@olympicpaints.co.za`. API key + sender address in `pulse_config.json` (key stored via env var `RESEND_API_KEY`, never committed). Recipients pulled from `pulse_config.json`.
- Resend webhooks capture `email.opened` and `email.bounced` events → logged to `data/email_events.parquet` and feed the leaderboard "engagement streak" column.
- Stop hook in Claude Code settings handles task-completion baseline.
- PULSE scripts send richer summaries directly via Telegram.

## 14. Out of scope (v1)

The following are explicitly NOT built in this design. Captured here so they don't sneak in:

- Rep-to-rep messaging.
- Customer-facing communication.
- Quote generation (STRIKER's domain).
- Inventory or factory ops (SIGMA's domain).
- Manager 1:1 templates (HAVEN's domain if needed).
- Mid-cycle plan-adherence alerts (only bi-weekly flagging in v1 — daily noise risk too high).
- Predictive scoring / "this rep is about to miss target" forecasting (PRISM territory).
- WhatsApp channel (Telegram-only for v1).
- Rep-facing edit of their cycle map (cycle map is read-only from `arref` in v1; edits go through Quintus updating the spreadsheet).

## 15. Risks & open questions

1. **`arref` data freshness.** If `Delivery Details_Updated.xlsx` is updated only sporadically, the cycle plan can drift from reality. Mitigation: `pulse_cycle_loader.py` logs the file's mtime and warns Quintus via Telegram if it hasn't been updated in 30+ days.
2. **JotForm submission attribution.** URL params can be spoofed/edited by reps. For v1 we trust the URL param (`?rep=AC`); no auth. If misuse appears, add a rep-specific token in v2.
3. **Telegram per-rep chat IDs.** Reps need to DM the bot once for PULSE to pick up their chat ID. Onboarding step. Until then, daily Telegram falls back to email-only.
4. **DNS prerequisite for Resend.** First send blocked until SPF, DKIM, DMARC records are added to `olympicpaints.co.za` DNS. Mitigation: verify domain in Resend before scheduling first daily run; implementation plan gates Phase 1 launch on DNS verification.
5. **Plan-adherence calculation when rep submits "deviations".** If rep declares "skipping Phalaborwa Mon", planner removes those customers from Monday's plan. Need to confirm: does Friday 09:00 escalation still fire if deviations are heavy enough that planner has nothing left?

## 16. Success criteria

1. Within **week 1**: All 5 reps submitting Daily Ack form by 17:00 ≥ 80% of weekdays.
2. Within **week 2**: Weekly Intake submitted by all 5 reps Thursday 16:00 ≥ 80% (4/5 reps).
3. Within **month 1**: Quintus reports "I now know who's slacking by 17:15 every day" — qualitative.
4. Within **month 2**: At least one bi-weekly scorecard surfaces a rep gap that Quintus actions.
5. Within **month 3**: New-stores tracker captures ≥ 10 distinct prospect names across the team.

## 17. Implementation phasing

**Built all at once** (per Quintus's decision). No phased shipping. Single implementation plan covers:

1. Agent profile + slash command + memory pointers (cosmetic / lightweight).
2. Cycle loader + planner + weekly intake form (Thursday rhythm).
3. Daily mini-mailer + ack form + escalation (daily rhythm).
4. Bi-weekly scorecard.
5. Live leaderboard + GitHub Pages repo creation.

Estimated total: **~3 working days** of build (the writing-plans skill will give a more precise breakdown).

## 18. Resend setup (precondition for go-live)

PULSE uses [Resend](https://resend.com) as the transactional email provider. Setup is a one-time precondition — no email goes out until this is complete.

### 18.1 Account & domain

1. Create Resend account at resend.com (free tier — 3,000 emails/month, 100/day; PULSE volume is ~150/month).
2. Add domain `olympicpaints.co.za` in Resend dashboard.
3. Resend generates DNS records to add. Three are required:
   - **SPF** (TXT record)
   - **DKIM** (CNAME or TXT records — Resend uses 3 CNAMEs)
   - **DMARC** (TXT record, recommended `p=none` initially, ramp to `quarantine` later)
4. Add records via whoever manages `olympicpaints.co.za` DNS (Quintus or IT contact).
5. Wait 10–60 minutes for propagation; click "Verify" in Resend dashboard.
6. Once verified, Resend allows sends from `*@olympicpaints.co.za`.

### 18.2 From-address & API key

- Sender: `pulse@olympicpaints.co.za` (dedicated, not Quintus's mailbox).
- Reply-to: `quintusl@olympicpaints.co.za` (so rep replies land with Quintus).
- API key generated in Resend dashboard. Stored as env var `RESEND_API_KEY`. Read by `pulse_render.py` send helper.

### 18.3 Webhook handler

Resend sends events to a webhook URL we configure. Events of interest: `email.delivered`, `email.opened`, `email.bounced`, `email.complained`.

- Webhook endpoint: hosted as a small Flask app (similar to merchandising trigger service on `localhost:8765`) OR via a Make.com scenario that writes to a Notion database / parquet file. Final choice deferred to implementation plan (cheapest is Make.com → Google Sheet → daily parquet sync).
- Each event row appended to `data/email_events.parquet` with: `message_id`, `rep`, `event_type`, `timestamp`.
- `pulse_leaderboard.py` joins this parquet to compute "engagement streak" (consecutive weekdays with at least one open).

### 18.4 Failure modes

| Failure | Detection | Action |
|---|---|---|
| API key invalid / revoked | `pulse_daily.py` logs API error | Telegram alert to Quintus, no email sent that day, retry next morning |
| Domain unverified | Resend rejects all sends | Same as above; gate first daily run on `verify_domain()` check |
| Bounce on a rep address | `email.bounced` webhook | Telegram alert to Quintus naming the rep + bounce reason |
| Rep marks as spam | `email.complained` webhook | Telegram alert; pause sends to that rep until resolved |

### 18.5 Migration path off Resend (if ever needed)

Email send is encapsulated in `pulse_render.py` `send_email()` helper. Swapping providers (e.g. to SES, Postmark, back to Outlook) is a one-function change. No other PULSE code calls Resend directly.

---

## Appendix A — Decisions log (from brainstorming session)

| Q | A |
|---|---|
| Cadence | Daily nudge + bi-weekly scorecard |
| Acknowledgement | JotForm with daily commitment + 17:00 escalation to Quintus |
| New stores / product dev tracking | Reps log via the same daily JotForm |
| Cycle data source | `arref` column in `consolidated` tab of `Delivery Details_Updated.xlsx` |
| Cycle length | 4 weeks (AC1, AC2, AC3, AC4) — all 5 reps |
| Weekly intake day | Thursday 16:00 deadline (not Friday) |
| Agent name | PULSE |
| Build phasing | All at once |
| Live leaderboard | Yes — included |
| JotForm ownership | PULSE builds the forms (via JotForm MCP) |
| Email send path | Resend API (replaces Outlook win32com) — preconditioned on DNS verification of olympicpaints.co.za |
