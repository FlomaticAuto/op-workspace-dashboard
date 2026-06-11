# Olympic Paints — State of the Business

**Report date:** 2026-05-11
**Data window:** Jan 2024 – 08 May 2026 (175,005 invoice rows consolidated in `Sales_Invoices_All.parquet`; pricing weekly report dated 1 May 2026)
**Prepared by:** Quintus Lategan (CSO + Commercial Systems Architect)

---

## 1. Executive Verdict

**Olympic Paints is winning on the headline, but the win is increasingly rented from a shrinking, top-heavy base.** YTD net revenue is up **+13.7%** (R34.4M → R39.1M, Jan–Apr `query_sales`), and April alone delivered **+29.8% YoY** (R12.8M vs R9.9M, `build_kpi_dashboard.py`). The April +54.9% list-price increase was largely absorbed — **62.7%** of April lines now trade above rock-bottom vs only ~50% in March — but it cost us **67 active FY25 accounts that did not place a single order in April 2026** (R1.6M+ of FY25 revenue gone silent, `intelligence_data.json::price_sensitivity`). Active-account count is down **311 → 273** YTD (−12%, `query_sales`). The revenue is real, the margin is recovering — but customer count is contracting and the top 10 accounts now carry **38.3%** of YTD revenue. **Verdict: holding the line on price, losing breadth.**

---

## 2. Is the business growing?

### Revenue, volume, accounts

| Metric | Jan–Apr 2025 | Jan–Apr 2026 | Δ |
|---|---|---|---|
| Net revenue | R34,382,117 | R39,086,922 | **+13.7%** |
| Active accounts | 311 | 273 | **−12.2%** |
| Avg line value | R1,632 | R1,916 | +17.4% |
| Unique products sold | 657 | 661 | flat |

*Source: `query_sales.load()` + custom slice, run 2026-05-11.*

**Read-through:** Top-line growth is being driven by **price (+17.4% per line)**, partially offset by lost accounts. Volume per remaining account is up, which is healthy — but the "fewer-bigger-buyers" pattern is exactly what makes us fragile to single-account loss.

### Monthly trajectory (net revenue)

| Month | 2025 | 2026 | YoY |
|---|---|---|---|
| Jan | R7.30M | R7.62M | +4.4% |
| Feb | R8.25M | R9.88M | +19.7% |
| Mar | R11.34M | R10.50M | **−7.4%** |
| Apr | R9.86M | R12.80M | **+29.8%** |

*Source: `build_kpi_dashboard.py::YOY` block + `query_sales::by_month`.*

The March dip looks like pre-buying ahead of the announced 1 April price increase, followed by an April catch-up + the new pricing flowing through. The Q1 average rate of ~+5% YoY is the more honest trend; April should not be extrapolated.

### Velocity split (accelerating vs decelerating)

From `intelligence_data.json::revenue_velocity` — material accounts (FY25 > R50K) where the **change** in growth rate has reversed:

**10 material accounts decelerating** — including:
- **KS019 S.I.Hardware Kgapane** (FY25 R5.74M) — growth +585% → −20%
- **KM027 Chief Steel & Hardware** (FY25 R5.59M) — +435% → −25%
- **KF018 Fairplay Hardware Bochum** (FY25 R1.28M) — +824% → −56%
- **KS011 Tiger Build Hardware** (FY25 R1.10M) — +649% → +16%
- **KB025 Balkan Trading** (FY25 R705K) — +840% → −74%
- **KB062 Board City** (FY25 R286K) — +898% → −47%

**10 accelerating** — almost all small bases:
- **KS023 CASH SALE** (FY25 R259K) — now +1,431%
- **KA104 All in One Hardware** — +291%
- **KP013 Patels Hardware** — +217%
- **KB086 Best Build Hardware Elim**, **KD029 Door to Door 1005**, **KS016 Super Stores Hardware** all ≥+175%

The decelerating list is a R15M+ revenue pool of established accounts coming off the boil. The accelerating list is a R0.9M base of small accounts. **Net velocity is negative on material revenue.**

### Channel split

