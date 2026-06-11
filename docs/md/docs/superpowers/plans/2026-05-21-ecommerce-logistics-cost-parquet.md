# E-Commerce Logistics Cost Parquet — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest RMZ Freight PDF invoices and Pudo wallet CSVs from `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/` into a single parquet, then produce a monthly markdown report of logistics cost as a % of WooCommerce revenue.

**Architecture:** Two small standalone Python scripts in `Delivery Invoices/_scripts/`:
1. `ingest_logistics_invoices.py` — drop-folder ingest. Scans inbox, dispatches to a PDF or CSV parser based on filename, upserts rows into `ecommerce_logistics_cost.parquet` keyed by `invoice_id`, moves consumed files to `_processed/<source>/`.
2. `logistics_cost_monthly.py` — reads the parquet + `Woocommerce_Transactions.csv` (the existing WC export) and prints a monthly markdown table: revenue, logistics cost, ratio.

**Tech Stack:** Python 3, pdfplumber 0.11.9, pandas 2.3.3, pyarrow 24.0.0 (all already installed). No new dependencies.

---

## File Structure

```
2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/
├── *.pdf, *.csv                                 ← inbox (drop new invoices here)
├── ecommerce_logistics_cost.parquet             ← output (created on first run)
├── _processed/
│   ├── RMZ/                                     ← consumed PDFs
│   └── Pudo Wallet/                             ← consumed CSVs
└── _scripts/
    ├── parsers/
    │   ├── __init__.py
    │   ├── rmz_pdf.py                           ← RMZ PDF parser (one function)
    │   └── pudo_wallet.py                       ← Pudo CSV parser (one function)
    ├── ingest_logistics_invoices.py             ← CLI entrypoint for ingest
    ├── logistics_cost_monthly.py                ← CLI entrypoint for report
    └── tests/
        ├── __init__.py
        ├── conftest.py                          ← shared fixtures (sample files)
        ├── test_rmz_pdf.py
        ├── test_pudo_wallet.py
        ├── test_ingest.py                       ← end-to-end ingest test
        └── test_monthly_report.py
```

**Responsibility split:**
- `parsers/rmz_pdf.py` — owns RMZ PDF text extraction. One public function `parse_rmz_pdf(path) -> dict`. No filesystem writes, no parquet knowledge.
- `parsers/pudo_wallet.py` — owns Pudo CSV parsing. One public function `parse_pudo_wallet_csv(path) -> list[dict]` (list because a CSV can span multiple months). No filesystem writes.
- `ingest_logistics_invoices.py` — owns folder scanning, parquet upsert, file moves. Imports the two parsers.
- `logistics_cost_monthly.py` — owns the join with WooCommerce revenue and the markdown render.

Tests live next to scripts under `_scripts/tests/`. Sample files committed under `_scripts/tests/fixtures/` (one redacted RMZ PDF + one tiny wallet CSV).

---

## Task 1: Project scaffolding + fixtures

**Files:**
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/__init__.py` (empty)
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/parsers/__init__.py` (empty)
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/__init__.py` (empty)
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/conftest.py`
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/fixtures/sample_rmz.pdf` (copy of `INV-001385 (1).pdf`)
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/fixtures/sample_wallet.csv` (5-row trimmed copy of `Wallet+transactions+report (1).csv`)

- [ ] **Step 1: Create the folders and empty `__init__.py` files**

```bash
cd "2.Areas/1. Sales/5.Eccomerce/Delivery Invoices"
mkdir -p _scripts/parsers _scripts/tests/fixtures _processed/RMZ "_processed/Pudo Wallet"
touch _scripts/__init__.py _scripts/parsers/__init__.py _scripts/tests/__init__.py
```

- [ ] **Step 2: Copy fixture PDF and create trimmed wallet CSV fixture**

```bash
cp "INV-001385 (1).pdf" _scripts/tests/fixtures/sample_rmz.pdf
head -6 "Wallet+transactions+report (1).csv" > _scripts/tests/fixtures/sample_wallet.csv
```

- [ ] **Step 3: Write `conftest.py` with fixture path constants**

File: `_scripts/tests/conftest.py`

```python
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_rmz_pdf():
    return FIXTURES / "sample_rmz.pdf"

@pytest.fixture
def sample_wallet_csv():
    return FIXTURES / "sample_wallet.csv"
```

- [ ] **Step 4: Verify pytest discovers the test module**

Run from the `Delivery Invoices/` directory:
```bash
python -m pytest _scripts/tests/ -v --collect-only
```
Expected: `no tests ran` (no test files yet) — but no collection errors.

- [ ] **Step 5: Commit**

