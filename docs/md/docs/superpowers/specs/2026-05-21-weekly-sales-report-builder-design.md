# Weekly Sales Report Builder — Design Spec

**Date:** 2026-05-21
**Author:** Quintus Lategan (with Claude)
**Status:** Approved design, pending implementation plan

---

## 1. Purpose

A single-user, week-scoped qualitative notebook for Olympic Paints sales. Quintus
drops free-form notes, photos, voice notes, screenshots, and PDFs into the system
throughout the week. Each note is stored on disk in the current ISO-week's bucket,
mirrored to a Notion database for queryability, and continuously re-compiled into a
live HTML report visible behind portal auth on Vercel. Friday 07:00 SAST, a snapshot
of the report is emailed to Quintus; Sunday midnight the week locks and archives.

The system replaces no existing tool — it is additive to PULSE (which handles
quantitative ops data: visits, leaderboards, scorecards). Where PULSE answers *"is
the team executing the plan?"*, this notebook answers *"what is happening in the
field, what's on my mind, what should we be thinking about?"*

## 2. Decisions log (Q&A summary)

The design is the product of eight sequenced decisions:

1. **Who feeds it.** Just Quintus. No reps, no factory, no permissions surface.
2. **Capture method.** Telegram free-form (hashtags optional, not required) + a
   folder watcher on `0.Inbox/weekly/` for desktop drops (PDFs, screenshots).
3. **Storage shape.** Weekly folders, one per ISO week, append-only JSON files.
   Pattern: `1.Projects/Weekly Sales Report/<ISO-week>/`.
4. **Report structure.** Hybrid — three fixed sections (Executive Summary, Rep
   Feedback, Quality & Operations) + LLM-clustered "Other Observations" below.
5. **Delivery.** Live URL that rebuilds on every note, plus a Friday 07:00 SAST
   email snapshot to Quintus only. Week stays open through Sunday 23:59.
6. **Classification rule.** By intent, not by origin. Rep Feedback = anything
   you'd discuss in a 1-on-1. Quality & Ops = anything affecting what we ship or
   how. Other = everything else. Hashtags are hints, never overrides.
7. **Hosting.** Vercel route `/weekly` on the existing
   `olympic-paints-portal.vercel.app` app, gated by Portal v1 auth.
8. **Database.** Files on disk (source of truth) + Notion `Weekly Sales Notes`
   database (queryable mirror). LanceDB deferred to Phase 2.

## 3. Architecture

```
                ┌────────────────────────┐
   Phone ──────►│ Telegram bot           │──┐
                │ (olympic_pulse_bot)    │  │
                └────────────────────────┘  │
                                            ▼
                                  ┌─────────────────────┐
   Desktop ─drop file──►  ┌──────►│ note_intake.py      │
                          │       │ (writes JSON+media) │
                ┌─────────┴──┐    └─────────┬───────────┘
                │ folder     │              │
                │ watcher    │              ▼
                │ (Inbox/    │   ┌──────────────────────────────┐
                │  weekly/)  │   │ 1.Projects/Weekly Sales      │
                └────────────┘   │ Report/2026-W21/             │
                                 │   notes/<ts>_<hash>.json     │
                                 │   media/<ts>_<original>.jpg  │
                                 └──────┬───────────────────────┘
                                        │ (rebuild trigger)
                          ┌─────────────┼────────────────┐
                          ▼             ▼                ▼
                ┌──────────────┐ ┌─────────────┐ ┌────────────────┐
                │ Notion mirror│ │ compile_    │ │ Vercel deploy  │
                │ (Weekly      │ │ report.py   │ │ portal /weekly │
                │  Notes DB)   │ │ → report.   │ │ (auth-gated)   │
                └──────────────┘ │   html      │ └────────────────┘
                                 └─────────────┘
                                        │
                                Friday 07:00 SAST
                                        ▼
                              ┌──────────────────────┐
                              │ Outlook → you only   │
                              │ HTML report attached │
                              └──────────────────────┘
```

**Key principle:** disk write is the only synchronously-required operation. Notion
mirror, compile, and Vercel deploy are best-effort and retried.

## 4. Components

