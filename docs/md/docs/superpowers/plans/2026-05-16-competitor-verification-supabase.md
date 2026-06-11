# Competitor Product Verification — Supabase Forms Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Supersedes:** `2026-05-16-competitor-verification-jotforms.md`. Decision (2026-05-16): skip JotForm entirely and build on the existing `olympic-paints-forms-admin` Supabase stack so submissions land in our own database, joinable to the sales parquet, with no external service in the loop.

**Goal:** Stand up 15 category-filtered, self-hosted verification forms (5 competitors × 3 categories) on the existing Supabase + Next.js stack, so reps can confirm or correct every Olympic ↔ competitor product matchup. Dispatch on a 3-day email cadence. Results aggregate into an internal Excel report.

**Architecture:** Two existing Python scripts (`categorise_skus.py`, `extract_matchups.py` — already specified in the JotForm plan, T1/T2) produce JSON data. A new Python builder posts each form to the Supabase admin API. The existing Next.js app gets two new routes: `/f/[form_id]` for public render and `/api/submit/[form_id]` for submission. The existing email dispatcher (`send_verification_emails.py`) is adapted to template Supabase URLs. A new Python aggregator pulls results via the admin API and writes Excel.

**Tech Stack:** Python 3 · openpyxl · requests · win32com.client · Next.js 15 · React 19 · Supabase (existing project `nssufmvpdtzhybcqispv`) · Outlook (local)

**Repo notes:**
- Forms repo: `C:\Users\quint\olympic-paints-forms-admin` (git, deploys to Vercel)
- Olympic Paints workspace: `c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints` (NOT a git repo; replace "commit" with "save file + append line to changelog")
- Two changelogs: `jotform_verification/CHANGELOG.md` (workspace side) and standard git commits (forms-admin side)

**Locked decisions (from architecture conversation):**
- Submit-once lockout, identified by `rep_code` URL param checked server-side against `form_submissions.metadata->>'rep_code'`
- URL shape: `/f/[form_id]?rep=<code>&email=<addr>&competitor=<slug>&category=<cat>`
- No SQL migration — rely on jsonb to accept the extended `FormField` shape (`type: 'html'`, optional `default`)
- Skip JotForm entirely; the JotForm plan is superseded

---

## File structure

Reuse the existing folder from the JotForm plan, rename `jotform_verification/` → `verification_forms/`:

```
2.Areas/1. Sales/7. Competitor information/verification_forms/
├── categorise_skus.py              # unchanged from JotForm plan T1
├── extract_matchups.py             # unchanged from JotForm plan T2
├── build_supabase_forms.py         # NEW — posts forms to /api/forms/create
├── send_verification_emails.py     # adapted — uses supabase_form_ids.json
├── pull_verification_results.py    # NEW — aggregates submissions to Excel
├── CHANGELOG.md
├── config/
│   ├── category_mapping.json       # unchanged from JotForm plan
│   └── rep_emails.json             # unchanged from JotForm plan
├── output/
│   ├── olympic_skus_<cat>.json                # 3 files
│   ├── competitor_matchups_<brand>_<cat>.json # 15 files
│   ├── supabase_form_ids.json                 # NEW — { competitor: { category: form_id } }
│   ├── dispatch_log.json
│   └── verification_results.xlsx              # NEW — aggregated rep responses
└── templates/
    └── daily_email.html
```

Forms-admin repo gets two new files:
```
olympic-paints-forms-admin/src/
├── app/
│   ├── f/[form_id]/page.tsx                   # NEW — public render
│   └── api/submit/[form_id]/route.ts          # NEW — public submission
└── components/
    └── FormRenderer.tsx                       # NEW — client component
```

---

## Pre-flight constants

```python
# Python (verification_forms scripts)
from pathlib import Path

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
VF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "verification_forms"
OUTPUT_DIR = VF_DIR / "output"
CONFIG_DIR = VF_DIR / "config"
TEMPLATES_DIR = VF_DIR / "templates"

# Forms admin API
FORMS_ADMIN_BASE = "https://olympic-paints-forms-admin.vercel.app"
# FORM_ADMIN_SECRET is loaded from env / .env in each script (NEVER hardcoded)

COMPETITORS = [
    ("africa_paints",  "Africa Paints"),
    ("anetic",         "Anetic"),
    ("crest",          "Crest"),
    ("excelsior",      "Excelsior"),
    ("golden_choice",  "Golden Choice"),
]
CATEGORIES = ["enamel", "pva", "waterproofing"]
```

---

## Task 0: Prerequisite — Tasks 1 & 2 from JotForm plan

The categoriser and extractor are unchanged from the JotForm plan. Either copy them over or run them in place under the renamed folder. **Do not re-specify them here.** Confirm both have run and the 3 SKU JSONs + 15 matchup JSONs are present in `verification_forms/output/`.

- [ ] **Step 0.1: Run categoriser** — produces `olympic_skus_<cat>.json` × 3
- [ ] **Step 0.2: Run extractor** — produces `competitor_matchups_<slug>_<cat>.json` × 15
- [ ] **Step 0.3: Spot-check Pick & Save is in `olympic_skus_enamel.json` (load-bearing per `feedback_pick_n_save_enamel_match`)**

Do not proceed past Task 0 with unmapped SKUs or empty matchup files.

---

## Task 1: Extend `FormField` type and add public schema fetcher

**Files:**
- Edit: `olympic-paints-forms-admin/src/lib/supabase/types.ts`
- Create: `olympic-paints-forms-admin/src/app/api/forms/public/[form_id]/route.ts`

The existing `FormField` type lacks two things competitor verification needs: an `html` field type for static section headers, and a `default` value for pre-selecting dropdowns. We extend the TypeScript type only — Supabase jsonb accepts the new shape without migration.

- [ ] **Step 1.1: Extend `FieldType` and `FormField`**

In `src/lib/supabase/types.ts`:

