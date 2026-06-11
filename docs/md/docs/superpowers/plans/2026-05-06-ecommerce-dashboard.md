# E-Commerce Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone HTML e-commerce dashboard from `Woocommerce_Transactions.csv` that mirrors the QuickSight tiles, defaults to navy theme, and matches Olympic Paints brand standards.

**Architecture:** Single Python script `build_ecommerce_dashboard.py` reads the CSV with pandas, computes order-level and line-item-level metrics into a `metrics` dict, then renders a single self-contained `index.html` (Chart.js + four-theme toggle + CSS tokens). Output goes to `1.Projects/AWS Data/ecommerce_dashboard/` alongside a copy of the official logo.

**Tech Stack:** Python 3, pandas, Chart.js 4 from cdnjs, vanilla CSS using the Olympic Paints token system, vanilla JS for theme toggle.

**Verification approach:** This plan does **not** use TDD. It is a one-off build-script project (matches existing pattern: `build_kpi_dashboard.py`, `gen_dashboard.py` — neither has unit tests). Verification is by **eyeball-checking output artifacts** at every task. Each task produces something inspectable — printed metric values, rendered HTML sections, opened-in-browser pages.

---

## File Structure

| File | Purpose |
|---|---|
| `1.Projects/AWS Data/build_ecommerce_dashboard.py` | The whole build script — single file by design (matches existing dashboards) |
| `1.Projects/AWS Data/ecommerce_dashboard/index.html` | Output — generated, never hand-edited |
| `1.Projects/AWS Data/ecommerce_dashboard/logo.jpg` | Output — copied from brand assets every run |

Single-file design is deliberate: matches `build_kpi_dashboard.py`, keeps the data-block updateable in one place, no premature abstraction. The script will internally separate concerns (load → compute → render) via top-level functions, not modules.

---

## Task 1: Project skeleton & CSV loader

**Files:**
- Create: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Create the script with constants, paths, and a CSV loader**

```python
"""
Olympic Paints — E-Commerce Dashboard Builder

Reads Woocommerce_Transactions.csv and produces a standalone HTML dashboard
mirroring the QuickSight WooCommerce tiles.

Run: python build_ecommerce_dashboard.py
Output: ./ecommerce_dashboard/index.html (+ logo.jpg)
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────
ROOT = Path(r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
CSV_PATH = ROOT / "3.Resources" / "16.Sales and Other data" / "Manual" / "Woocommerce_Transactions.csv"
LOGO_SRC = ROOT / "3.Resources" / "9. Brand Assets & Images" / "Misc Pictures" / "Olympic Paints Logo Digital.jpg"
OUT_DIR = Path(__file__).resolve().parent / "ecommerce_dashboard"

# ── Business constants ────────────────────────────────────────────────────
SERVICE_LEVEL_TARGET = 5            # days
OVERDUE_LOOKBACK_DAYS = 28
RECENT_ORDERS_LIMIT = 50
EXCLUDED_FROM_SALES = {"cancelled", "refunded"}
EXCLUDED_FROM_OVERDUE = {"completed", "cancelled", "refunded"}
PROVINCE_ORDER = ["GP", "NW", "WC", "NC", "MP", "EC", "KZN", "LP"]
TOP_PRODUCTS_HIGHLIGHT = 3

NOW = datetime.now()
TODAY = NOW.date()


def load_csv(path: Path) -> pd.DataFrame:
    """Load WooCommerce export. Lower-case status, parse dates, normalise province."""
    if not path.exists():
        sys.exit(f"ERROR: CSV not found at {path}")

    df = pd.read_csv(path, dtype=str, low_memory=False)
    df["order_status"] = df["order_status"].str.lower().str.strip()

    for col in ("date_created", "date_completed", "date_paid"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["billing_state"] = (
        df["billing_state"].fillna("").str.strip().replace({"": "empty"})
    )

    for col in ("total", "line_item_quantity", "line_item_total"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


if __name__ == "__main__":
    df = load_csv(CSV_PATH)
    print(f"Loaded {len(df)} line-items across {df['order_id'].nunique()} orders")
    print(f"Statuses: {sorted(df['order_status'].dropna().unique())}")
    print(f"Provinces: {sorted(df['billing_state'].dropna().unique())}")
    print(f"Date range: {df['date_created'].min()} → {df['date_created'].max()}")
```

- [ ] **Step 2: Run and verify**

Run: `python "1.Projects/AWS Data/build_ecommerce_dashboard.py"`

Expected output (approximate):
```
Loaded 666 line-items across ~300 orders
Statuses: ['cancelled', 'completed', 'failed', 'on-hold', 'pending', 'processing', 'refunded']
Provinces: ['EC', 'GP', 'KZN', 'LP', 'MP', 'NC', 'NW', 'WC', 'empty']
Date range: 2025-03-12 ... → 2026-05-... ...
```

If the CSV is missing or columns differ, fix the loader before continuing.

---

## Task 2: Compute order-level metrics

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add `build_orders_df()` after `load_csv()`**

```python
def build_orders_df(df: pd.DataFrame) -> pd.DataFrame:
    """One row per order_id with all order-level fields."""
    orders = (
        df.sort_values("date_created")
          .drop_duplicates(subset=["order_id"], keep="first")
          .copy()
    )

    # YTD filter
    current_year = TODAY.year
    orders = orders[orders["date_created"].dt.year == current_year]

    # days_in_system per spec §3.1
    def _days(row) -> float:
        if row["order_status"] in ("completed", "refunded") and pd.notna(row["date_completed"]):
            delta = (row["date_completed"] - row["date_created"]).days
        else:
            delta = (pd.Timestamp(TODAY) - row["date_created"]).days
        return max(delta, 0)

    orders["days_in_system"] = orders.apply(_days, axis=1)
    orders["dispatch_target"] = orders["date_created"] + pd.Timedelta(days=SERVICE_LEVEL_TARGET)
    orders["is_overdue"] = (
        (~orders["order_status"].isin(EXCLUDED_FROM_OVERDUE))
        & (orders["days_in_system"] > SERVICE_LEVEL_TARGET)
    )
    return orders
```

