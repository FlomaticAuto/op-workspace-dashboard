# Olympic Paints — Business Context
# Passed to every sub-agent on every invocation

---

## COMPANY

**Legal name:** K & K Paint Manufacturers CC
**Trading name:** Olympic Paints
**Location:** Lenasia, Gauteng, South Africa
**Type:** Paint manufacturer — produces and sells its own branded paint products

---

## PEOPLE

**Quintus Lategan** — Sales Manager (the person you work for)

**Factory / Operations supervisors:**
- Jagdish — Factory Floor, Production & Returns Supervisor
- Hiren — Inventory Control & Stock Supervisor
- Mukesh — Production Supervisor – Enamel
- Nikil — Dispatch Supervisor
- Masingita — Safety Liaison / Assistant

**Office colleagues:**
- Sejal Purbhoo
- Nikhil Panchal
- Kishan Morar
- Sumit

---

## SYSTEMS

| System | Purpose | Owner |
|---|---|---|
| **Zoho CRM** | Sales pipeline, customer records, B2B outreach, stockist management | Quintus |
| **PAD** | Orders, invoices, delivery notes, dispatch (operational system — NOT the CRM) | Operations |
| **AWS QuickSight** | All dashboards and reporting | Quintus / Flowmatic |
| **JotForm** | Kiosk and factory floor forms | Operations |
| **Zoho Books** | Finance, invoicing, reconciliation (GLB-01 scope — not handled here) | Finance |

**CRITICAL:** PAD and Zoho CRM are separate systems. PAD handles operational documents. Zoho CRM handles sales relationships. Do not conflate them.

---

## RUNBOOKS — AUTHORITATIVE PROCEDURES

Every scheduled or recurring automation has a runbook at `3.Resources/19. Runbooks/`. Index: `RUNBOOKS.md`. Template: `_template.md` (Purpose / How it runs / Inputs / Outputs / Known failure modes / Logs / Manual run / Recent incidents).

**Rule for every agent:** if the task you've been handed touches a job that has a runbook, the runbook is the source of truth. Read it before acting. After material changes, update `Last verified` and append to `Recent incidents`. Do not improvise around documented procedures — fix the runbook instead.

---

## DISTRIBUTION & SALES MODEL

- Primary channel: B2B wholesale to hardware stores, paint stockists, and dealers
- Key account type: independent hardware stores and building supply retailers
- Notable account: Boxer Build (hardware retail chain)
- Geographic focus: Gauteng-based operations; national reach via stockist network

---


## PRODUCT RANGE

<!-- AUTO-GENERATED from Olympic Paints SKU master list. Last updated: April 2026 -->
<!-- Format: Product Name — Sub-category | Available Sizes -->

---

### PVA Paints

- **7-IN-1 ACRYLIC PVA** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **ACORNHOEK PVA** — Wall Paint (PVA/Acrylic) | Sizes: 20L
- **BEST BUILD PVA** — Wall Paint (PVA/Acrylic) | Sizes: 20L
- **DECOR** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **ECLIPSE PVA** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **HI HIDING CONT PVA** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **JUST PAINT WALL** — Economy Wall Paint | Sizes: 20L
- **KALAHARI CONTRACTORS** — Contractor Wall Paint | Sizes: 5L, 20L
- **LIBERTY PVA** — Wall Paint (PVA/Acrylic) | Sizes: 20L
- **MADALAS CHOICE PVA** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **MASTER DECORATORS** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **NATURAL ELEGANCE** — Premium Wall Paint | Sizes: 5L, 20L
- **RUGGED BEAUTY** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **SUBURBAN BLISS** — Wall Paint (PVA/Acrylic) | Sizes: 5L, 20L
- **ULTIMATE SHINE BASE** — Clear Base | Sizes: 5L
- **VERSA PVA** — Wall Paint (PVA/Acrylic) | Sizes: 20L

---

### Enamel (Solvent-Based)

- **EGGSHELL ENAMEL** — Eggshell Finish | Sizes: 1L, 5L, 20L
- **FLAT ENAMEL** — Matt Finish | Sizes: 1L, 5L, 20L
- **HIGH GLOSS ENAMEL** — High Gloss Finish | Sizes: 500ML, 1L, 5L, 20L
- **PICK 'N SAVE ECONO** — Economy Enamel | Sizes: 1L, 5L, 20L
- **ULTIMATE SHINE** — Premium Gloss | Sizes: 500ML, 1L, 5L, 20L

---

### QD Enamel (Quick-Dry)

- **3-IN-1 Q.D GRIP COAT** — Primer / Undercoat / Topcoat | Sizes: 5L
- **HYPER STEEL Q.D ENAMEL** — Industrial QD Enamel | Sizes: 1L, 5L
- **HYPER STEEL Q.D GREY PRIMER** — QD Grey Primer | Sizes: 5L
- **HYPER STEEL Q.D GRIP COAT** — QD 3-in-1 System | Sizes: 5L
- **Q.D CLEAR BASE** — QD Clear Base | Sizes: 1L, 5L
- **Q.D ENAMEL** — Quick-Dry Enamel | Sizes: 1L, 5L, 20L

---

### Floor & Roof Paints

- **3-IN-1 ROOF PAINT** — Roof Coating | Sizes: 5L, 20L
- **ALKYD ROOF / STOEP** — Alkyd Roof & Stoep Paint | Sizes: 1L, 5L, 20L
- **JUST PAINT ROOF** — Economy Roof Paint | Sizes: 20L
- **PLUSH COAT** — Floor / Roof Coating | Sizes: 5L, 20L
- **STOEP** — Stoep / Floor Paint | Sizes: 5L
- **UNIVERSAL ROOF** — Universal Roof Paint | Sizes: 5L, 20L, 200L

---

### Primers & Undercoats

- **ALL IN ONE** — Multi-Purpose Primer | Sizes: 1L, 5L, 20L
- **BLACK WATER BASE OXIDE PRIMER** — Water-Based Black Oxide | Sizes: 200L
- **BONDING LIQUID** — Bonding Primer | Sizes: 1L, 5L, 20L
- **ETCH PRIMER** — Metal Etch Primer | Sizes: 1L, 5L
- **HYPER STEEL Q.D RED OXIDE PRIMER** — QD Red Oxide | Sizes: 1L, 5L
- **HYPERSTEEL Q.D OXIDE PRIMER** — QD Oxide Primer | Sizes: 1L
- **PLASTER & TILE BONDING LIQUID** — Plaster / Tile Primer | Sizes: 1L, 2.5L, 5L, 20L
- **Q.D GREY PRIMER** — QD Grey Primer | Sizes: 5L, 20L
- **Q.D OXIDE PRIMER** — QD Oxide Primer | Sizes: 1L, 5L, 20L
- **Q.D BLACK OXIDE PRIMER** — QD Black Oxide | Sizes: 1L, 5L
- **SANDING SEALER** — Wood Sealer | Sizes: 1L, 5L, 20L
- **UNIV UNDERCOAT** — Universal Undercoat | Sizes: 1L, 5L, 20L
- **WATER BASE BLACK OXIDE PRIMER** — Water-Based Oxide | Sizes: 200L
- **WATERBASE OXIDE PRIMER** — Water-Based Oxide Primer | Sizes: 1L, 5L, 20L
- **WATERBASED PLASTER PRIMER** — Plaster Primer | Sizes: 5L, 20L
- **WOOD PRIMER** — Wood Primer | Sizes: 1L, 5L, 20L
- **ZINC PHOSPHATE PRIMER** — Anti-Corrosion Primer | Sizes: 1L, 5L, 20L

