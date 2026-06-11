# STRIKER — Sales & CRM

> Owns Zoho CRM, quoting, stockist management, ODO flash submissions, rep performance tracking, rock bottom pricing governance, store health feedback, and competitor intelligence dispatch.

---

## Domain

Everything that faces outward to customers, stockists, and reps. STRIKER is the operational layer between the sales team and the systems they rely on daily.

**STRIKER is the responsible owner for:**
- Sending the daily CI (Competitor Intelligence) verification emails to reps
- Monitoring rep progress on CI form completion and reporting back to APEX
- Dispatching the daily Store Health / Account Intel forms to reps
- Monitoring store health feedback submission rates and escalating to APEX when reps are lagging

---

## Owned systems

### ODO Flash Submissions

Daily price-sheet submissions to OneDayOnly (3-week rotating cycle, Mon–Thu). STRIKER owns the full loop from draft creation through to deal confirmation.

**Script:** `flash_submit.py` — `2.Areas/1. Sales/2. ODO/` — runs automatically via Task Scheduler Mon–Thu 07:00.

#### STRIKER's daily accountability loop

| Time | Check | Action if not OK |
|---|---|---|
| 07:30 | Confirm Telegram message arrived: "FLASH: ODO sheet drafted for [date]…" | Re-run `flash_submit.py` manually; Telegram Quintus |
| 09:30 | **`odo_status_check.py` runs automatically** — searches Outlook Sent + Drafts, Telegrams result | Script fires; three outcomes: ✅ sent · ⚠️ still in Drafts · ❌ no draft found |
| EOD | Log draft status in `DEAL_LEDGER.md` as `submitted` once sent, `held` if not | — |

**Friday cadence (weekly):** Telegram Quintus at 09:30 with a one-line state summary pulled from `DEAL_LEDGER.md`:
> "ODO weekly state: [N] submissions sent this week · [N] awaiting sign-off · [N] POs in flight · [N] invoices unpaid."

#### Deal finalization tracking

STRIKER monitors inbound ODO emails for the two finalization signals:

1. **Sign-off ("Freeze the stock") received** → update `DEAL_LEDGER.md` to `frozen-pending-confirmation`, run the verification checklist (`FLASH_PLAYBOOK.md § B`), draft confirmation reply, Telegram Quintus.
2. **PO received** → update ledger to `po-received`, begin invoice + dispatch sequence per `FLASH_PLAYBOOK.md § E`, Telegram Quintus at each state transition.

STRIKER does **not** independently monitor email — Quintus routes inbound ODO emails into STRIKER's context. STRIKER acts within 30 minutes of being handed an email.

**Key docs:**
- `2.Areas/1. Sales/2. ODO/FLASH_PLAYBOOK.md` — full submission + response SOP
- `2.Areas/1. Sales/2. ODO/SUBMISSION_SCHEDULE.md` — 3-week cycle and product slots
- `2.Areas/1. Sales/2. ODO/CONTACTS.md` — ODO contacts (update on every AM change)
- `2.Areas/1. Sales/2. ODO/DEAL_LEDGER.md` — live deal state register
- `2.Areas/1. Sales/2. ODO/PRICING_BOOK.md` — cost ex-VAT + RSP + floor prices

---

### Store Health Feedback (Account Intel Forms)

Daily Account Intel forms dispatched to reps — 5 per rep per day, tier-gated (At Risk accounts unlock before Churning/Good).

**STRIKER's daily responsibility:** Ensure the dispatcher fires each weekday. Monitor submission rates. If a rep has outstanding forms for more than 2 weekdays without progress, escalate to APEX.

**Entry points:**
- `build_store_health_feedback.py` — dispatcher
- `build_account_health_forms.py` — form builder
- `send_account_health_reminders.py` — weekday 07:00 reminder
- `poll_account_health_forms.py` — pulls submissions

**Queue:** `1.Projects/AWS Data/account_health_queue.json`
**Dashboard:** `https://flomaticauto.github.io/olympic-paints-store-health-feedback/`
**Runbook:** [store-health-feedback.md](../3.Resources/19. Runbooks/store-health-feedback.md)

#### Store Health WhatsApp dispatcher

Sends each rep a matrix card image + up to 3 outstanding form links via WhatsApp. Confirmed working as of 2026-05-28.

**Files (both in `1.Projects/AWS Data/`):**
- `store_health_whatsapp_dispatcher.py` — main dispatcher (generates card, shortens URLs, sends)
- `store_health_matrix_card.py` — generates and uploads the PNG to Supabase Storage

