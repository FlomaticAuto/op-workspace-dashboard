# Competitor Product Verification JotForms — Implementation Plan

> **SUPERSEDED 2026-05-16** — Mid-build we switched from JotForm to self-hosted Supabase forms on `olympic-paints-forms-admin`. Tasks 1 (categoriser) and 2 (extractor) here were completed and remain in use; tasks 3–11 (JotForm MCP build, JotForm-URL dispatcher, JotForm-only memory) are replaced by the Supabase plan: `docs/superpowers/plans/2026-05-16-competitor-verification-supabase.md`. Do not execute tasks below T2.


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up 15 category-filtered JotForms (5 competitors × 3 categories) so reps can confirm or correct every Olympic ↔ competitor product matchup, and dispatch them on a 3-day email cadence.

**Architecture:** Two Python scripts produce JSON data (Olympic SKUs by category, competitor matchups by category). Agent then iteratively calls the JotForm MCP to create each of the 15 forms from those JSONs. A third Python script generates the daily HTML emails (5 form links per rep) and dispatches via win32com Outlook with force-flush. Submissions land in JotForm's native storage; aggregation is out of scope for v1.

**Tech Stack:** Python 3 · openpyxl · pandas (optional) · win32com.client · JotForm MCP server · Outlook (local)

**Repo note:** Not a git repo. Replace every "commit" instruction with "save file + log line to changelog at `jotform_verification/CHANGELOG.md`".

---

## File structure

All new files under `2.Areas/1. Sales/7. Competitor information/jotform_verification/`:

```
jotform_verification/
├── categorise_skus.py              # T1 — reads pricelist, writes 3 JSONs
├── extract_matchups.py             # T2 — reads 5 competitor workbooks, writes 15 JSONs
├── send_verification_emails.py     # T7 — Day 1/2/3 dispatcher
├── CHANGELOG.md                    # running log of what was built when
├── config/
│   ├── category_mapping.json       # locked bucketing from spec §4
│   └── rep_emails.json             # rep_code → email map
├── output/
│   ├── olympic_skus_enamel.json
│   ├── olympic_skus_pva.json
│   ├── olympic_skus_waterproofing.json
│   ├── competitor_matchups_<brand>_<category>.json   # 15 files
│   ├── jotform_urls.json           # live URL map — written by T4–T5, read by T7
│   └── dispatch_log.json           # per-day send results
└── templates/
    └── daily_email.html            # navy executive theme, {{links}} placeholder
```

---

## Pre-flight constants (referenced throughout plan)

```python
# Paths — used by every script
from pathlib import Path

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
PRICELIST = REPO_ROOT / "2.Areas" / "1. Sales" / "1. Pricing" / "List Price 2026 15 % Increase.xlsx"
COMPETITOR_DIR = REPO_ROOT / "3.Resources" / "17. Strategic Intelligence"
JF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "jotform_verification"
OUTPUT_DIR = JF_DIR / "output"
CONFIG_DIR = JF_DIR / "config"
TEMPLATES_DIR = JF_DIR / "templates"

COMPETITORS = [
    ("africa_paints",  "Africa Paints",  "Olympic_vs_Africa_Paints_Competitor_Analysis.xlsx"),
    ("anetic",         "Anetic",         "Olympic_vs_Anetic_Competitor_Analysis.xlsx"),
    ("crest",          "Crest",          "Olympic_vs_Crest_Competitor_Analysis.xlsx"),
    ("excelsior",      "Excelsior",      "Olympic_vs_Excelsior_Competitor_Analysis.xlsx"),
    ("golden_choice",  "Golden Choice",  "Olympic_vs_Golden_Choice_Competitor_Analysis.xlsx"),
]
CATEGORIES = ["enamel", "pva", "waterproofing"]
```

---

## Task 1: SKU categoriser

**Files:**
- Create: `jotform_verification/config/category_mapping.json`
- Create: `jotform_verification/categorise_skus.py`
- Create: `jotform_verification/output/olympic_skus_{enamel,pva,waterproofing}.json`

- [ ] **Step 1.1: Write the category mapping config**

Save this exactly as `config/category_mapping.json`:

