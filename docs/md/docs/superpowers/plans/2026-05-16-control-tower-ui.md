# Olympic Paints Control Tower UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single static HTML page (`workspace-dashboard/index-v2.html`) that becomes Olympic Paints' operational front door — replacing the current `index.html` and `updates.html`. Five sections (Today · Schedule · Dashboards · Reports · Agents) consume `schedule_manifest.json` live, with inline JS constants for the more static data.

**Architecture:** Hand-authored static HTML + vanilla JS, no framework, no build step. Sidebar nav on desktop, bottom-tab nav on mobile. Olympic Paints design system (4-theme tokens, Barlow fonts, real logo). The page lives at `workspace-dashboard/index-v2.html` during development, then a single rename swap promotes it to `index.html` and archives the old one as `index-snapshot.html.bak`.

**Tech Stack:** HTML5, vanilla CSS (Olympic Paints token system), vanilla JS (ES2020+), Google Fonts (Barlow + Barlow Condensed). No bundler. No NPM. No test framework — pure functions can be exercised via `?test=1` query param which runs in-page console assertions.

**Spec:** `docs/superpowers/specs/2026-05-16-control-tower-ui-design.md`

**Working directory:** `C:\Users\quint\workspace-dashboard\`
**Working branch:** `control-tower-ui` (created in Task 1)

---

## File Structure

**Create:**
- `C:\Users\quint\workspace-dashboard\index-v2.html` — the entire UI (one file)

**Modify (only in the final swap task):**
- Rename `C:\Users\quint\workspace-dashboard\index.html` → `index-snapshot.html.bak`
- Rename `C:\Users\quint\workspace-dashboard\index-v2.html` → `index.html`

**Output files consumed (already exist):**
- `data/schedule_manifest.json` — produced hourly by sub-project #1
- `logo.jpg` — already present at the workspace-dashboard root

---

## Section A — Scaffold

### Task 1: Create branch and HTML skeleton with theme system

**Files:**
- Create: `index-v2.html`

- [ ] **Step 1: Create the feature branch**

```powershell
Set-Location C:\Users\quint\workspace-dashboard
git checkout master
git pull origin master
git checkout -b control-tower-ui
git branch --show-current
```

Expected output: `control-tower-ui`

- [ ] **Step 2: Write the skeleton with the full CSS token block from CLAUDE.md**

Create `C:\Users\quint\workspace-dashboard\index-v2.html`:

```html
<!DOCTYPE html>
<html lang="en" class="theme-dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Olympic Control Tower</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<!-- Pre-paint theme restore -->
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>
/* ── RAW DESIGN TOKENS ─────────────────────────────────────────── */
:root {
  --_y50:#FEF9E0; --_y100:#FDF0A0; --_y200:#FAE04D;
  --_y400:#F5C400; --_y600:#D4A800; --_y800:#A88000; --_y900:#6A5000;
  --_n50:#E8EFF8; --_n100:#B8CCE8; --_n300:#6B9ED0;
  --_n500:#2D6BA8; --_n700:#1A3D6E; --_n900:#0D2040; --_n950:#071022;
  --_g0:#FFFFFF; --_g50:#F7F6F3; --_g100:#E8E7E2; --_g200:#C8C7C0;
  --_g400:#949390; --_g600:#5C5B58; --_g800:#2E2E2C;
  --_g900:#1A1A18; --_g950:#0D0D0B;
  --_teal:#2D8C7A; --_teal-light:#C8EDE7; --_teal-dark:#1a5c50;
  --_terra:#C97A3A; --_coral:#E86060; --_coral-light:#FDDCDC;
  --_pink:#E87BAD; --_violet:#9B7DBF; --_sage:#7A8C55; --_ink:#5C6B7A;
  --font-display:'Barlow Condensed',sans-serif;
  --font-body:'Barlow',sans-serif;
  --r-sm:4px; --r-md:8px; --r-lg:12px; --r-xl:16px; --r-pill:50px;
}
.theme-light {
  color-scheme:light;
  --color-surface-page:var(--_g50); --color-surface-base:var(--_g0);
  --color-surface-elevated:var(--_g0); --color-surface-sunken:var(--_g100);
  --color-surface-overlay:rgba(0,0,0,0.04);
  --color-surface-brand:var(--_y400); --color-surface-secondary:var(--_n700);
  --color-text-primary:var(--_g950); --color-text-secondary:var(--_g600);
  --color-text-tertiary:var(--_g400); --color-text-on-brand:var(--_g950);
  --color-text-on-navy:var(--_g0);
  --color-brand-primary:var(--_y400); --color-brand-hover:var(--_y600);
  --color-brand-secondary:var(--_n700); --color-brand-accent:var(--_y400);
  --color-border-subtle:var(--_g100); --color-border-default:var(--_g200);
  --color-border-strong:var(--_g400); --color-border-brand:var(--_y400);
  --color-success-bg:#EDF7F5; --color-success-fg:var(--_teal-dark); --color-success-bd:var(--_teal);
  --color-warning-bg:var(--_y50); --color-warning-fg:var(--_y900); --color-warning-bd:var(--_y600);
  --color-danger-bg:#FEF2F2; --color-danger-fg:#C0392B; --color-danger-bd:var(--_coral);
  --color-info-bg:var(--_n50); --color-info-fg:var(--_n700); --color-info-bd:var(--_n500);
  --color-neutral-bg:var(--_g100); --color-neutral-fg:var(--_g600); --color-neutral-bd:var(--_g400);
  --shadow-sm:0 1px 3px rgba(0,0,0,0.08); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg:0 10px 30px rgba(0,0,0,0.10); --shadow-brand:0 4px 16px rgba(245,196,0,0.20);
}
.theme-dark {
  color-scheme:dark;
  --color-surface-page:var(--_g950); --color-surface-base:var(--_g900);
  --color-surface-elevated:var(--_g800); --color-surface-sunken:var(--_g950);
  --color-surface-overlay:rgba(255,255,255,0.04);
  --color-surface-brand:var(--_y400); --color-surface-secondary:var(--_n700);
  --color-text-primary:var(--_g100); --color-text-secondary:var(--_g400);
  --color-text-tertiary:var(--_g600); --color-text-on-brand:var(--_g950);
  --color-text-on-navy:var(--_g0);
  --color-brand-primary:var(--_y400); --color-brand-hover:var(--_y200);
  --color-brand-secondary:var(--_n700); --color-brand-accent:var(--_y400);
  --color-border-subtle:rgba(255,255,255,0.06); --color-border-default:rgba(255,255,255,0.10);
  --color-border-strong:rgba(255,255,255,0.20); --color-border-brand:var(--_y400);
  --color-success-bg:rgba(45,140,122,0.12); --color-success-fg:var(--_teal-light); --color-success-bd:rgba(45,140,122,0.30);
  --color-warning-bg:rgba(245,196,0,0.10); --color-warning-fg:var(--_y200); --color-warning-bd:rgba(245,196,0,0.25);
  --color-danger-bg:rgba(232,96,96,0.12); --color-danger-fg:var(--_coral-light); --color-danger-bd:rgba(232,96,96,0.30);
  --color-info-bg:rgba(26,61,110,0.30); --color-info-fg:var(--_n100); --color-info-bd:rgba(107,158,208,0.30);
  --color-neutral-bg:rgba(255,255,255,0.05); --color-neutral-fg:var(--_g400); --color-neutral-bd:rgba(255,255,255,0.10);
  --shadow-sm:0 1px 3px rgba(0,0,0,0.40); --shadow-md:0 4px 12px rgba(0,0,0,0.40);
  --shadow-lg:0 10px 30px rgba(0,0,0,0.50); --shadow-brand:0 4px 20px rgba(245,196,0,0.15);
}
.theme-brand {
  color-scheme:light;
  --color-surface-page:var(--_y400); --color-surface-base:var(--_y200);
  --color-surface-elevated:var(--_y50); --color-surface-sunken:var(--_y600);
  --color-surface-overlay:rgba(0,0,0,0.05);
  --color-surface-brand:var(--_y400); --color-surface-secondary:var(--_g950);
  --color-text-primary:var(--_g950); --color-text-secondary:var(--_y900);
  --color-text-tertiary:var(--_y800); --color-text-on-brand:var(--_g950);
  --color-text-on-navy:var(--_g0);
  --color-brand-primary:var(--_g950); --color-brand-hover:var(--_n700);
  --color-brand-secondary:var(--_n700); --color-brand-accent:var(--_g950);
  --color-border-subtle:rgba(0,0,0,0.08); --color-border-default:rgba(0,0,0,0.14);
  --color-border-strong:rgba(0,0,0,0.25); --color-border-brand:var(--_g950);
  --color-success-bg:rgba(45,140,122,0.12); --color-success-fg:var(--_teal-dark); --color-success-bd:var(--_teal);
  --color-warning-bg:rgba(0,0,0,0.08); --color-warning-fg:var(--_y900); --color-warning-bd:var(--_y900);
  --color-danger-bg:rgba(232,96,96,0.12); --color-danger-fg:#C0392B; --color-danger-bd:var(--_coral);
  --color-info-bg:rgba(26,61,110,0.10); --color-info-fg:var(--_n900); --color-info-bd:var(--_n700);
  --color-neutral-bg:rgba(0,0,0,0.06); --color-neutral-fg:var(--_y900); --color-neutral-bd:rgba(0,0,0,0.15);
  --shadow-sm:0 1px 3px rgba(0,0,0,0.12); --shadow-md:0 4px 12px rgba(0,0,0,0.14);
  --shadow-lg:0 10px 30px rgba(0,0,0,0.18); --shadow-brand:0 4px 16px rgba(0,0,0,0.15);
}
.theme-navy {
  color-scheme:dark;
  --color-surface-page:var(--_n950); --color-surface-base:var(--_n900);
  --color-surface-elevated:var(--_n700); --color-surface-sunken:var(--_n950);
  --color-surface-overlay:rgba(255,255,255,0.04);
  --color-surface-brand:var(--_y400); --color-surface-secondary:var(--_n700);
  --color-text-primary:var(--_g0); --color-text-secondary:var(--_n100);
  --color-text-tertiary:var(--_n300); --color-text-on-brand:var(--_g950);
  --color-text-on-navy:var(--_g0);
  --color-brand-primary:var(--_y400); --color-brand-hover:var(--_y200);
  --color-brand-secondary:var(--_n500); --color-brand-accent:var(--_y400);
  --color-border-subtle:rgba(107,158,208,0.12); --color-border-default:rgba(107,158,208,0.20);
  --color-border-strong:rgba(107,158,208,0.35); --color-border-brand:var(--_y400);
  --color-success-bg:rgba(45,140,122,0.15); --color-success-fg:var(--_teal-light); --color-success-bd:rgba(45,140,122,0.35);
  --color-warning-bg:rgba(245,196,0,0.12); --color-warning-fg:var(--_y200); --color-warning-bd:rgba(245,196,0,0.30);
  --color-danger-bg:rgba(232,96,96,0.14); --color-danger-fg:var(--_coral-light); --color-danger-bd:rgba(232,96,96,0.35);
  --color-info-bg:rgba(45,107,168,0.20); --color-info-fg:var(--_n100); --color-info-bd:rgba(107,158,208,0.35);
  --color-neutral-bg:rgba(255,255,255,0.05); --color-neutral-fg:var(--_n300); --color-neutral-bd:rgba(255,255,255,0.12);
  --shadow-sm:0 1px 3px rgba(0,0,0,0.50); --shadow-md:0 4px 12px rgba(0,0,0,0.50);
  --shadow-lg:0 10px 30px rgba(0,0,0,0.60); --shadow-brand:0 4px 20px rgba(245,196,0,0.18);
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--color-surface-page);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  min-height: 100vh;
}

