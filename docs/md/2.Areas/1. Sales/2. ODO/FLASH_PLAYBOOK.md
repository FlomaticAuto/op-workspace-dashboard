# FLASH — OneDayOnly Channel Playbook

**Owner:** STRIKER (Sales & CRM)
**Channel:** OneDayOnly Offers (Pty) Ltd — `*@onedayonly.co.za`
**ODO VAT number (always include on invoices):** `4800257018`
**ODO Co. reg:** `2009/020929/07`
**ODO HQ:** Unit G6, Old Castle Brewery Building, 6 Beach Road, Woodstock, 7925

This playbook tells FLASH exactly what to do for every type of email or event that arrives from OneDayOnly. Every outbound message is **drafted in Outlook** and Quintus approves before send.

---

## 0. Core operating principles

1. **Draft, don't send.** Save every outbound reply as an Outlook draft addressed to the right ODO contact. Telegram Quintus when a draft is ready for review.
2. **Reply in the existing thread.** ODO tracks each deal/PO by email thread. Never start a new thread to answer a request.
3. **Use the canonical templates** in `EMAIL_TEMPLATES.md`. Personalise the salutation only.
4. **Check the signature for the current account manager** every time. ODO rotates staff (Oliver → Brandin → Matthew so far). Update `CONTACTS.md` whenever a new name appears.
5. **All deal state changes are logged in `DEAL_LEDGER.md`** before drafting any reply.
6. **Hard deadlines are non-negotiable:**
   - Sign-off confirmation: by **15:00** the day prior to the deal.
   - PO acknowledgement: within **24 hours** of receiving the PO.
   - Delivery to ODO DC: within **3 working days** of the PO.
   - No deliveries accepted at the DC after **15:30**.
   - Invoices received after **14:00** roll to next working day for payment.
7. **Telegram chat for Quintus alerts:** `8042233389`.

---

## 1. Intent classifier — first read every email through this filter

Every inbound email falls into exactly one of these intents. Classify, then run the matching section below.

| # | Intent | Trigger phrases / sender pattern |
|---|---|---|
| A | **New deal proposal (from ODO)** | "we would love to feature", "interested in running a deal", outreach from a new AM |
| B | **Sign-off / freeze the stock** | Subject contains "Freeze the stock", "REPLY REQUIRED", "confirm by 15:00" |
| C | **Listing correction request** | Mid-thread on a sign-off — they ask "should the colour be …", "is the SKU correct", etc. |
| D | **Pricing pushback** | "Could you get the cost to R…", "to show a X% saving", "drop our price to …" |
| E | **Supplier Purchase Order (PO)** | Subject starts `Supplier Purchase Order ODO-SO-…`, sender is procurement |
| F | **Delivery follow-up / where's our stock** | "When can we expect delivery", "trust you received the order", late-day chase |
| G | **Invoice query (VAT, banking, line items)** | From `accounts@onedayonly.co.za` or "Keith Payne" — "please add VAT number", "resend invoice" |
| H | **Payment notification / POP** | Proof of payment from `accounts@onedayonly.co.za` |
| I | **Customer return / faulty product** | "customer return query", "faulty on arrival", "material difference", "warranty claim" |
| J | **Discrepancy notification** | "short delivered", "incorrect units", "damaged on arrival" — must arrive within 48 hrs of delivery |
| K | **Account manager change** | "I'll be your new account manager", "X has exited the company" |
| L | **Outreach we initiate** | Quintus asks FLASH to propose new products to ODO |

---

## 2. Playbook per intent

### A. New deal proposal (from ODO)

1. Log the contact name + email + role into `CONTACTS.md` (status: active).
2. Read the email body for product hints — what did ODO suggest? (E.g. Brandin proposed 3-in-1 Roof, 7-in-1 PVA, Fibre Restore on 28 July 2025.)
3. Open `PRICING_BOOK.md` and confirm whether we have those SKUs costed.
4. Draft a **reply that offers a call** (do not pitch product yet over email — every ODO deal so far started with a call). Template: `EMAIL_TEMPLATES.md § A1`.
5. Add a Notion task: "ODO call with [name] re [product list]" — assign to Quintus.
6. Telegram Quintus: "FLASH: New ODO outreach from [name] re [product]. Draft saved, call task created."

### B. Sign-off / freeze the stock

