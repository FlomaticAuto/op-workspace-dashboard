# Pamphlet Framework Reference

## Physical spec
- A4 landscape, 297 × 210 mm, **two pages** (outside, inside). `@page margin: 0`.
- Letter / tri-fold. Three panels per page. **Tuck panel = 97 mm** (folds in first),
  other two = **100 mm**. 97 + 100 + 100 = 297.
- The tuck is the *same physical panel* on both sheets: **outside-left == inside-right**.
- Dashed lines in the PDF mark the two fold positions (guide only — printer imposes).

## Panel map (fixed)
| Page | Left | Middle | Right |
|------|------|--------|-------|
| OUTSIDE (p1) | `intro` (tuck, 97) | `back` (100) | `front` (100) |
| INSIDE  (p2) | `products_a` (100) | `products_b` (100) | `why` (tuck, 97) |

Reading flow when folded: **front cover → open the intro flap → inside spread
(products A → products B → why)**. "Why" is the last panel read.

## Brand tokens
| Token | Hex | Use |
|---|---|---|
| Inspiration Yellow | `#F5C400` | primary, CTAs, "why" panel bg |
| Yellow dark / light | `#D4A800` / `#FEF9E0` | eyebrows / product panel bg |
| Olympic Navy | `#1A3D6E` | chips, accents |
| Navy dark | `#0D2040` | front cover, dark blocks |
| Navy light | `#E8EFF8` | text on navy |
| Ink / White | `#0D0D0D` / `#FFFFFF` | body text / surfaces |
| Grey | `#5C6B7A` | captions |

Fonts: **Barlow Condensed** (display/headings, 700–900, ALL CAPS) + **Barlow** (body, 300–600).
Bundled in `assets/fonts/` and embedded as base64 — the PDF is fully self-contained.

### Colour-on-colour rules
- Yellow bg → black text only.  Navy bg → white or light-blue.  White bg → ink (never navy text).
- Never use yellow as a background under coloured (non-black) text.

## Suggested swatch palettes (circular swatches)
- **Walls (PVA/acrylic):** `#F2EFE7 #F0E3C4 #F2D6C0 #D7BB92 #B8B6AD #A9B596`
- **Roof:** `#3A3D42 #9E4A33 #3B5A3F #59626B`
- **Enamel (metal & wood):** `#FBFBF9 #1A1A1A #6E747B #6E4B2A #B5322B #2E4D3A`
- **Varnish (timber):** `#B5793B #5E3A24 #7A3B2E #C99A5B`
(These are indicative; replace with official SKU colours when available.)

## Substrate matching (do not get this wrong)
| Product type | Correct surface |
|---|---|
| Acrylic / PVA wall paint | interior & exterior walls — plaster, brick, concrete |
| Roof paint | roofs — concrete tiles, IBR, fibre-cement |
| Gloss / QD enamel | metal & wood — doors, trim, steel, gates |
| Varnish | interior & exterior timber |

## content.json schema
```jsonc
{
  "panels": {
    "front":  { "logo": "path", "estd": "...", "tagline": ["Inspiring","Colour"], "sub": "...", "surfaces": "..." },
    "back":   { "logo": "path", "eyebrow": "...", "heading": "...", "visit": ["line1","line2"],
                "contact": {"Call":"...","Email":"...","Web":"..."},
                "cta": {"h":"...","c":"..."}, "badge": "Proudly South African",
                "legal": "...", "disclaimer": "..." },
    "intro":  // EITHER full-bleed image:
              { "mode": "image", "src": "path", "fit": "cover", "pos": "72% 50%" }
              // OR written panel:
              // { "eyebrow":"Who We Are", "heading":"Inspiring<br>Colour",
              //   "paras":["...","..."], "vision":{"label":"Our Vision","text":"..."},
              //   "serve":{"label":"Trusted by","text":"Homeowners · Contractors<br>..."} },
    "products_a": { "eyebrow":"The Range", "title":["One supplier.","Every surface."],
                    "items":[ {"name":"...","image":"path","info":"...","spread":"6&ndash;8 m&sup2;/&#8467;",
                               "colours":["#...","#..."]} ] },        // up to 4 items
    "products_b": { "eyebrow":"More From The Range", "title":"Enamels & woodcare",
                    "items":[ ... ],                                   // up to 3 items
                    "tintnote":{"h":"2 000+ Colours","c":"..."},
                    "chips":["...","..."] },
    "why":    { "eyebrow":"The Olympic Difference", "heading":"Why<br>Olympic Paints",
                "items":[ {"h":"...","b":"..."} ],                     // ~4 reasons
                "image":"path"  // optional lifestyle image; OR "cta":{"h":"...","c":"..."} }
  }
}
```

### Notes
- **Image paths are relative to the content JSON file** (absolute paths also work).
- Text fields accept HTML entities (`&mdash;`, `&middot;`, `&amp;`, `<br>`, `m&sup2;/&#8467;`).
- `intro.mode:"image"` + `pos` controls the crop: `"50% 50%"` = centre, raise the first
  number (e.g. `"72% 50%"`) to nudge the visible area right.
- `why.image` is shown whole (contain) and centred — no cropping.
- The logo loader auto-trims white padding so the badge sits cleanly on navy.

## Image-fit guidance
- **Full-bleed panel images** (`intro`): `fit:"cover"` fills the panel; set `pos` to keep
  important content (faces, text) in frame. Pre-composed poster images (with their own
  text/logo) work best here.
- **In-flow images** (`why.image`, product packshots): shown contained/whole, never cropped.
- For crisp print, supply images ≥ 1000 px on the long edge (300 dpi at placed size).
