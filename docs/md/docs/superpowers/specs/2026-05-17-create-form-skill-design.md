# Design Spec — `create-form` Skill

**Date:** 2026-05-17  
**Status:** Approved  
**Author:** Brainstorming session — Quintus + Claude  

---

## Overview

A Claude Code skill (`create-form`) that any agent in the Olympic Paints workspace can invoke whenever it encounters an information gap it cannot resolve from local files, parquet, or Zoho. The skill guides the agent through creating a form on the existing `olympic-paints-forms-admin` Supabase stack, dispatching it via Outlook email, documenting its assumptions, and logging the pending request. A separate scheduled Python script polls for completions and sends a Telegram notification when all respondents have submitted.

---

## Scope

### In scope
- Skill document (`SKILL.md`) read by any agent
- `check_pending_forms.py` — scheduled poller script
- `pending_forms.json` — central log of all open/closed forms
- One new Supabase table: `form_respondents` (respondent tracking, decoupled from answer shape)
- One new API endpoint on `forms-admin`: `GET /api/forms/{form_id}/submissions`
- Updates to existing `create` and `submit` endpoints to write/upsert into `form_respondents`
- Task Scheduler job for the poller
- Telegram notification on form completion and 3-day nudge for partial completion

### Out of scope
- New Vercel projects (forms-admin already serves the form UI)
- JotForm (superseded by forms-admin stack)
- Polling or waiting by the calling agent — agent continues with assumptions immediately

---

## Trigger Conditions

Any agent invokes `create-form` when ALL of the following are true:
1. A piece of information is required to complete or improve the current task
2. The information is not available in local files, parquet, or Zoho CRM
3. The information can be collected via a short form sent to one or more known email addresses

You (Quintus) may also invoke it directly: "create a form to collect X from Y."

**Decision checklist agents use before invoking:**
- [ ] Is it in the sales parquet? → skip
- [ ] Is it in a Zoho CSV or the meetings parquet? → skip
- [ ] Is it in a local file in this repo? → skip
- [ ] None of the above → invoke `create-form`

---

## Form Creation Flow (6 Steps)

### Step 1 — Identify the gap
Document exactly:
- What information is missing (field names, types, why needed)
- Who needs to answer (respondent emails)
- Which agent/task triggered this

### Step 2 — Build the form schema
Construct a JSON schema using the forms-admin flat field format:

```json
{
  "title": "Human-readable title",
  "description": "One sentence explaining context to the respondent",
  "fields": [
    {
      "id": "snake_case_field_id",
      "label": "Question label shown to respondent",
      "type": "text|textarea|select|radio|date|number",
      "required": true,
      "options": ["Option A", "Option B"]
    }
  ]
}
```

**Tone guide by respondent type:**
- **Customer:** Professional, brief, no jargon. "Please confirm your delivery address."
- **Employee:** Direct, friendly. "Which shift do you prefer?"
- **Rep:** Concise, action-oriented. "Confirm your week cycle: 1 / 2 / 3 / 4."

### Step 3 — POST to forms-admin API
```
POST https://olympic-paints-forms-admin.vercel.app/api/forms/create
Authorization: Bearer {FORM_ADMIN_SECRET}
Content-Type: application/json

{
  "schema": { ...field schema from Step 2... },
  "metadata": {
    "title": "...",
    "description": "...",
    "created_by": "AGENT_NAME",
    "context": "One sentence: what triggered this form",
    "respondents": ["email1@domain.com", "email2@domain.com"]
  }
}
```

Response: `{ "form_id": "abc123" }`

### Step 4 — Register in pending log
Append to `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json`:

```json
{
  "form_id": "abc123",
  "title": "...",
  "context": "AGENT_NAME — task description",
  "assumptions": "What the agent assumed in order to continue",
  "respondents": ["email1@domain.com"],
  "submitted": [],
  "nudge_sent": false,
  "created_at": "2026-05-17T09:00:00",
  "status": "open"
}
```

If the file does not exist, create it as a JSON array `[]` and append the first entry.

### Step 5 — Dispatch email via Outlook (win32com)
Send one email per respondent. Use force-flush pattern (see memory: `feedback_outlook_send_flush`).

