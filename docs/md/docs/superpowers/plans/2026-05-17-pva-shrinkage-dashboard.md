# PVA Shrinkage Intelligence Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python build script that computes price-adjusted PVA shrinkage by region from the sales parquet and writes `pva_areas.json`, plus a single-file React dashboard that renders the data as a bubble map with a slide-in side panel.

**Architecture:** Python build script reads `Sales_Invoices_All.parquet` + `accounts.parquet`, assigns accounts to 11 regions via `Area_Grouping` tag (Tier 1) or GPS bounding box (Tier 2), deflates FY2025 revenue by 10% to strip price increases, computes shrinkage per region, and writes `pva_areas.json`. The React component (`PVAShrinkageDashboard.jsx`) fetches that JSON and renders a full-viewport dark map with absolutely-positioned bubbles, a fixed header with KPI chips, a slide-in side panel, and a legend. No backend required.

**Tech Stack:** Python 3, pandas, pyarrow — for build script. React (CDN, no bundler), Tailwind CSS (CDN), vanilla JS fetch — for dashboard. Deployable as a static HTML file to GitHub Pages or Vercel.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `1.Projects/AWS Data/build_pva_shrinkage.py` | Create | Data transform: parquet → `pva_areas.json` |
| `1.Projects/AWS Data/pva_areas.json` | Generated | Static data consumed by the dashboard |
| `1.Projects/AWS Data/competitors-override.json` | Create (stub) | Manual competitor override; merged at build time if present |
| `1.Projects/AWS Data/PVAShrinkageDashboard.html` | Create | Self-contained React dashboard (CDN React + Tailwind, fetches `pva_areas.json`) |
| `1.Projects/AWS Data/tests/test_pva_shrinkage.py` | Create | Unit tests for transform logic |

---

## Task 1: Test scaffold + area assignment logic

**Files:**
- Create: `1.Projects/AWS Data/tests/test_pva_shrinkage.py`
- Create: `1.Projects/AWS Data/build_pva_shrinkage.py` (skeleton only)

- [ ] **Step 1.1: Create the test file**

```python
# 1.Projects/AWS Data/tests/test_pva_shrinkage.py
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from build_pva_shrinkage import assign_area, parse_coord, PRICE_DEFLATOR


def test_parse_coord_valid():
    assert parse_coord("-26.268,27.858", 0) == pytest.approx(-26.268)
    assert parse_coord("-26.268,27.858", 1) == pytest.approx(27.858)


def test_parse_coord_garbage():
    assert np.isnan(parse_coord("1750.0,27.858", 0))   # lat > 90 → garbage
    assert np.isnan(parse_coord("not a coord", 0))


def test_assign_area_tier1_uses_area_grouping():
    row = pd.Series({"Area_Grouping": "Tzaneen", "lat": np.nan, "lon": np.nan})
    assert assign_area(row) == "Tzaneen"


def test_assign_area_tier1_ignores_unknown():
    row = pd.Series({"Area_Grouping": "Unknown", "lat": -26.3, "lon": 27.9})
    assert assign_area(row) == "Johannesburg"   # falls through to GPS tier


def test_assign_area_tier2_gauteng_gps():
    row = pd.Series({"Area_Grouping": None, "lat": -26.268, "lon": 27.858})
    assert assign_area(row) == "Johannesburg"


def test_assign_area_tier2_outside_gauteng():
    # Tzaneen GPS — no Area_Grouping tag, outside Gauteng bbox → excluded
    row = pd.Series({"Area_Grouping": None, "lat": -23.8, "lon": 30.1})
    assert assign_area(row) is None


def test_assign_area_no_data():
    row = pd.Series({"Area_Grouping": None, "lat": np.nan, "lon": np.nan})
    assert assign_area(row) is None


def test_price_deflator_constant():
    assert PRICE_DEFLATOR == pytest.approx(1.10)
```

- [ ] **Step 1.2: Create the script skeleton with just enough to make the tests runnable**