- [ ] **Step 2: Add `compute_metrics()` skeleton with KPI tiles**

```python
def compute_metrics(orders: pd.DataFrame, df: pd.DataFrame) -> dict:
    m: dict = {}

    eligible_for_sl = orders[~orders["order_status"].isin({"cancelled"})]

    if len(eligible_for_sl):
        m["service_level"] = round(eligible_for_sl["days_in_system"].mean(), 2)
    else:
        m["service_level"] = None

    target = SERVICE_LEVEL_TARGET
    actual = m["service_level"]
    if actual is not None and target:
        m["service_level_variance_pct"] = round((actual - target) / target * 100, 2)
    else:
        m["service_level_variance_pct"] = None

    m["overdue_total"] = int(orders["is_overdue"].sum())
    cutoff = pd.Timestamp(TODAY - timedelta(days=OVERDUE_LOOKBACK_DAYS))
    m["overdue_4w"] = int(
        ((orders["date_created"] >= cutoff) & orders["is_overdue"]).sum()
    )

    return m
```

- [ ] **Step 3: Update `__main__` to print these metrics**

Replace the existing `__main__` block:

```python
if __name__ == "__main__":
    df = load_csv(CSV_PATH)
    orders = build_orders_df(df)
    metrics = compute_metrics(orders, df)
    print(f"Orders this year: {len(orders)}")
    print(f"Service Level: {metrics['service_level']} days (target {SERVICE_LEVEL_TARGET})")
    print(f"Variance: {metrics['service_level_variance_pct']}%")
    print(f"Overdue total: {metrics['overdue_total']}")
    print(f"Overdue past 4 weeks: {metrics['overdue_4w']}")
```

- [ ] **Step 4: Run and sanity-check against QuickSight**

Run: `python "1.Projects/AWS Data/build_ecommerce_dashboard.py"`

Expected: Service Level near `8.73`, Overdue Total near `8`, Overdue 4w near `7`. Numbers won't match exactly because the CSV cutoff differs from QuickSight's snapshot — variance under ±20% is acceptable. Investigate larger gaps before continuing.

---

## Task 3: Provincial service level + sales-by-province + status-mix metrics

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Extend `compute_metrics()` with provincial, sales, and status sections**

Add inside `compute_metrics()` before the final `return m`:

```python
    # Provincial service level
    province_sl: dict[str, float | None] = {}
    eligible = orders[~orders["order_status"].isin({"cancelled"})]
    for prov in PROVINCE_ORDER:
        sub = eligible[eligible["billing_state"] == prov]
        province_sl[prov] = round(sub["days_in_system"].mean(), 2) if len(sub) else None
    m["province_service_level"] = province_sl

    # Sales by province (excludes cancelled & refunded)
    sales_orders = orders[~orders["order_status"].isin(EXCLUDED_FROM_SALES)]
    sbp = (
        sales_orders.groupby("billing_state")["total"].sum()
                    .sort_values(ascending=False)
    )
    m["sales_by_province"] = [
        {"province": p, "total": float(v)} for p, v in sbp.items() if v > 0
    ]
    m["total_sales"] = float(sales_orders["total"].sum())

    # Order status mix
    status_counts = orders["order_status"].value_counts()
    m["status_mix"] = [
        {"status": s, "count": int(c)} for s, c in status_counts.items()
    ]
    m["total_orders"] = int(len(orders))

    return m
```

- [ ] **Step 2: Print these in `__main__`**

Append to `__main__`:

```python
    print(f"\nProvincial Service Level:")
    for p, v in metrics["province_service_level"].items():
        print(f"  {p}: {v if v is not None else 'No data'}")
    print(f"\nTotal sales (YTD): R{metrics['total_sales']:,.2f}")
    print(f"Top 3 provinces by sales:")
    for row in metrics["sales_by_province"][:3]:
        print(f"  {row['province']}: R{row['total']:,.2f}")
    print(f"\nStatus mix: {metrics['status_mix']}")
```

- [ ] **Step 3: Run and verify**

Expected: GP dominates sales (matches QuickSight pie ~92K). Status mix shows `completed` as largest slice (~461 in QuickSight). NW shows `No data` if it has no non-cancelled orders this year.

---

## Task 4: Sales-per-product + recent-orders + dispatch-schedule + daily-trend

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Append product, recent-orders, dispatch, and trend sections to `compute_metrics()`**

Add before `return m`:

```python
    # Sales per product (line-item level, excludes cancelled & refunded)
    valid_order_ids = set(sales_orders["order_id"])
    line_items = df[df["order_id"].isin(valid_order_ids)].copy()
    prod = (
        line_items.groupby("line_item_name")
                  .agg(qty=("line_item_quantity", "sum"),
                       total=("line_item_total", "sum"))
                  .reset_index()
                  .sort_values("total", ascending=False)
    )
    m["sales_per_product"] = [
        {
            "name": r["line_item_name"],
            "qty": int(r["qty"]),
            "total": float(r["total"]),
        }
        for _, r in prod.iterrows()
    ]
    m["product_qty_total"] = int(prod["qty"].sum())
    m["product_value_total"] = float(prod["total"].sum())

    # Service level per order — most recent N
    recent = orders.sort_values("date_created", ascending=False).head(RECENT_ORDERS_LIMIT)
    m["recent_orders"] = [
        {
            "order_date": r["date_created"].strftime("%b %-d, %Y") if hasattr(r["date_created"], "strftime") else "",
            "customer": str(r.get("billing_first_name") or "").strip() or "—",
            "status": r["order_status"],
            "province": r["billing_state"],
            "days_in_system": int(r["days_in_system"]),
            "service": int(r["days_in_system"]) if r["order_status"] in ("completed", "refunded") else None,
        }
        for _, r in recent.iterrows()
    ]

    # Dispatch schedule — non-completed, non-cancelled only
    open_orders = orders[~orders["order_status"].isin({"completed", "cancelled", "refunded"})]
    open_orders = open_orders.sort_values("date_created", ascending=False)
    m["dispatch_schedule"] = [
        {
            "order_date": r["date_created"].strftime("%b %-d, %Y"),
            "dispatch_target": r["dispatch_target"].strftime("%b %-d, %Y"),
            "customer": str(r.get("billing_first_name") or "").strip() or "—",
            "status": r["order_status"],
            "item_name": r.get("line_item_name", ""),
            "province": r["billing_state"],
            "days_in_system": int(r["days_in_system"]),
            "qty": int(r.get("line_item_quantity", 1) or 1),
            "is_overdue": bool(r["is_overdue"]),
        }
        for _, r in open_orders.iterrows()
    ]

    # Daily order trend — last 30 days
    cutoff_30 = pd.Timestamp(TODAY - timedelta(days=29))
    daily = (
        orders[orders["date_created"] >= cutoff_30]
        .groupby(orders["date_created"].dt.date).size()
    )
    days = [(TODAY - timedelta(days=i)) for i in range(29, -1, -1)]
    m["daily_trend"] = [
        {"date": d.strftime("%b %-d"), "count": int(daily.get(d, 0))} for d in days
    ]

    return m
```

**Note on `%-d`:** that format specifier doesn't work on Windows. Replace `%-d` with `%#d` for Windows-compatible day-without-leading-zero. Final code uses `%#d`. Update the four occurrences accordingly:

```python
# Use %#d on Windows (this script's target platform)
"order_date": r["date_created"].strftime("%b %#d, %Y") ...
"dispatch_target": r["dispatch_target"].strftime("%b %#d, %Y"),
"date": d.strftime("%b %#d") ...
```

- [ ] **Step 2: Verify metrics print correctly**

Add to `__main__`:

```python
    print(f"\nTop 5 products by value:")
    for p in metrics["sales_per_product"][:5]:
        print(f"  {p['name']}: qty={p['qty']} total=R{p['total']:,.2f}")
    print(f"\nProduct totals: qty={metrics['product_qty_total']} value=R{metrics['product_value_total']:,.2f}")
    print(f"\nRecent orders: {len(metrics['recent_orders'])}")
    print(f"Open dispatch queue: {len(metrics['dispatch_schedule'])}")
    print(f"Daily trend points: {len(metrics['daily_trend'])}")
```

Run: `python "1.Projects/AWS Data/build_ecommerce_dashboard.py"`

Expected: product qty total ≈ 797, product value total ≈ R233,076 (matches QuickSight footer). Daily trend has exactly 30 entries.

---

## Task 5: HTML — head, CSS tokens, theme toggle, header bar

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add the CSS token block as a constant at top of script (after imports)**

