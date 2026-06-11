# OneDayOnlyData.xlsx — Revision Audit

**Revised:** 2026-05-12
**Backup of pre-revision file:** `OneDayOnlyData.backup.20260512_205859.xlsx`
**Source of truth for pricing:** `2.Areas/1. Sales/1. Pricing/List Price 2026 15 % Increase.xlsx`

---

## Pricing formula

- **Normal RSP (col J)**  = List Price × 1.15  (gross-up to incl-VAT retail anchor for the customer)
- **Cost ex-VAT (col I)** = List Price × 0.75  (25% off list, ex-VAT)

Confirmed with Quintus 2026-05-12: list price in the 2026 file is VAT-exclusive.

---

## Why a revision was needed (issues found in the previous file)

The previous `OneDayOnlyData.xlsx` (or its predecessor `OneDayOnely.xlsx`) had 28 rows containing significant data integrity problems:

| Problem | Examples | Count |
|---|---|---|
| Cost ex-VAT & RSP entirely blank | Every row | 28 |
| Wrong SKU mapped to product name | "Décor 5L" row carried SKU `139411` which is **20L Cream**; "Kalahari 20L" row carried `129898` which is **5L Apricot**; "Natural Elegance" carried `339419` which is in the **Schoolboard** group | 8 |
| Missing SKU | "Hi-Hiding Contractors", "All-In-One Primer", "Olympic Damp Sealer", "Olympic Damp Fix", "Universal Undercoat" (duplicate row) | 7 |
| Product name encoded incorrectly | "D�cor" (mojibake for "Décor"), "Hididng" (typo for "Hiding"), "Master Décorators" missing space | 5 |
| SKU points to a non-default colour | Suburban Bliss → "WILD ORCHID", Natural Elegance → "RED PASSION", Rugged Beauty → "SUEDE GREY", Eclipse → "PEACH", Master Decorators → "MISTY STORM", Platinum Plus → "G BROWN" — all default to a non-white SKU when the listing should be the white/base variant | 6 |
| Product not in the 2026 price list at all | Olympic Damp Sealer, Olympic Damp Fix, Zinc Phosphate Primer **20L** (`279442` exists in master but has no published price), High Gloss Enamel SKU `229451` (does not exist), Plush Coat SKU `329434` (does not exist), Suburban Bliss 20L `459419` (does not exist), Natural Elegance `339419` (Schoolboard group) | 7 |
| Duplicate row | "All-In-One Primer" appears twice, "Universal Undercoat" appears twice, "Décor 20L" appears twice, "Suburban Bliss 20L" appears twice, "Natural Elegance" appears twice | 5 |

**Conclusion**: rebuilding from scratch was the safer path than patching.

---

## Decisions made

### 18 products kept (the new sheet)

| # | Product | Canonical SKU | List Price (ex-VAT) | RSP | Cost ex-VAT |
|---|---|---|---|---|---|
| 1  | 20L Décor Acrylic PVA               | `139401` (White) | R 497.55 | R 572.18 | R 373.16 |
| 2  | 5L Décor Acrylic PVA                | `139801` (White) | R 133.27 | R 153.26 | R 99.95 |
| 3  | 20L Kalahari Contractors Acrylic PVA| `129401` (White) | R 604.15 | R 694.77 | R 453.11 |
| 4  | 20L Master Decorators Acrylic PVA   | `209401` (White) | R 851.16 | R 978.83 | R 638.37 |
| 5  | 20L Hi-Hiding Contractors Acrylic PVA| `499401` (White) | R 710.78 | R 817.40 | R 533.09 |
| 6  | 20L Suburban Bliss Matt Acrylic PVA | `459401` (White) | R 1,294.27 | R 1,488.41 | R 970.70 |
| 7  | 20L Natural Elegance Sheen Acrylic PVA | `399401` (Brilliant White) | R 1,845.28 | R 2,122.07 | R 1,383.96 |
| 8  | 20L Rugged Beauty Textured Acrylic PVA | `149401` (White) | R 1,193.42 | R 1,372.43 | R 895.07 |
| 9  | 20L Eclipse Acrylic PVA             | `E9401` (White) | R 314.51 | R 361.69 | R 235.88 |
| 10 | 20L Universal Undercoat             | `229401` (White) | R 1,936.44 | R 2,226.91 | R 1,452.33 |
| 11 | 5L Universal Undercoat              | `229801` (White) | R 522.19 | R 600.52 | R 391.64 |
| 12 | 20L High Gloss Enamel               | `299401` (MQ White) | R 1,563.70 | R 1,798.26 | R 1,172.78 |
| 13 | 5L Platinum Plus Ultimate Shine Enamel | `409801` (White) | R 584.26 | R 671.90 | R 438.20 |
| 14 | 5L Zinc Phosphate Primer            | `279842` | R 548.29 | R 630.53 | R 411.22 |
| 15 | 20L All-In-One Primer               | `359401` (White) | R 1,709.36 | R 1,965.76 | R 1,282.02 |
| 16 | 20L Universal Roof Coating (Black)  | `309421` (Black) | R 1,155.61 | R 1,328.95 | R 866.71 |
| 17 | 20L Plush Coat Roof Coating (Charcoal) | `329422` (Charcoal) | R 1,319.49 | R 1,517.41 | R 989.62 |
| 18 | 20L Red Oxide Primer (Waterbase)    | `379475` | R 1,176.39 | R 1,352.85 | R 882.29 |

