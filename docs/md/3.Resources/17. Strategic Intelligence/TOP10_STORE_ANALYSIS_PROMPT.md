# Olympic Paints — Top 10 Store Deep-Dive Analysis
## Claude Code Terminal Prompt
_Paste this entire file into Claude Code CLI or run as a task. All file paths are relative to the repo root `1.Olympic Paints/`._

---

## YOUR MISSION

You are conducting a forensic commercial investigation into Olympic Paints' top 10 revenue-generating stores. These 10 accounts represent ~38% of total company revenue. There are signs of contraction in FY2026 across 7 of the 10 accounts. Your job is to determine, with evidence, **what is happening inside each store relationship**: is it market decline, competitor encroachment, product mix contraction, pricing breakdown, rep neglect, or some combination? 

Produce a **per-store diagnostic report** plus a **cross-store synthesis** that management can act on immediately.

---

## THE 10 STORES TO INVESTIGATE

These are identified by their account codes and names. You must resolve store identity across all datasets using fuzzy matching on name or exact match on account code where available.

| # | Store Name | Account Code(s) | Rep |
|---|---|---|---|
| 1 | Brits Hardware & Glass | KB011 | Bhadresh Vallabh |
| 2 | Kit Kat Group (Pty) Ltd | KK021, KK022 (multiple branches) | Nikhil Panchal |
| 3 | HGM Steelboys CC | KH035 | Bhadresh Vallabh |
| 4 | Builders Direct Depot Pty Ltd | KB100 | Nikhil Panchal |
| 5 | Dada's World of Hardware CC | KD008 | Bhadresh Vallabh |
| 6 | Dainty's Wholesale Hardware | KD001 | Bhadresh Vallabh |
| 7 | Del Piero Trading CC | KD003, KD028 | Nikhil Panchal / Bhadresh Vallabh |
| 8 | Patel (Nkomazi Imp. & Exp. CC) | KP005 | Bhadresh Vallabh |
| 9 | Easy Build Hardware | KE002, KE005, KE008, KE009, KE010, KE012, KE023 (group) | Nikhil Panchal |
| 10 | Ebrahim Abramjee Traders CC | KH021 | Aboo Cassim |

> **Note on groups:** Kit Kat operates multiple branches (Marble Hall, Groblersdal, etc.). Easy Build is a group with multiple locations. Where a store has multiple account codes, aggregate them for group-level analysis AND show per-branch breakdown where data permits.

---

## DATA SOURCES — EXACT PATHS AND SCHEMAS

### PRIMARY SALES DATA

**`3.Resources/16.Sales and Other data/Sales_Invoices_All.parquet`**  
_189,045 rows | 2024-03-01 → 2026-05-25_

| Column | Type | Notes |
|---|---|---|
| `tranno` | int | Invoice/credit note number |
| `ivtype` | str | `INVOICE` or `CRNOTE` (credit note). Apply sign: invoices positive, credit notes negative |
| `trandate` | datetime | Transaction date |
| `accno` / `delno` | str | Account code (use for joins) |
| `store_name` | str | Human-readable store name |
| `prodno` / `prodname` | str | Product code and description |
| `ivqty` | float | Units sold |
| `invprice` | float | Unit selling price (ex VAT) |
| `ivcost` | float | Unit cost |
| `ivnett` | float | Net revenue ex VAT (price × qty) |
| `itemtotal` | float | incl. VAT |
| `year` / `month` / `fy` / `fy_label` | int/str | Calendar year, month, financial year (FY runs calendar year) |
| `category_l1` | str | Top-level category: Enamel, PVA Paints, QD Enamel, Woodcare, Waterproofing, Primers, Floor & Roof Paints, Accessories, General, Specialised Coatings, Putty |
| `category_l2` | str | Sub-category |
| `brand_family` | str | Brand grouping |
| `rb_price` | float | Rock bottom price for that SKU (may be NaN for some products) |
| `rb_status` | str | `Below RB`, `Above RB`, or None |

**Signed revenue rule:** `signed_nett = ivnett if ivtype == 'INVOICE' else -ivnett`

---

### PRICE REFERENCE DATA

**`3.Resources/16.Sales and Other data/Price_List_2025.parquet`** (pre-April 2025 pricing)  
**`3.Resources/16.Sales and Other data/Price_List_2026.parquet`** (post-April 2026 pricing, 15% increase)

| Column | Notes |
|---|---|
| `product_name` | Full product name |
| `pack_size` | Size (1L, 5L, 20L, etc.) |
| `lookup_key` | Join key: `product_name.lower() + '|' + pack_size.lower()` |
| `list_price_2025` / `list_price_2026` | Official list prices |
| `rock_bottom` | Absolute floor price (use `rb_price` on invoice data for per-transaction matching) |

