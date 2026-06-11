# FLASH — ODO Pricing Book

The cost-ex-VAT FLASH offers ODO per SKU, the RSP, the colour-specific SKU codes, and **the Rock Bottom Price** — the absolute floor below which we will not sell, no matter how hard ODO pushes. The full catalogue lives in `OneDayOnlyData.xlsx` and the canonical price list is `2.Areas/1. Sales/1. Pricing/Rock Bottom/OLYMPIC PAINTS PRICE LIST 2026 15%.pdf`.

> All prices ex-VAT. Add 15% on the invoice. Retail price (RSP) is what the public sees as the in-store anchor; ODO sets their own customer-facing sale price after their markup.

---

## Pricing formula (canonical)

- **Normal RSP (column J in product sheet)** = List Price × 1.15
- **Cost ex-VAT to ODO (column I)** = List Price × 0.75 (25% off list)

Source list price: `Rock Bottom/OLYMPIC PAINTS PRICE LIST 2026 15%.pdf` — column "List Price 2026", confirmed by Quintus 2026-05-12 as VAT-exclusive.

---

## Negotiation floor: Rock Bottom Price

The price list PDF carries a `Rock Bottom Price` column for many SKUs. This is the absolute floor below which Olympic will not sell, period. When ODO pushes for a lower cost ex-VAT (Intent D in `FLASH_PLAYBOOK.md`), FLASH must:

1. Quote the **current cost ex-VAT** (list × 0.75).
2. Have the **Rock Bottom Price** in hand as the worst-case fallback.
3. **Never** counter below the Rock Bottom — that requires explicit Quintus override.
4. If ODO's ask is between current cost and Rock Bottom: pause, Telegram Quintus, get instruction before responding.

---

## Active catalogue (19 priced SKUs as of 2026-05-12)

| # | Product | Canonical SKU | List Price | Cost ex-VAT (×0.75) | RSP (×1.15) | Rock Bottom Floor |
|---|---|---|---|---|---|---|
| 1  | 20L Décor Acrylic PVA               | `139401` (White) | R 497.54 | R 373.16 | R 572.18 | **R 285.00** |
| 2  | 5L Décor Acrylic PVA                | `139801` (White) | R 133.27 | R 99.95  | R 153.26 | **R 80.50** |
| 3  | 20L Kalahari Contractors PVA        | `129401` (White) | R 604.15 | R 453.11 | R 694.77 | _no floor published_ |
| 4  | 20L Master Decorators PVA           | `209401` (White) | R 851.16 | R 638.37 | R 978.83 | **R 495.00** |
| 5  | 20L Hi-Hiding Contractors PVA       | `499401` (White) | R 710.78 | R 533.09 | R 817.40 | **R 420.00** |
| 6  | 20L Suburban Bliss Matt PVA         | `459401` (White) | R 1,294.27 | R 970.70 | R 1,488.41 | _no floor published_ |
| 7  | 20L Natural Elegance Sheen PVA      | `399401` (Brilliant White) | R 1,845.28 | R 1,383.96 | R 2,122.07 | _no floor published_ |
| 8  | 20L Rugged Beauty Textured PVA      | `149401` (White) | R 1,193.43 | R 895.07 | R 1,372.43 | _no floor published_ |
| 9  | 20L Eclipse Acrylic PVA             | `E9401` (White)  | R 314.52 | R 235.88 | R 361.69 | **R 201.25** |
| 10 | 20L Universal Undercoat             | `229401` (White) | R 1,936.44 | R 1,452.33 | R 2,226.91 | _no floor published_ |
| 11 | 5L Universal Undercoat              | `229801` (White) | R 522.19 | R 391.64 | R 600.52 | _no floor published_ |
| 12 | 20L High Gloss Enamel               | `299401` (MQ White) | R 1,563.71 | R 1,172.78 | R 1,798.26 | **R 995.00** |
| 13 | 5L Platinum Plus Ultimate Shine Enamel | `409801` (White) | R 584.26 | R 438.20 | R 671.90 | **R 270.00** |
| 14 | 5L Zinc Phosphate Primer Green      | `279842`         | R 548.29 | R 411.22 | R 630.53 | _no floor published_ |
| 15 | 20L All-In-One Primer (Platinum Plus All-in-one Protector) | `359401` (White) | R 1,709.36 | R 1,282.02 | R 1,965.76 | _no floor published_ |
| 16 | 20L Universal Roof Coating          | `309421` (Black) | R 1,155.61 | R 866.71 | R 1,328.95 | **R 550.00** |
| 17 | 20L Plush Coat Roof Coating         | `329422` (Charcoal) | R 1,319.49 | R 989.62 | R 1,517.41 | _no floor published_ |
| 18 | 20L Red Oxide Primer (Waterbase)    | `379475`         | R 1,176.39 | R 882.29 | R 1,352.85 | **R 770.00** |
| 19 | 5L Olympic Damp Fix                 | _SKU to confirm with Pricing_ | R 429.77 | R 322.33 | R 494.24 | _no floor published_ |