### 2 products dropped from the sheet

| Product | Reason |
|---|---|
| Olympic Damp Sealer | Not in the 2026 price list — no published list price to compute cost from. **Affects schedule:** Week 2 Thursday |
| Olympic Damp Fix    | Not in the 2026 price list — same. **Affects schedule:** Week 2 Thursday |

**Action**: ask Pricing / Production to publish 2026 prices for these two SKUs if they're meant to be sold. Until then, both are excluded from the ODO submission rotation.

### Notes on swaps & defaults

- **5L Zinc Phosphate Primer** substituted for the schedule's "Zinc Phosphate Primer" slot because the 20L (`279442`) has no 2026 published price. 5L (`279842`) at R548.29 is available.
- **Universal Roof Coating defaulted to Black (`309421`)** — no white variant exists in the Universal Roof Paint family. Other colours (Charcoal `309422`, Grey `309425`, Brown `309435`, etc.) can be offered as variants in the ODO listing.
- **Plush Coat Roof Coating defaulted to Charcoal (`329422`)** — no white variant exists. Other colours: Grey `329425`, Green `329442`.
- **Red Oxide Primer defaulted to Waterbase (`379475`)** rather than Q.D. (`369475`) — Waterbase is more commonly used for general DIY exterior priming and ODO's audience skews DIY.
- **Suburban Bliss White appears at SKU `459401` for both 5L (R361.40) and 20L (R1,294.27) in the price list** — this is a data quality issue in the source price list (same code used for two sizes). The new ODO sheet only includes the 20L variant to avoid confusion; flag to Pricing for cleanup.

### Encoding fixes applied

- `D�cor` → `Décor` (proper UTF-8 é)
- `Hididng` → `Hiding`
- `Master D�corators` → `Master Decorators` (no accent on Decorators — matches the 2025 sign-off naming where the e was unaccented; consistent with the price list "MASTER DECOR ...")

---

## Open follow-ups

1. **Pricing team** to publish 2026 list prices for Olympic Damp Sealer + Olympic Damp Fix (or confirm discontinuation).
2. **Pricing team** to deduplicate SKU `459401` (Suburban Bliss) — currently maps to two sizes.
3. **Pricing team** to publish 2026 price for 20L Zinc Phosphate Primer (`279442`) if it's still sold in that size.
4. **Quintus** to confirm Product Info / Features text for each product. The descriptive paragraphs from the old file have been migrated where they fit by product family, but several products (Hi-Hiding Contractors, Universal Roof, Plush Coat, Red Oxide, All-In-One, Zinc Phosphate, High Gloss, Platinum Plus) have **placeholder/empty Product Info** that needs filling.
5. **Marketing / BLAZE** to provide brand images (JPEG, column A) for each product before first submission.

---

## Verification pass — 2026-05-12 (PDF cross-check)

**Source PDF:** `2.Areas/1. Sales/1. Pricing/Rock Bottom/OLYMPIC PAINTS PRICE LIST 2026 15%.pdf`

Quintus confirmed the **Rock Bottom PDF is the canonical price list** for ODO. Every list price I used from the Excel `List Price 2026 15 % Increase.xlsx` was cross-checked against the PDF. Result: **all 18 SKUs verified — list prices match to the cent** (only sub-cent rounding artefacts).

What the PDF carries beyond the Excel:

1. **Rock Bottom Prices** — absolute price floor per SKU. Captured into `PRICING_BOOK.md`. New rule added to `FLASH_PLAYBOOK.md § D` (Pricing pushback): never counter below Rock Bottom without Quintus override.
2. **Discount band reference (Less 10 / 20 / 30 Min-Max)** — useful future input if we move to a tiered ODO discount instead of the flat 25%.
3. **Damp Fix exists** in the PDF (1LT R 127.28, 5LT R 429.77) but is **missing from the Excel master**. Added 5L Damp Fix to `OneDayOnlyData.xlsx` (row 21), SKU placeholder pending confirmation from Pricing. W2 Thursday in `SUBMISSION_SCHEDULE.md` restored to run 5L Damp Fix solo.
4. **Damp Sealer still not found** in either source — remains dropped from the catalogue and schedule.
5. **Rainproof 20LT and QD Bronze 20LT** appear at the bottom of the PDF with **no list price** — flagged to Pricing as missing data, not currently in the ODO sheet.

