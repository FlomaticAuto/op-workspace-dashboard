# Rock Bottom to Product Codes Mapping

**Purpose:** Reproducible methodology for populating SKU-level prices on the Olympic Paints master product sheet (`Sheet1 (2)`) by looking up each product against the price-bracket sheet (`Sheet2`), applying colour routing, size normalisation, and fallback rules.

**Source file pattern:** `Updated_Rock_Bottom_-_All_Products_<DATE>.xlsx`

**Output file pattern:** `Rock_Bottom_Prices_Populated_<DATE>.xlsx`

---

## 1. Input file structure

The input workbook contains three sheets that must be understood correctly before any work begins. Sheet naming can drift, so always identify them by content shape, not name.

### 1.1 `sheet1` — legacy price list (8 columns)

Flat list of product codes with Pre-April and Post-April prices. Columns:

| Col | Header | Description |
|-----|--------|-------------|
| A | Product Code | 6-digit SKU code or alphanumeric (e.g. `119401`, `RMWHITE1L`) |
| B | prodname.1 | Full description e.g. "20LT 7-IN-1 ACRYLIC PVA WHITE" |
| C | product_group | Category label |
| D | Pre April | Old price |
| E | Post April | New price |

This sheet is **reference only** — NOT used as the price source in this workflow.

### 1.2 `Sheet2` — price bracket sheet (14 columns, ~205 rows)

**This is the price source.** Two-row header:

Row 1 headers: Product | Pack Size | List Price 2024 | Less 10 | | Less 15 | Less 17.5 | Less 20 | | Less 22.5 | Less 25 | Less 30 | | Rock Bottom

Row 2 headers: (blank) | (blank) | (blank) | Min | Max | (blank) | (blank) | Min | Max | (blank) | (blank) | Min | Max | Price

Critical column map:

| Col | Header | Use |
|-----|--------|-----|
| A | Product | Sheet2 product name (e.g. "Décor White / Cream") |
| B | Pack Size | Pack size string (e.g. "20LT", "5LT", "500Gr X 24") |
| L | Less 30 (Max) | **Fallback price** |
| N | Rock Bottom Price | **Primary price** |

Data starts at row 3. Some products (e.g. rows 207-208 "Rainproof", "QD Bronze") were appended with only List Price filled — no L or N — these rows cannot be priced.

**Whitespace quirk:** Some cells (e.g. Putty 10Kg Less 25) contain a whitespace-only string instead of a number or blank. Treat whitespace-only strings as `None`.

### 1.3 `Sheet1 (2)` — SKU master (24 columns, ~1,200 rows)

**This is the target.** Every row is one SKU (unique Product Code + Colour + Size combination). Columns of interest:

| Col | Header | Use |
|-----|--------|-----|
| A | Product Code | SKU identifier |
| C | Product Name | Product family (e.g. "NATURAL ELEGANCE") |
| D | Color | Colour variant (e.g. "Brilliant White", "Caledon Green") |
| J | Size | Pack size (e.g. "20L", "5L", "500GM") |
| X | Price | **Target cell — initially empty** |

---

## 2. Business rules (the user's requirements)

1. **Match each SKU in `Sheet1 (2)` to a price bracket in `Sheet2`** using Product Name + Pack Size.
2. **Colour routing:** In `Sheet2`, some products have separate White/Cream and Colours entries. Route by colour:
   - White, Cream, Ivory, etc. → White/Cream bracket
   - Everything else → Colours bracket
3. **Price priority:** Use `Sheet2` **column N (Rock Bottom Price)**. If column N is empty, fall back to **column L (Less 30)**. If both are empty, leave blank.
4. **Output:** Populate column X of `Sheet1 (2)` with the matched price.

---

## 3. Tools used

The entire workflow runs in the Claude claude.ai code-execution sandbox (Linux/Ubuntu with Python 3 + openpyxl + LibreOffice available). No external APIs, no MCP connectors, no web search — this is a pure local-file transformation task.

| Tool | Purpose |
|------|---------|
| `view` | Read the `xlsx` SKILL.md before any Excel work (mandatory first step) |
| `bash_tool` | Run Python scripts for inspection and transformation |
| `create_file` | Write the `price_lookup.py` mapping module and `build_output.py` writer |
| `str_replace` | Iterative edits to the lookup module as edge cases were discovered |
| `present_files` | Deliver the final `.xlsx` to the user |

**Python libraries used:** `openpyxl` (read/write xlsx while preserving formulas/formatting), `shutil` (copy source to preserve original), `collections.Counter` (diagnostic grouping of unmatched rows).

**No pandas used** — openpyxl is the correct choice here because we need row-level coordinate access and cell-level formatting (yellow highlighting for unmatched rows).

---

## 4. Process walkthrough

### Phase 1 — Understand the ask

Re-read the user's instructions carefully. The user labelled the sheets "1, 2, 3" in the message ("Sheet one, Sheet two, Sheet one (2)") but their description of column layouts revealed that:

- "**sheet 2**" in the user's prose = `Sheet1 (2)` in the file (the SKU target with Product Name in col C, sizes in cols I–L)
- The price reference is `Sheet2` (the bracket sheet with col N = Rock Bottom, col L = Less 30)

Confirming this before coding is non-negotiable — the opposite interpretation wipes out existing prices and produces nonsense.

### Phase 2 — Read the SKILL and inspect the file

1. `view /mnt/skills/public/xlsx/SKILL.md` (mandatory before any xlsx work).
2. Copy the uploaded file to the working directory: `cp /mnt/user-data/uploads/<file>.xlsx /home/claude/input.xlsx`.
3. Enumerate sheets, dimensions, and first 5 rows of each with `openpyxl.load_workbook(..., data_only=True)`.
4. Dump the full `Sheet2` catalogue (only ~205 rows) to understand the product+size universe.
5. Extract unique Product+Size → Colours combinations from `Sheet1 (2)` to see what needs mapping.

