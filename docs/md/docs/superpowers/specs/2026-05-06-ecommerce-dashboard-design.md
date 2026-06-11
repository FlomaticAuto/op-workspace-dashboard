# E-Commerce (WooCommerce) Dashboard — Design Spec

**Owner:** PRISM (Analytics & BI)
**Date:** 2026-05-06
**Status:** Draft — awaiting approval

---

## 1. Purpose

Replace the QuickSight WooCommerce e-commerce dashboard with a self-hosted standalone HTML dashboard that mirrors its tiles, runs from the local CSV export, and matches the Olympic Paints brand system (navy default theme, four-theme toggle, Barlow fonts, real digital logo).

The dashboard answers four operational questions:

1. **Are we shipping fast enough?** (Service Level vs 5-day target, overall and per province)
2. **What's stuck?** (Overdue orders — total and last 4 weeks)
3. **Where are sales coming from?** (Sales by province, order status mix)
4. **What's selling?** (Sales per product table, daily order volume trend)

---

## 2. Inputs

| File | Path | Format | Cadence |
|---|---|---|---|
| WooCommerce transactions | `3.Resources/16.Sales and Other data/Manual/Woocommerce_Transactions.csv` | Row-per-line-item CSV (~666 rows, growing) | Manual export from WooCommerce |
| Logo | `3.Resources/9. Brand Assets & Images/Misc Pictures/Olympic Paints Logo Digital.jpg` | JPEG | Static |

**Key columns used:**
- `order_id` — unique order key (multiple line-items per order_id)
- `order_status` — `completed`, `processing`, `pending`, `on-hold`, `cancelled`, `refunded`, etc.
- `date_created` — order placement timestamp (primary date)
- `date_completed` — fulfilment timestamp (nullable)
- `total` — order grand total (ZAR; same value repeated on every line-item of an order)
- `billing_first_name` — customer label (matches QuickSight "Customer" column)
- `billing_state` — province code (`GP`, `WC`, `KZN`, `EC`, `MP`, `NW`, `NC`, `LP`)
- `line_item_name`, `line_item_quantity`, `line_item_total` — product-level rows
- `line_item_sku` — SKU (e.g. `NE_5L_Pinetop`)

**De-duplication rule:** Order-level metrics (sales, status, service level) must group by `order_id` and take the first row per order. Product-level metrics (Sales Per Product) operate on every line-item row.

---

## 3. Metrics & Definitions

### 3.1 Service Level (headline tile)

```
days_in_system =
    if order_status in ('completed','refunded')  → date_completed - date_created
    elif order_status == 'cancelled'              → exclude entirely
    else                                          → today() - date_created   (in-flight)

Service Level (overall) = mean(days_in_system) for all non-cancelled orders
                          created in the reporting period (current YTD)
```

- **Target:** 5 days (constant — display as `Service Level Target 5`)
- **Variance vs target:** `(actual - target) / target * 100` shown with up/down arrow + green/red colour
- **Per-province tile:** same formula filtered by `billing_state`. If province has **zero non-cancelled orders in period**, render `No data` (matches QuickSight behaviour seen for NW).

### 3.2 Overdue Orders

```
is_overdue =
    order_status NOT IN ('completed','cancelled','refunded')
    AND days_in_system > 5
```

- **Overdue Orders — Total:** count of all orders matching `is_overdue` (yellow tile)
- **Overdue Orders — Past 4 Weeks:** count where `date_created >= today() - 28 days` AND `is_overdue` (orange tile)
- **Dispatch Target Date:** `date_created + 5 days` (calendar days)
- **Overdue Status indicator:** green dot if `today() <= dispatch_target`, red dot if `today() > dispatch_target` AND status not completed/cancelled/refunded

### 3.3 Sales

```
order_total = first(total) per order_id   (avoid line-item double-counting)
total_sales_period = sum(order_total) for all orders excluding cancelled & refunded
sales_by_province = sum(order_total) grouped by billing_state, same exclusions
```