```python
# 1.Projects/AWS Data/build_pva_shrinkage.py
import json
import math
import numpy as np
import pandas as pd
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
PRICE_DEFLATOR = 1.10   # FY2025 net revenue divided by this to strip ~10% price increase

PARQUET_SALES   = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\16.Sales and Other data\Sales_Invoices_All.parquet")
PARQUET_ACCTS   = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings\data\accounts.parquet")
OVERRIDE_FILE   = Path(__file__).parent / "competitors-override.json"
OUT_JSON        = Path(__file__).parent / "pva_areas.json"

# Gauteng GPS bounding box for Tier-2 assignment
GAUTENG_LAT = (-27.2, -25.0)
GAUTENG_LON = (27.0, 29.5)

# Valid Area_Grouping values — anything else is treated as untagged
VALID_AREA_GROUPS = {
    "Tzaneen", "Venda", "Mafakeng", "Johannesburg",
    "Groblersdal", "Free State", "Ermelo", "Botswana",
    "Mpumalanga", "South Gauteng", "North Gauteng",
}

# Area metadata: Area_Grouping value → (id, display name, x%, y%)
AREA_META = {
    "Tzaneen":      ("tzaneen",      "Tzaneen",      72, 18),
    "Venda":        ("venda",        "Venda",        78, 10),
    "Mafakeng":     ("mafakeng",     "Mafakeng",     28, 52),
    "Johannesburg": ("johannesburg", "Johannesburg", 52, 58),
    "Groblersdal":  ("groblersdal",  "Groblersdal",  65, 40),
    "Free State":   ("free_state",   "Free State",   48, 75),
    "Ermelo":       ("ermelo",       "Ermelo",       68, 62),
    "Botswana":     ("botswana",     "Botswana",     18, 35),
    "Mpumalanga":   ("mpumalanga",   "Mpumalanga",   74, 48),
    "South Gauteng":("south_gauteng","South Gauteng",50, 65),
    "North Gauteng":("north_gauteng","North Gauteng",52, 48),
}


def parse_coord(s: str, idx: int) -> float:
    """Parse lat or lon from 'lat,lon' string. Returns NaN for garbage values."""
    try:
        val = float(str(s).split(",")[idx].strip())
        return val if abs(val) <= 90 else math.nan
    except Exception:
        return math.nan


def assign_area(row: pd.Series) -> str | None:
    """
    Tier 1: valid Area_Grouping tag → use it directly.
    Tier 2: no tag but GPS in Gauteng bbox → 'Johannesburg'.
    Otherwise: None (excluded from dashboard).
    """
    ag = row.get("Area_Grouping")
    if ag and ag in VALID_AREA_GROUPS:
        return ag
    lat, lon = row.get("lat"), row.get("lon")
    if (
        lat is not None and lon is not None
        and not (isinstance(lat, float) and math.isnan(lat))
        and not (isinstance(lon, float) and math.isnan(lon))
        and GAUTENG_LAT[0] <= lat <= GAUTENG_LAT[1]
        and GAUTENG_LON[0] <= lon <= GAUTENG_LON[1]
    ):
        return "Johannesburg"
    return None


if __name__ == "__main__":
    pass   # filled in Task 2
```

- [ ] **Step 1.3: Run the tests — expect all to pass**

```
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python -m pytest tests/test_pva_shrinkage.py -v
```

Expected output: 8 tests, all PASSED.

- [ ] **Step 1.4: Commit**

```
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/AWS Data/build_pva_shrinkage.py" "1.Projects/AWS Data/tests/test_pva_shrinkage.py"
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: pva shrinkage — area assignment logic + tests"
```

---

## Task 2: Aggregation + price deflation logic

**Files:**
- Modify: `1.Projects/AWS Data/tests/test_pva_shrinkage.py` (add aggregation tests)
- Modify: `1.Projects/AWS Data/build_pva_shrinkage.py` (add `compute_area_stats`)

- [ ] **Step 2.1: Add aggregation tests**

Append to `tests/test_pva_shrinkage.py`:

```python
from build_pva_shrinkage import compute_area_stats


def _make_pva_df(rows):
    """Helper: build a minimal PVA invoice DataFrame."""
    return pd.DataFrame(rows, columns=["area", "fy", "net", "prodname"])


def test_compute_area_stats_shrinkage():
    df = _make_pva_df([
        ("Tzaneen", 2024, 1000.0, "20L DECOR WHITE PVA"),
        ("Tzaneen", 2025, 990.0,  "20L DECOR WHITE PVA"),  # raw +990 → adj 990/1.10 = 900
    ])
    stats = compute_area_stats(df)
    tz = next(s for s in stats if s["id"] == "tzaneen")
    # adj net_2025 = 990 / 1.10 = 900 → shrinkage = (900-1000)/1000*100 = -10%
    assert tz["pvaShrinkage"] == pytest.approx(-10.0, abs=0.01)
    assert tz["totalLoss"] == pytest.approx(100.0, abs=0.01)


def test_compute_area_stats_growth_clips_loss_to_zero():
    df = _make_pva_df([
        ("Venda", 2024, 500.0, "20L DECOR CREAM PVA"),
        ("Venda", 2025, 700.0, "20L DECOR CREAM PVA"),  # adj 700/1.10 = 636 → growth
    ])
    stats = compute_area_stats(df)
    vd = next(s for s in stats if s["id"] == "venda")
    assert vd["totalLoss"] == 0.0
    assert vd["pvaShrinkage"] > 0


def test_compute_area_stats_top5_skus():
    rows = [
        ("Ermelo", 2024, float(i * 100), f"SKU_{i}") for i in range(1, 8)
    ] + [
        ("Ermelo", 2025, float(i * 80),  f"SKU_{i}") for i in range(1, 8)
    ]
    df = _make_pva_df(rows)
    stats = compute_area_stats(df)
    em = next(s for s in stats if s["id"] == "ermelo")
    assert len(em["products"]) == 5
    # top SKU by FY2024 revenue is SKU_7 (700)
    assert em["products"][0]["name"] == "SKU_7"


def test_compute_area_stats_competitor_null():
    df = _make_pva_df([
        ("Botswana", 2024, 200.0, "SKU_A"),
        ("Botswana", 2025, 180.0, "SKU_A"),
    ])
    stats = compute_area_stats(df)
    bt = next(s for s in stats if s["id"] == "botswana")
    assert bt["topCompetitor"] is None
    assert bt["competitorShare"] is None
    assert all(p["competitor"] is None for p in bt["products"])


def test_compute_area_stats_excludes_unknown_areas():
    df = _make_pva_df([
        ("Unknown Region", 2024, 999.0, "SKU_X"),
        ("Unknown Region", 2025, 888.0, "SKU_X"),
    ])
    stats = compute_area_stats(df)
    ids = [s["id"] for s in stats]
    assert "unknown_region" not in ids
```

- [ ] **Step 2.2: Run tests — expect new tests to FAIL**

```
python -m pytest tests/test_pva_shrinkage.py -v
```

Expected: the 5 new `compute_area_stats` tests fail with `ImportError` or `NameError`.

- [ ] **Step 2.3: Implement `compute_area_stats` in `build_pva_shrinkage.py`**

Add this function after the `assign_area` function:

```python
def compute_area_stats(df: pd.DataFrame) -> list[dict]:
    """
    Given a DataFrame with columns [area, fy, net, prodname],
    compute per-area shrinkage after price deflation and return
    the AREAS list ready for JSON serialisation.
    """
    results = []

    for area_group, area_df in df.groupby("area"):
        if area_group not in AREA_META:
            continue

        area_id, area_name, x_pct, y_pct = AREA_META[area_group]

        net_2024 = area_df[area_df["fy"] == 2024]["net"].sum()
        net_2025_raw = area_df[area_df["fy"] == 2025]["net"].sum()
        net_2025_adj = net_2025_raw / PRICE_DEFLATOR

        if net_2024 == 0:
            shrinkage = 0.0
        else:
            shrinkage = (net_2025_adj - net_2024) / net_2024 * 100

        total_loss = max(0.0, net_2024 - net_2025_adj)

        # Top 5 SKUs by FY2024 revenue
        sku_2024 = (
            area_df[area_df["fy"] == 2024]
            .groupby("prodname")["net"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        sku_2025 = (
            area_df[area_df["fy"] == 2025]
            .groupby("prodname")["net"]
            .sum()
        )

        products = []
        for sku_name, rev_2024 in sku_2024.items():
            rev_2025_raw = sku_2025.get(sku_name, 0.0)
            rev_2025_adj = rev_2025_raw / PRICE_DEFLATOR
            if rev_2024 == 0:
                sku_loss = 0.0
            else:
                sku_loss = (rev_2025_adj - rev_2024) / rev_2024 * 100
            products.append({
                "name": sku_name,
                "loss": round(sku_loss, 1),
                "competitor": None,
            })

        results.append({
            "id": area_id,
            "name": area_name,
            "x": x_pct,
            "y": y_pct,
            "pvaShrinkage": round(shrinkage, 1),
            "totalLoss": round(total_loss, 2),
            "topCompetitor": None,
            "competitorShare": None,
            "products": products,
        })

    return results
```

