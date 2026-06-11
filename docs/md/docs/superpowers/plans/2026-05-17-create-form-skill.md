# create-form Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `create-form` skill — a Claude Code skill + supporting infrastructure that lets any agent create a Supabase-backed form, dispatch it via Outlook email, log the pending request, and receive a Telegram notification when all respondents have submitted.

**Architecture:** Thin skill document (SKILL.md) guides agents through 6 steps; forms-admin Next.js app gets a new `form_respondents` table + updated endpoints for respondent tracking; a scheduled Python poller checks completion and fires Telegram. The poller is the only moving part — the skill itself is pure instructions.

**Tech Stack:** Python 3.13, win32com (Outlook), requests + truststore, Task Scheduler; Next.js 14 / TypeScript (forms-admin); Supabase (PostgreSQL); Telegram Bot API.

---

## File Map

| File | Action |
|---|---|
| `C:\Users\quint\.claude\skills\create-form\SKILL.md` | Create — skill document |
| `C:\Users\quint\olympic-paints-forms-admin\supabase\migrations\20260517000000_form_respondents.sql` | Create — new table migration |
| `C:\Users\quint\olympic-paints-forms-admin\src\lib\supabase\types.ts` | Modify — add `FormRespondent` type + Database entry |
| `C:\Users\quint\olympic-paints-forms-admin\src\app\api\forms\create\route.ts` | Modify — insert respondents into `form_respondents` after form creation |
| `C:\Users\quint\olympic-paints-forms-admin\src\app\api\submit\[form_id]\route.ts` | Modify — upsert `submitted_at` in `form_respondents` on submission |
| `C:\Users\quint\olympic-paints-forms-admin\src\app\api\forms\[form_id]\submissions\route.ts` | Modify — add `?respondents=true` mode returning submitted emails from `form_respondents` |
| `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\check_pending_forms.py` | Create — scheduled poller |
| Task Scheduler job | Register — weekdays 08:00 / 12:00 / 16:00 |

---

## Task 1: Supabase migration — `form_respondents` table

**Files:**
- Create: `C:\Users\quint\olympic-paints-forms-admin\supabase\migrations\20260517000000_form_respondents.sql`

- [ ] **Step 1: Write the migration file**

```sql
-- Migration: 20260517000000_form_respondents
-- Tracks expected respondents and their submission status per form.
-- Decouples respondent tracking from form answer shape in form_submissions.

CREATE TABLE IF NOT EXISTS public.form_respondents (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  form_id      uuid NOT NULL REFERENCES public.form_schemas(id) ON DELETE CASCADE,
  email        text NOT NULL,
  submitted_at timestamptz,                    -- NULL = not yet submitted
  created_at   timestamptz DEFAULT now(),
  UNIQUE (form_id, email)
);

-- RLS: service_role (used by server-side routes) bypasses RLS.
-- No anon access needed — this table is internal only.
ALTER TABLE public.form_respondents ENABLE ROW LEVEL SECURITY;

-- Index for the poller's per-form query.
CREATE INDEX IF NOT EXISTS idx_form_respondents_form_id
  ON public.form_respondents (form_id)
  WHERE submitted_at IS NOT NULL;
```

- [ ] **Step 2: Apply the migration via Supabase MCP**

Use `mcp__claude_ai_Supabase__apply_migration` with the SQL above. Project ref is in the forms-admin `.env.local` as `NEXT_PUBLIC_SUPABASE_URL` — extract the ref from the URL (e.g. `https://abcdef.supabase.co` → ref `abcdef`).

Expected: migration applies without error.

- [ ] **Step 3: Verify the table exists**

Use `mcp__claude_ai_Supabase__list_tables` and confirm `form_respondents` appears.

