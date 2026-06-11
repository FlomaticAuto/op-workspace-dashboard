# Olympic Paints Design System

HTML standards, theme system, typography, and brand guidelines for all Olympic Paints dashboards and reports.

---

## Who you are for HTML output

You are a senior frontend developer working within the Olympic Paints brand system. Every HTML file you produce MUST comply with the standards below. Apply them automatically — do not ask whether to apply them. Only make changes directly requested. Do not add features or refactor beyond what was asked.

---

## Critical rules — NEVER violate for HTML output

1. NEVER hardcode hex colours into component CSS. Always use the semantic CSS custom property tokens defined below.
2. NEVER generate an HTML file without including the full CSS custom property block from the Theme System section.
3. NEVER use fonts other than Barlow Condensed (display/headlines) and Barlow (body/UI). Always import from Google Fonts.
4. NEVER produce a page without a four-button theme toggle (Light / Dark / Brand / Navy) unless told "single theme only."
5. ALWAYS apply the active theme class to `<html>`, not `<body>`. Default to `class="theme-dark"` unless told otherwise.
6. ALWAYS use the official `Olympic Paints Logo Digital.jpg` via an `<img>` tag wrapped in a `border-radius:50%;overflow:hidden` div. NEVER use the old inline SVG badge — it does not match the registered brand mark. See the Logo section below for the canonical HTML and the Python `LOGO_SRC` constant.
7. NEVER use Tailwind, Bootstrap, or any external CSS framework. Vanilla CSS with the token system only.
8. NEVER use external chart libraries unless specifically asked. Chart.js from cdnjs is acceptable when asked.
9. ALWAYS include the `barLabels` Chart.js plugin whenever Chart.js is used. Register it once after `Chart.defaults` setup. All bar charts MUST use `_lblMap.set()` to configure labels — values render inside bars when they fit, automatically outside when they don't. See the **Chart label plugin** section below for the canonical code.

---

## Theme system

Four themes, applied via class on `<html>`:

| Class | Appearance | Use for |
|---|---|---|
| `theme-dark` | Near-black surface, light text, yellow accents | **Default for all files** |
| `theme-light` | White surface, dark text, yellow accents | Print-friendly, external sharing |
| `theme-brand` | Full Inspiration Yellow surface, black text | Cover pages, brand moments |
| `theme-navy` | Olympic Navy surface, white text, yellow accents | Executive / management reports |

Components reference only `--color-*` semantic tokens. Adding a fifth theme = one new CSS block, zero component changes.

---

## CSS token block — include in every HTML file

```css
/* ── RAW DESIGN TOKENS ─────────────────────────────────────────── */
:root {
  /* Yellow ramp */
  --_y50:#FEF9E0; --_y100:#FDF0A0; --_y200:#FAE04D;
  --_y400:#F5C400; --_y600:#D4A800; --_y800:#A88000; --_y900:#6A5000;

  /* Navy ramp */
  --_n50:#E8EFF8; --_n100:#B8CCE8; --_n300:#6B9ED0;
  --_n500:#2D6BA8; --_n700:#1A3D6E; --_n900:#0D2040; --_n950:#071022;

  /* Neutral ramp */
  --_g0:#FFFFFF; --_g50:#F7F6F3; --_g100:#E8E7E2; --_g200:#C8C7C0;
  --_g400:#949390; --_g600:#5C5B58; --_g800:#2E2E2C;
  --_g900:#1A1A18; --_g950:#0D0D0B;

  /* Mood / accent */
  --_teal:#2D8C7A; --_teal-light:#C8EDE7; --_teal-dark:#1a5c50;
  --_terra:#C97A3A; --_terra-light:#F7E0C8;
  --_coral:#E86060; --_coral-light:#FDDCDC;
  --_pink:#E87BAD; --_pink-light:#FCE4EF;
  --_violet:#9B7DBF; --_violet-light:#EDE0F7;
  --_sage:#7A8C55; --_ink:#5C6B7A;

  /* Typography */
  --font-display:'Barlow Condensed',sans-serif;
  --font-body:'Barlow',sans-serif;

  /* Radius */
  --r-sm:4px; --r-md:8px; --r-lg:12px; --r-xl:16px; --r-pill:50px;
}

/* ── LIGHT THEME ──────────────────────────────────────────────── */
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

/* ── DARK THEME ───────────────────────────────────────────────── */
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

/* ── BRAND THEME (full yellow) ────────────────────────────────── */
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

/* ── NAVY EXECUTIVE THEME ─────────────────────────────────────── */
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
```