```typescript
export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'email'
  | 'tel'
  | 'select'
  | 'radio'
  | 'checkbox'
  | 'date'
  | 'html'        // NEW — static content rendered between inputs (section headers, intro text)
  | 'hidden';     // NEW — carries URL prefill into submission.data without rendering

export interface FormField {
  id:          string;
  type:        FieldType;
  label:       string;
  placeholder?: string;
  required?:   boolean;
  options?:    string[];     // for select / radio / checkbox
  default?:    string;       // NEW — pre-selected value (select/radio) or pre-filled text
  html?:       string;       // NEW — rendered when type === 'html' (sanitized — see Step 3.4)
  order:       number;
}
```

- [ ] **Step 1.2: Create public schema fetcher**

The public render page needs to read the schema without an admin secret. Create `src/app/api/forms/public/[form_id]/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase/server';
import type { FormSchema } from '@/lib/supabase/types';

// GET /api/forms/public/[form_id]
// PUBLIC endpoint — returns schema only (NO submissions, NO admin data).
// Only returns the form if it's not archived and within active window.
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ form_id: string }> }
) {
  const { form_id } = await params;
  if (!form_id) {
    return NextResponse.json({ error: 'Missing form_id' }, { status: 400 });
  }

  const db = createServerClient();
  const { data: raw, error } = await db
    .from('form_schemas')
    .select('id,title,description,schema,active_from,active_until,is_archived')
    .eq('id', form_id)
    .maybeSingle();
  const form = raw as Partial<FormSchema> | null;

  if (error) {
    console.error('[public form]', error);
    return NextResponse.json({ error: 'Failed to load form' }, { status: 500 });
  }
  if (!form) {
    return NextResponse.json({ error: 'Form not found' }, { status: 404 });
  }
  if (form.is_archived) {
    return NextResponse.json({ error: 'Form archived' }, { status: 410 });
  }
  const now = new Date();
  if (form.active_from && new Date(form.active_from) > now) {
    return NextResponse.json({ error: 'Form not yet active' }, { status: 403 });
  }
  if (form.active_until && new Date(form.active_until) < now) {
    return NextResponse.json({ error: 'Form closed' }, { status: 410 });
  }

  return NextResponse.json({
    id:          form.id,
    title:       form.title,
    description: form.description,
    schema:      form.schema,
  });
}
```

- [ ] **Step 1.3: Commit (forms-admin repo)**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
git add src/lib/supabase/types.ts src/app/api/forms/public
git commit -m "feat: extend FormField with html/hidden types + public schema endpoint"
```

Do NOT push yet — wait until Task 3 is done so the deploy includes the render page.

---

## Task 2: Public submission endpoint

**Files:**
- Create: `olympic-paints-forms-admin/src/app/api/submit/[form_id]/route.ts`

This is the load-bearing public endpoint. No auth header (it's open to the internet by URL knowledge), but it enforces:
1. Form exists, not archived, within active window
2. `rep_code` is present in the body
3. No existing submission for `(form_id, rep_code)` — submit-once lockout

- [ ] **Step 2.1: Write the route**

`src/app/api/submit/[form_id]/route.ts`:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase/server';
import type { FormSchema, FormSubmission } from '@/lib/supabase/types';

// POST /api/submit/[form_id]
// PUBLIC endpoint — no admin auth.
// Body: { data: Record<string, unknown>, metadata: { rep_code, rep_email, competitor, category } }
// Enforces submit-once per (form_id, rep_code).
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ form_id: string }> }
) {
  const { form_id } = await params;
  if (!form_id) {
    return NextResponse.json({ error: 'Missing form_id' }, { status: 400 });
  }

  let body: { data?: Record<string, unknown>; metadata?: Record<string, unknown> };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const data = body.data;
  const metadata = body.metadata ?? {};
  const repCode = typeof metadata.rep_code === 'string' ? metadata.rep_code.trim() : '';

  if (!data || typeof data !== 'object') {
    return NextResponse.json({ error: '`data` object required' }, { status: 400 });
  }
  if (!repCode) {
    return NextResponse.json({ error: '`metadata.rep_code` required' }, { status: 400 });
  }

  const db = createServerClient();

  // 1. Form must exist, not archived, within window
  const { data: rawForm, error: formError } = await db
    .from('form_schemas')
    .select('id,is_archived,active_from,active_until')
    .eq('id', form_id)
    .maybeSingle();
  const form = rawForm as Pick<FormSchema, 'id' | 'is_archived' | 'active_from' | 'active_until'> | null;

  if (formError || !form) {
    return NextResponse.json({ error: 'Form not found' }, { status: 404 });
  }
  if (form.is_archived) {
    return NextResponse.json({ error: 'Form archived' }, { status: 410 });
  }
  const now = new Date();
  if (form.active_until && new Date(form.active_until) < now) {
    return NextResponse.json({ error: 'Form closed' }, { status: 410 });
  }
  if (form.active_from && new Date(form.active_from) > now) {
    return NextResponse.json({ error: 'Form not yet active' }, { status: 403 });
  }

  // 2. Lockout — already submitted by this rep?
  // We query the JSON metadata column with a ->> selector.
  const { data: rawExisting, error: existsError } = await db
    .from('form_submissions')
    .select('id')
    .eq('form_id', form_id)
    .filter('metadata->>rep_code', 'eq', repCode)
    .limit(1);
  const existing = (rawExisting ?? []) as { id: string }[];

  if (existsError) {
    console.error('[submit — lockout check]', existsError);
    return NextResponse.json({ error: 'Submission check failed' }, { status: 500 });
  }
  if (existing.length > 0) {
    return NextResponse.json({ error: 'Already submitted', code: 'DUPLICATE' }, { status: 409 });
  }

  // 3. Insert
  const submittedBy = typeof metadata.rep_email === 'string' ? metadata.rep_email : null;
  const insertRow: Omit<FormSubmission, 'id' | 'submitted_at'> = {
    form_id,
    submitted_by: submittedBy,
    data,
    metadata,
  };

  const { data: rawIns, error: insError } = await db
    .from('form_submissions')
    .insert(insertRow as never)
    .select('id,submitted_at')
    .single();

  if (insError || !rawIns) {
    console.error('[submit — insert]', insError);
    return NextResponse.json({ error: 'Save failed' }, { status: 500 });
  }

  const ins = rawIns as { id: string; submitted_at: string };
  return NextResponse.json({ submission_id: ins.id, submitted_at: ins.submitted_at }, { status: 201 });
}
```