```bash
git add "_scripts/__init__.py" "_scripts/parsers/__init__.py" "_scripts/tests/__init__.py" "_scripts/tests/conftest.py" "_scripts/tests/fixtures/sample_rmz.pdf" "_scripts/tests/fixtures/sample_wallet.csv"
git commit -m "feat(logistics): scaffold _scripts/ folder and test fixtures"
```

---

## Task 2: RMZ PDF parser

**Files:**
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/parsers/rmz_pdf.py`
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/test_rmz_pdf.py`

- [ ] **Step 1: Write the failing test**

File: `_scripts/tests/test_rmz_pdf.py`

```python
from datetime import date
from _scripts.parsers.rmz_pdf import parse_rmz_pdf

def test_parse_rmz_pdf_extracts_canonical_row(sample_rmz_pdf):
    row = parse_rmz_pdf(sample_rmz_pdf)
    assert row["source"] == "RMZ"
    assert row["vendor"] == "RMZ FREIGHT PTY LTD"
    assert row["invoice_no"] == "INV-001385"
    assert row["invoice_id"] == "RMZ-INV-001385"
    assert row["invoice_date"] == date(2026, 3, 11)
    assert row["cost_month"] == "2026-03"
    assert row["amount_incl_vat"] == 1215.00
    assert row["line_count"] == 4
    assert row["source_file"] == "sample_rmz.pdf"
```

- [ ] **Step 2: Run the test to verify it fails**

Run from the `Delivery Invoices/` directory:
```bash
python -m pytest _scripts/tests/test_rmz_pdf.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named '_scripts.parsers.rmz_pdf'`.

- [ ] **Step 3: Implement the parser**

File: `_scripts/parsers/rmz_pdf.py`

```python
"""RMZ Freight PDF invoice parser.

Parses Zoho Invoice-template PDFs from RMZ Freight (Pty) Ltd into a
single canonical dict matching the ecommerce_logistics_cost.parquet schema.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pdfplumber

_INVOICE_NO_RE = re.compile(r"#\s*(INV-\d+)")
_INVOICE_DATE_RE = re.compile(r"Invoice Date\s*:\s*(\d{1,2}\s+\w+\s+\d{4})")
_TOTAL_RE = re.compile(r"Total\s+R?([\d,]+\.\d{2})")
# Line items are numbered 1, 2, 3... at the start of a line inside the items table
_LINE_ITEM_RE = re.compile(r"^\s*(\d+)\s+\S", re.MULTILINE)


class RmzPdfParseError(ValueError):
    """Raised when an RMZ PDF can't be parsed (layout changed?)."""


def parse_rmz_pdf(path: Path) -> dict:
    path = Path(path)
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    m_no = _INVOICE_NO_RE.search(text)
    if not m_no:
        raise RmzPdfParseError(f"{path.name}: could not find invoice number")
    invoice_no = m_no.group(1)

    m_date = _INVOICE_DATE_RE.search(text)
    if not m_date:
        raise RmzPdfParseError(f"{path.name}: could not find invoice date")
    invoice_date = datetime.strptime(m_date.group(1), "%d %b %Y").date()

    # Last "Total RX,XXX.XX" wins — the balance-due row repeats the total
    totals = _TOTAL_RE.findall(text)
    if not totals:
        raise RmzPdfParseError(f"{path.name}: could not find total amount")
    amount = float(totals[-1].replace(",", ""))

    # Count line items by matching leading "1 ", "2 ", ... in the items table.
    # Take the max number seen — robust to body text that happens to start with a digit.
    line_numbers = [int(n) for n in _LINE_ITEM_RE.findall(text)]
    line_count = max(line_numbers) if line_numbers else 0

    return {
        "invoice_id": f"RMZ-{invoice_no}",
        "source": "RMZ",
        "vendor": "RMZ FREIGHT PTY LTD",
        "invoice_no": invoice_no,
        "invoice_date": invoice_date,
        "cost_month": invoice_date.strftime("%Y-%m"),
        "amount_incl_vat": amount,
        "line_count": line_count,
        "source_file": path.name,
    }
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
python -m pytest _scripts/tests/test_rmz_pdf.py -v
```
Expected: PASS.

- [ ] **Step 5: Add a parse-failure test**

Append to `_scripts/tests/test_rmz_pdf.py`:

```python
import pytest
from _scripts.parsers.rmz_pdf import RmzPdfParseError

def test_parse_rmz_pdf_raises_on_garbage(tmp_path):
    bad = tmp_path / "bad.pdf"
    # Minimal valid PDF that has no RMZ content
    bad.write_bytes(b"%PDF-1.4\n%%EOF\n")
    with pytest.raises(RmzPdfParseError):
        parse_rmz_pdf(bad)
```

- [ ] **Step 6: Run all parser tests**

```bash
python -m pytest _scripts/tests/test_rmz_pdf.py -v
```
Expected: 2 PASSED.

- [ ] **Step 7: Commit**