**Email spec:**
- **Subject:** `[Olympic Paints] Your input needed — {form title}`
- **From:** `quintusl@olympicpaints.co.za`
- **Body:** Navy executive HTML template. Include:
  - Hosted logo: `https://flomaticauto.github.io/olympic-paints-clocking/logo.jpg`
  - One-sentence context (why they're being asked)
  - Button-style link: `https://olympic-paints-forms-admin.vercel.app/f/{form_id}?email={respondent_email}`
  - Footer: "Olympic Paints — this form takes less than 2 minutes to complete."

### Step 6 — Document assumptions in response
Paste this block into the agent's response to Quintus:

```
> ⚠️ Form sent — continuing with assumptions
> Missing: {what information was missing}
> Assumed: {value the agent used to continue}
> Form: "{form title}" sent to {respondent list}
> Will be corrected when responses arrive.
```

---

## Response Collection — `check_pending_forms.py`

**Location:** `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\check_pending_forms.py`

**Schedule:** Weekdays only (Mon–Fri), 08:00 / 12:00 / 16:00 SAST  
**Task Scheduler job:** `\Olympic Paints\Forms\OlympicPaints_CheckPendingForms`  
**Log location:** `C:\Users\quint\.claude\logs\pending-forms\`

**Algorithm each run:**

```
for each entry in pending_forms.json where status == "open":
    GET /api/forms/{form_id}/submissions  (returns list of respondent emails)
    update entry.submitted = intersection(respondents, submitted_emails)

    if len(submitted) == len(respondents):
        entry.status = "closed"
        send_telegram(completion message)

    elif (now - created_at).days >= 3 and not entry.nudge_sent:
        entry.nudge_sent = True
        send_telegram(nudge message)

write pending_forms.json
```

**Telegram — completion message:**
```
✅ Form complete: {title}
Context: {context}
Respondents: {n}/{n} submitted
Assumptions made: {assumptions}
Review: olympic-paints-forms-admin.vercel.app/admin
```

**Telegram — 3-day nudge (sent once only):**
```
⏳ Form pending: {title}
{submitted_count}/{total} responded — {missing_emails} still outstanding
```

**Telegram bot token:** Read from `1.Projects\PULSE — Sales & Ops Manager\.env` → `TELEGRAM_BOT_TOKEN`  
**Chat ID:** `8042233389`

---

## New API Endpoint — forms-admin

**`GET /api/forms/{form_id}/submissions`**

- Gated by `FORM_ADMIN_SECRET` (same header as existing create endpoint)
- Returns: `{ "submitted": ["email1@domain.com", "email2@domain.com"] }` — list of `email` values from `form_respondents` where `submitted_at IS NOT NULL` and `form_id` matches
- Queries `form_respondents` table, not `form_submissions` — respondent tracking is fully decoupled from form answer shape

## New Supabase Table — `form_respondents`

```sql
create table form_respondents (
  id           uuid primary key default gen_random_uuid(),
  form_id      text not null,
  email        text not null,
  submitted_at timestamptz,
  created_at   timestamptz default now(),
  unique (form_id, email)
);
```

**Write pattern:**
- `POST /api/forms/create` — inserts one row per respondent with `submitted_at = NULL`
- `POST /api/submit/{form_id}` (existing submission handler) — upserts `submitted_at = now()` on the matching `(form_id, email)` row when a submission lands

**Why this over metadata convention:** Form answers in `form_submissions.data` can be any shape — a customer address form looks nothing like an employee preference form. Storing respondent tracking in a dedicated table keeps the poller trivially simple and gives a clean audit trail across all forms regardless of their internal structure.

---

## File Summary

| File | Action | Purpose |
|---|---|---|
| `C:\Users\quint\.claude\skills\create-form\SKILL.md` | Create | Skill document read by agents |
| `1.Projects\Forms\check_pending_forms.py` | Create | Scheduled poller |
| `0.Inbox\pending_forms.json` | Create on first use | Open/closed form log |
| `forms-admin: /api/forms/[form_id]/submissions/route.ts` | Add | Submissions query endpoint (reads form_respondents) |
| `forms-admin: supabase migration` | Add | Create `form_respondents` table |
| `forms-admin: /api/forms/create/route.ts` | Update | Insert rows into form_respondents on form creation |
| `forms-admin: /api/submit/[form_id]/route.ts` | Update | Upsert submitted_at in form_respondents on submission |
| Task Scheduler job | Register | Weekdays 08:00/12:00/16:00 |

---

## Constraints & Invariants

- `FORM_ADMIN_SECRET` is never hardcoded — always read from the `_verification/.env`
- Telegram bot token always read from `PULSE/.env` → `TELEGRAM_BOT_TOKEN` (see memory: `feedback_telegram_token_source`)
- Python scripts on this machine require `truststore.inject_into_ssl()` at top (see memory: `feedback_python_truststore_for_https`)
- Logs go to `C:\Users\quint\.claude\logs\` not OneDrive (see memory: `feedback_schtasks_logs_outside_onedrive`)
- Outlook Send() requires force-flush (see memory: `feedback_outlook_send_flush`)
- Email HTML always uses hosted logo URL, not relative path (see memory: `reference_logo_hosted_url`)
- `pending_forms.json` is append-only for open entries; `status: "closed"` entries are never deleted (audit trail)