/* Theme bar — temporary at top until Task 2 moves it into header */
.theme-bar {
  display: flex; gap: 4px;
  padding: 8px 16px;
  background: var(--color-surface-secondary);
}
.theme-bar button {
  background: transparent;
  color: var(--color-text-on-navy);
  border: 1px solid rgba(255,255,255,0.2);
  padding: 4px 10px;
  border-radius: var(--r-sm);
  font-family: var(--font-display); font-weight: 700; font-size: 11px;
  letter-spacing: 0.06em; text-transform: uppercase;
  cursor: pointer;
}
.theme-bar button.active { background: var(--color-brand-primary); color: var(--color-text-on-brand); border-color: var(--color-brand-primary); }

.boot-marker { padding: 24px; text-align: center; font-family: var(--font-display); font-size: 24px; font-weight: 800; letter-spacing: 0.06em; }
</style>
</head>
<body>
  <div class="theme-bar">
    <button onclick="olyTheme('theme-light',this)">Light</button>
    <button onclick="olyTheme('theme-dark',this)" class="active">Dark</button>
    <button onclick="olyTheme('theme-brand',this)">Brand</button>
    <button onclick="olyTheme('theme-navy',this)">Navy</button>
  </div>

  <div class="boot-marker">OLYMPIC CONTROL TOWER — SCAFFOLD OK</div>

<script>
const OLY_THEMES = ['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t, btn){
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme', t);
  document.querySelectorAll('.theme-bar button').forEach(b => b.classList.toggle('active', b === btn));
}
// Sync the visible active button on load if user has a saved theme
(function(){
  const saved = localStorage.getItem('oly-theme');
  if (!saved) return;
  document.querySelectorAll('.theme-bar button').forEach((b, i) => {
    b.classList.toggle('active', OLY_THEMES[i] === saved);
  });
})();
</script>
</body>
</html>
```

- [ ] **Step 3: Verify in browser**

Open `C:\Users\quint\workspace-dashboard\index-v2.html` in Chrome.

Expected:
- Page loads with dark theme (off-black background, light text).
- "OLYMPIC CONTROL TOWER — SCAFFOLD OK" rendered in uppercase Barlow Condensed.
- Theme bar shows 4 buttons; "Dark" is highlighted yellow.
- Click each theme button — surface and text colours change correctly. Yellow accent on Light/Dark/Navy; full yellow background on Brand.
- Reload page after clicking — last-selected theme persists.

- [ ] **Step 4: Commit**

```powershell
Set-Location C:\Users\quint\workspace-dashboard
git add index-v2.html
git commit -m "feat(control-tower): HTML5 skeleton with 4-theme token system and theme toggle"
git log --oneline -1
```

Expected: commit lands on `control-tower-ui` branch with a hash visible.

---

### Task 2: Header strip with logo, greeting, day/date, refresh button

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the placeholder body content with the header strip**

In `index-v2.html`:

Replace `<div class="theme-bar">…</div>` and `<div class="boot-marker">…</div>` with:

```html
  <header class="app-header">
    <div class="header-left">
      <div class="logo-wrap">
        <img src="logo.jpg" alt="Olympic Paints" width="40" height="40">
      </div>
      <div class="header-text">
        <div class="greet" id="greet">Good day</div>
        <div class="day-date" id="day-date">—</div>
      </div>
    </div>
    <div class="header-right">
      <button class="refresh-btn" id="refresh-btn" title="Refresh schedule data">
        <span class="refresh-icon">↻</span>
        <span class="refresh-label">Refresh</span>
      </button>
      <div class="theme-bar">
        <button onclick="olyTheme('theme-light',this)">Light</button>
        <button onclick="olyTheme('theme-dark',this)" class="active">Dark</button>
        <button onclick="olyTheme('theme-brand',this)">Brand</button>
        <button onclick="olyTheme('theme-navy',this)">Navy</button>
      </div>
    </div>
  </header>
  <div class="freshness-bar" id="freshness-bar">
    <span id="freshness-text">Manifest not yet loaded</span>
  </div>
