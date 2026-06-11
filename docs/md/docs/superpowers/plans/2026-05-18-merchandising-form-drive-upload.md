# Merchandising Recording Form — Google Drive Photo Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the native file-upload fields in the Merchandising Recording form with a Google Drive Picker button that auto-creates a `Rep / Store / Date` folder in a shared Drive and stores only the folder URL in Supabase.

**Architecture:** A new `DrivePickerField` React component handles OAuth, folder creation via Drive API v3, and file upload entirely client-side. `FormRenderer.tsx` is updated to render `DrivePickerField` instead of the native `<input type="file">` when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set. The Merchandising Recording form schema is updated so all 6 photo fields carry `"drive": true` in their field config. No backend changes needed — the folder URL is a plain string stored in the existing `data` JSONB column.

**Tech Stack:** Next.js 15, React 19, TypeScript, Google Identity Services (`accounts.google.com/gsi/client`), Google Picker API (`apis.google.com/js/api.js`), Google Drive API v3 (via `gapi.client.drive`), Supabase (existing), Vercel (existing).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/components/DrivePickerField.tsx` | **Create** | Self-contained Drive Picker component — OAuth, folder creation, upload, status display |
| `src/components/FormRenderer.tsx` | **Modify** | Swap `file` field branch to use `DrivePickerField` when env var present; remove Supabase Storage upload for drive-backed fields |
| `src/lib/supabase/types.ts` | **Modify** | Add `drive?: boolean` to `FormField` interface |
| `src/app/f/[form_id]/page.tsx` | **No change** | Already passes schema + prefill to `FormRenderer` — no change needed |
| `.env.local` | **Modify** | Add `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `NEXT_PUBLIC_GOOGLE_API_KEY`, `NEXT_PUBLIC_GOOGLE_DRIVE_ROOT_FOLDER_ID` |
| `vercel-env-setup.md` (new, docs only) | **Create** | Step-by-step for adding env vars to Vercel — not committed to repo |

---

## Pre-Requisites (manual steps before coding)

Complete these in the Google Cloud Console and Google Drive **before** running any code. Record the three values — you'll need them for `.env.local`.