### Action items added 2026-05-12

6. **Pricing team** to confirm the SKU code for 5L Damp Fix (currently a placeholder in `OneDayOnlyData.xlsx`).
7. **Pricing team** to publish list prices for Rainproof 20LT and QD Bronze 20LT (blank rows at the bottom of the PDF).
8. **Pricing team** to merge Damp Fix into the Excel master `List Price 2026 15 % Increase.xlsx` so both sources stay in sync.

---

## Product Info & Features pass — 2026-05-12

**Source:** Olympic Paints 2025 Technical Data Sheets, located at `3.Resources/1. Products Related Information/<product>/OP <PRODUCT> TDS 2025.pdf`.

For each of the 19 SKUs, **Product Info** (column F) was distilled from the TDS "General Description" plus the product family use-case, kept to 2–3 sentences. **Product Features** (column G) captures the TDS Composition + Specifications + Application Details + Drying Properties as a clean bulleted block.

| TDS coverage | Count | Products |
|---|---|---|
| Official 2025 TDS read & sourced | 17 | Décor (×2), Kalahari, Master Decorators, Hi-Hiding, Suburban Bliss, Natural Elegance, Rugged Beauty, Eclipse, Universal Undercoat (×2), High Gloss Enamel, Ultimate Shine, Zinc Phosphate, All-In-One Primer, Universal Roof, Plush Coat |
| **No local TDS — conservative description, flagged** | 2 | Water-Based Red Oxide Primer (20L), Olympic Damp Fix (5L) |

The two flagged products carry a `Note: full TDS pending issue by Olympic Technical — confirm with Pricing before final listing.` line in their feature block so ODO doesn't see unverified spec claims and FLASH knows to escalate before submission.

### Action items added 2026-05-12 (Product Info pass)

9. **Olympic Technical** to issue official 2026 TDS for **Water-Based Red Oxide Primer 20L** (folder exists at `3.Resources/.../Wter Based Red Oxide Primer/` but contains only a docx that is content-mislabelled to Rugged Beauty).
10. **Olympic Technical** to issue official 2026 TDS for **Olympic Damp Fix** (no folder or TDS exists locally — the product appears on the PDF price list but is undocumented in the technical resources).

---

## Finalisation pass — 2026-05-12

### Product Features condensed to 5-line standard (per Quintus)

The verbose 11-line technical block was replaced with the 5-line standard for all 19 rows:

```
Polymer: <Styrene/Pure Acrylic>     ← Resin: Long Oil Alkyd for alkyds
Finish: <Matt/Sheen/Gloss/Textured/Primer/Undercoat>
Coverage: <m² per litre>
Touch dry: <hours>
Hard dry / Overcoat: <hours>        ← Hard dry: <hours> for alkyds (no overcoat line)
```

Red Oxide (R20) and Damp Fix (R21) carry a 6th `Note: full TDS pending issue by Olympic Technical.` line because their core spec values are not yet published.

### Product images restored from the original backup

The original `OneDayOnely.xlsx`/`OneDayOnlyData.xlsx` stored images using Excel 365's "Image in Cell" rich-data format (incompatible with openpyxl, which is why our earlier reads showed `#VALUE!` in column A). I parsed the worksheet XML's `vm` attributes to map each image to its original row, then extracted all 12 product images from `xl/media/` in the backup zip to a new `images/` folder and re-embedded them as anchored drawings in column A of the working file. This format is fully portable and editable.

| Restored | Count | SKUs |
|---|---|---|
| Images embedded in column A | 12 | 139401, 139801, 129401, 209401, 499401, 459401, 399401, 149401, 229801, 409801, 279842, 329422 |
| **Missing image — need to source** | 7 | E9401 (Eclipse), 229401 (Universal Undercoat 20L), 299401 (High Gloss Enamel), 359401 (All-In-One Primer), 309421 (Universal Roof), 379475 (Red Oxide Primer), Damp Fix |

The 12 raw image files now live in `2.Areas/1. Sales/2. ODO/images/` named by SKU — re-usable next time the sheet needs to be rebuilt without going through the old rich-data format.

### Action items added 2026-05-12 (finalisation)

11. **BLAZE / Marketing** to provide product bucket / can photographs for the 7 SKUs without an image: **Eclipse 20L, Universal Undercoat 20L, High Gloss Enamel 20L, All-In-One Primer 20L, Universal Roof Black 20L, Red Oxide Primer 20L, Damp Fix 5L**. These are needed before each appears in a scheduled ODO submission. JPEG or PNG, square aspect, transparent or white background, ≥ 800px on the long edge.