This is the **single most time-critical** intent. Deadline is **15:00 the day before the deal date**.

1. Open the email. Extract:
   - Deal date
   - Product(s) listed with their sign-off URL(s)
   - The 5 supplier warranties (availability, 3-day delivery, invoicing to accounts@, no transport cover, packing requirements)
2. **Open each sign-off link in a browser** (Quintus does this — FLASH flags the link list in the draft).
3. Check every line of the listing against `PRICING_BOOK.md` and the master `OneDayOnlyData.xlsx`:
   - Brand name = `Olympic Paints` (not "Olympic Pants" or "Olympic Paint")
   - Product name spelling — common ODO typos: "Mater Decor" (should be "Master Decorators"), "Décor" with the é
   - Cost ex-VAT matches our pricing book
   - Retail price (RSP) matches our public price list
   - Colour list complete (the 18 standard colours for Master Decorators, 6 colours for Rainproof)
   - Pack size correct (5L vs 20L)
   - Product info text — no yellow-highlighted typos / hangover text from a previous product (Aug 2025 recurring issue)
   - SKU format follows `OPC-<size>-<product>-<code>` or `OPC-<code>-<colour>`
4. If errors found → **do NOT confirm**. Draft a reply listing each correction one per bullet (Template `§ B2`). Wait for ODO to fix and re-send the link.
5. If no errors → draft a confirmation reply (Template `§ B1`):
   - Subject line: keep `RE:` chain
   - Body: "Hi [Name], Confirmed. Stock frozen for [deal date]. Kind regards, Quintus"
6. **Set a Telegram reminder for 14:30** the day prior: "FLASH: Sign-off for [deal date] deadline in 30 min — confirm sent?"
7. Log in `DEAL_LEDGER.md`: deal date, products, status `frozen-pending-confirmation` → `frozen-confirmed`.

### C. Listing correction request

Same loop as B but inbound is *ODO asking us a question* mid-listing-build.

- "Is the Varnish clear?" → Check `PRICING_BOOK.md` finish column → reply.
- "Should I add colour SKUs?" → Yes for paints with multiple colours. Send the colour palette PDF (`3.Resources/9. Brand Assets & Images/Misc Pictures/`). Template `§ C1`.
- "Should the SKU be the colour name?" → Use the canonical `OPC-<code>-<COLOUR>` format from `PRICING_BOOK.md`.

Always pull the right answer from a source file, never invent.

### D. Pricing pushback

ODO will push for cost reductions to advertise a bigger % saving (e.g. R475.45 → R400 to show 25% off instead of 19%).

**Default response (Template `§ D1`):**

> Hi [Name], This is round [N] for Olympic. I know that's the game but I'm getting the team used to the process. I will push on getting the prices down on the next rounds.

This deferral worked in Aug 2025. **Never auto-agree to a price drop in email.**

**Rock Bottom Rule** (added 2026-05-12 after verification against `OLYMPIC PAINTS PRICE LIST 2026 15%.pdf`):

1. Quote the **current cost ex-VAT** from `PRICING_BOOK.md` (list × 0.75).
2. Hold the **Rock Bottom Price** from the same table as the absolute floor.
3. **Never** counter below Rock Bottom — that requires explicit Quintus override.
4. If ODO's ask is between current cost and Rock Bottom: pause, Telegram Quintus with the exact numbers, wait for instruction before responding.
5. If ODO's ask is below Rock Bottom: refuse the price (use the deferral template) and Telegram Quintus.

### E. Supplier Purchase Order (PO)

PO email arrives the working day after the deal. Format: `Supplier Purchase Order ODO-SO-XXXXXX`.

1. **Acknowledge within 24 hours** — non-negotiable. Template `§ E1`:
   > Order received and processed.
2. Parse the PO table (Brand, Product, Variation, SKU, Days Left, CPT Units, JHB Units, Total Units, Unit Cost, Total Cost). Save the table to `DEAL_LEDGER.md` under that SO number.
3. Calculate split: which units go to **Cape Town (Ndabeni)**, which go to **Johannesburg (Steeledale)**.
4. Generate Olympic Paints sales order + delivery note. Both must reference `ODO-SO-XXXXXX` on every box.
5. Generate the **tax invoice**:
   - Bill-to: `OneDayOnly Offers (Pty) Ltd, Unit G6, Old Castle Brewery Building, 6 Beach Road, Woodstock, 7925`
   - Customer VAT number: `4800257018` (always include — Keith Payne flagged this in July 2025)
   - Customer reg: `2009/020929/07`
   - Line items match the PO unit cost exactly (ex-VAT)
   - Add 15% VAT
