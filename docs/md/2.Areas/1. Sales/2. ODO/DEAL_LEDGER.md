# FLASH — ODO Deal Ledger

Running register of every deal Olympic Paints has run on OneDayOnly. **Every state transition is logged here before drafting any email.** The ledger is FLASH's source of truth — emails reference it, not the other way around.

---

## State machine

```
proposed → frozen-pending-confirmation → frozen-confirmed
  → deal-live → po-received → invoice-sent → dispatched
  → delivered → paid → closed
```

Possible branches:
- `proposed → killed` (deal didn't run)
- any state `→ disputed` (return/discrepancy/payment dispute)

---

## Deal log

### Deal 1 — SO-280164  ·  Deal date 2025-07-02  ·  Status: `closed`

| Field | Value |
|---|---|
| Account manager | Oliver Wood |
| Initial product sheet sent | 2025-06-23 |
| Updated sheet sent | 2025-07-01 10:19 |
| Freeze-the-stock email | (received before 2025-07-01) |
| Confirmation sent | (before 15:00 2025-07-01) |
| PO received | 2025-07-04 08:31 |
| PO acknowledged | 2025-07-04 14:51 — "Order Received and processed" |
| Invoice | 125825 — Keith Payne flagged missing VAT, resent with `4800257018` |
| Total invoiced | R 7,385.00 ex-VAT |
| Payment status | Paid (COD) |

**Line items (PO SO-280164):**

| Product | Variation | SKU | CPT | JHB | Total | Unit cost | Line total |
|---|---|---|---|---|---|---|---|
| 20L Décor Acrylic PVA | White | OPC-20L-DECOR-139401 | 0 | 13 | 13 | 260.00 | 3,380.00 |
| 20L Décor Acrylic PVA | Cream | OPC-20L-DECOR-139411 | 0 | 7  | 7  | 260.00 | 1,820.00 |
| 5L Rainproof Paint | Black | OPC-5L-RAINPROOF-389821 | 0 | 7 | 7 | 95.00 | 665.00 |
| 5L Rainproof Paint | Charcoal | OPC-5L-RAINPROOF-389822 | 0 | 2 | 2 | 95.00 | 190.00 |
| 5L Rainproof Paint | Grey | OPC-5L-RAINPROOF-389825 | 0 | 12 | 12 | 95.00 | 1,140.00 |
| 5L Rainproof Paint | Terracotta | OPC-5L-RAINPROOF-389876 | 0 | 2 | 2 | 95.00 | 190.00 |
| **Total** | | | **0** | **43** | **43** | | **7,385.00** |

**Lessons learned:**
- All units shipped to JHB (Steeledale) — none to CPT. Watch for this skew in future deals to plan stock allocation.
- Best-seller: Rainproof Grey (12 units, 28% of total units).
- VAT number must be on the invoice from day 1 — don't wait for Keith to ask.

---

### Deal 2 — SO-283881  ·  Deal date 2025-08-05  ·  Status: `closed` (assumed — verify payment)

| Field | Value |
|---|---|
| Account manager | Brandin Gooding → Matthew Van Schalkwyk (handover during round) |
| Initial product sheet sent | 2025-07-16 12:36 (to Oliver, then resent to Brandin 2025-07-29) |
| Freeze-the-stock email | 2025-08-04 |
| Listing corrections | 5 corrections during 11:43-12:56 on 2025-08-04 (typo "Mater Decor", yellow-highlight on application areas, colour addition x2) |
| Pricing pushback | 2025-08-04 13:19 — Matthew asked for cost R400 (from R475.45); deferred to next round |
| Colour palette PDF sent | 2025-08-04 13:06 (Colour Pallet.pdf, 71 KB) |
| Confirmation sent | 2025-08-04 (before 15:00) |
| PO received | (working day after deal, ~2025-08-06) |
| PO acknowledged | _verify_ |
| Total invoiced | R 7,202.35 ex-VAT |
| Payment status | _verify in Pastel / accounts_ |

**Line items (PO SO-283881):**

| Product | Variation | SKU | CPT | JHB | Total | Unit cost | Line total |
|---|---|---|---|---|---|---|---|
| 20L Master Decorators PVA | Shiloh | OPC-209401-SHILOH | 0 | 4 | 4 | 475.45 | 1,901.80 |
| 20L Master Decorators PVA | Stone Grey | OPC-209401-STONE-GREY | 0 | 4 | 4 | 475.45 | 1,901.80 |
| 20L Master Decorators PVA | White | OPC-209401-WHITE | 0 | 3 | 3 | 475.45 | 1,426.35 |
| 5L Wood Varnish & Protector | Clear | OPC-419881 | 0 | 8 | 8 | 246.55 | 1,972.40 |
| **Total** | | | **0** | **19** | **19** | | **7,202.35** |

**Lessons learned:**
- ODO will negotiate cost down to fit their "% saving" banner. The R400 ask was rebuffed with the Round-2 deferral language and it stuck — log the language as the canonical pushback in `EMAIL_TEMPLATES.md § D1`.
- Listing corrections always come *during* the sign-off window. Proof every line of the sign-off page against `PRICING_BOOK.md` before confirming.
- Again all units to JHB — Olympic-Paints-on-ODO is currently a Gauteng-skewed audience.
- Multi-colour SKUs work: 18 colours of Master Decorators were offered, 3 sold. ODO's "dropdown" deal format is the right vehicle for our painted products.

---

## Open deals

### Round 3 / Submission 1 — Monday 18 May 2026  ·  Status: `proposed`

| Field | Value |
|---|---|
| Submission date | 2026-05-18 (drafted 2026-05-12) |
| Cycle | Week 1 / Day 1 of the 3-week rotation |
| Products | 20L Décor (`139401`) · 20L Kalahari Contractors (`129401`) · 20L Master Decorators (`209401`) |
| Sheet file | `Sheets To Submit/2026-05-18/ODO Sheet — 2026-05-18.xlsx` |
| JPEG attachments | 3 — all from new 2026 photography backlog (Décor, Kalahari, Master Decorators) |
| Outlook draft | Created — pending Quintus to add the active AM's email address and Send |
| Account manager | _(not yet confirmed — last known: Matthew Van Schalkwyk)_ |

**Line items (proposed):**

| Product | SKU | Cost ex-VAT | RSP | Units |
|---|---|---|---|---|
| 20L Décor Acrylic PVA | `139401` | R 373.16 | R 572.18 | 100 |
| 20L Kalahari Contractors Acrylic PVA | `129401` | R 453.11 | R 694.77 | 100 |
| 20L Master Decorators Acrylic PVA | `209401` | R 638.37 | R 978.83 | 100 |

Next state transition: `proposed → frozen-pending-confirmation` when ODO returns a Freeze-the-Stock email.

---

## Backlog / candidates for next round

From Brandin Gooding (28 July 2025), pre-handover:
- 3-in-1 Roof
- 7-in-1 PVA
- Fibre Restore
- *(Brandin's "dropdown deal" idea: include 2025 Colour Collection colours alongside)*

---

## Rolling totals

| Metric | Value |
|---|---|
| Deals run | 2 |
| Total units shipped | 62 |
| Total invoiced ex-VAT | R 14,587.35 |
| CPT split | 0 % |
| JHB split | 100 % |
| Returns / disputes | 0 |

---

## Append protocol

Every new entry must include:
- SO number (or `pending` if not yet issued)
- Deal date
- Status (one of the state-machine values)
- Account manager active at the time
- A line-item table
- A "lessons learned" stub — fill in after the deal closes

Date entries `YYYY-MM-DD HH:MM` SAST.