```

- [ ] **Step 2: Add the corresponding CSS**

In the `<style>` block, append (after `.theme-bar button.active`):

```css
.app-header {
  position: sticky; top: 0; z-index: 10;
  background: var(--color-surface-base);
  border-bottom: 1px solid var(--color-border-default);
  padding: 12px 20px;
  display: flex; justify-content: space-between; align-items: center;
  gap: 16px;
}
.header-left { display: flex; align-items: center; gap: 14px; }
.logo-wrap {
  width: 40px; height: 40px;
  border-radius: 50%; overflow: hidden;
  flex-shrink: 0;
}
.logo-wrap img { display: block; width: 100%; height: 100%; object-fit: cover; }
.header-text .greet {
  font-family: var(--font-display); font-weight: 800;
  font-size: 18px; line-height: 1.1;
  color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.03em;
}
.header-text .day-date {
  font-family: var(--font-body); font-weight: 500;
  font-size: 12px; color: var(--color-text-secondary);
  margin-top: 2px;
}
.header-right { display: flex; align-items: center; gap: 10px; }
.refresh-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-md);
  padding: 6px 12px;
  font-family: var(--font-body); font-weight: 500; font-size: 12px;
  cursor: pointer;
}
.refresh-btn:hover { border-color: var(--color-border-brand); }
.refresh-btn.spinning .refresh-icon { animation: spin 0.6s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.refresh-icon { display: inline-block; font-size: 14px; }
.freshness-bar {
  background: var(--color-surface-sunken);
  border-bottom: 1px solid var(--color-border-subtle);
  padding: 6px 20px;
  font-size: 11px; color: var(--color-text-secondary);
  letter-spacing: 0.04em;
}
.freshness-bar.error {
  background: var(--color-warning-bg);
  color: var(--color-warning-fg);
  border-bottom-color: var(--color-warning-bd);
}

@media (max-width: 560px) {
  .header-text .day-date { display: none; }
  .refresh-label { display: none; }
  .theme-bar button { padding: 4px 6px; font-size: 10px; }
}
```

- [ ] **Step 3: Add greeting and date helper at bottom of `<script>` block**

Append to the inline `<script>`:

```javascript
function updateGreeting(){
  const h = new Date().getHours();
  const part = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
  document.getElementById('greet').textContent = `Good ${part}, Quintus`;
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const d = new Date();
  const dayStr = `${days[d.getDay()]}, ${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
  document.getElementById('day-date').textContent = dayStr;
}
updateGreeting();
```

- [ ] **Step 4: Verify in browser**

Reload `index-v2.html`.

Expected:
- Sticky header at top showing the Olympic Paints logo (yellow circle), "Good morning, Quintus" / "Good afternoon, Quintus" / "Good evening, Quintus" depending on time of day, then "Sunday, 17 May 2026" (or whatever today's date is) underneath.
- Right side: a `↻ Refresh` button + the 4 theme buttons.
- Below the header: a thin freshness bar reading "Manifest not yet loaded".
- Resize browser narrower (< 560px): the date line disappears, the "Refresh" word collapses to just the icon, theme buttons shrink.
- Reload: theme still persists. Time-of-day greeting matches current hour.

- [ ] **Step 5: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): sticky header with logo, greeting, refresh button, freshness bar"
```

---

## Section B — Layout shell

### Task 3: Sidebar (desktop) + main panel grid

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the layout shell after the freshness bar**

After `</div>` of `freshness-bar`, before `<script>`, insert:

```html
  <div class="app-body">
    <aside class="sidebar" id="sidebar">
      <nav>
        <button class="nav-item active" data-section="today" onclick="showSection('today', this)">
          <span class="nav-icon" aria-hidden="true">●</span><span class="nav-label">Today</span>
        </button>
        <button class="nav-item" data-section="schedule" onclick="showSection('schedule', this)">
          <span class="nav-icon" aria-hidden="true">▦</span><span class="nav-label">Schedule</span>
        </button>
        <button class="nav-item" data-section="dashboards" onclick="showSection('dashboards', this)">
          <span class="nav-icon" aria-hidden="true">▤</span><span class="nav-label">Dashboards</span>
        </button>
        <button class="nav-item" data-section="reports" onclick="showSection('reports', this)">
          <span class="nav-icon" aria-hidden="true">▥</span><span class="nav-label">Reports</span>
        </button>
        <button class="nav-item" data-section="agents" onclick="showSection('agents', this)">
          <span class="nav-icon" aria-hidden="true">◇</span><span class="nav-label">Agents</span>
        </button>
      </nav>
    </aside>
    <main class="main">
      <section class="section-pane active" id="section-today">
        <h1 class="section-title">Today</h1>
        <p class="section-placeholder">Today content lands here in Task 9-11.</p>
      </section>
      <section class="section-pane" id="section-schedule">
        <h1 class="section-title">Schedule</h1>
        <p class="section-placeholder">Schedule content lands here in Task 12-14.</p>
      </section>
      <section class="section-pane" id="section-dashboards">
        <h1 class="section-title">Dashboards</h1>
        <p class="section-placeholder">Dashboards content lands here in Task 15.</p>
      </section>
      <section class="section-pane" id="section-reports">
        <h1 class="section-title">Reports</h1>
        <p class="section-placeholder">Reports content lands here in Task 16.</p>
      </section>
      <section class="section-pane" id="section-agents">
        <h1 class="section-title">Agents</h1>
        <p class="section-placeholder">Agents content lands here in Task 17.</p>
      </section>
    </main>
  </div>
```

- [ ] **Step 2: Add the CSS for the shell**

In `<style>`, append after the freshness-bar rules:

```css
.app-body {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: calc(100vh - 110px);
}
.sidebar {
  background: var(--color-surface-base);
  border-right: 1px solid var(--color-border-default);
  padding: 16px 12px;
}
.sidebar nav { display: flex; flex-direction: column; gap: 4px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  background: transparent;
  color: var(--color-text-secondary);
  border: none;
  border-radius: var(--r-md);
  padding: 10px 14px;
  font-family: var(--font-display); font-weight: 700; font-size: 13px;
  letter-spacing: 0.04em; text-transform: uppercase;
  cursor: pointer;
  text-align: left;
}
.nav-item:hover { background: var(--color-surface-overlay); color: var(--color-text-primary); }
.nav-item.active {
  background: var(--color-brand-primary);
  color: var(--color-text-on-brand);
}
.nav-icon { font-size: 14px; opacity: 0.85; width: 16px; text-align: center; }
.main {
  padding: 24px;
  overflow-x: hidden;
}
.section-pane { display: none; }
.section-pane.active { display: block; }
.section-title {
  font-family: var(--font-display); font-weight: 900;
  font-size: 32px; line-height: 1.1;
  color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.02em;
  margin: 0 0 16px;
}
.section-placeholder {
  color: var(--color-text-tertiary);
  font-style: italic;
  font-size: 14px;
}
```

- [ ] **Step 3: Add the `showSection` function in the inline `<script>`**

Append to the `<script>` block:

```javascript
function showSection(name, btn){
  document.querySelectorAll('.section-pane').forEach(p => p.classList.remove('active'));
  const pane = document.getElementById('section-' + name);
  if (pane) pane.classList.add('active');
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  // Also sync mobile bottom-nav (defined in Task 4)
  document.querySelectorAll('.bottom-nav-item').forEach(b => {
    b.classList.toggle('active', b.dataset.section === name);
  });
}
```

- [ ] **Step 4: Verify in browser**

Reload at desktop width (≥768px).

Expected:
- Left sidebar 220px wide with 5 nav buttons: Today / Schedule / Dashboards / Reports / Agents.
- "Today" highlighted yellow (active).
- Main panel shows "Today" heading + placeholder text.
- Click each nav item → section content swaps, the clicked item gets the yellow highlight.

- [ ] **Step 5: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): desktop sidebar + main panel layout with 5 section switcher"
```

---

### Task 4: Mobile bottom nav + responsive breakpoint

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the bottom-nav HTML after the closing `</main>` but inside `.app-body`**

In `index-v2.html`, just before `</div>` that closes `.app-body`, insert:

```html
      <nav class="bottom-nav">
        <button class="bottom-nav-item active" data-section="today" onclick="showSection('today', findSidebarBtn('today'))">
          <span class="bn-icon" aria-hidden="true">●</span><span class="bn-label">Today</span>
        </button>
        <button class="bottom-nav-item" data-section="schedule" onclick="showSection('schedule', findSidebarBtn('schedule'))">
          <span class="bn-icon" aria-hidden="true">▦</span><span class="bn-label">Schedule</span>
        </button>
        <button class="bottom-nav-item" data-section="dashboards" onclick="showSection('dashboards', findSidebarBtn('dashboards'))">
          <span class="bn-icon" aria-hidden="true">▤</span><span class="bn-label">Dashboards</span>
        </button>
        <button class="bottom-nav-item" data-section="more" onclick="openMoreDrawer()">
          <span class="bn-icon" aria-hidden="true">⋯</span><span class="bn-label">More</span>
        </button>
      </nav>
      <div class="more-drawer" id="more-drawer" onclick="if(event.target===this)closeMoreDrawer()">
        <div class="more-sheet">
          <h3>More</h3>
          <button class="more-item" onclick="showSection('reports', findSidebarBtn('reports')); closeMoreDrawer()">
            <span class="nav-icon">▥</span> Reports
          </button>
          <button class="more-item" onclick="showSection('agents', findSidebarBtn('agents')); closeMoreDrawer()">
            <span class="nav-icon">◇</span> Agents
          </button>
        </div>
      </div>
```

- [ ] **Step 2: Add the responsive CSS**

In `<style>`, append:

```css
.bottom-nav { display: none; }
.more-drawer { display: none; }

@media (max-width: 767px) {
  .app-body {
    grid-template-columns: 1fr;
    padding-bottom: calc(56px + env(safe-area-inset-bottom));
  }
  .sidebar { display: none; }
  .main { padding: 16px; }
  .section-title { font-size: 26px; }

  .bottom-nav {
    display: flex;
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 20;
    background: var(--color-surface-base);
    border-top: 1px solid var(--color-border-default);
    padding-bottom: env(safe-area-inset-bottom);
  }
  .bottom-nav-item {
    flex: 1;
    background: transparent;
    color: var(--color-text-secondary);
    border: none;
    padding: 10px 4px;
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    font-family: var(--font-body); font-weight: 500; font-size: 10px;
    cursor: pointer;
    min-height: 56px;
    position: relative;
  }
  .bottom-nav-item.active { color: var(--color-brand-primary); }
  .bottom-nav-item.active::after {
    content: '';
    position: absolute; top: 0; left: 25%; right: 25%; height: 2px;
    background: var(--color-brand-primary);
  }
  .bn-icon { font-size: 18px; }
  .bn-label { letter-spacing: 0.03em; }

  .more-drawer.open {
    display: flex; align-items: flex-end;
    position: fixed; inset: 0; z-index: 30;
    background: rgba(0,0,0,0.45);
  }
  .more-sheet {
    background: var(--color-surface-base);
    border-top-left-radius: var(--r-xl);
    border-top-right-radius: var(--r-xl);
    padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
    width: 100%;
    display: flex; flex-direction: column; gap: 8px;
  }
  .more-sheet h3 {
    font-family: var(--font-display); font-weight: 800; font-size: 18px;
    color: var(--color-text-primary);
    text-transform: uppercase; letter-spacing: 0.04em;
    margin: 0 0 8px;
  }
  .more-item {
    display: flex; align-items: center; gap: 12px;
    background: var(--color-surface-elevated);
    color: var(--color-text-primary);
    border: 1px solid var(--color-border-default);
    border-radius: var(--r-md);
    padding: 14px;
    font-family: var(--font-display); font-weight: 700; font-size: 14px;
    text-transform: uppercase; letter-spacing: 0.04em;
    cursor: pointer;
    text-align: left;
  }
}
```

- [ ] **Step 3: Add the helper JS**

Append to inline `<script>`:

```javascript
function findSidebarBtn(name){
  return document.querySelector(`.nav-item[data-section="${name}"]`);
}
function openMoreDrawer(){
  document.getElementById('more-drawer').classList.add('open');
  document.querySelectorAll('.bottom-nav-item').forEach(b => b.classList.toggle('active', b.dataset.section === 'more'));
}
function closeMoreDrawer(){
  document.getElementById('more-drawer').classList.remove('open');
  // Restore the highlight on whichever section is actually showing
  const activeSection = document.querySelector('.section-pane.active');
  if (activeSection) {
    const name = activeSection.id.replace('section-', '');
    document.querySelectorAll('.bottom-nav-item').forEach(b => b.classList.toggle('active', b.dataset.section === name));
  }
}
```

- [ ] **Step 4: Verify in browser**

Open Chrome DevTools, toggle device toolbar, set to iPhone 14 Pro (390×844).

Expected:
- Sidebar disappears; bottom nav appears with 4 tabs: Today / Schedule / Dashboards / More.
- "Today" highlighted (yellow color + yellow bar above).
- Tap Schedule / Dashboards — section switches, highlight moves.
- Tap More — half-sheet drawer slides up from bottom with Reports + Agents buttons.
- Tap Reports → drawer closes, Reports section shows. Tap More again, choose Agents → Agents section shows.
- Tap outside the drawer → drawer closes.
- Resize to ≥ 768px → bottom nav disappears, sidebar reappears.

- [ ] **Step 5: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): mobile bottom-nav + more drawer with responsive breakpoint at 768px"
```

---

## Section C — Data constants

### Task 5: Seed DASHBOARDS, REPORTS, AGENTS, INFO_INSIGHT_DATA constants

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the constants at the top of the inline `<script>` block**

Find the existing `<script>` block (the one starting with `const OLY_THEMES = …`). Just above `const OLY_THEMES`, insert:

```javascript
// ── DATA CONSTANTS ─────────────────────────────────────────────
// Updated by humans / build scripts. Schedule-related data is fetched
// live from data/schedule_manifest.json — not stored here.

const DASHBOARDS = [
  { id: 'kpi',             title: 'KPI Sales Dashboard',  agent: 'PRISM',   url: 'https://flomaticauto.github.io/olympic-paints-kpi/',                                                          desc: 'MTD sales, rep performance, debtors aging.' },
  { id: 'pulse-board',     title: 'PULSE Leaderboard',    agent: 'PULSE',   url: 'https://olympic-paints-pulse-web.vercel.app/leaderboard',                                                     desc: 'Daily rep leaderboard — plan adherence, visits, leads.' },
  { id: 'pulse-scorecard', title: 'PULSE Scorecard',      agent: 'PULSE',   url: 'https://olympic-paints-pulse-web.vercel.app/scorecard',                                                       desc: 'Bi-weekly rep scorecards.' },
  { id: 'haven-clocking',  title: 'HAVEN Clocking',       agent: 'HAVEN',   url: 'https://flomaticauto.github.io/olympic-paints-clocking/',                                                     desc: 'Yesterday, daily, weekly, missed clock-outs.' },
  { id: 'ecommerce',       title: 'E-Commerce',           agent: 'FLASH',   url: 'https://flomaticauto.github.io/olympic-paints-ecommerce/',                                                    desc: 'WooCommerce orders, revenue, top products.' },
  { id: 'merch-calendar',  title: 'Merchandising Calendar', agent: 'STRIKER', url: 'https://op-merch-calendar.vercel.app/',                                                                     desc: 'Booked merchandising visits, mobile-first.' },
  { id: 'store-health',    title: 'Store Health',         agent: 'STRIKER', url: 'https://flomaticauto.github.io/olympic-paints-store-health/',                                                 desc: 'Account-level visit + sales health.' },
  { id: 'rep-kpi',         title: 'Rep KPI Dashboards',   agent: 'PRISM',   url: 'https://flomaticauto.github.io/workspace-dashboard/kpi/ac/',                                                  desc: 'Per-rep activity heatmaps + monthly revenue.' },
  { id: 'cso-insights',    title: 'CSO Insights',         agent: 'PRISM',   url: 'https://flomaticauto.github.io/olympic-paints-cso-insights/',                                                 desc: 'Strategic intelligence briefings.' }
];

const REPORTS = [
  { id: 'friday-sales',       title: 'Friday Sales Meeting',     agent: 'STRIKER', cadence: 'Weekly · Fri 09:00', job_id: 'olympicpaints-friday-sales-meeting' },
  { id: 'vehicle-weekly',     title: 'Vehicle Report Weekly',    agent: 'SIGMA',   cadence: 'Weekly · Mon 09:00', job_id: 'vehicle-report-weekly' },
  { id: 'workspace-health',   title: 'Workspace Health Report',  agent: 'PRISM',   cadence: 'Weekly · Fri 16:00', job_id: 'olympicpaints-workspace-health-report' },
  { id: 'cso-intelligence',   title: 'CSO Intelligence Data',    agent: 'PRISM',   cadence: 'Weekly · Sun 06:00', job_id: 'cso-intelligence-data' }
];

const AGENTS = [
  { id: 'APEX',    name: 'APEX',    tagline: 'Coordinator — routes all tasks',                  slash: '/apex',    task_ids: [] },
  { id: 'HAVEN',   name: 'HAVEN',   tagline: 'HR & People — clocking, JDs, onboarding',         slash: '/haven',   task_ids: ['haven-clocking-report-daily'] },
  { id: 'PRISM',   name: 'PRISM',   tagline: 'Analytics — QuickSight, formulas, YoY',           slash: '/prism',   task_ids: ['build-schedule-manifest','olympicpaints-kpi-dashboard-update','olympicpaints-sales-dashboard-refresh','olympicpaints-workspace-health-report','cso-intelligence-data'] },
  { id: 'STRIKER', name: 'STRIKER', tagline: 'Sales & CRM — Zoho, quotes, stockists',           slash: '/striker', task_ids: ['olympic-paints-zoho-meetings-pull','olympicpaints-friday-sales-meeting','zoho-leads-pull','vehicle-report-health-check'] },
  { id: 'SIGMA',   name: 'SIGMA',   tagline: 'Operations — SOPs, dispatch, factory',            slash: '/sigma',   task_ids: ['olympic-portal-trigger-server','vehicle-report-weekly'] },
  { id: 'BLAZE',   name: 'BLAZE',   tagline: 'Marketing — social, copy, campaigns',             slash: '/blaze',   task_ids: [] },
  { id: 'VAULT',   name: 'VAULT',   tagline: 'Admin & Filing — PARA, inbox, Notion docs',       slash: '/vault',   task_ids: ['sync-claude-todos','olympic-paints-kaizen-daily-sync','vault-meeting-extraction-daily','meeting-minutes-extractor'] },
  { id: 'PULSE',   name: 'PULSE',   tagline: 'Sales & Ops Manager — daily ack, leaderboard',    slash: '/pulse',   task_ids: [] },
  { id: 'FLASH',   name: 'FLASH',   tagline: 'E-Commerce — OneDayOnly, orders',                 slash: '/flash',   task_ids: ['olympicpaints-emailecommercedashboard'] }
];

// Name kept as INFO_INSIGHT_DATA for backwards compatibility with the
// "add to information insight" workflow that appends to this array in index.html.
const INFO_INSIGHT_DATA = [
  // Existing insights from the current index.html will be merged in during the final swap (Task 18).
];
```

- [ ] **Step 2: Verify the constants parse and are accessible**

Reload `index-v2.html` in Chrome. Open DevTools → Console.

Run each of these and confirm output:

```javascript
console.log('Dashboards:', DASHBOARDS.length);
console.log('Reports:', REPORTS.length);
console.log('Agents:', AGENTS.length);
console.log('Sample dashboard:', DASHBOARDS[0].title);
console.log('PRISM owns N tasks:', AGENTS.find(a => a.id === 'PRISM').task_ids.length);
```

Expected output:
- Dashboards: 9
- Reports: 4
- Agents: 9
- Sample dashboard: KPI Sales Dashboard
- PRISM owns N tasks: 5

- [ ] **Step 3: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): seed DASHBOARDS, REPORTS, AGENTS, INFO_INSIGHT_DATA constants"
```

---

## Section D — Manifest fetch + refresh

### Task 6: Fetch schedule_manifest.json with last-good cache and error banner

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the manifest state and fetch logic**

Append to the inline `<script>` block:

```javascript
// ── MANIFEST STATE ─────────────────────────────────────────────
const MANIFEST_STATE = {
  data: null,           // last-good manifest
  loadedAt: null,       // Date of last successful fetch
  error: null,          // last error message
  inFlight: false,
};

async function fetchManifest(){
  if (MANIFEST_STATE.inFlight) return;
  MANIFEST_STATE.inFlight = true;
  setRefreshSpinning(true);
  try {
    const res = await fetch('data/schedule_manifest.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    if (!json || !Array.isArray(json.tasks)) throw new Error('malformed manifest');
    MANIFEST_STATE.data = json;
    MANIFEST_STATE.loadedAt = new Date();
    MANIFEST_STATE.error = null;
  } catch (err) {
    MANIFEST_STATE.error = err.message || String(err);
    console.warn('fetchManifest failed:', MANIFEST_STATE.error);
  } finally {
    MANIFEST_STATE.inFlight = false;
    setRefreshSpinning(false);
    renderFreshness();
    renderAll();
  }
}

function renderFreshness(){
  const bar = document.getElementById('freshness-bar');
  const text = document.getElementById('freshness-text');
  if (MANIFEST_STATE.error && MANIFEST_STATE.data) {
    bar.classList.add('error');
    text.textContent = `Refresh failed (${MANIFEST_STATE.error}) — showing data from ${formatTimestamp(MANIFEST_STATE.loadedAt)}`;
  } else if (MANIFEST_STATE.error) {
    bar.classList.add('error');
    text.textContent = `Manifest unreachable: ${MANIFEST_STATE.error}`;
  } else if (MANIFEST_STATE.data) {
    bar.classList.remove('error');
    const generated = MANIFEST_STATE.data.generated_at || 'unknown';
    text.textContent = `Manifest generated ${generated} · loaded ${formatTimestamp(MANIFEST_STATE.loadedAt)}`;
  } else {
    bar.classList.remove('error');
    text.textContent = 'Loading manifest...';
  }
}

function formatTimestamp(d){
  if (!d) return '—';
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function setRefreshSpinning(on){
  const btn = document.getElementById('refresh-btn');
  if (btn) btn.classList.toggle('spinning', !!on);
}

// Stub — real implementation lands in Task 9
function renderAll(){
  // intentionally empty until each section's renderer is added
}
```

- [ ] **Step 2: Wire the refresh button + initial load**

Append:

```javascript
document.getElementById('refresh-btn').addEventListener('click', fetchManifest);
fetchManifest();  // initial load
```

- [ ] **Step 3: Verify success path in browser**

The page expects `data/schedule_manifest.json` to be reachable. Serve the directory via Python and open through HTTP (file:// won't allow fetch).

```powershell
Set-Location C:\Users\quint\workspace-dashboard
python -m http.server 8765
```

Open `http://localhost:8765/index-v2.html` in Chrome. DevTools → Console.

Expected:
- Refresh button briefly shows a spinning ↻ icon.
- Freshness bar shows: "Manifest generated 2026-05-16T... · loaded HH:MM:SS".
- No errors in console.
- Run `MANIFEST_STATE.data.tasks.length` — should print ~17.

Click the Refresh button manually. Expected: spinner shows, freshness timestamp updates.

- [ ] **Step 4: Verify error path**

In DevTools → Network tab, toggle "Offline". Click Refresh.

Expected:
- Freshness bar turns yellow/warning, shows "Refresh failed (Failed to fetch) — showing data from HH:MM:SS".
- Previous tasks still in `MANIFEST_STATE.data`.

Toggle Offline back off. Reload page from scratch with Offline ON.

Expected:
- Freshness bar yellow, "Manifest unreachable: Failed to fetch".
- `MANIFEST_STATE.data === null`.

- [ ] **Step 5: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): manifest fetch, refresh button, freshness bar, error handling with last-good cache"
```

---

## Section E — Today section

### Task 7: KPI row computing from manifest

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the Today section placeholder**

Find:

```html
<section class="section-pane active" id="section-today">
  <h1 class="section-title">Today</h1>
  <p class="section-placeholder">Today content lands here in Task 9-11.</p>
</section>
```

Replace with:

```html
<section class="section-pane active" id="section-today">
  <h1 class="section-title">Today</h1>
  <div class="kpi-row" id="today-kpis">
    <!-- Filled by renderTodayKpis() -->
  </div>
  <div class="today-issues" id="today-issues" hidden>
    <!-- Filled by renderTodayIssues() in Task 8 -->
  </div>
  <div class="today-insights" id="today-insights">
    <!-- Filled by renderInsights() in Task 8 -->
  </div>
</section>
```

- [ ] **Step 2: Add the KPI row CSS**

Append to `<style>`:

```css
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.kpi-card {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  padding: 16px;
}
.kpi-label {
  font-family: var(--font-body); font-weight: 500;
  font-size: 11px; color: var(--color-text-secondary);
  text-transform: uppercase; letter-spacing: 0.08em;
}
.kpi-number {
  font-family: var(--font-display); font-weight: 900;
  font-size: 36px; line-height: 1.05;
  color: var(--color-text-primary);
  margin-top: 6px;
}
.kpi-card.success .kpi-number { color: var(--color-success-fg); }
.kpi-card.warning .kpi-number { color: var(--color-warning-fg); }
.kpi-card.danger .kpi-number { color: var(--color-danger-fg); }
.kpi-empty .kpi-number { color: var(--color-text-tertiary); }

@media (max-width: 560px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .kpi-number { font-size: 28px; }
}
```

- [ ] **Step 3: Add the KPI compute + render logic**

Append to the `<script>`:

```javascript
function renderTodayKpis(){
  const el = document.getElementById('today-kpis');
  const tasks = MANIFEST_STATE.data ? MANIFEST_STATE.data.tasks : [];

  let ok = 0, failed = 0, stale = 0;
  for (const t of tasks){
    const hb = t.last_run;
    if (t.heartbeat_status === 'stale') stale++;
    if (hb && hb.ok === true) ok++;
    if (hb && hb.ok === false) failed++;
  }

  const next = computeNextRunDelta(tasks);

  el.innerHTML = `
    <div class="kpi-card success">
      <div class="kpi-label">Jobs OK</div>
      <div class="kpi-number">${tasks.length ? ok : '—'}</div>
    </div>
    <div class="kpi-card ${failed ? 'danger' : ''}">
      <div class="kpi-label">Jobs Failed</div>
      <div class="kpi-number">${tasks.length ? failed : '—'}</div>
    </div>
    <div class="kpi-card ${stale ? 'warning' : ''}">
      <div class="kpi-label">Stale</div>
      <div class="kpi-number">${tasks.length ? stale : '—'}</div>
    </div>
    <div class="kpi-card kpi-empty">
      <div class="kpi-label">Next run in</div>
      <div class="kpi-number">${next || '—'}</div>
    </div>
  `;
}

function computeNextRunDelta(tasks){
  if (!tasks || !tasks.length) return null;
  const now = Date.now();
  let earliest = null;
  for (const t of tasks){
    if (!t.next_run) continue;
    const ts = Date.parse(t.next_run.replace(' ', 'T'));
    if (isNaN(ts) || ts <= now) continue;
    if (earliest === null || ts < earliest) earliest = ts;
  }
  if (earliest === null) return null;
  return humanizeDelta(earliest - now);
}

function humanizeDelta(ms){
  if (ms < 0) return 'now';
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  if (h < 24) return rem ? `${h}h${rem}m` : `${h}h`;
  const d = Math.floor(h / 24);
  return `${d}d`;
}
```

- [ ] **Step 4: Wire `renderTodayKpis` into `renderAll`**

Find:

```javascript
function renderAll(){
  // intentionally empty until each section's renderer is added
}
```

Replace with:

```javascript
function renderAll(){
  renderTodayKpis();
}
```

- [ ] **Step 5: Verify**

Reload `http://localhost:8765/index-v2.html`.

Expected:
- 4 KPI cards on Today: Jobs OK · Jobs Failed · Stale · Next run in.
- Numbers populate from the real manifest (something like 2, 0, 0, "23m" or whatever).
- DevTools console: run `humanizeDelta(120000)` → returns `"2m"`. Run `humanizeDelta(3700000)` → returns `"1h1m"`. Run `humanizeDelta(90000000)` → returns `"1d"`.
- Tap a theme button → KPI cards still look correct on all themes.

- [ ] **Step 6: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Today KPI row with manifest-driven counters"
```

---

### Task 8: Today Issues card + Information Insights

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the CSS for the Issues card and Insights**

Append to `<style>`:

```css
.today-issues {
  background: var(--color-danger-bg);
  border: 1px solid var(--color-danger-bd);
  border-radius: var(--r-lg);
  padding: 16px;
  margin-bottom: 24px;
}
.today-issues h2 {
  font-family: var(--font-display); font-weight: 800;
  font-size: 16px; color: var(--color-danger-fg);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0 0 10px;
}
.today-issues ul { list-style: none; padding: 0; margin: 0; }
.today-issues li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0;
  border-top: 1px solid var(--color-danger-bd);
  font-family: var(--font-body); font-size: 13px;
  color: var(--color-text-primary);
  cursor: pointer;
}
.today-issues li:first-child { border-top: none; }
.today-issues .issue-meta { font-size: 11px; color: var(--color-text-secondary); }