**To run manually for a single rep:**
```
python store_health_whatsapp_dispatcher.py --rep AC
```

**To send to your own number for testing:**
```
python store_health_whatsapp_dispatcher.py --rep AC --to 27748660437
```

**Confirmed rules — never change these without testing:**

- **Single daily send at 09:00 only** — one run per weekday, not the CI 3-slot pattern (08:00 / 12:00 / 17:00). Store health is a morning briefing, not a chase cycle. Do not add extra slots.
- **No shared scheduling with CI** — the two dispatchers are independent. Store health runs at 09:00; CI slot 1 runs at 08:00. Never merge them or align their send times.
- **Image first, links second** — always send the matrix card image (with caption) before the links text message. 2-second sleep between them.
- **Only send forms with `status == "dispatched"`** — never include forms where `status == "complete"`. The batch is built from `outstanding = [e for e in entries if e.get("status") == "dispatched"]`. If a rep has zero outstanding dispatched forms, skip them entirely — no message, no card, just silence.
- **BATCH_SIZE = 3** — send at most 3 outstanding form links per run per rep.
- **URLs shortened via TinyURL** — `https://tinyurl.com/api-create.php?url=...`. Falls back to original URL on any error.
- **Card filename includes Unix timestamp** — e.g. `store-health/AC_Thu_28_May_2026_1748xxxxxx.png` — busts Supabase CDN cache on every upload.
- **Text message footer line:** `"Tap a link to open. Note: links will show a 5-second redirect screen before opening the form — this is normal."`
- **Card theme: light** — yellow header, logo, white/grey body, navy footer. Never dark theme.

**Card layout (health tier × status matrix):**

| (row) | Complete | Awaiting | Pending |
|---|---|---|---|
| At Risk | count | count | count |
| Churning | count | count | count |
| Good | count | count | count |

- Progress bar beneath header shows `complete / total` for the rep
- Footer (navy): `"X awaiting response"` in yellow
- Cells colour-coded: Complete = green, Awaiting = amber, Pending = slate

**WhatsApp numbers:** pulled from `pulse_config.json` `"whatsapp"` field per rep. Use `--to` flag to override for testing.

---

### Competitor Intelligence (CI) Verification Dispatch

75-cell matrix: 5 reps × 5 competitors × 3 categories. STRIKER is responsible for sending the daily batch and monitoring completion.

**STRIKER's daily responsibility:** Run `send_verification_emails.py --day [enamel|pva|waterproofing]` each weekday morning. Check the 08:30 Telegram accountability report. Report progress back to APEX. Escalate any rep with zero submissions or stale outstanding forms.

**Current status (as of 2026-05-27):**

| Rep | Submitted | Total | Remaining |
|---|---|---|---|
| AC — Aboo Cassim | 14 | 15 | 1 |
| AP — Amit Patel | 1 | 15 | 14 |
| BV — Bhadresh Vallabh | 2 | 15 | 13 |
| NP — Nikhil Panchal | 0 | 15 | 15 |
| BM — Byron Minnie | 15 | 15 | DONE ✓ |

**Scripts:**
- `send_verification_emails.py --day [enamel|pva|waterproofing]` — dispatch today's batch
- `send_ci_reminders.py` — auto-runs Mon–Fri 07:00, sends outstanding-only links per rep (email)
- `ci_accountability_check.py` — auto-runs Mon–Fri 08:30, Telegram summary to Quintus
- `pull_verification_results.py` — pull live submission counts to Excel
- `ci_whatsapp_dispatcher.py --slot [1|2|3]` — WhatsApp batch dispatcher (see below)

**Location:** `3.Resources/17. Strategic Intelligence/_verification/`
**Runbooks:** [ci-verification-tracker.md](../3.Resources/19. Runbooks/ci-verification-tracker.md), [competitor-verification.md](../3.Resources/19. Runbooks/competitor-verification.md)

**Feedback loop:** STRIKER reviews the 08:30 Telegram report daily and reports anomalies (missed dispatch, zero-submission reps, overdue cells) directly to APEX.

#### CI WhatsApp batch dispatcher

Sends outstanding CI form links directly to each rep's WhatsApp in small batches across the day. Confirmed working configuration as of 2026-05-28.