---

## Required HTML boilerplate

Every HTML file generated in this repository MUST use this structure:

```html
<!DOCTYPE html>
<html lang="en" class="theme-dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[REPORT TITLE] — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<!-- Reads saved theme BEFORE first paint — eliminates flash on reload -->
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>
/* [Full CSS token block goes here] */
/* Component styles use only --color-* and --font-* tokens — never raw hex */
</style>
</head>
<body style="background:var(--color-surface-page);color:var(--color-text-primary);font-family:var(--font-body);margin:0;">

  <!-- Theme toggle — required on every page -->
  <div class="theme-bar" style="display:flex;gap:4px;padding:8px 16px;background:var(--color-surface-secondary);">
    <button onclick="olyTheme('theme-light',this)">Light</button>
    <button onclick="olyTheme('theme-dark',this)" class="active">Dark</button>
    <button onclick="olyTheme('theme-brand',this)">Brand</button>
    <button onclick="olyTheme('theme-navy',this)">Navy</button>
  </div>

  <!-- [Page content here] -->

<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}
</script>
</body>
</html>
```

---

## Logo — official Clickpaint digital badge

**Canonical file:** `3.Resources/9. Brand Assets & Images/Misc Pictures/Olympic Paints Logo Digital.jpg`

This is the official Olympic Paints digital logo — a yellow circle with bold "OLYMPIC™ PAINTS" on a white JPEG background. **Always wrap in a `border-radius:50%; overflow:hidden` container** to clip the white corners; the yellow circle then renders cleanly on any background colour including dark and navy themes.

**NEVER use the old inline SVG badge. Always use the real logo image.**

### HTML implementation — three sizes

```html
<!-- Small (36px) — navbars, slide nav bars -->
<div style="width:36px;height:36px;border-radius:50%;overflow:hidden;flex-shrink:0;">
  <img src="logo.jpg" alt="Olympic Paints" width="36" height="36" style="display:block;width:100%;height:100%;object-fit:cover;">
</div>

<!-- Medium (48px) — page / report headers -->
<div style="width:48px;height:48px;border-radius:50%;overflow:hidden;flex-shrink:0;">
  <img src="logo.jpg" alt="Olympic Paints" width="48" height="48" style="display:block;width:100%;height:100%;object-fit:cover;">
</div>

<!-- Large (72px) — hero sections, cover pages -->
<div style="width:72px;height:72px;border-radius:50%;overflow:hidden;flex-shrink:0;">
  <img src="logo.jpg" alt="Olympic Paints" width="72" height="72" style="display:block;width:100%;height:100%;object-fit:cover;">
</div>
```

### Logo file — where to put it

| Context | How to provide logo.jpg |
|---|---|
| GitHub Pages repo (build script output) | `shutil.copy2(LOGO_SRC, OUT_DIR / 'logo.jpg')` in the Python build script before writing HTML |
| Local standalone HTML file | Use a relative path from the HTML file to the canonical JPG |
| Any Python script generating HTML | Define `LOGO_SRC` at the top of the script pointing to the canonical file |

Python constant to include at the top of every build script:
```python
LOGO_SRC = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\9. Brand Assets & Images\Misc Pictures\Olympic Paints Logo Digital.jpg")
```

### Logo rules

- **Always** wrap in `border-radius:50%; overflow:hidden` — this clips the white JPEG background
- **Always** use `object-fit:cover` on the `<img>` so the circle fills the wrapper cleanly
- **Never** distort: wrapper and img must always have equal width and height
- **Never** apply `border-radius` to the `<img>` itself — only to the wrapper `<div>`
- **Minimum size:** 28px
- **alt text:** always `"Olympic Paints"`
- **Never** use the old inline SVG badge — it does not match the registered brand mark

---

## Typography scale

| Role | Font | Weight | Size | Transform |
|---|---|---|---|---|
| Hero / page title | Barlow Condensed | 900 | 40–56px | UPPERCASE |
| Section heading H2 | Barlow Condensed | 800 | 24–32px | UPPERCASE |
| Card heading H3 | Barlow Condensed | 700 | 16–20px | UPPERCASE |
| Eyebrow / label | Barlow Condensed | 700 | 10–11px | UPPERCASE, tracking 0.12em |
| Body paragraph | Barlow | 400 | 14–15px | normal |
| Body emphasis | Barlow | 500 | 14–15px | normal |
| Caption / meta | Barlow | 400 | 11–12px | normal |
| KPI number | Barlow Condensed | 900 | 28–48px | normal |
| KPI label | Barlow | 500 | 11px | UPPERCASE, tracking 0.08em |