**`3.Resources/16.Sales and Other data/Customer_Price_Lists.parquet`**  
_16,383 rows — customer-specific pricing overrides_

| Column | Notes |
|---|---|
| `curef` | Customer account code |
| `pricecat` | Product/category description |
| `effective_price` | The price this customer is supposed to receive |
| `has_active_override` | True if customer has a special price |
| `p2sdate` / `p2fdate` | Override start/end dates |

---

### STORE HEALTH & CRM DATA

**`1.Projects/AWS Data/store-health/store_health_scores.csv`**  
_439 rows — composite health score per account_

| Column | Notes |
|---|---|
| `accno` | Account code (join key) |
| `store_name` | Name |
| `rep_name` | Assigned rep |
| `health_score` | 0–100 composite score |
| `tier_code` | `growing`, `at_risk`, `dead` etc. |
| `tier_label` | Human label: `Active & Growing`, `At-Risk`, `Dead / Dormant`, `Active but Narrow` |
| `freq_3m` / `freq_6m` / `freq_12m` | Average orders/month over trailing 3/6/12 months |
| `freq_score` | 0–100 sub-score |
| `visits_6m` | Rep visits in last 6 months |
| `visits_per_month` | Average visit rate |
| `days_since_purchase` | Recency |
| `cadence_score` | 0–100: regularity of ordering |
| `n_cats_all` / `n_cats_12m` | Total categories ever bought vs. in last 12m |
| `cats_12m` | Comma-separated list of active categories |
| `basket_score` | 0–100: diversity of basket |
| `sku_depth_score` | 0–100: depth within categories |
| `sku_depth_detail` | Per-category SKU penetration (e.g. "Enamel:26.2%; PVA:52.4%") |
| `trend_slope_pct` | % monthly revenue trend slope (positive = growing, negative = shrinking) |
| `trend_score` | 0–100 score from trend slope |
| `is_recovery` | Boolean — was this account dormant and is now recovering |

---

**`1.Projects/AWS Data/Output/Rep_Account_Health.xlsx`**  
_82 rows — management-level account review sheet_

| Column | Notes |
|---|---|
| `Customer Number` | Account code |
| `Customer Name` | Name |
| `Revenue Velocity` | % revenue trend (e.g. `+24.7%`) |
| `Health` | Good / Concerning / Bad |
| `12M Turnover YoY` | Revenue and growth string |
| `Visits (12M)` | Rep visits in last 12 months |
| `Competitor 1/2/3` | Named competitors at this account |
| `Comp 1/2/3 Products` | Products competitors sell there |
| `Reasons` | Free-text reason for health rating |
| `Group/Wholesaler` | Group affiliation |

---

**`1.Projects/AWS Data/store-health/ZOHO Meeting Feedback/account_feedback.parquet`**  
_110 rows — structured field observations per account_

| Column | Notes |
|---|---|
| `store_name` | Account name |
| `store_ref_code` | Account code |
| `category` | Observation type: `product_range`, `stock_quality`, `pricing`, `branding`, etc. |
| `source_field` | CRM field the note came from |
| `notes` | Free-text field observation |
| `rating` | `Narrow` / `Broad` / `Good` / `Poor` etc. |
| `account_rep` | Rep who made the observation |
| `modified_time` | When last updated |

---

**`1.Projects/AWS Data/store-health/ZOHO Meeting Feedback/meeting_feedback_recovered.parquet`**  
_488 rows — rep visit notes with store matching_

| Column | Notes |
|---|---|
| `meeting_id` | Unique visit ID |
| `start_dt` | Visit datetime |
| `rep_name` / `rep_email` | Rep |
| `store_name` / `store_ref_code` | Account (may be NULL — use `match_account_name_norm` or `linked_name`) |
| `title` | Visit title / store name from calendar |
| `note_content` | Full structured visit note (contains checklist responses: stock location, FIFO, colour charts, replenishment order, etc.) |
| `feedback_text` | AI-extracted summary |
| `check_in_status` | `VISITED` / `PLANNED` |
| `tasks_completed` | Array of checklist items completed |
| `match_method` | How the store was matched: `exact`, `fuzzy`, `title`, `unmatched` |
| `match_confidence` | 0–1 confidence of store match |

---

**`1.Projects/AWS Data/zoho_meetings/data/meetings.parquet`**  
_4,770 rows — all CRM meetings_

| Column | Notes |
|---|---|
| `Start_DateTime` / `End_DateTime` | Visit datetimes |
| `Owner_name` | Rep |
| `Event_Title` | Store name (from calendar) |
| `Check_In_Status` | `VISITED` / `PLANNED` |
| `Check_In_Time` | Actual check-in time |
| `Note_Content` | Full visit note |
| `Tasks_Completed` | Array of completed tasks |
| `What_Id_name` | Linked CRM account name |

