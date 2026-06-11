# Competitor Product Verification JotForms — Design

**Date:** 2026-05-16
**Owner:** Quintus Lategan (CSO)
**Audience:** Sales reps (AC, AP, BV, NP, BM)
**Status:** Approved — ready for plan

---

## 1. Goal

Validate that the Olympic product mapped against each competitor SKU in our six `Olympic_vs_<Brand>_Competitor_Analysis.xlsx` workbooks is actually the right match in the field. Reps confirm or correct the matchup using daily category-filtered JotForms.

## 2. Why now

The workbooks were built from desk research (TDS + pricelist). Memory entries [[feedback_pva_vs_enamel_categories]] and [[feedback_pick_n_save_enamel_match]] show category-mismatch errors slipped past prior reviews. Rep field experience is the missing input. Without their sign-off, every battlecard rests on assumptions.

## 3. Scope

### In scope
- 5 competitors: **Africa Paints, Anetic, Crest, Excelsior, Golden Choice**
- 3 category forms per competitor = **15 forms** total
- 5 reps receive every form
- Daily email delivery over 3 consecutive working days
- Olympic dropdown sourced from `2.Areas/1. Sales/1. Pricing/List Price 2026 15 % Increase.xlsx` (733 SKUs)
- Competitor row data sourced from `3.Resources/17. Strategic Intelligence/Olympic_vs_<Brand>_Competitor_Analysis.xlsx` (5 files, Overview Matrix sheet)

### Out of scope (deliberately)
- Auto-updating the competitor workbooks from submissions — manual review afterwards
- Webhook integrations
- Mobile-native form app — JotForm's responsive forms are enough
- Reminder cadence — single email per day, no re-sends in v1

## 4. Category bucketing (the load-bearing rule)

Filtered dropdowns enforce category discipline that judgment alone fails at.

**Enamels (Day 1, ~272 SKUs)**
High Gloss · QD Enamel · Ultimate Shine · Pick & Save · QD Primer · Eggshell · Universal Undercoat · Zinc Phosphate · Wood Primer · Wood Varnish · Etch Primer · Sanding Sealer · Primer · Aerosol

**PVAs (Day 2, ~286 SKUs)**
Rugged Beauty · Master Decorators · Kalahari Contractors · Decor · Suburban Bliss · Natural Elegance · Eclipse PVA · 7-in-1 PVA · Distemper · All In One · Plush Coat · Schoolboard · Hi Hiding Contr · Plaster Primer · Just Paint · LIBERTY · Madalas Choice · Best Build

**Waterproofing / Accessories (Day 3, ~175 SKUs)**
Universal Roof · RainProof · Roof & Stoep · 3-in-1 Roof · Fibre Restore · Membrane · 3-in-1 Gripcoat · Crack Filler · Putty · Plaster n Tile Bond · Stainer · Oxide · Road Marking · Thinner · Turpentine · Carbolineum · Linseed Oil · Paint Remover · Galvanized Cleaner · Rust Remover · Bonding Liquid · FB Dressing · Accessories · Spirit of Salt

**Excluded:** Commission, Delivery (non-product lines).

## 5. Form structure (per form)

- **Title:** `Olympic vs <Competitor> — <Category> Matchup Verification`
- **Intro text:** Short paragraph: "Confirm the Olympic product we currently match against each <Competitor> <category> SKU. If wrong, pick the right one or flag it."
- **One row per competitor product** (JotForm Input Table widget):
  - Col A — Competitor SKU name (read-only display)
  - Col B — Competitor pack size + price (read-only display)
  - Col C — **Dropdown of Olympic SKUs in this category**, default = current match from workbook
  - Col D — Confidence radio: `Strong match` / `Acceptable` / `Wrong — see notes`
  - Col E — Notes (optional text)
- **Hidden fields** (URL-pre-fill): `rep_email`, `rep_code`, `competitor`, `category`
- **Submission:** Native JotForm storage. Pull via API for aggregation later.

## 6. Components

### 6.1 SKU categoriser (Python)
Reads `List Price 2026 15 % Increase.xlsx`, applies the bucketing table from §4, writes three JSON files:
```
output/olympic_skus_enamel.json
output/olympic_skus_pva.json
output/olympic_skus_waterproofing.json
```
Each entry: `{code, name, group, list_price}`. Single source of truth for every dropdown.

### 6.2 Competitor matchup extractor (Python)
For each of the 5 `Olympic_vs_<Brand>_Competitor_Analysis.xlsx` files:
- Read the Overview Matrix sheet
- For every row, classify the competitor product into a category (uses Olympic-side group as the signal — the bucketing already happened during workbook authoring)
- Emit `output/competitor_matchups_<brand>_<category>.json`:
  ```
  [
    {
      "competitor_product": "Hi-Lite QD Enamel White 20L",
      "pack_size": "20L",
      "competitor_price": "R897",
      "current_olympic_match_code": "115210",
      "current_olympic_match_name": "20LT QD ENAMEL WHITE"
    },
    ...
  ]
  ```