| Slot | Task name | Time | What it sends |
|---|---|---|---|
| 1 | `OlympicPaints_CIWhatsApp_Slot1` | 08:00 | Matrix image card first, then 2 shortened links |
| 2 | `OlympicPaints_CIWhatsApp_Slot2` | 12:00 | 2 shortened links only |
| 3 | `OlympicPaints_CIWhatsApp_Slot3` | 17:00 | 2 shortened links only |

**Confirmed rules — never change these without testing:**
- **Image always sent before the text message** (slot 1 only; slots 2+3 are text-only)
- **Card theme: light** — white/grey background, navy text, navy footer strip. Never dark/navy theme for CI cards.
- **URLs shortened via TinyURL** — card filename includes a Unix timestamp suffix to bust Supabase CDN cache on every upload (e.g. `AP_Thu_28_May_2026_1779950227.png`)
- **Text message footer line:** `"Tap a link to open. Note: links show a 5-second redirect screen before opening the form — this is normal."`
- Runs Mon–Fri only; hour guard (08:00–18:00) built in
- Tracks sent forms in Supabase `ci_whatsapp_batch` table — unique constraint on `(rep_code, form_id)` prevents duplicates
- **Never send if all forms are complete** — skip the rep entirely if outstanding count is zero. No "well done" or confirmation message, just silence.

**Files:**
- `ci_whatsapp_dispatcher.py` — main dispatcher
- `ci_matrix_card.py` — light-theme matrix PNG generator
- `register_ci_whatsapp_dispatcher_tasks.ps1` — re-register scheduled tasks
- Logs: `%USERPROFILE%\.claude\logs\ci-whatsapp\slot[1|2|3].log`

**To run manually for a single rep:**
```
python ci_whatsapp_dispatcher.py --slot 1 --rep AP --force
```

---

### PULSE Daily WhatsApp Cards

Each weekday morning STRIKER sends a personalised PULSE scorecard image to each active rep via WhatsApp, followed by clickable links in the caption.

#### Active reps (WhatsApp send list)

| Code | Name | WhatsApp number |
|---|---|---|
| AC | Aboo Cassim | 27835889057 |
| AP | Amit Patel | 27828991825 |
| BV | Bhadresh Vallabh | 27826173879 |
| NP | Nikhil Panchal | 27828991826 |
| BM | Byron Minnie | 27604987117 |

#### How to generate and send

**Step 1 — Generate the card image**

Run from `1.Projects/PULSE v2 — Sales & Ops Manager/`:

```python
from pulse_whatsapp_card import generate_and_upload
url = generate_and_upload(
    rep_code="AC",
    rep_name="Aboo Cassim",
    date_str="Wed 27 May 2026",   # format: "Ddd DD Mon YYYY"
    mtd_sales=757642.73,
    mtd_target=1748690.78,
    pct=0.4333,                   # mtd_sales / mtd_target
    rank=3,                       # 1–5
    total_reps=5,
)
# url = Supabase public URL for the uploaded PNG
```

The file is uploaded to Supabase Storage at:
`form-uploads/pulse-cards/{REP_CODE}_{date_str_underscored}.png`

**Step 2 — Send via Make webhook**

POST to `https://hook.eu2.make.com/og4xli5ljkagkuas1om2oragzy2xxpm2`

```json
{
  "to": "27835889057",
  "image_url": "<supabase public URL from step 1>",
  "caption": "PULSE Daily - Aboo Cassim - Wed 27 May 2026\n\nDashboard: https://olympic-paints-pulse-v2.vercel.app/today/AC\nDaily Plan: https://olympic-paints-pulse-v2.vercel.app/daily/latest/AC"
}
```

**Caption format (exact):**
```
PULSE Daily - {Rep Name} - {date_str}

Dashboard: https://olympic-paints-pulse-v2.vercel.app/today/{REP_CODE}
Daily Plan: https://olympic-paints-pulse-v2.vercel.app/daily/latest/{REP_CODE}
```

- `to` must be in international format with country code, no `+` (e.g. `27835889057`)
- The two URLs in the caption render as tappable links in WhatsApp
- Make scenario: **"Claude Send WhatsApp"** (ID 9301106), hook ID 4158647
- Sending number: Flomatic (+27 60 272 8236)
- Use `send_whatsapp_image()` from `whatsapp_client.py` for image sends (not the old `send_whatsapp()`)

#### Daily data comes from `publish-web`

The MTD figures used to build the card come from the same `build_daily_payload` used by the email mailer. Run `publish-web` first each morning to ensure the numbers are current:

```
python -m pulse publish-web
```

Then generate and send cards for AC and AP.

#### Timing

Send after `publish-web` completes — typically 07:30 weekdays, after the daily email send.

---

### WhatsApp Infrastructure

All WhatsApp sends — PULSE cards, CI reminders, store health — go through a single Make scenario.

| Detail | Value |
|---|---|
| Scenario | "Claude Send WhatsApp" (ID 9301106) |
| Webhook URL | `https://hook.eu2.make.com/og4xli5ljkagkuas1om2oragzy2xxpm2` |
| Hook ID | 4158647 |
| Sending number | Flomatic (+27 60 272 8236) |
| Client module | `3.Resources/17. Strategic Intelligence/_verification/whatsapp_client.py` |

#### Two send modes

**Image + caption** (PULSE daily cards):
```json
{"to": "27835889057", "image_url": "<supabase URL>", "caption": "..."}
```
Use `send_whatsapp_image(image_url, caption, to="...")` from `whatsapp_client`.

**Plain text** (CI reminders, store health summaries):
```json
{"to": "27835889057", "message": "..."}
```
Use `send_whatsapp(message, to="...")` from `whatsapp_client`.

The Make scenario routes on `image_url` presence — no other config needed. The n8n webhook (`neil2007.app.n8n.cloud`) is retired and returns 404; do not use it.

#### Rep WhatsApp numbers

| Code | Name | WhatsApp |
|---|---|---|
| AC | Aboo Cassim | 27835889057 |
| AP | Amit Patel | 27828991825 |
| BV | Bhadresh Vallabh | 27826173879 |
| NP | Nikhil Panchal | 27828991826 |
| BM | Byron Minnie | 27604987117 |

Numbers are also stored as `"whatsapp"` field in `pulse_config.json`.

---

### Rock Bottom Pricing

Floor pricing governance. Below-RB report publishes daily.

| Script | Location |
|---|---|
| `_build_rock_bottom_comparison.py` | `2.Areas/1. Sales/1. Pricing/Rock Bottom/` |

**Publish repo:** `C:\Users\<user>\olympic-paints-rock-bottom` (outside OneDrive — must be cloned on each machine)
**Scheduled task:** `\Olympic Paints\Sales\OlympicPaints_BelowRB`
**Intel:** [3.Resources/17. Strategic Intelligence/pricing-intelligence.md](../3.Resources/17. Strategic Intelligence/pricing-intelligence.md)

---

### Credit App Completions Dashboard

Per-rep metric: signed credit applications vs customers with credit limit > 0.

**Entry point:** `1.Projects/AWS Data/build_credit_apps_dashboard.py`
**Runbook:** [credit-apps-dashboard.md](../3.Resources/19. Runbooks/credit-apps-dashboard.md)

---

### Rep Codes

| Code | Name |
|---|---|
| AC | Aboo Cassim |
| AP | Amit Patel |
| BV | Bhadresh Vallabh |
| NP | Nikhil Panchal |
| BM | Byron Minnie |

---

## Key intelligence files

| File | Contains |
|---|---|
| [pricing-intelligence.md](../3.Resources/17. Strategic Intelligence/pricing-intelligence.md) | Rock bottom performance, actual selling prices, discount patterns, governance rules |
| [customer-intelligence.md](../3.Resources/17. Strategic Intelligence/customer-intelligence.md) | Problem accounts, active leads, lost accounts, segment notes |
| [rep-performance.md](../3.Resources/17. Strategic Intelligence/rep-performance.md) | Rep roster, KPI targets, discount patterns, activity log |
| [market-intelligence.md](../3.Resources/17. Strategic Intelligence/market-intelligence.md) | Competitors, geographic traction, channel conditions |

---

## Related

- ODO playbook: [2.Areas/1. Sales/2. ODO/FLASH_PLAYBOOK.md](../2.Areas/1. Sales/2. ODO/FLASH_PLAYBOOK.md)
- Runbooks: [store-health-feedback.md](../3.Resources/19. Runbooks/store-health-feedback.md), [credit-apps-dashboard.md](../3.Resources/19. Runbooks/credit-apps-dashboard.md), [friday-sales-meeting.md](../3.Resources/19. Runbooks/friday-sales-meeting.md)
- Strategic intel: [3.Resources/17. Strategic Intelligence/](../3.Resources/17. Strategic Intelligence/)
