# Competitor Information → Olympic Paints Matrix

Turns the raw competitor files in `2.Areas/1. Sales/7. Competitor information/` into a structured Excel sheet that maps every competitor line item to its closest Olympic Paints product, ready for rep validation.

---

## Output

`Output/Competitor Product Matrix.xlsx` — one row per competitor SKU.

Columns the **rep fills in**:
- `Rep Confirms? (Y/N)`
- `Correct Olympic Code (Rep)` — override if the suggestion is wrong
- `Rep Notes`

Columns the **script fills in**:
- Competitor: Brand, Category, Sub-Category, Description, Colour, Size, Stock Code, Barcode, Price (Excl VAT)
- Suggested Olympic match: Code, Product Name, Median Price
- Delta: Olympic vs Competitor (Δ%)
- Match Confidence: **HIGH / MED / LOW** (colour-coded)
- Match Reason: which signals matched — `family / size / colour`

Two extra summary sheets:
- **Summary by Brand** — row counts × confidence
- **Categories** — what categories we extracted per brand

---

## Pipeline

```
                ┌────────── extracted/*.json (per source) ──────────┐
PDFs ──► parse_fast_solvents.py                                     │
DOCX ──► parse_crest_docx.py                                        ├─► build_competitor_matrix.py ─► Output/Competitor Product Matrix.xlsx
Image ──► encode_anetic.py    (manual transcription, see below)     │
PDF  ──► encode_buhle.py      (manual transcription, see below)     │
Image ──► encode_ecostar.py   (manual transcription, see below)     │
                └─────────────────────────────────────────────────────┘
```

| Script | Source | Notes |
|---|---|---|
| `parse_fast_solvents.py` | `Fast Solvents & Sundries FACTORY price list 01APR26.pdf` | Auto: PDF text is regular tabular text, regex-parsed |
| `parse_crest_docx.py` | `Document1.docx` | Auto: Word tables iterated via python-docx |
| `encode_buhle.py` | `Golden Choice 2026.pdf` | Manual: PDF text extraction garbles columns; data hand-encoded from page renders |
| `encode_anetic.py` | `WhatsApp Image 2026-05-14 at 11.33.27.jpeg` | Manual: image, no OCR pipeline |
| `encode_ecostar.py` | `Screenshot 2026-05-14 135746.jpg` | Manual: single product photo, no price |
| `build_competitor_matrix.py` | `extracted/*.json` + Olympic master | Match + write Excel |

The Olympic product master is read from `3.Resources/16.Sales and Other data/Customer Pricelist Odoo.xlsx`.

---

## How to add a new competitor source

1. **Drop the new file** into `2.Areas/1. Sales/7. Competitor information/`.
2. **Extract it**, depending on shape:
   - Clean tabular PDF → copy `parse_fast_solvents.py` and adapt the regex.
   - Word doc with tables → copy `parse_crest_docx.py`.
   - Image or messy PDF → use Claude (or a vision model) to read it, then write an `encode_<brand>.py` that emits the same JSON shape (see below).
3. **JSON record shape** (one row per SKU):
   ```json
   {
     "brand": "Brandname",
     "source_file": "Original filename.pdf",
     "category": "High Gloss Enamel",       // see CATEGORY_MAP keys
     "subcategory": "AN70 External PVA",     // optional
     "description": "Optional full description",
     "colour": "White",                       // optional, where applicable
     "size": "5L",                            // standardised: 1L/5L/20L/750ML/1KG etc
     "pack_qty": "12",                        // optional
     "stock_code": "SOLA750",                 // optional
     "barcode": "6006459001326",              // optional
     "price_excl_vat": 54.95,                 // null if POA
     "price_note": "POA",                     // optional
     "currency": "ZAR"
   }
   ```
4. **Update `CATEGORY_MAP`** in `build_competitor_matrix.py` if the new file has categories the matcher doesn't know about. Each entry says which Olympic product-name keywords are valid matches.
5. **Re-run** `python build_competitor_matrix.py`.

---

## How the matcher works (HIGH / MED / LOW)

For each competitor row:
1. Look up the row's `category` in `CATEGORY_MAP` → get the list of Olympic keywords.
2. Filter Olympic products whose name contains any keyword → **family hit**.
3. Within that, filter by exact size token (e.g. `5L`) → **size hit**.
4. Within that, filter by colour substring (e.g. `WHITE`) → **colour hit**.

Confidence:
- **HIGH** — all three matched (family + size + colour)
- **MED** — two of three (typically family + size, missing colour)
- **LOW** — only family, or no category mapping at all

The matcher always picks the first remaining candidate, so:
- **Reps must still validate**. The confidence label is a workload guide, not a guarantee.
- LOW rows are usually products with no Olympic equivalent (e.g. Buhle Rubber Flex, Anetic Cornice Glue, Fast Acetone). Reps should leave `Rep Confirms?` blank or write "No equivalent".

---

## Commands

```bash
cd "c:/Users/quint/OneDrive/1.Projects/1.Olympic Paints/2.Areas/1. Sales/7. Competitor information/scripts"

# regenerate all extracted JSONs from source (idempotent)
python parse_fast_solvents.py
python parse_crest_docx.py
python encode_buhle.py
python encode_anetic.py
python encode_ecostar.py

# build the matrix
python build_competitor_matrix.py
```

---

## Dependencies

```bash
pip install pypdf python-docx pandas openpyxl pymupdf
```

`pymupdf` is only needed if you want to re-render messy PDFs to images (see `_render/` for the Golden Choice page renders).
