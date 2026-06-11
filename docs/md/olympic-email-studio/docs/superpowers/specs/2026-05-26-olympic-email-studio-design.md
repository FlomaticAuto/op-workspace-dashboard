# Olympic Email Studio — Design Spec

**Date:** 2026-05-26
**Author:** Quintus + Claude (brainstorming session)
**Status:** Draft, pending user review
**Implements:** Notion task ["Build a copy skill for Olympic Paints design assets"](https://www.notion.so/35eff48d2bb18105a964eb6716aa5e5d) (2026-05-14), expanded into a web app per session decision.

---

## Goal

Anyone at Olympic Paints (marketing, sales, management) can produce a brand-correct, send-ready trade email in under three minutes by filling a single web form. The web app generates the HTML; the user pastes it into their normal email client (Outlook, Zoho Campaigns, etc.) to send. Sending, list management, and deliverability are explicitly out of scope for v1.

The Notion task framing was *"~10× cheaper than iterating inside Claude Design"* — this is the realised version of that, but extended from "a skill Quintus runs" to "a web tool the company runs."

---

## Non-goals (v1)

- **No sending.** App produces HTML; user sends via their existing email tool. No deliverability, unsubscribe, bounce-handling, or POPIA-compliance burden.
- **No campaign history / analytics.** Stateless generation. Add later if there's demand.
- **No list management.** The "to" line is the user's problem.
- **No consumer marketing templates.** v1 is trade only (Stockists, Reps, Contractors, Architects). Consumer-aspirational copy ("Inspiring Colour, Now Closer to Your Site") is a separate future template family.
- **No multi-language.** South African English only.
- **No image upload at runtime.** Product imagery comes from a curated asset set committed to the repo.

---

## High-level architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (anyone @olympicpaints.co.za, signed in via Clerk SSO)  │
│  ┌────────────────────┐  ┌─────────────────────────────────────┐ │
│  │ /compose           │  │ /preview/[id]                       │ │
│  │ 3-step form        │  │ rendered email + Download / Edit    │ │
│  └─────────┬──────────┘  └──────────▲──────────────────────────┘ │
└────────────┼─────────────────────────┼───────────────────────────┘
             ▼                         │
┌──────────────────────────────────────┴───────────────────────────┐
│  Vercel — Next.js 16 App Router                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ POST /api/render-email                                     │  │
│  │  1. Load voice/{audience}.md + visual-vocabulary.md        │  │
│  │  2. Build system prompt; build user prompt from form data  │  │
│  │  3. generateObject(Claude Sonnet 4.6) via Vercel AI SDK    │  │
│  │  4. Validate JSON with Zod                                 │  │
│  │  5. Render React Email component for the chosen template   │  │
│  │  6. Store HTML in Vercel KV (24h TTL), return previewId    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ GET /api/products → reads lib/products.json                │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ public/assets/ → logo, packshots, banners, icons (CDN)     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                                       ▼
                            Anthropic API (Sonnet 4.6)
```

### Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 16 (App Router) + TypeScript | Vercel-native, server components reduce JS shipped to browser |
| Styling | Tailwind CSS + shadcn/ui | Matches Olympic dark-theme aesthetic; shadcn primitives are accessible by default |
| Auth | Clerk, domain-restricted to `@olympicpaints.co.za` | SSO via Google/Microsoft, auto-revokes on staff exit |
| AI | Anthropic Claude Sonnet 4.6 via Vercel AI SDK (`generateObject` + Zod) | Sonnet-class task; typed output catches misbehaving responses |
| Email rendering | `@react-email/components` + `@react-email/render` | Outputs Outlook 2016-safe table-based inlined HTML |
| Preview cache | Vercel KV (24h TTL) | Built-in, sub-ms reads, free tier sufficient |
| Product data | `lib/products.json` (file in repo) | Simple, version-controlled, edit-commit-deploy |
| Hosting | Vercel Pro ($20/mo flat) | One-click deploys, automatic preview URLs per branch |
| Domain (v1) | `olympic-email.vercel.app` | Move to `email.olympicpaints.co.za` after v1 sign-off |

---

## Project layout

```
olympic-email-studio/
├── app/
│   ├── (auth)/sign-in/[[...sign-in]]/page.tsx     # Clerk SSO
│   ├── page.tsx                                    # Landing: "Start a campaign"
│   ├── compose/page.tsx                            # The 3-step form
│   ├── preview/[id]/page.tsx                       # Rendered email + actions
│   └── api/
│       ├── render-email/route.ts                   # POST: form → HTML
│       └── products/route.ts                       # GET: products.json
├── lib/
│   ├── brand/
│   │   ├── design-tokens.ts                        # ported from DESIGN_SYSTEM.md
│   │   ├── visual-vocabulary.md                    # the "how Olympic looks" appendix
│   │   └── voice/
│   │       ├── stockist.md
│   │       ├── sales-rep.md
│   │       ├── contractor.md
│   │       └── architect.md
│   ├── templates/
│   │   ├── product-promotion.tsx                   # React Email component
│   │   ├── price-promotion.tsx
│   │   ├── trade-information.tsx
│   │   └── shared/                                 # Header, Footer, AttributeStrip, MetaBlock
│   ├── ai/
│   │   ├── render-email.ts                         # build prompt, call Claude, validate
│   │   └── schemas.ts                              # Zod schemas for typed AI output
│   ├── products.json                               # seeded SKU list (~15 to start)
│   └── combos.ts                                   # which audience × template combos are valid
├── components/                                     # shadcn form primitives, app-level UI
├── public/
│   └── assets/
│       ├── logo.png                                # Olympic Paints Logo Digital (yellow circle)
│       ├── packshots/                              # hero shots, white background
│       ├── banners/                                # in-context shots (5 existing Olympic Mail banners)
│       └── icons/                                  # attribute icons (v2 — v1 reuses baked banner images)
├── docs/superpowers/specs/
│   └── 2026-05-26-olympic-email-studio-design.md   # this file
├── .env.example                                    # ANTHROPIC_API_KEY, CLERK keys, KV creds
└── next.config.ts
```

---

## Brand layer

### `lib/brand/design-tokens.ts`

A TypeScript port of `DESIGN_SYSTEM.md`, scoped to email needs (no theme toggle, no Chart.js plugin, no dashboard surfaces). Includes:

- **Colors:** brand core (yellow `#F5C400`, navy `#1A3D6E`, black `#0D0D0D`, white), yellow ramp (7 steps), navy ramp (7 steps), neutral ramp (7 steps), mood palette (teal, terra, coral, pink, violet, sage, ink).
- **Fonts:** display = `'Barlow Condensed', 'Arial Narrow', Arial, sans-serif`; body = `'Barlow', Arial, Helvetica, sans-serif`. Outlook on Windows ignores web fonts — fallback stack must look as close as possible to the real face.
- **Type scale:** hero / h2 / h3 / eyebrow / body / caption — explicit px sizes and weights.
- **Spacing scale:** xs/sm/md/lg/xl/xxl.
- **Radius scale:** sm/md/lg/pill.
- **Email constraints:** container width 600px, default theme = light, CSS inlining required, table layout required.

Two deliberate deviations from the dashboard system:
1. **Font fallback stacks** — Outlook strips web fonts; fallback must be carried in every style declaration.
2. **600px container** — universal email-safe width.

### `lib/brand/visual-vocabulary.md`

The appendix the brand guide does *not* have. Extracted from the existing Olympic Mail banners, the Natural Elegance packshot, and the Retail Deck. Codifies:

1. **Hero image conventions** — always wrap lifestyle photos in a 3px solid `#0D0D0D` window frame with 8px radius. Architectural interiors only. Never people. Never close-ups of paint application.
2. **Logo placement** — yellow circle badge top-left of hero (48px). Stockist/partner slot top-right when used.
3. **Yellow usage rule (load-bearing):** yellow is **punctuation**, not background. Allowed: logo badge, price pill, button fill, headline against dark. Forbidden: full-bleed yellow body areas, with one exception: max one full-yellow hero block per email (Product Promotion uses this).
4. **Packshot conventions** — two styles, picked by context: "hero shot" (white background, 3/4 angle, roller-on-can) for Product Promotion; "in-context shot" (composited onto lifestyle) for Stockist banners. v1 uses existing baked banner images; v2 composites on demand.
5. **Product attribute strip** — black 1px-bordered horizontal strip, 5 monochrome icons + caps labels. v1 uses existing banner images with icons baked in; v2 extracts icon set into `public/assets/icons/`.
6. **Typography mood** — product names in Barlow Condensed Black 900, uppercase, 40–56px. Body in Barlow Regular 15px / 1.65 line-height. Sentence case for body. South African English (colour, organisation, programme).
7. **Negative space rules** — no drop shadows on text. No gradients on headlines. No emoji in subject lines. No stock-photo "happy painter" cliché.

### `lib/brand/voice/*.md`

Four files, one per audience. Each file controls **voice rules, CTA vocabulary, meta-block label, meta-block fields (order matters), and sign-off.** Read at runtime and injected into the Claude system prompt.

The audiences are:

- **stockist.md** — hardware-store buyer. Direct, factual, trade language (SKU, MOQ, ex VAT). CTAs: *Place an order*, *Confirm your stock*, *Download price list*. Meta: At a glance — SKU / Pack / Trade price / RRP / Lead time / MOQ. Sign-off: Olympic Trade Team.
- **sales-rep.md** — internal Olympic team. Punchy, action-oriented, talking-points format. CTAs: *Open campaign in CRM*, *Download talking-points PDF*. Meta: Sales talking points — Margin % / Top 5 accounts / Comp vs Dulux / Stock available. Sign-off: Sales Ops.
- **contractor.md** — registered painter. Jobsite-practical, coverage and suitability. CTAs: *Find your nearest stockist*, *View coverage calculator*. Meta: On the job — Coverage / Recoat time / Surfaces / Where to buy. Sign-off: Olympic Painter Programme.
- **architect.md** — specifier. Technical-precise, standards-referenced. CTAs: *Download TDS (PDF)*, *Request a sample*. Meta: Specification data — Finish (sheen %) / VOC g/L / DFT / Standards. Sign-off: Olympic Specification.

---

## Templates

Three trade templates. Each is a React component that renders to email-safe HTML via `@react-email/render`. Layout is fixed per template; copy and CTAs come from the audience voice file + Claude-generated body.

### Template 1 — Product Promotion (`lib/templates/product-promotion.tsx`)

**Use when:** a new SKU is in stock, a re-launched product is shipping again, or a featured product needs trade attention.

**Structure:** Header (Olympic Trade wordmark + date) → black-framed banner with floating packshot bottom-right → headline + body → yellow-bordered "At a glance" meta box → primary CTA + secondary CTA → footer.

**Variables:** product_name, range_name, eyebrow, headline, body, sku, pack_sizes, trade_price, rrp, lead_time, banner_image, packshot_image, cta_primary_url, cta_secondary_url.

### Template 2 — Price Promotion (`lib/templates/price-promotion.tsx`)

**Use when:** running a date-bound promotional price across 1+ SKUs.

**Structure:** Header with explicit validity dates → yellow promo banner strip → headline + body → multi-row price table (Product / Pack / Was / Now / Save) → terms-and-conditions meta block → primary CTA + secondary CTA → footer.

**Variables:** promo_name, valid_from, valid_to, eyebrow, headline, body, price_rows[] (product, pack, was, now, save), terms_text, cta_primary_url, cta_secondary_url.

### Template 3 — Trade Information (`lib/templates/trade-information.tsx`)

**Use when:** communicating a non-promotional change — packaging, formulation, dates, policy, training, system updates.

**Structure:** Header with notice date → no banner image → headline + body → "What's changing" bulleted list → "What stays the same" bulleted list → yellow "What you need to do" action box → primary CTA + secondary CTA → footer.

**Variables:** notice_date, eyebrow, headline, body, changing_items[], unchanged_items[], action_required_text, cta_primary_url, cta_secondary_url.

Trade Information deliberately has no hero image. Information is the substance; an image delays the eye getting to the bullets.

---

## Audience × template combo matrix

The form **disables invalid combinations** so users cannot generate nonsense emails. Final matrix:

| | Product Promotion | Price Promotion | Trade Information |
|---|---|---|---|
| **Stockist** | ✓ | ✓ | ✓ |
| **Sales Rep** | ✓ | ✓ | ✓ |
| **Contractor** | ✓ | ✓ (RRP shown, not trade price — see voice override note below) | ✓ |
| **Architect** | ✓ | ✗ (greyed out — architects don't buy paint; use Trade Information for spec-bound pricing notices) | ✓ |

The combos table lives in `lib/combos.ts` so it's editable in one place. If a user picks an invalid combo, the form shows a tooltip explaining the recommended alternative.

**Voice file field overrides:** voice files can override which columns appear in the Price Promotion price table. For example, `contractor.md` declares `price_table_columns: [product, pack, rrp_was, rrp_now, save]` instead of the Stockist default of `[product, pack, trade_was, trade_now, save]`. The form and the template both read this override at render time. This keeps the layout the same while presenting audience-appropriate pricing.

---

## Compose form (`app/compose/page.tsx`)

Single page, three sections stacked top-to-bottom. Not a multi-step wizard. shadcn/ui components throughout.

**Step 1 — What kind of email?**
ToggleGroup with three options: Product Promotion / Price Promotion / Trade Information. Each option shows a one-line description underneath.

**Step 2 — Who is this for?**
ToggleGroup with four options: Stockist (default) / Sales Rep / Contractor / Architect. Invalid combos with Step 1 are disabled with a tooltip.

**Step 3 — The details**
Conditional field set based on Step 1's choice:

- **Product Promotion fields:** product picker (dropdown from products.json) + auto-fill of SKU/pack/trade price/RRP/lead time (editable) + "what's new about it" textarea + optional AI hint textarea.
- **Price Promotion fields:** promo name + valid_from + valid_to + multi-row price table (add/remove rows; each row picks a product from dropdown and fills was/now/save) + terms textarea + optional AI hint textarea.
- **Trade Information fields:** notice date + headline-direction textarea + "What's changing" multi-line list + "What stays the same" multi-line list + "What you need to do" textarea + optional AI hint textarea.

All three Step 3 variants end with an "Optional — anything else for Claude to emphasise?" textarea, accompanied by a yellow info box explaining what Claude will do and that the copy is editable on the preview page.

Bottom of form: [← Start over] [Generate email →].

Mobile: form collapses to single column under 768px.

---

## Render pipeline (`POST /api/render-email`)

```tsx
// Pseudocode — actual implementation uses Vercel AI SDK
async function POST(req: Request) {
  const formData = await req.json();
  const { template, audience, fields, ai_notes } = formData;

  // 1. Load voice config + brand context
  const voice = await loadVoiceFile(audience);
  const visualVocab = await loadVisualVocabulary();

  // 2. Build prompts
  const systemPrompt = buildSystemPrompt(voice, visualVocab, template);
  const userPrompt = buildUserPrompt(template, fields, ai_notes);

  // 3. Call Claude with typed output
  const { object: copy } = await generateObject({
    model: anthropic('claude-sonnet-4-6'),
    schema: emailCopySchema, // Zod
    system: systemPrompt,
    prompt: userPrompt,
  });

  // 4. Look up product data
  const product = lookupProduct(fields.product_id);

  // 5. Render React Email component → HTML
  const Component = templates[template];
  const html = await render(
    <Component
      tokens={designTokens}
      voice={voice}
      copy={copy}
      data={fields}
      product={product}
    />
  );

  // 6. Cache HTML in Vercel KV
  const previewId = crypto.randomUUID();
  await kv.set(`preview:${previewId}`, html, { ex: 86400 }); // 24h

  return Response.json({ previewId });
}
```

### Zod schema for Claude output

```typescript
const emailCopySchema = z.object({
  eyebrow: z.string().max(80),
  headline: z.string().max(120),
  body: z.string().max(500),
  cta_primary: z.string().max(40),
  cta_secondary: z.string().max(40).optional(),
});
```

If Claude's first response fails validation, we retry once. Second failure returns a 500 with the validation error. We do not silently accept malformed output.

### Cost & latency

- **Per generation:** ~$0.002 (Sonnet 4.6, typical token counts for this prompt size).
- **Cold latency:** ~5–10 seconds (Claude cold start + first KV write).
- **Warm latency:** ~3 seconds (cache hits on prompt caching, fast KV).
- **At 100 emails/month:** Claude cost is ~$0.20/month, well within free credit.

---

## Preview page (`app/preview/[id]/page.tsx`)

Three regions:

1. **Top bar:** `Email preview · {template} · {audience} voice` + actions: [Download HTML] [Copy to Clipboard] [Edit copy] [Regenerate]
2. **The email** rendered in a 600px-wide iframe — what the inbox sees.
3. **Editable copy panel** (collapsible below the preview): JSON Claude returned, every text fragment inline-editable. Edit → preview re-renders client-side with new strings. No new Claude call.

**Edit vs Regenerate:**
- **Edit copy** = "this is 90% right, fix word X." Client-side re-render, zero cost.
- **Regenerate** = "try a different direction." Server call, new Claude generation.

Two different operations for two different intents.

**Suggested subject line:** the preview page shows the email's `eyebrow` text in a "Copy as subject line" chip above the preview. The user clicks it to copy to clipboard, then pastes into Outlook's subject field when sending. This is the v1 substitute for subject-line generation (which is listed as out of scope, item 10).

---

## Product data (`lib/products.json`)

Flat JSON, version-controlled, committed to repo. Seeded from `Packshot Mockups - May 2025/` — approximately 15 SKUs at v1 launch.

```json
[
  {
    "id": "NEP",
    "name": "Natural Elegance Plus",
    "range": "PlatinumPlus",
    "finish": "Silky soft-touch",
    "packshot_url": "/assets/packshots/natural-elegance-plus.png",
    "in_context_url": "/assets/banners/natural-elegance-banner.jpg",
    "skus": [
      { "sku": "NEP-5L-WHT",  "pack": "5L",  "trade_price": 489,  "rrp": 629  },
      { "sku": "NEP-20L-WHT", "pack": "20L", "trade_price": 1749, "rrp": 2199 }
    ],
    "attributes": ["PVA ACRYLIC", "WASHABLE", "INTERIOR", "EXTERIOR", "DURABILITY"],
    "spec": {
      "sheen_pct": 5,
      "voc_g_per_l": 12,
      "coverage_m2_per_l": 11,
      "recoat_hours": 4,
      "standards": ["SANS 1586", "ISO 11998"]
    },
    "spec_sheet_url": "https://olympicpaints.co.za/tds/natural-elegance-plus.pdf"
  }
]
```

**v1 maintenance:** update prices = edit JSON, commit, push, Vercel auto-redeploys (~30s).

**v2 (deferred):** `/admin/products` page editing JSON via a UI, persisted in Vercel KV instead of file, gated by an admin role check in Clerk.

---

## Image hosting

Assets live in `public/assets/` and are served by Vercel's CDN. Emails reference fully-qualified URLs (`https://olympic-email.vercel.app/assets/packshots/natural-elegance-plus.png`) so the images load when the recipient opens the email — no attachments, no broken links.

Seeded asset set (v1):
- **Logo:** copied from `3.Resources/9. Brand Assets & Images/Misc Pictures/Olympic Paints Logo Digital.jpg`
- **Packshots:** copied from `Packshot Mockups - May 2025/` (15 PNGs)
- **Banners:** copied from `2.Areas/8. Marketing/Digital/Olympic Mail (1200 x 325 px)/` (5 PNGs)

A `scripts/sync-assets.ts` script copies these from OneDrive into the repo as part of project setup. Not run at runtime.

---

## Auth (`@olympicpaints.co.za` only)

Clerk handles SSO. Sign-in supports Google (most Olympic staff use Google Workspace) and Microsoft. Clerk middleware in `middleware.ts` enforces:

1. Unauthenticated users redirect to `/sign-in`.
2. Authenticated users with non-`@olympicpaints.co.za` email get a 403 "Access denied — Olympic Paints staff only" page.
3. Authenticated `@olympicpaints.co.za` users can access all routes.

No role hierarchy in v1 — everyone is the same. v2 may add an "admin" role for product-data editing.

---

## Environment variables (`.env`)

```
ANTHROPIC_API_KEY=...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...
KV_REST_API_URL=...        # provisioned by Vercel KV integration
KV_REST_API_TOKEN=...
```

`.env.example` checked into the repo with placeholder values.

---

## Operational cost (v1)

| Item | Cost |
|---|---|
| Vercel Pro | $20/month flat |
| Vercel KV | $0 (free tier covers projected use) |
| Clerk | $0 (free tier covers ≤10k MAU; we'll have ≤20) |
| Claude API | ~$0.20/month at 100 emails/month |
| Domain | $0 (use `olympic-email.vercel.app`, or move to subdomain of existing `olympicpaints.co.za`) |
| **Total** | **~$20/month** |

---

## Out of scope explicitly (revisit in v2+)

1. **Sending** — Zoho Campaigns or SendGrid integration. v2.
2. **Campaign history** — list of past sends with re-open links. v2.
3. **Multi-language** — Afrikaans. v3.
4. **Image upload at runtime** — currently the asset set is curated; users cannot upload their own product images. v2.
5. **A/B variants** — generate two versions of headline/body for testing. v2.
6. **In-context packshot compositor** — currently uses pre-baked banner images; v2 composites a packshot onto a lifestyle photo at render time.
7. **Attribute-icon library** — currently uses the existing banner images with icons baked in; v2 extracts the icons into `public/assets/icons/` for recomposable strips per product.
8. **Admin UI for products.json** — currently a code edit; v2 adds a `/admin/products` editor.
9. **Save-as-draft on the compose form** — currently form state is lost on navigation; v2 persists drafts to KV.
10. **Subject line generation** — v1 the user types the subject themselves into Outlook after pasting. v2 the form asks for it / Claude generates it.

---

## Risks & open questions for review

1. **Outlook 2016 rendering** — even with `@react-email`, some Outlook quirks slip through. We'll need to run a test send through Litmus or Email on Acid before declaring v1 done. Budget half a day for fix-up.
2. **Image-blocking by recipient email clients** — most corporate Outlook installs block external images by default. Our emails should still read sensibly with images off (alt text on every `<img>`).
3. **Clerk domain restriction edge case** — if an Olympic staff member has a non-`@olympicpaints.co.za` Google account they use for work (e.g. a personal Gmail), they're locked out. Acceptable for v1; flag if it bites.
4. **Anthropic API key in Vercel env** — single shared key, no per-user rate limiting in v1. If we ever expose this beyond internal Olympic, we'd need per-user quotas. Not a v1 problem.
5. **The 24-hour preview TTL in KV** — if someone generates an email, leaves it overnight, and comes back the next day, the preview is gone and they have to regenerate. Acceptable; could extend to 7 days if it becomes a complaint.

---

## Approval

- [ ] User has reviewed this spec and approved (or requested changes)
- [ ] Spec is committed to repo before implementation plan begins