### Phase 3 — Build the Sheet2 catalogue

```python
catalog = {}  # (product_name_stripped, pack_size_stripped) -> (rock_bottom_N, less_30_L)
for r in range(3, ws2.max_row + 1):
    pname = ws2.cell(row=r, column=1).value
    psize = ws2.cell(row=r, column=2).value
    less30 = ws2.cell(row=r, column=12).value  # col L
    rock = ws2.cell(row=r, column=14).value    # col N
    if pname is None:
        continue
    key = (pname.strip(), str(psize).strip() if psize else '')
    catalog[key] = (rock, less30)
```

### Phase 4 — Build the lookup function

Three layers, in order:

1. **Size normalisation** (`normalize_size`) — coerces Sheet1(2) sizes to Sheet2 format.
2. **Product routing** (`_route`) — maps Sheet1(2) product name + colour to the correct Sheet2 product name.
3. **Fallback chain** (`_route_with_fallbacks`) — when a primary target doesn't exist at the requested size, try a sensible alternative.

Then apply the lookup in order:
- Try `(primary, size)` → if rock is not None, return it (source "N")
- Else if less30 is not None, return it (source "L")
- Else try next fallback candidate
- Else return None

### Phase 5 — Iterate on unmatched rows

Start with coarse mapping, run, measure. The unmatched list groups naturally by Product+Size, which makes it obvious where edges are. Each iteration either:
- **Adds a mapping** (a Sheet2 product we didn't recognise before), or
- **Adds a fallback** (a size that doesn't exist in the primary bracket), or
- **Accepts as genuinely unmatched** (product not in the price list at all, or Sheet2 row missing both N and L)

Started at 0 matched → 1037 matched (86.4%) on first pass → 1065 (88.7%) after fallback rules.

### Phase 6 — Write the output

1. Copy the input file to the output path (preserves all existing data, formulas, formatting).
2. Load with openpyxl (NOT `data_only=True` — that would destroy formulas permanently).
3. Populate col X with matched prices (rounded to 2 dp).
4. Add three audit columns (Y, Z, AA) for traceability.
5. Apply ZAR currency formatting to col X: `R #,##0.00;[Red]-R #,##0.00`.
6. Highlight unmatched rows yellow (`#FFF4CC`).
7. Freeze header row.
8. Save.

### Phase 7 — Deliver

Move to `/mnt/user-data/outputs/` and call `present_files`.

---

## 5. Size normalisation table

| Sheet1(2) size | Sheet2 size | Notes |
|----------------|-------------|-------|
| `20L` or `20LT` | `20LT` | |
| `5L` or `5LT` | `5LT` | |
| `1L` or `1LT` | `1LT` | |
| `2.5L` | `2.5LT` | |
| `500ML` | `500ML` | |
| `750ML` | `750ML` | Exception: Carbolineum, Thinners, Turpentine, Raw Linseed Oil → `750ML X 12` |
| `100ML` | `100ML x12` | For Stainers |
| `50ML` | `50ML x 12` | For Stainers |
| `200MM` | `200MM` | Membrane |
| `75MM` | `75MM` | Membrane |
| `10KG` | `10Kg` | Putty only |
| `20KG` | `20Kg` | Putty only |
| `5KG` | `5Kg` | |
| `1KG` | `1kg X 24` | Putty |
| `2KG` | `2Kg X 12` | (Distemper → `2Kg X 6`) |
| `40KG` | `40Kg` | Putty |
| `500GM` | `500Gr X 24` | Oxides |
| `DOZ 1L` | `1LT X 12` | Galvanised Iron Cleaner, Rust Remover |

---

## 6. Product routing table (complete)

Sheet1 (2) Product Name → Sheet2 Product Name(s). UPPERCASE = Sheet1 (2) source; normal case = Sheet2 target.

### 6.1 Direct product mappings (one-to-one)

| Sheet1 (2) | Sheet2 |
|-----------|--------|
| `7-IN-1 ACRYLIC PVA` | `7 in 1 Acrylic PVA` |
| `3-IN-1 ROOF PAINT`, `3-1N-1 ROOF PAINT` | `3 in 1 Roof Paint` |
| `BONDING LIQUID` | `Bonding Liquid` |
| `CARBOLINEUM` | `Carbolineum` |
| `CRACK FILLER` | `Crack Filler` |
| `DAMP FIX` | `Damp Fix` |
| `DISTEMPER` | `Distemper Colours` |
| `FACE BRICK` | `Face-Brick Dressing` |
| `GALVANISED IRON CLEANER` | `Galvanised Iron Cleaner & Degreaser` |
| `HI HIDING CONT PVA` | `Hi-Hiding Super Acrylic Cont. PVA White` |
| `ETCH PRIMER` | `One ETCH Primer Black` |
| `PAINT REMOVER` | `Paint Remover` |
| `WOOD PRIMER` | `Pink Wood Primer` |
| `PLASTER & TILE BOND`, `PLASTER & TILE BONDING LIQUID` | `Plaster & Tile Bond` |
| `PUTTY` | `Putty` |
| `ALL IN ONE` | `Platinum Plus All-in-one Protector` |
| `FIBRE RESTORE` | `Platinum Plus Fibre Restore` |
| `ALKYD ROOF /STOEP`, `STOEP` | `Roof & Stoep` |
| `RUST REMOVER` | `Rust Remover` |
| `SANDING SEALER` | `Sanding Sealer` |
| `UNIV UNDERCOAT` | `Universal Undercoat` |
| `TURPENTINE` | `Turpentine` |
| `LACQUER THINNERS` | `Thinners` |
| `RAW LINSEED OIL` | `Raw Linseed Oil` |
| `ZINC PHOSPHATE PRIMER` | `Zinc Phosphate Primer Green` |
| `WATERBASE OXIDE PRIMER` | `Water Based Red Oxide Primer` |
| `WATERBASED PLASTER PRIMER` | `Water Based Plaster Primer` |
| `LIBERTY PVA` | `Liberty White/Cream` |
| `RAINPROOF`, `HYPER STEEL RAINPROOF`, `HYPERSTEEL RAINPROOF` | `Rainproof + Membrane` |

### 6.2 Colour-routed products (White/Cream vs Colours)

"White family" = `WHITE`, `CREAM`, `IVORY`, `BROKEN WHITE`, `BRILLIANT WHITE`, `VANILLA WHITE`, `WHITE WISPER`, `RICE WHITE`, `FLAT WHITE`, `APPLICANCE WHITE`.

| Sheet1 (2) Product | White family → | Other colours → |
|--------------------|----------------|-----------------|
| `DECOR` | `Décor White / Cream` | `Décor Colours` |
| `ECLIPSE PVA` | `Eclipse White / Cream` | `Eclipse Colours` |
| `EGGSHELL ENAMEL` | White=`Eggshell Enamel White`; Cream/Ivory=`Eggshell Enamel Cream` | default `Eggshell Enamel White` |
| `KALAHARI CONTRACTORS`, `KALAHARI CONTR` | `Kalahari Contractors White / Cream` | `Kalahari Contractors Colours` |
| `MASTER DECORATORS` | `Master Decorators White/Cream` | `Master Decorators Colours` |
| `NATURAL ELEGANCE` | `Platinum Plus Natural Elegance White` | `Platinum Plus Natural Elegance Colours` |
| `RUGGED BEAUTY` | `Platinum Plus Rugged Beauty White` | `Platinum Plus Rugged Beauty Colours` |
| `SUBURBAN BLISS` | `Platinum Plus Suburban Bliss White` | `Platinum Plus Suburban Bliss Colours` |

### 6.3 Special colour groupings

| Sheet1 (2) Product | Colour rule | Sheet2 target |
|--------------------|-------------|---------------|
| `HIGH GLOSS ENAMEL` | White | `High Gloss White` |
| `HIGH GLOSS ENAMEL` | Black | `High Gloss White/Black` |
| `HIGH GLOSS ENAMEL` | Peach, Cream, G Brown, Maxi Peach | `High Gloss Peach / Cream / Golden Brown` |
| `HIGH GLOSS ENAMEL` | all other | `High Gloss Colours` |
| `PLUSH COAT` | Green, Emu Green | `Platinum Plus Plush Coat Green/Emu Green` |
| `PLUSH COAT` | all other | `Platinum Plus Plush Coat Colours` |
| `UNIVERSAL ROOF`, `JUST PAINT ROOF`, `UNIV ROOF PLAIN BUCKET` | Green, Emu Green, Albany, Ocean Blue | `Universal Roof Green / Emu Green / Albany / Ocean Blue` |
| `UNIVERSAL ROOF`, `JUST PAINT ROOF`, `UNIV ROOF PLAIN BUCKET` | all other | `Universal Roof Colours` |
| `PICK 'N SAVE ECONO` | Peach | `Pick and Save Peach` |
| `PICK 'N SAVE ECONO` | White, Cream | `Pick and Save White / Cream` |
| `PICK 'N SAVE ECONO` | all other | `Pick and Save Colours` |
| `ULTIMATE SHINE` | White | `Ulitmate Shine White` *(note typo in Sheet2)* |
| `ULTIMATE SHINE` | Cream | `Ulitmate Shine Cream` |
| `ULTIMATE SHINE` | Black | `Ulitmate Shine White/Black` |
| `ULTIMATE SHINE` | all other | `Ulitmate Shine Colours` |
| `VARNISH` | Copal | `Varnish Copal` |
| `VARNISH` | all other (Teak, Walnut, Dark Oak, etc.) | `Varnish Colours` |
| `ROAD MARKING` | Yellow | `Road Marking Paint Yellow` |
| `ROAD MARKING` | White (default) | `Road Marking Paint White` |
| `SCHOOL BOARD` | Green | `Schoolboard Green` |
| `SCHOOL BOARD` | all other (default Black) | `Schoolboard Black` |
| `OXIDE`, `BLUE OXIDE` | Green, Blue | `Oxide Green/Blue` |
| `OXIDE`, `RED OXIDE` | Red, Black | `Oxide Red/Black` |
| `OXIDE` | Yellow, Brown | `Oxide Yellow/Brown` |
| `100ML STAINERS`, `50ML STAINERS`, `50ML STAINERS L`, `STAINER` | Violet | `Stainers (Doz) Violet` |
| `100ML STAINERS`, `50ML STAINERS`, `50ML STAINERS L`, `STAINER` | all other | `Stainers (Doz)` |

### 6.4 Q.D Enamel colour-by-colour mapping

Each colour has its own bracket. For `Q.D ENAMEL`, `Q.D ENAMEL (PLAIN)`, and `HYPER STEEL Q.D ENAMEL`:

| Colour | Target |
|--------|--------|
| Black, Matt Black, Blue Black | `QD Enamel Black` |
| White | `QD Enamel White` |
| Bronze, Light Bronze | `Q.D Enamel Bronze` (at 20L, fallback to `QD Bronze`) |
| Burgundy, Berry Blaze | `Q.D Enamel Burgundy` |
| Cat Yellow | `Q.D Enamel Cat Yellow` |
| Copper | `Q.D Enamel Copper` |
| Dark Grey, Grey, Charcoal, Charcoal Grey, Blue Grey | `Q.D Enamel Dark Grey` |
| G Brown | `Q.D Enamel G Brown` |
| PWD Brown | `Q.D Enamel PWD Brown` |
| Green, Windsor Green | `Q.D Enamel Green` |
| JD Green | `Q.D Enamel JD Green` |
| Royal Blue, Azure Blue, S Blue | `Q.D Enamel Royal Blue` |
| S Red, Post Office Red, Red | `Q.D Enamel Signal Red` |
| Silver | `Q.D Enamel Silver` |
| default | `Q.D Enamel Signal Red` |

For `3-IN-1 Q.D GRIP COAT` and `HYPER STEEL Q.D GRIP COAT`:

| Colour | Target |
|--------|--------|
| Black | `Q.D Gripcoat Enamel Black` |
| Bronze | `Q.D Gripcoat Enamel Bronze` |
| White | `Q.D Gripcoat Enamel White` |

### 6.5 Q.D Primer consolidation

| Sheet1 (2) | Sheet2 |
|-----------|--------|
| `Q.D OXIDE PRIMER`, `Q D OXIDE PRIMER`, `HYPER STEEL Q.D RED OXDE PRIMER`, `HYPER STEEL Q.D RED PRIMER`, `HYPER STEEL QD OXIDE`, `Q.DBLACK OXIDE PRIMER` | `QD Red Oxide Primer` |
| `QD GREY OXIDE PRIMER`, `HYPERSTEEL Q.D OXIDE PRIMER`, `QD PRIMER`, `Q.D GREY PRIMER`, `Q.DGREY PRIMER`, `HYPER STEEL Q.D GREY PRIMER` | `QD Grey Oxide Primer` |

### 6.6 FLAT ENAMEL special handling

`FLAT ENAMEL` has no Sheet2 equivalent. Route to Eggshell as nearest proxy:
- White → `Eggshell Enamel White`
- else → `Eggshell Enamel Cream`

### 6.7 Products with NO Sheet2 mapping (return None → unmatched)

`AEROSOL`, `JUST PAINT WALL`, `VERSA PVA`, `ACORNHOEK PVA`, `BEST BUILD PVA`, `MADALAS CHOICE PVA`, `DROP SHEET`, `MASKING TAPE`, `PAINT BRUSH`, `SANDGRIT PAPER`, `SPIRIT OF SALTS`, `PLATINUM PAINT`, `Platinum Paint Roller`, `Q.D CLEAR BASE`, `ULTIMATE SHINE BASE`, `ULTIMATE SHINEBASE`, `BLACK WATER BASE OXIDE PRIMER`, `WATER BASE BLACK OXIDE PRIMER`, `MEMBRANE` (at 200MM/75MM — Sheet2 has Membrane Large/Small but no matching size link is safe).

---

## 7. Size-missing fallback chains

When the primary target exists in Sheet2 but not at the requested size, try a secondary target. Applied only after primary lookup fails.

| Product | Primary | Size gap | Fallback |
|---------|---------|----------|----------|
| `HIGH GLOSS ENAMEL` | `High Gloss Peach / Cream / Golden Brown` | 1LT, 5LT, 500ML | `High Gloss Colours` |
| `HIGH GLOSS ENAMEL` | `High Gloss White` | 1LT, 5LT, 500ML | `High Gloss White/Black` |
| `ULTIMATE SHINE` | `Ulitmate Shine Cream` | 1LT, 5LT, 500ML | `Ulitmate Shine Colours` |
| `ULTIMATE SHINE` | `Ulitmate Shine White` | 1LT, 5LT, 500ML | `Ulitmate Shine White/Black` |
| `EGGSHELL ENAMEL` | `Eggshell Enamel Cream` | 20LT | `Eggshell Enamel White` |
| `Q.D ENAMEL` (Bronze) | `Q.D Enamel Bronze` | 20LT | `QD Bronze` |

---

## 8. Known unmatched rows (expected "NO MATCH" in output)

These are legitimate Sheet2 gaps. Review and either fill in Sheet2 or accept as-is.

### 8.1 Products not in price list at all (~90 rows)
AEROSOL (26), JUST PAINT WALL 20L (21), VERSA PVA 20L (11), MASKING TAPE (3), PAINT BRUSH (4), DROP SHEET (2), ACORNHOEK/BEST BUILD/MADALAS PVA (~8), Q.D CLEAR BASE (2), ULTIMATE SHINE BASE (2), Platinum Paint Roller (1), SANDGRIT PAPER (1), SPIRIT OF SALTS (2), etc.

### 8.2 Sheet2 size-bracket gaps (~30 rows)
- OXIDE 10KG/40KG/20KG — Sheet2 only has 5Kg and 500Gr packs
- ROAD MARKING 20L — Sheet2 has 1LT and 5LT only
- BONDING LIQUID 20L — Sheet2 has 1LT and 5LT only
- ALL IN ONE 1L — Sheet2 has 20LT and 5LT only
- CRACK FILLER 20KG — Sheet2 has 10Kg, 5Kg, 2Kg, 500Gr only
- PLASTER & TILE BONDING LIQUID 1L — Sheet2 "1 X 12" is a 12-pack of 1L, not a single 1L
- LACQUER THINNERS 200L, various 200L items

### 8.3 Sheet2 rows with no N and no L (~15 rows)
Rows appended at bottom of Sheet2 (R207 Rainproof 20LT, R208 QD Bronze 20LT) and other entries where both "Less 30 Max" and "Rock Bottom Price" are blank. These affect:
- HIGH GLOSS 20L coloured variants (not White, not Peach/Cream/G.Brown)
- PICK 'N SAVE 20L coloured variants
- Q.D ENAMEL 20L Charcoal
- Rainproof 20L, QD Bronze 20L

---

## 9. Complete executable code

### 9.1 `price_lookup.py`

```python
"""
Price lookup module: maps (Product Name, Colour, Size) from Sheet1 (2)
to a price from Sheet2 via column N (Rock Bottom) with fallback to column L (Less 30).
"""
from openpyxl import load_workbook

# ---------- Load Sheet2 catalog ----------
wb = load_workbook('input.xlsx', data_only=True)
ws2 = wb['Sheet2']

# (product_name_stripped, pack_size_stripped) -> (rock_bottom, less_30)
catalog = {}
for r in range(3, ws2.max_row + 1):
    pname = ws2.cell(row=r, column=1).value
    psize = ws2.cell(row=r, column=2).value
    less30 = ws2.cell(row=r, column=12).value  # L
    rock = ws2.cell(row=r, column=14).value    # N
    if pname is None:
        continue
    key = (pname.strip(), str(psize).strip() if psize is not None else '')
    catalog[key] = (rock, less30)


def _clean_price(v):
    """Return numeric price or None. Treat blank strings / whitespace as None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def normalize_size(s):
    """Convert Sheet1(2) size to Sheet2 format."""
    if s is None:
        return ''
    s = str(s).strip().upper()
    if s in ('20L', '20LT'): return '20LT'
    if s in ('5L', '5LT'): return '5LT'
    if s in ('1L', '1LT'): return '1LT'
    if s in ('2.5L', '2.5LT'): return '2.5LT'
    if s == '500ML': return '500ML'
    if s == '750ML': return '750ML'
    if s == '100ML': return '100ML'
    if s == '50ML': return '50ML'
    if s == '200MM': return '200MM'
    if s == '75MM': return '75MM'
    if s == '10KG': return '10Kg'
    if s == '20KG': return '20Kg'
    if s == '5KG': return '5Kg'
    if s == '1KG': return '1kg X 24'
    if s == '2KG': return '2Kg X 12'
    if s == '40KG': return '40Kg'
    if s == '500GM': return '500Gr X 24'
    return s


def _route_size(pname_u, size_n):
    """Handle special size mappings."""
    if 'STAINER' in pname_u:
        if size_n == '100ML': return '100ML x12'
        if size_n == '50ML': return '50ML x 12'
    if pname_u == 'CARBOLINEUM' and size_n == '750ML':
        return '750ML X 12'
    if 'THINNERS' in pname_u and size_n == '750ML':
        return '750ML X 12'
    if pname_u == 'TURPENTINE' and size_n == '750ML':
        return '750ML X 12'
    if 'RAW LINSEED' in pname_u and size_n == '750ML':
        return '750ML X 12'
    if 'GALVANISED IRON' in pname_u and size_n == 'DOZ 1L':
        return '1LT X 12'
    if 'RUST REMOVER' in pname_u and size_n == 'DOZ 1L':
        return '1LT X 12'
    if pname_u == 'OXIDE' and size_n == '500GM':
        return '500Gr X 24'
    if pname_u == 'DISTEMPER' and size_n == '2Kg X 12':
        return '2Kg X 6'
    return size_n


def _route(pname_u, color_u):
    """Return Sheet2 product name given upper-cased Sheet1(2) product + colour, or None."""
    white_family = color_u in ('WHITE', 'CREAM', 'IVORY', 'BROKEN WHITE', 'BRILLIANT WHITE',
                                'VANILLA WHITE', 'WHITE WISPER', 'RICE WHITE', 'FLAT WHITE',
                                'APPLICANCE WHITE')

    # Direct mappings (one-to-one)
    if pname_u == '7-IN-1 ACRYLIC PVA': return '7 in 1 Acrylic PVA'
    if pname_u in ('3-IN-1 ROOF PAINT', '3-1N-1 ROOF PAINT'): return '3 in 1 Roof Paint'
    if pname_u == 'BONDING LIQUID': return 'Bonding Liquid'
    if pname_u == 'CARBOLINEUM': return 'Carbolineum'
    if pname_u == 'CRACK FILLER': return 'Crack Filler'
    if pname_u == 'DAMP FIX': return 'Damp Fix'
    if pname_u == 'DISTEMPER': return 'Distemper Colours'
    if pname_u == 'FACE BRICK': return 'Face-Brick Dressing'
    if pname_u == 'GALVANISED IRON CLEANER': return 'Galvanised Iron Cleaner & Degreaser'
    if pname_u == 'HI HIDING CONT PVA': return 'Hi-Hiding Super Acrylic Cont. PVA White'
    if pname_u == 'ETCH PRIMER': return 'One ETCH Primer Black'
    if pname_u == 'PAINT REMOVER': return 'Paint Remover'
    if pname_u == 'WOOD PRIMER': return 'Pink Wood Primer'
    if pname_u == 'PLASTER & TILE BOND': return 'Plaster & Tile Bond'
    if pname_u == 'PLASTER & TILE BONDING LIQUID': return 'Plaster & Tile Bond'
    if pname_u == 'PUTTY': return 'Putty'
    if pname_u == 'ALL IN ONE': return 'Platinum Plus All-in-one Protector'
    if pname_u == 'FIBRE RESTORE': return 'Platinum Plus Fibre Restore'
    if pname_u in ('ALKYD ROOF /STOEP', 'STOEP'): return 'Roof & Stoep'
    if pname_u == 'RUST REMOVER': return 'Rust Remover'
    if pname_u == 'SANDING SEALER': return 'Sanding Sealer'
    if pname_u == 'UNIV UNDERCOAT': return 'Universal Undercoat'
    if pname_u == 'TURPENTINE': return 'Turpentine'
    if pname_u == 'LACQUER THINNERS': return 'Thinners'
    if pname_u == 'RAW LINSEED OIL': return 'Raw Linseed Oil'
    if pname_u == 'ZINC PHOSPHATE PRIMER': return 'Zinc Phosphate Primer Green'
    if pname_u == 'WATERBASE OXIDE PRIMER': return 'Water Based Red Oxide Primer'
    if pname_u == 'WATERBASED PLASTER PRIMER': return 'Water Based Plaster Primer'
    if pname_u == 'LIBERTY PVA': return 'Liberty White/Cream'
    if pname_u in ('RAINPROOF', 'HYPER STEEL RAINPROOF', 'HYPERSTEEL RAINPROOF'):
        return 'Rainproof + Membrane'

    # Colour-routed products
    if pname_u == 'DECOR':
        return 'Décor White / Cream' if white_family else 'Décor Colours'
    if pname_u == 'ECLIPSE PVA':
        return 'Eclipse White / Cream' if white_family else 'Eclipse Colours'
    if pname_u == 'EGGSHELL ENAMEL':
        if color_u == 'WHITE': return 'Eggshell Enamel White'
        if color_u in ('CREAM', 'IVORY'): return 'Eggshell Enamel Cream'
        return 'Eggshell Enamel White'
    if pname_u in ('KALAHARI CONTRACTORS', 'KALAHARI CONTR'):
        return 'Kalahari Contractors White / Cream' if white_family else 'Kalahari Contractors Colours'
    if pname_u == 'MASTER DECORATORS':
        return 'Master Decorators White/Cream' if white_family else 'Master Decorators Colours'
    if pname_u == 'NATURAL ELEGANCE':
        return 'Platinum Plus Natural Elegance White' if white_family else 'Platinum Plus Natural Elegance Colours'
    if pname_u == 'RUGGED BEAUTY':
        return 'Platinum Plus Rugged Beauty White' if white_family else 'Platinum Plus Rugged Beauty Colours'
    if pname_u == 'SUBURBAN BLISS':
        return 'Platinum Plus Suburban Bliss White' if white_family else 'Platinum Plus Suburban Bliss Colours'

    # Special colour groupings
    if pname_u == 'HIGH GLOSS ENAMEL':
        if color_u == 'WHITE': return 'High Gloss White'
        if color_u == 'BLACK': return 'High Gloss White/Black'
        if color_u in ('PEACH', 'CREAM', 'G BROWN', 'MAXI PEACH'):
            return 'High Gloss Peach / Cream / Golden Brown'
        return 'High Gloss Colours'
    if pname_u == 'PLUSH COAT':
        if color_u in ('GREEN', 'EMU GREEN'): return 'Platinum Plus Plush Coat Green/Emu Green'
        return 'Platinum Plus Plush Coat Colours'
    if pname_u in ('UNIVERSAL ROOF', 'JUST PAINT ROOF', 'UNIV ROOF PLAIN BUCKET'):
        if color_u in ('GREEN', 'EMU GREEN', 'ALBANY', 'OCEAN BLUE'):
            return 'Universal Roof Green / Emu Green / Albany / Ocean Blue'
        return 'Universal Roof Colours'
    if pname_u == "PICK 'N SAVE ECONO":
        if color_u == 'PEACH': return 'Pick and Save Peach'
        if white_family: return 'Pick and Save White / Cream'
        return 'Pick and Save Colours'
    if pname_u == 'ULTIMATE SHINE':
        if color_u == 'WHITE': return 'Ulitmate Shine White'
        if color_u == 'CREAM': return 'Ulitmate Shine Cream'
        if color_u == 'BLACK': return 'Ulitmate Shine White/Black'
        return 'Ulitmate Shine Colours'
    if pname_u == 'VARNISH':
        return 'Varnish Copal' if color_u == 'COPAL' else 'Varnish Colours'
    if pname_u == 'ROAD MARKING':
        return 'Road Marking Paint Yellow' if color_u == 'YELLOW' else 'Road Marking Paint White'
    if pname_u == 'SCHOOL BOARD':
        return 'Schoolboard Green' if color_u == 'GREEN' else 'Schoolboard Black'

    # Oxides
    if pname_u == 'OXIDE':
        if color_u in ('GREEN', 'BLUE'): return 'Oxide Green/Blue'
        if color_u in ('RED', 'BLACK'): return 'Oxide Red/Black'
        if color_u in ('YELLOW', 'BROWN'): return 'Oxide Yellow/Brown'
        return None
    if pname_u == 'RED OXIDE': return 'Oxide Red/Black'
    if pname_u == 'BLUE OXIDE': return 'Oxide Green/Blue'

    # Stainers
    if pname_u in ('100ML STAINERS', '50ML STAINERS', '50ML STAINERS L', 'STAINER'):
        return 'Stainers (Doz) Violet' if color_u == 'VIOLET' else 'Stainers (Doz)'

    # Q.D Enamel (colour-specific)
    if pname_u in ('Q.D ENAMEL', 'Q.D ENAMEL (PLAIN)'):
        color_map = {
            'BLACK': 'QD Enamel Black', 'MATT BLACK': 'QD Enamel Black', 'BLUE BLACK': 'QD Enamel Black',
            'WHITE': 'QD Enamel White',
            'BRONZE': 'Q.D Enamel Bronze',
            'BURGUNDY': 'Q.D Enamel Burgundy', 'BERRY BLAZE': 'Q.D Enamel Burgundy',
            'CAT YELLOW': 'Q.D Enamel Cat Yellow',
            'COPPER': 'Q.D Enamel Copper',
            'DARK GREY': 'Q.D Enamel Dark Grey', 'GREY': 'Q.D Enamel Dark Grey',
            'CHARCOAL GREY': 'Q.D Enamel Dark Grey', 'CHARCOAL': 'Q.D Enamel Dark Grey',
            'BLUE GREY': 'Q.D Enamel Dark Grey',
            'G BROWN': 'Q.D Enamel G Brown',
            'PWD BROWN': 'Q.D Enamel PWD Brown',
            'GREEN': 'Q.D Enamel Green',
            'JD GREEN': 'Q.D Enamel JD Green',
            'ROYAL BLUE': 'Q.D Enamel Royal Blue', 'AZURE BLUE': 'Q.D Enamel Royal Blue',
            'S BLUE': 'Q.D Enamel Royal Blue',
            'S RED': 'Q.D Enamel Signal Red', 'RED': 'Q.D Enamel Signal Red',
            'SILVER': 'Q.D Enamel Silver',
        }
        return color_map.get(color_u, 'Q.D Enamel Signal Red')

    if pname_u == 'HYPER STEEL Q.D ENAMEL':
        color_map = {
            'BLACK': 'QD Enamel Black', 'MATT BLACK': 'QD Enamel Black',
            'WHITE': 'QD Enamel White',
            'BRONZE': 'Q.D Enamel Bronze', 'LIGHT BRONZE': 'Q.D Enamel Bronze',
            'BURGUNDY': 'Q.D Enamel Burgundy',
            'CAT YELLOW': 'Q.D Enamel Cat Yellow',
            'COPPER': 'Q.D Enamel Copper',
            'DARK GREY': 'Q.D Enamel Dark Grey', 'GREY': 'Q.D Enamel Dark Grey',
            'CHARCOAL GREY': 'Q.D Enamel Dark Grey', 'CHARCOAL': 'Q.D Enamel Dark Grey',
            'G BROWN': 'Q.D Enamel G Brown',
            'PWD BROWN': 'Q.D Enamel PWD Brown',
            'GREEN': 'Q.D Enamel Green', 'WINDSOR GREEN': 'Q.D Enamel Green',
            'ROYAL BLUE': 'Q.D Enamel Royal Blue',
            'S RED': 'Q.D Enamel Signal Red', 'POST OFFICE RED': 'Q.D Enamel Signal Red',
            'RED': 'Q.D Enamel Signal Red',
            'CREAM': 'Q.D Enamel Burgundy',
            'SILVER': 'Q.D Enamel Silver',
        }
        return color_map.get(color_u, 'Q.D Enamel Signal Red')

    # Gripcoat Enamel
    if pname_u in ('3-IN-1 Q.D GRIP COAT', 'HYPER STEEL Q.D GRIP COAT'):
        if color_u == 'BLACK': return 'Q.D Gripcoat Enamel Black'
        if color_u == 'BRONZE': return 'Q.D Gripcoat Enamel Bronze'
        if color_u == 'WHITE': return 'Q.D Gripcoat Enamel White'
        return None

    # Q.D primers
    if pname_u in ('Q.D OXIDE PRIMER', 'Q D OXIDE PRIMER', 'HYPER STEEL Q.D RED OXDE PRIMER',
                   'HYPER STEEL Q.D RED PRIMER', 'HYPER STEEL QD OXIDE', 'Q.DBLACK OXIDE PRIMER'):
        return 'QD Red Oxide Primer'
    if pname_u in ('QD GREY OXIDE PRIMER', 'HYPERSTEEL Q.D OXIDE PRIMER', 'QD PRIMER',
                   'Q.D GREY PRIMER', 'Q.DGREY PRIMER', 'HYPER STEEL Q.D GREY PRIMER'):
        return 'QD Grey Oxide Primer'

    # FLAT ENAMEL proxy
    if pname_u == 'FLAT ENAMEL':
        return 'Eggshell Enamel White' if color_u == 'WHITE' else 'Eggshell Enamel Cream'

    # Explicitly unmapped
    return None


def _route_with_fallbacks(pname_u, color_u, size_n):
    """Return ordered list of candidate Sheet2 product names."""
    primary = _route(pname_u, color_u)
    if primary is None:
        return []
    candidates = [primary]

    if pname_u == 'HIGH GLOSS ENAMEL':
        if primary == 'High Gloss Peach / Cream / Golden Brown':
            candidates.append('High Gloss Colours')
        elif primary == 'High Gloss White':
            candidates.append('High Gloss White/Black')

    if pname_u == 'ULTIMATE SHINE':
        if primary == 'Ulitmate Shine Cream':
            candidates.append('Ulitmate Shine Colours')
        elif primary == 'Ulitmate Shine White':
            candidates.append('Ulitmate Shine White/Black')

    if pname_u == 'EGGSHELL ENAMEL':
        if primary == 'Eggshell Enamel Cream':
            candidates.append('Eggshell Enamel White')

    if pname_u in ('Q.D ENAMEL', 'Q.D ENAMEL (PLAIN)', 'HYPER STEEL Q.D ENAMEL'):
        if primary == 'Q.D Enamel Bronze':
            candidates.append('QD Bronze')

    return candidates


def lookup(product_raw, color_raw, size_raw):
    """
    Returns (price, source_label, sheet2_key_used).
    source_label is 'N' (Rock Bottom) or 'L' (Less 30) or None.
    """
    if product_raw is None:
        return (None, None, None)
    pname_u = str(product_raw).strip().upper()
    color_u = (color_raw or '').strip().upper()
    size_n = normalize_size(size_raw)

    candidates = _route_with_fallbacks(pname_u, color_u, size_n)
    if not candidates:
        return (None, None, None)

    s2_size = _route_size(pname_u, size_n)

    for s2_name in candidates:
        key = (s2_name, s2_size)
        if key in catalog:
            rock, less30 = catalog[key]
            rock = _clean_price(rock)
            less30 = _clean_price(less30)
            if rock is not None:
                return (rock, 'N', key)
            if less30 is not None:
                return (less30, 'L', key)
        # Try trailing-space variants of the name
        for (k_name, k_size), v in catalog.items():
            if k_name.strip() == s2_name and k_size == s2_size:
                rock, less30 = v
                rock = _clean_price(rock)
                less30 = _clean_price(less30)
                if rock is not None:
                    return (rock, 'N', (k_name, k_size))
                if less30 is not None:
                    return (less30, 'L', (k_name, k_size))

    return (None, None, (candidates[0], s2_size))
```

### 9.2 `build_output.py`

```python
"""Populate Sheet1 (2) column X with matched prices and write audit columns."""
import shutil
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from price_lookup import lookup

SRC = '/home/claude/input.xlsx'
DST = '/home/claude/Rock_Bottom_Prices_Populated.xlsx'

shutil.copy(SRC, DST)
wb = load_workbook(DST)  # NOT data_only=True (would destroy formulas)
ws = wb['Sheet1 (2)']

header_font = Font(name='Arial', bold=True)
ws.cell(row=1, column=24).font = header_font
ws.cell(row=1, column=25, value='Matched Sheet2 Product').font = header_font
ws.cell(row=1, column=26, value='Matched Sheet2 Size').font = header_font
ws.cell(row=1, column=27, value='Price Source').font = header_font

yellow_fill = PatternFill('solid', start_color='FFF4CC')

matched_n = matched_l = unmatched = 0
for r in range(2, ws.max_row + 1):
    pname = ws.cell(row=r, column=3).value
    color = ws.cell(row=r, column=4).value
    size = ws.cell(row=r, column=10).value
    if pname is None:
        continue

    price, source, key = lookup(pname, color, size)
    if price is not None:
        ws.cell(row=r, column=24, value=round(float(price), 2))
        if key is not None:
            ws.cell(row=r, column=25, value=key[0])
            ws.cell(row=r, column=26, value=key[1])
        ws.cell(row=r, column=27, value='N (Rock Bottom)' if source == 'N' else 'L (Less 30)')
        if source == 'N':
            matched_n += 1
        else:
            matched_l += 1
    else:
        ws.cell(row=r, column=24).fill = yellow_fill
        ws.cell(row=r, column=27, value='NO MATCH')
        ws.cell(row=r, column=27).fill = yellow_fill
        if key is not None:
            ws.cell(row=r, column=25, value=f"(tried: {key[0]})")
            ws.cell(row=r, column=26, value=f"(tried: {key[1]})")
        unmatched += 1

for r in range(2, ws.max_row + 1):
    ws.cell(row=r, column=24).number_format = 'R #,##0.00;[Red]-R #,##0.00'

ws.column_dimensions['X'].width = 12
ws.column_dimensions['Y'].width = 42
ws.column_dimensions['Z'].width = 18
ws.column_dimensions['AA'].width = 18
ws.freeze_panes = 'A2'

wb.save(DST)
print(f"Matched N: {matched_n}, Matched L: {matched_l}, Unmatched: {unmatched}")
```

---

## 10. Expected output statistics (baseline)

When run against `Updated_Rock_Bottom_-_All_Products_23042026.xlsx`:

- **Total rows processed:** 1,200
- **Matched via Rock Bottom (N):** 478
- **Matched via Less 30 (L) fallback:** 586
- **Unmatched (no price):** 136
- **Total match rate:** 88.7%

If numbers drift by more than ±5 for a similarly-sized dataset, investigate before delivering — something has changed in the source data.

---

## 11. Output artefact specification

1. **Path:** `/mnt/user-data/outputs/Rock_Bottom_Prices_Populated.xlsx`
2. **Structure:** Exact copy of input, with four changes on `Sheet1 (2)`:
   - Col X (Price): populated with matched price, ZAR-formatted (`R #,##0.00`)
   - Col Y (Matched Sheet2 Product): audit — which bracket was used
   - Col Z (Matched Sheet2 Size): audit — which size was used
   - Col AA (Price Source): `N (Rock Bottom)` | `L (Less 30)` | `NO MATCH`
3. **Unmatched rows:** Highlighted with soft yellow fill (`#FFF4CC`) on Price and Price Source cells.
4. **Header row:** Frozen, bold, Arial font.
5. `sheet1` and `Sheet2` are preserved unchanged.

---

## 12. Reproducibility checklist

For an AI assistant executing this playbook against a new monthly snapshot:

- [ ] Read `xlsx` SKILL.md before touching any spreadsheet
- [ ] Copy input to `/home/claude/input.xlsx` — never modify the upload
- [ ] Verify three sheets present: `sheet1`, `Sheet2`, `Sheet1 (2)` (fuzzy-match names if renamed)
- [ ] Verify `Sheet2` col N = "Rock Bottom Price" and col L = "Less 30 Max"
- [ ] Verify `Sheet1 (2)` col C = Product Name, col D = Color, col J = Size, col X = Price
- [ ] Load `price_lookup.py` and `build_output.py` from this doc
- [ ] Run build; capture match statistics
- [ ] Spot-check 10+ samples across colour variants (White, Cream, Black, coloured) — prices must align with the bracket rules in section 6
- [ ] Verify unmatched count is within ±5 of baseline; if not, investigate product-routing changes
- [ ] Save to `/mnt/user-data/outputs/` with date-suffixed filename
- [ ] `present_files` to deliver

---

## 13. When to extend this playbook

Update this document when:

- **New products added to Sheet2:** add to section 6 routing table
- **New colour variants in Sheet1 (2):** add to colour routing if a White/Cream variant appears; default to Colours bracket otherwise
- **Sheet2 size gaps filled in:** remove relevant fallback from section 7
- **User reports a mispriced SKU:** trace through the routing table, identify the faulty rule, update section 6 or 7, re-run, and record the change here with a date

---

*Last updated: 23 April 2026 — initial baseline from `Updated_Rock_Bottom_-_All_Products_23042026.xlsx`.*
