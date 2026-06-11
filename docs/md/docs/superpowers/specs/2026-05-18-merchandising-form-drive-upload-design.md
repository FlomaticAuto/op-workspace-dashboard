# Merchandising Recording Form — Google Drive Photo Upload

**Date:** 2026-05-18  
**Status:** Approved  
**Author:** VAULT (brainstormed with Quintus)

---

## Problem

The Merchandising Recording form (Supabase form ID `04dc0ce5-8f1a-410a-a61c-883ac252139c`) has 5 photo upload fields. Storing binary image data directly in Supabase is impractical — it bloats the database, hits row size limits quickly, and makes browsing/sharing photos difficult. Goolab (the merchandiser) takes multiple photos per field per visit, compounding the volume problem.

---

## Decision

Photo fields use the **Google Drive Picker API** embedded in the form. Photos upload to a shared Google Drive folder. Supabase stores only the Drive folder URL (text), not binary data.

---

## Architecture

```
[Goolab's phone — mobile browser]
  ↓  opens form URL
[olympic-paints-forms-admin.vercel.app/f/<id>]
  ↓  taps "Upload to Google Drive" on a photo field
[Google Drive Picker popup]  ←  OAuth: Goolab's Google account (one-time consent)
  ↓  selects photos from camera roll
[Google Drive API]
  ↓  creates subfolder: Rep / Store / YYYY-MM-DD (if not exists)
  ↓  uploads selected photos into that subfolder
  ↓  returns folder URL
[Form field value]  ←  folder URL stored automatically in the field
  ↓  on form submit
[Supabase responses table]  ←  all text fields + Drive folder URLs persisted
```

---

## Google Drive Folder Structure

Root folder: **Olympic Paints — Merchandising Visits**  
Owner: Quintus (`qlategan@gmail.com`)  
Sharing: all 5 reps (view) + Goolab (contributor) + Quintus (owner)

```
📁 Olympic Paints — Merchandising Visits
  📁 Bhadresh
    📁 Kit Kat Polokwane
      📁 2026-05-18
        🖼 store-front.jpg
        🖼 stock-location-before.jpg
        🖼 stock-location-after.jpg
        🖼 colour-chart-before.jpg
        🖼 colour-chart-after.jpg
        🖼 gazebo-1.jpg         ← only on Gazebo Day visits
  📁 Nikhil
    📁 Big On Hardware
      📁 2026-05-17
  📁 Amit
  📁 Aboo
  📁 Byron
```

Folder creation is triggered at upload time. If the `Rep / Store / Date` path already exists, photos are added to the existing folder (idempotent).

---

## Form UI Changes

The `forms-admin` Vercel app renders `type: "file"` fields differently when a Google Drive OAuth client ID is configured:

**Before:** Native `<input type="file">` — uploads binary to Supabase.  
**After:** A styled **"Upload to Google Drive"** button. On tap:
1. Google Drive Picker opens (popup/sheet on mobile)
2. User selects one or more photos from camera roll or Drive
3. Drive API uploads to `Rep / Store / Date` subfolder
4. Field displays: `✓ N photos uploaded · View folder ↗`
5. Field value = Drive folder URL (string)

All 5 photo fields use this pattern:
- `store_front_photo`
- `stock_location_before`
- `stock_location_after`
- `colour_chart_before`
- `colour_chart_after`

Plus the optional Gazebo field:
- `gazebo_day_images`

All photos for a single visit land in the same dated subfolder, so all 6 fields store the **same folder URL**. Each field button still triggers a separate Picker session — the label tells Goolab which photos to select (e.g. "Stock Location Before"). This means Goolab taps Upload 6 times per visit (once per photo group), each time uploading the relevant set of images into the same folder. The folder URL written to Supabase is identical across all 6 fields for that submission.

---

## Supabase Data Model

No schema changes to the `responses` table. All photo fields remain `text` columns — they store Drive folder URLs instead of file paths.