- [ ] **Step 2.2: Commit**

```bash
git add src/app/api/submit
git commit -m "feat: public submission endpoint with submit-once lockout"
```

Still do NOT push.

---

## Task 3: Public form renderer

**Files:**
- Create: `olympic-paints-forms-admin/src/app/f/[form_id]/page.tsx`
- Create: `olympic-paints-forms-admin/src/components/FormRenderer.tsx`
- Create: `olympic-paints-forms-admin/src/app/f/[form_id]/already-submitted.tsx` (or inline component)
- Create: `olympic-paints-forms-admin/src/app/f/layout.tsx` (optional — public layout without admin chrome)

- [ ] **Step 3.1: Page (server component, reads schema + searchParams)**

`src/app/f/[form_id]/page.tsx`:

```tsx
import { createServerClient } from '@/lib/supabase/server';
import type { FormSchema } from '@/lib/supabase/types';
import FormRenderer from '@/components/FormRenderer';

interface PageProps {
  params: Promise<{ form_id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function PublicFormPage({ params, searchParams }: PageProps) {
  const { form_id } = await params;
  const sp = await searchParams;

  const db = createServerClient();
  const { data: raw } = await db
    .from('form_schemas')
    .select('id,title,description,schema,active_from,active_until,is_archived')
    .eq('id', form_id)
    .maybeSingle();
  const form = raw as FormSchema | null;

  if (!form) {
    return <NotFound title="Form not found" message="This link may be wrong or the form may have been removed." />;
  }
  if (form.is_archived) {
    return <NotFound title="Form archived" message="This form is no longer accepting responses." />;
  }
  const now = new Date();
  if (form.active_until && new Date(form.active_until) < now) {
    return <NotFound title="Form closed" message="The deadline for this verification has passed." />;
  }

  // URL prefill — strings only, drop arrays
  const prefill: Record<string, string> = {};
  for (const [k, v] of Object.entries(sp)) {
    if (typeof v === 'string') prefill[k] = v;
  }

  // If we have a rep_code, check lockout server-side and render the "already done" state
  if (prefill.rep) {
    const { data: existing } = await db
      .from('form_submissions')
      .select('id,submitted_at')
      .eq('form_id', form_id)
      .filter('metadata->>rep_code', 'eq', prefill.rep)
      .limit(1);
    if ((existing ?? []).length > 0) {
      return <AlreadySubmitted submittedAt={(existing as { submitted_at: string }[])[0].submitted_at} />;
    }
  }

  return (
    <FormRenderer
      formId={form.id}
      title={form.title}
      description={form.description}
      schema={form.schema}
      prefill={prefill}
    />
  );
}

function NotFound({ title, message }: { title: string; message: string }) {
  return (
    <main style={{ padding: 32, textAlign: 'center', color: '#fff', background: '#0D2040', minHeight: '100vh' }}>
      <h1 style={{ fontFamily: 'Barlow Condensed, sans-serif', color: '#F5C400', textTransform: 'uppercase' }}>{title}</h1>
      <p style={{ color: '#B8CCE8' }}>{message}</p>
    </main>
  );
}

function AlreadySubmitted({ submittedAt }: { submittedAt: string }) {
  const when = new Date(submittedAt).toLocaleString('en-ZA', { dateStyle: 'medium', timeStyle: 'short' });
  return (
    <main style={{ padding: 32, textAlign: 'center', color: '#fff', background: '#0D2040', minHeight: '100vh' }}>
      <h1 style={{ fontFamily: 'Barlow Condensed, sans-serif', color: '#F5C400', textTransform: 'uppercase' }}>Thanks — already submitted</h1>
      <p style={{ color: '#B8CCE8' }}>You completed this verification on {when}.</p>
      <p style={{ color: '#6B9ED0', fontSize: 14, marginTop: 24 }}>Need to correct an answer? Reply to the email and we&apos;ll edit it manually.</p>
    </main>
  );
}
```

- [ ] **Step 3.2: Client renderer**

`src/components/FormRenderer.tsx`:

