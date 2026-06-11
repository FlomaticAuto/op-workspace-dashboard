 # Mobile-Readiness Pass — All Olympic Paints Dashboards

**Date:** 2026-05-15
**Owner:** Quintus (review) / Claude (implementation)
**Goal:** Every Olympic Paints dashboard renders correctly on phones (375–414 px) and feels like a native app — without breaking the desktop layout.

---

## Scope

All dashboards across two hosting platforms. Worked in this priority order:

**Group 1 — Front doors**
- `op-workspace-dashboard/index.html` (Vercel)
- `op-workspace-dashboard/portal.html` (Vercel)
- Staff Portal (GH Pages: `olympic-paints-staff-portal`)

**Group 2 — Field-use, rep-facing**
- PULSE web (Vercel, Next.js 16: `olympic-paints-pulse-web`)
- PULSE Leaderboard (GH Pages, also at `op-workspace-dashboard/pulse/`)
- PULSE Scorecard (also at `op-workspace-dashboard/pulse/scorecard/`)

**Group 3 — Management**
- KPI Sales Dashboard (`op-workspace-dashboard/kpi/{ac,ap,bv,np,bm}/`)
- CSO Insights (`op-workspace-dashboard/cso/`)
- E-Commerce (`op-workspace-dashboard/ecommerce/`)
- Store Health (`op-workspace-dashboard/store-health/`)

**Group 4 — Field + reference + admin**
- Merchandising Calendar (Vercel: `olympic-paints-merchandising-calendar`)
- Merchandising Impact (`op-workspace-dashboard/merchandising/`)
- Geo Map (Vercel: `olympic-paints-geo-map` + `olympic-paints-geo-mobile`)
- HAVEN Clocking (`op-workspace-dashboard/clocking/`)
- Forms Admin (Vercel: `olympic-paints-forms-admin`)
- Odoo Walkthroughs (GH Pages: `olympic-paints-odoo-walkthroughs`)

---

## Global mobile principles (apply to every dashboard)

These are rules every page gets. Per-page bespoke layout decisions go on top.

### Breakpoints
```
≥ 1100 px   desktop (existing layout untouched)
769–1099 px tablet (column collapse, existing behavior fine)
≤ 768 px    mobile (app shell kicks in)
≤ 480 px    small mobile (further padding/font tweaks)
```

### Required `<head>` additions on every page
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0D0D0B">
```

### Safe-area handling (iPhone notch / Android nav)
- Body padding uses `env(safe-area-inset-*)` on mobile
- Bottom nav sits above `env(safe-area-inset-bottom)`
- Sticky header respects `env(safe-area-inset-top)`

### Tap targets
- Minimum 44 × 44 px (iOS HIG)
- Buttons / links inside data tables: 36 × 36 px is acceptable
- Spacing between adjacent tap targets: ≥ 8 px

### Typography on mobile
- Body 15 px (down from 14 desktop is fine — readability matters more)
- Hero / page title: 28 px on mobile (down from 40–56 desktop)
- KPI numbers: 24–32 px on mobile (down from 28–48)
- Eyebrows, labels: keep tracking, drop to 10 px

### Scroll behavior
- `-webkit-overflow-scrolling: touch` on any horizontally scrolling container (tables, tab bars)
- Sticky header `position: sticky; top: 0` not `fixed` — avoids iOS Safari's URL bar wobble
- Bottom nav `position: fixed; bottom: 0` with `padding-bottom: env(safe-area-inset-bottom)`

---

## App-shell pattern (mobile only)

```
┌─────────────────────────┐
│ ☰  Page Title       ⋯   │  ← sticky header, 56 px tall
├─────────────────────────┤
│                         │
│  Card (full-bleed,      │
│  edge-to-edge, 12 px    │
│  side padding only)     │
│                         │
│  Card                   │
│                         │
│  Card                   │
│                         │
├─────────────────────────┤
│  ⌂   📊   👥   ⚙        │  ← bottom tab bar, 56 px + safe-area
└─────────────────────────┘
```

- Hide the desktop top navbar at ≤ 768 px
- Show a compact sticky header with the page title + optional menu/back button
- Show a bottom tab bar with 3–5 primary destinations per dashboard (chosen per-dashboard)
- Cards become full-bleed (no max-width, 12 px side padding)
- All multi-column grids collapse to a single column

### Bottom tab bar markup (canonical)
```html
<nav class="oly-mobile-tabs" aria-label="Primary">
  <a href="..." class="active"><svg>...</svg><span>Home</span></a>
  <a href="..."><svg>...</svg><span>KPIs</span></a>
  <a href="..."><svg>...</svg><span>Team</span></a>
  <a href="..."><svg>...</svg><span>More</span></a>
</nav>
```

```css
.oly-mobile-tabs { display: none; }
@media (max-width: 768px) {
  .oly-mobile-tabs {
    display: grid;
    grid-template-columns: repeat(var(--n,4), 1fr);
    position: fixed; left: 0; right: 0; bottom: 0;
    background: var(--color-surface-elevated);
    border-top: 1px solid var(--color-border-default);
    padding: 8px 0 calc(8px + env(safe-area-inset-bottom));
    z-index: 100;
  }
  .oly-mobile-tabs a {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    padding: 6px 4px;
    color: var(--color-text-secondary);
    text-decoration: none;
    font: 600 10px/1 var(--font-display);
    text-transform: uppercase; letter-spacing: 0.08em;
    min-height: 44px;
  }
  .oly-mobile-tabs a.active { color: var(--color-brand-primary); }
  .oly-mobile-tabs svg { width: 22px; height: 22px; }
  body { padding-bottom: calc(72px + env(safe-area-inset-bottom)); }
}
```

### Sticky compact header (canonical)
```html
<header class="oly-mobile-header">
  <button class="back" aria-label="Back">‹</button>
  <h1>Page Title</h1>
  <button class="menu" aria-label="Menu">⋯</button>