---

**`1.Projects/AWS Data/zoho_meetings/data/accounts.parquet`**  
_731 rows — CRM account master_

| Column | Notes |
|---|---|
| `Account_Name` | Store name |
| `Account_Site` | Account code |
| `Rep_Name` | Assigned rep |
| `Product_Range` | Rating (Narrow/Broad/None) |
| `Product_Pricing` | Pricing rating |
| `Stock_Quality` / `Stock_Rotation` / `Stock_Location` / `Color_Charts_Boards` / `Brand_Quality` | Health attributes |
| `Product_Range_Notes` / `Stock_Quality_Notes` etc. | Free-text per attribute |
| `Area_Grouping` | Geographic grouping |

---

**`1.Projects/AWS Data/zoho_meetings/data/Visit_Notes_Intelligence_2026.xlsx`**  
_150 rows — AI-summarised visit notes 2026_

| Column | Notes |
|---|---|
| `Date` | Visit date |
| `Rep` | Rep code + name |
| `Store / Account` | Store name |
| `Status` | Lead/account status |
| `Store Status` | Active / Unknown |
| `AI Summary` | Summarised visit note |
| `Competitors Stocked` | Named competitors seen at this location |
| `Competitor Intel` | Pricing or product intelligence gathered |
| `Action Required` | Recommended follow-up |
| `Price Flag` | Pricing issue flag |

---

### COMPETITOR DATA

**`3.Resources/17. Strategic Intelligence/Output/competitor_intelligence.parquet`**  
_693 rows — scraped/photographed competitor pricing_

| Column | Notes |
|---|---|
| `brand` | Competitor brand name |
| `category` / `subcategory` | Product category |
| `colour` / `size` | SKU attributes |
| `price_excl_vat` / `price_incl_vat` | Competitor price |
| `price_date` | When collected |
| `source_file` | Source image/document |

---

**`2.Areas/1. Sales/7. Competitor information/Output/Competitor Product Matrix.xlsx`**  
_685 rows — direct Olympic vs competitor price comparison_

| Column | Notes |
|---|---|
| `Brand` | Competitor |
| `Category` / `Sub-Category` | Product type |
| `Competitor Price (Excl VAT)` | Competitor's price |
| `Olympic Product` / `Olympic Code` | Matched Olympic SKU |
| `Olympic Median Price` | What Olympic actually sells this for |
| `Δ R (Olympic − Competitor)` | Absolute price gap |
| `Δ % (Olympic vs Competitor)` | % premium/discount vs competitor |
| `Verdict` | Interpretation (e.g. "Olympic +29.7% higher") |
| `Match Confidence` | HIGH / MED / LOW |

---

### CUSTOMER MASTER & AGING DATA

**`2.Areas/1. Sales/4. Customers/Misc Files/Active Customers 2026.xlsx`**  
_462 rows — live Advius customer master with aging_

| Column | Notes |
|---|---|
| `curef` | Account code |
| `cudesc` | Customer name |
| `smref` / `arref` | Rep codes |
| `cucrstat` | Credit status: `Good`, `C.O.D`, `On Hold`, etc. |
| `cucrlim` | Credit limit (R) |
| `cubalance` | Outstanding balance |
| `cucurrent` / `cu30days` / `cu60days` / `cu90days` / `cu120days` | Aging buckets |
| `cusalemtd` / `cusaleytd` | Sales month-to-date and year-to-date |
| `cuinvlast` | Date of last invoice |
| `cucrnlast` | Date of last credit note |
| `cuivdisc` | Standard discount % on account |

---

### REP CALL CYCLE

**`1.Projects/PULSE v2 — Sales & Ops Manager/data/pulse_cycle.parquet`**  
_539 rows — rep call cycle assignments_

| Column | Notes |
|---|---|
| `rep` | Rep code (BV, NP, AC, etc.) |
| `cycle_week` | Which week of the cycle this store is visited |
| `curef` | Account code |
| `customer_name` | Name |
| `town` | Location |

---

## ANALYSIS INSTRUCTIONS

### STEP 1 — Data Assembly & Joins

Before any analysis, build a master account table for the top 10 by joining:

```python
# Core revenue table
invoices = read_parquet('Sales_Invoices_All.parquet')
invoices['signed_nett'] = invoices['ivnett'].where(invoices['ivtype']=='INVOICE', -invoices['ivnett'])
invoices['signed_qty'] = invoices['ivqty'].where(invoices['ivtype']=='INVOICE', -invoices['ivqty'])

# Filter to top 10 by accno OR store_name fuzzy match
TOP10_ACCNOS = ['KB011','KK021','KK022','KH035','KB100','KD008','KD001','KD003','KD028','KP005',
                'KE002','KE005','KE008','KE009','KE010','KE012','KE023','KH021']

TOP10_GROUPS = {
    'Brits Hardware & Glass': ['KB011'],
    'Kit Kat Group': ['KK021','KK022'],
    'HGM Steelboys CC': ['KH035'],
    'Builders Direct Depot': ['KB100'],
    "Dada's World of Hardware": ['KD008'],
    "Dainty's Wholesale Hardware": ['KD001'],
    'Del Piero Trading CC': ['KD003','KD028'],
    'Patel (Nkomazi)': ['KP005'],
    'Easy Build Hardware': ['KE002','KE005','KE008','KE009','KE010','KE012','KE023'],
    'Ebrahim Abramjee Traders CC': ['KH021'],
}
```

Join these datasets per store:
- Store health scores → join on `accno`
- Account feedback → join on `store_ref_code`
- Meeting feedback → join on `store_ref_code` or fuzzy match `store_name`
- Rep Account Health → join on `Customer Number`
- Active Customers 2026 → join on `curef`
- CRM Accounts → join on `Account_Site`
- Pulse cycle → join on `curef`

---

### STEP 2 — Revenue Trajectory Analysis

For each store group, compute:

#### 2a. Absolute Monthly Revenue (signed_nett)
- Monthly revenue from 2024-03 through 2026-05
- Plot as time series (if generating charts) or output as a table with months as columns
- Flag any months where a single transaction ≥ 50% of that month's total (indicates bulk/one-off orders that could distort trend)
- Flag months with zero revenue (order gap — check if seasonal or concerning)

#### 2b. Rolling Revenue Velocity
Compute these for each store:
- **3-month rolling average** (trailing)
- **6-month rolling average** (trailing)
- **12-month rolling total**
- **Velocity**: `(3M rolling avg) / (12M avg) - 1` expressed as % — positive means accelerating, negative means decelerating

#### 2c. Year-Over-Year Comparisons
- Calendar year 2024 vs 2025 (Jan–Dec)
- FY2024 vs FY2025 (as labelled in data)
- Trailing 12 months ending May 2026 vs trailing 12 months ending May 2025

#### 2d. FY2026 Run Rate
- Sum all FY2026 invoices (March–May 2026, 3 months)
- Annualise by multiplying by 4 (or by 12/3)
- Compare annualised FY2026 run rate to FY2025 actual total
- Express as % change — this is the "early warning" signal

#### 2e. Order Frequency & Inter-Purchase Interval
- Count distinct `tranno` per month per store
- Calculate average days between consecutive orders (inter-purchase interval)
- **Flag**: if inter-purchase interval is increasing over time, the store is ordering less frequently
- Compute trend in order frequency: is the store ordering more or less often?

#### 2f. Average Order Value (AOV)
- `AOV = monthly_revenue / orders_per_month`
- Trend: is AOV growing (fewer, bigger orders) or shrinking (more, smaller orders)?
- A declining AOV alongside declining frequency = true contraction
- A declining AOV with stable frequency = basket shrinkage within orders

---

### STEP 3 — Product Mix & Basket Analysis

This is the most important diagnostic. Product category shifts reveal *what* is changing, which points to *why*.

#### 3a. Category Revenue Share Over Time
For each store, compute `category_l1` revenue as % of that store's total revenue, by:
- FY2024 period
- FY2025 period
- FY2026 YTD period

Output as a table showing category share in each period. **Flag any category that has dropped more than 10 percentage points** — this is a category-level shrinkage signal.

Example output format:
```
Store: Brits Hardware & Glass
Category         FY2024%   FY2025%   FY2026%   Trend
Enamel           67%       65%       42%       ⬇ SHRINKING
Woodcare         18%       19%       21%       → Stable
QD Enamel        15%       16%       37%       ⬆ Growing
PVA Paints       0%        0%        0%        — Never bought
```

#### 3b. Category Absolute Revenue Trend
Same as 3a but in rand values, not percentages. A category can be stable in % share but declining in absolute terms if the whole store is declining.

#### 3c. SKU-Level Analysis
For each store:
- List all SKUs purchased in FY2024 but NOT in FY2025 (dropped SKUs)
- List all SKUs purchased in FY2025 but NOT in FY2026 YTD (recently dropped)
- List SKUs that appear for the first time in FY2025 or FY2026 (new introductions)
- Count total distinct SKUs per period — is the range expanding or contracting?
- Use `sku_depth_detail` from store_health_scores as a cross-check (e.g. "PVA Paints:8.1%")

