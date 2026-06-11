# SLM Competitor-Doc Extraction — Build Spec

**Purpose:** Hand the *first-pass extraction* of competitor price lists to a local
vision model. A doc drops into `_field-intake/` — a WhatsApp photo, screenshot, or
PDF of a price list — and the model pulls structured rows (competitor, product,
pack, price, VAT basis, price type) into a **staging file for review**. Claude or
you then interpret and promote them into the `Olympic_vs_X` workbooks and
`pricing-intelligence.md`. The model never writes into those curated files.

**Why this task:** the output schema already exists (see `pricing-intelligence.md`),
the docs arrive often, and the data — competitor pricing — is exactly what you want
kept on your own box. Same offload profile as the email triage, one tier up because
the input is images.

**Status:** draft v0.1 — 2026-06-09. Sibling to `_slm-triage/`.

---

## 1. Architecture

```
_field-intake/*.{jpg,jpeg,png,pdf}
      │  (PDF pages rendered to images via PyMuPDF)
      ▼
  local VISION SLM (Ollama: llama3.2-vision)  ──►  JSON rows per doc
      │
      │  validate (numbers, enums) + flag needs_review
      ▼
  _extract/staging-YYYY-MM-DD.csv   +   _extract/<doc>.json
      │
      ▼
  YOU / Claude review  ──►  promote into Olympic_vs_X.xlsx + pricing-intelligence.md
```

The model only reads pixels and emits candidate rows. Nothing is trusted into the
intelligence of record without a human/Claude pass — that boundary is the whole
safety design, because a misread price is worse than no price.

---

## 2. Model & runtime

Local via **Ollama**, vision-capable:

| Need | Pick |
|---|---|
| Recommended | `llama3.2-vision:11b` — reads price tables, keeps columns aligned |
| Lighter box | `minicpm-v` or `llava:7b` (lower table accuracy — expect more review flags) |

```
ollama pull llama3.2-vision:11b
pip install requests pymupdf --break-system-packages
```

~8GB+ free RAM/VRAM for the 11B. Force JSON with Ollama's `format: json`.
(Check for newer local vision models when you build — this reflects mid-2025.)

---

## 3. Output schema (one row per product × pack size)

Matches the `pricing-intelligence.md` benchmark tables.

| Field | Notes |
|---|---|
| `competitor` | Crest, Dulux, Plascon, Berger, Golden Choice… (doc-level) |
| `product` | e.g. "Crest Extra Thick PVA" |
| `category` | `PVA \| Enamel \| Primer \| Varnish \| Filler \| Waterproofing \| Other \| Unknown` |
| `pack_size` | `1L, 5L, 20L, 500G, 2KG, 10KG…` as printed |
| `price_rand` | numeric, e.g. `99.99` or `1298` |
| `price_raw` | original text e.g. `"R 99,99"` — kept for audit |
| `vat_basis` | `ex-VAT \| incl-VAT \| Unknown` (doc-level: wholesale lists are usually ex-VAT, retail ads incl) |
| `price_type` | `wholesale \| retail \| factory \| Unknown` |
| `source_file` | filename in `_field-intake/` |
| `source_page` | PDF page (1 for images) |
| `confidence` | 0.0–1.0 |
| `needs_review` | TRUE if confidence < 0.7, price unparseable, or any enum = Unknown |
| `notes` | model's short note / ambiguity flag |

**SA number trap:** `R 99,99` = 99.99 (comma = decimal), but `R 1,298` = 1298
(comma = thousands). The harness parses both; the model returns the numeric value
*and* the raw string so a wrong parse is auditable.

---

## 4. Vision prompt (paste verbatim)

```
You are a price-list extraction engine for Olympic Paints competitor intelligence.
You are shown ONE image of a competitor price list. Extract every product/price you
can read. Do not guess prices you cannot read clearly — lower the confidence instead.

Return ONLY a JSON object:
{
  "competitor":  the brand/company name on the sheet, or "Unknown",
  "price_type":  one of ["wholesale","retail","factory","Unknown"],
  "vat_basis":   one of ["ex-VAT","incl-VAT","Unknown"],
  "rows": [
    {
      "product":   product name as printed,
      "category":  one of ["PVA","Enamel","Primer","Varnish","Filler","Waterproofing","Other","Unknown"],
      "pack_size": e.g. "5L","20L","1L","500G","2KG", as printed,
      "price_raw": the price exactly as printed, e.g. "R 99,99",
      "price_rand": that price as a plain number (99.99),
      "confidence": 0.0 to 1.0 for THIS row,
      "notes": "" or a short flag if unclear (max 12 words)
    }
  ]
}

RULES:
- One row per product AND pack size. A product sold in 5L and 20L = two rows.
- South African prices: "R 99,99" means 99.99 (comma is the decimal). "R 1 298" or
  "R 1,298" means 1298 (space/comma is thousands).
- If you cannot read a value, put "Unknown"/null and set that row's confidence below 0.5.
- Never invent products or prices. Never add keys. Output only the JSON.
```

---

## 5. Review rule (what gets flagged, not escalated to Claude live)

Unlike triage, this is event-driven, not a daily alert. Every row lands in the
staging CSV; `needs_review = TRUE` when any of:

1. row `confidence < 0.7`
2. `price_rand` missing or not a positive number
3. `category`, `vat_basis`, or `price_type` = Unknown
4. doc-level `competitor` = Unknown

You sort the CSV by `needs_review` and eyeball those first. Clean high-confidence
rows can be promoted in bulk. Expect photos/skew/glare to drive most flags.

---

## 6. Validation (in the harness, not the model)

- Coerce every enum to its allowed set; anything else → Unknown → flags the row.
- Re-parse `price_rand` from `price_raw` in Python using the SA rule, and compare to
  the model's number; mismatch → flag. Python's parse wins.
- Drop fully empty rows. Keep partial rows but flag them — a half-read row is a lead
  to re-shoot the photo, not noise.
- Write one `<doc>.json` per source so every staging row traces back to its origin.

---

## 7. Rollout

1. **Backfill test.** Run it over the existing `_field-intake/_archive/` (you have
   Crest/Stevensons, Golden Choice, Fast Solvents PDFs + WhatsApp photos). Compare the
   staging rows to the Crest table already in `pricing-intelligence.md` — that table is
   your ground truth for accuracy.
2. **Tune** the confidence flag threshold from what the backfill shows.
3. **Standing use.** Drop a new doc in `_field-intake/`, run on demand, review staging,
   promote. Optionally a watcher that runs when the folder changes — but on-demand is
   fine; these don't arrive daily.

---

## 8. Honest caveats

- Vision OCR of phone photos is the weak point: glare, angle, and creased paper cause
  misreads. The confidence flag and `price_raw`/`price_rand` cross-check exist for this.
- Never let it write the workbooks. A wrong competitor price that reaches a rep is worse
  than a blank — the human review gate is non-negotiable here.
- If one competitor's list is always the same layout (e.g. a regular Stevensons PDF),
  a fixed parser for that one format will beat the model. Use the SLM for the long tail
  of one-off photos.
```
