# FLASH — Canonical Email Templates

Every template below is intentionally short. ODO communication is transactional; long paragraphs slow the cycle. FLASH personalises the salutation and slot variables (`[Name]`, `[Date]`, etc.) — the rest stays verbatim unless Quintus edits before send.

**Sign every reply:** `Kind regards,\nQuintus Lategan\nOlympic Paints`

---

## § A — New deal proposal received

### A1 — First reply to ODO outreach (offer a call)

```
Hi [Name],

Thanks for reaching out and for the introduction to OneDayOnly.

We'd like to explore running deals on your platform. Let's set up a call so we can discuss product candidates and the process in more detail.

Are you available [day] or [day] this week?
```

---

## § B — Sign-off / freeze the stock

### B1 — Clean confirmation (no errors found)

```
Hi [Name],

Confirmed. Stock frozen for [deal date].

Products signed off:
  - [Product 1]
  - [Product 2]
```

### B2 — Corrections required (errors found)

```
Hi [Name],

Before we confirm, please correct the following:

1. [Specific error e.g. "Product name reads 'Mater Decor' — should be 'Master Decorators'"]
2. [Specific error e.g. "Yellow highlight on the application areas paragraph under Product Features — please remove"]
3. [Specific error]

Once updated, please resend the sign-off link and we'll confirm in time for the 15:00 deadline.
```

---

## § C — Listing correction request from ODO

### C1 — Sending colour palette / SKU list for multi-colour products

```
Hi [Name],

Attached is the colour palette PDF and the SKU list for [product]:

  - [Colour 1]  — OPC-[code]-[COLOUR1]
  - [Colour 2]  — OPC-[code]-[COLOUR2]
  - ...

Use the colour name as the variation label.
```

### C2 — Confirming a single attribute (varnish clear, paint white, etc.)

```
Hi [Name],

Confirmed — [attribute, e.g. "the Varnish is clear and the Acrylic is white"].
```

---

## § D — Pricing pushback (ODO asking for a lower cost)

### D1 — Deferral (standard response)

```
Hi [Name],

This is round [N] for Olympic. I know that's the game but I'm getting the team used to the process. I will push on getting the prices down on the next rounds.

For this round let's run at the costs already agreed.
```

### D2 — Counter (if we can move but not as far as ODO asked)

```
Hi [Name],

I can get [product] to R[counter price] ex-VAT. That gets your saving to [X]%. Lower than that won't work for us this round.

Let me know and I'll update the sign-off.
```

---

## § E — Purchase Order received

### E1 — PO acknowledgement (send within 24 hrs)

```
Hi [Name],

Order received and processed. SO [ODO-SO-XXXXXX] booked for delivery within 3 working days.

Invoice will follow to accounts@onedayonly.co.za.
```

### E2 — Delivery confirmation when courier is booked

```
Hi [Name],

Stock for SO [ODO-SO-XXXXXX] dispatched today.
Courier: [courier name]
Waybill: [number]
ETA at [CPT/JHB] DC: [date]
Boxes: [N] boxes, all marked with SO number.

Tax invoice has been sent to accounts@onedayonly.co.za.
```

---

## § F — Delivery follow-up from ODO

### F1 — On track

```
Hi [Name],

Stock dispatched [date]. Waybill [number] with [courier].
ETA at [CPT/JHB] DC: [date].
```

### F2 — Late (plain apology, no excuses)

```
Hi [Name],

Apologies for the delay on SO [number]. Stock is dispatching today, [courier], waybill [number]. ETA at the DC: [date].
```

---

## § G — Invoice / VAT query

### G1 — VAT number added and invoice resent (the Keith Payne pattern)

```
Hi Keith,

Updated invoice attached with your VAT number 4800257018 added.

Original invoice [number] cancelled — please use [new invoice number] for settlement.
```

---

## § H — Payment notification / POP

### H1 — Payment received, reconciled

```
Hi Keith,

Payment received and reconciled against invoice [number] for SO [ODO-SO-XXXXXX].

Thank you.
```

### H2 — Payment short / mismatched

```
Hi Keith,

Payment received against SO [ODO-SO-XXXXXX] for R[amount], but the invoice total was R[expected]. Please can you confirm the variance.

Invoice attached for reference.
```

---

## § I — Customer return / faulty / warranty

### I1 — Acknowledgement (always send within 24 hrs)

```
Hi [Name],

Received — looking into the return on SO [ODO-SO-XXXXXX], item [SKU].
I'll come back to you within [N] working days with assessment / next steps.
```

### I2 — Accepting return and crediting

```
Hi [Name],

We accept the return on [SKU], SO [ODO-SO-XXXXXX].
Credit note [number] attached — please apply against future settlement.

Return courier: [arrangement]
```

### I3 — Disputing return (item not faulty)

```
Hi [Name],

We've assessed the unit returned against SO [ODO-SO-XXXXXX] (SKU [SKU]).
Finding: [detailed description of assessment]

Per SOP §7 we are dispatching the unit back. Waybill: [number].
```

---

## § J — Discrepancy notification from ODO DC

### J1 — Acknowledgement + collection arrangement

```
Hi [Name],

Acknowledged. We'll arrange collection of [N] excess / incorrect units from your [CPT/JHB] DC within 7 working days.

Courier: [arrangement] · Booking ref: [number]
```

---

## § K — Account manager change

### K1 — Warm welcome + product reload

```
Hi [Name],

Welcome — looking forward to working with you.

Attached is our current product sheet. A few candidates I'd like to put forward for the next round:
  - [Product 1]
  - [Product 2]
  - [Product 3]

Happy to set up a call to walk through these.
```

---

## § L — Outreach we initiate (new round)

### L1 — Push new products to ODO

```
Hi [Name],

We'd like to run another deal on OneDayOnly. Attached is the product sheet with [N] candidates for round [N]:

  - [Product 1] — [size], R[cost] ex-VAT, [units] units
  - [Product 2] — [size], R[cost] ex-VAT, [units] units
  - ...

Product JPEGs are attached separately, one per SKU.

Let me know what works and we can move on sign-off.
```

**Attachments rule for Intent L emails:**
1. The populated `Product Sheet Template (Share).xlsx` (renamed `ODO Sheet — YYYY-MM-DD.xlsx`)
2. **One JPEG per product on the sheet**, named `<SKU>_<short-name>.jpg`. PNGs from `images/` must be converted to JPEG (Quality 90, sRGB) before attaching. ODO needs the standalone images even when the sheet has them embedded — their listing system pulls from the JPEGs, not the cells.

---

## Style rules

1. **Salutation**: `Hi [Name],` — never `Dear`, never `Good day`.
2. **Sign-off**: always `Kind regards, Quintus Lategan, Olympic Paints` unless the email is from Quintus's personal address.
3. **Tone**: friendly but transactional. Don't apologise unnecessarily — only when we're genuinely late or wrong.
4. **Subject lines**: never start a new one. Always reply to keep the deal thread intact.
5. **Attachments**: confirm them in the body. "Attached is X."
6. **Names**: copy the spelling and capitalisation from the contact's own signature.
7. **Numbers**: always cite the SO number when referencing a specific order — never just "the order".