</header>
```

```css
.oly-mobile-header { display: none; }
@media (max-width: 768px) {
  .oly-mobile-header {
    display: grid;
    grid-template-columns: 44px 1fr 44px;
    align-items: center;
    position: sticky; top: 0;
    height: calc(56px + env(safe-area-inset-top));
    padding-top: env(safe-area-inset-top);
    background: var(--color-surface-elevated);
    border-bottom: 1px solid var(--color-border-default);
    z-index: 90;
  }
  .oly-mobile-header h1 {
    font: 800 16px/1 var(--font-display);
    text-transform: uppercase; letter-spacing: 0.06em;
    text-align: center; margin: 0;
    color: var(--color-text-primary);
  }
  .oly-mobile-header button {
    background: none; border: 0;
    color: var(--color-text-primary);
    font-size: 22px;
    min-width: 44px; min-height: 44px;
  }
  .desktop-nav, .theme-bar { display: none; }
}
```

---

## Per-dashboard workflow (loop for each page)

For each dashboard, in priority order:

1. **Audit** — read the current HTML, document what's there:
   - What's the desktop layout?
   - What media queries exist?
   - What's broken on mobile right now?
   - What charts / tables / forms are present?

2. **Design** — draft the bespoke mobile layout:
   - Which 3–5 sections become bottom tabs (or scroll-only if better)?
   - Which cards stack first?
   - Which tables become horizontal scrollers vs. card lists?
   - Any data hidden on mobile (rare — only if completely irrelevant)?
   - Present design to user for per-page approval.

3. **Implement** — edit the HTML / Python build script:
   - Add the four required `<head>` meta tags
   - Inject the global mobile CSS block (above)
   - Add the per-page bottom nav markup with chosen sections
   - Add the per-page sticky header markup
   - Add per-page mobile tweaks for tables, charts, forms

4. **Preview** — push to a Vercel preview URL (or a feature branch on GH Pages):
   - Send the URL to user
   - User checks on phone
   - Iterate if needed

5. **Promote** — merge / push to production
   - Confirm live URL
   - Tick the dashboard off in todo list
   - Move to next dashboard

---

## Tables on mobile (decision rule)

Tables are the main unsolved layout problem. Per-dashboard decision rule:

- **≤ 4 columns:** stack as cards, one per row, label-value pairs
- **5–8 columns:** keep as table, wrap in `overflow-x: auto; -webkit-overflow-scrolling: touch`, freeze first column with `position: sticky; left: 0`
- **> 8 columns:** card-per-row with primary fields visible, expandable for the rest

## Charts on mobile (decision rule)

Charts already use Chart.js with `responsive: true`. Confirm each chart's container:
- `width: 100%`
- Min height 220 px
- Legend repositioned to bottom
- Tooltip enabled (touch fires it)
- For bar charts with many categories, allow horizontal scroll instead of squeezing

## Forms on mobile (decision rule)

- Inputs full width, font-size ≥ 16 px (prevents iOS zoom on focus)
- Labels above, not beside
- Submit button full width, 48 px tall, sticky at bottom of form on long forms

---

## Risk + mitigation

| Risk | Mitigation |
|---|---|
| Breaking desktop layout while adding mobile | All mobile rules wrapped in `@media (max-width: 768px)` |
| Bottom nav covering content on Android Chrome (no safe-area) | `env(safe-area-inset-bottom, 0)` defaults to 0 — works fine |
| iOS Safari URL bar shrinking page | Use `position: sticky` not `fixed` for header; bottom nav uses `fixed` (URL bar doesn't affect bottom) |
| Charts not resizing on orientation change | Chart.js handles this; just confirm `responsive: true` is on |
| Per-page approval loop dragging on | Group similar pages (5 KPI rep dashboards = 1 design, 5 implementations) |

---

## Out of scope

- Redesigning desktop layouts
- Adding new features
- Touching the 3 non-Olympic Vercel projects (`timion-intranet`, `soley-briyan-mauritius`, `trade-craft1`)
- Changing data sources or build pipelines
- Anything beyond visible mobile rendering

---

## Order of execution

1. **op-workspace-dashboard/index.html** (workspace dashboard)
2. **op-workspace-dashboard/portal.html** (portal directory)
3. **olympic-paints-staff-portal** (front-of-house)
4. **olympic-paints-pulse-web** (Next.js — different stack, gets its own design pass)
5. **op-workspace-dashboard/pulse/** + **/pulse/scorecard/**
6. **op-workspace-dashboard/kpi/{ac,ap,bv,np,bm}/** (5 sister pages, single design)
7. **op-workspace-dashboard/cso/**
8. **op-workspace-dashboard/ecommerce/**
9. **op-workspace-dashboard/store-health/**
10. **olympic-paints-merchandising-calendar** (Vercel)
11. **op-workspace-dashboard/merchandising/**
12. **olympic-paints-geo-map** + **olympic-paints-geo-mobile** (review whether mobile twin still needed)
13. **op-workspace-dashboard/clocking/**
14. **olympic-paints-forms-admin**
15. **olympic-paints-odoo-walkthroughs** (GH Pages, separate repo)