---

## Colour-variant premium (when ODO requests colours on a listing)

The PDF shows that **colour variants cost more than the white base** at list-price level. If ODO adds colours to a deal, FLASH must reprice each colour variant using the COLOURS line in the PDF:

| Product family | White list | Colours list | Δ |
|---|---|---|---|
| Décor 20L | R 497.54 | R 524.20 | +R 26.66 |
| Kalahari Contractors 20L | R 604.15 | R 630.81 | +R 26.66 |
| Eclipse 20L | R 314.52 | R 337.61 | +R 23.09 |
| Master Decorators 20L | R 851.16 | R 888.46 | +R 37.30 |
| Suburban Bliss 20L | R 1,294.27 | R 1,336.30 | +R 42.03 |
| Natural Elegance 20L | R 1,845.28 | R 1,941.42 | +R 96.14 |
| Rugged Beauty 20L | R 1,193.43 | R 1,218.64 | +R 25.21 |
| High Gloss 20L (Peach/Cream/Golden Brown) | R 1,563.71 | R 1,617.01 | +R 53.30 |
| Plush Coat 20L (standard colours) | base | R 1,319.49 | n/a |
| Plush Coat Green/Emu Green 20L | base | R 1,386.73 | +R 67.24 over standard colours |
| Universal Roof (standard) | base | R 1,155.61 | n/a |
| Universal Roof Green/Emu/Albany/Ocean Blue | base | R 1,196.69 | +R 41.08 over standard colours |

**Rule for FLASH:** when sending colour-variant SKUs on a deal, look up the matching COLOURS row in the PDF, multiply × 0.75 for cost, × 1.15 for RSP. Don't blindly use the white-base price for a coloured SKU.

---

## Deals run to date

| Deal | Date | Products | Source pricing |
|---|---|---|---|
| Deal 1 (SO-280164) | 2025-07-02 | 20L Décor White, 20L Décor Cream, 5L Rainproof × 4 colours | Pre-2026 pricing (R260 for Décor 20L, R95 for 5L Rainproof) |
| Deal 2 (SO-283881) | 2025-08-05 | 20L Master Decorators × 3 colours, 5L Wood Varnish | Pre-2026 pricing (R475.45 for Master Decorators 20L) |

Both deals used **pre-2026 pricing.** Going forward (Round 3 and on), use the 2026 price list with the × 0.75 cost / × 1.15 RSP formula above.

---

## Update protocol

Whenever the master price list changes:
1. Re-run the audit script against the PDF.
2. Update list prices in this file.
3. Recompute Cost ex-VAT and RSP for every active SKU.
4. Save a new `OneDayOnlyData.xlsx` (with timestamped backup of the old).
5. Append a change log entry below.

---

## Change log

- **2026-05-12** — File rebuilt from `OLYMPIC PAINTS PRICE LIST 2026 15%.pdf`. 18 priced SKUs seeded. Rock Bottom floors captured for 9 SKUs. Verified by Quintus against the PDF.
- **2026-05-12 (later same day)** — Added 5L Damp Fix (R429.77 list / R322.33 cost / R494.24 RSP) after PDF revealed it (Excel master is missing this product). SKU code to confirm with Pricing.