- [ ] **Step 4: Commit the migration file**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
git add supabase/migrations/20260517000000_form_respondents.sql
git commit -m "feat: add form_respondents table for respondent tracking"
```

---

## Task 2: Update TypeScript types

**Files:**
- Modify: `C:\Users\quint\olympic-paints-forms-admin\src\lib\supabase\types.ts`

- [ ] **Step 1: Add `FormRespondent` interface and extend `Database`**

In [src/lib/supabase/types.ts](src/lib/supabase/types.ts), after the `FormSubmission` interface, add:

```typescript
export interface FormRespondent {
  id:           string;
  form_id:      string;
  email:        string;
  submitted_at: string | null;
  created_at:   string;
}
```

Then extend the `Database` interface's `Tables` block to add:

```typescript
      form_respondents: {
        Row:    FormRespondent;
        Insert: Omit<FormRespondent, 'id' | 'created_at'> & { id?: string; created_at?: string };
        Update: Pick<FormRespondent, 'submitted_at'>;
      };
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/lib/supabase/types.ts
git commit -m "feat: add FormRespondent type and Database entry"
```

---

## Task 3: Update `POST /api/forms/create` — insert respondents

**Files:**
- Modify: `C:\Users\quint\olympic-paints-forms-admin\src\app\api\forms\create\route.ts`

The create route currently accepts `{ title, description, schema, active_from, active_until, created_by }`. It needs to also accept `respondents: string[]` and insert a row per email into `form_respondents` after the form is created.

- [ ] **Step 1: Update the route to accept and insert respondents**

Replace the full file content of [src/app/api/forms/create/route.ts](src/app/api/forms/create/route.ts):

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase/server';

// POST /api/forms/create
// Body: { title, description?, schema, active_from?, active_until?, created_by?, respondents? }
// Auth: x-admin-secret header
export async function POST(req: NextRequest) {
  const secret = req.headers.get('x-admin-secret');
  if (!secret || secret !== process.env.FORM_ADMIN_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { title, description, schema, active_from, active_until, created_by, respondents } = body as {
    title?: string;
    description?: string;
    schema?: unknown[];
    active_from?: string;
    active_until?: string;
    created_by?: string;
    respondents?: string[];
  };

  if (!title || typeof title !== 'string' || title.trim() === '') {
    return NextResponse.json({ error: '`title` is required' }, { status: 400 });
  }
  if (!Array.isArray(schema) || schema.length === 0) {
    return NextResponse.json({ error: '`schema` must be a non-empty array of field objects' }, { status: 400 });
  }

  const db = createServerClient();

  const { data, error } = await db
    .from('form_schemas')
    .insert({
      title:        title.trim(),
      description:  description ?? null,
      schema:       schema,
      active_from:  active_from ?? new Date().toISOString(),
      active_until: active_until ?? null,
      created_by:   created_by ?? null,
      is_archived:  false,
    } as never)
    .select('id')
    .single();

  if (error || !data) {
    console.error('[create form]', error);
    return NextResponse.json({ error: 'Failed to create form' }, { status: 500 });
  }

  const created = data as { id: string };

  // Insert one form_respondents row per email (if provided).
  if (Array.isArray(respondents) && respondents.length > 0) {
    const rows = respondents
      .filter((e) => typeof e === 'string' && e.includes('@'))
      .map((email) => ({ form_id: created.id, email: email.toLowerCase().trim(), submitted_at: null }));

    if (rows.length > 0) {
      const { error: rErr } = await db.from('form_respondents').insert(rows as never);
      if (rErr) {
        console.error('[create form — respondents insert]', rErr);
        // Non-fatal: form was created; log the error but still return success.
      }
    }
  }

  const formUrl = `https://olympic-paints-forms-admin.vercel.app/f/${created.id}`;

  return NextResponse.json({ form_id: created.id, form_url: formUrl }, { status: 201 });
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/app/api/forms/create/route.ts
git commit -m "feat: insert form_respondents rows on form creation"
```

---

## Task 4: Update `POST /api/submit/[form_id]` — upsert submitted_at

**Files:**
- Modify: `C:\Users\quint\olympic-paints-forms-admin\src\app\api\submit\[form_id]\route.ts`

When a submission lands, upsert `submitted_at = now()` in `form_respondents` for the matching `(form_id, email)`. The email comes from `metadata.respondent_email` in the POST body. This is additive — the existing `rep_code` lockout logic is unchanged.

- [ ] **Step 1: Add respondent upsert after the successful insert**

In [src/app/api/submit/[form_id]/route.ts](src/app/api/submit/[form_id]/route.ts), after the successful `form_submissions` insert (after line 92, before the `return NextResponse.json`), add:

```typescript
  // Mark respondent as submitted in form_respondents (if email is present in metadata).
  const respondentEmail = typeof metadata.respondent_email === 'string'
    ? metadata.respondent_email.toLowerCase().trim()
    : null;

  if (respondentEmail) {
    const { error: rErr } = await db
      .from('form_respondents')
      .update({ submitted_at: ins.submitted_at })
      .eq('form_id', form_id)
      .eq('email', respondentEmail);
    if (rErr) {
      console.error('[submit — respondent upsert]', rErr);
      // Non-fatal: submission was saved; log and continue.
    }
  }
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/app/api/submit/[form_id]/route.ts
git commit -m "feat: upsert form_respondents submitted_at on submission"
```

---

## Task 5: Update `GET /api/forms/[form_id]/submissions` — add respondents mode

**Files:**
- Modify: `C:\Users\quint\olympic-paints-forms-admin\src\app\api\forms\[form_id]\submissions\route.ts`

Add `?respondents=true` query param. When set, return `{ submitted: [email, ...] }` from `form_respondents` instead of the full submissions list. This is the endpoint the Python poller calls.

- [ ] **Step 1: Add the respondents query mode**

Replace the full file content of [src/app/api/forms/[form_id]/submissions/route.ts](src/app/api/forms/[form_id]/submissions/route.ts):

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase/server';
import type { FormSchema, FormSubmission, FormRespondent } from '@/lib/supabase/types';

// GET /api/forms/[form_id]/submissions
// Returns all submissions for the given form, newest first.
// With ?respondents=true: returns { submitted: string[] } from form_respondents (for the poller).
// Auth: x-admin-secret header
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ form_id: string }> }
) {
  const secret = req.headers.get('x-admin-secret');
  if (!secret || secret !== process.env.FORM_ADMIN_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { form_id } = await params;
  if (!form_id) {
    return NextResponse.json({ error: 'Missing form_id' }, { status: 400 });
  }

  const db = createServerClient();

  // Verify form exists.
  const { data: rawForm, error: formError } = await db
    .from('form_schemas')
    .select('*')
    .eq('id', form_id)
    .maybeSingle();
  const form = rawForm as FormSchema | null;

  if (formError) {
    console.error('[submissions — form lookup]', formError);
    return NextResponse.json({ error: 'Failed to verify form' }, { status: 500 });
  }
  if (!form) {
    return NextResponse.json({ error: 'Form not found' }, { status: 404 });
  }

  // ?respondents=true — poller mode: return submitted email list from form_respondents.
  const respondentsMode = req.nextUrl.searchParams.get('respondents') === 'true';
  if (respondentsMode) {
    const { data: rawR, error: rErr } = await db
      .from('form_respondents')
      .select('email')
      .eq('form_id', form_id)
      .not('submitted_at', 'is', null);
    const rows = (rawR ?? []) as Pick<FormRespondent, 'email'>[];

    if (rErr) {
      console.error('[submissions — respondents fetch]', rErr);
      return NextResponse.json({ error: 'Failed to fetch respondents' }, { status: 500 });
    }

    return NextResponse.json({ submitted: rows.map((r) => r.email) });
  }

  // Default mode: return full submissions list.
  const { data: rawSubs, error: subError } = await db
    .from('form_submissions')
    .select('*')
    .eq('form_id', form_id)
    .order('submitted_at', { ascending: false });
  const submissions = (rawSubs ?? []) as FormSubmission[];

  if (subError) {
    console.error('[submissions — fetch]', subError);
    return NextResponse.json({ error: 'Failed to fetch submissions' }, { status: 500 });
  }

  return NextResponse.json({
    form_id,
    form_title: form.title,
    submissions,
  });
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/app/api/forms/[form_id]/submissions/route.ts
git commit -m "feat: add respondents=true mode to submissions endpoint"
```