```json
{
  "enamel": [
    "High Gloss", "Q.D. Enamel", "Ultimate Shine", "Pick & Save",
    "Q.D. Primer", "Eggshell Enamel", "Universal Undercoat",
    "Zinc Phosphate", "Wood Primer", "Wood Varnish",
    "Etch Primer", "Sanding Sealer", "Primer", "Aerosol"
  ],
  "pva": [
    "Rugged Beauty", "Master Decorators", "Kalahari Contractors",
    "Decor", "Suburban Bliss", "Natural Elegance", "Eclipse Pva",
    "7 in 1 PVA", "Distemper", "All In One", "Plush Coat",
    "Schoolboard", "Hi Hiding Contr", "Plaster Primer", "Just Paint",
    "LIBERTY", "Madalas Choice", "Best Build"
  ],
  "waterproofing": [
    "Universal Roof Paint", "RainProof", "Roof & Stoep", "3 in 1 Roof",
    "Fibre Restore", "Membrane", "3 in 1 Gripcoat ", "Crack Filler",
    "Putty", "Plaster n Tile Bond", "Stainer", "Oxide", "Road Marking",
    "Thinner", "Turpentine", "Carbolineum", "Linseed Oil", "Paint Remover",
    "Galvanized Cleaner", "Rust Remover", "Bonding Liquid", "FB Dressing",
    "Accessories", "Spirit of Salt", "20L Face Brick Dressing"
  ],
  "_excluded": ["Commision", "DELIVERY"]
}
```

Note the trailing space on `"3 in 1 Gripcoat "` and the spelling `"Commision"` — these match the pricelist exactly. Do not "fix" them.

- [ ] **Step 1.2: Write `categorise_skus.py`**

```python
"""Read Olympic master pricelist, bucket SKUs into 3 category JSONs."""
import json
from pathlib import Path
import openpyxl

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
PRICELIST = REPO_ROOT / "2.Areas" / "1. Sales" / "1. Pricing" / "List Price 2026 15 % Increase.xlsx"
JF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "jotform_verification"
CONFIG = JF_DIR / "config" / "category_mapping.json"
OUTPUT_DIR = JF_DIR / "output"

def main():
    mapping = json.loads(CONFIG.read_text(encoding="utf-8"))
    group_to_cat = {}
    for cat, groups in mapping.items():
        if cat.startswith("_"):
            continue
        for g in groups:
            group_to_cat[g] = cat

    wb = openpyxl.load_workbook(PRICELIST, data_only=True, read_only=True)
    ws = wb["sheet1"]

    buckets = {"enamel": [], "pva": [], "waterproofing": []}
    unmapped = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        code, name, group, price = row[0], row[1], row[2], row[3]
        if not code or not group:
            continue
        if group in mapping.get("_excluded", []):
            continue
        cat = group_to_cat.get(group)
        if cat is None:
            unmapped.append((code, name, group))
            continue
        buckets[cat].append({
            "code": str(code),
            "name": str(name),
            "group": str(group),
            "list_price": float(price) if price is not None else None,
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for cat, rows in buckets.items():
        path = OUTPUT_DIR / f"olympic_skus_{cat}.json"
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"  {cat:14s} {len(rows):4d} SKUs -> {path.name}")

    if unmapped:
        print(f"\nUNMAPPED groups ({len(unmapped)}):")
        for code, name, group in unmapped[:20]:
            print(f"  {code} | {group} | {name}")
        raise SystemExit("Fix category_mapping.json so every group is mapped or excluded.")

    print("\nOK — every SKU classified.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 1.3: Run the categoriser**

```bash
cd "c:/Users/quint/OneDrive/1.Projects/1.Olympic Paints/2.Areas/1. Sales/7. Competitor information/jotform_verification"
python categorise_skus.py
```

Expected output:
```
  enamel         ~272 SKUs -> olympic_skus_enamel.json
  pva            ~286 SKUs -> olympic_skus_pva.json
  waterproofing  ~175 SKUs -> olympic_skus_waterproofing.json

