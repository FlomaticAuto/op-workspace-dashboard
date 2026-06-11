# FLASH — ODO Submission Schedule

**Cadence:** 4 submissions per week (Mon–Thu); each Mon/Tue/Wed/Thu pushes one bundled product sheet to ODO covering 2–3 products. The schedule **rotates on a 3-week cycle** then loops indefinitely.

**Cycle anchor:** Cycle Week 1 = the week beginning **Monday 18 May 2026** (shifted from the original 9 Feb 2026 anchor on Quintus's instruction "ignore the dates in my work — start from activation").

**ISO week tracking:** Cycle Week 1 corresponds to ISO week 21/2026. The cycle then maps as `(iso_week - 21) mod 3` → 0 = Cycle 1, 1 = Cycle 2, 2 = Cycle 3.

---

## Cycle Week 1

| Day | Date | Products to pitch | SKUs |
|---|---|---|---|
| Mon | 18 May 2026 | Décor PVA · Kalahari Contractors PVA · Master Decorators PVA | `139401` · `129401` · `209401` |
| Tue | 19 May 2026 | Hi-Hiding Contractors PVA · Suburban Bliss · Natural Elegance Sheen | `499401` · `459401` · `399401` |
| Wed | 20 May 2026 | Rugged Beauty Textured · Universal Undercoat (20L) | `149401` · `229401` |
| Thu | 21 May 2026 | High Gloss Enamel · Platinum Plus Ultimate Shine · Zinc Phosphate Primer | `299401` · `409801` · `279842` |

## Cycle Week 2

| Day | Date | Products to pitch | SKUs |
|---|---|---|---|
| Mon | 25 May 2026 | Eclipse PVA · Suburban Bliss | `E9401` · `459401` |
| Tue | 26 May 2026 | Hi-Hiding · Kalahari Contractors · All-In-One Primer | `499401` · `129401` · `359401` |
| Wed | 27 May 2026 | Universal Roof Coating (Black) · Plush Coat Roof Coating (Charcoal) | `309421` · `329422` |
| Thu | 28 May 2026 | Olympic Damp Fix (5L) — solo | `<5L Damp Fix SKU>` (verify with pricing) |

## Cycle Week 3

| Day | Date | Products to pitch | SKUs |
|---|---|---|---|
| Mon | 1 Jun 2026  | Décor PVA · Master Decorators PVA | `139401` · `209401` |
| Tue | 2 Jun 2026  | Natural Elegance Sheen · Suburban Bliss · All-In-One Primer | `399401` · `459401` · `359401` |
| Wed | 3 Jun 2026  | Rugged Beauty Textured · Universal Undercoat (20L) | `149401` · `229401` |
| Thu | 4 Jun 2026  | High Gloss Enamel · Red Oxide Primer | `299401` · `379475` |

---

## Cycle Week 4 onwards (rolling loop)

After Thursday 4 June 2026 the cycle restarts at Cycle Week 1 (Monday 8 June 2026).

| Cycle | Week starting | Repeats |
|---|---|---|
| Cycle 1 | 18 May 2026 | (first run) |
| Cycle 2 | 25 May 2026 | (first run) |
| Cycle 3 | 1 Jun 2026  | (first run) |
| Cycle 1 | 8 Jun 2026  | repeat |
| Cycle 2 | 15 Jun 2026 | repeat |
| Cycle 3 | 22 Jun 2026 | repeat |
| Cycle 1 | 29 Jun 2026 | repeat |
| … | | continues indefinitely |

---

## How FLASH uses this schedule

Each weekday morning at **07:00**, FLASH:

1. Computes today's cycle-week via `(iso_week(today) - 21) mod 3 + 1`.
2. Looks up today's products from the matching cycle-week table above.
3. Confirms the SKU rows still exist and are priced in the current `OneDayOnlyData.xlsx`.
4. **Drafts** a new `Product Sheet Template (Share)` populated only with today's product rows (Brand, Product, SKU, Units = 100, Info, Features, Dimensions, Cost ex-VAT, RSP). Save to a working location, e.g. `Sheets To Submit/ODO Sheet — YYYY-MM-DD.xlsx`.
5. **Prepares JPEG attachments** — copies each product's image from `images/<SKU>.*`, converts any PNGs to JPEG (Quality 90, sRGB), renames `<SKU>_<short-name>.jpg`. ODO requires the JPEGs separately even though they are embedded in the sheet.
6. **Drafts** the cover email to the active ODO Account Manager (per `CONTACTS.md`) using template `EMAIL_TEMPLATES.md § L1`.
7. Saves the email as an **Outlook draft** addressed to the current AM, attaches the **xlsx + every JPEG**, leaves it unsent.
8. **Telegrams Quintus** at `8042233389`: "FLASH: ODO sheet drafted for [date] — [n] products — [names]. [n] JPEGs attached. Outlook draft saved."
9. Quintus reviews + sends.

If a scheduled product has no image in `images/<SKU>.*`, FLASH **holds that product off the day's submission** rather than silently sending an incomplete sheet. Other products on the same day still go forward. The held product is flagged on Telegram so BLAZE can source the JPEG before the next cycle.

---

## Drift handling

- **Public holiday on a sales day** → FLASH skips that day and rolls the missed products into the **next** sales day's submission bundle. Telegram alert: "FLASH: [holiday] on [date]. Rolling [products] into [next sales day]."
- **Quintus instructs a pause** → schedule paused, all draft generation suspended until `/flash resume`.
- **Product runs out / discontinued** → FLASH leaves the day with the remaining products only, alerts to add a replacement.
- **Pricing change** → `OneDayOnlyData.xlsx` rebuilt from the latest price list; affected cycle-week tables auto-regenerate from the canonical product list (this file gets updated).

---

## Change log

- **2026-05-12** — Schedule built from Quintus's original 9 Feb anchor, shifted to 18 May 2026 start. Olympic Damp Sealer + Fix dropped from Week 2 Thursday (no 2026 price). Confirmed by Quintus.
