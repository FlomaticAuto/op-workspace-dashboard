# PULSE — Rep Walkthrough Guide

**For:** Sales reps (AC / AP / BV / NP / BM)
**Updated:** May 2026
**Purpose:** Step-by-step guide to reading your daily email and using the PULSE web app.

---

## Part 1 — Your daily email

### Step 1 — Open your PULSE email

Your email arrives each weekday morning. The subject line tells you the most important things immediately:

> **PULSE [AC] — Rank #2/5 · 78% of target · Mon 18 May**

You know your rank and your target % before you even open the email.

---

### Step 2 — Read your rank and cycle code

At the top of the email body:

```
┌─────────────────────────────────────────────┐
│  Rank #2 of 5 · 78% of target               │
│  AC2 · Day 2/5                              │
└─────────────────────────────────────────────┘
```

- **Rank #2 of 5** — you are second on the team by % of monthly target
- **78% of target** — you have achieved 78% of your MTD sales target
- **AC2 · Day 2/5** — you are on Cycle 2, day 2 of a 5-day week

![Top of email — rank strip + cycle label](screenshots/02-email-rank-strip.png)

---

### Step 3 — Check your three KPI blocks

Three coloured blocks sit beneath the rank strip:

| Block | What it shows | When it goes red |
|---|---|---|
| **MTD Sales** | Your cumulative net sales this calendar month | Never — informational only |
| **Target** | Your dynamic target for this month | Never — informational only |
| **Achieved %** | MTD Sales ÷ Target | Below 70% |

> **Example:**
> MTD Sales: R 186 200
> Target: R 240 000
> Achieved: **78%** ← amber, within reach

![KPI block row — amber 78% example](screenshots/03-email-kpi-blocks.png)

---

### Step 4 — Tap the yellow button

The yellow **"View today's stores →"** button is the most important element in the email. Tap it to open the PULSE web app directly at your today page.

Do this before you start driving.

![Yellow CTA button in email](screenshots/04-email-yellow-button.png)

---

### Step 5 — Read yesterday's recap

Below the button:

```
Yesterday — 4 visits logged
• Builders Warehouse Polokwane
• OK Hardware Mokopane
• Checkers Hardware Mokopane (×2)
• Pioneer Cash and Carry Lephalale

Sales R 14 800 · 1 lead logged
```

- Each store you checked into in Zoho appears here by name
- **(×2)** means you checked in at that store twice (two separate visits logged)
- The sales figure is yesterday's invoiced revenue attributed to you
- The lead count is leads you recorded in Zoho yesterday

If a visit is missing here, it means it wasn't logged in Zoho. Check your Zoho check-ins.

![Yesterday recap section — list of stores + sales + leads footer](screenshots/05-email-yesterday-recap.png)

---

### Step 6 — Check this week's plan

The week plan shows all five days. Today is highlighted. Other days are visible so you can see what's coming.

```
Mon 18 May ← TODAY (5 stores)
Tue 19 May (4 stores)
Wed 20 May (6 stores)
Thu 21 May (3 stores)
Fri 22 May (4 stores)
```

![Week plan section — today highlighted](screenshots/06-email-week-plan.png)

![Week plan section — continued](screenshots/06-email-week-plan_2.png)

---

### Step 7 — Recovery accounts (if shown)

If you have recovery accounts in your territory, the top 3 appear below the week plan:

```
RECOVERY — TOP 3
────────────────────────────
PIONEER CASH & CARRY BELA-BELA
89 days quiet · score 12

OK HARDWARE MOKOPANE
64 days quiet · score 28

AFRICAN HARDWARE TZANEEN
51 days quiet · score 34

See full recovery list (7) →
```

These are your highest-priority accounts to re-engage. The "score" is a health score — lower is worse. The full list is on the web app Recovery tab.

![Recovery panel — top 3 list](screenshots/07-email-recovery-panel.png)

---

### Step 8 — Check your debtors snapshot

At the bottom of the email:

```
DEBTORS
R 84 300  ← total outstanding across your book

Current    30d       60d ⚠      90d+ 🔴
R 42 100   R 18 000  R 14 200   R 10 000
```

Colour coding:
- **Blue/white** — Current and 30-day: normal, no action needed
- **Amber** — 60-day: flag this to the customer on your next visit
- **Red** — 90-day+: your accounts team needs to be involved; mention it to Quintus

This is your entire book's combined position. Individual store debtor detail is on the web app.

![Debtors panel — amber 60d + red 90d example](screenshots/08-email-debtors.png)

---

## Part 2 — The PULSE web app

You access the web app by tapping the yellow button in your email, or by going directly to:

`https://olympic-paints-pulse-v2.vercel.app/today/[YOUR REP CODE]`

e.g. `https://olympic-paints-pulse-v2.vercel.app/today/AC`

---

### Step 9 — The four tabs

The web app has four sticky tabs at the top:

```
┌──────────┬────────┬────────┬──────────┐
│ Overview │ Today  │  Week  │ Recovery │
└──────────┴────────┴────────┴──────────┘
```

Tabs stay at the top of the screen as you scroll. Active tab is highlighted in yellow.

![Tab strip — Today tab active](screenshots/09-app-tab-strip.png)

---

### Step 10 — Today tab: your visit plan

The **Today** tab shows every store on your plan for today. Each store is a card:

```
┌─────────────────────────────────────┐
│ BUILDERS WAREHOUSE POLOKWANE    [Clean] │
│ Polokwane · KH042                      │
│ Last purchase: 14 May  R 9 200         │
│ Outstanding:   R 0                     │
│ View invoice & full history →          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ OK HARDWARE MOKOPANE          [60+ Overdue] │
│ Mokopane · KJ018                           │
│ Last purchase: 02 Apr  R 4 400             │
│ Outstanding:   R 8 600 (90+: R 3 100)      │
│ View invoice & full history →              │
└─────────────────────────────────────┘
```

Status badge in the top-right corner:
- **Clean** (green) — no outstanding balance
- **Has balance** (grey) — balance present but within terms
- **Overdue 60+** (amber) — 60-day balance present
- **Overdue 90+** (red) — 90-day balance present — handle carefully

![Today tab — two store cards, one clean, one overdue 60+](screenshots/10-app-today-store-cards.png)

---

### Step 11 — Tap a store card for the full detail

Tapping any store card opens the **Store Detail** page. This is where you prepare for the conversation before you walk in.

**Top section — status badges:**
```
[90+ overdue]  [Tier B]  [Declining]
```

![Store detail — header with status badges](screenshots/11-app-store-detail-badges.png)

**Debtors grid — the full breakdown:**
```
Total outstanding: R 12 400

Current     30d        60d ⚠       90d+ 🔴
R 2 200     R 1 800    R 4 400     R 4 000

12-month sales: R 67 800
```

![Store detail — debtors metric grid](screenshots/12-app-store-detail-debtors.png)

**Last invoice — line by line:**
```
Last invoice · #INV-00412 · 02 Apr 2026

Product                    Qty   Unit     Net
───────────────────────────────────────────────
High Gloss Enamel White 5L  12   R 320   R 3 840
Quick Dry Enamel Black 1L   24   R 89    R 2 136
Turps 5L                     6   R 115   R 690
                                          ──────
3 lines                                  R 6 666
```

You know exactly what they last ordered, at what price, and when. Use this to:
- Lead with a re-order conversation ("you took 12 units of High Gloss in April — how's stock?")
- Spot product gaps ("you haven't taken Quick Dry in a while — have you seen the new colours?")
- Know the debtor amount before they mention it

![Store detail — last invoice line items table](screenshots/13-app-store-detail-invoice.png)

---

### Step 12 — Week tab: your five-day plan

The **Week** tab shows all five days with their stores. Today's day is highlighted with a yellow border.

Use this for:
- Planning the order of your visits within a day
- Spotting if a day is under-loaded or over-loaded
- Identifying which recovery accounts fall in your path this week

![Week tab — today highlighted, other days shown](screenshots/14-app-week-tab.png)

---

### Step 13 — Recovery tab: your full quiet-account list

The **Recovery** tab shows every account in your territory that has been flagged as at-risk, sorted worst-first.

```
Recovery accounts · 7 total

Recovery accounts: 7
Worst score:      12

#1  PIONEER CASH & CARRY BELA-BELA
    BBCB001 · 89 days quiet

#2  OK HARDWARE MOKOPANE
    KJ018 · 64 days quiet

#3  AFRICAN HARDWARE TZANEEN
    TZ004 · 51 days quiet
    ...
```

Each row is a link. Tapping it opens that account's Store Detail page (same as Step 11).

![Recovery tab — ranked list of accounts](screenshots/15-app-recovery-tab.png)

**How to use this tab:**

1. Open it every Monday morning.
2. Look at the top 3. If any are in a town you're visiting this week, plan a drop-in.
3. Note the "days quiet" count. Over 60 days = priority conversation this week.
4. After visiting a recovery account, log the visit in Zoho as normal. Next morning's email will show the visit in Yesterday's recap.

---

## Part 3 — The weekly plan form

Every Thursday you'll receive (or be reminded about) the **PULSE Weekly Intake Form**. It asks two things:

1. **Which cycle week are you running next week?** (1, 2, 3, or 4)
2. **Any deviations?** e.g. "Skipping Phalaborwa on Monday — attending product launch"

This takes under two minutes. The system uses your answer to plan next week's store list in your PULSE emails.

**Deadline: Thursday 16:00.**

If you don't submit, the system assumes the default next cycle. Your stores might not exactly match your actual plan for the week.

![Weekly intake form — cycle radio buttons + deviations text field](screenshots/16-PULSE Weekly Intake Form.png)

---

## Quick reference

| What you see | What it means | What to do |
|---|---|---|
| Rank #5/5 | You are last on the team by % target | Check your week plan — are you visiting enough high-value accounts? |
| Achieved % red (<70%) | More than 30% below target | Talk to Quintus — there may be a structural issue |
| Recovery account — 90+ days quiet | This account hasn't bought in 3 months | Visit this week. Open with their last invoice. |
| 90d+ debt on a store card | Account is 90+ days overdue | Do NOT take an order without checking with accounts first |
| 60d debt amber | 60-day balance on the account | Mention the balance during your visit — polite prompt only |
| Visit missing from Yesterday recap | Zoho check-in wasn't logged | Check your Zoho and log the visit; Quintus sees what the system sees |
| Competitor forms nag (red banner) | You have outstanding competitor price verification forms | Complete the form at the link provided — takes 2 minutes |

---

## Getting help

Reply to any PULSE email — it goes directly to Quintus.

For Zoho questions (visit logging, lead entry), contact Quintus or your area coordinator.

---

*Walkthrough version: May 2026.*