.today-insights {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  padding: 16px;
}
.today-insights h2 {
  font-family: var(--font-display); font-weight: 800;
  font-size: 16px; color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0 0 12px;
}
.today-insights .insight {
  border-top: 1px solid var(--color-border-subtle);
  padding: 10px 0;
}
.today-insights .insight:first-of-type { border-top: none; }
.today-insights .insight-title {
  font-family: var(--font-body); font-weight: 600; font-size: 13px;
  color: var(--color-text-primary);
}
.today-insights .insight-body {
  font-family: var(--font-body); font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
.today-insights .insight-meta {
  font-size: 11px; color: var(--color-text-tertiary);
  margin-top: 4px;
}
.today-insights .insights-empty {
  font-size: 13px; color: var(--color-text-tertiary);
  font-style: italic;
}
```

- [ ] **Step 2: Add the render functions**

Append to `<script>`:

```javascript
function renderTodayIssues(){
  const wrap = document.getElementById('today-issues');
  const tasks = MANIFEST_STATE.data ? MANIFEST_STATE.data.tasks : [];
  const issues = [];
  for (const t of tasks){
    if (t.last_run && t.last_run.ok === false){
      issues.push({ task: t, kind: 'failed', text: 'Last run failed' });
    } else if (t.heartbeat_status === 'stale'){
      issues.push({ task: t, kind: 'stale', text: 'Heartbeat stale' });
    }
  }
  if (!issues.length){ wrap.hidden = true; wrap.innerHTML = ''; return; }
  wrap.hidden = false;
  wrap.innerHTML = `
    <h2>${issues.length} issue${issues.length === 1 ? '' : 's'} need attention</h2>
    <ul>
      ${issues.map(i => `
        <li onclick="jumpToScheduleTask('${escapeAttr(i.task.job_id)}')">
          <span><strong>${escapeHtml(i.task.name)}</strong> <span class="issue-meta">· ${escapeHtml(i.task.agent)}</span></span>
          <span class="issue-meta">${escapeHtml(i.text)}</span>
        </li>
      `).join('')}
    </ul>
  `;
}

function renderInsights(){
  const wrap = document.getElementById('today-insights');
  if (!INFO_INSIGHT_DATA.length){
    wrap.innerHTML = `<h2>Information Insights</h2><div class="insights-empty">No insights yet. Add one via the "add to information insight" workflow.</div>`;
    return;
  }
  wrap.innerHTML = `
    <h2>Information Insights</h2>
    ${INFO_INSIGHT_DATA.map(i => `
      <div class="insight">
        <div class="insight-title">${escapeHtml(i.title || '')}</div>
        <div class="insight-body">${escapeHtml(i.body || i.text || '')}</div>
        <div class="insight-meta">${escapeHtml(i.date || '')}</div>
      </div>
    `).join('')}
  `;
}

function escapeHtml(s){
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttr(s){ return escapeHtml(s); }

// Placeholder; real implementation in Task 11 jumps to schedule and expands the task.
function jumpToScheduleTask(jobId){
  showSection('schedule', findSidebarBtn('schedule'));
  console.log('jumpToScheduleTask:', jobId, '(expansion handled in Task 11)');
}
```

- [ ] **Step 3: Wire into renderAll**

Replace the existing `renderAll` body with:

```javascript
function renderAll(){
  renderTodayKpis();
  renderTodayIssues();
  renderInsights();
}
```

- [ ] **Step 4: Verify**

Reload `http://localhost:8765/index-v2.html`.

Expected:
- Today section shows: KPI row, then Information Insights card with "No insights yet..." (empty array seed).
- Issues card is hidden (no failed/stale tasks currently).
- DevTools console: temporarily inject a failure to verify:
  ```javascript
  MANIFEST_STATE.data.tasks[0].last_run = { ok: false };
  renderAll();
  ```
  Expected: Red Issues card appears with that task name. Click it → console logs "jumpToScheduleTask: ..." and the Schedule section becomes active.

- [ ] **Step 5: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Today Issues card and Information Insights renderer"
```

---

## Section F — Schedule section

### Task 9: Schedule filter chips + agent groups + task rows

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the Schedule section placeholder**

Find:

```html
<section class="section-pane" id="section-schedule">
  <h1 class="section-title">Schedule</h1>
  <p class="section-placeholder">Schedule content lands here in Task 12-14.</p>
</section>
```

Replace with:

```html
<section class="section-pane" id="section-schedule">
  <h1 class="section-title">Schedule</h1>
  <div class="chip-row" id="schedule-chips">
    <!-- Populated by renderScheduleChips() -->
  </div>
  <div class="agent-groups" id="agent-groups">
    <!-- Populated by renderScheduleGroups() -->
  </div>
</section>
```

- [ ] **Step 2: Add the CSS**

Append:

```css
.chip-row {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin-bottom: 16px;
}
.chip {
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-pill);
  padding: 6px 12px;
  font-family: var(--font-display); font-weight: 700; font-size: 11px;
  text-transform: uppercase; letter-spacing: 0.04em;
  cursor: pointer;
}
.chip.active {
  background: var(--color-brand-primary);
  color: var(--color-text-on-brand);
  border-color: var(--color-brand-primary);
}
.agent-group {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  margin-bottom: 12px;
  overflow: hidden;
}
.agent-group-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background: var(--color-surface-sunken);
}
.agent-group-header h3 {
  font-family: var(--font-display); font-weight: 800; font-size: 14px;
  color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0;
}
.agent-group-summary {
  font-size: 11px; color: var(--color-text-secondary);
}
.agent-tasks { display: none; }
.agent-group.open .agent-tasks { display: block; }
.agent-group.open .agent-group-caret { transform: rotate(90deg); }
.agent-group-caret { display: inline-block; transition: transform 0.15s ease; margin-right: 8px; }