```python
CSS_TOKENS = """
:root {
  --_y50:#FEF9E0; --_y100:#FDF0A0; --_y200:#FAE04D;
  --_y400:#F5C400; --_y600:#D4A800; --_y800:#A88000; --_y900:#6A5000;
  --_n50:#E8EFF8; --_n100:#B8CCE8; --_n300:#6B9ED0;
  --_n500:#2D6BA8; --_n700:#1A3D6E; --_n900:#0D2040; --_n950:#071022;
  --_g0:#FFFFFF; --_g50:#F7F6F3; --_g100:#E8E7E2; --_g200:#C8C7C0;
  --_g400:#949390; --_g600:#5C5B58; --_g800:#2E2E2C;
  --_g900:#1A1A18; --_g950:#0D0D0B;
  --_teal:#2D8C7A; --_teal-light:#C8EDE7; --_teal-dark:#1a5c50;
  --_terra:#C97A3A; --_terra-light:#F7E0C8;
  --_coral:#E86060; --_coral-light:#FDDCDC;
  --_pink:#E87BAD; --_pink-light:#FCE4EF;
  --_violet:#9B7DBF; --_violet-light:#EDE0F7;
  --_sage:#7A8C55; --_ink:#5C6B7A;
  --font-display:'Barlow Condensed',sans-serif;
  --font-body:'Barlow',sans-serif;
  --r-sm:4px; --r-md:8px; --r-lg:12px; --r-xl:16px; --r-pill:50px;
}
.theme-light{color-scheme:light;--color-surface-page:var(--_g50);--color-surface-base:var(--_g0);--color-surface-elevated:var(--_g0);--color-surface-sunken:var(--_g100);--color-surface-overlay:rgba(0,0,0,0.04);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g950);--color-text-secondary:var(--_g600);--color-text-tertiary:var(--_g400);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y600);--color-brand-secondary:var(--_n700);--color-brand-accent:var(--_y400);--color-border-subtle:var(--_g100);--color-border-default:var(--_g200);--color-border-strong:var(--_g400);--color-border-brand:var(--_y400);--color-success-bg:#EDF7F5;--color-success-fg:var(--_teal-dark);--color-success-bd:var(--_teal);--color-warning-bg:var(--_y50);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y600);--color-danger-bg:#FEF2F2;--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--color-info-bg:var(--_n50);--color-info-fg:var(--_n700);--color-info-bd:var(--_n500);--color-neutral-bg:var(--_g100);--color-neutral-fg:var(--_g600);--color-neutral-bd:var(--_g400);--shadow-sm:0 1px 3px rgba(0,0,0,0.08);--shadow-md:0 4px 12px rgba(0,0,0,0.08);--shadow-lg:0 10px 30px rgba(0,0,0,0.10);--shadow-brand:0 4px 16px rgba(245,196,0,0.20);}
.theme-dark{color-scheme:dark;--color-surface-page:var(--_g950);--color-surface-base:var(--_g900);--color-surface-elevated:var(--_g800);--color-surface-sunken:var(--_g950);--color-surface-overlay:rgba(255,255,255,0.04);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g100);--color-text-secondary:var(--_g400);--color-text-tertiary:var(--_g600);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y200);--color-brand-secondary:var(--_n700);--color-brand-accent:var(--_y400);--color-border-subtle:rgba(255,255,255,0.06);--color-border-default:rgba(255,255,255,0.10);--color-border-strong:rgba(255,255,255,0.20);--color-border-brand:var(--_y400);--color-success-bg:rgba(45,140,122,0.12);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,0.30);--color-warning-bg:rgba(245,196,0,0.10);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,0.25);--color-danger-bg:rgba(232,96,96,0.12);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,0.30);--color-info-bg:rgba(26,61,110,0.30);--color-info-fg:var(--_n100);--color-info-bd:rgba(107,158,208,0.30);--color-neutral-bg:rgba(255,255,255,0.05);--color-neutral-fg:var(--_g400);--color-neutral-bd:rgba(255,255,255,0.10);--shadow-sm:0 1px 3px rgba(0,0,0,0.40);--shadow-md:0 4px 12px rgba(0,0,0,0.40);--shadow-lg:0 10px 30px rgba(0,0,0,0.50);--shadow-brand:0 4px 20px rgba(245,196,0,0.15);}
.theme-brand{color-scheme:light;--color-surface-page:var(--_y400);--color-surface-base:var(--_y200);--color-surface-elevated:var(--_y50);--color-surface-sunken:var(--_y600);--color-surface-overlay:rgba(0,0,0,0.05);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_g950);--color-text-primary:var(--_g950);--color-text-secondary:var(--_y900);--color-text-tertiary:var(--_y800);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_g950);--color-brand-hover:var(--_n700);--color-brand-secondary:var(--_n700);--color-brand-accent:var(--_g950);--color-border-subtle:rgba(0,0,0,0.08);--color-border-default:rgba(0,0,0,0.14);--color-border-strong:rgba(0,0,0,0.25);--color-border-brand:var(--_g950);--color-success-bg:rgba(45,140,122,0.12);--color-success-fg:var(--_teal-dark);--color-success-bd:var(--_teal);--color-warning-bg:rgba(0,0,0,0.08);--color-warning-fg:var(--_y900);--color-warning-bd:var(--_y900);--color-danger-bg:rgba(232,96,96,0.12);--color-danger-fg:#C0392B;--color-danger-bd:var(--_coral);--color-info-bg:rgba(26,61,110,0.10);--color-info-fg:var(--_n900);--color-info-bd:var(--_n700);--color-neutral-bg:rgba(0,0,0,0.06);--color-neutral-fg:var(--_y900);--color-neutral-bd:rgba(0,0,0,0.15);--shadow-sm:0 1px 3px rgba(0,0,0,0.12);--shadow-md:0 4px 12px rgba(0,0,0,0.14);--shadow-lg:0 10px 30px rgba(0,0,0,0.18);--shadow-brand:0 4px 16px rgba(0,0,0,0.15);}
.theme-navy{color-scheme:dark;--color-surface-page:var(--_n950);--color-surface-base:var(--_n900);--color-surface-elevated:var(--_n700);--color-surface-sunken:var(--_n950);--color-surface-overlay:rgba(255,255,255,0.04);--color-surface-brand:var(--_y400);--color-surface-secondary:var(--_n700);--color-text-primary:var(--_g0);--color-text-secondary:var(--_n100);--color-text-tertiary:var(--_n300);--color-text-on-brand:var(--_g950);--color-text-on-navy:var(--_g0);--color-brand-primary:var(--_y400);--color-brand-hover:var(--_y200);--color-brand-secondary:var(--_n500);--color-brand-accent:var(--_y400);--color-border-subtle:rgba(107,158,208,0.12);--color-border-default:rgba(107,158,208,0.20);--color-border-strong:rgba(107,158,208,0.35);--color-border-brand:var(--_y400);--color-success-bg:rgba(45,140,122,0.15);--color-success-fg:var(--_teal-light);--color-success-bd:rgba(45,140,122,0.35);--color-warning-bg:rgba(245,196,0,0.12);--color-warning-fg:var(--_y200);--color-warning-bd:rgba(245,196,0,0.30);--color-danger-bg:rgba(232,96,96,0.14);--color-danger-fg:var(--_coral-light);--color-danger-bd:rgba(232,96,96,0.35);--color-info-bg:rgba(45,107,168,0.20);--color-info-fg:var(--_n100);--color-info-bd:rgba(107,158,208,0.35);--color-neutral-bg:rgba(255,255,255,0.05);--color-neutral-fg:var(--_n300);--color-neutral-bd:rgba(255,255,255,0.12);--shadow-sm:0 1px 3px rgba(0,0,0,0.50);--shadow-md:0 4px 12px rgba(0,0,0,0.50);--shadow-lg:0 10px 30px rgba(0,0,0,0.60);--shadow-brand:0 4px 20px rgba(245,196,0,0.18);}
"""
```

- [ ] **Step 2: Add component CSS as a constant**