#### 3d. Category Entry/Exit Patterns
A store "exits" a category when it has not purchased from it for 90+ consecutive days.
- For each `category_l1`, find the last purchase date
- Flag categories not purchased in last 90 days as "dormant"
- Flag categories where the last purchase was over 180 days ago as "exited"
- Cross-reference against `cats_12m` in store_health_scores for validation

#### 3e. PVA Shrinkage Analysis (Priority)
PVA Paints is the single largest category by overall company volume. For each store:
- Compute PVA revenue by quarter: Q1 2024, Q2 2024, Q3 2024, Q4 2024, Q1 2025, Q2 2025, Q3 2025, Q4 2025, Q1 2026
- Compute PVA units (ivqty) by same periods
- Calculate **revenue per unit** trend on PVA: if price/unit is dropping while volume is flat, pricing is eroding; if both drop, volume is being lost
- Compare PVA absolute revenue trend to Enamel trend at the same store — if PVA drops faster, suspect a specific PVA competitor
- Key PVA competitors from the data: Crest (R279.99/20L wholesale), Anetic (R672/20L), Splash Paints (R127/20L MY CHOICE), Duram, Continental, Ecostar (R130/20L)

#### 3f. QD Enamel Concentration Risk
For stores where QD Enamel is ≥30% of revenue (Del Piero, Patel, Ebrahim Abramjee):
- Compute QD Enamel revenue by quarter
- Trend direction and velocity
- Note: Splash Paints SA's QD Enamel (5L = R299–R408) is a known competitor in the geographic area (Limpopo/Mpumalanga)

---

### STEP 4 — Pricing Quality Analysis

#### 4a. Sub-Rock-Bottom Transaction Rate
For invoices with `rb_price` not null:
- Count lines where `rb_status == 'Below RB'`
- Express as % of all priced lines
- Trend over time: compute quarterly — is the proportion improving or worsening?
- **Flag**: any quarter where >50% of lines are below rock bottom is a commercial integrity problem

#### 4b. Average Discount Depth
- `discount_pct = (invprice - rb_price) / rb_price * 100` (negative = below RB)
- Average discount depth per store per quarter
- Trend: is the average discount increasing (more aggressive) or decreasing (discipline improving)?

#### 4c. Effective Price Realisation vs List
Using the appropriate price list (2025 for pre-April 2025 transactions, 2026 for post):
- Join `Price_List_2025` or `Price_List_2026` on `lookup_key` = `prodname.lower() + '|' + pack_size_extracted_from_prodname.lower()`
- Compute `price_realisation = invprice / list_price` (1.0 = full list price, 0.7 = 30% below list)
- Average price realisation per store, by period
- A declining price realisation trend indicates structural pricing erosion, not just occasional one-off discounts

#### 4d. Customer-Specific Pricing Anomalies
From `Customer_Price_Lists.parquet`:
- Check if any top-10 account has `has_active_override = True`
- If yes: compare the `effective_price` to the actual `invprice` on their invoices
- Are they being charged *below* their contracted override price? (Rep is going even lower than the agreed special price)

#### 4e. Credit Note Ratio (Returns Signal)
- `credit_note_value = sum(ivnett where ivtype == 'CRNOTE')` per store per period
- `gross_invoice_value = sum(ivnett where ivtype == 'INVOICE')` per store per period
- `return_ratio = credit_note_value / gross_invoice_value * 100`
- A rising return ratio may indicate: product quality issues, incorrect pricing corrected post-invoice, or the store returning slow-moving stock
- Flag any store with return_ratio > 5% in any 6-month period

---

### STEP 5 — Competitor Intelligence Overlay

#### 5a. Named Competitors Per Account
From `Rep_Account_Health.xlsx`:
- Extract `Competitor 1`, `Competitor 2`, `Competitor 3` for each top-10 account
- Note the products they supply (`Comp 1/2/3 Products`)

From `Visit_Notes_Intelligence_2026.xlsx`:
- Extract all rows where `Store / Account` fuzzy-matches a top-10 store name
- Capture `Competitors Stocked` and `Competitor Intel` columns
- Extract any price intelligence (`Competitor Price`, specific product prices mentioned)

From `account_feedback.parquet`:
- Filter `category = 'product_range'` or any category mentioning competitors
- Read `notes` field for mentions of competitor brands

Cross-reference all three sources to build a per-store competitor table:

```
Store: [Name]
Competitor          Products                        Price Intel                 Confirmed?
Crest               Gloss Enamel 5L                 R239 (wholesale)            Yes — price list
Anetic              PVA (external)                  R55/1L, R672/20L            Yes — field photo
Splash Paints SA    QD Enamel                       R299–R408/5L                Yes — field visit
```