.task-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  border-top: 1px solid var(--color-border-subtle);
  cursor: pointer;
}
.task-row:hover { background: var(--color-surface-overlay); }
.task-name {
  flex: 1;
  font-family: var(--font-body); font-weight: 500; font-size: 13px;
  color: var(--color-text-primary);
}
.task-meta {
  font-size: 11px; color: var(--color-text-secondary);
  font-family: var(--font-body);
  white-space: nowrap;
}
.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: var(--r-pill);
  font-family: var(--font-display); font-weight: 700; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.status-badge.fresh    { background: var(--color-success-bg); color: var(--color-success-fg); border: 1px solid var(--color-success-bd); }
.status-badge.stale    { background: var(--color-warning-bg); color: var(--color-warning-fg); border: 1px solid var(--color-warning-bd); }
.status-badge.failed   { background: var(--color-danger-bg);  color: var(--color-danger-fg);  border: 1px solid var(--color-danger-bd); }
.status-badge.never_run{ background: var(--color-neutral-bg); color: var(--color-neutral-fg); border: 1px solid var(--color-neutral-bd); }
.status-badge.missing  { background: var(--color-neutral-bg); color: var(--color-neutral-fg); border: 1px solid var(--color-neutral-bd); }

@media (max-width: 560px) {
  .task-meta.last-run { display: none; }
}
```

- [ ] **Step 3: Add the render logic**

Append to `<script>`:

```javascript
const FILTER_STATE = {
  group: 'all',   // 'all' | 'failing' | 'today'
  agents: new Set(),  // empty = no agent filter
};

function renderScheduleChips(){
  const el = document.getElementById('schedule-chips');
  const agents = Array.from(new Set((MANIFEST_STATE.data?.tasks || []).map(t => t.agent))).sort();
  const chips = [
    `<button class="chip ${FILTER_STATE.group === 'all' ? 'active' : ''}" onclick="setFilterGroup('all')">All</button>`,
    `<button class="chip ${FILTER_STATE.group === 'failing' ? 'active' : ''}" onclick="setFilterGroup('failing')">Failing</button>`,
    `<button class="chip ${FILTER_STATE.group === 'today' ? 'active' : ''}" onclick="setFilterGroup('today')">Today</button>`,
  ];
  for (const a of agents){
    chips.push(`<button class="chip ${FILTER_STATE.agents.has(a) ? 'active' : ''}" onclick="toggleAgentFilter('${escapeAttr(a)}')">${escapeHtml(a)}</button>`);
  }
  el.innerHTML = chips.join('');
}

function setFilterGroup(group){
  FILTER_STATE.group = group;
  renderScheduleChips();
  renderScheduleGroups();
}

function toggleAgentFilter(agent){
  if (FILTER_STATE.agents.has(agent)) FILTER_STATE.agents.delete(agent);
  else FILTER_STATE.agents.add(agent);
  renderScheduleChips();
  renderScheduleGroups();
}

function filteredTasks(){
  const tasks = MANIFEST_STATE.data?.tasks || [];
  return tasks.filter(t => {
    if (FILTER_STATE.group === 'failing'){
      if (!(t.heartbeat_status === 'stale' || (t.last_run && t.last_run.ok === false))) return false;
    }
    if (FILTER_STATE.group === 'today'){
      const next = t.next_run ? Date.parse(t.next_run.replace(' ', 'T')) : NaN;
      const todayEnd = new Date(); todayEnd.setHours(23,59,59,999);
      if (!(next && next <= todayEnd.getTime())) return false;
    }
    if (FILTER_STATE.agents.size && !FILTER_STATE.agents.has(t.agent)) return false;
    return true;
  });
}