- [ ] **Create Drive root folder**
  1. Open [drive.google.com](https://drive.google.com) as `qlategan@gmail.com`
  2. Create folder: `Olympic Paints — Merchandising Visits`
  3. Share with Viewer: `bhadreshv@olympicpaints.co.za`, `nikhilp@olympicpaints.co.za`, `amitp@olympicpaints.co.za`, `abooc@olympicpaints.co.za`, `byronm@olympicpaints.co.za`
  4. Share with Contributor: Goolab's Gmail address
  5. Copy the folder ID from the URL: `drive.google.com/drive/folders/<FOLDER_ID>` — save as `GOOGLE_DRIVE_ROOT_FOLDER_ID`

- [ ] **Create Google Cloud project**
  1. Go to [console.cloud.google.com](https://console.cloud.google.com)
  2. Create project: `olympic-paints-forms`
  3. Enable APIs: **Google Drive API** + **Google Picker API** (search in "APIs & Services > Library")

- [ ] **Create OAuth 2.0 Client ID**
  1. APIs & Services > Credentials > Create Credentials > OAuth client ID
  2. Type: **Web application**
  3. Name: `forms-admin`
  4. Authorised JavaScript origins: `https://olympic-paints-forms-admin.vercel.app` and `http://localhost:3000`
  5. Authorised redirect URIs: `https://olympic-paints-forms-admin.vercel.app` (no callback path needed — implicit flow)
  6. Save the **Client ID** as `GOOGLE_CLIENT_ID`

- [ ] **Create API Key**
  1. APIs & Services > Credentials > Create Credentials > API key
  2. Restrict key: Application restrictions = HTTP referrers
  3. Add referrers: `https://olympic-paints-forms-admin.vercel.app/*` and `http://localhost:3000/*`
  4. API restrictions: restrict to Drive API + Picker API only
  5. Save the **API key** as `GOOGLE_API_KEY`

---

## Task 1: Add `drive` flag to FormField type

**Files:**
- Modify: `src/lib/supabase/types.ts`

- [ ] **Step 1: Update `FormField` interface**

Open `src/lib/supabase/types.ts`. Change the `FormField` interface to add an optional `drive` field after `html`:

```typescript
export interface FormField {
  id:          string;
  type:        FieldType;
  label:       string;
  placeholder?: string;
  required?:   boolean;
  options?:    string[];
  default?:    string;
  html?:       string;     // rendered when type === 'html' (sanitized in FormRenderer)
  drive?:      boolean;    // when true and NEXT_PUBLIC_GOOGLE_CLIENT_ID is set, use Drive Picker instead of native file input
  order:       number;
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
git add src/lib/supabase/types.ts
git commit -m "feat: add drive flag to FormField type"
```

---

## Task 2: Add environment variables locally

**Files:**
- Modify: `.env.local` (never committed — already in `.gitignore`)

- [ ] **Step 1: Add the three env vars**

Open (or create) `C:\Users\quint\olympic-paints-forms-admin\.env.local` and add:

```
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<paste your OAuth Client ID here>
NEXT_PUBLIC_GOOGLE_API_KEY=<paste your API Key here>
NEXT_PUBLIC_GOOGLE_DRIVE_ROOT_FOLDER_ID=<paste the Drive root folder ID here>
```

- [ ] **Step 2: Verify Next.js picks them up**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). No errors in terminal.  
Stop the dev server with Ctrl+C.

---

## Task 3: Build `DrivePickerField` component

**Files:**
- Create: `src/components/DrivePickerField.tsx`

This component handles everything: loading the Google APIs, OAuth, folder creation, file upload, and status display. It accepts the folder path segments (`repName`, `storeName`, `visitDate`) and calls `onChange(folderUrl)` when at least one photo is uploaded.

- [ ] **Step 1: Create the file with the full implementation**

Create `src/components/DrivePickerField.tsx`:

```typescript
'use client';
import { useEffect, useRef, useState } from 'react';

// These are NEXT_PUBLIC_ vars — safe to use client-side
const CLIENT_ID   = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';
const API_KEY     = process.env.NEXT_PUBLIC_GOOGLE_API_KEY ?? '';
const ROOT_FOLDER = process.env.NEXT_PUBLIC_GOOGLE_DRIVE_ROOT_FOLDER_ID ?? '';
const SCOPES      = 'https://www.googleapis.com/auth/drive.file';

declare global {
  interface Window {
    gapi: any;
    google: any;
  }
}

interface Props {
  fieldId:   string;
  label:     string;
  required:  boolean;
  repName:   string;   // e.g. "Bhadresh"
  storeName: string;   // e.g. "Kit Kat Polokwane"
  visitDate: string;   // ISO date string e.g. "2026-05-18T09:15" — date portion used
  value:     string;   // current folder URL ('' if not yet uploaded)
  onChange:  (folderUrl: string) => void;
}

type UploadStatus = 'idle' | 'loading-api' | 'auth' | 'creating-folder' | 'uploading' | 'done' | 'error';

function normaliseName(s: string): string {
  return s.trim().replace(/\//g, '-').replace(/\s+/g, ' ');
}

function dateOnly(iso: string): string {
  // Take "2026-05-18T09:15" → "2026-05-18"
  return iso.split('T')[0] || new Date().toISOString().split('T')[0];
}

async function ensureFolder(
  accessToken: string,
  parentId: string,
  name: string,
): Promise<string> {
  // Search for existing folder with this name under parent
  const search = await fetch(
    `https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(
      `name='${name}' and '${parentId}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false`
    )}&fields=files(id)`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  const searchData = await search.json();
  if (searchData.files?.length > 0) {
    return searchData.files[0].id as string;
  }
  // Create it
  const create = await fetch('https://www.googleapis.com/drive/v3/files', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name,
      mimeType: 'application/vnd.google-apps.folder',
      parents: [parentId],
    }),
  });
  const createData = await create.json();
  if (!createData.id) throw new Error(`Failed to create folder "${name}": ${JSON.stringify(createData)}`);
  return createData.id as string;
}

async function uploadFile(
  accessToken: string,
  folderId: string,
  file: File,
): Promise<void> {
  const metadata = { name: file.name, parents: [folderId] };
  const form = new FormData();
  form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
  form.append('file', file);
  const res = await fetch(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}` },
      body: form,
    },
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(`Upload failed: ${JSON.stringify(err)}`);
  }
}