---

### Waterproofing

- **DAMP FIX** — Damp-Proof Coating | Sizes: 1L, 5L
- **FIBRE RESTORE** — Fibre Repair & Waterproofing | Sizes: 1L, 5L
- **HYPER STEEL RAINPROOF** — Metal Waterproofing | Sizes: 1L, 5L
- **RAINPROOF** — General Waterproofing | Sizes: 1L, 5L

---

### Specialised Coatings

- **FACE BRICK** — Exterior Face Brick Sealer | Sizes: 1L, 5L, 20L
- **ROAD MARKING** — Traffic / Road Marking Paint | Sizes: 1L, 5L, 20L
- **SCHOOL BOARD** — Chalkboard Paint | Sizes: 1L, 5L

---

### Woodcare

- **VARNISH** — Interior/Exterior Varnish | Sizes: 500ML, 1L, 5L

---

### Putty & Fillers

- **CRACK FILLER** — Wall Crack Filler | Sizes: 500GM, 2KG, 5KG, 10KG, 20KG
- **PUTTY** — Glazing / Stopping Putty | Sizes: 1KG, 2KG, 5KG, 10KG, 20KG, 40KG

---

### General / Sundries

- **AEROSOL** — Aerosol Spray Paint | Sizes: Various
- **BLUE OXIDE** — Blue Oxide Pigment | Sizes: 500GM
- **DISTEMPER** — Interior Distemper | Sizes: 2KG
- **GALVANISED IRON CLEANER** — Surface Prep | Sizes: 1L, 5L
- **OXIDE / RED OXIDE** — Oxide Pigment | Sizes: 500GM, 5KG, 10KG, 20KG, 40KG
- **PLASTER & TILE BOND** — Bonding Agent | Sizes: Various
- **STAINERS** — Universal Tinting Stainers | Sizes: 50ML, 100ML

---

### Accessories & Tools

- **CARBOLINEUM** — Wood Preservative | Sizes: 750ML, 5L
- **DROP SHEET** — Painter's Drop Sheet | Sizes: 2M x 3M
- **LACQUER THINNERS** — Solvent Thinner | Sizes: 750ML, 5L, 200L
- **MASKING TAPE** — Painter's Masking Tape | Sizes: 18mm, 24mm, 36mm x 40M
- **MEMBRANE** — Waterproofing Membrane | Sizes: 75MM, 200MM
- **PAINT BRUSH** — Bristle / Plastic Brushes | Sizes: 25MM, 38MM, 100MM
- **PAINT REMOVER** — Chemical Stripper | Sizes: 750ML
- **PLATINUM PAINT ROLLER** — Paint Roller | Sizes: 225MM
- **RAW LINSEED OIL** — Linseed Oil | Sizes: 750ML, 5L
- **RUST REMOVER** — Rust Treatment | Sizes: 1L, 5L
- **SANDGRIT PAPER** — Abrasive Paper | Sizes: 40#, 60#, 80# x 1M
- **SPIRIT OF SALTS** — Hydrochloric Acid Cleaner | Sizes: 750ML, 5L
- **TURPENTINE** — Mineral Turpentine | Sizes: 750ML, 5L

---

## PRICING