| File | Purpose | Depends on |
|---|---|---|
| `note_intake.py` | Single entry point: takes text + media → writes JSON, copies media, calls notion mirror, fires compile (debounced) | Notion API, week_paths.py |
| `week_paths.py` | Returns canonical paths for the current ISO week (notes dir, media dir, HTML out) | datetime (ISO calendar) |
| `folder_watcher.py` | `watchdog` on `0.Inbox/weekly/` → invokes note_intake on file drop | watchdog, note_intake |
| `telegram_handler.py` | Plugged into existing PULSE bot — routes DMs from Quintus's chat ID (8042233389) to note_intake | python-telegram-bot, note_intake |
| `notion_mirror.py` | Pushes one note to the Weekly Notes DB; tolerant of rate limits | notion-client |
| `compile_report.py` | Reads week's JSON, classifies via Claude, renders HTML, copies to portal repo | anthropic SDK, jinja2 |
| `send_weekly_email.py` | Builds + sends Friday 07:00 SAST email via Outlook (win32com), force-flushes Outbox | win32com, compile_report |
| `archive_week.py` | Sunday 23:59 lock: rename current/ to dated folder, build locked HTML | week_paths |
| `init_new_week.py` | Monday 00:01: creates empty bucket for new ISO week | week_paths |
| `notion_retry_pending.py` | Every 5 min: sweeps notes with `_notion_state: pending` | notion_mirror |

## 5. Data shape

### JSON note file

Path: `1.Projects/Weekly Sales Report/<ISO-week>/notes/<ts>_<hash>.json`

```json
{
  "id": "2026-05-21T14-32-08_a3f9",
  "ts_utc": "2026-05-21T12:32:08Z",
  "ts_sast": "2026-05-21T14:32:08+02:00",
  "iso_week": "2026-W21",
  "source": "telegram",
  "source_meta": {
    "chat_id": "8042233389",
    "message_id": 18472,
    "forwarded_from": null
  },
  "text": "BV says the new Polokwane Build It is asking about our Pick & Save tinting service — they think there's volume in colour-on-demand for trade",
  "hashtags": ["#rep:BV", "#opportunity"],
  "media": [
    {
      "filename": "2026-05-21T14-32-08_a3f9_store_front.jpg",
      "kind": "image",
      "bytes": 2184322,
      "portal_url": "https://olympic-paints-portal.vercel.app/weekly/2026-W21/media/2026-05-21T14-32-08_a3f9_store_front.jpg"
    }
  ],
  "classification": null,
  "_compile_state": "pending",
  "_notion_state": "pending"
}
```

After successful classification:

```json
"classification": {
  "section": "rep_feedback",
  "subject": "BV / Polokwane Build It",
  "theme_label": null,
  "summary_one_line": "BV exploring Pick & Save tinting service at new Polokwane Build It",
  "tags_inferred": ["opportunity", "tinting", "polokwane", "build_it"],
  "classified_at": "2026-05-21T15:32:14Z",
  "classifier_version": "v1"
},
"_compile_state": "classified"
```

`section` is one of: `rep_feedback`, `quality_ops`, `other`, `unclassified`.

### Folder structure (one week)

```
1.Projects/Weekly Sales Report/
├── 2026-W21/
│   ├── notes/
│   │   ├── 2026-05-18T09-12-44_b1c0.json
│   │   ├── 2026-05-18T14-02-08_e7a2.json
│   │   └── … (one file per note)
│   ├── media/
│   │   ├── 2026-05-18T09-12-44_b1c0_paint_drip.jpg
│   │   └── 2026-05-21T14-32-08_a3f9_store_front.jpg
│   ├── report.html              # live, rebuilt on every note
│   ├── report_locked.html       # created Sunday 23:59
│   ├── friday_email_sent.json   # timestamp/recipient log
│   └── week_meta.json           # week start/end dates, note count, status
└── _archive_index.json          # rolling index of all locked weeks
```

### Notion `Weekly Sales Notes` database — columns

| Property | Type | Source |
|---|---|---|
| Title | text | `summary_one_line` (after classification), `text[:60]` before |
| Week | select | `iso_week` e.g. `2026-W21` |
| Section | select | `rep_feedback` / `quality_ops` / `other` / `unclassified` |
| Theme | text | `theme_label` (only if section=other) |
| Subject | text | `subject` |
| Source | select | `telegram` / `folder` |
| Captured | date | `ts_sast` |
| Hashtags | multi-select | `hashtags` |
| Tags (inferred) | multi-select | `tags_inferred` |
| Media | URL | first `portal_url` (comma-separated if multiple) |
| Note ID | text | matches JSON filename (round-trip key) |
| Full text | text | the raw `text` field, no truncation |

**Notion media policy:** path-only (URL to portal). No images uploaded into Notion
blocks. Authenticated portal URL means deleting a week's folder revokes Notion
access too — single point of revocation.