- **Empty province** (`billing_state` blank/null) → bucketed as `empty` per QuickSight behaviour
- Pie chart shows top 8 provinces by sales; remainder bucketed if needed (likely not needed at current row count)

### 3.4 Order Status Breakdown

Pie chart: count of orders per `order_status`, grouped by `order_id`. Statuses observed in current data: `completed`, `cancelled`, `processing`, `pending`, `on-hold`, `failed`, `refunded`.

### 3.5 Sales Per Product

Table grouped by `line_item_name`, summing `line_item_quantity` and `line_item_total`. Sorted by Total descending. Excludes orders with status `cancelled` or `refunded`.

- **Top 3 by quantity:** highlighted with brand-yellow row tint
- **Footer row:** sums of Qty and Total (matches QuickSight `797` / `R233,076.00`)

### 3.6 Service Level per Order

Recent-orders table (most recent 50 by `date_created`), columns:
- Order Date · Customer (`billing_first_name`) · Status · Province · `days_in_system` · Service (= `days_in_system` if status is completed, else blank)

### 3.7 Dispatch Schedule

Filtered to non-completed, non-cancelled orders only. Columns:
- Order Date · Dispatch Target Date · Customer Name · Status · Item Name · Province · `days_in_system` · Qty · Overdue Status (green/red dot)

### 3.8 Daily Order Volume Trend (PRISM stretch)

Line chart: x-axis = last 30 days, y-axis = count of distinct `order_id` per day. Single yellow line on grid, sparkline-style.

---

## 4. Layout

Page structure (single scrollable HTML, navy theme default):

```
┌─ Header bar ────────────────────────────────────────────────────────┐
│ [logo 48px]  E-Commerce Dashboard — Olympic Paints                  │
│              Period: YTD 2026 · Generated: 6 May 2026 14:32 SAST    │
│                                            [Light][Dark][Brand][Navy]│
├─ KPI row (3 tiles) ─────────────────────────────────────────────────┤
│ ┌ Service Level ┐  ┌ Overdue Total ┐  ┌ Overdue 4 Weeks ┐           │
│ │ 8.73          │  │ 8             │  │ 7               │           │
│ │ Target 5  ▲%  │  │ (yellow tile) │  │ (orange tile)   │           │
│ └───────────────┘  └───────────────┘  └─────────────────┘           │
├─ Provincial Service Level (8 mini-tiles, 2 rows × 4) ───────────────┤
│ GP · NW · WC · NC · MP · EC · KZN · LP                              │
├─ Two pies (50/50 split) ────────────────────────────────────────────┤
│ Sales by Province                Order Status Breakdown             │
├─ Daily Order Volume Trend (full-width, 200px tall) ─────────────────┤
├─ Two tables (50/50 split) ──────────────────────────────────────────┤
│ Service Level per Order          Sales Per Product                  │
├─ Dispatch Schedule (full-width, scrollable) ────────────────────────┤
└─ Footer: "Olympic Paints E-Commerce Dashboard — generated by PRISM" ┘
```

Mobile: KPI row stacks, provincial grid wraps to 2 cols, pies stack, tables stack.

---

## 5. Colour & Theme

- **Default theme:** `theme-navy` (per `feedback_sales_dashboard_theme.md`)
- **All four themes available** via toggle (Light / Dark / Brand / Navy)
- **KPI tile colours** (mimic QuickSight semantics, but use design-system tokens):
  - Service Level tile background: `--color-success-bg` (green tint) — mood: "we're hitting target"
  - Overdue Total: `--color-warning-bg` (yellow tint)
  - Overdue 4 Weeks: `--color-danger-bg` (red/orange tint)
  - Provincial Service Level tiles: cycle through **mood/accent ramp** (`--_y200`, `--_n300`, `--_pink-light`, `--_teal-light`, `--_terra-light`, `--_violet-light`, `--_y400`, `--_teal-light`) — each province gets a fixed tint slot for consistency across reruns