- Price list is managed in the sales context via Zoho CRM (STRIKER's domain)
- Operational pricing (invoices, delivery notes) is handled in PAD
<!-- Source: Olympic Paints 2025 Price List. All prices in ZAR (excl. VAT) -->
<!-- Discount structure available on full price list. This table shows List Price (ceiling) and Rock Bottom (floor). -->
<!-- PRICING POLICY: Standard discount tiers run from 10% to 30%. Rock Bottom is the absolute floor — never quote below this. -->
<!-- A 10% price increase was applied effective April 2026. These are the 2025 base figures — adjust accordingly. -->

| Product | Size | List Price (2025) | Rock Bottom Floor |
|---------|------|:-----------------:|:-----------------:|
| 3 in 1 Roof Paint | 20LT | R 1 009.80 | R 727.06 |
| 3 in 1 Roof Paint | 5LT | R 285.12 | R 205.29 |
| 7 in 1 Acrylic PVA | 20LT | R 1 009.80 | R 727.06 |
| 7 in 1 Acrylic PVA | 5LT | R 285.12 | R 205.29 |
| Bonding Liquid | 1LT | R 101.92 | R 73.38 |
| Bonding Liquid | 5LT | R 398.72 | R 287.08 |
| Carbolineum | 750ML X 12 | R 378.00 | R 272.16 |
| Carbolineum | 5LT | R 216.00 | R 155.52 |
| Crack Filler | 10Kg | R 277.17 | R 199.56 |
| Crack Filler | 2Kg X 12 | R 723.87 | R 521.19 |
| Crack Filler | 500Gr X 24 | R 682.09 | R 491.10 |
| Crack Filler | 5Kg | R 146.21 | R 105.27 |
| Damp Fix | 1LT | R 110.68 | R 79.69 |
| Damp Fix | 5LT | R 373.71 | R 269.07 |
| Distemper Colours | 2Kg X 6 | R 200.86 | R 144.62 |
| Décor Colours | 20LT | R 455.83 | R 328.20 |
| Décor Colours | 5LT | R 131.34 | R 94.57 |
| Décor White / Cream | 20LT | R 432.65 | R 311.50 |
| Décor White / Cream | 5LT | R 115.89 | R 83.44 |
| Eclipse Colours | 20LT | R 293.58 | R 211.38 |
| Eclipse Colours | 5LT | R 105.06 | R 75.64 |
| Eclipse White / Cream | 20LT | R 273.49 | R 196.92 |
| Eclipse White / Cream | 5LT | R 97.34 | R 70.09 |
| Eggshell Enamel Cream | 1LT | R 134.87 | R 97.11 |
| Eggshell Enamel Cream | 5LT | R 539.84 | R 388.69 |
| Eggshell Enamel White | 1LT | R 130.62 | R 94.04 |
| Eggshell Enamel White | 20LT | R 1 929.58 | R 1 389.30 |
| Eggshell Enamel White | 5LT | R 500.61 | R 360.44 |
| Face-Brick Dressing | 1LT | R 101.92 | R 73.38 |
| Face-Brick Dressing | 20LT | R 1 335.69 | R 961.70 |
| Face-Brick Dressing | 5LT | R 398.76 | R 287.10 |
| Field Marking Paint White | 1LT | R 98.01 | R 70.57 |
| Field Marking Paint White | 20LT | R 1 140.48 | R 821.15 |
| Field Marking Paint White | 5LT | R 350.46 | R 252.33 |
| Galvanised Iron Cleaner & Degreaser | 1LT | R 61.81 | R 44.50 |
| Galvanised Iron Cleaner & Degreaser | 1LT X 12 | R 664.42 | R 478.38 |
| Galvanised Iron Cleaner & Degreaser | 5LT | R 246.45 | R 177.44 |
| Hi-Hiding Super Acrylic Cont. PVA White | 20LT | R 618.07 | R 445.01 |
| Hi-Hiding Super Acrylic Cont. PVA White | 5LT | R 190.08 | R 136.86 |
| High Gloss Colours | 1LT | R 113.18 | R 81.49 |
| High Gloss Colours | 500ML | R 66.45 | R 47.84 |
| High Gloss Colours | 5LT | R 417.19 | R 300.38 |
| High Gloss Peach / Cream / Golden Brown | 20LT | R 1 406.10 | R 1 012.39 |
| High Gloss White | 20LT | R 1 359.74 | R 979.02 |
| High Gloss White/Black | 1LT | R 98.20 | R 70.71 |
| High Gloss White/Black | 500ML | R 61.81 | R 44.50 |
| High Gloss White/Black | 5LT | R 360.03 | R 259.22 |
| Kalahari Contractors Colours | 20LT | R 548.53 | R 394.94 |
| Kalahari Contractors Colours | 5LT | R 169.96 | R 122.37 |
| Kalahari Contractors White / Cream | 20LT | R 525.35 | R 378.25 |
| Kalahari Contractors White / Cream | 5LT | R 154.51 | R 111.25 |
| Liberty White/Cream | 20LT | R 262.67 | R 189.12 |
| Master Decorators Colours | 20LT | R 772.58 | R 556.25 |
| Master Decorators Colours | 5LT | R 228.67 | R 164.64 |
| Master Decorators White/Cream | 20LT | R 740.14 | R 532.90 |
| Master Decorators White/Cream | 5LT | R 208.60 | R 150.19 |
| Membrane Large | 200MM | R 61.19 | R 44.05 |
| Membrane Small | 75MM | R 39.94 | R 28.76 |
| One ETCH Primer Black | 1LT | R 135.97 | R 97.90 |
| One ETCH Primer Black | 5LT | R 479.00 | R 344.88 |
| Oxide Green/Blue | 500Gr X 24 | R 633.51 | R 456.13 |
| Oxide Green/Blue | 5Kg | R 286.39 | R 206.20 |
| Oxide Red/Black | 500Gr X 24 | R 200.86 | R 144.62 |
| Oxide Red/Black | 5Kg | R 82.85 | R 59.65 |
| Oxide Yellow/Brown | 500Gr X 24 | R 231.77 | R 166.88 |
| Oxide Yellow/Brown | 5Kg | R 95.60 | R 68.84 |
| Paint Remover | 750ML | R 108.16 | R 77.87 |
| Paint Remover | 750ML X 12 | R 1 143.92 | R 823.62 |
| Pick and Save Colours | 1LT | R 91.80 | R 66.10 |
| Pick and Save Colours | 5LT | R 334.80 | R 241.06 |
| Pick and Save Peach | 20LT | R 1 128.60 | R 812.59 |
| Pick and Save White / Cream | 1LT | R 88.51 | R 63.72 |
| Pick and Save White / Cream | 20LT | R 1 280.85 | R 922.21 |
| Pick and Save White / Cream | 5LT | R 331.45 | R 238.65 |
| Pink Wood Primer | 1LT | R 125.41 | R 90.29 |
| Pink Wood Primer | 5LT | R 475.09 | R 342.07 |
| Plaster & Tile Bond | 1 X 12 | R 679.87 | R 489.51 |
| Plaster & Tile Bond | 2.5LT | R 105.06 | R 75.64 |
| Plaster & Tile Bond | 20LT | R 687.60 | R 495.07 |
| Plaster & Tile Bond | 5LT | R 183.88 | R 132.39 |
| Platinum Plus All-in-one Protector | 20LT | R 1 486.40 | R 1 070.21 |
| Platinum Plus All-in-one Protector | 5LT | R 432.10 | R 311.11 |
| Platinum Plus Fibre Restore | 1LT | R 103.67 | R 74.65 |
| Platinum Plus Fibre Restore | 5LT | R 406.22 | R 292.48 |
| Platinum Plus Natural Elegance Colours | 20LT | R 1 688.19 | R 1 215.50 |
| Platinum Plus Natural Elegance Colours | 5LT | R 475.03 | R 342.03 |
| Platinum Plus Natural Elegance White | 20LT | R 1 604.59 | R 1 155.31 |
| Platinum Plus Natural Elegance White | 5LT | R 445.80 | R 320.97 |
| Platinum Plus Plush Coat Colours | 20LT | R 1 147.38 | R 826.12 |
| Platinum Plus Plush Coat Colours | 5LT | R 333.24 | R 239.93 |
| Platinum Plus Plush Coat Green/Emu Green | 20LT | R 1 205.85 | R 868.21 |
| Platinum Plus Plush Coat Green/Emu Green | 5LT | R 355.18 | R 255.73 |
| Platinum Plus Rugged Beauty Colours | 20LT | R 1 059.69 | R 762.98 |
| Platinum Plus Rugged Beauty Colours | 5LT | R 305.49 | R 219.95 |
| Platinum Plus Rugged Beauty White | 20LT | R 1 037.76 | R 747.19 |
| Platinum Plus Rugged Beauty White | 5LT | R 290.87 | R 209.43 |
| Platinum Plus Suburban Bliss Colours | 20LT | R 1 162.00 | R 836.64 |
| Platinum Plus Suburban Bliss Colours | 5LT | R 328.86 | R 236.78 |
| Platinum Plus Suburban Bliss White | 20LT | R 1 125.45 | R 810.33 |
| Platinum Plus Suburban Bliss White | 5LT | R 314.26 | R 226.27 |
| Putty | 10Kg | R 130.68 | R 94.09 |
| Putty | 1kg X 24 | R 332.64 | R 239.50 |
| Putty | 20Kg | R 249.48 | R 179.63 |
| Putty | 2Kg X 12 | R 314.82 | R 226.67 |
| Putty | 40Kg | R 469.26 | R 337.87 |
| Putty | 5Kg | R 68.90 | R 49.61 |
| Q.D Enamel Bronze | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Bronze | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Burgundy | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Burgundy | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Cat Yellow | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Cat Yellow | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Copper | 1LT | R 120.00 | R 86.40 |
| Q.D Enamel Copper | 5LT | R 500.00 | R 360.00 |
| Q.D Enamel Dark Grey | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Dark Grey | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel G Brown | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel G Brown | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Green | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Green | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel JD Green | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel JD Green | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel PWD Brown | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel PWD Brown | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Royal Blue | 1LT | R 120.00 | R 86.40 |
| Q.D Enamel Royal Blue | 5LT | R 500.00 | R 360.00 |
| Q.D Enamel Signal Red | 1LT | R 100.00 | R 72.00 |
| Q.D Enamel Signal Red | 5LT | R 400.00 | R 288.00 |
| Q.D Enamel Silver | 1LT | R 120.00 | R 86.40 |
| Q.D Enamel Silver | 5LT | R 500.00 | R 360.00 |
| Q.D Gripcoat Enamel Black | 1LT | R 136.67 | R 98.40 |
| Q.D Gripcoat Enamel Black | 5LT | R 564.85 | R 406.69 |
| Q.D Gripcoat Enamel Bronze | 1LT | R 153.72 | R 110.68 |
| Q.D Gripcoat Enamel Bronze | 5LT | R 584.26 | R 420.67 |
| Q.D Gripcoat Enamel White | 1LT | R 181.44 | R 130.64 |
| Q.D Gripcoat Enamel White | 5LT | R 615.53 | R 443.18 |
| QD Enamel Black | 1LT | R 100.00 | R 72.00 |
| QD Enamel Black | 5LT | R 400.00 | R 288.00 |
| QD Enamel White | 1LT | R 100.00 | R 72.00 |
| QD Enamel White | 5LT | R 400.00 | R 288.00 |
| QD Grey Oxide Primer | 1LT | R 110.08 | R 79.26 |
| QD Grey Oxide Primer | 20LT | R 1 361.23 | R 980.09 |
| QD Grey Oxide Primer | 5LT | R 387.08 | R 278.70 |
| QD Red Oxide Primer | 1LT | R 106.00 | R 76.32 |
| QD Red Oxide Primer | 20LT | R 1 314.55 | R 946.47 |
| QD Red Oxide Primer | 5LT | R 369.05 | R 265.72 |
| Rainproof + Membrane | 1LT | R 59.79 | R 43.05 |
| Rainproof + Membrane | 5LT | R 188.85 | R 135.97 |
| Raw Linseed Oil | 5LT | R 338.41 | R 243.65 |
| Raw Linseed Oil | 750ML X 12 | R 677.55 | R 487.84 |
| Road Marking Paint White | 1LT | R 146.28 | R 105.32 |
| Road Marking Paint White | 5LT | R 622.34 | R 448.08 |
| Road Marking Paint Yellow | 1LT | R 158.39 | R 114.04 |
| Road Marking Paint Yellow | 5LT | R 689.87 | R 496.71 |
| Roof & Stoep | 1LT | R 129.62 | R 93.33 |
| Roof & Stoep | 20LT | R 1 866.68 | R 1 344.01 |
| Roof & Stoep | 5LT | R 508.70 | R 366.26 |
| Rust Remover | 1LT | R 62.95 | R 45.32 |
| Rust Remover | 1LT X 12 | R 676.72 | R 487.24 |
| Rust Remover | 5LT | R 251.01 | R 180.73 |
| Sanding Sealer | 1LT | R 106.64 | R 76.78 |
| Sanding Sealer | 5LT | R 429.78 | R 309.44 |
| Schoolboard Black | 1LT | R 129.84 | R 93.48 |
| Schoolboard Black | 5LT | R 550.82 | R 396.59 |
| Schoolboard Green | 1LT | R 135.34 | R 97.45 |
| Schoolboard Green | 5LT | R 577.57 | R 415.85 |
| Stainers (Doz) | 100ML x12 | R 409.05 | R 294.52 |
| Stainers (Doz) | 50ML x 12 | R 218.86 | R 157.58 |
| Stainers (Doz) Violet | 100ML x12 | R 501.72 | R 361.23 |
| Stainers (Doz) Violet | 50ML x 12 | R 252.76 | R 181.99 |
| Thinners | 750ML X 12 | R 385.00 | R 277.20 |
| Thinners | 5LT | R 220.00 | R 158.40 |
| Turpentine | 750ML X 12 | R 314.77 | R 226.63 |
| Turpentine | 5LT | R 136.93 | R 98.59 |
| Ulitmate Shine Colours | 1LT | R 146.36 | R 105.38 |
| Ulitmate Shine Colours | 500ML | R 84.67 | R 60.96 |
| Ulitmate Shine Colours | 5LT | R 545.29 | R 392.61 |
| Ulitmate Shine Cream | 20LT | R 1 885.22 | R 1 357.36 |
| Ulitmate Shine White | 20LT | R 1 814.46 | R 1 306.41 |
| Ulitmate Shine White/Black | 1LT | R 133.77 | R 96.32 |
| Ulitmate Shine White/Black | 500ML | R 79.10 | R 56.95 |
| Ulitmate Shine White/Black | 5LT | R 508.05 | R 365.80 |
| Universal Roof Colours | 20LT | R 1 004.88 | R 723.51 |
| Universal Roof Colours | 5LT | R 297.74 | R 214.37 |
| Universal Roof Green / Emu Green / Albany / Ocean Blue | 20LT | R 1 040.60 | R 749.23 |
| Universal Roof Green / Emu Green / Albany / Ocean Blue | 5LT | R 320.08 | R 230.46 |
| Universal Undercoat | 1LT | R 114.39 | R 82.36 |
| Universal Undercoat | 20LT | R 1 683.86 | R 1 212.38 |
| Universal Undercoat | 5LT | R 454.08 | R 326.93 |
| Varnish Colours | 1LT | R 132.00 | R 95.04 |
| Varnish Colours | 500ML | R 82.50 | R 59.40 |
| Varnish Colours | 5LT | R 453.30 | R 326.37 |
| Varnish Copal | 1LT | R 115.50 | R 83.16 |
| Varnish Copal | 500ML | R 77.00 | R 55.44 |
| Varnish Copal | 5LT | R 387.43 | R 278.95 |
| Water Based Plaster Primer | 20LT | R 660.00 | R 475.20 |
| Water Based Plaster Primer | 5LT | R 220.00 | R 158.40 |
| Water Based Red Oxide Primer | 1LT | R 86.56 | R 62.33 |
| Water Based Red Oxide Primer | 20LT | R 1 022.95 | R 736.52 |
| Water Based Red Oxide Primer | 5LT | R 322.63 | R 232.29 |
| Zinc Phosphate Primer Green | 1LT | R 120.97 | R 87.10 |
| Zinc Phosphate Primer Green | 20LT | R 1 716.99 | R 1 236.23 |
| Zinc Phosphate Primer Green | 5LT | R 476.77 | R 343.28 |

---

## KEY ACCOUNTS & STOCKISTS

## KEY STOCKIST DIRECTORY

<!-- Source: Olympic Paints CRM — Active accounts only. Flagged/inactive accounts excluded. -->
<!-- Format: Company ID | Account Name | Delivery branches indented below parent -->
<!-- Sales cycle weeks determine visit/call frequency for route planning. -->

**Total accounts:** 404 parent accounts | 100 delivery/branch points

### Week 1 — 175 accounts

- **KA002** | Angamia Building Material
- **KA008** | Safu Building Material *(+2 delivery points)*
  - KA008/1 | Aa Hardware 3 - Dzwerani Village
  - KA008/2 | Aa Hardware 2-Mahematshene
- **KA014** | Ayob'S Hardware
- **KA030** | Hassan & Sons Hardware
- **KA031** | Ash Building Supplies
- **KA050** | Fountain Square Trading 129Cc
- **KA055** | A K Distributors (Pty) Ltd
- **KA057** | Abies Security Gates
- **KA060** | Golden Hardware And Paint
- **KA077** | African Business Solutions
- **KA082** | Ashrafi Hardware
- **KA090** | A A Owaish Maize Depot Pty Ltd -   U Save Randzus Complex *(+1 delivery point)*
  - KA090/1 | A A Owaish Maize Depot Pty Ltd - Next TO Boxer HW
- **KA101** | Ad Fancy Goods T/A
- **KA102** | Aym Enterprises Pty Lyd
- **KA108** | Azhari Auto Spares
- **KA115** | Amin Supermarket T/A Ayat Hw
- **KB003** | New Best Build Hardware
- **KB007** | Assasi Bhams Investments (Pty)
- **KB011** | Brits Hardware Cc
- **KB013** | New Bafana Bafana H/Ware-MUTALE *(+1 delivery point)*
  - KB013/2 | New Bafana Bafana H Ware -Mulale
- **KB022** | Bethani Hardware
- **KB044** | Border Plumbing & Hardware
- **KB077** | Baps  Mayfair
- **KB082** | Bobras  Hardware
- **KB086** | Best Build Hardware  Elim
- **KB098** | Bismillah Hardware
- **KB105** | Baps Lenasia
- **KB111** | Baps Laudium
- **KB112** | Big On Hw T/A Phutas Mica Rain
- **KB113** | Burj Khalifa Properties (Pty)
- **KC013** | Central Building Supplies
- **KC029** | Choice Build Hardware
- **KC034** | Capstone 1456Cc
- **KC053** | Choice Build Hardware Siloam
- **KC054** | Choice Build Matanda
- **KC055** | Ckw Life Style (Pty) Ltd
- **KD001** | Dainty'S Wholesale Hardware
- **KD002** | Dhaval Patel Ent
- **KD024** | Darul Uloom Zakariyya
- **KD058** | Discount Build Hardware
- **KE001** | Ekhaya Hardware
- **KE005** | Easy Build Hardware - Mabopane *(+1 delivery point)*
  - KE005/1 | Easy Build Hardware - Olivenhoutsbosch
- **KE008** | Easy Build - Morula
- **KE009** | Easy Build - Laudium
- **KE010** | Easy Build Soweto
- **KE012** | Easy Build Hardware - Klipgat
- **KE016** | Eeezee Foam (Pty) Ltd
- **KE018** | Thamarah Pty Ltd
- **KE023** | Easy Build Hardware Jubilee
- **KE024** | Ridder Street General Dealer
- **KE035** | Easytile & Sanware
- **KE037** | Epic Foods (Pty) Ltd
- **KE040** | Exclusive Wholesalers
- **KF028** | Fayaz  And Brother 891 Pty Ltd
- **KF033** | 241 Fairview
- **KG004** | Gani Osman (Pty) Ltd
- **KG015** | Gani Osman Building Supplies
- **KG030** | Grootvlei Hardware
- **KG035** | Gayatri Paper Mills
- **KG037** | Genprint & Pack Davidson Road
- **KH004** | Hardware Centre
- **KH013** | Henque 3481 Cc *(+1 delivery point)*
  - KH013/1 | Henque 3481 Builders Mecca
- **KH032** | Hardware Hub
- **KH039** | House It Cash & Carry Cc
- **KH050** | Hope And Harmony Projects
- **KI010** | I.Build Hardware
- **KI013** | Incapeace Trading & Projects89
- **KI016** | Iconic Hardware
- **KJ019** | Jiva Auto Paints
- **KJ020** | J.M  Supermarket
- **KK011** | Kph Trading Cc
- **KK021** | Kit Kat Group (Pty) Ltd *(+2 delivery points)*
  - KK021/1 | Kit Kat Group (Pty) Ltd - Kliptown
  - KK021/2 | Kit Kat Group (Pty) Ltd - Benoni
- **KK022** | Kit Kat Group (Pty) Ltd - Silverton
- **KK039** | Key 2 Africa Wholesalers (Pty)
- **KL004** | World Focus1932 Cc *(+2 delivery points)*
  - KL004/1 | World Focus 1932 Cc
  - KL004/2 | Power Build - Mutale
- **KL020** | Light Centre And Hardware
- **KL023** | Lakha 786 Rs Pty Ltd T/A M.A H *(+1 delivery point)*
  - KL023/2 | Rabali Hardware
- **KL048** | Living Inspired Interiors
- **KM001** | Mega Doors And Paint  Hardware
- **KM004** | Magezi Hardware *(+1 delivery point)*
  - KM004/1 | Magezi Hw Wholesale Village
- **KM007** | Marshall Hardware & Furniture
- **KM022** | Makhumi S/Market T/A Mambose H
- **KM027** | Maliks Paint & Hardware *(+23 delivery points)*
  - KM027/1 | IMFA HARDWARE - RANDFONTEIN
  - KM027/10 | Taung Hardware
  - KM027/12 | Chief Steel & Hardware - Carltonville
  - KM027/13 | Chief Steel & Hw - Cosmo City
  - KM027/14 | Chief Steel & Hw - Virginia
  - KM027/15 | Chief Steel & Hardware - Khuma
  - KM027/16 | Power Build - Krugersdorp
  - KM027/17 | Discount Hardware Kanyamazane
  - KM027/18 | Discount Hw Homebuild
  - KM027/2 | Imfa Hardware - MAIN REEF ROAD
  - KM027/20 | Discount Hardware - Hazyview
  - KM027/21 | Power Build - Soweto
  - KM027/22 | Khutsong Hardware & Steel
  - KM027/23 | Discount Home Build
  - KM027/24 | Jane Furse Building Supply
  - KM027/25 | Jane Furse Cash & Carry
  - KM027/3 | Randfontein Hardware
  - KM027/4 | Active Build
  - KM027/5 | Power Build - Azaadville
  - KM027/6 | Power Build - KAGISO
  - KM027/7 | Power Build - Roodepoort
  - KM027/8 | Power Build Cosmo City
  - KM027/9 | Rank Hardware
- **KM031** | Mica Hardware - Purple Rain
- **KM043** | Goldville S/M T/A Meem H/Ware
- **KM044** | Overland Blyvoor
- **KM048** | A A Hardware 2
- **KM053** | Dr Build Hardware
- **KM070** | Max Hardware
- **KM077** | Manglasi Hardware
- **KM083** | Diy  Lindley
- **KM085** | Mpisani General Dealers
- **KM088** | Mukula Hardware
- **KM098** | Mahriya General Trading Cc
- **KM126** | Manjra Hardware
- **KM130** | Hansoty Holdings 03 (Pty) Ltd
- **KM151** | Medi Print
- **KM156** | Mohan Hira
- **KM160** | Mr Build Musina (Pty) Ltd
- **KM162** | Makro Sa Market Place
- **KM164** | Mas Hardware
- **KN010** | Northam Hardware
- **KN014** | Norman Buildling Material
- **KN021** | New Magic Build
- **KN032** | Narayan Properties
- **KN034** | Nu Shop Hardware
- **KO004** | Olympic Resins
- **KO005** | Olympic Inspiration Studio (Pt
- **KO011** | One Day Only
- **KP018** | Khotawala 786 Traders Cc *(+1 delivery point)*
  - KP018/1 | Khotawala 786 Traders Ta
- **KP022** | Perfect Build & Hardware
- **KP029** | Paragon Design
- **KP030** | Platinum Distribution Centre *(+1 delivery point)*
  - KP030/1 | Platinum Rainbow Hardware
- **KP048** | P Shah
- **KP058** | Paint Max - Commissoners Street *(+1 delivery point)*
  - KP058/1 | Paint Max - Annan Road
- **KP059** | Prime Build
- **KP060** | Pepper Tree Lane Body Corporat
- **KP063** | Projo Projects
- **KQ005** | Qwa Qwa H/W-T/A Mica Hardware
- **KQ009** | Keystone Diy (Pty) Ltd
- **KQ012** | Sembro Hardware T/A Concrete &
- **KR027** | Faizaan General Tradings T/A
- **KR032** | Raj Signs
- **KR034** | Jeelani Investment T/A Matanda
- **KR040** | Rose Hip Propertiess 9
- **KR043** | Roshnee Primary School
- **KS004** | S.E.Z. Superette
- **KS005** | Skeerpoort Handelhuis
- **KS007** | Star Hardware
- **KS017** | Femac Hyper Ta Spaza Hyper
- **KS023** | Cash Sale
- **KS038** | Sams Hardware
- **KS044** | Sayed'S Ind. Supplies Pty Ltd
- **KS045** | Siloam Hardware
- **KS046** | Scenic Route Trading 580 Cc
- **KS048** | Elim Hardware & Supermarket
- **KS049** | Shayona Foundation
- **KS052** | Oriant Invest T/A Smart Build
- **KS060** | Cash Suspense Account
- **KS061** | Safari Hardware (Pty) Ltd *(+1 delivery point)*
  - KS061/1 | Safari Hardware
- **KS089** | S.A. Hardware (Makhado)
- **KS103** | Sameer It
- **KS106** | Jaiba Trading Pty Ltd-Sabri Ha
- **KS107** | Soolimans Furnitures Cc
- **KS108** | Silver Supermarket
- **KS115** | S & N Tile & Hardware
- **KS118** | Sh Hardware
- **KS119** | Sibanda 108 Construction
- **KS120** | Shriya & Yatika Investments Cc
- **KS123** | Sollys Radiator
- **KS124** | Super Electro Plumb City
- **KS126** | Shayona Properties And Investm
- **KS127** | Star Auto Paint Kliptown *(+2 delivery points)*
  - KS127/1 | Auto Paint Centre Westonarea
  - KS127/2 | Prestige Auto Paint
- **KT005** | Delli 786 T/A Tshaulu Hw
- **KT014** | Timber City *(+1 delivery point)*
  - KT014/1 | Motalas Hardware
- **KT028** | Takolias Hyper Hardware
- **KT034** | Tfs Hardware ( Qwa Qwa)
- **KT036** | Tshino Hardware
- **KT048** | Smd Electrical Plumbing And Hw
- **KT057** | Takolias Hardware Devland
- **KT061** | Total Hardware & Tiles
- **KT064** | Techni-Pro Coating Sa
- **KU007** | Ultra Safety Tint
- **KU009** | Unibiz Exports Trading
- **KV001** | Vuwani Hardware & Furniture Cc
- **KV003** | Volta Home Hardware
- **KV007** | Vendaland H/W & Furniture
- **KV010** | Ws Empire (Pty) Ltd
- **KV018** | Vantis Gift Centre Cc
- **KV020** | Sv Construction
- **KW003** | Wolhuterskop Trading
- **KW014** | Walwati Properties (Pty) Ltd
- **KY007** | Ymbm Enterorise T/A Value Hard
- **KZ007** | Z M Hardware Pty Ltd Ta Mr Hw
- **KZ011** | Z Build Khubvi

### Week 2 — 77 accounts

- **KA040** | A & S Enterprises (Pty) Ltd
- **KA058** | Acornhoek Hardware Cc
- **KA100** | Absolute Hardware And Tools
- **KA103** | Al Madinah Hardware
- **KA109** | Arham @ Melrose Hardware
- **KB014** | Bara Paint & Hardware
- **KB032** | Bonanza Plumbing & Electrical
- **KB038** | Bob'S Hardware C.C.
- **KB053** | Mekka Hardware
- **KB064** | Builders Hyper Pty Ltd
- **KB085** | Best Build Hardware
- **KB094** | Builders Den Pty Ltd
- **KB100** | Builders Direct Depot Pty Ltd
- **KB109** | S.R. Mullas Hardware & Superma
- **KC023** | Choice H/W & Elec.(Carolina)
- **KC041** | Central Build It
- **KC056** | Cheap Cheap Hardware
- **KD012** | Discount Hardware (Hazeyview)
- **KD016** | Dinal Enterprices (Pty) Ltd - Botswana *(+1 delivery point)*
  - KD016/2 | Dinal Enterprices (Pty) Ltd - Ramotswa
- **KD030** | Desai Hardware
- **KD033** | Diy Depot ( Petrus Styne)
- **KD054** | Discount Builders
- **KD060** | Best Build Hazyview (Pty) Ltd
- **KE031** | Il Molino (Pty) Ltd
- **KF011** | Family Hardware
- **KG006** | Gulmohur Building Supplies P/L *(+3 delivery points)*
  - KG006/2 | Gulmohur G B S
  - KG006/3 | Gulmohur Building Supplies P L -  Opposite Filling Station
  - KG006/4 | Gulmohur Building Supplies P L - Halie Sellasie Road
- **KG010** | Gardees Cc T/A Gardees H/Ware
- **KG022** | Builders Solution
- **KG027** | Emgwenya Investments Pty Ltd
- **KH018** | Help U Build (Pty) Ltd
- **KH048** | Hardware City - Main Street
- **KI006** | Iqbals Welding Shop (Faizel)
- **KJ037** | Jad Doors (Pty) Ltd
- **KK016** | Faiz Hardware (Pty) Ltd
- **KK038** | Kelly'S Hardware
- **KL006** | Lcs Wholesalers (Kanye) P/L
- **KL028** | Ilanga Hardware
- **KM008** | Maxi Save Hardware Corporation
- **KM025** | Masons Hardware
- **KM033** | Moin'S Enterprises (Pty) Ltd
- **KM035** | Mikes Hardware
- **KM061** | Manish Naran
- **KM064** | Masons Home Hardware
- **KM091** | Malebeswa Investment (Pty) Ltd
- **KM094** | Al-Kauthar Investments
- **KM096** | Mykatrade 510 (Pty) Ltd
- **KM105** | Mc Roux T/A Monyakeng Hardware
- **KM109** | Mullas  Hardware
- **KM141** | Memel Hardware
- **KM159** | Mts Hardware
- **KM163** | Maxi Hardware
- **KN004** | Neha H/W & Bldg.Mat.
- **KN011** | Discount H/Ware T/A Best Build
- **KN018** | Naaz Hardware & Furniture
- **KN024** | Navisha Investments Pty Ltd - Kopong *(+9 delivery points)*
  - KN024/1 | Navisha Investments Pty Ltd - Molepolole
  - KN024/2 | Navisha Investments Pty Ltd - Taung  Ramotswa
  - KN024/3 | Navisha Investments Pty Ltd - New Choppies Mall
  - KN024/4 | Navisha Investments Pty Ltd - Lentsweletau
  - KN024/5 | Navisha Investments Pty Ltd - BOKAA
  - KN024/6 | Navisha Investments Pty Ltd - Side Sikwane
  - KN024/7 | Navisha Investments Pty Ltd - Mochudi
  - KN024/8 | Navisha Investments Pty Ltd - Broasrust Gaborone
  - KN024/9 | Navisha Investments Pty Ltd Ka
- **KO009** | One Price Store
- **KP005** | Patel (Nkomazi Imp. & Exp. Cc) - Tonga *(+4 delivery points)*
  - KP005/1 | Patel (Nkomazi Imp. & Exp. Cc) - NAAS
  - KP005/2 | Patel (Nkomazi Imp. & Exp. Cc) - MALELANE
  - KP005/3 | Patel (Nkomazi Imp. & Exp. Cc) - Opp Makro, Nelspruit
  - KP005/4 | Patel (Nkomazi Imp. & Exp. Cc) - Kwartek Street, Hazyview
- **KP009** | Payless Hardware
- **KP013** | Patels Hardware & Tiles
- **KP015** | Mono Steelworks Cc
- **KP053** | Paint Mart *(+5 delivery points)*
  - KP053/2 | Paint Mart (Benoni)
  - KP053/3 | Paint Mart (Vereeniging)
  - KP053/4 | Paint Mart (Lenasia)
  - KP053/6 | Paint Mart (Carltonville)
  - KP053/7 | Paint Mart (Lenasia South)
- **KP061** | Paint Mart Moe *(+2 delivery points)*
  - KP061/2 | Paint Mart Moe (Lenasia)
  - KP061/3 | Paint Mart Moe (Lenasia South)
- **KR036** | Royal Water Pty Ltd
- **KS012** | Solly'S Hardware
- **KS016** | Super Stores Hardware & Elec.
- **KS021** | Shalom Hardware
- **KS028** | Sunbeam Fibre Products Cc
- **KS050** | Sheffield Paints & Hardware
- **KT003** | Thanda Bantu Masakhane
- **KT007** | Tourist Bazaar
- **KU005** | Candyland General Trading
- **KU006** | U Save Glass And Hardware
- **KU008** | Uzzi Hardware Pty Ltd
- **KV002** | Vereeniging Builders Supplies
- **KV005** | Valencia Hardware (Pty) Ltd
- **KV021** | Vaal Auto Paints
- **KZ008** | Zonelite Enterprises Pty Ltd - Masetedi Ward *(+1 delivery point)*
  - KZ008/1 | Zonelite Enterprises Pty Ltd - Next to Liquor Rama

### Week 3 — 78 accounts

- **KA038** | Ace Hardware & Furniture
- **KA053** | Dadabhay Ma-Archies Furniture
- **KA054** | Al Soud Traders
- **KA056** | A N Hardware
- **KA072** | Amods Electrical & Plumbing
- **KA078** | Asif Cash & Carry &  Hw
- **KA080** | Bhambanana Park
- **KA104** | All In One Hardware
- **KA111** | Akoob Group Pty (Ltd)
- **KA113** | Alex Hardware Devon
- **KB002** | Bright Build
- **KB010** | Siraaj Bera Cc
- **KB012** | Buy-Rite
- **KB035** | Amoriscape Pty Ltd
- **KB046** | Bhana And Shikh General Dealer
- **KB062** | Board City
- **KB066** | Bala & Sons T/A Bns Supermark
- **KB075** | Burgersfort Wood Centre Cc
- **KC011** | Molepo Coal Centre Pty Ltd
- **KC012** | Cassims Hardware
- **KC021** | Choice Hardware & Electrical
- **KC031** | Masiqhame Trading 1629
- **KC032** | Cheers Supermarket
- **KD004** | Discount Hardware - Near Mooketsi
- **KD008** | Dada'S World Of Hardware Cc
- **KD017** | Discount Hardware(Groblersdal)
- **KD028** | Del Piero Trading Cc - Bok Street
- **KD062** | Deanans Auto Paints
- **KE030** | Express Mall @ 85
- **KF009** | Hibiscus Investments (Pty) Ltd
- **KF018** | Fairplay Hardware Bochum *(+5 delivery points)*
  - KF018/1 | Fairplay Hardware Lebowakgomo
  - KF018/2 | Fairplay Hardware Nobody
  - KF018/3 | Fairplay Hardware Jane Furse
  - KF018/4 | Fairplay Hardware Mabopane
  - KF018/5 | Fairplay Hardware Kwamhlanga
- **KF022** | F A P Holdings Pty Ltd Ta Kgn
- **KF030** | Fairplay Hardware (Mabopane)
- **KF032** | Alex Hardware -  Kotze Street
- **KG031** | Kgn Builders Supplies
- **KH005** | H.M.G. Wholesalers
- **KH021** | Ebrahim Abramjee Traders Cc - Head Office-Lenz *(+2 delivery points)*
  - KH021/1 | Ebrahim Abramjee Traders Cc -  Protea Glen
  - KH021/2 | Ebrahim Abramjee Traders Cc - Braamfontein
- **KH023** | Hassims Hyper
- **KH028** | Omela Dhabi & Sons Cc
- **KH029** | Hadid Hardware & Furniture
- **KH035** | Hgm Steelboys Cc
- **KJ022** | Jane Furse Builders Supply Cc
- **KK006** | Pir And Sons Trd (Kalamazoo)
- **KK012** | Pacfic Beach Trading 8Cc
- **KK040** | Kareena Traders
- **KL011** | Lalita Supermarket & Hardware *(+1 delivery point)*
  - KL011/1 | Gigas Supermarket
- **KL022** | Lucky Save Hardware
- **KL034** | Lucky Save 2
- **KM002** | Bapedi Timber & Hardware
- **KM012** | Vendeco Trading 53 Cc *(+1 delivery point)*
  - KM012/1 | Hardware City - Next to Build It
- **KM013** | Moollas Hardware & Furniture
- **KM037** | Maphalle Hardware
- **KM046** | Aslam Motala Hardware Cc
- **KM060** | Maponya Hyper Rama
- **KM076** | Moosas Supermarket
- **KM079** | Mohamedys Hardware Cc
- **KM087** | Mangera'S Hardware City
- **KM101** | Mehvish Cash & Carry
- **KM110** | Alex Hardware - Leandra
- **KM120** | Mr Build Pty Ltd
- **KM127** | Myka Trade 2  Mankweng *(+1 delivery point)*
  - KM127/1 | Myka Trade 2 T A New Builders
- **KM152** | Betta Spares & Accessories T/A
- **KM161** | Mkh Hardware
- **KN022** | M.H.I Hardware (Nkambako H/W) *(+1 delivery point)*
  - KN022/1 | M H I Hardware (Nkambako H/W)
- **KN026** | New South Building Supplies
- **KP002** | Power Hardware - Burgersfort *(+1 delivery point)*
  - KP002/2 | Power Hardware - Lebowakgomo
- **KP025** | Platinum Auto Paints - Lenasia *(+1 delivery point)*
  - KP025/1 | Platinum Auto Paints - Vereeniging
- **KP057** | Priyanka Supermarket
- **KR018** | Sonu Supermarket (Raj)
- **KS022** | Super Blue Supermarket
- **KS029** | Patel Hardware *(+1 delivery point)*
  - KS029/1 | Duro Build
- **KS071** | Nimeshkumar General Dealer
- **KS080** | Sehlware (Pty) Ltd
- **KS129** | Siza Bantu Mkhwenyana Hardware
- **KS130** | Shingange General Dealer
- **KV016** | Vendeco Trading
- **KW011** | Hassims Supply Store
- **KW013** | Wood Corner Pty Ltd

### Week 4 — 74 accounts

- **KA051** | A Hardware
- **KA095** | Akay Build And Save-Madonsi Village *(+1 delivery point)*
  - KA095/1 | Sure Build -Vuwani
- **KA096** | Alston Trading T/A Vhembe H/W
- **KA106** | Afia Pty (Ltd) T/A
- **KA107** | Applemint Properties 91 Pty Lt
- **KA110** | Ace Steel And Roofing
- **KA114** | Amk Hardware
- **KB025** | Balkan Trading Cc
- **KB071** | Intshebe Props 216 Pty Ltd - Mr Build *(+1 delivery point)*
  - KB071/1 | Intshebe Props 216 Pty Ltd - The Builder
- **KB101** | Berario Hardware & Tool
- **KB106** | Baps Randburg
- **KB108** | Salema Hardware (Pty) Ltd
- **KB110** | Best Build Hw Giyani
- **KC008** | Sage Wise 1065 Cc
- **KD003** | Del Piero Trading Cc - Main Rd R523
- **KD027** | New Discount Build
- **KD029** | Door To Door Trade 1005 Cc
- **KD063** | Dhp Construction (Pty) Ltd
- **KF008** | Faroque General Trading P/L
- **KF020** | Fast Build Hardware *(+1 delivery point)*
  - KF020/1 | Malamulele Hardware
- **KF031** | Fairplay Kwamhlange (Pty) Ltd
- **KF034** | Faeez Cassim
- **KF035** | Fix It Hardware
- **KG011** | Gani'S Mining Services Cc
- **KG012** | Galaxy Hardware
- **KH002** | Handy Joes Hardware
- **KH008** | Honest Electrical & Plumbing
- **KH034** | Home Build
- **KH049** | Home Build Hardware Dumasi Vil
- **KI012** | I T S My Style
- **KI015** | Iskcon Steel - Ramasaga Street Industrial *(+1 delivery point)*
  - KI015/1 | Iskcon Steel - Next to Redrock
- **KK028** | Kgapane Hardware Pty Ltd
- **KK031** | Kazi Hardware & Tool
- **KK036** | Khotawala Hardware
- **KL009** | Low Cost Hardware
- **KL032** | Mala Hardware Ta Limpopo Hw
- **KL035** | Lucky Domestic Hardware
- **KL037** | Lavender Moon Trading Ta
- **KL046** | Lunnesa Properties Cc
- **KL047** | Leroy Merlin
- **KM011** | Quick Save Hardware
- **KM056** | Madina Property Trust
- **KM065** | Mega Hardware
- **KM071** | Inyameko Trading 1605Cc - Giyani *(+1 delivery point)*
  - KM071/1 | Inyameko Trading 1605Cc - Malamulele
- **KM078** | Mavambe Hardware
- **KM123** | Honest Electrical And Plumbing
- **KM148** | Aaliya Hardware
- **KM155** | Mr Build  Ltt (Pty) Ltd
- **KN033** | Nimmi Investment
- **KO002** | Omega Hardware And Supermarket
- **KO010** | Olympic Colour Studio (Pty)
- **KP046** | Pride Pak Packaging
- **KP052** | Pristine Pumps & Electrial
- **KP056** | Pardhi Patel (Pty) Ltd
- **KQ001** | Khavhade Trading Store
- **KQ008** | Silver Solution 1399 Cc
- **KQ011** | Quick Solutions Cos (Pty) Ltd
- **KR003** | Ammo Distributors (Pty) Ltd (R
- **KR008** | Shingwedzi B.M.Cc *(+4 delivery points)*
  - KR008/1 | Budget Hardware
  - KR008/2 | Wonderbuild Hardware
  - KR008/3 | Rank Hardware & Furniture
  - KR008/4 | Khotwala Best Build Shop
- **KR041** | Raza Auto Spares
- **KR042** | Rnc Group
- **KS003** | S.M. Hardware
- **KS011** | Star Glass & Hardware *(+1 delivery point)*
  - KS011/1 | Tiger Build Hardware
- **KS018** | Shikundu Trading Store
- **KS019** | S.I.Hardware - Opp. U.I.F. Building *(+7 delivery points)*
  - KS019/1 | S.I.Hardware - In Between Siloam & Mh H/W
  - KS019/2 | Saselamani Stores
  - KS019/3 | S.I.Hardware - Next To Mopani Depot, Giyani
  - KS019/4 | S.I.Hardware - Shayandima
  - KS019/5 | S.I.Hardware  Polokwane
  - KS019/6 | S.I.Hardware  Kgapane
  - KS019/7 | S.I.Hardware - Giyani Road Malamulele
- **KS026** | S.A. Hardware
- **KS068** | Seasonfind 1366 Cc T/A Ndhambi
- **KS122** | Nasco Properties (Pty)Ltd
- **KS128** | Tshixwadza Dairy Shop Pty Ltd
- **KT019** | Trendleaders Trading & Inv. Cc
- **KV015** | Viva Hardware
- **KW004** | Siam Trading Cc
- **KX003** | Exclusive Paint & Hardware
- **KY006** | Ymm Motors

---

## COMPETITORS

<!-- Source: Olympic Paints internal knowledge — key competitors in the South African decorative and trade paint market -->

### Direct Competitors

- **Plascon** *(Kansai Plascon Africa)* — market leader, premium positioning, strong retail presence
- **Dulux** *(AkzoNobel)* — premium/mid-market, strong brand equity and colour range
- **Medal Paints** — mid-market trade paint, active in hardware and contractor channels
- **Prominent Paints** — regional competitor, trade and retail focus
- **Promac Paints** — trade-focused, competitive pricing, hardware store distribution
- **Africa Paints** — value-segment competitor, similar channel overlap to Olympic
- **Excelsior Paints** — regional/independent manufacturer
- **Duram** — specialised coatings and waterproofing overlap
- **Paintcor** — trade and hardware channel competitor
- **Stevensons** — value-segment, hardware store distribution

<!-- AGENT NOTE: Olympic Paints competes primarily on price-competitiveness, product breadth, and direct service to independent hardware stores — a channel where Plascon and Dulux are less dominant. Avoid directly disparaging competitors in customer-facing communications. -->

---

## SEASONALITY & DEMAND PATTERNS

- Paint demand typically peaks in spring/summer (September–February in South Africa)
- Slower winter period (May–August)

---

## FLOWMATIC NOTE

Don't handle any actions for FLOWMATIC. 
