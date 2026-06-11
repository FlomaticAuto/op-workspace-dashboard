---
name: op-pamphlet-designer
description: >-
  Design a print-ready Olympic Paints tri-fold pamphlet / brochure / leaflet / handout.
  Produces an A4-landscape, 6-panel tri-fold PDF on the Olympic Paints brand framework
  (yellow + navy, Barlow Condensed / Barlow, fold-correct panel order). Use whenever the
  user wants to create, update, or re-skin an Olympic Paints pamphlet, brochure, flyer,
  product leaflet or trade handout. Triggers: "OP pamphlet", "Olympic Paints brochure",
  "make a leaflet/handout", "trifold", "product pamphlet", or any variation. Content is
  supplied via a JSON file; the framework, fonts and layout are fixed and on-brand.
---

# Olympic Paints — Pamphlet Designer

Builds a **print-ready A4 tri-fold pamphlet** (6 panels, double-sided) using the locked
Olympic Paints brand framework. You only write the *content*; the layout, fonts, colours
and fold logic are handled for you.

## When to use
Any request to create or update an Olympic Paints pamphlet, brochure, leaflet, flyer,
product handout or trade one-pager. For other formats (poster, web page, dashboard) use
the `olympic-paints-brand` skill instead.

## How it works (do this)
1. **Gather content.** Confirm what goes on each panel: front cover line, the contact /
   store details, the product list (name, one-line use, spread rate, colour swatches,
   packshot image), the "Why Olympic Paints" reasons, and any lifestyle/cover image.
   Pull product facts and addresses from `3.Resources/17. Strategic Intelligence/` and
   brand assets from `3.Resources/9. Brand Assets & Images/`.
2. **Copy the template.** Duplicate `templates/content.example.json` to a working file
   (e.g. `examples/<campaign>.json`) and edit the values. Image paths are relative to the
   JSON file. Leave HTML entities like `&mdash;`, `&middot;`, `m&sup2;/&#8467;` as-is.
3. **Build.**
   ```
   python scripts/build_pamphlet.py --content <your.json> --out <output>.pdf
   ```
   (Needs `weasyprint` and `pillow`: `pip install weasyprint pillow --break-system-packages`.)
4. **Verify.** Render each page to PNG and eyeball it before sharing:
   ```
   pdftoppm -png -r 110 <output>.pdf preview
   ```
   Check: nothing overflows a panel, fold order is right, images aren't awkwardly cropped,
   text fits. Adjust the JSON and re-run. Then copy the PDF to `2.Areas/8. Marketing/`.

## The fixed framework
A4 landscape (297×210mm), two pages, letter-fold. Tuck panel = 97mm, others = 100mm.

```
OUTSIDE (page 1)  L->R :  INTRO (tuck)   |  BACK cover   |  FRONT cover
INSIDE  (page 2)  L->R :  PRODUCTS A     |  PRODUCTS B   |  WHY (tuck)
```
- **FRONT** — logo badge, "Inspiring Colour", est. line, surfaces strip (navy).
- **BACK** — contact / store address, "Stock Olympic" CTA, reg + disclaimer (white).
- **INTRO** (tuck) — either a full-bleed image (e.g. the contractor "Inspiring Colour
  Since 1981" graphic) OR a written "Who We Are / Inspiring Colour" panel with vision text.
- **PRODUCTS A / B** — up to 4 + 3 products, each with packshot, one-line *substrate-correct*
  use, spread rate, and circular colour swatches. Panel B also carries the tinting note + chips.
- **WHY** (tuck, last panel) — numbered reasons, plus an optional lifestyle image or CTA.

See `reference/framework.md` for the full JSON schema, brand tokens, and design rules
(substrate matching, image-fit, colour-on-colour rules).

## Hard rules
- **Heritage = 1981** ("over 40 years"). The 1997 in the reg number is the cc registration,
  not the founding year. Never put "since 1997" as the founding date.
- **Match each coating to its real substrate** (enamels = metal & wood; PVA/acrylic = walls;
  roof paint = roofs; varnish = timber). Do not imply a product works on a surface it doesn't.
- **Spread rates** in the example are typical industry figures — confirm against the product
  TDS before publishing if exact numbers matter.
- **Colour rules:** black text on yellow only; white/light-blue on navy; never navy text on white.
- Always use the **real logo asset** (the script auto-trims its white border). Never redraw it.
- Tell the user the print shop may want **3mm bleed + crop marks** added for a long run.