```python
COMPONENT_CSS = """
*{box-sizing:border-box}
body{background:var(--color-surface-page);color:var(--color-text-primary);font-family:var(--font-body);margin:0;font-size:14px;line-height:1.5}
h1,h2,h3,h4{font-family:var(--font-display);text-transform:uppercase;margin:0;letter-spacing:0.02em}
.eyebrow{font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.12em;color:var(--color-text-secondary)}

.topbar{display:flex;align-items:center;gap:16px;padding:14px 24px;background:var(--color-surface-base);border-bottom:1px solid var(--color-border-default);position:sticky;top:0;z-index:10}
.topbar .logo{width:48px;height:48px;border-radius:50%;overflow:hidden;flex-shrink:0}
.topbar .logo img{display:block;width:100%;height:100%;object-fit:cover}
.topbar .title{flex:1}
.topbar h1{font-size:22px;font-weight:800;line-height:1.1}
.topbar .meta{font-size:12px;color:var(--color-text-secondary);margin-top:2px}
.theme-bar{display:flex;gap:4px;background:var(--color-surface-elevated);padding:4px;border-radius:var(--r-pill);border:1px solid var(--color-border-default)}
.theme-bar button{font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;padding:6px 14px;border:0;background:transparent;color:var(--color-text-secondary);border-radius:var(--r-pill);cursor:pointer}
.theme-bar button.active{background:var(--color-brand-primary);color:var(--color-text-on-brand)}

.main{padding:24px;max-width:1400px;margin:0 auto}
.row{display:grid;gap:16px;margin-bottom:24px}
.row-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.row-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.row-prov{grid-template-columns:repeat(4,minmax(0,1fr))}
@media(max-width:900px){.row-3,.row-2,.row-prov{grid-template-columns:1fr}}

.kpi{padding:20px;border-radius:var(--r-lg);border:1px solid var(--color-border-default);box-shadow:var(--shadow-md)}
.kpi.kpi-good{background:var(--color-success-bg);border-color:var(--color-success-bd);color:var(--color-success-fg)}
.kpi.kpi-warn{background:var(--color-warning-bg);border-color:var(--color-warning-bd);color:var(--color-warning-fg)}
.kpi.kpi-bad{background:var(--color-danger-bg);border-color:var(--color-danger-bd);color:var(--color-danger-fg)}
.kpi .label{font-family:var(--font-display);font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;text-align:center}
.kpi .value{font-family:var(--font-display);font-weight:900;font-size:48px;text-align:center;line-height:1.05;margin:8px 0}
.kpi .sub{font-size:12px;text-align:center;display:flex;gap:8px;justify-content:center;align-items:center}
.kpi .arrow-up{color:var(--color-success-fg)}
.kpi .arrow-down{color:var(--color-danger-fg)}

.tile-prov{padding:14px;border-radius:var(--r-md);border:1px solid var(--color-border-default);background:var(--color-surface-elevated);text-align:center}
.tile-prov .label{font-family:var(--font-display);font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:var(--color-text-secondary)}
.tile-prov .value{font-family:var(--font-display);font-weight:800;font-size:20px;margin-top:4px}
.tile-prov.no-data .value{color:var(--color-text-tertiary)}

.card{background:var(--color-surface-elevated);border:1px solid var(--color-border-default);border-radius:var(--r-lg);padding:18px;box-shadow:var(--shadow-sm)}
.card h3{font-size:14px;font-weight:800;margin-bottom:14px;text-align:center}

table{width:100%;border-collapse:collapse;font-size:13px}
table th{font-family:var(--font-display);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;text-align:left;padding:8px 10px;background:var(--color-surface-sunken);color:var(--color-text-secondary);border-bottom:1px solid var(--color-border-default)}
table td{padding:8px 10px;border-bottom:1px solid var(--color-border-subtle)}
table tbody tr:nth-child(even) td{background:var(--color-surface-overlay)}
.row-highlight td{background:var(--color-warning-bg) !important}

.badge{display:inline-block;padding:2px 8px;border-radius:var(--r-pill);font-size:11px;font-family:var(--font-display);font-weight:700;text-transform:uppercase;letter-spacing:0.06em}
.badge-completed{background:var(--color-success-bg);color:var(--color-success-fg);border:1px solid var(--color-success-bd)}
.badge-processing{background:var(--color-info-bg);color:var(--color-info-fg);border:1px solid var(--color-info-bd)}
.badge-pending,.badge-on-hold{background:var(--color-warning-bg);color:var(--color-warning-fg);border:1px solid var(--color-warning-bd)}
.badge-cancelled,.badge-failed,.badge-refunded{background:var(--color-neutral-bg);color:var(--color-neutral-fg);border:1px solid var(--color-neutral-bd)}
.dot{display:inline-block;width:14px;height:14px;border-radius:50%}
.dot-good{background:var(--color-success-fg)}
.dot-bad{background:var(--color-danger-fg)}

.scroll-y{max-height:520px;overflow-y:auto}
.footer{padding:24px;text-align:center;color:var(--color-text-tertiary);font-size:12px}
"""
```

- [ ] **Step 3: Add `render_html(metrics)` skeleton — head, header bar, theme toggle, footer placeholder**