```tsx
'use client';
import { useState, FormEvent } from 'react';
import type { FormField } from '@/lib/supabase/types';

interface Props {
  formId:      string;
  title:       string;
  description: string | null;
  schema:      FormField[];
  prefill:     Record<string, string>;  // { rep, email, competitor, category, ... }
}

export default function FormRenderer({ formId, title, description, schema, prefill }: Props) {
  const initial: Record<string, unknown> = {};
  for (const f of schema) {
    if (f.type === 'html') continue;
    if (f.type === 'hidden') {
      // hidden fields take their value from prefill if matching id, else from default
      initial[f.id] = prefill[f.id] ?? f.default ?? '';
    } else {
      initial[f.id] = f.default ?? (f.type === 'checkbox' ? [] : '');
    }
  }
  const [values, setValues] = useState<Record<string, unknown>>(initial);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ordered = [...schema].sort((a, b) => a.order - b.order);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);

    const metadata = {
      rep_code:   prefill.rep ?? '',
      rep_email:  prefill.email ?? '',
      competitor: prefill.competitor ?? '',
      category:   prefill.category ?? '',
      submitted_from_ua: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    };

    try {
      const res = await fetch(`/api/submit/${formId}`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ data: values, metadata }),
      });
      const j = await res.json();
      if (!res.ok) {
        if (j.code === 'DUPLICATE') {
          setError('You already submitted this form. Refresh to see the confirmation page.');
        } else {
          setError(j.error ?? 'Submission failed');
        }
        setBusy(false);
        return;
      }
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
      setBusy(false);
    }
  }

  if (done) {
    return (
      <main className="oly-public">
        <div className="card">
          <h1>Thanks!</h1>
          <p>Your responses have been recorded. You can close this tab.</p>
        </div>
        <style jsx>{styles}</style>
      </main>
    );
  }

  return (
    <main className="oly-public">
      <form onSubmit={onSubmit} className="card">
        <h1>{title}</h1>
        {description && <p className="desc">{description}</p>}
        {ordered.map((f) => (
          <Field key={f.id} field={f} value={values[f.id]} onChange={(v) => setValues({ ...values, [f.id]: v })} />
        ))}
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy} className="submit">
          {busy ? 'Submitting…' : 'Submit verification'}
        </button>
      </form>
      <style jsx>{styles}</style>
    </main>
  );
}

function Field({ field, value, onChange }: { field: FormField; value: unknown; onChange: (v: unknown) => void }) {
  if (field.type === 'html') {
    return <div className="html-block" dangerouslySetInnerHTML={{ __html: field.html ?? '' }} />;
  }
  if (field.type === 'hidden') {
    return null;
  }

  const v = typeof value === 'string' ? value : '';

  if (field.type === 'select') {
    return (
      <label className="field">
        <span className="label">{field.label}{field.required && ' *'}</span>
        <select
          value={v}
          onChange={(e) => onChange(e.target.value)}
          required={field.required}
        >
          <option value="">— select —</option>
          {(field.options ?? []).map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === 'radio') {
    return (
      <fieldset className="field">
        <legend className="label">{field.label}{field.required && ' *'}</legend>
        {(field.options ?? []).map((opt) => (
          <label key={opt} className="radio-row">
            <input
              type="radio"
              name={field.id}
              value={opt}
              checked={v === opt}
              onChange={(e) => onChange(e.target.value)}
              required={field.required}
            />
            <span>{opt}</span>
          </label>
        ))}
      </fieldset>
    );
  }

  if (field.type === 'textarea') {
    return (
      <label className="field">
        <span className="label">{field.label}{field.required && ' *'}</span>
        <textarea
          value={v}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          required={field.required}
          rows={3}
        />
      </label>
    );
  }

  return (
    <label className="field">
      <span className="label">{field.label}{field.required && ' *'}</span>
      <input
        type={field.type === 'email' ? 'email' : field.type === 'tel' ? 'tel' : field.type === 'number' ? 'number' : 'text'}
        value={v}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder}
        required={field.required}
      />
    </label>
  );
}

const styles = `
  .oly-public { background:#0D2040; color:#fff; font-family:'Barlow',sans-serif; min-height:100vh; padding:24px 16px 64px; }
  .card { max-width:680px; margin:0 auto; background:#1A3D6E; border-radius:12px; padding:24px; box-shadow:0 10px 30px rgba(0,0,0,0.5); }
  h1 { font-family:'Barlow Condensed',sans-serif; font-weight:900; color:#F5C400; text-transform:uppercase; font-size:28px; margin:0 0 8px; }
  .desc { color:#B8CCE8; margin:0 0 24px; line-height:1.4; }
  .field { display:block; margin:16px 0; }
  .label { display:block; font-family:'Barlow Condensed',sans-serif; font-weight:700; color:#F5C400; text-transform:uppercase; letter-spacing:0.08em; font-size:11px; margin-bottom:6px; }
  input, select, textarea { width:100%; box-sizing:border-box; padding:12px 14px; min-height:44px; font-size:16px; font-family:'Barlow',sans-serif; background:#0D2040; color:#fff; border:1px solid rgba(107,158,208,0.35); border-radius:8px; }
  input:focus, select:focus, textarea:focus { outline:2px solid #F5C400; outline-offset:2px; }
  textarea { min-height:80px; resize:vertical; }
  .html-block { padding:12px 14px; background:rgba(245,196,0,0.08); border-left:4px solid #F5C400; border-radius:8px; margin:16px 0; }
  .html-block strong { color:#F5C400; }
  .radio-row { display:flex; align-items:center; gap:10px; padding:10px 0; min-height:44px; }
  .radio-row input { width:auto; min-height:auto; }
  fieldset { border:0; padding:0; margin:16px 0; }
  legend { padding:0; }
  .submit { width:100%; padding:16px; min-height:52px; background:#F5C400; color:#0D2040; border:0; border-radius:8px; font-family:'Barlow Condensed',sans-serif; font-weight:900; text-transform:uppercase; letter-spacing:0.08em; font-size:16px; cursor:pointer; margin-top:24px; }
  .submit:disabled { opacity:0.5; cursor:not-allowed; }
  .error { color:#FDDCDC; background:rgba(232,96,96,0.14); border:1px solid rgba(232,96,96,0.35); padding:12px; border-radius:8px; margin-top:16px; }
  @media (max-width:480px) { h1 { font-size:24px; } .card { padding:16px; } }
`;
```

- [ ] **Step 3.3: Public layout without admin chrome**

If the root layout includes the admin shell (sidebar/topbar), you'll see admin UI on public pages. Confirm by reading `src/app/layout.tsx`. If it does, create `src/app/f/layout.tsx` that returns `{children}` with no chrome.

- [ ] **Step 3.4: Sanitize the `html` field**

The `html` field renders raw HTML via `dangerouslySetInnerHTML`. Forms are admin-authored (no public input), so XSS risk is low — but defence in depth. Install `isomorphic-dompurify` and sanitize:

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npm install isomorphic-dompurify
```

Update `FormRenderer.tsx`:
```typescript
import DOMPurify from 'isomorphic-dompurify';
// ...
return <div className="html-block" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(field.html ?? '') }} />;
```

- [ ] **Step 3.5: Commit & deploy**

```bash
git add src/app/f src/components/FormRenderer.tsx package.json package-lock.json
git commit -m "feat: public form renderer at /f/[form_id] with submit-once lockout"
git push origin main
```

Vercel auto-deploys. Wait for green build (~90s).

- [ ] **Step 3.6: Smoke-test in production with a throwaway form**

Build a 2-field test form via the admin UI at `/admin/forms` (or via curl to `/api/forms/create`). Visit `https://olympic-paints-forms-admin.vercel.app/f/<id>?rep=QL_TEST` and submit. Then refresh — the page should show "already submitted". Delete the test form afterwards (or archive).

- [ ] **Step 3.7: Commit changelog**

Append to `olympic-paints-forms-admin` README or CHANGELOG and to workspace `CHANGELOG.md`:
```
2026-05-16  T1–T3 done — Public form renderer live at /f/[form_id]. Submit-once enforced server-side by rep_code lookup.
```

---

## Task 4: Python builder — POST forms to Supabase

**Files:**
- Create: `verification_forms/build_supabase_forms.py`
- Create: `verification_forms/output/supabase_form_ids.json`

- [ ] **Step 4.1: Load FORM_ADMIN_SECRET**

The admin secret currently equals `ADMIN_SECRET`. Source of truth = Vercel env vars. For local script use, mirror it into a `.env` next to the script:

```
# verification_forms/.env  (gitignored / never committed)
FORM_ADMIN_SECRET=<paste value from Vercel>
```

If you haven't already, pull it with the Vercel CLI:
```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx vercel env pull .env.local
# copy FORM_ADMIN_SECRET line into verification_forms/.env
```

- [ ] **Step 4.2: Write the builder**

```python
"""
Build 15 Supabase forms by POSTing schemas to /api/forms/create.
Reads:  output/olympic_skus_<cat>.json + output/competitor_matchups_<slug>_<cat>.json
Writes: output/supabase_form_ids.json

Re-running this script CREATES NEW FORMS each time. To re-build a specific form,
either: (a) archive the old one and run, or (b) delete the (competitor, category)
entry from supabase_form_ids.json before running (only that pair will rebuild).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests
import truststore  # per feedback_python_truststore_for_https

truststore.inject_into_ssl()

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
VF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "verification_forms"
OUTPUT_DIR = VF_DIR / "output"

FORMS_ADMIN_BASE = "https://olympic-paints-forms-admin.vercel.app"

COMPETITORS = [
    ("africa_paints",  "Africa Paints"),
    ("anetic",         "Anetic"),
    ("crest",          "Crest"),
    ("excelsior",      "Excelsior"),
    ("golden_choice",  "Golden Choice"),
]
CATEGORIES = ["enamel", "pva", "waterproofing"]

def load_secret() -> str:
    env_path = VF_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("FORM_ADMIN_SECRET="):
                return line.split("=", 1)[1].strip()
    val = os.environ.get("FORM_ADMIN_SECRET")
    if val:
        return val
    sys.exit("FORM_ADMIN_SECRET not found in verification_forms/.env or environment")

def build_schema(matchups: list[dict], olympic_skus: list[dict], competitor_label: str, category: str) -> list[dict]:
    """
    Builds a flat FormField[] with one group of fields per matchup row.

    Group convention (flat IDs, prefix-grouped):
      row_{n}_header     html section header
      row_{n}_match      select  (Olympic SKU dropdown)
      row_{n}_confidence radio   (Strong / Acceptable / Wrong)
      row_{n}_notes      textarea
    """
    # SKU dropdown options — same for every row in this category
    sku_options = [f"{sku['code']} — {sku['name']}" for sku in olympic_skus]

    fields: list[dict] = []
    order = 0

    # Intro HTML
    fields.append({
        "id": "intro",
        "type": "html",
        "label": "",
        "html": (
            f"<strong>{competitor_label} — {category.title()} matchup verification.</strong> "
            f"For each {competitor_label} product below, confirm the Olympic match shown is correct. "
            f"If wrong, choose the right one or add a note."
        ),
        "order": order,
    })
    order += 1

    for n, m in enumerate(matchups, start=1):
        # Header
        comp_label_full = f"{m['competitor_product']} · {m['pack_size']} · {m['competitor_price']}".strip(" ·")
        fields.append({
            "id": f"row_{n}_header",
            "type": "html",
            "label": "",
            "html": f"<strong>Line {n}: {comp_label_full}</strong>",
            "order": order,
        })
        order += 1

        # Current match label as default
        default = ""
        if m.get("current_olympic_match_code") and m.get("current_olympic_match_name"):
            default = f"{m['current_olympic_match_code']} — {m['current_olympic_match_name']}"

        fields.append({
            "id": f"row_{n}_match",
            "type": "select",
            "label": "Correct Olympic match",
            "options": sku_options,
            "default": default,
            "required": True,
            "order": order,
        })
        order += 1

        fields.append({
            "id": f"row_{n}_confidence",
            "type": "radio",
            "label": "Confidence",
            "options": ["Strong match", "Acceptable", "Wrong — see notes"],
            "default": "Strong match",
            "required": True,
            "order": order,
        })
        order += 1

        fields.append({
            "id": f"row_{n}_notes",
            "type": "textarea",
            "label": "Notes (optional)",
            "placeholder": "Anything to flag — chemistry, pricing, customer feedback…",
            "order": order,
        })
        order += 1

    return fields

def create_form(secret: str, title: str, description: str, schema: list[dict]) -> str:
    resp = requests.post(
        f"{FORMS_ADMIN_BASE}/api/forms/create",
        headers={"x-admin-secret": secret, "content-type": "application/json"},
        json={
            "title": title,
            "description": description,
            "schema": schema,
            "created_by": "competitor_verification_builder",
        },
        timeout=30,
    )
    if resp.status_code != 201:
        raise RuntimeError(f"create_form failed: {resp.status_code} {resp.text}")
    return resp.json()["form_id"]

def main():
    secret = load_secret()

    # Load existing URL map if present (resume support)
    map_path = OUTPUT_DIR / "supabase_form_ids.json"
    if map_path.exists():
        urls = json.loads(map_path.read_text(encoding="utf-8"))
    else:
        urls = {slug: {cat: None for cat in CATEGORIES} for slug, _ in COMPETITORS}

    for slug, label in COMPETITORS:
        sku_paths = {cat: OUTPUT_DIR / f"olympic_skus_{cat}.json" for cat in CATEGORIES}
        for cat in CATEGORIES:
            if urls.get(slug, {}).get(cat):
                print(f"  skip   {label:15s} {cat:14s} (already built: {urls[slug][cat]})")
                continue

            matchups_path = OUTPUT_DIR / f"competitor_matchups_{slug}_{cat}.json"
            if not matchups_path.exists() or not sku_paths[cat].exists():
                print(f"  miss   {label:15s} {cat:14s} (missing input JSON)")
                continue

            matchups = json.loads(matchups_path.read_text(encoding="utf-8"))
            olympic_skus = json.loads(sku_paths[cat].read_text(encoding="utf-8"))

            if not matchups:
                print(f"  empty  {label:15s} {cat:14s} (0 matchups — skipping)")
                continue

            schema = build_schema(matchups, olympic_skus, label, cat)
            title = f"Olympic vs {label} — {cat.title()} Matchup Verification"
            description = f"15-form verification rollout, {label} {cat}. {len(matchups)} matchup lines."

            try:
                form_id = create_form(secret, title, description, schema)
            except Exception as e:
                print(f"  FAIL   {label:15s} {cat:14s} — {e}")
                continue

            urls.setdefault(slug, {})[cat] = form_id
            map_path.write_text(json.dumps(urls, indent=2), encoding="utf-8")
            print(f"  built  {label:15s} {cat:14s} -> {form_id}")
            time.sleep(0.5)  # be nice to Vercel

    # Final tally
    built = sum(1 for cats in urls.values() for v in cats.values() if v)
    print(f"\nForms built: {built} / 15")
    if built < 15:
        missing = [(c, k) for c, cats in urls.items() for k, v in cats.items() if not v]
        for c, k in missing:
            print(f"  MISSING: {c} / {k}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4.3: Run the builder**

```bash
cd "c:/Users/quint/OneDrive/1.Projects/1.Olympic Paints/2.Areas/1. Sales/7. Competitor information/verification_forms"
python build_supabase_forms.py
```

Expected: `Forms built: 15 / 15`.

- [ ] **Step 4.4: Manual verify one form**

Pick one form_id from `output/supabase_form_ids.json`. Visit `https://olympic-paints-forms-admin.vercel.app/f/<id>?rep=QL&email=quintusl@olympicpaints.co.za`. Confirm:
- Title and intro render
- Each matchup line has a header + dropdown + radio + notes
- Dropdown has a default pre-selected (the current Olympic match)
- Dropdown contains ONLY category-appropriate SKUs (no PVAs in an enamel form)
- Mobile view works (test on phone)

- [ ] **Step 4.5: Log to changelog**

```
2026-05-16  T4 done — 15 Supabase forms built. URL map at output/supabase_form_ids.json.
```

---

## Task 5: Adapt email dispatcher

**Files:**
- Edit: `verification_forms/send_verification_emails.py`
- Reuse: `verification_forms/templates/daily_email.html` (unchanged from JotForm plan T6)
- Reuse: `verification_forms/config/rep_emails.json` (unchanged from JotForm plan T5)

- [ ] **Step 5.1: Update URL builder to use Supabase form IDs**

Copy the JotForm-plan dispatcher (T7.1) into the Supabase folder. Change two things:

1. URL map source:
```python
# OLD: jotform_urls = json.loads((OUTPUT_DIR / "jotform_urls.json").read_text())
urls = json.loads((OUTPUT_DIR / "supabase_form_ids.json").read_text())
```

2. URL builder:
```python
FORMS_BASE = "https://olympic-paints-forms-admin.vercel.app/f"

def build_link(form_id: str, rep_code: str, rep_email: str, competitor: str, category: str) -> str:
    params = urllib.parse.urlencode({
        "rep":        rep_code,
        "email":      rep_email,
        "competitor": competitor,
        "category":   category,
    })
    return f"{FORMS_BASE}/{form_id}?{params}"

def render_links_html(urls: dict, category: str, rep_code: str, rep_email: str) -> str:
    parts = []
    for slug, label in COMPETITORS:
        form_id = urls.get(slug, {}).get(category)
        if not form_id:
            continue
        full = build_link(form_id, rep_code, rep_email, slug, category)
        parts.append(
            f'<a class="link-row" href="{full}">'
            f'<strong>{label}</strong><br>'
            f'<span style="font-size:13px;color:#B8CCE8;">Open {label} {category} verification form &rarr;</span>'
            f'</a>'
        )
    return "\n".join(parts)
```

Everything else (Outlook force-flush per [[feedback_outlook_send_flush]], navy template, Telegram notify) stays identical.

- [ ] **Step 5.2: Dry-run to Quintus only**

```bash
python send_verification_emails.py --day enamel --dry-run
```

Verify the email arrives in Quintus's inbox, then click ONE link:
- Page loads with the right title
- URL params are visible in the address bar
- Fill in 1–2 fields and submit → confirmation page shows
- Refresh same URL → "already submitted" page shows

If "already submitted" doesn't show on refresh, the lockout query is wrong — debug `metadata->>rep_code` filter before going live.

- [ ] **Step 5.3: Log to changelog**

```
2026-05-16  T5 done — dispatcher adapted to Supabase URLs; dry-run verified end-to-end.
```

---

## Task 6: Aggregator — pull results into Excel

**Files:**
- Create: `verification_forms/pull_verification_results.py`
- Create: `verification_forms/output/verification_results.xlsx`

This is what JotForm couldn't give you cheaply: a single Excel with one tab per competitor, joining rep responses back to the source matchups so disagreements are visually obvious.

- [ ] **Step 6.1: Write the aggregator**

```python
"""
Pull all submissions for the 15 competitor verification forms, write one Excel
with one tab per competitor (3 categories stacked in each tab).

Highlights any row where any rep's match disagrees with the workbook's current
Olympic match.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl
import requests
import truststore
from openpyxl.styles import Font, PatternFill, Alignment

truststore.inject_into_ssl()

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
VF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "verification_forms"
OUTPUT_DIR = VF_DIR / "output"
FORMS_ADMIN_BASE = "https://olympic-paints-forms-admin.vercel.app"

COMPETITORS = [
    ("africa_paints",  "Africa Paints"),
    ("anetic",         "Anetic"),
    ("crest",          "Crest"),
    ("excelsior",      "Excelsior"),
    ("golden_choice",  "Golden Choice"),
]
CATEGORIES = ["enamel", "pva", "waterproofing"]

# Excel styling tokens (mirrors navy executive theme)
NAVY_FILL   = PatternFill("solid", fgColor="0D2040")
YELLOW_FILL = PatternFill("solid", fgColor="F5C400")
WARN_FILL   = PatternFill("solid", fgColor="FDDCDC")
WHITE_FONT  = Font(name="Barlow", size=11, color="FFFFFF", bold=True)
DARK_FONT   = Font(name="Barlow", size=11, color="0D2040", bold=True)

def load_secret() -> str:
    env_path = VF_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("FORM_ADMIN_SECRET="):
                return line.split("=", 1)[1].strip()
    val = os.environ.get("FORM_ADMIN_SECRET")
    if val:
        return val
    sys.exit("FORM_ADMIN_SECRET not set")

def fetch_submissions(secret: str, form_id: str) -> list[dict]:
    resp = requests.get(
        f"{FORMS_ADMIN_BASE}/api/forms/{form_id}/submissions",
        headers={"x-admin-secret": secret},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  WARN fetch {form_id}: {resp.status_code}")
        return []
    return resp.json().get("submissions", [])

def main():
    secret = load_secret()
    urls = json.loads((OUTPUT_DIR / "supabase_form_ids.json").read_text(encoding="utf-8"))

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    for slug, label in COMPETITORS:
        ws = wb.create_sheet(label[:31])  # Excel tab name max 31 chars
        ws.append([f"{label} — Verification Results"])
        ws["A1"].font = Font(name="Barlow Condensed", size=18, color="F5C400", bold=True)
        ws.append([])

        for cat in CATEGORIES:
            form_id = urls.get(slug, {}).get(cat)
            if not form_id:
                continue

            # Load source matchups for context
            matchups_path = OUTPUT_DIR / f"competitor_matchups_{slug}_{cat}.json"
            if not matchups_path.exists():
                continue
            matchups = json.loads(matchups_path.read_text(encoding="utf-8"))

            subs = fetch_submissions(secret, form_id)

            # Category header
            ws.append([f"{cat.upper()}  ({len(subs)} submission(s))"])
            ws[ws.max_row][0].font = Font(name="Barlow Condensed", size=14, color="0D2040", bold=True)
            ws[ws.max_row][0].fill = YELLOW_FILL

            # Column headers
            header_row = ["#", "Competitor product", "Pack", "Comp. price", "Current match (workbook)"]
            for s in subs:
                rep = s.get("metadata", {}).get("rep_code", "?")
                header_row.append(f"{rep} — match")
                header_row.append(f"{rep} — conf")
                header_row.append(f"{rep} — notes")
            ws.append(header_row)
            r = ws.max_row
            for c in range(1, len(header_row) + 1):
                cell = ws.cell(row=r, column=c)
                cell.fill = NAVY_FILL
                cell.font = WHITE_FONT
                cell.alignment = Alignment(wrap_text=True, vertical="top")

            # Body rows
            for n, m in enumerate(matchups, start=1):
                current = f"{m.get('current_olympic_match_code','')} — {m.get('current_olympic_match_name','')}".strip(" —")
                row = [
                    n,
                    m.get("competitor_product", ""),
                    m.get("pack_size", ""),
                    m.get("competitor_price", ""),
                    current,
                ]
                disagree = False
                for s in subs:
                    d = s.get("data", {})
                    rep_match = str(d.get(f"row_{n}_match", "") or "")
                    rep_conf  = str(d.get(f"row_{n}_confidence", "") or "")
                    rep_notes = str(d.get(f"row_{n}_notes", "") or "")
                    if rep_match and rep_match != current:
                        disagree = True
                    row.extend([rep_match, rep_conf, rep_notes])
                ws.append(row)
                if disagree:
                    for c in range(1, len(row) + 1):
                        ws.cell(row=ws.max_row, column=c).fill = WARN_FILL

            ws.append([])  # spacer

        # Column widths
        for col, width in [("A", 4), ("B", 36), ("C", 10), ("D", 12), ("E", 36)]:
            ws.column_dimensions[col].width = width
        for col_letter_ord in range(ord("F"), ord("F") + 30):
            ws.column_dimensions[chr(col_letter_ord)].width = 28

    out_path = OUTPUT_DIR / "verification_results.xlsx"
    wb.save(out_path)
    print(f"Saved {out_path}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6.2: Run after at least one rep has submitted**

```bash
python pull_verification_results.py
```

Open `output/verification_results.xlsx`. Confirm:
- 5 tabs (one per competitor)
- Each tab has up to 3 category sections
- Rows where the rep disagreed with the workbook are highlighted pink
- Notes appear in the rep's notes column

- [ ] **Step 6.3: (Optional) Schedule it**

If you want a daily refresh during the rollout, add a Windows Task Scheduler job per [[feedback_schtasks_logs_outside_onedrive]]. Logs go to `C:\Users\quint\.claude\logs\verification_results\`. Skip if you'd rather run it on demand.

- [ ] **Step 6.4: Log to changelog**

```
2026-05-DD  T6 done — aggregator written; first results pull saved to verification_results.xlsx.
```

---

## Task 7: Day 1 live dispatch (Enamels)

Same as JotForm plan T8 — only difference is the dispatcher now points at Supabase forms.

- [ ] **Step 7.1: Final check — today is the right day to fire?** (don't dispatch on weekends)

- [ ] **Step 7.2: Send Day 1**

```bash
python send_verification_emails.py --day enamel
```

- [ ] **Step 7.3: Verify Outlook Sent Items has 5 emails with CC to quintusl@**

- [ ] **Step 7.4: Telegram notify** (per [[feedback_telegram_notifications]], token from PULSE .env per [[feedback_telegram_token_source]])

```python
import requests
from pathlib import Path
env_path = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE — Sales & Ops Manager\.env")
token = next(line.split("=",1)[1].strip() for line in env_path.read_text().splitlines() if line.startswith("TELEGRAM_BOT_TOKEN="))
requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": 8042233389, "text": "✅ Day 1 (Enamel) Supabase verification emails sent to 5 reps."},
    timeout=10,
)
```

- [ ] **Step 7.5: Log to changelog**

---

## Task 8: Day 2 live dispatch (PVAs)

- [ ] **Step 8.1:** `python send_verification_emails.py --day pva`
- [ ] **Step 8.2:** Verify Outlook Sent + Telegram notify
- [ ] **Step 8.3:** Log to changelog

---

## Task 9: Day 3 live dispatch (Waterproofing)

- [ ] **Step 9.1:** `python send_verification_emails.py --day waterproofing`
- [ ] **Step 9.2:** Verify Outlook Sent + Telegram notify
- [ ] **Step 9.3:** Log to changelog

---

## Task 10: Memory entry

- [ ] **Step 10.1: Replace the JotForm memory with Supabase memory**

The existing `reference_competitor_verification_forms.md` describes JotForm. Rewrite it to describe the Supabase rollout. Save to `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\reference_competitor_verification_forms.md`:

```markdown
---
name: competitor-verification-forms
description: Self-hosted Supabase verification forms — 15 forms (5 competitors × 3 categories), rendered at /f/[form_id] on olympic-paints-forms-admin.vercel.app, results aggregated to verification_results.xlsx
metadata:
  type: reference
---

15 verification forms live on the existing Supabase + Next.js stack (`olympic-paints-forms-admin`). Replaces the abandoned JotForm rollout. Built 2026-05-DD.

**URL pattern:** `https://olympic-paints-forms-admin.vercel.app/f/<form_id>?rep=<code>&email=<addr>&competitor=<slug>&category=<cat>`

**Build artifacts:** `2.Areas/1. Sales/7. Competitor information/verification_forms/`
- `categorise_skus.py` / `extract_matchups.py` — re-run if pricelist or competitor workbooks change
- `build_supabase_forms.py` — re-run AFTER deleting an entry from `output/supabase_form_ids.json` (otherwise it skips already-built forms)
- `send_verification_emails.py --day enamel|pva|waterproofing` — Day 1/2/3 dispatcher (Outlook force-flushed, Telegram notify)
- `pull_verification_results.py` — aggregates submissions to `output/verification_results.xlsx` (one tab per competitor, pink highlight where rep disagrees with workbook)
- `output/supabase_form_ids.json` — `{ competitor_slug: { category: form_id } }`. Source of truth for the dispatcher.

**Forms-admin app changes (commits in `olympic-paints-forms-admin` repo):**
- `src/app/f/[form_id]/page.tsx` — server component, reads schema + searchParams, renders lockout page if `rep_code` already submitted
- `src/app/api/submit/[form_id]/route.ts` — public POST endpoint; enforces submit-once via `metadata->>'rep_code'` filter
- `src/app/api/forms/public/[form_id]/route.ts` — public GET schema endpoint (no admin secret)
- `src/components/FormRenderer.tsx` — client component with html/hidden field types and `default` prefill
- `src/lib/supabase/types.ts` — extended `FieldType` (`html`, `hidden`) + optional `default` field. No SQL migration — jsonb accepts the shape.

**Submit-once lockout:** server-side check on `metadata->>'rep_code'`. Per-rep, not per-IP. Spoofable but reps have no incentive to spoof — internal use only. If forms go external, sign URLs with HMAC.

**Why not JotForm:** see superseded plan `docs/superpowers/plans/2026-05-16-competitor-verification-jotforms.md`. We own the data; submissions join directly to the sales parquet via `metadata.rep_code` and per-row `current_olympic_match_code`.
```

- [ ] **Step 10.2: Index update in MEMORY.md**

The existing `reference_competitor_verification_forms.md` line under "Competitor Intelligence" already exists — replace its hook text:

```
- [Competitor Verification Forms — self-hosted Supabase rollout](reference_competitor_verification_forms.md) — 15 forms at /f/[form_id]; build/send/pull scripts in verification_forms/; results aggregated to verification_results.xlsx
```

- [ ] **Step 10.3: Archive the JotForm plan**

Move (or rename in place) `docs/superpowers/plans/2026-05-16-competitor-verification-jotforms.md` → add `SUPERSEDED — see 2026-05-16-competitor-verification-supabase.md` as the first line under the existing H1.

- [ ] **Step 10.4: Log to changelog**

```
2026-05-DD  T10 done — memory updated, JotForm plan marked superseded.
```

---

## Self-review checklist (run before handoff)

- [ ] Task 0 (categoriser + extractor) ran successfully — all 18 JSONs in `output/`
- [ ] Pick & Save is in `olympic_skus_enamel.json` (load-bearing per `feedback_pick_n_save_enamel_match`)
- [ ] `FormField` extended in `types.ts` with `html`, `hidden`, `default`
- [ ] Public submission endpoint enforces submit-once via `metadata->>'rep_code'`
- [ ] Public render page shows "already submitted" when `rep_code` matches existing submission
- [ ] Mobile-first CSS in `FormRenderer.tsx` (≥16px font, ≥44px tap targets) per [[feedback_html_mobile_first]]
- [ ] DOMPurify sanitizes the `html` field content
- [ ] Dispatcher URLs point at `olympic-paints-forms-admin.vercel.app/f/<id>`
- [ ] Outlook force-flush after `Send()` per [[feedback_outlook_send_flush]]
- [ ] Telegram notify after each live dispatch per [[feedback_telegram_notifications]]
- [ ] Telegram token sourced from PULSE `.env` per [[feedback_telegram_token_source]]
- [ ] Logo uses hosted URL not local file path per [[reference_logo_hosted_url]]
- [ ] `truststore.inject_into_ssl()` at top of any Python script making HTTPS calls per [[feedback_python_truststore_for_https]]
- [ ] Memory entry rewritten, JotForm memory line replaced in `MEMORY.md`
- [ ] JotForm plan marked SUPERSEDED

If any item fails, fix inline. No re-review needed.
