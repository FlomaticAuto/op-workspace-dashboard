# PVA Shrinkage Intelligence Dashboard — Design Spec

_Date: 2026-05-17 | Author: Claude (brainstorming session)_

---

## Overview

A standalone intelligence dashboard showing PVA paint revenue shrinkage across **all Olympic Paints trading regions** (Gauteng, Limpopo, Venda, North West, Mpumalanga, Free State, Ermelo, Botswana, Groblersdal), built as a Python build script + static JSON data layer + single-file React component. Deployable to Vercel or as a GitHub Pages artifact.

The map canvas displays a simplified southern Africa outline with area pins spanning the full geographic spread of Olympic Paints' customer base — not Gauteng-only.

---

## Decisions Made

| Decision | Choice | Reason |
|---|---|---|
| Area scope | All regions, not Gauteng-only | Tzaneen, Venda, Mafakeng etc. are significant revenue areas; Gauteng-only view was misleading |
| Area assignment — tagged accounts | Use `Area_Grouping` field directly | 36% of PVA revenue already tagged across 11 named regions in accounts.parquet |
| Area assignment — untagged Gauteng accounts | GPS bounding box → "Johannesburg / Gauteng" bucket | KK/KP/KE/KB prefix accounts are clearly Greater Johannesburg by GPS; no tag exists |
| Competitor data | Omit — no data exists | No competitor field in any source; side panel shows "populate competitors-override.json" notice |
| Architecture | Python build → static JSON → React | Matches existing Olympic Paints dashboard pattern; one-command refresh |
| YoY period | FY2024 vs FY2025 | Only two complete fiscal years in parquet (Mar 2024–present; FY2026 only has Jan–Apr) |
| Price inflation adjustment | Flat 10% deflator on FY2025 | FY2025 net revenue divided by 1.10 before computing shrinkage; prevents price increases masking volume loss |

---

## Data Sources

| Source | Path | Used For |
|---|---|---|
| Sales invoices | `3.Resources/16.Sales and Other data/Sales_Invoices_All.parquet` | PVA revenue by account, FY2024 and FY2025 |
| Accounts | `1.Projects/AWS Data/zoho_meetings/data/accounts.parquet` | `Area_Grouping` tags + GPS coordinates for fallback assignment |
| Competitor override | `1.Projects/AWS Data/competitors-override.json` | Optional manual competitor data; merged at build time if present |

---

## Data Layer — `build_pva_shrinkage.py`

**Location:** `1.Projects/AWS Data/build_pva_shrinkage.py`

**Steps:**

1. Load `Sales_Invoices_All.parquet`, filter `category_l1 == 'PVA Paints'`
2. Sign ivnett: `net = ivnett × {INVOICE: +1, CRNOTE: −1}`
3. Load `accounts.parquet`, parse `Store_Coordinates` → `lat`, `lon` floats (filter garbage values: `abs(lat) > 90` → NaN)
4. **Two-tier area assignment:**
   - **Tier 1:** If account has a valid `Area_Grouping` (not None / Unknown), use it directly
   - **Tier 2:** If no `Area_Grouping` but GPS falls within Gauteng bounding box (lat −27.2 to −25.0, lon 27.0 to 29.5) → assign `"Johannesburg"` (matches the existing `Area_Grouping` value used for tagged Gauteng accounts)
   - Accounts with neither tag nor Gauteng GPS are excluded
5. Merge area assignment back onto PVA invoice rows via `accno = Account_Site`
6. Aggregate `net` per area for `fy == 2024` and `fy == 2025`
7. Apply price deflator: `net_2025_adj = net_2025 / 1.10` — strips the ~10% annual list price increase to isolate real volume movement. Constant defined as `PRICE_DEFLATOR = 1.10` at top of script for easy future adjustment.
8. `pvaShrinkage = (net_2025_adj − net_2024) / net_2024 × 100`
9. `totalLoss = max(0, net_2024 − net_2025_adj)` (zero for areas with real volume growth after deflation)
10. Per area: top 5 SKUs by FY2024 net revenue, each with individual price-adjusted `loss` % and `competitor: null`
11. If `competitors-override.json` exists, merge `topCompetitor` and `competitorShare` by area `id`
12. Write to `1.Projects/AWS Data/pva_areas.json`

**Area definitions** (id = slugified Area_Grouping, x/y = viewport % on a simplified SA map):

| ID | Name | x% | y% | Notes |
|---|---|---|---|---|
| tzaneen | Tzaneen | 72 | 18 | Limpopo — highest PVA revenue area |
| venda | Venda | 78 | 10 | Far north Limpopo |
| mafakeng | Mafakeng | 28 | 52 | North West / Mahikeng |
| johannesburg | Johannesburg | 52 | 58 | Greater Gauteng (tagged + GPS-inferred) |
| groblersdal | Groblersdal | 65 | 40 | Limpopo/Mpumalanga border |
| free_state | Free State | 48 | 75 | Bloemfontein region |
| ermelo | Ermelo | 68 | 62 | Mpumalanga south |
| botswana | Botswana | 18 | 35 | Cross-border |
| mpumalanga | Mpumalanga | 74 | 48 | Nelspruit region |
| south_gauteng | South Gauteng | 50 | 65 | Vaal Triangle and south JHB |
| north_gauteng | North Gauteng | 52 | 48 | Pretoria / Tshwane |