## 6. Compile algorithm

`compile_report.py` is the only place LLM cost is incurred.

1. Walk `notes/*.json` for the current week. Load all.
2. For any note with `_compile_state == "pending"`, send to Claude in one batched
   call. System prompt encodes the intent classification rule (rep_feedback /
   quality_ops / other). Hashtags passed as hints only. Model returns `section`,
   `subject`, `summary_one_line`, `tags_inferred`. Write back into each JSON, set
   `_compile_state = "classified"`.
3. For the "other" bucket: send all `other` notes together in a second Claude call →
   cluster into 2–4 themes, return a `theme_label` for each. Write back.
4. Render `report.html` from a single Jinja2 template using the Olympic navy theme
   (per `DESIGN_SYSTEM.md`).
5. Write `report.html` to the week folder AND copy into the Vercel portal repo at
   `/public/weekly/current/`. Push (or rely on auto-deploy if portal repo is
   git-watched).

**Debouncing:** intake schedules a compile for 5s from now. If another intake
arrives within those 5s, the timer resets. Single compile per burst.

**Performance budget:** ~10–15s end-to-end for ~50 notes.

## 7. Report layout

Top to bottom:

1. **Header.** Logo (Olympic Paints Logo Digital.jpg in 50%-radius wrapper) + title
   "WEEKLY SALES REPORT — 2026 WEEK 21" + period + note/photo counts + LIVE/LOCKED
   badge + theme toggle (Light / Dark / Brand / Navy — default Navy).
2. **Executive Summary.** Claude-written 3–5 bullets distilled from the whole
   week, regenerated on every compile (cheap — short prompt over the full
   classified corpus). Headline number: *"23 notes, 4 reps mentioned, 2 quality
   concerns flagged, 5 opportunities surfaced."*
3. **Rep Feedback** (fixed section). Grouped by rep (AC / AP / BV / NP / BM /
   Unattributed). Each note rendered as a uniform card: summary headline, full text,
   optional photo grid (max 3-wide thumbnails, click → lightbox to full portal URL),
   tag pills, timestamp. Lightbox is Phase 1 — vanilla JS, no new dependencies,
   uses the existing portal auth cookie for the image fetch.
4. **Quality & Operations** (fixed section). Grouped by subject. Severity badge
   (info / warning / danger) inferred by Claude.
5. **Other Observations** (themed section). 2–4 LLM-clustered theme blocks.
   Each theme has a label + count + grid of note cards.
6. **Footer.** Note count, last update timestamp, locked-snapshot link, Notion DB
   link, archive nav (previous weeks).