function renderScheduleGroups(){
  const wrap = document.getElementById('agent-groups');
  const tasks = filteredTasks();
  if (!tasks.length){
    wrap.innerHTML = `<p class="section-placeholder">No tasks match the current filters.</p>`;
    return;
  }
  const byAgent = {};
  for (const t of tasks){
    if (!byAgent[t.agent]) byAgent[t.agent] = [];
    byAgent[t.agent].push(t);
  }
  const agentNames = Object.keys(byAgent).sort();
  wrap.innerHTML = agentNames.map(agent => renderAgentGroup(agent, byAgent[agent])).join('');
}

function renderAgentGroup(agent, tasks){
  const counts = tasks.reduce((acc, t) => {
    if (t.heartbeat_status === 'fresh') acc.fresh++;
    else if (t.heartbeat_status === 'stale') acc.stale++;
    if (t.last_run && t.last_run.ok === false) acc.failed++;
    return acc;
  }, { fresh: 0, stale: 0, failed: 0 });
  return `
    <div class="agent-group open" id="group-${escapeAttr(agent)}">
      <div class="agent-group-header" onclick="toggleGroup('${escapeAttr(agent)}')">
        <h3><span class="agent-group-caret">▶</span>${escapeHtml(agent)}</h3>
        <div class="agent-group-summary">${tasks.length} jobs · ${counts.fresh} fresh · ${counts.stale} stale · ${counts.failed} failed</div>
      </div>
      <div class="agent-tasks">
        ${tasks.map(renderTaskRow).join('')}
      </div>
    </div>
  `;
}

function toggleGroup(agent){
  document.getElementById('group-' + agent)?.classList.toggle('open');
}

function renderTaskRow(t){
  const last = t.last_run ? humanizeAgo(t.last_run.finished_at) : '—';
  const next = t.next_run ? humanizeAgo(t.next_run, true) : '—';
  const status = t.last_run && t.last_run.ok === false ? 'failed' : (t.heartbeat_status || 'never_run');
  return `
    <div class="task-row" data-job-id="${escapeAttr(t.job_id)}" onclick="toggleTaskExpand('${escapeAttr(t.job_id)}', this)">
      <span class="task-name">${escapeHtml(t.name)}</span>
      <span class="status-badge ${status}">${escapeHtml(status)}</span>
      <span class="task-meta last-run">last ${last}</span>
      <span class="task-meta next-run">next ${next}</span>
    </div>
  `;
}

function humanizeAgo(isoStr, future){
  if (!isoStr) return '—';
  const t = Date.parse(isoStr.replace(' ', 'T'));
  if (isNaN(t)) return '—';
  const diff = future ? t - Date.now() : Date.now() - t;
  if (diff < 0) return future ? 'now' : 'in future';
  return (future ? 'in ' : '') + humanizeDelta(diff) + (future ? '' : ' ago');
}

// Placeholder until Task 10
function toggleTaskExpand(jobId, row){
  console.log('toggleTaskExpand:', jobId, '(detail rendering in Task 10)');
}
```

- [ ] **Step 4: Wire into renderAll**

Update `renderAll`:

```javascript
function renderAll(){
  renderTodayKpis();
  renderTodayIssues();
  renderInsights();
  renderScheduleChips();
  renderScheduleGroups();
}
```

- [ ] **Step 5: Verify**

Reload `http://localhost:8765/index-v2.html`. Tap Schedule in the sidebar.

Expected:
- Filter chips: All (active), Failing, Today, then one chip per agent.
- Below: agent groups (FLASH, HAVEN, PRISM, etc.), each expanded by default.
- Each group header: agent name + summary like "5 jobs · 1 fresh · 0 stale · 0 failed".
- Each task row: name + status badge + "last 1m ago" + "next in 4h".
- Click an agent group header → group collapses (caret rotates).
- Click "Failing" chip → only failed/stale tasks shown. With current data, this should show empty placeholder.
- Click an agent chip (e.g. "PRISM") → only PRISM tasks shown. Click again to deselect.
- Click All → resets.
- Mobile view: "last X ago" column hidden; "next in X" stays.

- [ ] **Step 6: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Schedule section with filter chips and collapsible agent groups"
```

---

### Task 10: Task row expand details

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Add the CSS for the expanded row**

Append:

```css
.task-detail {
  display: none;
  padding: 16px;
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-surface-sunken);
  font-family: var(--font-body); font-size: 12px;
  color: var(--color-text-secondary);
}
.task-row.expanded + .task-detail { display: block; }
.task-detail h4 {
  font-family: var(--font-display); font-weight: 800; font-size: 12px;
  color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0 0 6px;
}
.task-detail .kv {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 4px 16px;
  margin-bottom: 12px;
}
.task-detail .kv dt { color: var(--color-text-tertiary); }
.task-detail .kv dd { margin: 0; color: var(--color-text-primary); word-break: break-all; }
.task-detail .history {
  display: grid;
  grid-template-columns: 1fr 60px 80px 50px;
  gap: 4px 12px;
  font-size: 11px;
}
.task-detail .history .h-head {
  font-family: var(--font-display); font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--color-text-tertiary);
}
.task-detail .ok-yes { color: var(--color-success-fg); }
.task-detail .ok-no  { color: var(--color-danger-fg); }
.task-detail .copy-btn {
  background: transparent; border: 1px solid var(--color-border-default);
  border-radius: var(--r-sm); padding: 2px 6px; cursor: pointer;
  font-size: 10px; color: var(--color-text-secondary);
  margin-left: 6px;
}
```

- [ ] **Step 2: Update `renderTaskRow` to emit a sibling detail div**

Replace the existing `renderTaskRow` function with:

```javascript
function renderTaskRow(t){
  const last = t.last_run ? humanizeAgo(t.last_run.finished_at) : '—';
  const next = t.next_run ? humanizeAgo(t.next_run, true) : '—';
  const status = t.last_run && t.last_run.ok === false ? 'failed' : (t.heartbeat_status || 'never_run');
  return `
    <div class="task-row" data-job-id="${escapeAttr(t.job_id)}" onclick="toggleTaskExpand('${escapeAttr(t.job_id)}', this)">
      <span class="task-name">${escapeHtml(t.name)}</span>
      <span class="status-badge ${status}">${escapeHtml(status)}</span>
      <span class="task-meta last-run">last ${last}</span>
      <span class="task-meta next-run">next ${next}</span>
    </div>
    <div class="task-detail" id="detail-${escapeAttr(t.job_id)}">
      ${renderTaskDetail(t)}
    </div>
  `;
}

function renderTaskDetail(t){
  const last = t.last_run || {};
  const hist = (t.history || []).slice(-5).reverse();
  const summary = last.summary && Object.keys(last.summary).length
    ? Object.entries(last.summary).map(([k,v]) => `<span><strong>${escapeHtml(k)}</strong>: ${escapeHtml(JSON.stringify(v))}</span>`).join(' · ')
    : '<span style="color:var(--color-text-tertiary)">none</span>';
  return `
    <h4>Details</h4>
    <dl class="kv">
      <dt>Schedule</dt><dd>${escapeHtml(t.schedule_summary || '—')}</dd>
      <dt>Next run</dt><dd>${escapeHtml(t.next_run || '—')}</dd>
      <dt>Last run</dt><dd>${escapeHtml(last.finished_at || '—')} (${last.duration_seconds != null ? last.duration_seconds + 's' : '—'})</dd>
      <dt>Exit code</dt><dd>${last.exit_code != null ? last.exit_code : '—'}</dd>
      <dt>Summary</dt><dd>${summary}</dd>
      <dt>Log path</dt><dd>${escapeHtml(last.log_path || '—')}<button class="copy-btn" onclick="event.stopPropagation();copyText('${escapeAttr(last.log_path || '')}')">copy</button></dd>
    </dl>
    <h4>History (last 5 runs)</h4>
    <div class="history">
      <span class="h-head">Started</span>
      <span class="h-head">Dur</span>
      <span class="h-head">Exit</span>
      <span class="h-head">OK</span>
      ${hist.length ? hist.map(h => `
        <span>${escapeHtml((h.started_at || '').replace('T',' ').slice(0,19))}</span>
        <span>${escapeHtml(String(h.duration_seconds != null ? h.duration_seconds + 's' : '—'))}</span>
        <span>${escapeHtml(String(h.exit_code != null ? h.exit_code : '—'))}</span>
        <span class="${h.ok ? 'ok-yes' : 'ok-no'}">${h.ok ? '✓' : '✗'}</span>
      `).join('') : `<span style="grid-column:1/-1;color:var(--color-text-tertiary);font-style:italic">no history yet</span>`}
    </div>
  `;
}

function toggleTaskExpand(jobId, row){
  row.classList.toggle('expanded');
}

function copyText(s){
  if (!s) return;
  navigator.clipboard.writeText(s).then(
    () => console.log('copied:', s),
    err => console.warn('copy failed:', err)
  );
}

