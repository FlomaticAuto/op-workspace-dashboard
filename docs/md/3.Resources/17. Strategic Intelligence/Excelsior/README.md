# Excelsior Paints — Competitor Intelligence

_Last updated: 2026-05-16_

**Location:** `3.Resources/17. Strategic Intelligence/Excelsior/` (sits alongside `Stevensons/` and the strategic intelligence files).

This folder contains a complete TDS and MSDS catalogue for **Excelsior Paints** (Johannesburg-based, 80+ year SA family company, SAPMA member). Built as part of the Olympic Paints competitor analysis programme.

---

## Folder structure

```
Excelsior/
├── README.md                        ← this file
├── TDS/                             ← 37 Technical Data Sheets (PDF)
├── MSDS/                            ← 35 Material Safety Data Sheets (PDF)
├── _raw_downloads/                  ← original PDFs as downloaded (kept for forensics)
├── _scraped_html/                   ← raw HTML of each Excelsior product page (37 files)
├── _scrape_excelsior.py             ← scraper: fetches product pages, finds PDF URLs
├── _download_gdrive_pdfs.py         ← downloader: pulls each PDF via Google Drive direct URL
├── _redownload_and_classify.py      ← v3 downloader with pypdf-based classification
├── _fixup_classify.py               ← size-heuristic classifier for files pypdf couldn't read
├── scrape_manifest.json             ← per-product URL inventory
└── download_log.json                ← per-file download + classification log
```

The full comparative analysis lives one level up at:
`3.Resources/17. Strategic Intelligence/Olympic_vs_Excelsior_Competitor_Analysis.xlsx`

---

## How the catalogue was built

1. **Scraped** all 37 product pages from https://www.excelsiorpaints.co.za/product-page/<slug>
2. **Extracted** PDF URLs from raw HTML — Excelsior hosts all TDS and MSDS files on **Google Drive view-only links** (`drive.google.com/file/d/...` and `drive.google.com/open?id=...`)
3. **Converted** Google Drive view URLs to direct-download URLs (`drive.google.com/uc?export=download&id=...`)
4. **Downloaded** all 72 PDFs (37 products × 2 documents each, except 2 products with only TDS)
5. **Classified** each PDF as TDS or MSDS using `pypdf` text extraction on page 1, with a size-heuristic fallback for files where pypdf could not extract text (image-based or non-standard font encoding)

To re-run any step: `python <script_name>.py` from this folder.

---

## Excelsior product range overview

| Range | Tier | Stated Guarantee | Count | Key Products |
|---|---|---|---|---|
| **Premium** | Top-of-line | 10 / 12 / 15 YEAR+ | 13 | Supa Matt, Supa Satin, High Gloss Enamel, Eggshell Enamel, Satin Roof Acrylic, Rubberlastic, Weatherflex, Pliolite Primer |
| **All Purpose** | Mid-tier | 8–10 YEAR+ | 6 | Matt / Sheen / Textured Acrylic, Gloss / Eggshell Enamel, **6in1 Multi-Task Acrylic** |
| **Trade Decorators** | Contractor value | None stated | 8 | Matt / Satin / Roof / Hi-Hiding / Formula 74, Plaster Primers, Undercoat |
| **Care-4-Metal** | Specialty metal | varies | 9 | Hammered Aluminium, Braai Coat, Aqua-Metalprime, Rust Stop, GI Primer/Cleaner, XL Degreaser, Bituminous |
| **Aqua-Var** | Wood | not stated | 1 | Exterior Gloss Varnish |

**Total: 37 SKUs across 5 ranges**

---

## Key competitive findings (vs Olympic Paints)

See `Olympic_vs_Excelsior_Competitor_Analysis.xlsx` → **Executive Summary** sheet for the full picture. Headlines:

### Where Olympic wins
- **All-In-One Primer**: 8-10 m²/L vs Excelsior 4-8 m²/L, hard dry 6-8 hr vs 18 hr (3× faster) — single biggest spec win
- **Plush Coat / 3-in-1 Roof**: Pure Acrylic chemistry vs Excelsior Co-polymer (hierarchy win)
- **Fibre Restore**: ZERO VOC + fibre reinforcement vs Rubberlastic's Low VOC + no fibre
- **Suburban Bliss / Natural Elegance**: Pure Acrylic chemistry parity with Excelsior premium

### Where Olympic loses
- **No published guarantee year-count** on any Olympic TDS (Excelsior puts 10/12/15 YEAR+ on every bucket)
- **Ultimate Shine Enamel**: coverage 4-5 m²/L vs Excelsior 9-10 m²/L (2× gap), shelf life 8 mo vs 12 mo
- **7-in-1 PVA**: solids 34% vs Excelsior 6in1 45-50%; drying 2-3hr vs 30 min
- **No SABS/SANS marks published** on Olympic TDSs (Excelsior cites SABS 1586 Gr 1/2 and SANS 940:2005)
- **No metal specialty range** (Excelsior Care-4-Metal is 8 SKUs of profit centre)
- **No eggshell enamel** (Excelsior has it in both Premium and All Purpose tiers)
- **No wood range** (Excelsior Aqua-Var category)

---

## Source

All TDS and MSDS PDFs sourced from Excelsior Paints' public Google Drive links, accessed via their product pages at https://www.excelsiorpaints.co.za. Files retained for competitive-analysis purposes under fair-use research provisions. Do not redistribute.

---

## Re-running the catalogue

If Excelsior updates their range or TDS PDFs:

```powershell
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence\Excelsior"
python _scrape_excelsior.py           # scrape product pages + find new PDF URLs
python _redownload_and_classify.py    # download + auto-classify TDS / MSDS
python _fixup_classify.py             # size-based fallback for unclassified files
```

Then re-run the comparison workbook:

```powershell
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence"
python _build_excelsior_xlsx_v2.py
```