- **Charts** use the multi-series order from CLAUDE.md: yellow → navy → teal → terra → pink → violet → ink
- **Overdue dots:** `--color-success-fg` (green) and `--color-danger-fg` (red)

No hardcoded hex anywhere in component CSS — all references go through `--color-*` and `--_*` tokens.

---

## 6. Implementation

### 6.1 Build script

**File:** `1.Projects/AWS Data/build_ecommerce_dashboard.py`
**Run:** `python build_ecommerce_dashboard.py`

Pipeline:
1. Load CSV with pandas: `dtype=str` initially, then parse dates with `pd.to_datetime(..., errors='coerce')`
2. Normalise: lowercase status, strip whitespace from `billing_state`, treat empty state as `'empty'`
3. Compute order-level dataframe (group by `order_id`, first row of each)
4. Compute line-item dataframe for product table (no grouping)
5. Calculate all metrics into a `metrics` dict
6. Render Jinja-style f-string templates into single `index.html`
7. Copy `Olympic Paints Logo Digital.jpg` to output dir as `logo.jpg`
8. Output to `1.Projects/AWS Data/ecommerce_dashboard/index.html` + `logo.jpg`
9. **No GitHub push in v1** — local file only. Open in browser to view.

### 6.2 Dependencies

- `pandas` (already in project)
- Chart.js 4.x via cdnjs
- `barLabels` plugin (pasted inline per CLAUDE.md rule)

No external CSS frameworks. No build step. Pure Python → pure HTML.

### 6.3 Key constants at top of script

```python
SERVICE_LEVEL_TARGET = 5
OVERDUE_LOOKBACK_DAYS = 28
RECENT_ORDERS_LIMIT = 50
EXCLUDED_FROM_SALES = {'cancelled', 'refunded'}
EXCLUDED_FROM_OVERDUE = {'completed', 'cancelled', 'refunded'}
PROVINCE_ORDER = ['GP', 'NW', 'WC', 'NC', 'MP', 'EC', 'KZN', 'LP']
TOP_PRODUCTS_HIGHLIGHT = 3
```

### 6.4 Reporting period

v1 hard-codes **YTD current year** (`date_created.year == today.year`). The header label reads `Period: YTD 2026`. Future iteration may add a period selector.

### 6.5 Output paths

```
1.Projects/AWS Data/ecommerce_dashboard/
  ├── index.html
  └── logo.jpg
```

The folder is local-only in v1. If GitHub Pages publishing is added in v2, it'll mirror the KPI dashboard pattern.

---

## 7. Edge cases & handling

| Case | Handling |
|---|---|
| Province has zero non-cancelled orders in period | Tile renders `No data` |
| Order has missing `date_created` | Excluded with warning to console |
| Order has `date_completed` earlier than `date_created` (data error) | `days_in_system` clamped to 0 |
| `total` column blank or zero on a completed order | Included in service level, excluded from sales sums |
| Province not in canonical list (e.g. `Gauteng` typed instead of `GP`) | Logged to console; bucketed as `other` |
| CSV missing entirely | Script exits with clear error |
| All orders in period are cancelled | Service Level tile shows `No data`, target still displayed |

---

## 8. Out of scope (v1)

- Time-window selector / date range picker
- GitHub Pages publish
- Auto-refresh / file watcher
- MTD vs LMTD comparison
- Customer leaderboard
- Source/UTM attribution analysis (data exists in CSV but deferred to v2)
- Cost / margin overlay
- Email export

---

## 9. Success criteria

- Running `python build_ecommerce_dashboard.py` produces a valid `index.html` in under 5 seconds with zero errors against the current 666-row CSV
- All six QuickSight tiles render with values within ±0.5% of the QuickSight reference (small variance acceptable due to date cutoffs)
- Theme toggle switches all four themes without flash on reload
- Logo renders correctly at 48px, circular, in the header on all four themes
- Mobile (<768px viewport) renders without horizontal scroll
- All values in the Sales Per Product footer match `sum(line_item_quantity)` and `sum(line_item_total)` over included orders