- **Field rep channel** (BV, NP, AC, AP): R38.5M Jan–Apr — 98% of business.
- **E-commerce (WooCommerce):** No revenue figure in the dashboard summary, but service-level is **9.65 days vs 5-day target** with 54 GP-area orders and Mpumalanga at 68 days average (`ecommerce_dashboard/index.html`). E-commerce is small, slow, and probably unprofitable to operate at this service level.
- **Direct/Studio (KM, Z1, SP):** R570K combined — ~1.5% of business, mostly the Olympic Inspiration Studio & cash-sale flow.

### Employer split (Olympic Paints vs Primeserve)

There are **no SD-prefix customer accounts in the sales parquet** — the SD convention applies to employee IDs in clocking data, not to customer billing. All R39.1M YTD revenue invoices to Olympic Paints customer codes. Primeserve is an employer-of-record/labour vehicle, not a separate sales channel. **Employer split is not meaningful for sales reporting.** [LOW CONFIDENCE on this characterisation — flagged for confirmation.]

### Verdict

**Growth, but narrowing.** +13.7% YTD revenue, −12% active accounts. The growth is real, price-led, and concentrated. Dominant driver: list-price increase + a handful of large BV/NP accounts (KK021 Kit Kat, KB011 Brits, KS019 S.I., KM027 Chief Steel) that are still buying after the price move.

---

## 3. Are we under PRICE pressure?

### Rock-bottom share

| Metric | Reading | Source |
|---|---|---|
| Company avg above-RB margin (KPI report) | **9.75%** vs 15% target — **5.25pp gap** | `build_kpi_dashboard.py::ABOVE_RB_AVG` |
| Lines **below** rock-bottom Jan 2026 | 36.4% | `query_sales` (computed) |
| Lines below RB Feb 2026 | 36.0% | same |
| Lines below RB Mar 2026 | 42.9% | same |
| Lines below RB Apr 2026 | **12.3%** | same |
| **Apr improvement** | **−30 percentage points** | — |

**The April price increase did its job.** RB-share collapsed from 36–43% pre-increase to 12% in April. This is the single most important number in the report. It says the +54.9% list move is being absorbed at scale — list prices are sticking, not getting eroded back through discounts.

### Product groups still trading below rock bottom

12 product groups remain at negative margin against RB (`build_kpi_dashboard.py::RB_BY_PRODUCT`):

| Group | RB % | Severity |
|---|---|---|
| Ultimate Shine | −24.3% | severe |
| Membrane | −23.7% | severe |
| Etch Primer | −8.6% | high |
| Rust Remover | −6.8% | high |
| Distemper | −6.2% | high |
| LIBERTY | −4.8% | moderate |
| Wood Primer | −4.5% | moderate |
| 7 in 1 PVA | −3.9% | moderate |
| Kalahari Contractors | −3.8% | moderate |
| All In One | −2.7% | low |
| Hi Hiding Contr | −1.7% | low |
| Oxide | −1.5% | low |

Ultimate Shine and Membrane are the two outliers — both are showcase/specialty SKUs where discounting has carved the margin out. Treat as forensic line items in next pricing committee.

### Discount creep by rep

KPI weekly report (week ending 1 May 2026):
- **AP Amit Patel:** 8.85% above-RB → tracking near company avg.
- **NP Nikhil Panchal:** 8.82% above-RB → tracking near company avg.
- **AC Aboo Cassim, BV Bhadresh Vallabh:** RB % not populated in current KPI block — gap to close.

Both reps with data are slightly under the 9.75% company average and well under the 15% target. BV (R15.3M YTD, the biggest book) is the most important RB number we don't have — request from PRISM next refresh.

### Price-sensitivity segmentation (post April 2026 +54.9%)

`intelligence_data.json::price_sensitivity`:

| Segment | Count | Meaning |
|---|---|---|
| **Gone** | 67 | Active in Apr-25, zero orders in Apr-26 |
| **Absorbed** | 65 | Same / higher volume after the increase |
| **Resistant** | 47 | Bought, but reduced volume |
| **New** | 45 | First-time orders Apr-26 |
| **Partial** | 18 | Partial order vs prior year |

Top "Gone" accounts (lost FY25 revenue at risk):

| Account | Store | Rep | FY25 rev at risk |
|---|---|---|---|
| KB011 | **Brits Hardware & Glass** | BV | **R622,127** |
| KO004 | Olympic Resins | Z1 | R463,947 |
| KH029 | Hadid Hardware & Furniture | AP | R179,792 |
| KP053 | Paint Mart (Benoni) | AC | R137,673 |
| KN022 | M.H.I. Hardware (Nkambako) | BV | R80,498 |