- [ ] **Step 2.4: Run tests — expect all to pass**

```
python -m pytest tests/test_pva_shrinkage.py -v
```

Expected: 13 tests, all PASSED.

- [ ] **Step 2.5: Commit**

```
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/AWS Data/build_pva_shrinkage.py" "1.Projects/AWS Data/tests/test_pva_shrinkage.py"
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: pva shrinkage — aggregation + price deflation logic"
```

---

## Task 3: Full build pipeline + JSON output

**Files:**
- Modify: `1.Projects/AWS Data/build_pva_shrinkage.py` (add `main()`)
- Create: `1.Projects/AWS Data/competitors-override.json` (stub)

- [ ] **Step 3.1: Create the competitors-override stub**

```json
[]
```

Save to `1.Projects/AWS Data/competitors-override.json`. This is the user-editable file. Format when populated:

```json
[
  {
    "id": "south_gauteng",
    "topCompetitor": "Eclipse",
    "competitorShare": 35
  }
]
```

- [ ] **Step 3.2: Add `main()` to `build_pva_shrinkage.py`**

Replace the `if __name__ == "__main__": pass` block at the bottom with:

```python
def main():
    import pyarrow.parquet as pq

    print("Loading parquet files...")
    df_sales = pq.read_table(PARQUET_SALES).to_pandas()
    df_accts = pq.read_table(PARQUET_ACCTS).to_pandas()

    # ── Parse GPS coords ──────────────────────────────────────────────────────
    df_accts["lat"] = df_accts["Store_Coordinates"].apply(lambda s: parse_coord(str(s), 0))
    df_accts["lon"] = df_accts["Store_Coordinates"].apply(lambda s: parse_coord(str(s), 1))

    # ── Assign area to each account ───────────────────────────────────────────
    df_accts["area"] = df_accts.apply(assign_area, axis=1)
    acct_area = df_accts[df_accts["area"].notna()][["Account_Site", "area"]]

    # ── Filter PVA invoices, sign net revenue ─────────────────────────────────
    pva = df_sales[df_sales["category_l1"] == "PVA Paints"].copy()
    pva["net"] = pva["ivnett"] * pva["ivtype"].map({"INVOICE": 1.0, "CRNOTE": -1.0})
    pva = pva[pva["fy"].isin([2024, 2025])]

    # ── Join area onto invoices via accno = Account_Site ──────────────────────
    pva = pva.merge(acct_area, left_on="accno", right_on="Account_Site", how="inner")

    # ── Compute per-area stats ────────────────────────────────────────────────
    areas = compute_area_stats(pva[["area", "fy", "net", "prodname"]])

    # ── Merge competitor override if present ──────────────────────────────────
    if OVERRIDE_FILE.exists():
        overrides = {o["id"]: o for o in json.loads(OVERRIDE_FILE.read_text())}
        for area in areas:
            if area["id"] in overrides:
                ov = overrides[area["id"]]
                area["topCompetitor"] = ov.get("topCompetitor")
                area["competitorShare"] = ov.get("competitorShare")
                for p in area["products"]:
                    p["competitor"] = ov.get("topCompetitor")

    # ── Write JSON ────────────────────────────────────────────────────────────
    OUT_JSON.write_text(json.dumps(areas, indent=2))
    print(f"Written {len(areas)} areas to {OUT_JSON}")
    for a in sorted(areas, key=lambda x: x["pvaShrinkage"]):
        direction = "▼" if a["pvaShrinkage"] < 0 else "▲"
        print(f"  {a['name']:<18} {direction} {a['pvaShrinkage']:+.1f}%  loss R{a['totalLoss']:,.0f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3.3: Run the build script and verify output**

```
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python build_pva_shrinkage.py
```

Expected output — something like:
```
Loading parquet files...
Written 11 areas to ...\pva_areas.json
  South Gauteng      ▼ -44.x%  loss R...
  Ermelo             ▼ -29.x%  loss R...
  ...
  Venda              ▲ +26.x%  loss R0
  Free State         ▲ +24.x%  loss R0