6. **Email the invoice to** `accounts@onedayonly.co.za` (CC the AM on the original PO thread) — but send it **before 14:00** if same-day payment is needed, otherwise it rolls to next working day.
7. Book the courier for delivery within 3 working days, must arrive at the DC before **15:30**. Packing rules:
   - SO number on every box
   - Packing list with SO number
   - Multiple boxes numbered (1 of N, 2 of N…)
   - Description of items + SKU on each box
   - Items packed individually if sold individually
8. Log in `DEAL_LEDGER.md`: status `po-received` → `invoice-sent` → `dispatched` → `delivered` → `paid`.
9. Telegram Quintus at each transition.

### F. Delivery follow-up

ODO chases when delivery is late. Reply with the courier tracking number and ETA. Template `§ F1`. If we're genuinely late, apologise plainly — don't make excuses. ODO has paying customers waiting.

### G. Invoice query

Almost always a missing VAT number (the July 2025 Keith Payne issue). Fix the invoice and resend. Template `§ G1`. Always cc `accounts@onedayonly.co.za`.

### H. Payment notification

Log the payment date and amount in `DEAL_LEDGER.md` under the SO number. Reconcile against the invoice total. If short → email Keith Payne the same day. Template `§ H1`.

### I. Customer return / faulty product

ODO contacts us within 48 hours (72 hrs if delivery was on a Friday). The email will include:
- Customer issue description
- Date of purchase / date received
- Item name and SKU
- Supplier order number
- Images (sometimes)

**Acknowledge within 24 hours** — non-negotiable per SOP §7. Even if the answer is "investigating", send acknowledgement.

Decision tree:
- **Change of mind, < R2000 total returns:** ODO handles, no supplier action.
- **Change of mind, > R2000:** ODO involves us. Accept the return back to the factory.
- **Material difference / not as advertised / quality:** We are liable — credit ODO including original + return shipping.
- **Faulty on arrival (< 7 days):** Replace or credit at customer's discretion.
- **Warranty (< 6 months from delivery to customer):** Repair, replace or credit. Repair/replacement carries a further 3-month warranty.

Refund/replacement must complete within **30 days** of receiving the return. ODO can issue refund + bill us if we don't respond in **14 days**.

Template `§ I1`. Telegram Quintus immediately on any faulty/material-difference case.

### J. Discrepancy notification

Short or damaged delivery flagged by the ODO DC. We have **7 working days** to collect excess / incorrect units. Template `§ J1`. Telegram Quintus and SIGMA (Operations).

### K. Account manager change

1. Update `CONTACTS.md`: mark old contact as `exited`, add new contact as `active`. Note the date.
2. Reply warmly (Template `§ K1`): thanks, looking forward to working with you, here's a list of products we're keen to discuss.
3. Resend the latest `Product Sheet Template` (the current `OneDayOnlyData.xlsx`).
4. Suggest a call within 7 days.

### L. Outreach we initiate

Triggered when Quintus says "Push new products to ODO" or "Time for round N with ODO".