```bash
git add "_scripts/parsers/rmz_pdf.py" "_scripts/tests/test_rmz_pdf.py"
git commit -m "feat(logistics): RMZ PDF invoice parser"
```

---

## Task 3: Pudo wallet CSV parser

**Files:**
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/parsers/pudo_wallet.py`
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/test_pudo_wallet.py`

- [ ] **Step 1: Inspect the trimmed fixture to confirm column names**

```bash
head -2 _scripts/tests/fixtures/sample_wallet.csv
```
Expected first row:
```
"ItemId","Transaction Date UTC","Balance Before","Amount","Balance After","Description","Negative Balance Allowed"
```

- [ ] **Step 2: Write the failing test**

File: `_scripts/tests/test_pudo_wallet.py`

```python
from datetime import date
from _scripts.parsers.pudo_wallet import parse_pudo_wallet_csv

def test_parse_pudo_wallet_csv_returns_one_row_per_month(sample_wallet_csv):
    rows = parse_pudo_wallet_csv(sample_wallet_csv)
    # Fixture has 5 transactions, all on 27 Nov 2025 → one month, one row
    assert len(rows) == 1
    row = rows[0]
    assert row["source"] == "Pudo Wallet"
    assert row["vendor"] == "Pudo Wallet"
    assert row["invoice_no"] == ""
    assert row["invoice_id"] == "WALLET-2025-11"
    assert row["cost_month"] == "2025-11"
    assert row["invoice_date"] == date(2025, 11, 27)
    # 80.50 + 149.50 + 17.25 + 17.25 + ? → recompute from the fixture, must be > 0
    assert row["amount_incl_vat"] > 0
    assert row["line_count"] == 5
    assert row["source_file"] == "sample_wallet.csv"
```

- [ ] **Step 3: Run the test to verify it fails**

```bash
python -m pytest _scripts/tests/test_pudo_wallet.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named '_scripts.parsers.pudo_wallet'`.

- [ ] **Step 4: Implement the parser**

File: `_scripts/parsers/pudo_wallet.py`

```python
"""Pudo Wallet transactions CSV parser.

Each CSV row is a per-label debit. We group by calendar month and emit one
row per month (matching the parquet's invoice-level grain).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


class PudoWalletParseError(ValueError):
    """Raised when a wallet CSV can't be parsed."""


def parse_pudo_wallet_csv(path: Path) -> list[dict]:
    path = Path(path)
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise PudoWalletParseError(f"{path.name}: failed to read CSV: {e}") from e

    required = {"Transaction Date UTC", "Amount"}
    missing = required - set(df.columns)
    if missing:
        raise PudoWalletParseError(f"{path.name}: missing columns {missing}")

    df["txn_dt"] = pd.to_datetime(df["Transaction Date UTC"], dayfirst=True, errors="coerce")
    if df["txn_dt"].isna().any():
        bad = df[df["txn_dt"].isna()]["Transaction Date UTC"].head(3).tolist()
        raise PudoWalletParseError(f"{path.name}: unparseable dates, e.g. {bad}")

    df["cost_month"] = df["txn_dt"].dt.strftime("%Y-%m")

    rows = []
    for cost_month, grp in df.groupby("cost_month", sort=True):
        # Amount column is negative for debits; total debit = abs(sum)
        amount = float(abs(grp["Amount"].sum()))
        last_dt = grp["txn_dt"].max().date()
        rows.append({
            "invoice_id": f"WALLET-{cost_month}",
            "source": "Pudo Wallet",
            "vendor": "Pudo Wallet",
            "invoice_no": "",
            "invoice_date": last_dt,
            "cost_month": cost_month,
            "amount_incl_vat": amount,
            "line_count": int(len(grp)),
            "source_file": path.name,
        })
    return rows
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
python -m pytest _scripts/tests/test_pudo_wallet.py -v
```
Expected: PASS.

- [ ] **Step 6: Add a multi-month test**

Append to `_scripts/tests/test_pudo_wallet.py`:

```python
import pandas as pd
from _scripts.parsers.pudo_wallet import parse_pudo_wallet_csv

def test_parse_pudo_wallet_csv_splits_multi_month_csv(tmp_path):
    csv = tmp_path / "multi.csv"
    pd.DataFrame({
        "ItemId": [1, 2, 3],
        "Transaction Date UTC": ["27/11/2025 1:01:08 PM", "03/12/2025 9:30:00 AM", "10/12/2025 2:00:00 PM"],
        "Balance Before": [100.0, 50.0, 30.0],
        "Amount": [-50.0, -20.0, -10.0],
        "Balance After": [50.0, 30.0, 20.0],
        "Description": ["a", "b", "c"],
        "Negative Balance Allowed": [True, True, True],
    }).to_csv(csv, index=False)

    rows = parse_pudo_wallet_csv(csv)
    assert len(rows) == 2
    by_month = {r["cost_month"]: r for r in rows}
    assert by_month["2025-11"]["amount_incl_vat"] == 50.0
    assert by_month["2025-11"]["line_count"] == 1
    assert by_month["2025-12"]["amount_incl_vat"] == 30.0
    assert by_month["2025-12"]["line_count"] == 2
```