Example submission row:
```json
{
  "store_name": "Kit Kat Polokwane",
  "servicing_rep": "Bhadresh",
  "checked_in_at": "2026-05-18T09:15",
  "checked_fifo": "Yes",
  "stock_sufficient": "No",
  "floor_vinyls": 2,
  "store_front_photo": "https://drive.google.com/drive/folders/ABC123",
  "stock_location_before": "https://drive.google.com/drive/folders/ABC123",
  "stock_location_after": "https://drive.google.com/drive/folders/ABC123",
  "colour_chart_before": "https://drive.google.com/drive/folders/ABC123",
  "colour_chart_after": "https://drive.google.com/drive/folders/ABC123",
  "gazebo_day_images": null
}
```

---

## Access Model

| Who | Drive access | Supabase/form access |
|---|---|---|
| Quintus | Owner — full control | Admin — all submissions |
| All 5 reps (AC/AP/BV/NP/BM) | View — can browse all visit folders | None (for now) |
| Goolab | Contributor — can upload, view own uploads | Submitter only |

Rep emails for Drive sharing:
- BV: `bhadreshv@olympicpaints.co.za`
- NP: `nikhilp@olympicpaints.co.za`
- AP: `amitp@olympicpaints.co.za`
- AC: `abooc@olympicpaints.co.za`
- BM: `byronm@olympicpaints.co.za`

---

## One-Time Setup Checklist

### Google Drive
- [ ] Create root folder **Olympic Paints — Merchandising Visits** in Quintus's Google Drive
- [ ] Share with all 5 rep emails (Viewer) and Goolab's email (Contributor)
- [ ] Record the root folder ID (from the Drive URL) — needed for the API

### Google Cloud
- [ ] Create a Google Cloud project (e.g. `olympic-paints-forms`)
- [ ] Enable **Google Drive API** and **Google Picker API**
- [ ] Create an **OAuth 2.0 Client ID** (Web application type)
  - Authorised JavaScript origins: `https://olympic-paints-forms-admin.vercel.app`
  - Authorised redirect URIs: `https://olympic-paints-forms-admin.vercel.app/api/auth/google/callback`
- [ ] Create an **API Key** (restricted to Drive API + Picker API, referrer: forms-admin domain)
- [ ] Record: `GOOGLE_CLIENT_ID`, `GOOGLE_API_KEY`, `GOOGLE_DRIVE_ROOT_FOLDER_ID`

### forms-admin (Vercel)
- [ ] Add environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_API_KEY`, `GOOGLE_DRIVE_ROOT_FOLDER_ID`
- [ ] Implement Drive Picker component (see Component Design below)
- [ ] Update form renderer to use Drive Picker for `type: "file"` fields when `GOOGLE_CLIENT_ID` is set
- [ ] Deploy and test on mobile (iOS Safari + Android Chrome)

---

## Component Design — DrivePickerField

New React/vanilla JS component in `forms-admin`:

**Props / inputs:**
- `fieldId` — snake_case field ID (e.g. `store_front_photo`)
- `label` — display label
- `required` — boolean
- `repName` — value of the `servicing_rep` field (passed at render time)
- `storeName` — value of the `store_name` field
- `visitDate` — value of `checked_in_at` (date portion)

**Behaviour:**
1. On mount: load Google Picker API script (`gapi`)
2. On button tap: call `gapi.auth2` for Drive scope, open Picker
3. On file selected: call Drive API to ensure folder path `Rep / Store / YYYY-MM-DD` exists (create if missing), upload file, return folder URL
4. On upload complete: set field value to folder URL, show `✓ N photos · View folder`
5. If `repName` / `storeName` not yet filled: show tooltip "Fill in Store Name and Servicing Rep first"

**Folder path construction:**
```
root_folder / repName / storeName / YYYY-MM-DD
```
All three segments normalised: trimmed, title-cased, slashes replaced with dashes.

---

## Out of Scope

- Viewing photos inside the form after submission (use Drive directly)
- Automatic Telegram/email notification when a submission arrives (separate task)
- Per-rep Drive folder access control beyond the shared root folder
- Offline-first / PWA support (Drive Picker requires internet)

---

## Dependencies

| Dependency | Version / Notes |
|---|---|
| Google Picker API | Loaded via CDN at runtime |
| Google Drive API v3 | Via `gapi.client.drive` |
| OAuth 2.0 | Client-side implicit flow (no backend token exchange needed) |
| forms-admin | Current Vercel deployment — needs `GOOGLE_CLIENT_ID` env var |