#### 5b. Category-Level Price Gap Analysis
From `Competitor_Product_Matrix.xlsx`:
- For each competitor, compute average `Δ % (Olympic vs Competitor)` per category
- This tells you how much more expensive Olympic is in each category, which helps explain shrinkage where a cheaper competitor is present
- Filter to HIGH and MED confidence matches only

#### 5c. Competitor-Category-Store Triangulation
This is the critical diagnostic step. For each store where a category is shrinking (from Step 3a), check:
1. Is there a named competitor at this store (from 5a)?
2. Does that competitor sell products in the shrinking category?
3. Is the Olympic price significantly higher in that category (from 5b)?

If yes to all three: **strong competitor encroachment signal**.  
If competitor present but category not shrinking: **Olympic is holding share despite competition**.  
If category shrinking but no competitor identified: **market decline or rep neglect hypothesis**.

---

### STEP 6 — Field Visit & Rep Activity Analysis

#### 6a. Visit Frequency vs. Revenue Correlation
From `meetings.parquet` and `meeting_feedback_recovered.parquet`:
- Count confirmed visits (`Check_In_Status == 'VISITED'`) per store per quarter
- Correlate with quarterly revenue at each store
- Compute: in quarters where visit frequency was higher, was revenue higher? (Pearson correlation per store)
- **Flag**: any store where visits are declining AND revenue is declining — rep neglect pattern
- **Flag**: any store where visits are high but revenue is declining — visits not translating (relationship/product issue, not access issue)

#### 6b. Visit Quality Assessment
From `note_content` / `feedback_text` in meeting_feedback_recovered:
- Parse structured checklist fields from visit notes:
  - "CHECKED STOCK LOCATION" → Yes/No
  - "CHECKED FIFO" → Yes/No
  - "HAVE YOU CHECKED THAT THE STOCK ON THE FLOOR IS SUFFICIENT" → Yes/No
  - "HAVE YOU PLACED A SUGGESTED STOCK REPLENISHMENT ORDER" → Yes/No/No stock to order
  - "WHO IS THE REP THAT SERVICES THE STORE" → Rep name
- Aggregate per store: what % of visits had a replenishment order placed?
- **Low replenishment order rate + declining revenue = rep visiting but not selling**

#### 6c. Visit Cadence vs. Pulse Cycle
From `pulse_cycle.parquet`:
- Identify which week of the rep cycle each top-10 account is scheduled in
- Compare to actual visit records: is the rep visiting on the prescribed cadence?
- A store assigned to cycle week 1 should see a rep visit ~every 4 weeks. If visits are at 8+ week intervals, the cadence is broken

#### 6d. Rep Assignment Anomalies
- Some stores in the top-10 have multiple reps appearing in visit records (e.g., KP005 shows both Bhadresh Vallabh and Amit Patel in meetings data)
- Flag any top-10 store with rep assignment ambiguity — unclear ownership = likely service gaps

---

### STEP 7 — Store Health Score Deep-Dive

From `store_health_scores.csv`, for each top-10 account:

#### 7a. Composite Score & Tier
- `health_score` (0–100)
- `tier_label` — what tier is this account in?
- `is_recovery` — was this account previously dormant?

#### 7b. Sub-Score Breakdown
Identify which sub-scores are dragging the composite down:
- `freq_score` < 50 → ordering less frequently than expected
- `cadence_score` < 50 → irregular ordering pattern
- `basket_score` < 50 → narrow product mix
- `sku_depth_score` < 50 → low penetration within categories
- `trend_score` < 50 → negative revenue trend

#### 7c. Category Penetration from sku_depth_detail
Parse the `sku_depth_detail` string (format: `Category:pct%; Category:pct%`) into a dict.
- Compare penetration per category to the company average
- A store with `PVA Paints:8.1%` vs company average of e.g. 40% has a massive PVA expansion opportunity — or evidence of competitor dominance in PVA

#### 7d. Days Since Purchase
- `days_since_purchase` — how long since the last order?
- Cross-check against invoice data recency
- For stores with `days_since_purchase > 30`, correlate with visit records — are they being visited but not ordering?

---

### STEP 8 — Account Financial Health

From `Active_Customers_2026.xlsx`, for each top-10 account:

- **Credit status** (`cucrstat`): Is the account in good standing, COD, or on hold?
- **Aging analysis**: Sum of `cu30days + cu60days + cu90days + cu120days` vs `cucurrent`
  - High overdue balance relative to credit limit = financial stress at the customer
  - A customer under financial pressure may reduce order volumes or switch to cheaper competitors
- **Credit utilisation**: `cubalance / cucrlim` — are they near their limit?
- **Month-to-date vs YTD run rate**: `cusalemtd * 12 / cusaleytd` — is current month pacing above or below the YTD average?
- **Standard discount** (`cuivdisc`): What is the contractual discount on this account? Compare to what they are actually receiving (from Step 4a)