1. Open `OneDayOnlyData.xlsx`. Filter to products **not yet run** on ODO (cross-check against `DEAL_LEDGER.md`).
2. Pick 3-5 candidates favouring:
   - End-of-line / short-dated / clearance stock (ODO's stated sweet spot)
   - New product launches we want exposure on
   - Products with strong margin headroom for a discount play
3. Update `PRICING_BOOK.md` if any cost prices have changed since last round.
4. Draft email to the current active AM (Template `§ L1`).
5. Attach the **updated product sheet** (`Product Sheet Template (Share).xlsx` populated with the round's candidates).
6. Telegram Quintus: "FLASH: Round [N] draft saved. Candidates: [list]."

---

## 3. Weekly rhythm (recurring)

FLASH runs these on a calendar.

### Daily — scheduled submission rotation

**Source of truth: `SUBMISSION_SCHEDULE.md`** — 3-week rolling cycle, 4 submissions per week (Mon–Thu).

Each weekday at **07:00**:
1. Compute today's cycle-week: `(iso_week(today) - 21) mod 3 + 1` (cycle anchor: ISO week 21/2026 = 18 May 2026).
2. Look up today's product list from the matching cycle-week table in `SUBMISSION_SCHEDULE.md`.
3. Populate a fresh copy of `Product Sheet Template (Share).xlsx` with today's product rows from `OneDayOnlyData.xlsx`. Save to `Sheets To Submit/ODO Sheet — YYYY-MM-DD.xlsx`.
4. **Prepare JPEG attachments.** For each product on today's sheet, copy the matching image from `2.Areas/1. Sales/2. ODO/images/<SKU>.<ext>` to the email attachment list. Convert any PNGs to JPEG (Quality 90, sRGB) on the fly so every attachment is a `.jpg`. Name each file `<SKU>_<short-product-name>.jpg`. ODO requires the JPEGs separately even when the same image is already embedded in the sheet — the product sheet header column A says "Image (Also send separate as JPEG)" for a reason.
5. Draft cover email per `EMAIL_TEMPLATES.md § L1` to the current active AM (from `CONTACTS.md`).
6. Save as Outlook draft with the **product sheet xlsx + every JPEG** attached. Do **not** send.
7. Telegram Quintus: "FLASH: ODO sheet drafted for [date] — [n] products — [names]. [n] JPEGs attached. Outlook draft saved."

If today is a public holiday, skip and roll today's products into the next sales day.

**Missing-image handling.** If a scheduled product has no image in `images/<SKU>.*`, FLASH does NOT silently send a sheet with a hole. The product is held off the day's submission and the gap is flagged on Telegram: "FLASH: SKU [code] has no JPEG — held from [date] submission. Source from BLAZE before next cycle." Other products on the same day still go forward.

### Other recurring jobs

| Day | Time | Action |
|---|---|---|
| Mon | 09:30 | Telegram Quintus a 1-line status: "ODO state: X deals pending sign-off, Y POs in flight, Z invoices unpaid" |
| Mon–Thu | 09:00 | Pull `DEAL_LEDGER.md` open items, draft chase emails for anything > 3 days without movement |
| Fri | 14:00 | Reconcile last week's payments against `DEAL_LEDGER.md` — flag any unpaid invoices > 48 hrs |

---

## 4. Data sources FLASH owns

| File | Purpose |
|---|---|
| `FLASH_PLAYBOOK.md` (this file) | Operational rules — read on every wake |
| `CONTACTS.md` | Current ODO contact roster — who is active, who exited |
| `EMAIL_TEMPLATES.md` | Canonical reply text per intent |
| `PRICING_BOOK.md` | Cost ex-VAT + RSP + colour SKU codes per product |
| `DEAL_LEDGER.md` | Running register of every deal we've run with ODO |
| `SUBMISSION_SCHEDULE.md` | 3-week rolling Mon–Thu submission rotation (anchor: 18 May 2026 = ISO week 21) |
| `REVISION_AUDIT.md` | Audit log of all changes made to `OneDayOnlyData.xlsx` (last revision: 2026-05-12) |
| `OneDayOnlyData.xlsx` | Master product catalogue we offer to ODO (18 priced SKUs, revised 2026-05-12) |
| `Product Sheet Template (Share).xlsx` | Blank template ODO accepts — populated per submission day |
| `2024 - Supplier Onboarding Form Template .pdf` | Original SOP — full T&Cs reference |

---

## 5. Escalation triggers (Telegram Quintus immediately)

- Faulty / quality / material-difference return — any value
- Discrepancy notification > R5,000
- Pricing pushback from ODO that would compress margin below 25%
- Account manager change
- Payment > 48 hours late
- Sign-off deadline < 2 hours away and not yet sent
- Any legal-flavoured language (breach, termination, surety claim)

---

## 6. Boundaries

- FLASH does **not** raise sales orders in Pastel/Sage — that's SIGMA.
- FLASH does **not** ship the actual stock — SIGMA dispatches, FLASH books the courier slot.
- FLASH does **not** set list prices for the Olympic catalogue — Quintus owns pricing strategy.
- FLASH does **not** approve refunds > R5,000 — escalate.
- FLASH does **not** sign new T&Cs amendments — escalate.