```

Verify `pva_areas.json` is valid JSON with 11 area objects, each having the required keys: `id`, `name`, `x`, `y`, `pvaShrinkage`, `totalLoss`, `topCompetitor`, `competitorShare`, `products`.

```
python -c "import json; d=json.load(open('pva_areas.json')); print(len(d), 'areas'); print([a['id'] for a in d])"
```

- [ ] **Step 3.4: Commit**

```
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/AWS Data/build_pva_shrinkage.py" "1.Projects/AWS Data/pva_areas.json" "1.Projects/AWS Data/competitors-override.json"
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: pva shrinkage — full build pipeline, pva_areas.json generated"
```

---

## Task 4: React dashboard — structure, header, map canvas

**Files:**
- Create: `1.Projects/AWS Data/PVAShrinkageDashboard.html`

- [ ] **Step 4.1: Create the HTML shell with CDN imports and inline React skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PVA Shrinkage Intelligence — Olympic Paints</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<script src="https://cdn.tailwindcss.com"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

@keyframes pulse-ring {
  0%   { transform: scale(1);   opacity: 0.6; }
  70%  { transform: scale(1.6); opacity: 0;   }
  100% { transform: scale(1.6); opacity: 0;   }
}

.pulse-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  animation: pulse-ring 2.4s ease-out infinite;
}

.side-panel {
  transition: transform 0.28s cubic-bezier(0.4,0,0.2,1);
}

.spinner {
  width: 40px; height: 40px;
  border: 3px solid rgba(255,255,255,0.15);
  border-top-color: #F5C400;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body style="background:#080c14; color:#e8e7e2; font-family:'Barlow',sans-serif;">

<div id="root"></div>

<script type="text/babel">
const { useState, useEffect, useMemo, useCallback } = React;

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n) => `R${Math.abs(n).toLocaleString("en-ZA", { maximumFractionDigits: 0 })}`;

function bubbleColour(shrinkage) {
  if (shrinkage > -10) return "#2D8C7A";   // green  — growth or <10% decline
  if (shrinkage > -20) return "#F5C400";   // yellow — 10–20%
  if (shrinkage > -35) return "#C97A3A";   // orange — 20–35%
  return "#E86060";                         // red    — >35%
}

function bubbleDiameter(totalLoss, maxLoss) {
  if (maxLoss === 0) return 36;
  return 36 + (totalLoss / maxLoss) * 84;
}

// ── Header ───────────────────────────────────────────────────────────────────
function Header({ areas }) {
  const { totalLoss, worstArea, bestArea } = useMemo(() => {
    if (!areas.length) return { totalLoss: 0, worstArea: null, bestArea: null };
    const tl = areas.reduce((s, a) => s + a.totalLoss, 0);
    const worst = areas.reduce((a, b) => a.pvaShrinkage < b.pvaShrinkage ? a : b);
    const best  = areas.reduce((a, b) => a.pvaShrinkage > b.pvaShrinkage ? a : b);
    return { totalLoss: tl, worstArea: worst, bestArea: best };
  }, [areas]);

  const Chip = ({ label, value, colour }) => (
    <div className="flex flex-col px-4 py-2 rounded" style={{ background: "rgba(255,255,255,0.06)" }}>
      <span style={{ fontSize: 10, color: "#949390", textTransform: "uppercase", letterSpacing: "0.1em" }}>{label}</span>
      <span style={{ fontSize: 16, fontWeight: 700, color: colour || "#e8e7e2" }}>{value}</span>
    </div>
  );

  return (
    <div className="fixed top-0 left-0 right-0 z-20 flex items-center gap-3 px-5 py-3"
         style={{ background: "rgba(8,12,20,0.92)", backdropFilter: "blur(8px)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
      <div style={{ width: 36, height: 36, borderRadius: "50%", overflow: "hidden", flexShrink: 0 }}>
        <img src="logo.jpg" alt="Olympic Paints" width="36" height="36"
             style={{ display: "block", width: "100%", height: "100%", objectFit: "cover" }}
             onError={e => { e.target.style.display = "none"; }} />
      </div>
      <div className="mr-4">
        <div style={{ fontSize: 13, fontWeight: 700, color: "#F5C400", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          PVA Shrinkage Intelligence
        </div>
        <div style={{ fontSize: 10, color: "#5C5B58" }}>FY2024 vs FY2025 · Price-adjusted (−10%)</div>
      </div>
      <div className="flex gap-2 flex-wrap">
        <Chip label="Total Volume Loss" value={areas.length ? fmt(totalLoss) : "—"} colour="#E86060" />
        <Chip label="Worst Area"        value={worstArea ? `${worstArea.name} (${worstArea.pvaShrinkage.toFixed(1)}%)` : "—"} colour="#E86060" />
        <Chip label="Best Area"         value={bestArea  ? `${bestArea.name} (+${bestArea.pvaShrinkage.toFixed(1)}%)`  : "—"} colour="#2D8C7A" />
        <Chip label="Competitor Data"   value="Not available" colour="#5C5B58" />
      </div>
    </div>
  );
}

// ── AreaBubble ────────────────────────────────────────────────────────────────
function AreaBubble({ area, maxLoss, onSelect }) {
  const d   = bubbleDiameter(area.totalLoss, maxLoss);
  const col = bubbleColour(area.pvaShrinkage);

  return (
    <div
      onClick={() => onSelect(area)}
      style={{
        position: "absolute",
        left: `${area.x}%`,
        top:  `${area.y}%`,
        transform: "translate(-50%, -50%)",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
      }}
    >
      <div style={{ position: "relative", width: d, height: d }}>
        {/* Pulsing ring */}
        <div className="pulse-ring" style={{ background: col }} />
        {/* Solid bubble */}
        <div style={{
          position: "absolute", inset: 0,
          borderRadius: "50%",
          background: col,
          opacity: 0.85,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: Math.max(9, d / 6), fontWeight: 700, color: "#080c14" }}>
            {area.pvaShrinkage > 0 ? "+" : ""}{area.pvaShrinkage.toFixed(0)}%
          </span>
        </div>
      </div>
      <span style={{ fontSize: 10, color: "#c8c7c0", textTransform: "uppercase",
                     letterSpacing: "0.08em", whiteSpace: "nowrap", textShadow: "0 1px 4px #080c14" }}>
        {area.name}
      </span>
    </div>
  );
}

// ── SidePanel ─────────────────────────────────────────────────────────────────
function SidePanel({ area, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const isOpen = !!area;

  return (
    <div className="side-panel fixed top-0 right-0 bottom-0 z-30 overflow-y-auto"
         style={{
           width: 320,
           background: "#0d111c",
           borderLeft: "1px solid rgba(255,255,255,0.08)",
           transform: isOpen ? "translateX(0)" : "translateX(100%)",
         }}>
      {area && (
        <div className="p-5">
          {/* Header row */}
          <div className="flex justify-between items-start mb-5">
            <div>
              <div style={{ fontSize: 11, color: "#5C5B58", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                Area
              </div>
              <div style={{ fontSize: 22, fontWeight: 800, color: "#e8e7e2" }}>{area.name}</div>
            </div>
            <button onClick={onClose}
                    style={{ background: "none", border: "none", color: "#5C5B58", fontSize: 20, cursor: "pointer", lineHeight: 1 }}>
              ✕
            </button>
          </div>

          {/* Shrinkage KPI */}
          <div className="rounded p-4 mb-3" style={{ background: "rgba(255,255,255,0.04)" }}>
            <div style={{ fontSize: 10, color: "#5C5B58", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>
              Price-Adjusted Shrinkage
            </div>
            <div style={{ fontSize: 32, fontWeight: 900, color: bubbleColour(area.pvaShrinkage) }}>
              {area.pvaShrinkage > 0 ? "▲" : "▼"} {Math.abs(area.pvaShrinkage).toFixed(1)}%
            </div>
            <div style={{ fontSize: 11, color: "#5C5B58", marginTop: 4 }}>
              FY2025 deflated by 10% to remove list price increase
            </div>
          </div>

          {/* Revenue rows */}
          <div className="rounded p-4 mb-3" style={{ background: "rgba(255,255,255,0.04)" }}>
            {[
              ["FY2024 Revenue",              fmt(area.totalLoss + (area.pvaShrinkage <= 0
                ? (area.totalLoss / (1 - area.pvaShrinkage / 100)) : 0))],
              ["Volume Loss",                 area.totalLoss > 0 ? fmt(area.totalLoss) : "—  (Growing)"],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between py-1"
                   style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", fontSize: 13 }}>
                <span style={{ color: "#949390" }}>{label}</span>
                <span style={{ fontWeight: 600 }}>{value}</span>
              </div>
            ))}
          </div>

          {/* Competitor notice */}
          <div className="rounded p-4 mb-3"
               style={{ background: "rgba(201,122,58,0.08)", border: "1px solid rgba(201,122,58,0.2)" }}>
            <div style={{ fontSize: 11, color: "#C97A3A", fontWeight: 600, marginBottom: 4 }}>
              Competitor Data Unavailable
            </div>
            <div style={{ fontSize: 12, color: "#949390", lineHeight: 1.5 }}>
              No competitor field exists in the CRM or invoice data.
              Populate <code style={{ color: "#F5C400" }}>competitors-override.json</code> with
              field intelligence from reps, then re-run <code style={{ color: "#F5C400" }}>build_pva_shrinkage.py</code>.
            </div>
          </div>

          {/* Products table */}
          {area.products.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#5C5B58", textTransform: "uppercase",
                            letterSpacing: "0.1em", marginBottom: 8 }}>
                Top SKUs (FY2024 Revenue)
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                <thead>
                  <tr style={{ color: "#5C5B58" }}>
                    <th style={{ textAlign: "left", paddingBottom: 6, fontWeight: 500 }}>Product</th>
                    <th style={{ textAlign: "right", paddingBottom: 6, fontWeight: 500 }}>YoY %</th>
                  </tr>
                </thead>
                <tbody>
                  {area.products.map((p, i) => (
                    <tr key={i} style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "6px 0", color: "#c8c7c0", maxWidth: 200,
                                   whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {p.name}
                      </td>
                      <td style={{ padding: "6px 0", textAlign: "right",
                                   color: p.loss >= 0 ? "#2D8C7A" : "#E86060", fontWeight: 600 }}>
                        {p.loss > 0 ? "+" : ""}{p.loss.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Legend ────────────────────────────────────────────────────────────────────
function Legend({ areas }) {
  const maxLoss = useMemo(() => Math.max(...areas.map(a => a.totalLoss), 0), [areas]);
  const minLoss = useMemo(() => Math.min(...areas.filter(a => a.totalLoss > 0).map(a => a.totalLoss), 0), [areas]);

  const severities = [
    { colour: "#2D8C7A", label: "< −10%  (growth / stable)" },
    { colour: "#F5C400", label: "−10% to −20%" },
    { colour: "#C97A3A", label: "−20% to −35%" },
    { colour: "#E86060", label: "> −35%  (severe)" },
  ];

  return (
    <div className="fixed bottom-5 left-5 z-20 rounded-lg p-4"
         style={{ background: "rgba(8,12,20,0.88)", backdropFilter: "blur(8px)",
                  border: "1px solid rgba(255,255,255,0.08)", minWidth: 200 }}>
      <div style={{ fontSize: 10, color: "#5C5B58", textTransform: "uppercase",
                    letterSpacing: "0.1em", marginBottom: 8 }}>Shrinkage Severity</div>
      {severities.map(s => (
        <div key={s.colour} className="flex items-center gap-2 mb-1">
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: s.colour, flexShrink: 0 }} />
          <span style={{ fontSize: 11, color: "#949390" }}>{s.label}</span>
        </div>
      ))}
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.07)", marginTop: 8, paddingTop: 8 }}>
        <div style={{ fontSize: 10, color: "#5C5B58", textTransform: "uppercase",
                      letterSpacing: "0.1em", marginBottom: 6 }}>Bubble = Volume Loss</div>
        <div className="flex items-center gap-2">
          <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#E86060", opacity: 0.8 }} />
          <span style={{ fontSize: 11, color: "#949390" }}>Small = {fmt(minLoss)}</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div style={{ width: 24, height: 24, borderRadius: "50%", background: "#E86060", opacity: 0.8 }} />
          <span style={{ fontSize: 11, color: "#949390" }}>Large = {fmt(maxLoss)}</span>
        </div>
      </div>
      <div style={{ borderTop: "1px solid rgba(255,255,255,0.07)", marginTop: 8, paddingTop: 8,
                    fontSize: 11, color: "#5C5B58" }}>
        ⚠ Competitor overlay: not available
      </div>
    </div>
  );
}

// ── App (root) ────────────────────────────────────────────────────────────────
function App() {
  const [areas, setAreas]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [selectedArea, setSelected] = useState(null);

  useEffect(() => {
    fetch("pva_areas.json")
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => { setAreas(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  const maxLoss = useMemo(() => Math.max(...areas.map(a => a.totalLoss), 0), [areas]);
  const onClose = useCallback(() => setSelected(null), []);

  if (loading) return (
    <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="spinner" />
    </div>
  );

  if (error) return (
    <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
                  flexDirection: "column", gap: 12 }}>
      <span style={{ fontSize: 32 }}>⚠</span>
      <div style={{ color: "#E86060", fontWeight: 600 }}>pva_areas.json not found</div>
      <div style={{ color: "#5C5B58", fontSize: 13 }}>Run <code>python build_pva_shrinkage.py</code> to generate data</div>
    </div>
  );

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden", background: "#080c14" }}>
      <Header areas={areas} />

      {/* Map canvas */}
      <div style={{ position: "absolute", inset: 0, paddingTop: 60 }}>
        {areas.map(area => (
          <AreaBubble key={area.id} area={area} maxLoss={maxLoss} onSelect={setSelected} />
        ))}
      </div>

      <SidePanel area={selectedArea} onClose={onClose} />
      <Legend areas={areas} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
</script>
</body>
</html>
```