---

### STEP 9 — Synthesis & Hypotheses Testing

After completing all steps above, for each store, explicitly evaluate these hypotheses. Assign a confidence level (High / Medium / Low / Undetectable) and supporting evidence.

| Hypothesis | Test | Signal |
|---|---|---|
| **Market decline** | Compare store trend to SA hardware retail index (−4.3% Nov 2024) | Store declining at market rate = market. Faster = other cause |
| **Competitor encroachment — specific category** | Named competitor present + that category shrinking in basket | High confidence if both conditions met |
| **Competitor encroachment — wholesale switch** | Wholesaler account (Dainty's) + sudden large revenue drop + no visit intelligence | Medium — needs field confirmation |
| **Pricing spiral** | Sub-RB rate increasing + revenue not recovering = discounting not buying loyalty | Detectable from invoice data alone |
| **Rep neglect / relationship breakdown** | Visits declining + revenue declining + no quality visit notes | Detectable from meeting + invoice data |
| **Customer financial stress** | Overdue balances + declining order frequency + no competitor signal | Detectable from customer master + aging |
| **Product mix contraction** | SKU list shrinking + categories exiting + basket score declining | Detectable from invoice data |
| **Bulk order timing distortion** | Single month with outsized order + adjacent months with nothing = seasonal/project, not trend | Need to identify and strip these from trend lines |
| **Group expansion / contraction** | Kit Kat, Easy Build: add/close branches distorts aggregate | Need per-branch breakdown |

---

### STEP 10 — OUTPUT FORMAT

Produce the following deliverables:

#### OUTPUT A: Per-Store Diagnostic Cards
For each of the 10 stores, a structured diagnostic card containing:

```
═══════════════════════════════════════════════════════════
STORE: [Name] | Account: [Code] | Rep: [Name]
═══════════════════════════════════════════════════════════

REVENUE TREND
  FY2024: R[x] | FY2025: R[x] (Δ [+/-]%) | FY2026 run rate: R[x] (Δ [+/-]%)
  3M velocity: [+/-]% | 12M trend slope: [+/-]%/month
  Last order: [date] | Order frequency: [N] orders/month
  AOV trend: [improving/declining]

BASKET HEALTH
  Active categories (last 12m): [N] of [N] total
  Category changes (FY2024→FY2026):
    Growing:    [category] (+X%), [category] (+Y%)
    Shrinking:  [category] (-X%), [category] (-Y%)
    Exited:     [category] (last purchase: [date])
    Never bought: [category], [category]
  SKU count: [N] in FY2024 → [N] in FY2025 → [N] in FY2026 YTD
  PVA trend: [R] in FY2024 → [R] in FY2025 → [R] annualised FY2026

PRICING QUALITY
  Sub-RB rate: [%] (Q1 2024) → [%] (Q4 2025) → [%] (Q1 2026)
  Avg discount vs list: [-X%]
  Return ratio: [%]
  Credit status: [Good / COD / On Hold]
  Overdue balance: R[x] ([%] of balance)

FIELD INTELLIGENCE
  Rep visits (last 6m): [N] | Target cadence: [N/month]
  Last visit: [date]
  Competitors confirmed: [Competitor 1, 2, 3]
  Competitor products: [list]
  Price gap vs main competitor: [+/-X% in category Y]
  Visit quality score: [replenishment orders placed: N/N visits]
  CRM product range rating: [Narrow / Broad / Not rated]

STORE HEALTH SCORE
  Health score: [X/100] | Tier: [tier_label]
  Sub-scores: Freq [X] | Cadence [X] | Basket [X] | SKU depth [X] | Trend [X]
  SKU depth by category: [parse sku_depth_detail]

DIAGNOSIS
  Primary hypothesis: [one sentence]
  Supporting evidence: [bullet points from data]
  Conflicting signals: [anything that doesn't fit]
  Confidence: [High / Medium / Low]

RECOMMENDED ACTIONS
  1. [Immediate action — Week 1]
  2. [Investigation action — Week 2]
  3. [Commercial action — Month 1]
═══════════════════════════════════════════════════════════
```

#### OUTPUT B: Cross-Store Summary Table
A single table comparing all 10 stores on key metrics:

| Store | FY25 Rev | FY26 Run Rate | Δ% | Sub-RB% | Active Cats | PVA Trend | Visits/6m | Health Score | Primary Hypothesis |
|---|---|---|---|---|---|---|---|---|---|

#### OUTPUT C: Red Flag Alert List
Bullet-point list of the most urgent issues requiring management action within 7 days, in priority order. Include: store name, specific metric/signal, threshold breached, recommended action.

#### OUTPUT D: Category-Level Cross-Store Analysis
A matrix showing revenue per category per store, with YoY trend arrows. This reveals patterns like "PVA is shrinking at all Bhadresh Vallabh accounts" (rep issue) vs "PVA is shrinking only at stores near Limpopo" (Splash Paints geographic encroachment).

#### OUTPUT E: Competitor Presence Map
A table showing which competitors are confirmed at which stores, which categories they compete in, and the Olympic price premium in each category. Mark categories as "contested" where a cheaper competitor is present and category revenue is declining.

---

## IMPORTANT IMPLEMENTATION NOTES

1. **Sign all revenue correctly.** Credit notes must be subtracted from revenue. Use `signed_nett = ivnett if ivtype == 'INVOICE' else -ivnett`.

2. **Handle the FY2026 partial year carefully.** FY2026 data runs March–May 2026 only (3 months). When annualising, note the caveat. When comparing periods, use trailing-12-month windows rather than FY labels where possible, to avoid partial-year distortion.

3. **Brits Hardware March 2026 spike.** Brits shows R2.56M in March 2026 alone, vs R255K in May 2026. Before drawing trend conclusions, determine whether March was a seasonal bulk order or an anomaly. Check if there was a single large `tranno` driving March — if one transaction = >60% of a month's revenue, flag it and show trend with and without that outlier.

4. **Kit Kat is a multi-branch group.** Aggregate all KK codes for group total, but show branch breakdown in the diagnostic card. The 135.6% FY24→FY25 growth may reflect a branch opening rather than organic growth.

5. **Easy Build is a group.** Multiple KE codes (KE002, KE005, KE008, KE009, KE010, KE012, KE023). Aggregate and show per-branch where data is sufficient.

6. **Fuzzy name matching.** `meeting_feedback_recovered` stores have unreliable name matching. Use `match_confidence` and cross-check `store_ref_code` where available. For unmatched visits, check if the visit `title` contains the store name.

7. **Rep name inconsistencies in CRM.** Rep names appear as "Bhadresh Vallabh", "BHADRESH", "BV", "Bhadresh" across different datasets. Normalise all rep references to a canonical name before analysis.

8. **PVA Shrinkage is a priority concern.** The user specifically flagged PVA shrinkage as a known issue. Give this extra emphasis in the per-store diagnosis and the category cross-store matrix.

9. **Do not hardcode the rock bottom.** Use `rb_price` from the invoice data (pre-populated for each line) as the source of truth for each SKU's floor price. Do not recalculate from price list files — there are known issues with some mapped values.

10. **Output to file.** Save all outputs to `3.Resources/17. Strategic Intelligence/top10_diagnostic_[YYYYMMDD]/` as:
    - `store_cards.md` — Per-store diagnostic cards (Output A)
    - `summary_table.xlsx` — Cross-store comparison (Output B)
    - `red_flags.md` — Red flag alert list (Output C)
    - `category_matrix.xlsx` — Category × Store matrix (Output D)
    - `competitor_map.md` — Competitor presence map (Output E)

---

## CONTEXT YOU MUST CARRY THROUGHOUT

- **Olympic Paints sells into independent hardware stores, building suppliers, and wholesalers.** Not chains. The customer base is owner-operated businesses — financially sensitive, price-negotiating, multi-supplier.
- **The enamel tiers are:** Ultimate Shine (Premium) → High Gloss (Mid-range) → Pick 'N Save (Budget). This matters when a store's enamel mix shifts between tiers.
- **Crest Gloss Enamel is 42% cheaper** than Olympic High Gloss at 5L list-to-list. Any enamel-heavy account with declining enamel revenue and a rep who is not visiting regularly is a Crest/Stevensons risk.
- **Splash Paints SA** is active in Limpopo/Mpumalanga/Venda corridor. Accounts in that corridor (Patel/Nkomazi, any KP or KN codes) are specifically at risk. Splash QD Enamel is confirmed at market prices below Olympic.
- **Continental** is competing on PVA in Nikhil Panchal's territory (Mabopane/Easy Build corridor). Field visit confirms "customer views Olympic as now more expensive" and "Continental offers competitive pricing with smaller recent price increases."
- **The 15% 2026 list price increase** was applied from April 2026 and was NOT passed on by reps — average actual discounts of 20–34% below list suggest the price increase was absorbed by discounting rather than retained as revenue.
- **Rock bottom is the absolute floor.** Selling below it destroys margin without a compensating volume or strategic benefit. The pattern of high sub-RB rates at declining accounts suggests reps are using discounting as a defensive measure that is not working.

---

_Run this analysis end-to-end. Be thorough. Where data is missing or ambiguous, say so explicitly rather than guessing. The goal is a commercially actionable diagnostic, not a data summary._