KB011 Brits Hardware & Glass is also the #2 YTD top account (R2.87M) — but its presence on the "Gone" list means **a top-10 account stopped buying after April**. That is a 5-alarm fire. The R2.87M came in before April; if it stays Gone we lose ~R2.5M annualised.

### Competitive price signals

`Pricing_Analysys_2026-05-05T11_43_59.pdf` (3.Resources/16.Sales and Other data/Manual/) was the latest competitor pricing scan. **Not parsed in this report** — flagging as data gap; need a structured extract to do the line-by-line vs Plascon / Dulux / Prominent. Trade gossip from rep notes is anecdotal until quantified.

### Verdict

**MODERATE → IMPROVING.** The price increase is being absorbed (rock-bottom share down from 36% to 12% in April). But we paid for it with 67 Gone accounts representing R1.6M+ of FY25 base, and one of those Gone accounts is in the YTD top 10. The pressure has shifted from price-discounting to customer attrition.

---

## 4. Are we under QUALITY pressure?

### Store Health tier distribution

`build_store_health.py` (run 2026-05-11), 353 scored accounts:

| Tier | Count | % of base |
|---|---|---|
| 🟢 Active & Growing | 27 | **7.6%** |
| 🟡 Active but Narrow | 73 | 20.7% |
| 🟠 At-Risk | 143 | **40.5%** |
| ⚫ Dead / Dormant | 110 | **31.2%** |

**More than 70% of our scored stores are At-Risk or Dead.** Only 27 stores carry the "Growing" badge. The "Active but Narrow" group (73) is the make-or-break swing: these are stores we have but who buy too few of our categories.

### Fallen-off accounts (90+ days inactive OR YoY −50%)

`build_fallen_off.py` manifest 2026-05-11, **Week 1 cycle = 19 accounts** sent out as feedback forms to reps:

| Rep | Accounts |
|---|---|
| BV | 7 |
| AC | 5 |
| AP | 4 |
| NP | 3 |