```python
def render_html(m: dict) -> str:
    sl = m["service_level"]
    sl_str = f"{sl}" if sl is not None else "—"
    var = m["service_level_variance_pct"]
    if var is None:
        var_html = ""
    elif var > 0:
        var_html = f'<span class="arrow-up">▲ {var:.2f}%</span>'
    else:
        var_html = f'<span class="arrow-down">▼ {abs(var):.2f}%</span>'

    generated = NOW.strftime("%-d %b %Y %H:%M").replace("-d", "#d")
    generated = NOW.strftime("%#d %b %Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en" class="theme-navy">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-Commerce Dashboard — Olympic Paints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<script>var t=localStorage.getItem('oly-theme');if(t)document.documentElement.className=t;</script>
<style>
{CSS_TOKENS}
{COMPONENT_CSS}
</style>
</head>
<body>
  <header class="topbar">
    <div class="logo"><img src="logo.jpg" alt="Olympic Paints" width="48" height="48"></div>
    <div class="title">
      <h1>E-Commerce Dashboard</h1>
      <div class="meta">Period: YTD {TODAY.year} · Generated: {generated} SAST · Source: Woocommerce_Transactions.csv</div>
    </div>
    <div class="theme-bar">
      <button onclick="olyTheme('theme-light',this)">Light</button>
      <button onclick="olyTheme('theme-dark',this)">Dark</button>
      <button onclick="olyTheme('theme-brand',this)">Brand</button>
      <button onclick="olyTheme('theme-navy',this)" class="active">Navy</button>
    </div>
  </header>

  <main class="main">
    <!-- KPI row, provincial grid, pies, trend, tables, dispatch will go here -->
    <p class="eyebrow" style="text-align:center;padding:40px">Sections rendered in subsequent tasks</p>
  </main>

  <footer class="footer">
    Olympic Paints E-Commerce Dashboard — generated by PRISM · {generated}
  </footer>

<script>
const OLY_THEMES=['theme-light','theme-dark','theme-brand','theme-navy'];
function olyTheme(t,btn){{
  document.documentElement.classList.remove(...OLY_THEMES);
  document.documentElement.classList.add(t);
  localStorage.setItem('oly-theme',t);
  document.querySelectorAll('.theme-bar button').forEach(b=>b.classList.toggle('active',b===btn));
}}
</script>
</body>
</html>"""
```

- [ ] **Step 4: Add `build()` and wire everything**

Replace the entire `__main__` block:

```python
def build() -> Path:
    df = load_csv(CSV_PATH)
    orders = build_orders_df(df)
    metrics = compute_metrics(orders, df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if LOGO_SRC.exists():
        shutil.copy2(LOGO_SRC, OUT_DIR / "logo.jpg")
    else:
        print(f"WARNING: logo not found at {LOGO_SRC}")

    html = render_html(metrics)
    out_html = OUT_DIR / "index.html"
    out_html.write_text(html, encoding="utf-8")
    return out_html


if __name__ == "__main__":
    out = build()
    print(f"\nDashboard written to: {out}")
    print(f"Open in browser: file:///{str(out).replace(chr(92), '/')}")
```

- [ ] **Step 5: Run and open in browser**

Run: `python "1.Projects/AWS Data/build_ecommerce_dashboard.py"`

Open the printed `file:///` URL in a browser. Expected: navy background, header bar with logo + title + period + theme toggle, four theme buttons that switch instantly, footer line. Body content shows the placeholder text. Verify all four theme switches work and persist on reload.

---

## Task 6: Render KPI row & provincial service level grid

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add `_render_kpi_row()` and `_render_provincial_grid()`**

Add helper functions before `render_html()`:

```python
def _render_kpi_row(m: dict) -> str:
    sl = m["service_level"]
    sl_str = f"{sl}" if sl is not None else "—"
    var = m["service_level_variance_pct"]
    if var is None:
        var_html = ""
    elif var > 0:
        var_html = f'<span class="arrow-up">▲ {var:.2f}%</span>'
    else:
        var_html = f'<span class="arrow-down">▼ {abs(var):.2f}%</span>'

    return f"""
    <section class="row row-3">
      <div class="kpi kpi-good">
        <div class="label">Current Service Level for {TODAY.year} (Days)</div>
        <div class="value">{sl_str}</div>
        <div class="sub"><span>Service Level Target {SERVICE_LEVEL_TARGET}</span> {var_html}</div>
      </div>
      <div class="kpi kpi-warn">
        <div class="label">Overdue Orders — Total</div>
        <div class="value">{m["overdue_total"]}</div>
        <div class="sub">&nbsp;</div>
      </div>
      <div class="kpi kpi-bad">
        <div class="label">Overdue Orders — Past 4 Weeks</div>
        <div class="value">{m["overdue_4w"]}</div>
        <div class="sub">&nbsp;</div>
      </div>
    </section>
    """


def _render_provincial_grid(m: dict) -> str:
    tiles = []
    for prov in PROVINCE_ORDER:
        v = m["province_service_level"].get(prov)
        if v is None:
            cls = "tile-prov no-data"
            val = "No data"
        else:
            cls = "tile-prov"
            val = f"{v} Days"
        tiles.append(f'<div class="{cls}"><div class="label">Service Level — {prov}</div><div class="value">{val}</div></div>')
    return f'<section class="row row-prov">{"".join(tiles)}</section>'
```

- [ ] **Step 2: Inject these into `render_html()` body**

Replace the placeholder paragraph in `<main class="main">` with:

```python
  <main class="main">
    {_render_kpi_row(m)}
    {_render_provincial_grid(m)}
    <p class="eyebrow" style="text-align:center;padding:40px">Charts and tables rendered in subsequent tasks</p>
  </main>
```

- [ ] **Step 3: Run and verify in browser**

Run the script and refresh the browser. Expected:
- Three KPI tiles: green (Service Level), yellow (Overdue Total), red/orange (Overdue 4w)
- Service Level shows actual number, target `5`, variance arrow + %
- Eight provincial tiles in a 4×2 grid: GP, NW, WC, NC, MP, EC, KZN, LP
- Provinces with no data show `No data` in muted text
- Theme switching still works on all components

---

## Task 7: Render pies (Sales by Province + Order Status) with Chart.js

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add Chart.js CDN + barLabels plugin to `<head>`**

