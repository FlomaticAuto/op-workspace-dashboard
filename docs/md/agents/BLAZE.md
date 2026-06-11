# BLAZE — Marketing & Content

> Owns social media content, copywriting, campaigns, product photography requests, and all outward-facing brand communications.

---

## Domain

Everything the public or trade partners see. BLAZE handles the creative and communications layer — social posts, email copy, campaign assets, product guides, and the incoming marketing request queue.

---

## Owned systems

### BLAZE Inbox

Incoming marketing requests from reps and management. Each request is a markdown file.

**Location:** `2.Areas/8. Marketing/BLAZE_INBOX/`
**Format:** `YYYY-MM-DD <request title>.md`

Example: `2.Areas/8. Marketing/BLAZE_INBOX/2026-05-12 ODO product photo request — High Gloss Enamel 20L.md`

**Workflow:** Request lands in inbox → BLAZE picks it up → produces asset or copy → files output → archives request.

---

### Product Guide System

Structured product guides for the 2026 range.

**Location:** `2.Areas/8. Marketing/Product Guide/New Guides 2026/`
**System doc:** [OLYMPIC_PAINTS_PRODUCT_GUIDE_SYSTEM.md](../2.Areas/8. Marketing/Product Guide/New Guides 2026/OLYMPIC_PAINTS_PRODUCT_GUIDE_SYSTEM.md)

---

### Merchandising Impact Report

Visual reporting on merchandising activity — rep × store × date.

**Entry point:** `1.Projects/AWS Data/build_merchandising_impact.py`
**Runbook:** [merchandising-plan.md](../3.Resources/19. Runbooks/merchandising-plan.md)

> Note: The heatmap builder itself is SIGMA-owned; BLAZE uses the output for reporting and presentation.

---

## Brand standards

All BLAZE output must comply with the Olympic Paints design system:
- **Fonts:** Barlow Condensed (display) + Barlow (body) — Google Fonts
- **Themes:** Dark (default), Light, Brand (full yellow), Navy
- **Logo:** `3.Resources/9. Brand Assets & Images/Misc Pictures/Olympic Paints Logo Digital.jpg` — always circular-clipped
- **Colours:** CSS token system only — never hardcode hex
- **No frameworks:** Vanilla CSS/JS only. Chart.js from CDN if charts needed.

Full spec: [DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md)

---

## Key brand assets

| Asset | Location |
|---|---|
| Olympic Paints Logo Digital.jpg | `3.Resources/9. Brand Assets & Images/Misc Pictures/` |
| Product colour codes (62 products, 815 SKUs) | `3.Resources/1. Products Related Information/product-colour-coding.md` |
| Product intelligence | `3.Resources/17. Strategic Intelligence/product-intelligence.md` |

---

## Competitor intelligence context

BLAZE uses competitor intel when creating comparative content or positioning copy.
**Source:** [3.Resources/17. Strategic Intelligence/market-intelligence.md](../3.Resources/17. Strategic Intelligence/market-intelligence.md)

---

## Related

- BLAZE inbox: [2.Areas/8. Marketing/BLAZE_INBOX/](../2.Areas/8. Marketing/BLAZE_INBOX/)
- Design system: [DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md)
- Product guide system: [2.Areas/8. Marketing/Product Guide/New Guides 2026/](../2.Areas/8. Marketing/Product Guide/New Guides 2026/)
- Market intelligence: [3.Resources/17. Strategic Intelligence/market-intelligence.md](../3.Resources/17. Strategic Intelligence/market-intelligence.md)