OK — every SKU classified.
```

If the script raises `SystemExit` with unmapped groups, add them to the correct bucket in `category_mapping.json` and re-run. Do NOT proceed until all 733 productive SKUs are bucketed.

- [ ] **Step 1.4: Spot-check the buckets**

Open `output/olympic_skus_enamel.json` and confirm:
- `Pick & Save` 20L white appears (memory `feedback_pick_n_save_enamel_match` — this is the load-bearing fix)
- No PVA brand names (no Decor, no Rugged Beauty)

Open `output/olympic_skus_pva.json` and confirm:
- `7 in 1 PVA` and `Decor` present
- No enamel brand names (no QD Enamel, no High Gloss)

- [ ] **Step 1.5: Log to changelog**

Append to `CHANGELOG.md`:
```
2026-05-16  T1 done — SKU categoriser built; 3 JSONs written, all 733 productive SKUs bucketed.
```

---

## Task 2: Competitor matchup extractor

**Files:**
- Create: `jotform_verification/extract_matchups.py`
- Create: `jotform_verification/output/competitor_matchups_<brand>_<category>.json` (15 files)

- [ ] **Step 2.1: Audit workbook layouts**

Before writing the extractor, open each of the 5 workbooks and confirm the Overview Matrix sheet's column layout. Per spec §9 A1, Stevensons is the canonical format but Stevensons doesn't have a workbook — Africa Paints / Anetic / Crest / Excelsior / Golden Choice may diverge.

Run this audit script in a Python REPL or as a throwaway script:

```python
import openpyxl
from pathlib import Path

COMPETITOR_DIR = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\3.Resources\17. Strategic Intelligence")
files = [
    "Olympic_vs_Africa_Paints_Competitor_Analysis.xlsx",
    "Olympic_vs_Anetic_Competitor_Analysis.xlsx",
    "Olympic_vs_Crest_Competitor_Analysis.xlsx",
    "Olympic_vs_Excelsior_Competitor_Analysis.xlsx",
    "Olympic_vs_Golden_Choice_Competitor_Analysis.xlsx",
]
for f in files:
    print(f"\n=== {f} ===")
    wb = openpyxl.load_workbook(COMPETITOR_DIR / f, data_only=True, read_only=True)
    print(f"sheets: {wb.sheetnames}")
    for sn in wb.sheetnames:
        ws = wb[sn]
        print(f"  [{sn}] dims {ws.max_row}r x {ws.max_column}c")
        for i, row in enumerate(ws.iter_rows(values_only=True, max_row=3)):
            print(f"    row{i}: {row[:12]}")
```

Record (in CHANGELOG.md or a scratch note) the actual sheet name + column positions for: competitor product name · pack size · competitor price · current Olympic match code · current Olympic match name. The extractor in 2.2 uses these positions.

- [ ] **Step 2.2: Write `extract_matchups.py`**

Adjust `OVERVIEW_SHEET_NAME` and column indices based on what Step 2.1 found. The skeleton assumes Stevensons-style stacked rows (one competitor row + one Olympic row per matchup). If layouts differ per workbook, add per-brand handlers.

```python
"""Extract competitor product matchups from 5 workbooks, bucket by category, write 15 JSONs."""
import json
from pathlib import Path
import openpyxl

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
COMPETITOR_DIR = REPO_ROOT / "3.Resources" / "17. Strategic Intelligence"
JF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "jotform_verification"
OUTPUT_DIR = JF_DIR / "output"

COMPETITORS = [
    ("africa_paints",  "Africa Paints",  "Olympic_vs_Africa_Paints_Competitor_Analysis.xlsx"),
    ("anetic",         "Anetic",         "Olympic_vs_Anetic_Competitor_Analysis.xlsx"),
    ("crest",          "Crest",          "Olympic_vs_Crest_Competitor_Analysis.xlsx"),
    ("excelsior",      "Excelsior",      "Olympic_vs_Excelsior_Competitor_Analysis.xlsx"),
    ("golden_choice",  "Golden Choice",  "Olympic_vs_Golden_Choice_Competitor_Analysis.xlsx"),
]

# Adjust per Step 2.1 findings
OVERVIEW_SHEET_NAME = "Overview Matrix"
COL = {
    "competitor_name":  2,   # B  — competitor product name
    "competitor_pack":  3,   # C  — pack size
    "competitor_price": 9,   # I or J (yellow) — verify in 2.1
    "olympic_code":     5,   # E
    "olympic_name":     6,   # F
    "olympic_group":    7,   # G  — Olympic product group, used for category classification
}

def load_group_to_category():
    mapping = json.loads((JF_DIR / "config" / "category_mapping.json").read_text())
    g2c = {}
    for cat, groups in mapping.items():
        if cat.startswith("_"):
            continue
        for g in groups:
            g2c[g] = cat
    return g2c