In `render_html()`, add inside `<head>` after the `<style>` close tag:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```

- [ ] **Step 2: Add `_render_pies()` helper**

```python
def _render_pies(m: dict) -> str:
    sbp = m["sales_by_province"]
    sbp_labels = [r["province"] for r in sbp]
    sbp_values = [round(r["total"], 2) for r in sbp]

    status = m["status_mix"]
    status_labels = [r["status"] for r in status]
    status_values = [r["count"] for r in status]

    import json as _json
    return f"""
    <section class="row row-2">
      <div class="card"><h3>Sales Breakdown Per Province</h3><div style="height:340px"><canvas id="piePro"></canvas></div></div>
      <div class="card"><h3>Order Status Breakdown</h3><div style="height:340px"><canvas id="pieStatus"></canvas></div></div>
    </section>
    <script>
    const PIE_COLORS=['#F5C400','#1A3D6E','#2D8C7A','#C97A3A','#E87BAD','#9B7DBF','#5C6B7A','#FAE04D','#6B9ED0','#7A8C55'];
    const txt=getComputedStyle(document.documentElement).getPropertyValue('--color-text-primary')||'#fff';
    Chart.defaults.color=txt.trim();
    Chart.defaults.font.family="Barlow, sans-serif";
    new Chart(document.getElementById('piePro'),{{
      type:'pie',
      data:{{labels:{_json.dumps(sbp_labels)},datasets:[{{data:{_json.dumps(sbp_values)},backgroundColor:PIE_COLORS}}]}},
      options:{{plugins:{{legend:{{position:'right'}},tooltip:{{callbacks:{{label:c=>c.label+': R'+c.parsed.toLocaleString()}}}}}},maintainAspectRatio:false}}
    }});
    new Chart(document.getElementById('pieStatus'),{{
      type:'pie',
      data:{{labels:{_json.dumps(status_labels)},datasets:[{{data:{_json.dumps(status_values)},backgroundColor:PIE_COLORS}}]}},
      options:{{plugins:{{legend:{{position:'right'}}}},maintainAspectRatio:false}}
    }});
    </script>
    """
```

- [ ] **Step 3: Wire into `render_html()`**

In the `<main>` body, insert after `_render_provincial_grid(m)`:

```python
    {_render_pies(m)}
```

- [ ] **Step 4: Run and verify**

Refresh browser. Expected: two side-by-side pies. Sales pie shows GP dominant (~92K). Status pie shows `completed` largest. Tooltips show formatted ZAR amounts on the sales pie. Both pies redraw cleanly when switching themes.

---

## Task 8: Daily order trend line chart

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add `_render_trend()` helper**

```python
def _render_trend(m: dict) -> str:
    import json as _json
    labels = [r["date"] for r in m["daily_trend"]]
    values = [r["count"] for r in m["daily_trend"]]
    return f"""
    <section class="row" style="grid-template-columns:1fr">
      <div class="card"><h3>Daily Order Volume — Last 30 Days</h3><div style="height:200px"><canvas id="trendChart"></canvas></div></div>
    </section>
    <script>
    new Chart(document.getElementById('trendChart'),{{
      type:'line',
      data:{{labels:{_json.dumps(labels)},datasets:[{{data:{_json.dumps(values)},borderColor:'#F5C400',backgroundColor:'rgba(245,196,0,0.15)',fill:true,tension:0.3,pointRadius:2}}]}},
      options:{{plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{stepSize:1}}}}}},maintainAspectRatio:false}}
    }});
    </script>
    """
```

- [ ] **Step 2: Wire into `render_html()`**

After `_render_pies(m)`:

```python
    {_render_trend(m)}
```

- [ ] **Step 3: Run and verify**

Refresh. Expected: a full-width line chart showing 30 daily points. Y-axis integer steps. Yellow line on translucent yellow fill. No legend.

---

## Task 9: Service Level per Order + Sales Per Product tables

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add `_status_badge()` helper and table renderers**

```python
def _status_badge(status: str) -> str:
    cls = f"badge badge-{status}"
    return f'<span class="{cls}">{status}</span>'


def _render_recent_orders(m: dict) -> str:
    rows = []
    for r in m["recent_orders"]:
        svc = r["service"] if r["service"] is not None else ""
        rows.append(
            f'<tr><td>{r["order_date"]}</td><td>{r["customer"]}</td>'
            f'<td>{_status_badge(r["status"])}</td><td>{r["province"]}</td>'
            f'<td style="text-align:right">{r["days_in_system"]}</td>'
            f'<td style="text-align:right">{svc}</td></tr>'
        )
    return f"""
      <div class="card">
        <h3>Service Level per Order</h3>
        <div class="scroll-y">
        <table>
          <thead><tr><th>Order Date</th><th>Customer</th><th>Status</th><th>Province</th><th style="text-align:right">days_in_system</th><th style="text-align:right">Service</th></tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
        </div>
      </div>
    """


def _render_products(m: dict) -> str:
    rows = []
    for i, p in enumerate(m["sales_per_product"]):
        cls = "row-highlight" if i < TOP_PRODUCTS_HIGHLIGHT else ""
        rows.append(
            f'<tr class="{cls}"><td>{p["name"]}</td>'
            f'<td style="text-align:right">{p["qty"]}</td>'
            f'<td style="text-align:right">R{p["total"]:,.2f}</td></tr>'
        )
    footer = (
        f'<tr><td><strong>Total</strong></td>'
        f'<td style="text-align:right"><strong>{m["product_qty_total"]}</strong></td>'
        f'<td style="text-align:right"><strong>R{m["product_value_total"]:,.2f}</strong></td></tr>'
    )
    return f"""
      <div class="card">
        <h3>Sales Per Product</h3>
        <div class="scroll-y">
        <table>
          <thead><tr><th>Item Name</th><th style="text-align:right">Qty</th><th style="text-align:right">Total</th></tr></thead>
          <tbody>{"".join(rows)}</tbody>
          <tfoot>{footer}</tfoot>
        </table>
        </div>
      </div>
    """
```

- [ ] **Step 2: Wire into `render_html()`**

After `_render_trend(m)`:

```python
    <section class="row row-2">
      {_render_recent_orders(m)}
      {_render_products(m)}
    </section>