**Uniformity rule:** all three sections use the same note-card component. Only the
grouping logic above the cards varies. Empty sections render a single line ("No rep
feedback logged this week.") rather than disappearing.

## 8. Error handling

The asynchronous-by-default rule: disk write is the only operation that must succeed
for a note to count as "captured." Everything else is best-effort, retried, and
logged.

| Failure | Response |
|---|---|
| Notion API down / rate-limited | Note still written to disk. `_notion_state: pending`. Retried every 5 min by `notion_retry_pending.py`. |
| Claude classification call fails | Note keeps `_compile_state: pending`. Report renders the note in an "Unclassified" subsection of "Other" until next compile. Never blocks the report. |
| Vercel deploy fails | `report.html` still written to disk. Next successful intake retries the deploy. |
| Outlook not running Friday 07:00 | `send_weekly_email.py` starts Outlook via win32com, force-flushes the Outbox. If it still fails, sends a Telegram notification to chat 8042233389 with the error. |
| Folder watcher crashes | Task Scheduler restart-on-failure. Telegram capture path independent — single-channel outage doesn't lose data. |
| Telegram bot crashes | Folder watcher still works. PULSE bot's existing monitoring covers this. |

## 9. Edge cases

- **Note at 23:58 Sunday.** Goes into the current week. Sunday 23:59 lock runs after
  cutoff. 1-minute ambiguity window is accepted.
- **Note at 00:01 Monday.** Lands in the new week's bucket. Previous week's
  `report_locked.html` already written.
- **Photo > 10MB on Telegram.** Bot API caps at 50MB. Saved to disk at full
  resolution. Portal serves at full res. Image resizing is Phase 2.
- **Deleted note.** Manual file delete from `notes/`. Next compile rebuilds without
  it. Notion row stays orphaned until manually deleted (Phase 2: sweep).
- **Edit a note in Notion.** Notion → disk sync is **not** bidirectional in
  Phase 1. Documented limitation. Phase 2 adds polling sync.

## 10. Scheduled jobs

All registered as Windows Task Scheduler jobs. Logs to
`C:\Users\quint\.claude\logs\weekly-report\` (per existing convention: never
log to OneDrive paths from scheduled jobs).

| Job name | Trigger | Action |
|---|---|---|
| `Olympic — Weekly Report Friday Email` | Fri 07:00 SAST | `send_weekly_email.py` |
| `Olympic — Weekly Report Sunday Lock` | Sun 23:59 SAST | `archive_week.py` |
| `Olympic — Weekly Report Monday Init` | Mon 00:01 SAST | `init_new_week.py` |
| `Olympic — Weekly Report Notion Retry` | Every 5 min | `notion_retry_pending.py` |
| `Olympic — Weekly Report Folder Watcher` | At boot, restart on failure | `folder_watcher.py` |

Friday email subject line: *"Weekly Sales Report — Week 21 (in-progress snapshot,
will lock Sunday)."* Email is sent only to `quintusl@olympicpaints.co.za`. No CC.

## 11. Testing strategy

- Unit tests on `note_intake.py` — feed it text/media combinations, assert JSON
  shape and disk layout.
- Unit tests on `week_paths.py` — assert correct ISO week derivation.
- Integration test on compile: seed a `_test_W00/` folder with 5 fixture JSON notes
  → run `compile_report.py` with the Claude classifier **mocked** (fixture returns
  pre-baked classification + theme cluster JSON) → snapshot the rendered HTML and
  assert the three sections render with expected note counts. Mocking the LLM keeps
  the test deterministic and free; a separate manual "smoke" script exercises the
  real Claude call once per release.
- No tests on Telegram or Notion API surfaces — mock them out; trust the SDKs.

## 12. Out of scope (Phase 1)

The following are intentionally deferred:

- **LanceDB / semantic search.** Only useful once corpus exceeds ~6 months. Notion
  filtered views handle Phase-1 extraction.
- **Bidirectional Notion ↔ disk sync.** Edits in Notion don't propagate back.
- **Multi-user / rep contribution.** This is single-user (Quintus). Reps continue
  to feed PULSE for quantitative data.
- **Image resizing / video transcoding.** Full-res serving via portal until media
  folders become heavy.
- **Photo gallery / chronological feed tabs.** Lean layout for now; add if needed.
- **Cross-week trend dashboards.** Weeks are self-contained. Cross-week analytics
  is a separate future project that reads from the Notion mirror.
- **Telegram bot for input categories (commands like /idea, /quality).** Free-form
  capture with LLM intent classification is the explicit design.

## 13. Olympic Paints integration touchpoints

- **Telegram bot:** `olympic_pulse_bot` (token in `1.Projects/PULSE — Sales & Ops
  Manager/.env` as `TELEGRAM_BOT_TOKEN`). Chat ID `8042233389`. New handler routes
  DMs from this chat to `note_intake.py`.
- **Notion:** Integration "Olympic Paints Automations" (token in project `.env` as
  `NOTION_API_TOKEN`). New database "Weekly Sales Notes" must be created and shared
  with this integration.
- **Vercel portal:** `olympic-paints-portal.vercel.app` (existing Phase-1 app).
  Add `/weekly` route reading `report.html` from `/public/weekly/current/`. Reuses
  existing auth.
- **Outlook:** win32com email send to `quintusl@olympicpaints.co.za` only, with
  force-flush per the project's standard email convention.
- **Design system:** Olympic navy theme by default, full CSS token block, Barlow
  Condensed + Barlow fonts, official logo.jpg in 50%-radius wrapper. Per
  `DESIGN_SYSTEM.md`.

## 14. Glossary

- **Note** — a single captured artefact: text, hashtags, optional media.
- **Bucket** — the folder for one ISO week: `2026-W21/`.
- **Section** — fixed top-level category: `rep_feedback` / `quality_ops` /
  `other` / `unclassified`.
- **Theme** — LLM-assigned label clustering notes inside the `other` section
  (e.g. "Competitor activity", "Pricing pressure in Limpopo").
- **Live report** — `report.html`, continuously rebuilt during the week.
- **Locked report** — `report_locked.html`, written once at Sunday 23:59 and
  never re-rendered.
- **Mirror** — the Notion `Weekly Sales Notes` database, written to on every
  note intake.
