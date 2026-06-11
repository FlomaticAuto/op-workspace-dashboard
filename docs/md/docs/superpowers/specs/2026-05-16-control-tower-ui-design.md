# Olympic Paints Control Tower UI — Design

**Date:** 2026-05-16
**Status:** Approved, ready for implementation plan
**Sub-project:** 3 of 3 (Olympic Paints management platform)

---

## Context

Sub-project #1 (Task Scheduler Consolidation) produced `schedule_manifest.json` — refreshed hourly with status for every Olympic-related scheduled task. Sub-project #2 (Agent Registry) was deferred. This spec covers sub-project #3: the **Control Tower UI** — a single front door consuming the schedule manifest and surfacing the broader operational picture.

The user's original problem: "too many dashboards, too many places to hide, too many things I don't look at." This UI is the one page Quintus opens in the morning that surfaces what needs attention, where everything else lives, and who owns it.

## Goals

1. One URL replaces the current `workspace-dashboard/index.html` and `updates.html` as the operational front door.
2. Five sections — **Today · Schedule · Dashboards · Reports · Agents** — cover the full surface area Quintus needs to scan daily.
3. Feels like a native app on mobile (per the project's "HTML must be mobile-first, app look on phone" rule).
4. Strict adherence to the Olympic Paints design system (4-theme tokens, Barlow fonts, real logo, no frameworks).
5. Manual refresh control for `schedule_manifest.json` (user chose this over auto-refresh).
6. Graceful degradation when the schedule manifest can't be loaded.

## Non-Goals

- A standalone Agent Registry data structure (sub-project #2 — deferred; agent data is inlined in the HTML for MVP).
- Replacing other dashboards (KPI, Store Health, etc.) — those remain at their existing URLs; the Control Tower links to them.
- Editing/triggering tasks from the UI — read-only surface.
- Auto-refresh while the page is open — explicitly out of scope (user picked manual refresh button).
- A build step / templating system — page is hand-authored static HTML.
- Mobile push notifications — Telegram already handles the "wake up" channel.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  workspace-dashboard/index.html (live: …/workspace-dashboard/)   │
│                                                                  │
│  • Hand-authored static HTML + vanilla JS (no framework)         │
│  • Embedded JS constants:                                        │
│      const DASHBOARDS = [...]                                    │
│      const REPORTS    = [...]                                    │
│      const AGENTS     = [...]                                    │
│      const INSIGHTS   = [...]   (preserves INFO_INSIGHT_DATA)    │
│  • CSS: Olympic Paints token system, 4 themes, dark default      │
│  • Manual "Refresh" button fetches data/schedule_manifest.json   │
│  • Fetches once on initial load; otherwise only on button click  │
│  • Falls back to last-good data on fetch failure (banner)        │
└─────────────────────────┬────────────────────────────────────────┘
                          │ on initial load + Refresh button
                          ▼
            data/schedule_manifest.json
              (refreshed hourly by sub-project #1)
```

### Information architecture

Sidebar nav on desktop (≥768px), bottom-tab nav on mobile (<768px). Sidebar sections, in order:

1. **Today** — first impression, "what needs my attention"
2. **Schedule** — full task inventory
3. **Dashboards** — links to the live dashboards
4. **Reports** — links to the standing PDF/static reports
5. **Agents** — agent profile cards

On mobile the bottom nav surfaces **Today · Schedule · Dashboards · More**. "More" opens a drawer with Reports + Agents.

### Rollout

Build at `workspace-dashboard/index-v2.html`. Iterate until satisfied. Final commit:
- Rename current `index.html` → `index-snapshot.html.bak`
- Rename `index-v2.html` → `index.html`
- Single revert path: swap the rename if needed.

---

## Components

### 1. Page skeleton (`index-v2.html` → `index.html`)

A single HTML document containing:

- `<head>` — title, viewport, font preconnects, Olympic Paints CSS token block (verbatim from `CLAUDE.md`), pre-paint theme-restore script (`localStorage` `oly-theme` → `<html>` class)
- `<body>` — sidebar + main panel + theme bar + bottom-nav (mobile)
- Inline `<script>` — data constants, fetch logic, view rendering, nav state

Strict design system rules apply (Barlow Condensed + Barlow, `--color-*` tokens only, no third-party frameworks, real logo at 36px in a `border-radius:50%;overflow:hidden` wrapper).

### 2. Layout shell

- **Desktop sidebar** (≥768px): fixed left, ~220px wide, dark surface, 5 nav items with icons + labels, active highlight using `--color-brand-primary`.
- **Mobile bottom nav** (<768px): fixed bottom, 4 tabs (Today / Schedule / Dashboards / More), iOS-style with `padding-bottom: env(safe-area-inset-bottom)`. Hidden sidebar on mobile.
- **Header**: sticky top, logo + greeting + day/date + theme toggle + manual Refresh button.

### 3. Section: Today

Five blocks, stacked:

- **Greeting strip** — "Good morning, Quintus" + day/date + last-manifest-fetch timestamp + Refresh button.
- **At-a-glance KPI row** — 4 numbers computed from `schedule_manifest.json`:
  - Jobs OK (count of `heartbeat_status == "fresh"` with `last_run.ok == true`)
  - Jobs Failed (count of `last_run.ok == false`)
  - Stale (count of `heartbeat_status == "stale"`)
  - Next run in (humanized delta to the earliest `next_run`)
- **Issues card** — hidden when empty. Lists failures and stale heartbeats, sorted by severity. Each row → tap to jump to that task's expanded view in Schedule.
- **Information Insights** — uses the existing `INFO_INSIGHT_DATA` array verbatim — same constant name, same shape — so the memory rule `feedback_information_insight_workflow.md` (append-entry workflow) continues to work unchanged. Any existing `<!--AUTO:key-->...<!--/AUTO-->` markers from `feedback_dashboard_auto_markers.md` that point at index.html must be preserved with the same names, or the auto-update scripts that target them have to be repointed before swap.
- **Manifest freshness banner** — when fetch failed: yellow banner with "Manifest unreachable — showing data from {timestamp}".

### 4. Section: Schedule

- **Filter chip row** at top: `All` · `Failing` · `Today` · followed by one chip per agent (multi-select; chips toggle).
- **Agent groups** — collapsible, sorted by agent name. Group header shows: `<AGENT NAME> · N jobs · X fresh · Y stale · Z failed` with status pill colour-coded.
- **Task rows** inside each group: name · status badge (`fresh`/`stale`/`failed`/`never_run`) · "last run 12m ago" · "next run in 4h"
- **Tap a row** → inline expand showing:
  - `schedule_summary`
  - Last 5 entries from `history`
  - `log_path` (with copy button)
  - `last_run.summary` (if present)
  - Quick link to a placeholder "View log" action (opens file:// URL — best-effort)

### 5. Section: Dashboards

A card grid (`auto-fit, minmax(280px, 1fr)`). Each card:

- Icon or thumbnail (use the dashboard's logo or a Lucide-style SVG)
- Title (e.g. "KPI Sales Dashboard")
- One-line description
- Optional "updated 2h ago" (when the dashboard owns a status JSON we can probe; otherwise omitted)
- "Open ↗" button → opens the dashboard URL in a new tab

Initial card list (from `reference_dashboards_inventory.md` memory):
- KPI Sales Dashboard
- PULSE Leaderboard
- PULSE Scorecard
- HAVEN Clocking
- E-Commerce
- Merchandising Calendar
- Store Health
- Rep KPI dashboards (composite link)
- Sales Geo Map

Filter chips: by owning agent.

### 6. Section: Reports

A list (not cards — reports are documents, not visual). Each row:

- Title (e.g. "Friday Sales Meeting")
- Agent owner
- Cadence (e.g. "Weekly · Friday 09:00")
- Last regenerated date (when known from the schedule manifest)
- "Open" action — opens the file or generation script's output

Initial list seeded from `reference_reports_inventory.md` memory; an entry is added every time a new standing report is built (per the existing convention).

### 7. Section: Agents

8 cards in a grid (3-column on desktop, 1-column on mobile):

- APEX (coordinator) · HAVEN · PRISM · STRIKER · SIGMA · BLAZE · VAULT · PULSE · FLASH

Each card:

- Agent name (Barlow Condensed, uppercase)
- One-line tagline (from the agent profile memory entries)
- Slash command (e.g. `/haven`) shown in a code chip
- Owned counts: `X scripts · Y dashboards · Z reports · W tasks` (computed live from cross-referencing the inline AGENTS constant against DASHBOARDS, REPORTS, and the loaded schedule manifest)
- Tap → expand inline with the cross-referenced item list

### 8. Theme toggle

Existing 4-button bar from the design system. Defaults to `theme-dark` per CLAUDE.md rule. Stored in `localStorage.oly-theme`. Pre-paint script in `<head>` to avoid flash on load.

---

## Data shapes

### Inline JS constants (in `index-v2.html`)

```js
const DASHBOARDS = [
  { id: 'kpi',         title: 'KPI Sales Dashboard',   agent: 'PRISM',   url: 'https://flomaticauto.github.io/olympic-paints-kpi/', desc: 'MTD sales, rep performance, debtors' },
  { id: 'pulse-board', title: 'PULSE Leaderboard',     agent: 'PULSE',   url: 'https://olympic-paints-pulse-web.vercel.app/leaderboard', desc: 'Daily rep leaderboard' },
  // ... etc.
];

const REPORTS = [
  { id: 'friday-sales',     title: 'Friday Sales Meeting',  agent: 'STRIKER', cadence: 'Weekly · Fri 09:00', job_id: 'olympicpaints-friday-sales-meeting' },
  // ... etc.
];

const AGENTS = [
  { id: 'APEX',    name: 'APEX',    tagline: 'Coordinator — routes all tasks',    slash: '/apex',    owns: { scripts: [], dashboards: [], reports: [], task_ids: [] } },
  { id: 'HAVEN',   name: 'HAVEN',   tagline: 'HR & People — clocking, JDs',       slash: '/haven',   owns: { task_ids: ['haven-clocking-report-daily'] } },
  // ... etc.
];

// Name kept as INFO_INSIGHT_DATA for backwards compatibility with the
// "add to information insight" append-entry workflow.
const INFO_INSIGHT_DATA = [
  // identical shape and constant name to the existing one in index.html
];
```

The `owns` field on each agent uses `task_ids` (matching `job_id` in `schedule_manifest.json`) so the cross-reference at render time is a simple set lookup.

### `data/schedule_manifest.json` (already produced)

Schema defined by sub-project #1. The Control Tower consumes the existing structure — no changes required.

---

## Error handling

| Scenario | Behaviour |
|---|---|
| `schedule_manifest.json` 404 / network error on initial load | Yellow banner: "Manifest unreachable — schedule data unavailable". KPI row shows `—` placeholders. Schedule section shows the failure state but renders agent group headers as placeholders. Other sections work normally. |
| Subsequent manual refresh fails | Banner: "Refresh failed — still showing data from {prev timestamp}". Last-good data retained in memory. |
| Manifest JSON malformed | Treated as fetch failure. Console error for diagnosis. |
| Unknown agent in manifest (not in `AGENTS` const) | Render under a synthetic "Unclassified" group. Don't break. |
| User in offline mode | Banner. Other sections still navigable. |
| Theme not in `localStorage` | Falls back to `theme-dark`. |

---

## Mobile specifics

- Viewport: `width=device-width, initial-scale=1, viewport-fit=cover`
- Breakpoint: 768px. Below this, sidebar hidden, bottom-nav shown.
- Bottom nav: fixed position, full width, 4 tabs (Today · Schedule · Dashboards · More), respect `env(safe-area-inset-bottom)`.
- Section header sticky inside main panel.
- Tap targets ≥ 44×44px (iOS guideline).
- Active section highlighted on bottom nav with `--color-brand-primary` underline.
- "More" tab opens a half-sheet drawer with Reports / Agents links.
- Card grids: 1 column below 480px, 2 columns 480–768px, 3+ on desktop.

---

## Testing

- **Visual regression**: open in Chrome at 390×844 (iPhone 14 Pro), 1280×800, 1920×1080. All 4 themes. Verify no horizontal scroll, sticky header behaves, theme toggle persists across reloads.
- **Data-shape robustness**:
  - Empty manifest (`{ "tasks": [] }`) — Today section shows zeros; Schedule shows "No scheduled tasks".
  - Manifest with unknown agent — task lands in "Unclassified" group.
  - Manifest with malformed `last_run.summary` — render rest, omit summary.
- **Manual-refresh smoke test**:
  - Click Refresh while page is open, confirm spinner indicator and updated freshness timestamp.
  - Simulate fetch failure (DevTools offline) → confirm banner appears and last-good data remains.
- **Theme switching**: cycle through Light → Dark → Brand → Navy. Reload page after each. Verify theme persists.
- **Mobile manual smoke**:
  - Bottom nav switches between Today / Schedule / Dashboards / More.
  - "More" drawer opens and is dismissible.
  - Tap a task row in Schedule, expand works, tap again to collapse.
- **Accessibility**: visible focus rings, 4.5:1 contrast for body text, tab order through nav → sections → cards.

---

## Rollout plan

| Phase | Action | Gate |
|---|---|---|
| 1 | Build `index-v2.html` end-to-end. All 5 sections functional with seed data. | Local file rendering matches the design across all 4 themes + mobile/desktop. |
| 2 | Commit and push. `index-v2.html` lives alongside the current `index.html` at a temporary URL. | Quintus opens both side-by-side, confirms parity + improvements. |
| 3 | Single commit performs the swap: rename `index.html` → `index-snapshot.html.bak`, rename `index-v2.html` → `index.html`. | Live root URL serves the Control Tower. |
| 4 | After 1 week of use without issues, delete `index-snapshot.html.bak`. Update `updates.html` to redirect to the new page (or delete and remove all references). | Old surfaces decommissioned. |

---

## Out of scope (explicitly)

- A backend service or build pipeline. Page is hand-authored static HTML.
- An admin / edit UI. Insights and other inline data are edited via the existing markup-edit workflow.
- Real-time task triggering. Read-only surface.
- Sub-project #2 (separate Agent Registry JSON). Agent data stays inline in this iteration; can be externalized later without changing the UI.
- Mobile push notifications.
- Cross-device sync of theme/scroll state beyond `localStorage`.

## Dependencies

- `schedule_manifest.json` (sub-project #1) — already in production.
- `Olympic Paints Logo Digital.jpg` — accessed via the existing `logo.jpg` adjacent to `index.html` (the build script for sub-project #1 already copies it; the new page uses the same file).
- Olympic Paints design system tokens (verbatim from `CLAUDE.md`).
- Modern browser (last-2 evergreen versions). No IE / pre-Chromium-Edge support needed.

## Open questions (deferred to implementation plan)

- Exact icon set for nav items and dashboard cards. Likely inline SVG (Lucide-style) for consistency. Decided at implementation time.
- Whether to add a "Search" affordance across all sections — deferred until the page is in use and a need is observed.
- Final wording of the greeting strip ("Good morning, Quintus" vs date-only header) — implementation-time aesthetic call.

## Hand-off

This is the last of the 3 sub-projects in the original Olympic Paints management platform decomposition. After this ships, sub-project #2 (Agent Registry as a separate JSON) can be picked up incrementally — the UI's inline `AGENTS` constant becomes the seed for `agents_manifest.json` with no UI changes required.