// Update jumpToScheduleTask to expand the target task
function jumpToScheduleTask(jobId){
  showSection('schedule', findSidebarBtn('schedule'));
  // Wait for render, then find and expand the row
  setTimeout(() => {
    const row = document.querySelector(`.task-row[data-job-id="${jobId}"]`);
    if (row){
      row.classList.add('expanded');
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, 50);
}
```

- [ ] **Step 3: Verify**

Reload. Schedule section.

Expected:
- Click any task row → expands to show: Details (Schedule, Next run, Last run, Exit code, Summary, Log path with copy button), then History grid of last 5 runs (or "no history yet" for never-run tasks).
- For `sync-claude-todos` (the pilot): should show history with at least 1 entry with green ✓.
- Click the copy button on Log path → no error, console shows "copied: C:\..." (clipboard).
- Click row again → collapses.
- Inject test failure: `MANIFEST_STATE.data.tasks[0].last_run = {ok:false}; renderAll();` → Issues card appears in Today. Click the issue → Schedule section opens AND the failed task is expanded and scrolled into view.

- [ ] **Step 4: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): task row expand with details, history, log copy, and jump-from-issues"
```

---

## Section G — Dashboards / Reports / Agents

### Task 11: Dashboards card grid

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the Dashboards section placeholder**

Find:

```html
<section class="section-pane" id="section-dashboards">
  <h1 class="section-title">Dashboards</h1>
  <p class="section-placeholder">Dashboards content lands here in Task 15.</p>
</section>
```

Replace with:

```html
<section class="section-pane" id="section-dashboards">
  <h1 class="section-title">Dashboards</h1>
  <div class="chip-row" id="dashboards-chips"></div>
  <div class="card-grid" id="dashboards-grid"></div>
</section>
```

- [ ] **Step 2: Add the CSS**

Append:

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}
.dash-card {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  padding: 16px;
  display: flex; flex-direction: column; gap: 8px;
  transition: border-color 0.15s ease, transform 0.15s ease;
}
.dash-card:hover {
  border-color: var(--color-border-brand);
  transform: translateY(-2px);
}
.dash-card h3 {
  font-family: var(--font-display); font-weight: 800;
  font-size: 16px; color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0;
}
.dash-card .agent-pill {
  align-self: flex-start;
  background: var(--color-info-bg);
  color: var(--color-info-fg);
  border: 1px solid var(--color-info-bd);
  border-radius: var(--r-pill);
  padding: 2px 8px;
  font-family: var(--font-display); font-weight: 700; font-size: 10px;
  text-transform: uppercase; letter-spacing: 0.06em;
}
.dash-card .desc {
  font-family: var(--font-body); font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
}
.dash-card .open-link {
  margin-top: auto;
  align-self: flex-start;
  background: var(--color-brand-primary);
  color: var(--color-text-on-brand);
  border: none;
  border-radius: var(--r-md);
  padding: 8px 14px;
  font-family: var(--font-display); font-weight: 700; font-size: 12px;
  text-transform: uppercase; letter-spacing: 0.04em;
  text-decoration: none;
  cursor: pointer;
}
```

- [ ] **Step 3: Add the render logic**

Append to `<script>`:

```javascript
const DASH_FILTER = { agents: new Set() };

function renderDashboardsChips(){
  const el = document.getElementById('dashboards-chips');
  const agents = Array.from(new Set(DASHBOARDS.map(d => d.agent))).sort();
  el.innerHTML = [
    `<button class="chip ${DASH_FILTER.agents.size === 0 ? 'active' : ''}" onclick="clearDashFilter()">All</button>`,
    ...agents.map(a => `<button class="chip ${DASH_FILTER.agents.has(a) ? 'active' : ''}" onclick="toggleDashFilter('${escapeAttr(a)}')">${escapeHtml(a)}</button>`)
  ].join('');
}

function clearDashFilter(){ DASH_FILTER.agents.clear(); renderDashboardsChips(); renderDashboardsGrid(); }
function toggleDashFilter(a){
  if (DASH_FILTER.agents.has(a)) DASH_FILTER.agents.delete(a);
  else DASH_FILTER.agents.add(a);
  renderDashboardsChips(); renderDashboardsGrid();
}

function renderDashboardsGrid(){
  const el = document.getElementById('dashboards-grid');
  const list = DASH_FILTER.agents.size
    ? DASHBOARDS.filter(d => DASH_FILTER.agents.has(d.agent))
    : DASHBOARDS;
  if (!list.length){ el.innerHTML = `<p class="section-placeholder">No dashboards match.</p>`; return; }
  el.innerHTML = list.map(d => `
    <div class="dash-card">
      <span class="agent-pill">${escapeHtml(d.agent)}</span>
      <h3>${escapeHtml(d.title)}</h3>
      <p class="desc">${escapeHtml(d.desc || '')}</p>
      <a class="open-link" href="${escapeAttr(d.url)}" target="_blank" rel="noopener">Open ↗</a>
    </div>
  `).join('');
}
```

- [ ] **Step 4: Wire into renderAll**

Update `renderAll`:

```javascript
function renderAll(){
  renderTodayKpis();
  renderTodayIssues();
  renderInsights();
  renderScheduleChips();
  renderScheduleGroups();
  renderDashboardsChips();
  renderDashboardsGrid();
}
```

- [ ] **Step 5: Verify**

Reload. Click Dashboards (sidebar).

Expected:
- 9 dashboard cards in a responsive grid.
- Each card: agent pill (e.g. "PRISM"), title, description, yellow "Open ↗" button.
- Click "Open ↗" → opens dashboard in a new tab. (Don't actually visit — just verify the link resolves; you can right-click → Copy link address.)
- Filter chips at top: All + one per unique agent. Click "PRISM" → only PRISM cards shown. Click again to deselect.
- Mobile: cards stack to single column.

- [ ] **Step 6: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Dashboards card grid with agent filter chips"
```

---

### Task 12: Reports list

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the Reports section placeholder**

Find:

```html
<section class="section-pane" id="section-reports">
  <h1 class="section-title">Reports</h1>
  <p class="section-placeholder">Reports content lands here in Task 16.</p>
</section>
```

Replace with:

```html
<section class="section-pane" id="section-reports">
  <h1 class="section-title">Reports</h1>
  <div class="report-list" id="reports-list"></div>
</section>
```

- [ ] **Step 2: Add the CSS**

Append:

```css
.report-list {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.report-row {
  display: grid;
  grid-template-columns: 1fr 100px 130px 80px;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--color-border-subtle);
  font-family: var(--font-body); font-size: 13px;
}
.report-row:first-child { border-top: none; }
.report-row .r-title {
  font-weight: 600;
  color: var(--color-text-primary);
}
.report-row .r-meta {
  font-size: 11px;
  color: var(--color-text-secondary);
}
.report-row .r-last {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}
.report-row .r-open {
  background: transparent;
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-sm);
  padding: 4px 10px;
  font-family: var(--font-display); font-weight: 700; font-size: 10px;
  color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  cursor: pointer;
}

@media (max-width: 560px) {
  .report-row {
    grid-template-columns: 1fr 80px;
    grid-template-areas: 'title open' 'meta meta' 'last last';
    gap: 4px 12px;
  }
  .report-row .r-title { grid-area: title; }
  .report-row .r-open  { grid-area: open; justify-self: end; }
  .report-row .r-meta  { grid-area: meta; }
  .report-row .r-last  { grid-area: last; }
}
```

- [ ] **Step 3: Add the render logic**

Append:

```javascript
function renderReports(){
  const el = document.getElementById('reports-list');
  if (!REPORTS.length){ el.innerHTML = `<p class="section-placeholder" style="padding:16px">No reports configured.</p>`; return; }
  el.innerHTML = REPORTS.map(r => {
    const task = MANIFEST_STATE.data?.tasks?.find(t => t.job_id === r.job_id);
    const lastRun = task?.last_run?.finished_at;
    const lastStr = lastRun ? humanizeAgo(lastRun) + ' ago' : 'never';
    return `
      <div class="report-row">
        <span class="r-title">${escapeHtml(r.title)}</span>
        <span class="r-meta">${escapeHtml(r.agent)} · ${escapeHtml(r.cadence)}</span>
        <span class="r-last">Last: ${lastStr}</span>
        <button class="r-open" onclick="jumpToScheduleTask('${escapeAttr(r.job_id)}')">View</button>
      </div>
    `;
  }).join('');
}
```

- [ ] **Step 4: Wire into renderAll**

Update `renderAll`:

```javascript
function renderAll(){
  renderTodayKpis();
  renderTodayIssues();
  renderInsights();
  renderScheduleChips();
  renderScheduleGroups();
  renderDashboardsChips();
  renderDashboardsGrid();
  renderReports();
}
```

- [ ] **Step 5: Verify**

Reload. Open Reports via the sidebar (desktop) or "More" drawer (mobile).

Expected:
- 4 rows: Friday Sales Meeting / Vehicle Report Weekly / Workspace Health Report / CSO Intelligence Data.
- Each row: title, "STRIKER · Weekly · Fri 09:00" style meta, "Last: 4h ago" (or "never" if not yet run under wrapper), and a "View" button.
- Click "View" → jumps to Schedule section with the corresponding task expanded.
- Mobile: rows reflow vertically.

- [ ] **Step 6: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Reports list with last-run from manifest and View action"
```

---

### Task 13: Agents card grid with cross-references

**Files:**
- Modify: `index-v2.html`

- [ ] **Step 1: Replace the Agents section placeholder**

Find:

```html
<section class="section-pane" id="section-agents">
  <h1 class="section-title">Agents</h1>
  <p class="section-placeholder">Agents content lands here in Task 17.</p>
</section>
```

Replace with:

```html
<section class="section-pane" id="section-agents">
  <h1 class="section-title">Agents</h1>
  <div class="card-grid" id="agents-grid"></div>
</section>
```

- [ ] **Step 2: Add the CSS**

Append:

```css
.agent-card {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-lg);
  padding: 16px;
  cursor: pointer;
}
.agent-card.expanded { border-color: var(--color-border-brand); }
.agent-card h3 {
  font-family: var(--font-display); font-weight: 900;
  font-size: 18px; color: var(--color-text-primary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0 0 4px;
}
.agent-card .tagline {
  font-family: var(--font-body); font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 10px;
}
.agent-card .slash {
  display: inline-block;
  background: var(--color-surface-sunken);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--r-sm);
  padding: 2px 6px;
  font-family: var(--font-body); font-weight: 500; font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.agent-card .counts {
  font-size: 11px; color: var(--color-text-secondary);
  margin-top: 10px;
}
.agent-card .owned-list {
  display: none;
  margin-top: 12px;
  border-top: 1px solid var(--color-border-subtle);
  padding-top: 12px;
  font-size: 12px;
}
.agent-card.expanded .owned-list { display: block; }
.owned-section { margin-bottom: 10px; }
.owned-section h4 {
  font-family: var(--font-display); font-weight: 800; font-size: 11px;
  color: var(--color-text-tertiary);
  text-transform: uppercase; letter-spacing: 0.04em;
  margin: 0 0 4px;
}
.owned-section ul { list-style: none; padding: 0; margin: 0; }
.owned-section li { padding: 2px 0; color: var(--color-text-primary); }
.owned-section .empty { color: var(--color-text-tertiary); font-style: italic; }
```

- [ ] **Step 3: Add the render logic**

Append:

```javascript
function renderAgents(){
  const el = document.getElementById('agents-grid');
  const tasksByJobId = {};
  (MANIFEST_STATE.data?.tasks || []).forEach(t => { tasksByJobId[t.job_id] = t; });

  el.innerHTML = AGENTS.map(a => {
    const ownedTasks = a.task_ids.map(id => tasksByJobId[id]).filter(Boolean);
    const ownedDashboards = DASHBOARDS.filter(d => d.agent === a.id);
    const ownedReports = REPORTS.filter(r => r.agent === a.id);
    return `
      <div class="agent-card" onclick="toggleAgentCard(this)">
        <h3>${escapeHtml(a.name)}</h3>
        <p class="tagline">${escapeHtml(a.tagline)}</p>
        <span class="slash">${escapeHtml(a.slash)}</span>
        <div class="counts">${ownedTasks.length} task${ownedTasks.length === 1 ? '' : 's'} · ${ownedDashboards.length} dashboard${ownedDashboards.length === 1 ? '' : 's'} · ${ownedReports.length} report${ownedReports.length === 1 ? '' : 's'}</div>
        <div class="owned-list">
          <div class="owned-section">
            <h4>Scheduled tasks</h4>
            <ul>${ownedTasks.length
              ? ownedTasks.map(t => `<li>${escapeHtml(t.name)}</li>`).join('')
              : '<li class="empty">none</li>'}</ul>
          </div>
          <div class="owned-section">
            <h4>Dashboards</h4>
            <ul>${ownedDashboards.length
              ? ownedDashboards.map(d => `<li>${escapeHtml(d.title)}</li>`).join('')
              : '<li class="empty">none</li>'}</ul>
          </div>
          <div class="owned-section">
            <h4>Reports</h4>
            <ul>${ownedReports.length
              ? ownedReports.map(r => `<li>${escapeHtml(r.title)}</li>`).join('')
              : '<li class="empty">none</li>'}</ul>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function toggleAgentCard(card){
  card.classList.toggle('expanded');
}
```

- [ ] **Step 4: Wire into renderAll**

Update `renderAll`:

```javascript
function renderAll(){
  renderTodayKpis();
  renderTodayIssues();
  renderInsights();
  renderScheduleChips();
  renderScheduleGroups();
  renderDashboardsChips();
  renderDashboardsGrid();
  renderReports();
  renderAgents();
}
```

- [ ] **Step 5: Verify**

Reload. Open Agents.

Expected:
- 9 agent cards: APEX · HAVEN · PRISM · STRIKER · SIGMA · BLAZE · VAULT · PULSE · FLASH.
- Each card: name, tagline, slash command (e.g. `/prism`) in code chip, counts ("5 tasks · 1 dashboard · 0 reports").
- Click a card → expands to show three lists (scheduled tasks, dashboards, reports) cross-referenced from the inline data.
- HAVEN card should show "1 task · 1 dashboard · 0 reports" with "HAVEN Clocking Report Daily" under tasks, "HAVEN Clocking" under dashboards.
- BLAZE card shows zeros — confirms the "none" placeholder works.

- [ ] **Step 6: Commit**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): Agents card grid with cross-referenced ownership lists"
```

---

## Section H — Polish + rollout

### Task 14: Mobile / accessibility verification pass

**Files:**
- Modify: `index-v2.html` (only if issues found)

- [ ] **Step 1: Mobile smoke test in DevTools**

Open `http://localhost:8765/index-v2.html`, DevTools device toolbar, iPhone 14 Pro (390×844).

Verify each:
- [ ] Header sticky on scroll.
- [ ] Bottom nav fixed, 4 tabs visible.
- [ ] "Today" KPIs in 2×2 grid.
- [ ] Schedule task rows: status badge + "next" visible, "last" hidden.
- [ ] Reports: rows reflow vertically.
- [ ] Tap More → drawer slides up. Tap outside → drawer dismisses.
- [ ] Each tap target ≥ 44px tall (use DevTools ruler).
- [ ] No horizontal scroll.
- [ ] Safe-area: bottom nav respects iOS home indicator gap.

- [ ] **Step 2: Accessibility smoke test**

Desktop, no DevTools device mode. Use keyboard only:

- [ ] Tab key cycles: theme toggle → Refresh → sidebar items (5) → main content focusable elements.
- [ ] Enter key activates the focused button.
- [ ] Visible focus ring on every focusable element. If not, add this CSS at the bottom of `<style>`:

```css
button:focus-visible, a:focus-visible, .task-row:focus-visible, .dash-card:focus-visible, .agent-card:focus-visible {
  outline: 2px solid var(--color-brand-primary);
  outline-offset: 3px;
}
```

- [ ] Text contrast: use DevTools "Inspect" → "Accessibility" pane on body text → contrast ratio ≥ 4.5:1. Try each theme.

- [ ] **Step 3: Cross-theme regression**

Cycle through all 4 themes (Light, Dark, Brand, Navy). For each:
- [ ] KPI numbers readable.
- [ ] Status badges legible (success/warning/danger contrast).
- [ ] Refresh button + chips visible against theme background.
- [ ] No invisible text (white-on-white or black-on-black).

- [ ] **Step 4: Data robustness smoke test**

In DevTools console:

```javascript
// Empty manifest
MANIFEST_STATE.data = { tasks: [] }; renderAll();
```
Expected: KPI row shows em-dashes, Issues hidden, Schedule shows "No tasks match the current filters."

```javascript
// Unknown agent in manifest
MANIFEST_STATE.data = { tasks: [{job_id:'mystery',name:'Mystery',agent:'UNKNOWN',heartbeat_status:'fresh',task_path:'\\test',history:[]}] }; renderAll();
```
Expected: Mystery task lands in an "UNKNOWN" group under Schedule. No errors.

```javascript
// Reload real data
fetchManifest();
```

- [ ] **Step 5: If any issue was found and fixed, commit**

```powershell
git status --short
# If anything changed:
git add index-v2.html
git commit -m "fix(control-tower): polish pass (mobile / a11y / theme / robustness)"
```

If nothing changed: skip the commit.

---

### Task 15: Final swap — promote index-v2.html to index.html

**Files:**
- Rename: `index.html` → `index-snapshot.html.bak`
- Rename: `index-v2.html` → `index.html`

- [ ] **Step 1: Read existing INFO_INSIGHT_DATA from the current index.html**

Open `C:\Users\quint\workspace-dashboard\index.html` in an editor. Find the `INFO_INSIGHT_DATA` array (a `const INFO_INSIGHT_DATA = [ ... ]` block). Copy its entries.

Open `index-v2.html`. Paste the entries inside the empty `INFO_INSIGHT_DATA` array, preserving JS syntax.

Save.

- [ ] **Step 2: Verify the merged INFO_INSIGHT_DATA renders**

Reload `http://localhost:8765/index-v2.html`. Today section → Information Insights card should show the entries from the old index.html.

- [ ] **Step 3: Commit the merge**

```powershell
git add index-v2.html
git commit -m "feat(control-tower): merge existing INFO_INSIGHT_DATA from index.html"
```

- [ ] **Step 4: Inspect existing index.html for `<!--AUTO:...-->` markers**

```powershell
Set-Location C:\Users\quint\workspace-dashboard
Select-String -Path index.html -Pattern '<!--AUTO:' -List
```

Expected: prints each marker name found. If markers exist, they identify what background scripts auto-update. For each marker found, search index-v2.html for the same marker. If absent and the marker is content the Control Tower should preserve, port it in. If the marker drives content the Control Tower deliberately doesn't surface, note it in the commit message so future-you knows the auto-update target moved.

- [ ] **Step 5: Perform the rename swap**

```powershell
Set-Location C:\Users\quint\workspace-dashboard
git mv index.html index-snapshot.html.bak
git mv index-v2.html index.html
git status --short
```

Expected:
- `R  index-v2.html -> index.html`
- `R  index.html -> index-snapshot.html.bak`

- [ ] **Step 6: Verify both files are correct after rename**

```powershell
# New index.html should contain "OLYMPIC CONTROL TOWER" markup
Select-String -Path index.html -Pattern 'Olympic Control Tower' -List
# Backup should still contain the OLD content
Select-String -Path index-snapshot.html.bak -Pattern 'INFO_INSIGHT_DATA' -List
```

Expected: matches in both.

- [ ] **Step 7: Commit the swap**

```powershell
git commit -m "feat(control-tower): promote control tower to index.html; old snapshot archived as index-snapshot.html.bak"
git log --oneline -3
```

- [ ] **Step 8: Squash-merge the feature branch into master**

```powershell
git checkout master
git pull origin master
git merge --squash control-tower-ui
git commit -m "Olympic Paints Control Tower (sub-project #3)

Replaces workspace-dashboard/index.html with the operational front door:
5 sections (Today / Schedule / Dashboards / Reports / Agents), 4-theme
toggle, sidebar on desktop / bottom-nav on mobile, live-fetch of
data/schedule_manifest.json with last-good cache and error banner.

The old index.html is archived as index-snapshot.html.bak (delete after
one week of clean operation)."
```

If the merge surfaces conflicts (the auto-commit drift pattern observed in sub-project #1): keep `theirs` (the feature-branch version) for `index.html` and `index-snapshot.html.bak`. Leave any other auto-commit-affected files (`store-health/index.html`, `clocking_stats.json`, `updates_status.json`, etc.) at their current master state. Only the two renamed files should change.

```powershell
git push origin master
```

- [ ] **Step 9: Live verification**

Wait for GitHub Pages to rebuild (~1–2 min). Open:

```
https://flomaticauto.github.io/workspace-dashboard/
```

Expected: the Control Tower loads at the root URL. KPI row populates from the live `schedule_manifest.json`. Theme persists across reloads.

If something is broken in production, revert the swap:

```powershell
git checkout master
git revert HEAD --no-edit
git push origin master
```

This restores the previous `index.html`. The Control Tower remains in `index-snapshot.html.bak` for later resurrection.

- [ ] **Step 10: One-week retention review (calendar reminder, not a code step)**

In one week (around 2026-05-23), if no issues have surfaced:

```powershell
Set-Location C:\Users\quint\workspace-dashboard
git rm index-snapshot.html.bak
git commit -m "chore(control-tower): retire index-snapshot.html.bak after one week of clean operation"
git push origin master
```

Also: if `updates.html` is no longer referenced by any auto-update script and the Control Tower fully covers its job, deprecate it:

```powershell
git rm updates.html
git commit -m "chore(control-tower): retire updates.html (job absorbed into the Control Tower)"
git push origin master
```

(Skip this if scripts still write to `updates_status.json` — that's a separate cleanup.)

---

## Appendix — Manual test runner via ?test=1

Optional. If you want a single console-driven smoke check during development, append this to the bottom of the `<script>` block in `index-v2.html`:

```javascript
(function(){
  const url = new URL(window.location.href);
  if (url.searchParams.get('test') !== '1') return;

  const results = [];
  function check(name, pass, detail){
    results.push({ name, pass, detail });
    console[pass ? 'log' : 'warn'](`${pass ? '✓' : '✗'} ${name}${detail ? ' — ' + detail : ''}`);
  }

  check('humanizeDelta seconds', humanizeDelta(45000) === '45s');
  check('humanizeDelta minutes', humanizeDelta(120000) === '2m');
  check('humanizeDelta hours',   humanizeDelta(3600000 * 2 + 60000 * 5) === '2h5m');
  check('humanizeDelta days',    humanizeDelta(86400000 * 3) === '3d');
  check('escapeHtml ampersand',  escapeHtml('a & b') === 'a &amp; b');
  check('escapeHtml quotes',     escapeHtml('"x"') === '&quot;x&quot;');
  check('DASHBOARDS length',     DASHBOARDS.length === 9);
  check('AGENTS length',         AGENTS.length === 9);
  check('REPORTS length',        REPORTS.length === 4);
  check('PRISM owns 5 tasks',    AGENTS.find(a => a.id === 'PRISM').task_ids.length === 5);

  const passed = results.filter(r => r.pass).length;
  console.log(`%c${passed}/${results.length} tests passed`, passed === results.length ? 'color:green;font-weight:bold' : 'color:red;font-weight:bold');
})();
```

Run by visiting `http://localhost:8765/index-v2.html?test=1` and checking the console. Optional; not part of the standard rollout.