- [ ] **Step 7: Run all parser tests**

```bash
python -m pytest _scripts/tests/test_pudo_wallet.py -v
```
Expected: 2 PASSED.

- [ ] **Step 8: Commit**

```bash
git add "_scripts/parsers/pudo_wallet.py" "_scripts/tests/test_pudo_wallet.py"
git commit -m "feat(logistics): Pudo wallet CSV parser with multi-month split"
```

---

## Task 4: Ingest CLI — folder scan, upsert, file move

**Files:**
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/ingest_logistics_invoices.py`
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/test_ingest.py`

- [ ] **Step 1: Write the failing end-to-end test**

File: `_scripts/tests/test_ingest.py`

```python
import shutil
from pathlib import Path

import pandas as pd

from _scripts.ingest_logistics_invoices import run_ingest

FIXTURES = Path(__file__).parent / "fixtures"


def _setup_inbox(tmp_path: Path) -> Path:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    shutil.copy(FIXTURES / "sample_rmz.pdf", inbox / "INV-001385.pdf")
    shutil.copy(FIXTURES / "sample_wallet.csv", inbox / "Wallet+transactions+report.csv")
    return inbox


def test_run_ingest_creates_parquet_and_moves_files(tmp_path):
    inbox = _setup_inbox(tmp_path)
    parquet = inbox / "ecommerce_logistics_cost.parquet"

    result = run_ingest(inbox)

    assert result["files_processed"] == 2
    assert result["rows_upserted"] == 2  # 1 RMZ + 1 wallet (single month)
    assert parquet.exists()

    df = pd.read_parquet(parquet)
    assert set(df["invoice_id"]) == {"RMZ-INV-001385", "WALLET-2025-11"}
    assert set(df.columns) >= {
        "invoice_id", "source", "vendor", "invoice_no", "invoice_date",
        "cost_month", "amount_incl_vat", "line_count", "source_file", "ingested_at",
    }

    # Files moved out of inbox
    assert not (inbox / "INV-001385.pdf").exists()
    assert not (inbox / "Wallet+transactions+report.csv").exists()
    assert (inbox / "_processed" / "RMZ" / "INV-001385.pdf").exists()
    assert (inbox / "_processed" / "Pudo Wallet" / "Wallet+transactions+report.csv").exists()


def test_run_ingest_is_idempotent_on_empty_inbox(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    result = run_ingest(inbox)
    assert result["files_processed"] == 0
    assert result["rows_upserted"] == 0


def test_run_ingest_upserts_on_reingest(tmp_path):
    inbox = _setup_inbox(tmp_path)
    run_ingest(inbox)
    # Drop the same PDF back into the inbox (e.g. user re-downloaded it)
    shutil.copy(FIXTURES / "sample_rmz.pdf", inbox / "INV-001385.pdf")
    result = run_ingest(inbox)
    assert result["files_processed"] == 1
    assert result["rows_upserted"] == 1
    df = pd.read_parquet(inbox / "ecommerce_logistics_cost.parquet")
    # Still only 2 rows total — RMZ row was overwritten, not appended
    assert len(df) == 2
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest _scripts/tests/test_ingest.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named '_scripts.ingest_logistics_invoices'`.

- [ ] **Step 3: Implement the ingest CLI**

File: `_scripts/ingest_logistics_invoices.py`