---

## Chart & data colours

**Multi-series order** (use in this sequence):
1. `#F5C400` — Inspiration Yellow (primary series)
2. `#1A3D6E` — Olympic Navy
3. `#2D8C7A` — Teal
4. `#C97A3A` — Terra
5. `#E87BAD` — Pink
6. `#9B7DBF` — Violet
7. `#5C6B7A` — India Ink (neutral / baseline)

**Status / directional:** Positive `#2D8C7A` · Negative `#E86060` · Neutral `#5C6B7A` · Highlight `#F5C400`

**Monochromatic yellow** (single-metric / YoY): `#FDF0A0` → `#FAE04D` → `#F5C400` → `#D4A800` → `#A88000`

---

## Chart label plugin (required for all Chart.js dashboards)

Every dashboard that uses Chart.js **must** include the `barLabels` plugin. It auto-detects fit: values render **inside** the bar in a readable contrast colour; if the bar is too short/narrow the value falls **outside** automatically. No external CDN dependency — inline JS only.

### Placement

Register once, immediately after `Chart.defaults` setup and before any `new Chart(...)` call. In Python f-string templates every `{` / `}` must be doubled to `{{` / `}}`.

### Canonical plugin code

```js
const _lblMap = new Map();
Chart.register({
  id: 'barLabels',
  afterDraw(chart) {
    const opts = _lblMap.get(chart.canvas && chart.canvas.id);
    if (!opts) return;
    const { ctx } = chart;
    const mode = opts.mode || 'v-top';
    const fnt  = 'bold ' + (opts.fs || 10) + "px 'Barlow',sans-serif";
    try {
      chart.data.datasets.forEach((ds, i) => {
        const meta = chart.getDatasetMeta(i);
        if (!meta || meta.hidden) return;
        meta.data.forEach((el, j) => {
          if (!el || isNaN(el.x) || isNaN(el.y)) return;
          const val  = ds.data[j];
          if (val == null || val === 0) return;
          const text = opts.fmt ? opts.fmt(val) : String(Math.round(val));
          if (!text) return;
          const base = el.base ?? el.y;
          ctx.save(); ctx.font = fnt;
          const textW     = ctx.measureText(text).width;
          const inColor   = (opts.dsColors && opts.dsColors[i]) || opts.color || '#fff';
          const outColor  = Chart.defaults.color || '#949390';
          if (mode === 'h-inside') {
            const barW = Math.abs(el.x - base);
            ctx.textBaseline = 'middle';
            if (barW >= textW + 10) {
              ctx.fillStyle = inColor; ctx.textAlign = 'center';
              ctx.fillText(text, (el.x + base) / 2, el.y);
            } else if (barW > 4) {
              ctx.fillStyle = outColor;
              ctx.textAlign = val >= 0 ? 'left' : 'right';
              ctx.fillText(text, val >= 0 ? el.x + 4 : el.x - 4, el.y);
            }
          } else if (mode === 'v-stacked') {
            const segH = Math.abs(base - el.y);
            const fs   = opts.fs || 10;
            if (segH >= fs + 6) {
              ctx.fillStyle = inColor;
              ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
              ctx.fillText(text, el.x, (el.y + base) / 2);
            } else if (segH >= 4) {
              ctx.fillStyle = outColor;
              ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
              ctx.fillText(text, el.x, Math.min(el.y, base) - 2);
            }
          } else {
            ctx.fillStyle = outColor;
            ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
            ctx.fillText(text, el.x, el.y - 3);
          }
          ctx.restore();
        });
      });
    } catch(e) {}
  }
});
```

### Modes

| Mode | Chart type | Behaviour |
|---|---|---|
| `v-stacked` | Vertical bar (grouped or stacked) | Inside (centred, `inColor`) when bar height ≥ `fs + 6`px; above bar (`outColor`) when too short |
| `h-inside` | Horizontal bar | Inside (centred, `inColor`) when bar width ≥ `textWidth + 10`px; right of bar end (`outColor`) when too narrow |
| `v-top` | Vertical bar (fallback) | Always above the bar — no inside logic |

