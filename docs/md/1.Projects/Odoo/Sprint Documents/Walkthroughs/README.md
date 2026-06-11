# Olympic Paints — Odoo Walkthroughs

Operational walkthroughs for staff using the Olympic Paints Odoo system. Three transaction types, each broken into named phases that match how the work flows through the business.

**Live site:** https://flomaticauto.github.io/olympic-paints-odoo-walkthroughs/

## Contents

| # | Walkthrough | Phases |
|---|---|---|
| 01 | [Sales Order](01-sales-order.html) | Place the Order → Approvals → Confirm & Fulfil → Invoice & Collect |
| 02 | [Customer Collection](02-customer-collection.html) | Take the Order → Issue Stock at Counter → Invoice & Collect |
| 03 | [Vehicle Scheduling](03-vehicle-scheduling.html) | Setup → Find Orders → Build Batch → Assign & Dispatch → Reporting |

## How these were built

These walkthroughs were extracted and consolidated from four UAT sprint documents:

| Document | Pages | Coverage |
|---|---|---|
| Sprint 1 User Guide | 30 | Credit limit · Customer onboarding · Warehouse setup |
| Sprint 2 Test Cases | 35 | Sales order creation · Email import · Discount approval · Customer portal |
| Sprint 4 Test Cases | 56 | Inventory · Stock movements · SKU management |
| Sprint 5 Test Cases | 42 | Deliveries · Batch transfers · Vehicle scheduling · POS |

The originals are test-case documents — structured around "did we build it correctly?" — not user guides. These walkthroughs invert that structure: task-first, with screenshots embedded inline at the relevant step.

## Inline markers

- **👤 Login as X** — pill showing the required user/role for the step
- `Field name` (blue) / `Button` (yellow) / `path/to/screen` — colour-coded inline references
- 🟦 **Info** / 🟨 **Warn** / 🟥 **Danger** / 🟩 **Success** callouts at decision points
- 🔘 **VERIFY** placeholders — flags where the sprint docs were silent and the live Odoo needs to be checked

## Design

Built with the Olympic Paints design system (Navy / Light / Dark / Brand themes, Barlow Condensed + Barlow fonts, official Clickpaint badge). No frameworks — vanilla HTML, CSS custom properties, vanilla JS.

Theme toggle is on every page (top-right). Selection persists across page navigation via `localStorage`.

## Maintenance

To regenerate screenshots from the source PDFs after they change:

```bash
python ../_extracted/extract_images.py
```

This renders every page at 250 DPI into `assets/screenshots/sprint{N}/p{NNN}.png`.

To edit the walkthroughs themselves, open any `.html` file in a text editor — the structure is repetitive on purpose (each step is a `<div class="step">` block with a number, title, and body).

## License

Internal Olympic Paints documentation. Not for redistribution.