```python
"""ingest_logistics_invoices.py — Olympic Paints

Drop-folder ingest for e-commerce courier invoices.

Scans the inbox folder for *.pdf and *.csv files, dispatches each to the
matching parser, upserts canonical rows into ecommerce_logistics_cost.parquet
(keyed by invoice_id), then moves the source file to _processed/<source>/.

Usage:
    python -m _scripts.ingest_logistics_invoices [--inbox PATH] [--reingest]

If --reingest is passed, _processed/ files are moved back into the inbox
before scanning (full rebuild of the parquet).
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from _scripts.parsers.rmz_pdf import RmzPdfParseError, parse_rmz_pdf
from _scripts.parsers.pudo_wallet import PudoWalletParseError, parse_pudo_wallet_csv

DEFAULT_INBOX = Path(
    r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
    r"\2.Areas\1. Sales\5.Eccomerce\Delivery Invoices"
)
PARQUET_NAME = "ecommerce_logistics_cost.parquet"

SCHEMA_COLUMNS = [
    "invoice_id", "source", "vendor", "invoice_no", "invoice_date",
    "cost_month", "amount_incl_vat", "line_count", "source_file", "ingested_at",
]


def _classify(path: Path) -> str | None:
    name = path.name.lower()
    if path.suffix.lower() == ".pdf" and name.startswith("inv-"):
        return "RMZ"
    if path.suffix.lower() == ".csv" and name.startswith("wallet+transactions"):
        return "Pudo Wallet"
    return None


def _parse(path: Path, kind: str) -> list[dict]:
    if kind == "RMZ":
        return [parse_rmz_pdf(path)]
    if kind == "Pudo Wallet":
        return parse_pudo_wallet_csv(path)
    raise ValueError(f"Unknown source kind: {kind}")


def _upsert(parquet_path: Path, new_rows: list[dict]) -> int:
    now = datetime.now()
    for r in new_rows:
        r["ingested_at"] = now

    new_df = pd.DataFrame(new_rows, columns=SCHEMA_COLUMNS)
    new_df["invoice_date"] = pd.to_datetime(new_df["invoice_date"])

    if parquet_path.exists():
        existing = pd.read_parquet(parquet_path)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["invoice_id"], keep="last")
    else:
        combined = new_df

    combined = combined.sort_values(["cost_month", "source", "invoice_id"]).reset_index(drop=True)

    tmp = parquet_path.with_suffix(parquet_path.suffix + ".tmp")
    combined.to_parquet(tmp, index=False)
    os.replace(tmp, parquet_path)
    return len(new_rows)


def _move_to_processed(path: Path, inbox: Path, kind: str) -> None:
    dest_dir = inbox / "_processed" / kind
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    if dest.exists():
        dest.unlink()
    path.rename(dest)


def _restore_processed(inbox: Path) -> int:
    processed = inbox / "_processed"
    if not processed.exists():
        return 0
    moved = 0
    for src in processed.rglob("*"):
        if src.is_file():
            (inbox / src.name).write_bytes(src.read_bytes())
            src.unlink()
            moved += 1
    return moved


def run_ingest(inbox: Path, *, reingest: bool = False) -> dict:
    inbox = Path(inbox)
    parquet_path = inbox / PARQUET_NAME

    if reingest:
        _restore_processed(inbox)
        if parquet_path.exists():
            parquet_path.unlink()

    files_processed = 0
    rows_upserted = 0
    errors: list[tuple[str, str]] = []

    candidates = [p for p in inbox.iterdir() if p.is_file()]
    for path in sorted(candidates):
        kind = _classify(path)
        if kind is None:
            continue
        try:
            rows = _parse(path, kind)
        except (RmzPdfParseError, PudoWalletParseError) as e:
            errors.append((path.name, str(e)))
            continue
        rows_upserted += _upsert(parquet_path, rows)
        _move_to_processed(path, inbox, kind)
        files_processed += 1

    return {
        "files_processed": files_processed,
        "rows_upserted": rows_upserted,
        "errors": errors,
        "parquet": str(parquet_path),
    }


def _print_summary(result: dict) -> None:
    print(f"Files processed: {result['files_processed']}")
    print(f"Rows upserted:   {result['rows_upserted']}")
    print(f"Parquet:         {result['parquet']}")
    if result["errors"]:
        print("Errors:")
        for name, msg in result["errors"]:
            print(f"  - {name}: {msg}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest e-commerce courier invoices into parquet")
    ap.add_argument("--inbox", type=Path, default=DEFAULT_INBOX, help="Folder to scan")
    ap.add_argument("--reingest", action="store_true", help="Move _processed/ files back and rebuild parquet")
    args = ap.parse_args()

    result = run_ingest(args.inbox, reingest=args.reingest)
    _print_summary(result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the ingest tests**

```bash
python -m pytest _scripts/tests/test_ingest.py -v
```
Expected: 3 PASSED.

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest _scripts/tests/ -v
```
Expected: 6 PASSED total (2 RMZ + 2 Pudo + 3 ingest — Pudo has 2 tests, that's 2+2+3=7... recount your own pass/fail; any failures, stop and debug).

- [ ] **Step 6: Run the ingest against the real inbox (live smoke test)**

From `Delivery Invoices/`:

```bash
python -m _scripts.ingest_logistics_invoices
```

Expected output:
```
Files processed: 13
Rows upserted:   13   (could be 12 if the two wallet CSVs cover the same month)
Parquet:         .../ecommerce_logistics_cost.parquet
```

- [ ] **Step 7: Verify the parquet manually**

```bash
python -c "import pandas as pd; df = pd.read_parquet('ecommerce_logistics_cost.parquet'); print(df.to_string())"
```

Expected: a table with `invoice_id`, `cost_month`, `amount_incl_vat`, etc. All RMZ rows from the 11 PDFs + 1-2 wallet rows.

- [ ] **Step 8: Run ingest again — should be a no-op**

```bash
python -m _scripts.ingest_logistics_invoices
```

Expected:
```
Files processed: 0
Rows upserted:   0
```

- [ ] **Step 9: Commit**

```bash
git add "_scripts/ingest_logistics_invoices.py" "_scripts/tests/test_ingest.py" "ecommerce_logistics_cost.parquet" "_processed/"
git commit -m "feat(logistics): ingest CLI with idempotent parquet upsert"
```

---

## Task 5: Monthly cost-ratio report CLI

**Files:**
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/logistics_cost_monthly.py`
- Create: `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/tests/test_monthly_report.py`

- [ ] **Step 1: Write the failing test**

File: `_scripts/tests/test_monthly_report.py`

```python
from datetime import datetime
from pathlib import Path

import pandas as pd

from _scripts.logistics_cost_monthly import build_monthly_report, render_markdown


def _make_logistics_parquet(path: Path) -> None:
    pd.DataFrame([
        {"invoice_id": "RMZ-INV-001", "source": "RMZ", "vendor": "RMZ", "invoice_no": "INV-001",
         "invoice_date": datetime(2025, 11, 15), "cost_month": "2025-11",
         "amount_incl_vat": 1000.0, "line_count": 5, "source_file": "a.pdf",
         "ingested_at": datetime(2026, 5, 21)},
        {"invoice_id": "WALLET-2025-11", "source": "Pudo Wallet", "vendor": "Pudo Wallet", "invoice_no": "",
         "invoice_date": datetime(2025, 11, 30), "cost_month": "2025-11",
         "amount_incl_vat": 500.0, "line_count": 10, "source_file": "w.csv",
         "ingested_at": datetime(2026, 5, 21)},
        {"invoice_id": "RMZ-INV-002", "source": "RMZ", "vendor": "RMZ", "invoice_no": "INV-002",
         "invoice_date": datetime(2025, 12, 10), "cost_month": "2025-12",
         "amount_incl_vat": 2000.0, "line_count": 8, "source_file": "b.pdf",
         "ingested_at": datetime(2026, 5, 21)},
    ]).to_parquet(path, index=False)


def _make_woocommerce_csv(path: Path) -> None:
    # Two orders in 2025-11 (one with two line items so total repeats), one in 2025-12
    pd.DataFrame([
        {"order_id": 1, "date_paid": "2025-11-05 10:00:00", "total": 10000.0, "line_item_index": 0},
        {"order_id": 1, "date_paid": "2025-11-05 10:00:00", "total": 10000.0, "line_item_index": 1},
        {"order_id": 2, "date_paid": "2025-11-20 14:00:00", "total": 5000.0, "line_item_index": 0},
        {"order_id": 3, "date_paid": "2025-12-01 09:00:00", "total": 20000.0, "line_item_index": 0},
    ]).to_csv(path, index=False)


def test_build_monthly_report_aggregates_by_month(tmp_path):
    parquet = tmp_path / "logi.parquet"
    csv = tmp_path / "wc.csv"
    _make_logistics_parquet(parquet)
    _make_woocommerce_csv(csv)

    df = build_monthly_report(parquet, csv)

    # Sort by month ascending so we can assert by position
    df = df.sort_values("cost_month").reset_index(drop=True)
    assert list(df["cost_month"]) == ["2025-11", "2025-12"]
    assert df.loc[0, "revenue_incl_vat"] == 15000.0  # 10000 (deduped order_id 1) + 5000
    assert df.loc[0, "logistics_incl_vat"] == 1500.0  # 1000 + 500
    assert round(df.loc[0, "logistics_pct"], 2) == 10.00
    assert df.loc[1, "revenue_incl_vat"] == 20000.0
    assert df.loc[1, "logistics_incl_vat"] == 2000.0
    assert round(df.loc[1, "logistics_pct"], 2) == 10.00


def test_render_markdown_produces_table(tmp_path):
    parquet = tmp_path / "logi.parquet"
    csv = tmp_path / "wc.csv"
    _make_logistics_parquet(parquet)
    _make_woocommerce_csv(csv)
    df = build_monthly_report(parquet, csv)
    md = render_markdown(df)
    assert "| Month" in md
    assert "2025-11" in md
    assert "10.00%" in md
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
python -m pytest _scripts/tests/test_monthly_report.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named '_scripts.logistics_cost_monthly'`.

- [ ] **Step 3: Implement the report**

File: `_scripts/logistics_cost_monthly.py`

```python
"""logistics_cost_monthly.py — Olympic Paints

Joins ecommerce_logistics_cost.parquet with the WooCommerce orders CSV
(one row per line item; order totals repeat) and prints a monthly markdown
table of logistics cost as a % of revenue (incl-VAT basis).

Usage:
    python -m _scripts.logistics_cost_monthly [--parquet PATH] [--wc-csv PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

DEFAULT_PARQUET = Path(
    r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
    r"\2.Areas\1. Sales\5.Eccomerce\Delivery Invoices\ecommerce_logistics_cost.parquet"
)
DEFAULT_WC_CSV = Path(
    r"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints"
    r"\3.Resources\16.Sales and Other data\Manual\Woocommerce_Transactions.csv"
)


def _wc_revenue_by_month(wc_csv: Path) -> pd.DataFrame:
    """Sum WooCommerce order totals by month (deduping repeated order rows)."""
    df = pd.read_csv(wc_csv)
    # date_paid is the right field (fall back to date_created if missing)
    if "date_paid" in df.columns and df["date_paid"].notna().any():
        df["order_dt"] = pd.to_datetime(df["date_paid"], errors="coerce")
    else:
        df["order_dt"] = pd.to_datetime(df["date_created"], errors="coerce")

    # The CSV repeats `total` once per line item; collapse to one row per order
    orders = df.dropna(subset=["order_dt"]).drop_duplicates(subset=["order_id"])
    orders = orders.assign(cost_month=orders["order_dt"].dt.strftime("%Y-%m"))
    return (
        orders.groupby("cost_month", as_index=False)["total"]
        .sum()
        .rename(columns={"total": "revenue_incl_vat"})
    )


def _logistics_by_month(parquet: Path) -> pd.DataFrame:
    df = pd.read_parquet(parquet)
    return (
        df.groupby("cost_month", as_index=False)["amount_incl_vat"]
        .sum()
        .rename(columns={"amount_incl_vat": "logistics_incl_vat"})
    )


def build_monthly_report(parquet: Path, wc_csv: Path) -> pd.DataFrame:
    rev = _wc_revenue_by_month(wc_csv)
    cost = _logistics_by_month(parquet)
    out = rev.merge(cost, on="cost_month", how="outer").fillna(0.0)
    out["logistics_pct"] = out.apply(
        lambda r: (r["logistics_incl_vat"] / r["revenue_incl_vat"] * 100.0)
        if r["revenue_incl_vat"] > 0 else 0.0,
        axis=1,
    )
    return out.sort_values("cost_month").reset_index(drop=True)


def render_markdown(df: pd.DataFrame) -> str:
    lines = [
        "| Month   | E-comm revenue (incl VAT) | Logistics cost (incl VAT) | Logistics % |",
        "|---------|---------------------------|---------------------------|-------------|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['cost_month']} "
            f"| R {r['revenue_incl_vat']:>14,.2f} "
            f"| R {r['logistics_incl_vat']:>14,.2f} "
            f"| {r['logistics_pct']:>6.2f}% |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Monthly logistics-cost ratio report")
    ap.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    ap.add_argument("--wc-csv", type=Path, default=DEFAULT_WC_CSV)
    args = ap.parse_args()

    if not args.parquet.exists():
        print(f"ERROR: parquet not found: {args.parquet}", file=sys.stderr)
        return 2
    if not args.wc_csv.exists():
        print(f"ERROR: WooCommerce CSV not found: {args.wc_csv}", file=sys.stderr)
        return 2

    df = build_monthly_report(args.parquet, args.wc_csv)
    print(render_markdown(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
python -m pytest _scripts/tests/test_monthly_report.py -v
```
Expected: 2 PASSED.

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest _scripts/tests/ -v
```
Expected: all tests pass (9 total: 2 RMZ + 2 Pudo + 3 ingest + 2 report).

- [ ] **Step 6: Run the report against real data**

From `Delivery Invoices/`:

```bash
python -m _scripts.logistics_cost_monthly
```

Expected: a markdown table with one row per month covered by the courier invoices, showing revenue / cost / %. Manually sanity-check: the ratios should be in single-digit to low-double-digit percentages (couriers are typically 5–15% of e-comm GMV).

- [ ] **Step 7: Commit**

```bash
git add "_scripts/logistics_cost_monthly.py" "_scripts/tests/test_monthly_report.py"
git commit -m "feat(logistics): monthly cost-ratio report CLI"
```

---

## Task 6: Document in CLAUDE.md and add a memory pointer

**Files:**
- Modify: `c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\CLAUDE.md` (add a row to the Quick Links table)
- Create: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\reference_ecommerce_logistics_cost.md`
- Modify: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\MEMORY.md` (add pointer under "E-Commerce Dashboard")

- [ ] **Step 1: Add a Quick Links row to CLAUDE.md**

Read the current Quick Links table in `CLAUDE.md` and add this row after the existing e-commerce entries:

```markdown
| Run logistics-cost ingest / report? | 2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/ | `python -m _scripts.ingest_logistics_invoices` to ingest, `python -m _scripts.logistics_cost_monthly` for the monthly markdown table |
```

- [ ] **Step 2: Write the memory file**

File: `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\reference_ecommerce_logistics_cost.md`

```markdown
---
name: ecommerce-logistics-cost
description: Parquet + CLI that ingests RMZ Freight PDFs and Pudo wallet CSVs from the e-comm Delivery Invoices folder and produces a monthly logistics-cost-% report
metadata:
  type: reference
---

E-commerce courier invoices are ingested from `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/` into `ecommerce_logistics_cost.parquet` (one row per invoice or per wallet-CSV-month). Two scripts under `_scripts/`:

- `python -m _scripts.ingest_logistics_invoices` — drop-folder ingest. Idempotent. Moves consumed files to `_processed/<source>/`. `--reingest` to rebuild from scratch.
- `python -m _scripts.logistics_cost_monthly` — prints a markdown table of logistics cost as % of WooCommerce revenue, monthly, incl-VAT both sides.

WooCommerce revenue source: `3.Resources/16.Sales and Other data/Manual/Woocommerce_Transactions.csv` (the same file `build_ecommerce_dashboard.py` consumes; CSV is one row per line item, `total` repeats — script dedupes by `order_id`).

Parsers live in `_scripts/parsers/`: `rmz_pdf.py` and `pudo_wallet.py`. To add a new courier vendor, add a parser + a `_classify()` branch in `ingest_logistics_invoices.py`.

Design spec: `docs/superpowers/specs/2026-05-21-ecommerce-logistics-cost-parquet-design.md`. Related: [[ecommerce-dashboard]], [[ecommerce-woocommerce-fetch]].
```

- [ ] **Step 3: Add the pointer line to MEMORY.md**

Open `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\MEMORY.md` and find the `## E-Commerce Dashboard` section. Add this line as a new bullet (keep one-line format):

```markdown
- [E-Commerce Logistics Cost Parquet — ingest + monthly report](reference_ecommerce_logistics_cost.md) — RMZ PDFs + Pudo wallet CSVs from `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/`; `python -m _scripts.ingest_logistics_invoices` + `python -m _scripts.logistics_cost_monthly`
```

- [ ] **Step 4: Commit the CLAUDE.md change**

```bash
cd "c:/Users/quint/OneDrive/1.Projects/1.Olympic Paints"
git add CLAUDE.md
git commit -m "docs(claude.md): add logistics-cost ingest/report to Quick Links"
```

(Memory files are outside the repo and don't need a git commit.)

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by |
|---|---|
| Parquet schema (10 columns) | Task 2 + Task 3 (parsers emit the schema), Task 4 (`SCHEMA_COLUMNS`) |
| RMZ PDF parser | Task 2 |
| Pudo wallet CSV parser, multi-month split | Task 3 (step 6) |
| Ingest flow (scan → detect → parse → upsert → move) | Task 4 |
| Idempotency by `invoice_id` | Task 4 (test_run_ingest_upserts_on_reingest) |
| `_processed/` move | Task 4 |
| `--reingest` flag | Task 4 (`_restore_processed`) |
| Monthly markdown report | Task 5 |
| Incl-VAT ÷ incl-VAT ratio | Task 5 (no VAT stripping anywhere) |
| File layout exactly as spec | Task 1 |
| Risk: fail loudly on layout change | Task 2 (`RmzPdfParseError`), Task 3 (`PudoWalletParseError`) |
| Success criteria #1 (all 13 files ingest cleanly) | Task 4 step 6 |
| Success criteria #4 (re-run is a no-op) | Task 4 step 8 + test_run_ingest_is_idempotent_on_empty_inbox |

All spec sections mapped. No gaps.

**Placeholder scan:** No TBDs, no "add appropriate error handling", every code step has full code. ✓

**Type consistency:** `parse_rmz_pdf` returns `dict`, `parse_pudo_wallet_csv` returns `list[dict]` — the dispatcher in Task 4 wraps the RMZ result in a list before iterating. `SCHEMA_COLUMNS` is the single source of truth, used by ingest and matches what both parsers emit. `cost_month` is consistently `"YYYY-MM"` string everywhere. ✓

**Test count sanity:** Task 4 step 5 said "6 PASSED total" then "Pudo has 2 tests, that's 2+2+3=7" — fix: it's 2 RMZ + 2 Pudo + 3 ingest = **7 tests**. After Task 5 adds 2 report tests, total = **9 tests**. Updated step 5 in Task 5 to match.

---

## Execution Handoff

**Plan complete and saved to** `docs/superpowers/plans/2026-05-21-ecommerce-logistics-cost-parquet.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Each task is self-contained so this works cleanly here.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch with checkpoints.

Which approach?
