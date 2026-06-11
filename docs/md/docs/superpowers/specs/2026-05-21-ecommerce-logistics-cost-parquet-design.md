# E-Commerce Logistics Cost Parquet — Design

**Date:** 2026-05-21
**Owner:** Quintus Lategan
**Status:** Approved — ready for implementation plan

## Purpose

Ingest courier invoices from `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/` into a single parquet that can be grouped by month to compute **logistics cost as a % of e-commerce product revenue**.

The reporting question this answers: *for each calendar month, what share of e-commerce gross sales went to courier delivery?*

## Scope

- **In scope:** parse RMZ Freight PDF invoices and Pudo-style wallet transaction CSVs into one canonical parquet; produce a monthly CLI report joining against WooCommerce revenue.
- **Out of scope:**
  - Per-customer / per-waybill attribution (parquet stays invoice-level; source PDFs preserved for future re-parse).
  - VAT-exclusive ratio (chose incl-VAT — apples-to-apples cash basis).
  - Auto-fetch from courier portals (drop-folder model).
  - Dashboard / HTML report (CLI markdown is sufficient for now).

## Sources

| Source | Format | Cadence | Notes |
|---|---|---|---|
| RMZ Freight | PDF (Zoho Invoice template) | Monthly-ish, Net 30 | Header has invoice no + date; line items are per-shipment with customer name + waybill |
| Pudo wallet | CSV (`Wallet+transactions+report*.csv`) | Per-export | Each row is a per-label debit; waybill in description; no customer name |

## Parquet schema — `ecommerce_logistics_cost.parquet`

**Grain:** one row per courier invoice (PDF) or per wallet statement file (CSV).

| Column | Type | Notes |
|---|---|---|
| `invoice_id` | string | Stable PK: `RMZ-INV-001385` or `WALLET-2025-11` |
| `source` | string | `RMZ` \| `Pudo Wallet` (extendable) |
| `vendor` | string | `RMZ FREIGHT PTY LTD` etc. |
| `invoice_no` | string | Raw invoice number from PDF; blank for wallet rollups |
| `invoice_date` | date | PDF header date; for wallets = last transaction date in the file |
| `cost_month` | string (`YYYY-MM`) | Derived from `invoice_date`; primary group key |
| `amount_incl_vat` | float | Invoice total. RMZ shows no VAT separately → treated as the total |
| `line_count` | int | Number of shipments on this invoice (audit/sanity) |
| `source_file` | string | Filename, for traceability |
| `ingested_at` | datetime | When this row was parsed |

### Decisions locked in during brainstorm

| Question | Decision |
|---|---|
| Cost ↔ order join | Monthly bucket only. No per-order match. |
| Date semantics | Invoice / transaction date (when the charge was incurred). |
| Ratio basis | Incl-VAT ÷ incl-VAT. Cash terms. |
| Output location | Co-located with invoices folder. |
| Row grain | One row per invoice / wallet file (totals only). |

## Ingest flow

```
ingest_logistics_invoices.py
  1. Scan 'Delivery Invoices/' for *.pdf and *.csv not in _processed/
  2. Detect type:
       PDF starting with "INV-"            → RMZ parser
       CSV named "Wallet+transactions*"    → Pudo wallet parser
  3. Parse → emit one row dict per file
  4. Read existing parquet (if present), upsert by invoice_id
  5. Write parquet (atomic via .tmp + os.replace)
  6. Move source file to _processed/<source>/
  7. Print summary: N files ingested, M rows added/updated
```

### Parsers

**RMZ PDF parser** (`pdfplumber` or `pypdf` for text extraction):
- Extract invoice number from "# INV-XXXXXXX" header.
- Extract invoice date from "Invoice Date :" line.
- Extract total from "Total R..." or "Sub Total ..." (validate they match).
- Count line items (rows between header and "Sub Total") for `line_count`.

**Pudo wallet CSV parser** (`pandas.read_csv`):
- Sum `Amount` column (values are negative → `abs(sum)` = total debit).
- Take min/max of `Transaction Date UTC` to confirm single-month coverage; use max as `invoice_date`.
- `invoice_id = f"WALLET-{cost_month}"`.
- If a single CSV spans multiple months, split into one row per month.

## Idempotency

- `invoice_id` is the PK. Re-running on the same file overwrites, doesn't duplicate.
- `_processed/<source>/` move means a normal re-run does nothing (inbox is empty).
- `--reingest` flag re-scans `_processed/` for backfill (rebuilds parquet from scratch).

## Reporting helper (separate, small)

`logistics_cost_monthly.py` — reads the parquet + the WooCommerce orders source, prints a markdown table:

```
| Month   | E-comm revenue (incl VAT) | Logistics cost (incl VAT) | Logistics % |
|---------|---------------------------|---------------------------|-------------|
| 2025-11 | R 48,210.00               | R 3,890.50                | 8.07%       |
| 2025-12 | R 62,140.00               | R 4,712.00                | 7.58%       |
```

WooCommerce revenue source: the same CSV/parquet `build_ecommerce_dashboard.py` already consumes (TBD — confirm in the implementation plan).

## File / folder layout

```
2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/
├── *.pdf, *.csv                              ← inbox (drop new invoices here)
├── ecommerce_logistics_cost.parquet          ← output
├── _processed/
│   ├── RMZ/                                  ← consumed PDFs
│   └── Pudo Wallet/                          ← consumed CSVs
└── _scripts/
    ├── ingest_logistics_invoices.py
    └── logistics_cost_monthly.py
```

## Risks / open items

- RMZ PDF layout could change (Zoho Invoice template updates) — parser must fail loudly with the offending filename, not silently skip.
- Wallet CSVs spanning >1 month: handled by splitting into one row per month (above).
- Future PDF vendors (other couriers) — schema is extensible via the `source` column; add a new parser branch.

## Success criteria

1. All 11 RMZ PDFs + 2 wallet CSVs in the folder ingest cleanly on first run.
2. `ecommerce_logistics_cost.parquet` exists with the schema above and N=13 rows (one per source file, minus any multi-month wallet splits).
3. `logistics_cost_monthly.py` prints a monthly table with non-zero ratios.
4. Re-running ingest is a no-op (inbox empty, parquet unchanged).