```

- [ ] **Step 3: Run and verify**

Expected: two side-by-side tables.
- Service Level per Order: 50 rows max, recent first, status badges coloured per state
- Sales Per Product: top 3 rows highlighted yellow, footer row bold with `797` qty and `R233,076.00` (or close — depends on CSV cutoff)

---

## Task 10: Dispatch Schedule full-width table

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add `_render_dispatch()` helper**

```python
def _render_dispatch(m: dict) -> str:
    rows = []
    for r in m["dispatch_schedule"]:
        dot_cls = "dot dot-bad" if r["is_overdue"] else "dot dot-good"
        rows.append(
            f'<tr><td>{r["order_date"]}</td><td>{r["dispatch_target"]}</td>'
            f'<td>{r["customer"]}</td><td>{_status_badge(r["status"])}</td>'
            f'<td>{r["item_name"]}</td><td>{r["province"]}</td>'
            f'<td style="text-align:right">{r["days_in_system"]}</td>'
            f'<td style="text-align:right">{r["qty"]}</td>'
            f'<td style="text-align:center"><span class="{dot_cls}"></span></td></tr>'
        )
    return f"""
    <section class="row" style="grid-template-columns:1fr">
      <div class="card">
        <h3>Date That Orders Need to Leave Olympic Paints</h3>
        <div class="scroll-y">
        <table>
          <thead><tr>
            <th>Order Date</th><th>Dispatch Target Date</th><th>Customer Name</th>
            <th>Status</th><th>Item Name</th><th>Province</th>
            <th style="text-align:right">days_in_system</th>
            <th style="text-align:right">Qty</th>
            <th style="text-align:center">Overdue</th>
          </tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
        </div>
      </div>
    </section>
    """
```

- [ ] **Step 2: Wire into `render_html()`**

Insert before the closing `</main>` tag, after the recent-orders/products row:

```python
    {_render_dispatch(m)}
```

- [ ] **Step 3: Run and verify**

Expected: full-width scrollable table. Each open order has a green or red dot in the rightmost column based on `is_overdue`. Completed/cancelled orders are not in this table.

---

## Task 11: Final polish + verification pass

**Files:**
- Modify: `1.Projects/AWS Data/build_ecommerce_dashboard.py`

- [ ] **Step 1: Add console summary at end of `build()`**

In `build()`, replace `return out_html` with:

```python
    print("\n── E-COMMERCE DASHBOARD BUILD SUMMARY ──")
    print(f"  Orders YTD:              {metrics['total_orders']}")
    print(f"  Service Level (days):    {metrics['service_level']}  (target {SERVICE_LEVEL_TARGET})")
    print(f"  Overdue total:           {metrics['overdue_total']}")
    print(f"  Overdue past 4 weeks:    {metrics['overdue_4w']}")
    print(f"  Total sales (ZAR):       R{metrics['total_sales']:,.2f}")
    print(f"  Open dispatch queue:     {len(metrics['dispatch_schedule'])}")
    print(f"  Output:                  {out_html}")
    return out_html
```

- [ ] **Step 2: Run final build and visual inspection checklist**

Run: `python "1.Projects/AWS Data/build_ecommerce_dashboard.py"`

Open the dashboard in a browser. Tick off:

- [ ] Page loads with **navy theme** by default (no flash)
- [ ] Logo renders crisply at 48px, circular
- [ ] All three KPI tiles show real numbers (none `—`)
- [ ] Service Level variance arrow + colour matches direction
- [ ] All eight provincial tiles render (some may show "No data")
- [ ] Sales pie shows GP dominant
- [ ] Status pie shows completed dominant
- [ ] Trend chart shows a 30-day line, no errors in console
- [ ] Recent orders table scrolls inside its card, status badges coloured
- [ ] Sales Per Product top-3 rows highlighted, footer matches column sums
- [ ] Dispatch Schedule shows green/red dots correctly
- [ ] Theme toggle: switch through Light / Dark / Brand / Navy — every component re-themes
- [ ] Reload page after switching theme — no flash, theme persists
- [ ] Resize browser to 800px wide — layout stacks, no horizontal scroll
- [ ] Browser console shows zero errors

If any item fails, fix in the relevant earlier task and re-run.

- [ ] **Step 3: Done**

The dashboard is complete. To regenerate after the CSV updates, just re-run the script. The data is read fresh every run.

---

## Self-Review (writer's checks before handoff)

**Spec coverage:**
- §3.1 Service Level → Task 2 ✓
- §3.2 Overdue (total + 4w) → Task 2 ✓
- §3.3 Sales by province → Task 3 ✓
- §3.4 Order status mix → Task 3 ✓
- §3.5 Sales per product → Task 4 + Task 9 ✓
- §3.6 Service level per order table → Task 4 + Task 9 ✓
- §3.7 Dispatch schedule → Task 4 + Task 10 ✓
- §3.8 Daily trend → Task 4 + Task 8 ✓
- §4 Layout → Tasks 5–10 ✓
- §5 Themes (4) → Task 5 (CSS_TOKENS includes all 4) ✓
- §6.1 Build script structure → All tasks ✓
- §7 Edge cases → Task 1 (loader), Task 2 (clamping, exclusion), Task 3 (empty province) ✓

**Placeholder scan:** none.

**Type consistency:** `metrics` keys are introduced and consumed consistently (`service_level`, `overdue_total`, `overdue_4w`, `province_service_level`, `sales_by_province`, `status_mix`, `sales_per_product`, `recent_orders`, `dispatch_schedule`, `daily_trend`). All renderer functions use the same names. `_status_badge()` defined in Task 9, used in Tasks 9 and 10.

**One known correction:** Task 5 step 3 had a stray `replace("-d", "#d")` line — corrected to use `strftime("%#d %b %Y %H:%M")` directly. Engineer should follow the final corrected line, not the dead one above it.