### 6.3 JotForm builder (Python + JotForm MCP)
For each `(competitor, category)` pair (15 total):
1. Create form via `mcp__claude_ai_Jotform__create_form`
2. Add title + intro
3. Add 4 hidden fields (rep_email, rep_code, competitor, category)
4. For each matchup row, add a labelled block: name + pack/price as static HTML, dropdown of category SKUs, confidence radio, notes textbox
5. Set default dropdown value to the current match code
6. Capture form URL, save to `output/jotform_urls.json`:
   ```
   { "stevensons": { "enamels": "https://form.jotform.com/...", ... }, ... }
   ```

### 6.4 Email dispatcher (Python + win32com Outlook)
- Three runs: Day 1 (Mon) Enamels · Day 2 (Tue) PVAs · Day 3 (Wed) Waterproofing
- Per rep, per day: one email with 5 form links (one per competitor), pre-filled with rep_email + rep_code via JotForm URL parameters
- Navy executive theme HTML template per [[feedback_email_report_workflow]]
- Force-flush per [[feedback_outlook_send_flush]]
- Recipients: rep email + cc `quintusl@olympicpaints.co.za`

### 6.5 Aggregator (out of scope for v1 — placeholder)
Future: pull submissions via JotForm API into `Rep_Competitor_Verification_Log.xlsx` for review.

## 7. Data flow

```
List Price 2026 15 % Increase.xlsx ──┐
                                     ├──> SKU categoriser ──> 3 SKU JSONs ──┐
Olympic_vs_<Brand>.xlsx (×5) ────────┴──> Matchup extractor ──> 15 JSONs ──┴──> JotForm builder ──> 15 forms + url map
                                                                                                       │
                                                                                                       ▼
                                                                                              Email dispatcher (×3 days)
                                                                                                       │
                                                                                                       ▼
                                                                                                  5 reps × 15 submissions
                                                                                                       │
                                                                                                       ▼
                                                                                                  JotForm native storage
                                                                                                  (aggregation: future)
```

## 8. File / path conventions

- All code: `2.Areas/1. Sales/7. Competitor information/jotform_verification/`
- Outputs: `2.Areas/1. Sales/7. Competitor information/jotform_verification/output/`
- Email templates: `2.Areas/1. Sales/7. Competitor information/jotform_verification/templates/`
- URL map (live state): `output/jotform_urls.json` — checked in, NOT regenerated unless rebuilding all forms

## 9. Open assumptions (verify during plan)

- **A1:** Every competitor workbook's Overview Matrix has a consistent column layout (competitor name, pack, price, Olympic match code, Olympic match name). Stevensons is the canonical format per [[feedback_competitor_side_by_side_format]] — verify the other 5 follow it.
- **A2:** JotForm MCP's `create_form` + `edit_form` support Input Table with default values and per-row dropdowns. If not, fall back to one labelled section per matchup row using `Dropdown` field type.
- **A3:** Rep email addresses live in PULSE config (`config['reps'][rep]['email']`). If not, source from staff portal data.
- **A4:** No regulatory/PII concern with rep-named submissions stored on JotForm cloud (sales product data only).

## 10. Success criteria

1. 15 forms exist on JotForm, each with the correct competitor products and category-filtered dropdowns
2. Each form's dropdown default matches the current matchup from the source workbook
3. Day 1 email lands with 6 enamel form links; Day 2 with 6 PVA links; Day 3 with 6 waterproofing links
4. All 5 reps can submit; submissions visible in JotForm dashboard
5. Memory entry added: `reference_competitor_verification_forms.md` with form URLs and rebuild instructions

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| JotForm MCP doesn't support all needed field types | Spike test with 1 form before building all 18; fall back to plain dropdowns if Input Table unsupported |
| Workbooks have inconsistent matrix layouts | Step in plan: open all 6 workbooks first, normalise extractor per layout |
| Rep email overload (6 links/day × 3 days) | Single consolidated email per day, not 6 separate ones; clear subject per day |
| SKU dropdown of ~280 PVAs is unwieldy on mobile | JotForm dropdowns are searchable; acceptable for v1 |
| Form URL leaked → outsider submits | JotForm's "Require login" or single-use URLs — defer to plan; for v1 use unguessable URL only |

## 12. What success looks like in 2 weeks

Every Olympic_vs_<Brand> workbook has a "Rep Verified" stamp on each row, sourced from the rep with strongest field exposure to that competitor. The 5–10 mismatches that surface drive the next round of workbook updates and become input for product team conversations on real portfolio gaps.