**Output schema:**
```json
[{
  "id": "tzaneen",
  "name": "Tzaneen",
  "x": 72,
  "y": 18,
  "pvaShrinkage": 11.2,
  "totalLoss": 0,
  "topCompetitor": null,
  "competitorShare": null,
  "products": [
    { "name": "20L DECOR WHITE PVA", "loss": 8.4, "competitor": null }
  ]
}]
```

---

## Component Architecture — `PVAShrinkageDashboard.jsx`

Single file. All components defined inline. No sub-files.

```
App
├── Header          (fixed top bar — title + 4 KPI chips)
├── MapCanvas       (full-viewport, #080c14)
│   └── AreaBubble × 11  (absolutely positioned by x/y %)
├── SidePanel       (320px, slides in from right on area click)
└── Legend          (fixed bottom-left)
```

### Header KPIs
- **Total PVA Loss** — sum of all `totalLoss` values (rands, formatted)
- **Worst Area** — area with highest absolute negative `pvaShrinkage`
- **Best Area** — area with highest positive `pvaShrinkage` (growth signal)
- **No Competitor Data** badge — always shown (static, until override file populated)
- All derived via `useMemo([areas])`

### AreaBubble
- Diameter: `36 + (area.totalLoss / maxLoss) × 84` px (36–120px range). Growing areas (totalLoss = 0) render at 36px.
- Colour by shrinkage severity:
  - Green `#2D8C7A`: pvaShrinkage > −10% (growth or minor decline)
  - Yellow `#F5C400`: −10% to −20%
  - Orange `#C97A3A`: −20% to −35%
  - Red `#E86060`: < −35%
- Two layers: solid fill circle + pulsing ring (`@keyframes pulse-ring`)
- Area name label below
- Click → `setSelectedArea(area)`

### SidePanel
- 320px, `transform: translateX(100%)` → `translateX(0)` on open
- Content: area name, price-adjusted shrinkage % (with up/down arrow), FY2024 revenue, FY2025 price-adjusted revenue, total volume loss in rands, a footnote "Price-adjusted: FY2025 deflated by 10% to remove list price increase", "No competitor data — populate `competitors-override.json` to enable" notice, affected products table (SKU | price-adjusted % columns)
- Close: ESC key (`useEffect` keydown listener) or ✕ button
- When `topCompetitor` is non-null (override file populated): show competitor name + share bar

### Legend
- Severity colour swatches (green/yellow/orange/red) with % thresholds labelled
- Bubble size key: small (min loss) / large (max loss) with rand values
- "Competitor overlay: not available" line

---

## Error & Edge Case Handling

| Scenario | Behaviour |
|---|---|
| `pva_areas.json` missing / fetch fails | Canvas shows `⚠ pva_areas.json not found — run build_pva_shrinkage.py` |
| Loading | Centered CSS spinner; header KPIs show `—` |
| Area with totalLoss = 0 (growth) | Renders at 36px minimum, green, side panel says "Area is growing — +X%" |
| All areas growing | All bubbles 36px minimum; colour still reflects severity |
| `topCompetitor: null` | Side panel renders "no competitor data" notice; no competitor dot on bubble |

---

## Data Gap Report

| Field | Status | Notes |
|---|---|---|
| PVA sales by account, FY2024–FY2025 | ✅ Found | `Sales_Invoices_All.parquet`, `category_l1 == 'PVA Paints'`, 35,945 rows |
| Area tags for non-Gauteng accounts | ✅ Found | `Area_Grouping` field in accounts.parquet covers Tzaneen, Venda, Mafakeng, Groblersdal, Free State, Ermelo, Botswana, Mpumalanga, South/North Gauteng, Johannesburg — 36% of PVA revenue |
| GPS coordinates per account | ✅ Found | `accounts.parquet`, `Store_Coordinates`, 515/727 accounts have valid coords |
| Area tags for Gauteng untagged accounts | ⚠ Proxy | KK/KP/KE/KB prefix accounts (~64% of PVA revenue) have no `Area_Grouping`; assigned to "Johannesburg" via GPS bounding box |
| Competitor field | ❌ Missing | No competitor data in any source; `topCompetitor` and `competitorShare` set to null; `competitors-override.json` pattern wired up |
| Lost deal / churn reason | ❌ Missing | `reason` field on credit notes is operational (PRICE DIFFERENCE, OLD STOCK) — not competitor names |

---

## Refresh Workflow

```
1. New parquet dropped to 3.Resources/16.Sales and Other data/
2. python 1.Projects/AWS Data/build_pva_shrinkage.py
3. Commit pva_areas.json → push to GitHub Pages (or Vercel redeploy)
```

Optional: populate `competitors-override.json` with field intel from reps, re-run script to merge.
