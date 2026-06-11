# Product Intelligence — Enamel Range

_Last updated: 2026-05-16 | Add new findings at the top of each section_

---

## Enamel Tier Structure

| Tier | Product Name | Type | Position |
|---|---|---|---|
| Premium | **Ultimate Shine** | Water-based enamel | Flagship premium product |
| Mid-Range | **High Gloss** (incl. MQ Premium sub-range) | Solvent enamel | Volume backbone |
| Budget | **Pick 'N Save** | Budget enamel | Entry-point / door-opener |

> **Note:** "Eyeglass" / "EyeGloss" is not a product in any system — likely a mispronunciation of Ultimate Shine. Do not create SKUs or pricing under this name.

---

## SKU Gaps Identified

- **Pick 'N Save has no 500ml or 1L SKUs.** Only 5L and 20L are available. This is a competitive disadvantage in stores where customers trial-purchase in smaller sizes. Flagged to Sejal for production consideration.
- **High Gloss MQ Premium** is a sub-category within the High Gloss mid-range tier — not a separate tier. Shares the same price band as standard High Gloss.

---

## 2026 List Prices (post 15% increase)

### Ultimate Shine (Premium)
| Size | White | Colour |
|---|---|---|
| 500ml | R 91 – 97 | varies |
| 1L | R 154 – 168 | varies |
| 5L | R 584.26 | R 627.08 |
| 20L | R 2,086.63 | R 2,168.00 |

### High Gloss (Mid-Range)
| Size | White | Colour |
|---|---|---|
| 500ml | R 71 – 76 | varies |
| 1L | R 113 – 130 | varies |
| 5L | R 414.03 | R 479.77 |
| 20L | R 1,563.70 | R 1,617.02 |

### Pick 'N Save (Budget)
| Size | White/Cream | Colour |
|---|---|---|
| 500ml | — (no SKU) | — |
| 1L | — (no SKU) | — |
| 5L | R 381.17 | R 385.02 |
| 20L | R 1,297.89 | R 1,472.98 |

---

## Price Spread — Pick 'N Save vs Other Tiers

| Size | vs Ultimate Shine | vs High Gloss |
|---|---|---|
| 5L White | –34.8% cheaper | –7.9% cheaper |
| 5L Colour | –38.6% cheaper | –19.7% cheaper |
| 20L White | –37.8% cheaper | –17.0% cheaper |
| 20L Colour | –32.1% cheaper | –8.9% cheaper |

---

## Rock Bottom Floors — Authoritative Reference

> **Period definitions:**
> - **Pre-April 2025** = `Price_List_2025.parquet` (source: `OLYMPIC PAINTS PRICE LIST 2025.xlsx`)
> - **Post-April 2026** = `Price_List_2026.parquet` (source: `OLYMPIC PAINTS PRICE LIST 2026 15%.pdf`)
> - **Comparison workbook:** `2.Areas/1. Sales/1. Pricing/Rock Bottom/Rock Bottom Prices 2026 vs 2025.xlsx`
> - Do NOT use ad-hoc rock bottom figures from dashboards or earlier notes — always refer to the parquets or the comparison workbook.

### High Gloss (Mid-Range)

| Size | Pre-April 2025 RB | Post-April 2026 RB | Change |
|---|---|---|---|
| 500ml White/Black | R 45.00 | R 51.75 | +15.0% |
| 1L White/Black | R 63.50 | R 75.00 | +18.1% |
| 1L Colours | R 67.50 | R 75.00 | +11.1% |
| 5L White/Black | R 235.00 | R 270.00 | +14.9% |
| 5L Colours | R 245.00 | R 280.00 | +14.3% |
| 20L White | R 865.00 | R 995.00 | +15.0% |
| 20L Peach/Cream/GBrown | R 865.00 | R 995.00 | +15.0% |

### Pick 'N Save (Budget)

| Size | Pre-April 2025 RB | Post-April 2026 RB | Change |
|---|---|---|---|
| 1L White/Cream | R 56.50 | R 58.00 | +2.7% |
| 1L Colours | R 56.50 | R 58.00 | +2.7% |
| 5L White/Cream | R 215.00 | R 210.00 | –2.3% |
| 5L Colours | R 215.00 | R 210.00 | –2.3% |
| 20L White/Cream | R 755.00 | R 870.00 | +15.2% |
| 20L Peach | R 755.00 | R 870.00 | +15.2% |

### Ultimate Shine (Premium)

| Size | Pre-April 2025 RB | Post-April 2026 RB | Note |
|---|---|---|---|
| All sizes | NaN | NaN | No rock bottom defined on either price list |

> ⚠ Previous data quality flags (High Gloss 20L showing R40, Pick 'N Save 20L showing R1,069) are now resolved — those were dashboard calculation errors. The values above are sourced directly from the official price list parquets and are authoritative.

---

## Open Questions / Flags for Sejal

- [ ] Is a 1L Pick 'N Save SKU feasible for next production run?
- [ ] Confirm whether Ultimate Shine cost structure supports current RB floors given –23.97% average selling gap
- [x] Corrupted Post-April rock bottom data — RESOLVED via Price_List_2026.parquet. High Gloss 20L = R 995, Pick 'N Save 20L = R 870.