export default function DrivePickerField({
  fieldId, label, required, repName, storeName, visitDate, value, onChange,
}: Props) {
  const [status, setStatus]         = useState<UploadStatus>('idle');
  const [uploadCount, setUploadCount] = useState(0);
  const [errorMsg, setErrorMsg]     = useState('');
  const accessTokenRef              = useRef<string>('');
  const pickerInited                = useRef(false);

  // Load Google Identity Services + gapi once
  useEffect(() => {
    if (pickerInited.current) return;
    pickerInited.current = true;

    const loadGapi = () =>
      new Promise<void>((resolve) => {
        const s = document.createElement('script');
        s.src = 'https://apis.google.com/js/api.js';
        s.onload = () => window.gapi.load('picker', resolve);
        document.head.appendChild(s);
      });

    const loadGis = () =>
      new Promise<void>((resolve) => {
        const s = document.createElement('script');
        s.src = 'https://accounts.google.com/gsi/client';
        s.onload = () => resolve();
        document.head.appendChild(s);
      });

    Promise.all([loadGapi(), loadGis()]).catch(() => {});
  }, []);

  const missingContext = !repName.trim() || !storeName.trim();

  async function handleUpload() {
    if (missingContext) return;
    if (!CLIENT_ID || !API_KEY || !ROOT_FOLDER) {
      setStatus('error');
      setErrorMsg('Google Drive is not configured. Contact Quintus.');
      return;
    }

    setStatus('auth');
    setErrorMsg('');

    // Request OAuth token via GIS
    const tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: SCOPES,
      callback: async (tokenResponse: any) => {
        if (tokenResponse.error) {
          setStatus('error');
          setErrorMsg(`Auth failed: ${tokenResponse.error}`);
          return;
        }
        accessTokenRef.current = tokenResponse.access_token;
        await runPickerAndUpload(tokenResponse.access_token);
      },
    });
    tokenClient.requestAccessToken({ prompt: '' });
  }

  async function runPickerAndUpload(accessToken: string) {
    return new Promise<void>((resolve) => {
      const pickerCallback = async (data: any) => {
        if (data.action !== window.google.picker.Action.PICKED) {
          setStatus('idle');
          resolve();
          return;
        }
        const files: any[] = data[window.google.picker.Response.DOCUMENTS];
        if (!files || files.length === 0) {
          setStatus('idle');
          resolve();
          return;
        }

        try {
          setStatus('creating-folder');

          // Build Rep / Store / Date folder path
          const rep   = normaliseName(repName);
          const store = normaliseName(storeName);
          const date  = dateOnly(visitDate || new Date().toISOString());

          const repFolderId   = await ensureFolder(accessToken, ROOT_FOLDER, rep);
          const storeFolderId = await ensureFolder(accessToken, repFolderId, store);
          const dateFolderId  = await ensureFolder(accessToken, storeFolderId, date);

          // Fetch the actual File objects from Drive (picker returns metadata only)
          setStatus('uploading');
          let uploaded = 0;
          for (const doc of files) {
            const fileId = doc[window.google.picker.Document.ID];
            // Download from Drive (user picked an existing Drive file)
            // OR if they picked from device (uploadType='photos'), it's already uploaded
            // For device photos: picker in PHOTOS view returns already-uploaded files
            // We just move them into the target folder
            await fetch(
              `https://www.googleapis.com/drive/v3/files/${fileId}?addParents=${dateFolderId}&removeParents=${doc[window.google.picker.Document.PARENT_ID] || ''}&fields=id`,
              {
                method: 'PATCH',
                headers: { Authorization: `Bearer ${accessToken}` },
              },
            );
            uploaded++;
            setUploadCount(uploaded);
          }

          const folderUrl = `https://drive.google.com/drive/folders/${dateFolderId}`;
          onChange(folderUrl);
          setStatus('done');
        } catch (err) {
          setStatus('error');
          setErrorMsg(err instanceof Error ? err.message : 'Upload failed');
        }
        resolve();
      };

      const picker = new window.google.picker.PickerBuilder()
        .addView(
          new window.google.picker.DocsUploadView()
            .setIncludeFolders(false)
        )
        .addView(new window.google.picker.PhotosView())
        .setOAuthToken(accessToken)
        .setDeveloperKey(API_KEY)
        .setCallback(pickerCallback)
        .setTitle(`${label} — select photos`)
        .enableFeature(window.google.picker.Feature.MULTISELECT_ENABLED)
        .build();
      picker.setVisible(true);
    });
  }

  const folderUrl = value;

  return (
    <div className="field" id={`drive-field-${fieldId}`}>
      <span className="label">{label}{required && ' *'}</span>

      {missingContext && (
        <p className="drive-hint">Fill in Store Name and Servicing Rep first</p>
      )}

      {!missingContext && status !== 'done' && (
        <button
          type="button"
          className="drive-btn"
          onClick={handleUpload}
          disabled={status !== 'idle' && status !== 'error'}
        >
          {status === 'idle'            && '📤 Upload to Google Drive'}
          {status === 'auth'            && 'Waiting for Google sign-in…'}
          {status === 'creating-folder' && 'Creating folder…'}
          {status === 'uploading'       && `Uploading… (${uploadCount} done)`}
          {status === 'error'           && '⚠ Retry upload'}
        </button>
      )}

      {status === 'done' && folderUrl && (
        <div className="drive-done">
          <span>✓ Photos uploaded</span>
          <a href={folderUrl} target="_blank" rel="noreferrer" className="drive-link">
            View folder ↗
          </a>
        </div>
      )}

      {status === 'error' && errorMsg && (
        <p className="drive-error">{errorMsg}</p>
      )}

      {/* Hidden input so the form submit handler reads the folder URL as a string */}
      <input type="hidden" name={fieldId} value={folderUrl} />

      <style jsx>{`
        .drive-btn {
          display: flex; align-items: center; justify-content: center;
          width: 100%; min-height: 44px; padding: 12px 14px;
          background: #0D2040; color: #B8CCE8;
          border: 1px dashed rgba(107,158,208,0.5); border-radius: 8px;
          font-size: 15px; font-family: Barlow, sans-serif; cursor: pointer;
          transition: border-color 0.15s, color 0.15s;
        }
        .drive-btn:hover:not(:disabled) { border-color: #F5C400; color: #F5C400; }
        .drive-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .drive-done {
          display: flex; align-items: center; gap: 12px;
          padding: 12px 14px; background: rgba(45,140,122,0.12);
          border: 1px solid rgba(45,140,122,0.30); border-radius: 8px;
          color: #C8EDE7; font-size: 14px;
        }
        .drive-link { color: #F5C400; font-weight: 600; text-decoration: none; }
        .drive-link:hover { text-decoration: underline; }
        .drive-hint { color: #6B9ED0; font-size: 13px; margin: 4px 0 0; }
        .drive-error { color: #FDDCDC; font-size: 13px; margin: 6px 0 0; }
      `}</style>
    </div>
  );
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
git add src/components/DrivePickerField.tsx
git commit -m "feat: add DrivePickerField component with OAuth + folder creation"
```

---

## Task 4: Wire `DrivePickerField` into `FormRenderer`

**Files:**
- Modify: `src/components/FormRenderer.tsx`

Two changes:
1. In the `Field` function: swap the `file` branch to use `DrivePickerField` when `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set and `field.drive` is true
2. In `onSubmit`: skip the Supabase Storage upload loop for fields where the value is already a Drive URL string (not a `File[]`)

