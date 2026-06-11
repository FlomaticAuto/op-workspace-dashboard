# CSO Sales Intelligence Briefing Prompt
**Owner:** Quintus (Chief Sales Officer) | **Created:** 2026-05-26 | **Scope:** Olympic Paints — All channels

---

## How to use this prompt

Open a new Cowork session, paste this prompt (or say "run the CSO briefing"), and I will read all source files listed below, synthesise the intelligence, and deliver a structured briefing. The prompt defines exactly what questions to answer and what data to pull. Update the **Data Refresh Triggers** section as new data sources come online.

---

## Briefing Instructions (for Claude)

You are acting as a senior sales analyst briefing Quintus, Chief Sales Officer of Olympic Paints — a South African paint manufacturer selling to hardware stores, building supplies stores, non-traditional paint stores, and online channels. Before producing any output, read every file in the **Source File Manifest** below. Do not skip files. Do not fabricate data. Where data does not exist to answer a question, say so explicitly and record it in the **Data Gaps** section of your output.

### Source File Manifest — read all before responding

| Priority | File | What to extract |
|---|---|---|
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/product-intelligence.md` | Tier structure, SKU gaps, list prices, rock bottom floors |
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/pricing-intelligence.md` | Rock bottom performance, actual vs list selling prices, competitor benchmarks |
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/customer-intelligence.md` | Problem accounts, active leads, lost/dormant accounts, segment notes |
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/market-intelligence.md` | Competitor landscape, geographic traction, pricing pressure signals |
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/rep-performance.md` | Rep roster, KPI targets, discount violations, activity log |
| ⚡ MUST READ | `3.Resources/17. Strategic Intelligence/strategy-decisions.md` | Settled decisions, open questions, things tried and abandoned |
| If available | `2.Areas/1. Sales/1. Pricing/Rock Bottom/Rock Bottom Prices 2026 vs 2025.xlsx` | Year-on-year rock bottom change by SKU |
| If available | `2.Areas/1. Sales/1. Pricing/customer-pricing.xlsx` | 16,383 actual transaction records — average selling price vs list by product |
| If available | `1.Projects/KPI Report/` | Latest QuickSight KPI exports — revenue, units, accounts |
| If available | `2.Areas/1. Sales/2. ODO/DEAL_LEDGER.md` | E-commerce channel volume and trend |
| If available | `0.Inbox/` | Any unprocessed field reports, store visit notes, or new competitor intel |

---

## Analytical Framework — Answer These Questions

Work through each section in order. For each question, cite the source file or data you are drawing from. If the data is absent, say **[DATA GAP]** and explain what would be needed to answer it.

---

### Section 1 — Business Health Snapshot

**What is the current state of the business?**

1. What is our total revenue trend — are we up or down versus the prior period? Is growth real or is it simply the 15% list price increase flowing through?
2. What is our average gross margin performance per enamel tier (Ultimate Shine / High Gloss / Pick 'N Save)? Are any tiers loss-making at current average selling prices?
3. Are any product groups performing above the +15% rock bottom target? Which are furthest below it?
4. How does our average selling price compare to list price across each tier? How much value is being given away by reps in discounts?
5. Where is the 15% list price increase (April 2026) actually sticking, and where has it been offset by rep discounting?

**Inflation context (mandatory):** South African CPI ran at approximately 4.4% in 2024 and 3.2% in 2025 (cumulative ~7.7% from Jan 2024 to Dec 2025). By May 2026 add approximately a further 3–4%, giving a cumulative 2024–2026 inflation of roughly 11–12%. Our list prices increased by 15% in April 2026, but only after a period of flat or modest increases before that. When evaluating revenue growth:
- A business growing revenue at 15% on the back of a 15% price increase with flat unit volume is **not growing — it is standing still in real terms**.
- If average selling prices are 20–34% below list (as the pricing data shows), the revenue realised from the price increase is being substantially eaten by discounting, potentially leaving real revenue **below inflation** even on a nominal uplift.
- Frame all revenue trend analysis through this lens. Ask: is our revenue growing faster than CPI? Are we gaining or losing purchasing power?

---

### Section 2 — Growth vs Churn (The Critical Question)

**Are we actually growing, or are we churning accounts and replacing them with new ones?**

This is the most important diagnostic the CSO needs. Revenue can look stable or growing even while the underlying customer base is deteriorating, if new accounts are replacing lost ones. The risk is that new-account acquisition costs are hidden while churn is treated as normal attrition.

Answer the following:

1. **Active account count:** How many unique accounts purchased in the last 12 months? How does this compare to 24 months ago?
2. **New account acquisition:** How many accounts placed their first-ever order in the last 6 months? 12 months?
3. **Dormant / lost accounts:** How many accounts that were active 12–24 months ago have not placed an order in the last 6 months? These are churned accounts.
4. **Net account movement:** New accounts minus churned accounts = net customer base change. Is this positive or negative?
5. **Revenue concentration risk:** What % of revenue comes from the top 10 / top 20 accounts? If this is above 50%, the business is exposed — losing one account could be catastrophic.
6. **Average order value trend:** Are existing accounts buying more or less per order? This distinguishes organic growth from simple account inflation.

> **The fictitious growth test:** If new stores are coming in at lower average order values than the stores falling away, the business may show account growth while actually shrinking in revenue per-customer terms. Flag this if data supports it.

---

### Section 3 — Pricing Discipline & Profitability

**Are we actually making money at the prices we are selling at?**

1. List all accounts currently selling below rock bottom. For each: name the account, the rep responsible (if known), the % below rock bottom, and the action status.
2. For Ultimate Shine specifically: at the average selling price of –23.97% below rock bottom, is this product loss-making? What is the estimated margin impact across total Ultimate Shine volume?
3. Are there any SKUs where the minimum price seen (R0 transactions excluded) is below the 2026 rock bottom? List them.
4. What would revenue look like if all transactions were at rock bottom (the floor, not the target)? What would it look like at the +15% target? Use this as a range to show the upside of pricing discipline.
5. Is rep discount authority appropriate, or should it be curtailed? What is the policy recommendation given current data?

---

### Section 4 — Competitive Threats

**Where are competitors eating our market, and what should we do about it?**

Work through each known competitor and assess:

1. **Crest / Stevensons:** Their Gloss Enamel is R239/5L wholesale vs our High Gloss at R414/5L list (–42% cheaper). At what segments and store types is Crest winning on price? What is our differentiated counter-story (chemistry, guarantee, service)?
2. **Splash Paints SA (Polokwane/Limpopo):** Verified manufacturer. QD Enamel at R299–408/5L. Active in our Limpopo territory. Which of our accounts in Limpopo are at risk? Are reps encountering Splash at store level?
3. **Duram:** WallTech 12-year guarantee + ColorPro tinting in Cashbuild/Builders/BUCO. Active in Paint Pot stores in Limpopo (Tzaneen, Polokwane, Giyani). Are we in these stores? Are we competing on guarantee language?
4. **Eclipse:** Confirmed stocking at GG 104 Building Supplies in Southdale — that account has NO Olympic enamel. How many other accounts are Eclipse-only? Is this data tracked?
5. **Home Seal / Dripp / Ecostar / Diamond Premium:** Budget brands at R115–200/20L PVA. These are price-anchoring threats — they shift the customer's price reference point downward, making our Pick 'N Save look expensive. How do we inoculate against this in rep conversations?
6. **Anetic / Finesse / Nudan:** Field reports suggest Limpopo account poaching. Are these real threats or market noise? What verification is outstanding?

Produce a **Competitor Threat Matrix:** rank each competitor by (a) evidence of active account poaching, (b) pricing threat level, (c) our current countermeasure strength. Flag which require immediate rep briefing.

---

### Section 5 — Geographic Performance

**Where are we winning, holding, and losing ground by territory?**

1. Map known account activity by territory: Mabopane, Lenasia, Chamdor, Southdale, Kagiso, Limpopo.
2. For each territory: how many active accounts, how many leads, how many known competitive threats?
3. Which territories have reps currently covering them? Are there territories with no rep coverage?
4. Flag the Limpopo corridor specifically — Splash Paints and Duram both have confirmed presence there. Are our Nikhil Panchal route accounts secure?
5. Non-Traditional Paint Stores (NTPS): Kagiso, Lenasia, Mabopane are active areas. What is the conversion rate from lead to active account?

---

### Section 6 — Rep Performance & Sales Execution

**Are our reps executing at the level the business needs?**

1. Byron Minnie: 81 store visits in January 2026 vs a target of 200/month. What is the current visit rate? What revenue uplift could be expected from reaching 200 visits/month?
2. Are any reps selling below rock bottom without management sign-off? Name the accounts and reps.
3. Which rep has the highest average discount rate? What is driving it — territory, customer mix, or poor discipline?
4. What is the current coaching or accountability process for sub-RB transactions? Is it working?
5. What KPI dashboard data exists to track rep performance week-on-week?

---

### Section 7 — Channel Performance

**How are individual sales channels performing?**

1. **Trade / Hardware (core channel):** Revenue trend, account count trend, average order value.
2. **Non-Traditional Paint Stores (NTPS):** Leads pipeline (Thandabunga Supermarket, GG 104). How many NTPS accounts have been converted in the last 12 months?
3. **E-Commerce (OneDayOnly):** 2 deals completed, R14,587.35 invoiced ex-VAT total. Is this channel growing? What is the round 3 forecast? Are the submission schedules being maintained?
4. **Interior Designers / Specifiers:** Homemakers show contacts. What is the follow-up status on Sahara Michelle Interiors and Bellissimo Lifestyle?
5. **Distribution partnerships:** Are there any distributor or sub-wholesaler relationships? Are they contributing meaningfully?

---

### Section 8 — Data Gaps & What We Need Next

After completing the above analysis, produce a prioritised list of data gaps — information that, if available, would materially change the quality of the strategic recommendations. Format:

| Priority | Gap | Why it matters | How to get it |
|---|---|---|---|
| 🔴 Critical | [gap description] | [why this is a blind spot] | [specific action to close the gap] |
| 🟡 Important | [gap description] | [why this matters] | [specific action] |
| 🟢 Nice to have | [gap description] | [why it would help] | [specific action] |

**Known gaps as of May 2026 (pre-fill from existing intelligence):**

| Priority | Gap | Why it matters | How to get it |
|---|---|---|---|
| 🔴 Critical | No velocity data by store (units/month per account) | Cannot distinguish growing accounts from churning ones | Pull from Advius/Pastel: monthly units purchased per account, all active accounts, 24-month history |
| 🔴 Critical | No total revenue figures by period | Cannot calculate real growth vs inflation | Extract from Advius/Pastel: monthly revenue by product group, 2024–2026 |
| 🔴 Critical | Lost/dormant account list is empty | Churn is invisible — growth may be fictitious | Run Advius query: accounts with purchases in 2024 but zero purchases in last 6 months |
| 🔴 Critical | Ultimate Shine cost structure unknown | Cannot confirm if product is loss-making or just under-priced | Sejal to provide: cost-to-produce per SKU for Ultimate Shine |
| 🟡 Important | Rep-level revenue attribution | Cannot assess which rep is growing vs shrinking their territory | Advius: revenue by customer, cross-referenced against rep route assignments |
| 🟡 Important | PVA, waterproofing, and other range intelligence not yet seeded | Enamel-only analysis is partial view of business | Extend strategic intelligence files to all product ranges |
| 🟡 Important | No confirmed account list for Limpopo | Cannot assess Splash/Duram threat to our accounts | Nikhil Panchal to supply his full call card / account list |
| 🟡 Important | Anetic, Finesse, Nudan competitor status unresolved | Field reports of poaching are unverified | Rep to purchase product, photograph label, return physical address |
| 🟡 Important | customer-pricing.xlsx snapshot date unknown | Pricing analysis may be stale | Confirm extract date; refresh monthly |
| 🟢 Nice to have | Pick 'N Save 1L SKU feasibility | Competitive disadvantage in trial-purchase market | Sejal to respond to open production question |
| 🟢 Nice to have | Akbro house-brand paint status | May be a competitor or just a hardware retailer | Rep visit / phone call (+27 11 857 1427) |

---

### Section 9 — Strategic Recommendations

Based on the analysis above, produce a **top 5 priority actions** the CSO should take in the next 30 days. For each:
- State the problem it solves
- State the expected outcome if acted on
- State the risk if not acted on
- Name the person responsible for executing it

Then produce a **90-day horizon plan** covering: pricing governance, account recovery, competitive response, and data infrastructure.

---

## Output Format

Structure the briefing as follows:

```
# Olympic Paints CSO Briefing — [Date]
## 1. Business Health Snapshot
## 2. Growth vs Churn
## 3. Pricing Discipline
## 4. Competitive Threats
## 5. Geographic Performance
## 6. Rep Performance
## 7. Channel Performance
## 8. Data Gaps (prioritised)
## 9. Top 5 Priority Actions
## 90-Day Horizon Plan
```

Each section should lead with a **1-sentence verdict** (e.g., "Pricing discipline is critically broken — three reps are selling below rock bottom with no management intervention."), followed by the supporting detail. End with the data gaps table.

The total output should be suitable for a 30-minute CSO review session. Lead with the most alarming findings. Do not pad with obvious commentary. If data is missing, say so and move on.

---

## Recurring Briefing Cadence (recommended)

| Frequency | Trigger | What to refresh |
|---|---|---|
| Weekly | Monday morning | Rep visit activity, new sub-RB transactions, ODO status |
| Monthly | End of month | Account active/dormant count, revenue by product group, new leads converted |
| Quarterly | End of quarter | Full briefing — all 9 sections, inflation-adjusted revenue trend, competitor verification |

---

## Version History

| Date | Change |
|---|---|
| 2026-05-26 | Initial version created. Seeded with enamel range, 10 competitors, 3 rep routes, ODO e-commerce channel. |