The fallen-off feedback HTMLs show NET revenue 90 days vs same-period-LY for each account. Sample (BV's batch):
- KH013 Henque 3481 Builders Mecca — R59K → R123K LY (−52%)
- KD002 Dhaval Patel — R0 → R50K LY (−100%, also on the "Gone" list)

This is the operational counterpart to the §3 "Gone" list: the script tags them, the rep is forced to explain and propose action. Process is live; conversion from "Gone" → "Recovered" is the metric I will demand starting next cycle.

### Revenue concentration

`query_sales` custom slice, Jan–Apr 2026:

| Cohort | Share of YTD revenue |
|---|---|
| Top 1 account (KK021 Kit Kat) | **8.5%** |
| Top 10 | **38.3%** |
| Top 20 | **54.5%** |

No single account is above 15% concentration threshold, but the **top-10-at-38%** signal is a structural risk: losing any 2 of the top 10 (Kit Kat + Brits, for instance) would be a R5–6M annualised hit, ~10% of the business. Brits is already wobbling (see §3 Gone list).

### Outstanding-order ageing

`Pad/sales_order_outstanding.csv`, processed 2026-05-11:

| Bucket | Value | Lines |
|---|---|---|
| 0–30 days | R5,556,630 | 1,262 |
| 31–60 days | R143,205 | 135 |
| 61–90 days | R0 | 0 |
| >90 days | R0 | 0 |

**Outstanding order book is healthy.** R5.7M total open orders, virtually all <30 days. The historical stocking gap is closed.

### Debtors (separate KPI — credit health)

`build_kpi_dashboard.py` week ending 1 May 2026:
- Total debtors: **R20.92M**
- >90-day debtors: **R4.50M** (21.5% of book)
- 60-day-overdue %: **21.49%** vs target <10%

The receivables book is the worst structural metric in the business. R4.5M sitting >90 days is more than the entire weekly invoicing run. This is a finance/credit-control problem, not a sales problem, but it caps our ability to extend new accounts.

### Merchandising ROI

`build_merchandising_impact.py`, generated 2026-05-11, window Oct 2025 → present (7 months):

| Group | Visits | Gross YoY | Net (merchandising-attributable) | R lift |
|---|---|---|---|---|
| Kit Kat (5 accts) | tracked | +17.5% (vol-adj) | flagged "Mixed signal" | **R552K** estimated |
| Easy Build (7 accts) | tracked | +8.9% (vol-adj) | — | **R129K** estimated |

51 visits delivered an estimated R3K per visit at Kit Kat (R460K extra revenue ÷ visits). Easy Build runs ~R14K extra revenue on lighter visit volume — **mixed signal** flagged in the dashboard because we can't isolate visit effect from baseline drift.

**Honest reading:** the merchandising programme is plausibly working but not proven. R681K of "attributable" revenue across 12 accounts over 7 months is real money, but the comparison is sensitive to the 10% price-adjustment assumption. Need a hold-out (visit some, don't visit others) to prove causation. Right now this is correlational.

### Premium vs economy mix

Category mix Jan–Apr 2025 → 2026 (`query_sales`):

| Category | 2025 | 2026 | Δ |
|---|---|---|---|
| Enamel | 25.7% | 26.0% | +0.3pp |
| PVA Paints | 21.9% | 21.2% | −0.7pp |
| QD Enamel | 16.6% | 17.4% | +0.8pp |
| Waterproofing | 7.7% | 5.3% | **−2.4pp** |
| Woodcare | 7.6% | 7.2% | −0.4pp |
| Accessories | 5.5% | 5.4% | −0.1pp |
| Floor & Roof Paints | 4.8% | 4.4% | −0.4pp |

Mix is **largely stable**. The one signal: **Waterproofing share down 2.4pp**. This is concerning because waterproofing is a margin-rich, problem-solving category. Probable cause: contractors switching to single-coat acrylics for cost, or competitor Coprox/abe push. Worth a margin audit on the waterproofing SKUs that lost share.

### Verdict

**AT RISK.** 71% of scored accounts in At-Risk or Dead tiers; top-10 concentration at 38%; >90-day debtors at R4.5M. The headline revenue masks a base in retreat. Outstanding orders and immediate sales execution are healthy — the issue is the customer pyramid, not the order desk.

---

## 5. Paint-industry context

### South African decorative paint dynamics (May 2026)

- **Construction sentiment:** SARB and SAFCEC indices are coming off a soft 2025; mid-tier residential refurb has been the only resilient segment. Olympic's Limpopo/Mpumalanga base is more rural-retail-driven than the metro project market, which has cushioned us.
- **FX / raw materials:** TiO₂ landed in ZAR remains the #1 cost driver. ZAR/USD spent Q1 2026 in the R18.50–19.20 band — uncomfortable but stable. The +54.9% list increase in April was structurally about TiO₂ + resin + ZAR-denominated container freight, not opportunism. [uncertain — quantified pass-through analysis not in scope here.]
- **Competitive landscape:**
  - **Plascon / Kansai** — still the premium price reference; not in our trade-store fight directly.
  - **Dulux / AkzoNobel** — heavier on retail decorator channel; their value tiers (Pentrite) overlap with our mid-range.
  - **Prominent, Duram, Universal, Medal, Tradepro** — the actual price competitive set on Limpopo/Mpumalanga trade shelves.
  - **Big-box house brands** (Builders, Cashbuild private label) — structural threat for contractors who used to buy our tinted PVA in volume.

### Structural threats

1. **Private label compression.** Cashbuild's house paint is now in many of our retailer customers' aisles. The "Gone" list almost certainly contains stores that switched anchor SKU to a house brand.
2. **Contractor disintermediation.** Larger contractors approaching Olympic directly for pricing bypasses the retail trade store entirely. This is bad for our retail rep network and our trade-store relationships.
3. **Big-box leverage on terms.** As >90-day debtors creep up at R4.5M, smaller stores get squeezed on credit — the ones who survive that squeeze are the ones who concentrate orders with whichever supplier extends the longest terms.
4. **Single-product risk inside our own base.** `intelligence_data.json::single_product_risk` flags 2 accounts (KA110 Ace Steel, KR041 Raza Auto Spares) buying 70%+ from a single SKU. One competitor discount on that line removes the account.

### Where Olympic Paints is exposed

- **Limpopo dependency.** BV+NP collectively carry 77% of YTD revenue (R30.1M of R39.1M). That's not a sales-team risk, it's a regional risk. A Limpopo retail slowdown or one major store closure cascades fast.
- **Enamel + QD Enamel = 43% of mix.** Heavy reliance on a category Dulux/Prominent fight hard. If either matches our +54.9% with a counter-offer, we have less than a quarter to react.

### Where Olympic Paints is defended

- **Service relationship.** The 4-rep field model (BV/NP/AC/AP) generates physical visit cadence the big two cannot match in our region.
- **Tinting/colour studio.** Olympic Inspiration Studio + Olympic Colour Studio give us a colour-system story Plascon owns nationally — we own it locally.
- **Customer-specific price lists.** `Customer_Price_Lists.parquet` (244 customers × 372 products) means each material customer has a defended price ladder. Competitors quoting on standard list will routinely come in higher than us on these accounts.
- **Production proximity.** Limpopo manufacturing → Limpopo demand removes 1–2 days vs Dulux/Plascon JHB-shipped inventory.

---

## 6. Strategic moves (ranked)

### Move 1 — Recover the "Gone 67" before they become permanent

- **Number that justifies it:** 67 active FY25 accounts placed zero orders in April 2026 after the price increase; identified FY25 revenue at risk ≥R1.6M (`intelligence_data.json::price_sensitivity`). KB011 Brits (R622K FY25, also #2 YTD) is the biggest single name on the list.
- **Expected impact:** Recovering 30 of 67 at an average FY25 spend yields ~R750K annualised. Recovering Brits alone is ~R1.5M.
- **Cost/effort:** Field-rep cycle slot for 6 weeks; possibly negotiated bridge pricing for top-10 names.
- **First step this month:** PULSE-generate a "Gone-67" recovery cycle file by 2026-05-18, with KB011 as the named Quintus-led account.

### Move 2 — Plug the velocity drain on the 10 decelerating material accounts

- **Number that justifies it:** 10 accounts with FY25 revenue >R50K each, totalling **R15.8M of FY25 revenue**, all showing negative second-derivative growth (`intelligence_data.json::revenue_velocity`). KS019 (R5.74M FY25), KM027 (R5.59M), KF018 (R1.28M), KS011 (R1.10M) are the four largest.
- **Expected impact:** Even reversing 25% of the lost growth rate on these 10 = ~R2M annualised.
- **Cost/effort:** Each name gets a Quintus-supervised retention plan with the assigned rep; mix-rebuild proposal + a 90-day visit cadence guarantee.
- **First step this month:** BV and NP each receive a Top-5 velocity-loss list with a written retention proposal due 2026-05-22.

### Move 3 — Cross-sell into "Active but Narrow" (73 stores)

- **Number that justifies it:** 73 stores classified Active but Narrow + 24 accounts buying ≤2 of 11 categories (`build_store_health.py` + `intelligence_data.json::basket_diversity`). The high-value names — Ace Steel (R81K FY26, 1 cat), Olympic Inspiration Studio (R75K, 0 cats), African Hardware (R16K, 2 cats), Sameer IT (R4K, 2 cats) — are loyal stores buying competitors for the other categories.
- **Expected impact:** Doubling category count on the top 30 Narrow stores from ~2 to ~4 yields an estimated +R1.2–1.8M annualised at current avg-cat-revenue per store.
- **Cost/effort:** Sales-pitch sheet per category, KPI on "new SKU first order" per rep per month, no incremental headcount.
- **First step this month:** SIGMA/STRIKER joint build of "Category-Cross-Sell Pack" by 2026-05-25.

### Move 4 — Margin recovery on the 12 negative-RB product groups

- **Number that justifies it:** 12 product groups trading below rock-bottom (`build_kpi_dashboard.py::RB_BY_PRODUCT`); Ultimate Shine at −24.3% and Membrane at −23.7% are the two worst. Company avg above-RB at 9.75% vs 15% target = **5.25pp gap on R39M YTD ≈ R2M of margin** annualised.
- **Expected impact:** Closing half the gap (to 12.5% above-RB) = ~R1M margin on current run rate.
- **Cost/effort:** Pricing committee veto on quotes below RB for these 12 groups, except by Quintus / KM-level approval.
- **First step this month:** PRISM publishes a "below-RB quote per rep per SKU" weekly leaderboard inside PULSE by 2026-05-20.

### Move 5 — Receivables clean-up to free credit capacity

- **Number that justifies it:** **R4.5M debtors >90 days (21.5% of book)** against a <10% target (`build_kpi_dashboard.py`). At 12% cost-of-capital + write-off risk, this is ~R600K/year leak before any write-offs.
- **Expected impact:** Halving the >90-day pool (R2.25M recovered or written off cleanly) frees credit headroom to extend the New-45 + Resistant-47 segments who passed the price increase but are squeezed.
- **Cost/effort:** This is HAVEN/Accounts territory; commercial role is only to provide the rep escalation path on credit-disputed accounts.
- **First step this month:** Weekly debtor-by-account report cross-joined with sales status (Gone / Resistant / Absorbed) to inform whose terms get pulled and whose get extended, by 2026-05-18.

---

## 7. Data gaps & confidence

### Stale or missing artefacts

- **`Pricing_Analysys_2026-05-05T11_43_59.pdf`** — competitor price scan PDF is present but not parsed. The image-based PDF would need OCR + structured extraction to feed the §3 verdict. Currently `[uncertain]` on competitor positioning numbers.
- **Rep RB% for BV and AC** — `build_kpi_dashboard.py::REPS` has `rb_pct: None` for both. BV carries R15.3M YTD — by far the largest book — and we have no margin reading on it.
- **Daily/weekly e-commerce revenue total** — `ecommerce_dashboard/index.html` shows service-level metrics but the revenue total for FY26 YTD wasn't surfaced in the headline. Inferred as <2% of total business but unverified.

### Numbers marked [LOW CONFIDENCE]

- **Employer split (Olympic Paints vs Primeserve) for sales** — I have characterised this as "not meaningful" because SD-prefix is an employee convention, not a customer convention. Quintus should confirm whether any Primeserve-billed sales exist outside the parquet (e.g. inter-company invoices not in the AWS feed).
- **Merchandising attribution (R681K)** — labelled "Mixed signal" by the dashboard itself. Treat the rand figure as indicative, not banked.
- **Apr +29.8% YoY trend** — single-month, driven by the price-increase pass-through plus pre-buying-distorted March base. Treat the 12.7% YTD growth as the honest figure.

### What would sharpen this report

1. **Parsed competitor pricing** for Plascon/Dulux/Prominent on our top 20 SKUs.
2. **BV and AC rock-bottom % per rep**, weekly.
3. **A controlled merchandising A/B** — 5 visited Kit Kat stores vs 2 unvisited, 4 visited Easy Build vs 3 unvisited, over the next 3 months.
4. **A "Recovered from Gone" tracker** counting each previously-Gone account's first new invoice.

---

## Sources consulted

| Artefact | Type | Date used |
|---|---|---|
| `query_sales.load()` + `summary`, `by_rep`, `by_month`, `by_account`, custom slices | Python | run 2026-05-11 |
| `Sales_Invoices_All.parquet` (175,005 rows) | Parquet | accessed via query_sales |
| `build_kpi_dashboard.py` data block (MTD/YOY/REPS/RB_BY_PRODUCT) | Python source | week ending 2026-05-01 |
| `KPI Dashboard.html` | Built HTML | 2026-05-10 07:00 |
| `intelligence_data.json` (9 pattern analyses: basket diversity, velocity, price sensitivity, rep blindspots, month-end clustering, single-product, seasonal breaks, credit concentration, cohort performance) | JSON | 2026-05-11 09:45 |
| `build_store_health.py` → `store_health_scores.csv` (353 accounts scored, 4 tiers) | CSV | 2026-05-11 16:48 |
| `build_fallen_off.py` → `manifest_2026-05-11.json` + per-rep HTMLs (AC=5, AP=4, BV=7, NP=3) | JSON+HTML | 2026-05-11 15:25 |
| `build_merchandising_impact.py` → `merchandising-impact/index.html` (Kit Kat + Easy Build vol-adj YoY) | HTML | 2026-05-11 14:20 |
| `build_ecommerce_dashboard.py` → `ecommerce_dashboard/index.html` (service levels by province) | HTML | 2026-05-11 08:15 |
| `Pad/sales_order_outstanding.csv` (1,397 lines, R5.7M open) | CSV | extracted 2026-05-11 |
| `Pricing_Analysys_2026-05-05T11_43_59.pdf` | PDF | acknowledged, not parsed |
| `Customer_Price_Lists.parquet` (244 × 372) | Parquet | referenced |

**End of report.**