- [ ] **Step 4.2: Open the dashboard in a browser to verify it loads**

Open `1.Projects/AWS Data/PVAShrinkageDashboard.html` in Chrome. Because `fetch("pva_areas.json")` requires a server (CORS), serve it locally:

```
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data"
python -m http.server 8500
```

Then open `http://localhost:8500/PVAShrinkageDashboard.html`.

Expected: 11 coloured bubbles visible on the dark canvas, header KPI chips populated, no console errors.

- [ ] **Step 4.3: QA checklist — work through all 7 items**

- [ ] All 11 area bubbles render at their x/y positions
- [ ] Bubble sizes vary correctly (larger = more loss)
- [ ] Click a shrinking area (red/orange) → side panel slides in from right
- [ ] Side panel shows name, shrinkage %, volume loss, competitor notice, products table
- [ ] ESC key closes the panel; ✕ button closes the panel
- [ ] Header KPIs (Total Loss, Worst Area, Best Area) match manual inspection of `pva_areas.json`
- [ ] No hardcoded placeholder values — all figures come from `pva_areas.json`

Fix any issues before continuing.

- [ ] **Step 4.4: Commit**

```
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" add "1.Projects/AWS Data/PVAShrinkageDashboard.html"
git -C "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints" commit -m "feat: pva shrinkage dashboard — full React component"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| Filter PVA only (`category_l1 == 'PVA Paints'`) | Task 3, `main()` |
| Sign ivnett by ivtype | Task 3, `main()` |
| Two-tier area assignment | Task 1, `assign_area()` |
| Price deflator 10% on FY2025 | Task 2, `compute_area_stats()` |
| pvaShrinkage formula | Task 2 |
| totalLoss clipped to 0 for growth | Task 2 |
| Top 5 SKUs per area with price-adjusted loss% | Task 2 |
| competitors-override.json merge | Task 3, `main()` |
| pva_areas.json output with exact schema | Task 3 |
| Full-viewport dark canvas (#080c14) | Task 4 |
| Bubble size = totalLoss, 36–120px | Task 4, `bubbleDiameter()` |
| Bubble colour by severity | Task 4, `bubbleColour()` |
| Pulsing ring animation | Task 4, CSS keyframes |
| Area name label below bubble | Task 4, `AreaBubble` |
| Click → 320px slide-in side panel | Task 4, `SidePanel` |
| ESC + ✕ close panel | Task 4, `SidePanel` useEffect |
| Header: total loss, worst area, best area, no-competitor badge | Task 4, `Header` |
| Legend: severity + size key + competitor notice | Task 4, `Legend` |
| Error state for missing JSON | Task 4, `App` |
| Loading spinner | Task 4, `App` |
| No hardcoded values | Task 4 — all from JSON |
| Price-adjustment footnote in side panel | Task 4, `SidePanel` |

All spec requirements covered. No placeholders found. Type/method names consistent across all tasks.