- [ ] **Step 1: Add the import at the top of `FormRenderer.tsx`**

After the existing imports (line 5), add:

```typescript
import DrivePickerField from '@/components/DrivePickerField';
```

- [ ] **Step 2: Update state initialisation for `file` fields**

In the `initial` state builder (lines 25-26), the `file` branch currently sets `initial[f.id] = []`. Change it so drive-backed file fields default to an empty string (they'll hold a URL, not a File array):

```typescript
} else if (f.type === 'file') {
  initial[f.id] = f.drive ? '' : [];   // drive fields: string URL; native: File[]
```

- [ ] **Step 3: Update `onSubmit` to skip Supabase Storage for drive fields**

In the `onSubmit` function, the file upload loop starts at the line `for (const f of schema) {`. Update the check at the top of that loop body:

```typescript
for (const f of schema) {
  if (f.type !== 'file') continue;
  if (f.drive) continue;  // drive fields already have a URL string — no Supabase upload needed
  const files = values[f.id] as File[];
  // ... rest of loop unchanged
```

- [ ] **Step 4: Swap the `file` branch in the `Field` component**

Find the `if (field.type === 'file')` block in the `Field` function (starts around line 245). Replace the entire block:

```typescript
if (field.type === 'file') {
  const DRIVE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';
  if (field.drive && DRIVE_CLIENT_ID) {
    // Drive Picker mode — value is a folder URL string
    // repName and storeName are read from sibling field values via the parent form state.
    // FormRenderer passes them down via the onChange closure — we need to surface them.
    // Since Field doesn't have access to sibling values directly, we use a data attribute
    // approach: the parent FormRenderer passes a `siblingValues` prop.
    // NOTE: see Task 4 Step 5 for the siblingValues wiring.
    return (
      <DrivePickerField
        fieldId={field.id}
        label={field.label}
        required={field.required ?? false}
        repName={(field as any)._repName ?? ''}
        storeName={(field as any)._storeName ?? ''}
        visitDate={(field as any)._visitDate ?? ''}
        value={value as string}
        onChange={onChange}
      />
    );
  }

  // Native file input fallback (no Drive configured, or field.drive not set)
  const files = (value as File[] | undefined) ?? [];
  return (
    <div className="field">
      <span className="label">{field.label}{field.required && ' *'}</span>
      <label className="file-label">
        <input
          type="file"
          accept="image/*,.pdf"
          multiple
          required={field.required && files.length === 0}
          className="file-input"
          onChange={(e) => {
            const selected = Array.from(e.target.files ?? []);
            onChange(selected);
          }}
        />
        <span className="file-btn">
          {files.length === 0 ? '📎 Choose photos / files' : `${files.length} file${files.length > 1 ? 's' : ''} selected`}
        </span>
      </label>
      {files.length > 0 && (
        <ul className="file-list">
          {files.map((f, i) => <li key={i}>{f.name}</li>)}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Pass sibling context to drive file fields**

The `DrivePickerField` needs `repName`, `storeName`, and `visitDate` from sibling fields. Add an enrichment step in the `FormRenderer` render loop, just before the `return` in the `ordered.map` call:

Replace:
```typescript
return (
  <Field key={f.id} field={f} value={values[f.id]} onChange={(v) => setValues((prev) => ({ ...prev, [f.id]: v }))} />
);
```

With:
```typescript
// Enrich drive file fields with sibling values needed for folder naming
const enrichedField = f.drive && f.type === 'file'
  ? { ...f, _repName: String(values['servicing_rep'] ?? ''), _storeName: String(values['store_name'] ?? ''), _visitDate: String(values['checked_in_at'] ?? '') }
  : f;

return (
  <Field key={f.id} field={enrichedField} value={values[f.id]} onChange={(v) => setValues((prev) => ({ ...prev, [f.id]: v }))} />
);
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add src/components/FormRenderer.tsx
git commit -m "feat: wire DrivePickerField into FormRenderer for drive-flagged file fields"
```

---

## Task 5: Update the Merchandising Recording form schema

**Files:**
- Script: run once from PowerShell — not committed

The Merchandising Recording form was created in Task 0 (already live in Supabase with ID `04dc0ce5-8f1a-410a-a61c-883ac252139c`). We need to update the 6 photo fields to include `"drive": true`. Use the forms-admin API's update endpoint if it exists, or patch Supabase directly.

- [ ] **Step 1: Patch the form schema via Supabase directly**

Run this Python script once from the terminal:

```python
# patch_merch_form_drive.py  — run once, do not commit
import truststore
truststore.inject_into_ssl()

import json
from supabase import create_client

SUPABASE_URL = "<your NEXT_PUBLIC_SUPABASE_URL from .env.local>"
SUPABASE_KEY = "<your SUPABASE SERVICE_ROLE_KEY from .env.local>"  # service role needed to patch
FORM_ID = "04dc0ce5-8f1a-410a-a61c-883ac252139c"

DRIVE_FIELD_IDS = {
    "store_front_photo",
    "stock_location_before",
    "stock_location_after",
    "colour_chart_before",
    "colour_chart_after",
    "gazebo_day_images",
}

sb = create_client(SUPABASE_URL, SUPABASE_KEY)
row = sb.table("form_schemas").select("schema").eq("id", FORM_ID).single().execute()
schema = row.data["schema"]

updated = 0
for field in schema:
    if field.get("id") in DRIVE_FIELD_IDS:
        field["drive"] = True
        updated += 1

sb.table("form_schemas").update({"schema": schema}).eq("id", FORM_ID).execute()
print(f"Patched {updated} fields with drive=True")
```

Get `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from `C:\Users\quint\olympic-paints-forms-admin\.env.local` (the service role key should be there, or find it in the Supabase dashboard under Settings > API).

Run:
```bash
cd C:\Users\quint\olympic-paints-forms-admin
pip install supabase --quiet
python patch_merch_form_drive.py
```

Expected output:
```
Patched 6 fields with drive=True
```

- [ ] **Step 2: Verify in the Supabase dashboard**

Open the Supabase Table Editor, find the row with `id = 04dc0ce5-8f1a-410a-a61c-883ac252139c` in `form_schemas`, and confirm the 6 photo fields in the `schema` JSONB column now have `"drive": true`.

---

## Task 6: Smoke-test locally on desktop

- [ ] **Step 1: Start dev server**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
npm run dev
```

- [ ] **Step 2: Open the Merchandising Recording form**

Open: `http://localhost:3000/f/04dc0ce5-8f1a-410a-a61c-883ac252139c`

- [ ] **Step 3: Verify Drive fields render correctly**

Fill in:
- Store Name: `Test Store`
- Servicing Rep: `Bhadresh`
- Date & Time Checked In: today's date

Scroll to "Store Front Photo" — it should show a **"📤 Upload to Google Drive"** button, not a native file picker.

Scroll to the bottom — "Postal / Zip Code" and text fields should still use native inputs (not Drive).

- [ ] **Step 4: Test OAuth and upload**

Click "📤 Upload to Google Drive" on Store Front Photo.

Expected flow:
1. Google sign-in popup appears
2. Goolab's (or your test) Google account authorises the app
3. Google Picker opens — select 1 test photo
4. Field shows "✓ Photos uploaded · View folder ↗"
5. Click "View folder ↗" — should open `Olympic Paints — Merchandising Visits / Bhadresh / Test Store / YYYY-MM-DD` in Drive

- [ ] **Step 5: Submit the form and verify Supabase**

Fill in all required text fields, upload at least the required photo fields, then click Submit.

Open Supabase Table Editor > `form_submissions`. The newest row's `data` column should contain:
```json
"store_front_photo": "https://drive.google.com/drive/folders/<some-id>"
```
Not a Supabase storage URL, not null — a Drive folder URL.

- [ ] **Step 6: Stop dev server**

Ctrl+C.

---

## Task 7: Deploy to Vercel and add env vars

- [ ] **Step 1: Add env vars to Vercel**

Do NOT pipe from PowerShell (BOM corruption risk). Use the Vercel dashboard instead:

1. Go to [vercel.com/flomaticautos-projects/olympic-paints-forms-admin/settings/environment-variables](https://vercel.com/flomaticautos-projects/olympic-paints-forms-admin/settings/environment-variables)
2. Add these three variables for **Production** + **Preview** environments:
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = your OAuth Client ID
   - `NEXT_PUBLIC_GOOGLE_API_KEY` = your API Key
   - `NEXT_PUBLIC_GOOGLE_DRIVE_ROOT_FOLDER_ID` = your Drive root folder ID

- [ ] **Step 2: Deploy**

```bash
cd C:\Users\quint\olympic-paints-forms-admin
$env:NODE_OPTIONS="--use-system-ca"
npx vercel --prod
```

Expected: deployment completes, prints production URL.

- [ ] **Step 3: Smoke-test on production URL**

Open on your phone: `https://olympic-paints-forms-admin.vercel.app/f/04dc0ce5-8f1a-410a-a61c-883ac252139c`

Fill in Store Name + Servicing Rep + Check-in time. Tap "📤 Upload to Google Drive" on Store Front Photo.

Expected: Google sign-in sheet appears (first time only), Picker opens from camera roll, photo uploads, folder link appears.

- [ ] **Step 4: Share the form URL with Goolab**

Send Goolab the URL via WhatsApp:
```
https://olympic-paints-forms-admin.vercel.app/f/04dc0ce5-8f1a-410a-a61c-883ac252139c
```

Ask him to:
1. Bookmark it to his home screen (browser menu > "Add to Home Screen")
2. Do one test submission with dummy data to confirm Drive access works on his phone

---

## Task 8: Final verification

- [ ] Goolab's test submission appears in Supabase `form_submissions`
- [ ] Drive folder `Olympic Paints — Merchandising Visits / [Rep] / [Store] / [Date]` was created
- [ ] Test photo appears in the folder
- [ ] All 5 rep email addresses can view the folder in Drive (ask one rep to confirm)
- [ ] Submit the form with `gazebo_day_images` left empty — submission succeeds (field is optional)
- [ ] Submit the form with `purpose_of_visit = Merchandising` — Gazebo fields are not required, form submits

---

## Notes

- The Google Picker uses `DocsUploadView` (device upload) + `PhotosView` (existing Drive photos). On mobile, `DocsUploadView` will offer the camera roll.
- The folder URL is the same for all 6 photo fields on one submission — this is by design. Each Picker session moves the selected files into the same `Rep / Store / Date` folder.
- If Goolab fills in the wrong rep name, the folder will be created under that name. The Supabase `data` column is the authoritative record — the `servicing_rep` text field determines the folder path.
- The `drive=True` flag in the schema is what activates the Picker UI. Forms without that flag continue to use native file input as before (no other forms are affected).