### Options object (`_lblMap.set(canvasId, opts)`)

| Key | Type | Default | Description |
|---|---|---|---|
| `mode` | string | `'v-top'` | One of the modes above |
| `fmt` | function | `v => String(Math.round(v))` | Value formatter, e.g. `v => fmtR(v)` |
| `fs` | number | `10` | Font size in px (also controls minimum bar height threshold) |
| `color` | string | `'#fff'` | Inside text colour — applies to all datasets unless `dsColors` is set |
| `dsColors` | string[] | `undefined` | Per-dataset inside colours indexed by dataset order, e.g. `['#fff', '#0D0D0B']` |

### Layout padding (required for `v-stacked`)

Always add `layout: { padding: { top: 22 } }` to the chart options when using `v-stacked`. This reserves space above the plot area so outside labels on short bars are never clipped by the canvas boundary.

### Standard usages

```js
// Grouped vertical bar — FY2025 (navy) vs FY2026 (yellow)
_lblMap.set('cSalesRev', { mode:'v-stacked', fmt:v=>fmtR(v), fs:9, dsColors:['#fff','#0D0D0B'] });
new Chart(document.getElementById('cSalesRev'), {
  ...
  options: { layout: { padding: { top: 22 } }, ... }
});

// Single vertical bar (teal)
_lblMap.set('cActivity', { mode:'v-stacked', fmt:v=>String(Math.round(v)), fs:9, color:'#fff' });

// Horizontal bar (yellow)
_lblMap.set('cAccCat', { mode:'h-inside', fmt:v=>'R'+v.toFixed(2)+'M', fs:9, color:'#0D0D0B' });
```

### Colour rule for `inColor`

Match the inside text to the bar's background for legibility:
- **Dark bars** (navy `#1A3D6E`, teal `#2D8C7A`, terra `#C97A3A`) → `#fff`
- **Light bars** (yellow `#F5C400`, `#FAE04D`) → `#0D0D0B`
- **Neutral bars** (India Ink `#5C6B7A`) → `#fff`

---

## Report type layouts

**KPI sales dashboard** (`build_kpi_dashboard.py` output)
- Full-width header: logo wordmark + "KPI Sales Dashboard" + week/date + theme toggle
- KPI row: MTD Sales · MTD Target · MTD % Target · Debtors Total · 90-day Debtors · Overdue 60d %
- Rep performance table: AC / AP / BV / NP / BM with sales, target, % columns and colour-coded status badge
- YoY chart: monochromatic yellow bars, current month highlighted at full `#F5C400`
- Rock-bottom % by product group: horizontal bar chart, danger colour (`#E86060`) for any bar above threshold
- Footer: "Olympic Paints KPI Dashboard — Week [n] — [date]"

**Clocking / HAVEN dashboard** (`gen_dashboard.py` output)
- Header: logo + "HAVEN HR — Clocking Dashboard" + period + theme toggle
- KPI row: Total employees · Total hours · Avg hours/employee · Missed clock-outs
- Employer split: Olympic Paints (74) vs Primeserve (28 — SD prefix) side-by-side cards
- Tabs: Overview · Yesterday · Daily Attendance · Departments · Weekly Hours · Missing Clock Out
- Employee table: ID, Name, Employer, Days worked, Total hours, Status badge
- Status badges: `--color-success-*` normal · `--color-warning-*` anomaly · `--color-danger-*` missing punch
- **Note:** 45-minute break deduction is applied upstream in `build_report.py` — do not re-apply in the dashboard

**Monthly / management report**
- Cover hero: brand-coloured full-width block, report title, period, generated date
- Executive summary card: 3–4 bullet points
- KPI metrics grid
- Full-width charts with section headings
- Data table with zebra striping using `--color-surface-sunken`
- Footer with logo badge

**Data table / product listing**
- Header + title
- Searchable/filterable table (vanilla JS only)
- Zebra rows: alternate `--color-surface-sunken`
- Status badges using status token triplets (bg / fg / border)
- Sticky header row

---

## WCAG compliance

- Body text: minimum 4.5:1 contrast ratio (AA)
- Large text / headings: minimum 3:1 (AA)
- Interactive elements: visible focus rings using `--color-brand-primary`, 2px solid, 3px offset
- Never use `--color-text-tertiary` for body text — decorative labels only
- Status badge text must use the matching `-fg` token, never a global text token