def main():
    g2c = load_group_to_category()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for slug, label, fname in COMPETITORS:
        path = COMPETITOR_DIR / fname
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        if OVERVIEW_SHEET_NAME not in wb.sheetnames:
            print(f"!! {label}: no '{OVERVIEW_SHEET_NAME}' sheet — sheets are {wb.sheetnames}")
            continue
        ws = wb[OVERVIEW_SHEET_NAME]

        buckets = {"enamel": [], "pva": [], "waterproofing": []}
        for row in ws.iter_rows(min_row=2, values_only=True):
            comp_name = row[COL["competitor_name"] - 1]
            if not comp_name or str(comp_name).strip().startswith("#"):
                continue
            olympic_group = row[COL["olympic_group"] - 1]
            cat = g2c.get(str(olympic_group).strip()) if olympic_group else None
            if cat is None:
                continue  # skip header/section rows
            buckets[cat].append({
                "competitor_product": str(comp_name).strip(),
                "pack_size": str(row[COL["competitor_pack"] - 1] or "").strip(),
                "competitor_price": str(row[COL["competitor_price"] - 1] or "").strip(),
                "current_olympic_match_code":  str(row[COL["olympic_code"] - 1] or "").strip(),
                "current_olympic_match_name":  str(row[COL["olympic_name"] - 1] or "").strip(),
                "current_olympic_match_group": str(olympic_group).strip(),
            })

        for cat, rows in buckets.items():
            out = OUTPUT_DIR / f"competitor_matchups_{slug}_{cat}.json"
            out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(f"  {label:15s} {cat:14s} {len(rows):3d} rows -> {out.name}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2.3: Run the extractor**

```bash
python extract_matchups.py
```

Expected: 15 JSON files written. Each should have between 3 and ~30 rows. If any file has 0 rows, the column indices in `COL` are wrong for that brand — revisit Step 2.1 audit output and add a per-brand override.

- [ ] **Step 2.4: Spot-check Golden Choice (the freshest workbook per memory)**

Open `output/competitor_matchups_golden_choice_enamel.json`. Per memory:
- `Pick & Save` should appear as a `current_olympic_match_group` (NOT High Gloss)
- 24 total Golden Choice matchups across the 3 files

If counts are off, the extractor missed rows — debug before continuing.

- [ ] **Step 2.5: Log to changelog**

```
2026-05-16  T2 done — extracted 15 competitor matchup JSONs from 5 workbooks. Counts logged in dispatch_log.json placeholder.
```

---

## Task 3: JotForm MCP spike (Africa Paints — Enamel)

Validate the JotForm MCP can build the form structure before committing to 15. Africa Paints Enamel is the smallest expected matchup set, so it's the safe pilot.

- [ ] **Step 3.1: Read the smallest JSON to know what fields are needed**

Read `output/competitor_matchups_africa_paints_enamel.json` and `output/olympic_skus_enamel.json`. Note the row counts.

- [ ] **Step 3.2: Build form structure plan**

The form needs (in order):
1. Title: `Olympic vs Africa Paints — Enamel Matchup Verification`
2. Intro HTML block: explanation text + deadline
3. Four hidden fields: `rep_email`, `rep_code`, `competitor`, `category` (so dispatcher can URL-prefill)
4. For each row in the matchup JSON, a labelled section containing:
   - Static HTML: `<strong>{competitor_product}</strong> · {pack_size} · {competitor_price}`
   - Dropdown labelled `Correct Olympic match` — populated with **all enamel SKUs** as `"{code} — {name} ({list_price})"`, default value = `current_olympic_match_code` formatted same way
   - Radio: `Confidence` with options `Strong match`, `Acceptable`, `Wrong — see notes`
   - Textbox: `Notes (optional)`
5. Submit button

- [ ] **Step 3.3: Call MCP `create_form`**

Invoke `mcp__claude_ai_Jotform__create_form` with the constructed form. Capture the returned form ID and URL.

- [ ] **Step 3.4: Open the form URL in a browser and verify**

Manual check:
- Dropdown contains only enamel SKUs (no PVAs, no waterproofing)
- Default selection matches the workbook's current Olympic match
- Confidence radio works
- Hidden fields are present (inspect URL with `?rep_email=test@test.com&rep_code=AC&competitor=africa_paints&category=enamel` and confirm prefill works)

If the dropdown population, defaults, or prefill don't work, debug with `mcp__claude_ai_Jotform__edit_form` and re-verify before moving to T4.

- [ ] **Step 3.5: Save the URL**

Write `output/jotform_urls.json`:

```json
{
  "africa_paints": {
    "enamel":        "https://form.jotform.com/<id>",
    "pva":           null,
    "waterproofing": null
  },
  "anetic":         { "enamel": null, "pva": null, "waterproofing": null },
  "crest":          { "enamel": null, "pva": null, "waterproofing": null },
  "excelsior":      { "enamel": null, "pva": null, "waterproofing": null },
  "golden_choice":  { "enamel": null, "pva": null, "waterproofing": null }
}
```

- [ ] **Step 3.6: Log to changelog**

```
2026-05-16  T3 done — JotForm MCP spike: Africa Paints Enamel form built and verified. URL captured.
```

---

## Task 4: Build remaining 14 forms

- [ ] **Step 4.1: Loop the 14 remaining (competitor, category) pairs**

Order: complete each competitor's 3 forms before moving to the next, so a half-built rollout still has internally consistent competitor sets.

For each `(slug, label, cat)` not already done:
1. Read `output/olympic_skus_{cat}.json` (dropdown options)
2. Read `output/competitor_matchups_{slug}_{cat}.json` (form rows)
3. Call `mcp__claude_ai_Jotform__create_form` with same structure as T3
4. Update `output/jotform_urls.json` with the new URL **immediately after each form is built** (do not batch — if a build fails mid-loop, you keep what's already done)

- [ ] **Step 4.2: Final URL map verification**

```bash
python -c "
import json
from pathlib import Path
urls = json.loads(Path(r'output/jotform_urls.json').read_text())
missing = [(c,k) for c, cats in urls.items() for k, v in cats.items() if not v]
print(f'Forms built: {15 - len(missing)} / 15')
if missing:
    for c, k in missing:
        print(f'  MISSING: {c} / {k}')
else:
    print('All 15 forms have URLs.')
"
```

Expected: `All 15 forms have URLs.` Do not proceed until this passes.

- [ ] **Step 4.3: Log to changelog**

```
2026-05-16  T4 done — all 15 JotForms built. URL map saved to output/jotform_urls.json.
```

---

## Task 5: Rep email config

**Files:**
- Create: `jotform_verification/config/rep_emails.json`

- [ ] **Step 5.1: Build the rep email map**

Confirm rep email addresses before writing the file. Source of truth = PULSE config (`1.Projects/PULSE — Sales & Ops Manager/.env` or its config json — per [[reference_pulse_system]]).

If PULSE config has them, copy verbatim. If not, populate from staff portal or ask Quintus.

```json
{
  "AC": { "name": "Aboo Cassim",     "email": "<from PULSE config>" },
  "AP": { "name": "Amit Patel",      "email": "<from PULSE config>" },
  "BV": { "name": "Bhadresh Vallabh","email": "<from PULSE config>" },
  "NP": { "name": "Nikhil Panchal",  "email": "<from PULSE config>" },
  "BM": { "name": "Byron Minnie",    "email": "<from PULSE config>" }
}
```

Do NOT invent email addresses. Leave a placeholder and abort the task if PULSE config doesn't have them — ask Quintus.

- [ ] **Step 5.2: Log to changelog**

```
2026-05-16  T5 done — rep_emails.json populated from PULSE config.
```

---

## Task 6: Email template

**Files:**
- Create: `jotform_verification/templates/daily_email.html`

- [ ] **Step 6.1: Write the navy executive HTML template**

Per [[feedback_email_report_workflow]] + [[reference_logo_hosted_url]]. Use the design system from `CLAUDE.md` (theme-navy, CSS tokens, Barlow fonts, hosted logo URL).

```html
<!DOCTYPE html>
<html lang="en" class="theme-navy">
<head>
<meta charset="UTF-8">
<title>{{day_label}} — Competitor Matchup Verification</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800;900&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* [Paste the full token block from CLAUDE.md §Theme system — navy theme only is needed inline for email] */
body { background:#0D2040; color:#FFFFFF; font-family:'Barlow',sans-serif; margin:0; padding:32px; }
.card { background:#1A3D6E; border-radius:12px; padding:24px; max-width:640px; margin:0 auto; }
h1 { font-family:'Barlow Condensed',sans-serif; font-weight:900; color:#F5C400; text-transform:uppercase; font-size:32px; margin:0 0 8px; }
.subtitle { color:#B8CCE8; font-size:14px; margin-bottom:24px; }
.link-row { display:block; padding:14px 18px; background:rgba(245,196,0,0.08); border-left:4px solid #F5C400; border-radius:8px; margin:8px 0; text-decoration:none; color:#FFFFFF; }
.link-row strong { font-family:'Barlow Condensed',sans-serif; font-weight:800; color:#F5C400; }
.footer { color:#6B9ED0; font-size:12px; margin-top:24px; text-align:center; }
.logo { width:48px;height:48px;border-radius:50%;overflow:hidden;display:inline-block;vertical-align:middle;margin-right:12px; }
</style>
</head>
<body>
  <div class="card">
    <div style="display:flex;align-items:center;margin-bottom:16px;">
      <div class="logo"><img src="https://flomaticauto.github.io/olympic-paints-clocking/logo.jpg" width="48" height="48" alt="Olympic Paints" style="display:block;width:100%;height:100%;object-fit:cover;"></div>
      <div>
        <h1>{{day_label}} Verification</h1>
        <div class="subtitle">{{date}} · {{rep_name}}</div>
      </div>
    </div>
    <p style="color:#E8EFF8;font-size:15px;line-height:1.5;">
      {{intro}}
    </p>
    {{links}}
    <div class="footer">
      Each form takes 5–10 minutes. If you can't reach the right answer for any line, mark it "Wrong — see notes" and leave the note blank. We'll triage.
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 6.2: Log to changelog**

```
2026-05-16  T6 done — daily_email.html template written (navy theme, hosted logo).
```

---

## Task 7: Email dispatcher

**Files:**
- Create: `jotform_verification/send_verification_emails.py`

- [ ] **Step 7.1: Write the dispatcher**

```python
"""
Send daily JotForm verification emails to all 5 reps.

Usage:
    python send_verification_emails.py --day enamel --dry-run
    python send_verification_emails.py --day enamel
    python send_verification_emails.py --day pva
    python send_verification_emails.py --day waterproofing

--dry-run sends only to quintusl@olympicpaints.co.za for review.
"""
import argparse
import json
import time
import urllib.parse
from datetime import date
from pathlib import Path

import win32com.client

REPO_ROOT = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints")
JF_DIR = REPO_ROOT / "2.Areas" / "1. Sales" / "7. Competitor information" / "jotform_verification"
OUTPUT_DIR = JF_DIR / "output"
CONFIG_DIR = JF_DIR / "config"
TEMPLATES_DIR = JF_DIR / "templates"

DAY_LABELS = {
    "enamel":        ("Day 1 — Enamel",        "These cover every enamel/wood/primer line we sell against."),
    "pva":           ("Day 2 — PVA",           "Wall paint matchups — confirm we're putting up the right Olympic product against each competitor PVA."),
    "waterproofing": ("Day 3 — Waterproofing", "Roof, waterproofing and sundries. Catch-all category — flag anything that doesn't fit."),
}

COMPETITORS = [
    ("africa_paints",  "Africa Paints"),
    ("anetic",         "Anetic"),
    ("crest",          "Crest"),
    ("excelsior",      "Excelsior"),
    ("golden_choice",  "Golden Choice"),
]

def build_link(base_url: str, rep_code: str, rep_email: str, competitor: str, category: str) -> str:
    """Append URL-encoded prefill params for JotForm hidden fields."""
    params = urllib.parse.urlencode({
        "rep_email":  rep_email,
        "rep_code":   rep_code,
        "competitor": competitor,
        "category":   category,
    })
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{params}"

def render_links_html(urls: dict, category: str, rep_code: str, rep_email: str) -> str:
    parts = []
    for slug, label in COMPETITORS:
        url = urls[slug][category]
        if not url:
            continue
        full = build_link(url, rep_code, rep_email, slug, category)
        parts.append(
            f'<a class="link-row" href="{full}">'
            f'<strong>{label}</strong><br>'
            f'<span style="font-size:13px;color:#B8CCE8;">Open {label} {category} verification form &rarr;</span>'
            f'</a>'
        )
    return "\n".join(parts)

def send_one(outlook, to_email: str, cc_email: str, subject: str, html_body: str):
    mail = outlook.CreateItem(0)
    mail.To = to_email
    mail.CC = cc_email
    mail.Subject = subject
    mail.HTMLBody = html_body
    mail.Send()

def force_flush(outlook_app):
    """Per memory feedback_outlook_send_flush — Send() only queues; iterate Outbox to dispatch."""
    namespace = outlook_app.GetNamespace("MAPI")
    outbox = namespace.GetDefaultFolder(4)  # 4 = olFolderOutbox
    # Iterate snapshot of items (collection is mutated by Send())
    items = list(outbox.Items)
    for item in items:
        try:
            item.Send()
        except Exception as e:
            print(f"  flush skip: {e}")
    time.sleep(2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", required=True, choices=list(DAY_LABELS))
    parser.add_argument("--dry-run", action="store_true",
                        help="Send only to quintusl@olympicpaints.co.za, no reps.")
    args = parser.parse_args()

    urls = json.loads((OUTPUT_DIR / "jotform_urls.json").read_text())
    reps = json.loads((CONFIG_DIR / "rep_emails.json").read_text())
    template = (TEMPLATES_DIR / "daily_email.html").read_text(encoding="utf-8")

    day_label, intro = DAY_LABELS[args.day]
    subject = f"[Olympic] {day_label} Verification — please action today"
    today = date.today().isoformat()

    outlook = win32com.client.Dispatch("Outlook.Application")

    recipients = (
        [("Quintus Lategan (DRY RUN)", "quintusl@olympicpaints.co.za", "QL")]
        if args.dry_run
        else [(r["name"], r["email"], code) for code, r in reps.items()]
    )

    dispatch_log = []
    for name, email, code in recipients:
        links_html = render_links_html(urls, args.day, code, email)
        html_body = (template
                     .replace("{{day_label}}", day_label)
                     .replace("{{date}}", today)
                     .replace("{{rep_name}}", name)
                     .replace("{{intro}}", intro)
                     .replace("{{links}}", links_html))
        send_one(
            outlook,
            to_email=email,
            cc_email="quintusl@olympicpaints.co.za" if not args.dry_run else "",
            subject=subject,
            html_body=html_body,
        )
        dispatch_log.append({"rep": code, "name": name, "email": email, "day": args.day, "sent_at": today})
        print(f"  queued -> {name} <{email}>")

    force_flush(outlook)
    print("Force-flushed Outbox.")

    # Append to dispatch log
    log_path = OUTPUT_DIR / "dispatch_log.json"
    existing = json.loads(log_path.read_text()) if log_path.exists() else []
    existing.extend(dispatch_log)
    log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
```

- [ ] **Step 7.2: Dry-run dispatch to Quintus only**

```bash
python send_verification_emails.py --day enamel --dry-run
```

Check Quintus's inbox. Verify:
- Navy theme rendered (no broken CSS)
- Logo visible (hosted URL, not broken image)
- 5 link rows, one per competitor
- Click one link — confirm hidden fields are prefilled (`rep_email=quintusl@...`, `rep_code=QL`, `competitor=africa_paints`, `category=enamel`)

If anything is broken, fix the template/dispatcher and re-run the dry-run before going live.

- [ ] **Step 7.3: Log to changelog**

```
2026-05-16  T7 done — dispatcher script written; dry-run to Quintus verified.
```

---

## Task 8: Day 1 live dispatch (Enamels)

- [ ] **Step 8.1: Final check — today is Day 1 (Monday)?**

Confirm the calendar date before dispatching. Don't fire on a weekend.

- [ ] **Step 8.2: Send Day 1 to all 5 reps**

```bash
python send_verification_emails.py --day enamel
```

Expected stdout:
```
  queued -> Aboo Cassim <ac@...>
  queued -> Amit Patel <ap@...>
  queued -> Bhadresh Vallabh <bv@...>
  queued -> Nikhil Panchal <np@...>
  queued -> Byron Minnie <bm@...>
Force-flushed Outbox.
```

- [ ] **Step 8.3: Verify delivery**

Wait 60 seconds, then check Outlook Sent Items. All 5 emails should be there with `quintusl@olympicpaints.co.za` on CC.

- [ ] **Step 8.4: Send Telegram notification per [[feedback_telegram_notifications]]**

```python
import os, requests
from pathlib import Path
env_path = Path(r"c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE — Sales & Ops Manager\.env")
for line in env_path.read_text().splitlines():
    if line.startswith("TELEGRAM_BOT_TOKEN="):
        token = line.split("=", 1)[1].strip()
        break
requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": 8042233389,
          "text": "✅ Day 1 (Enamel) verification emails dispatched to 5 reps. CC: quintusl@."},
    timeout=10,
)
```

- [ ] **Step 8.5: Log to changelog**

```
2026-05-DD  T8 done — Day 1 (Enamel) live dispatch complete; 5 reps sent.
```

---

## Task 9: Day 2 live dispatch (PVAs)

- [ ] **Step 9.1: Send Day 2**

```bash
python send_verification_emails.py --day pva
```

- [ ] **Step 9.2: Verify Outlook Sent + send Telegram (same pattern as T8.3 / T8.4 with text "Day 2 (PVA)...")**

- [ ] **Step 9.3: Log to changelog**

```
2026-05-DD  T9 done — Day 2 (PVA) live dispatch complete; 5 reps sent.
```

---

## Task 10: Day 3 live dispatch (Waterproofing)

- [ ] **Step 10.1: Send Day 3**

```bash
python send_verification_emails.py --day waterproofing
```

- [ ] **Step 10.2: Verify Outlook Sent + send Telegram (same pattern, text "Day 3 (Waterproofing)...")**

- [ ] **Step 10.3: Log to changelog**

```
2026-05-DD  T10 done — Day 3 (Waterproofing) live dispatch complete; 5 reps sent. Verification rollout complete.
```

---

## Task 11: Memory entry

- [ ] **Step 11.1: Write memory file**

Save to `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\reference_competitor_verification_forms.md`:

```markdown
---
name: competitor-verification-forms
description: JotForm verification rollout — 15 forms (5 competitors x 3 categories) for reps to confirm Olympic <-> competitor product matchups
metadata:
  type: reference
---

15 JotForms verify Olympic ↔ competitor product matchups. One form per (competitor, category): 5 competitors × 3 categories. Built 2026-05-16.

**Build artifacts:** `2.Areas/1. Sales/7. Competitor information/jotform_verification/`
- `categorise_skus.py` — re-run if pricelist changes; writes 3 SKU JSONs
- `extract_matchups.py` — re-run if any `Olympic_vs_<Brand>_Competitor_Analysis.xlsx` changes; writes 15 matchup JSONs
- `send_verification_emails.py --day enamel|pva|waterproofing` — daily dispatcher
- `output/jotform_urls.json` — live form URL map (don't regenerate unless rebuilding all forms)
- `config/category_mapping.json` — load-bearing bucketing rules; enforces [[feedback_pva_vs_enamel_categories]]

**Rebuild rule:** If a workbook is hand-edited, re-run `extract_matchups.py` then re-create only the affected form via JotForm MCP `edit_form` (do NOT delete + recreate — the URL changes break the email links).

**Submissions:** Native JotForm storage. Aggregation script is future work (see plan §6.5).
```

- [ ] **Step 11.2: Index in MEMORY.md**

Append to `C:\Users\quint\.claude\projects\c--Users-quint-OneDrive-1-Projects-1-Olympic-Paints\memory\MEMORY.md` under "Competitor Intelligence":

```
- [Competitor Verification Forms — rollout artifacts](reference_competitor_verification_forms.md) — 15 JotForms confirm Olympic↔competitor matchups; scripts in `jotform_verification/`; live URL map in `output/jotform_urls.json`
```

- [ ] **Step 11.3: Log to changelog**

```
2026-05-DD  T11 done — memory entry saved and indexed.
```

---

## Self-review checklist (run before handoff)

- [ ] All file paths use raw strings or quoted strings (paths contain spaces)
- [ ] No placeholders ("TBD", "implement later") remain in any task
- [ ] Memory references use double-bracket `[[name]]` syntax
- [ ] Function signatures consistent (no `categorise_skus()` in T1 vs `categorise()` in T2)
- [ ] T2 column indices flagged for verification in T2.1 — extractor is not assumed correct until audited
- [ ] Force-flush after Outlook.Send() present (T7.1)
- [ ] Logo uses hosted URL, not local file path (T6.1)
- [ ] Dry-run before live dispatch (T7.2 before T8)
- [ ] Telegram notification after each live dispatch (T8.4, T9.2, T10.2)

If any item fails, fix inline. No re-review needed.