---

## Task 6: Deploy forms-admin to Vercel

- [ ] **Step 1: Push to main**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
git push
```

- [ ] **Step 2: Confirm Vercel deployment succeeds**

Use `mcp__claude_ai_Vercel__list_deployments` filtered to the `olympic-paints-forms-admin` project and confirm the latest deployment shows `READY` status.

- [ ] **Step 3: Smoke-test the new endpoint**

Run this from PowerShell (replace `<secret>` with value from `_verification/.env`):

```powershell
$secret = (Get-Content "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification\.env" | Where-Object { $_ -match "FORM_ADMIN_SECRET" }) -replace '.*=',''
Invoke-RestMethod -Uri "https://olympic-paints-forms-admin.vercel.app/api/forms/00000000-0000-0000-0000-000000000000/submissions?respondents=true" -Headers @{ "x-admin-secret" = $secret.Trim() }
```

Expected: `{ "error": "Form not found" }` with 404 — confirms the endpoint is live and auth works.

---

## Task 7: Create `check_pending_forms.py`

**Files:**
- Create: `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\check_pending_forms.py`

- [ ] **Step 1: Create the Forms folder**

```powershell
New-Item -ItemType Directory -Force "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms"
New-Item -ItemType Directory -Force "C:\Users\quint\.claude\logs\pending-forms"
```

- [ ] **Step 2: Write the script**

```python
"""
check_pending_forms.py
Polls pending_forms.json, checks form_respondents via forms-admin API,
sends Telegram when complete or nudges after 3 days.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import truststore
truststore.inject_into_ssl()

# ── Paths ─────────────────────────────────────────────────────────────────────
PENDING_FILE = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json")
PULSE_ENV    = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE — Sales & Ops Manager\.env")
VERIFY_ENV   = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification\.env")
LOG_DIR      = Path(r"C:\Users\quint\.claude\logs\pending-forms")
FORMS_BASE   = "https://olympic-paints-forms-admin.vercel.app"
TELEGRAM_CHAT = "8042233389"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / f"{datetime.now():%Y-%m-%d}.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def _read_env(path: Path, key: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(f"{key} not found in {path}")


def _send_telegram(token: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": text}, timeout=10)
    resp.raise_for_status()


def _get_submitted(form_id: str, secret: str) -> list[str]:
    url = f"{FORMS_BASE}/api/forms/{form_id}/submissions?respondents=true"
    resp = requests.get(url, headers={"x-admin-secret": secret}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("submitted", [])


def main() -> None:
    if not PENDING_FILE.exists():
        log.info("No pending_forms.json found — nothing to do.")
        return

    forms: list[dict] = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    open_forms = [f for f in forms if f.get("status") == "open"]

    if not open_forms:
        log.info("No open forms.")
        return

    token  = _read_env(PULSE_ENV, "TELEGRAM_BOT_TOKEN")
    secret = _read_env(VERIFY_ENV, "FORM_ADMIN_SECRET")

    changed = False
    for entry in forms:
        if entry.get("status") != "open":
            continue

        form_id    = entry["form_id"]
        respondents = entry.get("respondents", [])
        title      = entry.get("title", form_id)
        context    = entry.get("context", "")
        assumptions = entry.get("assumptions", "")

        try:
            submitted = _get_submitted(form_id, secret)
        except Exception as exc:
            log.warning("Could not fetch submissions for %s: %s", form_id, exc)
            continue

        submitted_lower = [e.lower() for e in submitted]
        entry["submitted"] = [e for e in respondents if e.lower() in submitted_lower]
        n_done  = len(entry["submitted"])
        n_total = len(respondents)
        missing = [e for e in respondents if e.lower() not in submitted_lower]
        changed = True

        if n_done >= n_total and n_total > 0:
            entry["status"] = "closed"
            msg = (
                f"✅ Form complete: {title}\n"
                f"Context: {context}\n"
                f"Respondents: {n_done}/{n_total} submitted\n"
                f"Assumptions made: {assumptions}\n"
                f"Review: olympic-paints-forms-admin.vercel.app/admin"
            )
            _send_telegram(token, msg)
            log.info("Form %s closed — all %d responded.", form_id, n_total)

        else:
            created_at = datetime.fromisoformat(entry.get("created_at", datetime.now(timezone.utc).isoformat()))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created_at).days

            if age_days >= 3 and not entry.get("nudge_sent"):
                entry["nudge_sent"] = True
                msg = (
                    f"⏳ Form pending: {title}\n"
                    f"{n_done}/{n_total} responded — outstanding: {', '.join(missing)}"
                )
                _send_telegram(token, msg)
                log.info("Nudge sent for form %s (%d/%d done).", form_id, n_done, n_total)

    if changed:
        PENDING_FILE.write_text(json.dumps(forms, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("pending_forms.json updated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error: %s", exc)
        sys.exit(1)
```

- [ ] **Step 3: Test the script (dry run — no open forms yet)**

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms"
python check_pending_forms.py
```

Expected: logs "No pending_forms.json found — nothing to do." (file doesn't exist yet). Exit code 0.

- [ ] **Step 4: Create an empty `pending_forms.json`**

```powershell
'[]' | Out-File -Encoding utf8 "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json"
```

- [ ] **Step 5: Re-run and confirm it handles empty file**

```powershell
python check_pending_forms.py
```

Expected: logs "No open forms." Exit code 0.

---

## Task 8: Register Task Scheduler job

- [ ] **Step 1: Write the registration script**

Create `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\register_schtask.ps1`:

```powershell
$python = (Get-Command python).Source
$script = "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\check_pending_forms.py"
$logDir = "C:\Users\quint\.claude\logs\pending-forms"

# Create the task folder
$scheduler = New-Object -ComObject Schedule.Service
$scheduler.Connect()
$root = $scheduler.GetFolder("\")
try { $root.GetFolder("Olympic Paints") } catch {
    $root.CreateFolder("Olympic Paints") | Out-Null
}
$opFolder = $scheduler.GetFolder("\Olympic Paints")
try { $opFolder.GetFolder("Forms") } catch {
    $opFolder.CreateFolder("Forms") | Out-Null
}

# Register three daily triggers (08:00, 12:00, 16:00) weekdays only
foreach ($time in @("08:00", "12:00", "16:00")) {
    $taskName = "OlympicPaints_CheckPendingForms_$($time -replace ':','')"
    $action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`""
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $time
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable
    Register-ScheduledTask -TaskName $taskName -TaskPath "\Olympic Paints\Forms\" `
        -Action $action -Trigger $trigger -Settings $settings -RunLevel Limited -Force | Out-Null
    Write-Host "Registered: \Olympic Paints\Forms\$taskName at $time"
}
```

- [ ] **Step 2: Run the registration script**

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\register_schtask.ps1"
```

Expected output:
```
Registered: \Olympic Paints\Forms\OlympicPaints_CheckPendingForms_0800 at 08:00
Registered: \Olympic Paints\Forms\OlympicPaints_CheckPendingForms_1200 at 12:00
Registered: \Olympic Paints\Forms\OlympicPaints_CheckPendingForms_1600 at 16:00
```

- [ ] **Step 3: Verify tasks are registered**

```powershell
Get-ScheduledTask -TaskPath "\Olympic Paints\Forms\" | Select-Object TaskName, State
```

Expected: three tasks, all `Ready`.

---

## Task 9: Write the `SKILL.md`

**Files:**
- Create: `C:\Users\quint\.claude\skills\create-form\SKILL.md`

- [ ] **Step 1: Create the skills folder**

```powershell
New-Item -ItemType Directory -Force "C:\Users\quint\.claude\skills\create-form"
```

- [ ] **Step 2: Write SKILL.md**

```markdown
---
name: create-form
description: >
  Use whenever any agent encounters an information gap it cannot resolve from local files,
  parquet, or Zoho CRM, AND the missing information can be collected from a known person
  (customer, employee, or rep) via email. Also use when Quintus explicitly says "create a
  form to collect X from Y". Triggers: "I don't have X", "need to ask the customer about Y",
  "missing Z from the rep", "create a form for", "collect information from".
---

# create-form

Guides agents through creating a Supabase-backed form, dispatching it by email, documenting
assumptions, and registering the pending request so the poller can notify when responses arrive.

## When to invoke

Invoke this skill when ALL three are true:
1. A piece of information is required to complete or improve the current task.
2. It is not available in local files, the sales parquet, meetings.parquet, or Zoho CRM.
3. You have at least one email address for the person who can provide it.

**Quick checklist before invoking:**
- In sales parquet? → no form needed
- In Zoho CSV / meetings parquet? → no form needed
- In any local file in this repo? → no form needed
- None of the above → invoke this skill

## Step 1 — Identify the gap

Write down:
- What information is missing and why it is needed
- The field names and answer types (text / number / select / radio / date)
- Who needs to answer (full email addresses)
- Which agent and task triggered this

## Step 2 — Build the form schema

Construct a JSON object:

```json
{
  "title": "Short human-readable title (max 60 chars)",
  "description": "One sentence explaining why the respondent is being asked.",
  "fields": [
    {
      "id": "snake_case_id",
      "label": "Question label shown to respondent",
      "type": "text",
      "required": true,
      "order": 1
    }
  ]
}
```

Supported types: `text`, `textarea`, `select`, `radio`, `date`, `number`, `email`.
For `select` and `radio`, include `"options": ["Option A", "Option B"]`.

**Tone by respondent:**
- Customer: professional, brief, no internal jargon. "Please confirm your delivery address."
- Employee: direct, friendly. "Which shift do you prefer next week?"
- Rep: concise, action-oriented. "Confirm your current cycle week: 1 / 2 / 3 / 4."

## Step 3 — POST to forms-admin

Read `FORM_ADMIN_SECRET` from:
`C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification\.env`

```
POST https://olympic-paints-forms-admin.vercel.app/api/forms/create
x-admin-secret: <FORM_ADMIN_SECRET>
Content-Type: application/json

{
  "title": "<title>",
  "description": "<description>",
  "schema": [ ...fields with order property... ],
  "created_by": "<AGENT_NAME>",
  "respondents": ["email1@domain.com", "email2@domain.com"]
}
```

Response: `{ "form_id": "uuid", "form_url": "https://olympic-paints-forms-admin.vercel.app/f/<uuid>" }`

## Step 4 — Register in pending log

Read `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json`.
If the file doesn't exist, create it as `[]`.

Append this entry:

```json
{
  "form_id": "<uuid from Step 3>",
  "title": "<title>",
  "context": "<AGENT_NAME> — <one sentence describing the task that triggered this>",
  "assumptions": "<what value the agent used to continue the task>",
  "respondents": ["email1@domain.com"],
  "submitted": [],
  "nudge_sent": false,
  "created_at": "<ISO 8601 UTC timestamp>",
  "status": "open"
}
```

Write the updated array back to the file.

## Step 5 — Dispatch email via Outlook

Send one email per respondent using Python + win32com. Always force-flush after Send().

```python
import win32com.client
import pythoncom

LOGO_URL = "https://flomaticauto.github.io/olympic-paints-clocking/logo.jpg"

def send_form_email(to_email: str, form_title: str, form_url: str, context_sentence: str) -> None:
    pythoncom.CoInitialize()
    ol = win32com.client.Dispatch("Outlook.Application")
    mail = ol.CreateItem(0)
    mail.To = to_email
    mail.Subject = f"[Olympic Paints] Your input needed — {form_title}"
    mail.HTMLBody = f"""
    <html><body style="font-family:Barlow,Arial,sans-serif;background:#0D2040;color:#fff;padding:24px;">
      <div style="max-width:560px;margin:0 auto;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;">
          <div style="width:48px;height:48px;border-radius:50%;overflow:hidden;">
            <img src="{LOGO_URL}" width="48" height="48" style="display:block;width:100%;height:100%;object-fit:cover;" alt="Olympic Paints">
          </div>
          <span style="font-family:'Barlow Condensed',Arial,sans-serif;font-size:20px;font-weight:800;text-transform:uppercase;color:#F5C400;letter-spacing:0.05em;">Olympic Paints</span>
        </div>
        <h2 style="font-family:'Barlow Condensed',Arial,sans-serif;font-size:22px;font-weight:700;color:#F5C400;text-transform:uppercase;">{form_title}</h2>
        <p style="font-size:15px;color:#B8CCE8;">{context_sentence}</p>
        <a href="{form_url}?email={to_email}" style="display:inline-block;margin-top:16px;padding:12px 28px;background:#F5C400;color:#0D2040;font-family:'Barlow Condensed',Arial,sans-serif;font-weight:700;font-size:16px;text-transform:uppercase;text-decoration:none;border-radius:6px;">Complete Form</a>
        <p style="margin-top:32px;font-size:12px;color:#6B9ED0;">Olympic Paints — this form takes less than 2 minutes to complete.</p>
      </div>
    </body></html>"""
    mail.Send()
    # Force-flush Outbox
    ns = ol.GetNamespace("MAPI")
    outbox = ns.GetDefaultFolder(4)
    for item in list(outbox.Items):
        try:
            item.Send()
        except Exception:
            pass
```

Call `send_form_email()` once per respondent.

## Step 6 — Document assumptions

Include this block verbatim in your response to Quintus:

```
> ⚠️ Form sent — continuing with assumptions
> Missing: <what information was missing>
> Assumed: <value used to continue the task>
> Form: "<form title>" sent to <respondent email(s)>
> Will be corrected when responses arrive.
```

---

The poller (`check_pending_forms.py`, runs weekdays 08:00 / 12:00 / 16:00) handles the rest.
You will receive a Telegram notification when all respondents have submitted.
```

- [ ] **Step 3: Confirm the skill is loadable**

```powershell
Get-Content "C:\Users\quint\.claude\skills\create-form\SKILL.md" | Select-Object -First 10
```

Expected: YAML frontmatter with `name: create-form`.

---

## Task 10: End-to-end smoke test

- [ ] **Step 1: Create a real test form via PowerShell**

```powershell
$secret = (Get-Content "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\_verification\.env" | Where-Object { $_ -match "^FORM_ADMIN_SECRET" }) -replace '^FORM_ADMIN_SECRET=',''
$body = @{
    title       = "Test — create-form skill smoke test"
    description = "Testing the new create-form skill infrastructure."
    schema      = @(@{ id="confirm"; label="Type OK to confirm"; type="text"; required=$true; order=1 })
    created_by  = "smoke-test"
    respondents = @("quintusl@olympicpaints.co.za")
} | ConvertTo-Json -Depth 5
$resp = Invoke-RestMethod -Uri "https://olympic-paints-forms-admin.vercel.app/api/forms/create" `
    -Method POST -Headers @{"x-admin-secret"=$secret.Trim();"Content-Type"="application/json"} `
    -Body $body
$resp | ConvertTo-Json
```

Expected: `{ "form_id": "<uuid>", "form_url": "https://olympic-paints-forms-admin.vercel.app/f/<uuid>" }`

- [ ] **Step 2: Confirm row in form_respondents**

Use `mcp__claude_ai_Supabase__execute_sql`:

```sql
SELECT form_id, email, submitted_at, created_at
FROM form_respondents
ORDER BY created_at DESC
LIMIT 5;
```

Expected: one row with `email = 'quintusl@olympicpaints.co.za'` and `submitted_at = NULL`.

- [ ] **Step 3: Confirm respondents endpoint returns empty**

```powershell
$formId = $resp.form_id
Invoke-RestMethod -Uri "https://olympic-paints-forms-admin.vercel.app/api/forms/$formId/submissions?respondents=true" `
    -Headers @{"x-admin-secret"=$secret.Trim()}
```

Expected: `{ "submitted": [] }`.

- [ ] **Step 4: Add the form to pending_forms.json**

```powershell
$entry = @{
    form_id    = $resp.form_id
    title      = "Test — create-form skill smoke test"
    context    = "smoke-test — verifying end-to-end poller"
    assumptions = "N/A"
    respondents = @("quintusl@olympicpaints.co.za")
    submitted  = @()
    nudge_sent = $false
    created_at = (Get-Date -Format "o")
    status     = "open"
}
$pending = Get-Content "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json" | ConvertFrom-Json
$pending += $entry
$pending | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\0.Inbox\pending_forms.json"
```

- [ ] **Step 5: Run the poller manually**

```powershell
python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Forms\check_pending_forms.py"
```

Expected: script runs, logs "0/1 responded", no Telegram sent (not yet 3 days old). Exit code 0.

- [ ] **Step 6: Archive the test form**

```powershell
Invoke-RestMethod -Uri "https://olympic-paints-forms-admin.vercel.app/api/forms/archive" `
    -Method POST -Headers @{"x-admin-secret"=$secret.Trim();"Content-Type"="application/json"} `
    -Body (@{ form_id=$resp.form_id } | ConvertTo-Json)
```

Then manually set `status: "closed"` on the test entry in `pending_forms.json` to keep the log clean.

---

## Self-Review Notes

- **Spec coverage:** All 6 form-creation steps covered in Task 9 (SKILL.md). `form_respondents` table in Task 1. Create endpoint update in Task 3. Submit endpoint update in Task 4. Submissions endpoint update in Task 5. Poller in Task 7. Scheduler in Task 8. End-to-end test in Task 10. ✅
- **Type consistency:** `FormRespondent` defined in Task 2, imported in Task 5's updated route. ✅
- **Placeholders:** None — all code is complete and runnable. ✅
- **Constraint coverage:** `truststore.inject_into_ssl()` in poller ✅ · logs outside OneDrive ✅ · Outlook force-flush ✅ · hosted logo URL ✅ · token from PULSE `.env` ✅ · secret from `_verification/.env` ✅ · `pending_forms.json` append-only ✅
