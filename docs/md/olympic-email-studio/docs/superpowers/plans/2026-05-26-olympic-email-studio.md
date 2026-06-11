# Olympic Email Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an internal Next.js web app on Vercel that lets any Olympic Paints staff member generate a brand-correct, send-ready trade email by filling a short form. The app produces a downloadable HTML file; users paste it into Outlook or Zoho Campaigns to send. No sending, list management, or analytics in v1.

**Architecture:** Next.js 16 App Router + TypeScript + Tailwind + shadcn/ui on Vercel. Claude Sonnet 4.6 via the Vercel AI SDK (`generateObject` + Zod) writes the headline and body copy. `@react-email` renders templates to Outlook-safe HTML. Vercel KV caches the rendered HTML for 24h so the preview page can load on refresh. Clerk SSO restricts access to `@olympicpaints.co.za` accounts. Product data lives in a committed `lib/products.json`.

**Tech Stack:** Next.js 16, TypeScript, Tailwind CSS, shadcn/ui, `@anthropic-ai/sdk`, Vercel AI SDK (`ai`, `@ai-sdk/anthropic`), Zod, `@react-email/components`, `@react-email/render`, `@clerk/nextjs`, `@vercel/kv`, Vitest for unit tests.

**Repo location:** `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\olympic-email-studio\`

**Spec:** [`docs/superpowers/specs/2026-05-26-olympic-email-studio-design.md`](../specs/2026-05-26-olympic-email-studio-design.md)

---

## File structure (target)

```
olympic-email-studio/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                                # Landing → "Start a campaign"
│   ├── compose/page.tsx                        # 3-step form
│   ├── preview/[id]/page.tsx                   # Rendered email + actions
│   ├── (auth)/sign-in/[[...sign-in]]/page.tsx  # Clerk
│   ├── api/
│   │   ├── render-email/route.ts               # POST: form → HTML
│   │   └── products/route.ts                   # GET: products.json
│   └── globals.css
├── lib/
│   ├── brand/
│   │   ├── design-tokens.ts
│   │   ├── visual-vocabulary.md
│   │   └── voice/{stockist,sales-rep,contractor,architect}.md
│   ├── templates/
│   │   ├── product-promotion.tsx
│   │   ├── price-promotion.tsx
│   │   ├── trade-information.tsx
│   │   └── shared/{Header,Footer,WindowFrame,MetaBlock,CtaButton}.tsx
│   ├── ai/
│   │   ├── render-email.ts                     # build prompt, call Claude
│   │   └── schemas.ts                          # Zod schemas
│   ├── products.json
│   ├── products.ts                             # typed reader for products.json
│   ├── voice.ts                                # typed reader for voice/*.md
│   └── combos.ts                               # audience × template matrix
├── components/                                  # shadcn primitives + app UI
│   ├── ui/...                                  # shadcn-generated
│   ├── ComposeForm.tsx
│   ├── PricePromoFields.tsx
│   ├── ProductPromoFields.tsx
│   ├── TradeInfoFields.tsx
│   └── PreviewActions.tsx
├── public/assets/
│   ├── logo.png
│   ├── packshots/*.png
│   └── banners/*.{jpg,png}
├── scripts/
│   └── sync-assets.ts                          # copy OneDrive assets → public/assets/
├── tests/
│   ├── design-tokens.test.ts
│   ├── products.test.ts
│   ├── schemas.test.ts
│   └── combos.test.ts
├── middleware.ts                               # Clerk auth gate + domain restriction
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

**File responsibilities:**

| File | What it owns |
|---|---|
| `lib/brand/design-tokens.ts` | All colour, type, spacing, radius constants. Single source of truth — every template imports from here, never hardcodes. |
| `lib/brand/visual-vocabulary.md` | Raw markdown injected into Claude's system prompt. Describes the "how Olympic looks" rules. |
| `lib/brand/voice/<audience>.md` | One per audience. Voice rules, CTA vocabulary, meta-block label, sign-off, price-table column override. |
| `lib/templates/<template>.tsx` | One React Email component per template. Takes `{tokens, voice, copy, data, product}` props. |
| `lib/templates/shared/*` | Small reusable email-safe components (header, footer, window frame, meta block, CTA button). |
| `lib/ai/render-email.ts` | The single function that builds the prompt, calls Claude, validates output. Imported by the API route. |
| `lib/ai/schemas.ts` | Zod schemas for AI output + form input. Re-used by API route, ComposeForm, render-email.ts. |
| `lib/products.json` | Seeded SKU list. Source of truth for the product dropdown. |
| `lib/products.ts` | Typed reader + Zod validation on load. Throws at build time if the JSON drifts from the schema. |
| `lib/combos.ts` | The 4×3 audience × template matrix. Used by the form to disable invalid combos. |
| `app/api/render-email/route.ts` | Thin route handler. Calls `lib/ai/render-email.ts`, renders React Email component, stores in KV, returns previewId. |
| `app/compose/page.tsx` | The form. Renders the right field set based on template choice. |
| `app/preview/[id]/page.tsx` | Loads cached HTML from KV, shows iframe + actions. |
| `middleware.ts` | Clerk auth on every route; domain check on `@olympicpaints.co.za`. |
| `scripts/sync-assets.ts` | One-shot script: copies logo, packshots, banners from OneDrive into `public/assets/`. Run during project setup. |

---

## Implementation order

We build in vertical slices that leave the app demoable at each commit:

1. **Phase 1: Foundation** (Tasks 1–4) — repo scaffold, design tokens, brand files, products.json
2. **Phase 2: First end-to-end path** (Tasks 5–10) — Product Promotion template + Stockist voice + render pipeline + manual API test
3. **Phase 3: The form** (Tasks 11–14) — landing page, compose form, preview page, wire the form to the API
4. **Phase 4: The other templates** (Tasks 15–16) — Price Promotion, Trade Information
5. **Phase 5: The other voices** (Task 17) — Sales Rep, Contractor, Architect
6. **Phase 6: Auth** (Task 18) — Clerk SSO with domain restriction
7. **Phase 7: Deploy** (Tasks 19–20) — Vercel project setup, env vars, KV, first deploy

After Phase 2 the app generates one type of email via direct API call (curl or REST client). After Phase 3 it has a working browser UI. After Phase 7 it's live for the team.

---

## Phase 1: Foundation

### Task 1: Scaffold the Next.js project

**Files:**
- Create: `package.json`, `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `.gitignore`, `.env.example`, `README.md`
- Create: `app/layout.tsx`, `app/page.tsx`, `app/globals.css`

- [ ] **Step 1: Initialise the Next.js app**

Run from `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\olympic-email-studio\`:

```powershell
npx create-next-app@latest . --typescript --tailwind --app --eslint --src-dir=false --import-alias="@/*" --use-npm
```

When prompted, accept defaults. If the folder is not empty, run it in a temp folder and copy contents over.

Expected: a working Next.js 16 app with Tailwind v4 configured.

- [ ] **Step 2: Verify it runs**

```powershell
npm run dev
```

Expected: dev server on `http://localhost:3000` showing the Next.js welcome page.

Stop the server (Ctrl+C) before proceeding.

- [ ] **Step 3: Replace the welcome page with a placeholder landing page**

Overwrite `app/page.tsx`:

```tsx
export default function Home() {
  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white flex flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-4xl font-black uppercase tracking-tight">Olympic Email Studio</h1>
      <p className="text-sm text-neutral-400">Scaffold complete — features coming online.</p>
    </main>
  );
}
```

- [ ] **Step 4: Add the Olympic font import to `app/layout.tsx`**

Replace the existing `app/layout.tsx` body with:

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Olympic Email Studio",
  description: "Generate brand-correct Olympic Paints trade emails.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
```

- [ ] **Step 5: Add `.env.example` with placeholder keys**

Create `.env.example`:

```
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
KV_REST_API_URL=
KV_REST_API_TOKEN=
```

- [ ] **Step 6: Initialise git and commit**

```powershell
git init
git add .
git commit -m "chore: scaffold Next.js 16 + Tailwind v4 + Olympic landing placeholder"
```

---

### Task 2: Install runtime dependencies

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install AI + email + auth + KV + Zod**

```powershell
npm install ai @ai-sdk/anthropic zod @react-email/components @react-email/render @clerk/nextjs @vercel/kv
```

- [ ] **Step 2: Install test tooling (Vitest)**

```powershell
npm install -D vitest @vitest/ui
```

- [ ] **Step 3: Add Vitest config**

Create `vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, ".") },
  },
});
```

- [ ] **Step 4: Add a test script to package.json**

In `package.json`, under `"scripts"`, add:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 5: Sanity-check the install**

```powershell
npm run test
```

Expected: "No test files found" (exit code 1 is fine — that's Vitest telling us there are no tests yet). If the command crashes with a module-not-found error, re-install.

- [ ] **Step 6: Commit**

```powershell
git add package.json package-lock.json vitest.config.ts
git commit -m "chore: install AI SDK, react-email, Clerk, KV, Zod, Vitest"
```

---

### Task 3: Port DESIGN_SYSTEM.md to design-tokens.ts (TDD)

**Files:**
- Create: `lib/brand/design-tokens.ts`
- Test: `tests/design-tokens.test.ts`
- Reference (read-only): `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\DESIGN_SYSTEM.md`

- [ ] **Step 1: Write the failing test**

Create `tests/design-tokens.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { tokens } from "@/lib/brand/design-tokens";

describe("design tokens", () => {
  it("exposes the four brand core colours", () => {
    expect(tokens.colors.brand.yellow).toBe("#F5C400");
    expect(tokens.colors.brand.navy).toBe("#1A3D6E");
    expect(tokens.colors.brand.black).toBe("#0D0D0D");
    expect(tokens.colors.brand.white).toBe("#FFFFFF");
  });

  it("uses Barlow Condensed for display and Barlow for body, with Outlook-safe fallbacks", () => {
    expect(tokens.fonts.display).toContain("Barlow Condensed");
    expect(tokens.fonts.display).toContain("Arial Narrow");
    expect(tokens.fonts.body).toContain("Barlow");
    expect(tokens.fonts.body).toContain("Arial");
  });

  it("uses a 600px email container width", () => {
    expect(tokens.email.containerWidthPx).toBe(600);
  });

  it("exposes the full yellow ramp from 50 to 900", () => {
    expect(tokens.colors.yellowRamp[50]).toBe("#FEF9E0");
    expect(tokens.colors.yellowRamp[400]).toBe("#F5C400");
    expect(tokens.colors.yellowRamp[900]).toBe("#6A5000");
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

```powershell
npm run test -- design-tokens
```

Expected: FAIL with "Cannot find module '@/lib/brand/design-tokens'".

- [ ] **Step 3: Write `lib/brand/design-tokens.ts`**

Create `lib/brand/design-tokens.ts`:

```ts
// Olympic Paints design tokens, ported from DESIGN_SYSTEM.md for email use.
// Email-specific: font fallback stacks are mandatory (Outlook strips web fonts);
// 600px container is the universal email-safe width.

export const tokens = {
  colors: {
    brand: {
      yellow: "#F5C400",
      navy: "#1A3D6E",
      black: "#0D0D0D",
      white: "#FFFFFF",
    },
    yellowRamp: {
      50: "#FEF9E0", 100: "#FDF0A0", 200: "#FAE04D",
      400: "#F5C400", 600: "#D4A800", 800: "#A88000", 900: "#6A5000",
    },
    navyRamp: {
      50: "#E8EFF8", 100: "#B8CCE8", 300: "#6B9ED0",
      500: "#2D6BA8", 700: "#1A3D6E", 900: "#0D2040", 950: "#071022",
    },
    neutralRamp: {
      0: "#FFFFFF", 50: "#F7F6F3", 100: "#E8E7E2", 200: "#C8C7C0",
      400: "#949390", 600: "#5C5B58", 800: "#2E2E2C", 900: "#1A1A18", 950: "#0D0D0B",
    },
    mood: {
      teal: "#2D8C7A", terra: "#C97A3A", coral: "#E86060",
      pink: "#E87BAD", violet: "#9B7DBF", sage: "#7A8C55", ink: "#5C6B7A",
    },
    status: {
      success: "#2D8C7A",
      danger: "#E86060",
      neutral: "#5C6B7A",
    },
  },
  fonts: {
    display: "'Barlow Condensed', 'Arial Narrow', Arial, sans-serif",
    body: "'Barlow', Arial, Helvetica, sans-serif",
  },
  typeScale: {
    hero:    { sizePx: 36, weight: 900, lineHeight: 1.05, transform: "uppercase" as const },
    h2:      { sizePx: 22, weight: 800, lineHeight: 1.1,  transform: "uppercase" as const },
    h3:      { sizePx: 18, weight: 700, lineHeight: 1.15, transform: "uppercase" as const },
    eyebrow: { sizePx: 11, weight: 700, lineHeight: 1.2,  transform: "uppercase" as const, letterSpacingEm: 0.12 },
    body:    { sizePx: 15, weight: 400, lineHeight: 1.65, transform: "none" as const },
    caption: { sizePx: 11, weight: 400, lineHeight: 1.4,  transform: "none" as const },
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48 },
  radius:  { sm: 4, md: 8, lg: 12, pill: 50 },
  email: {
    containerWidthPx: 600,
    defaultTheme: "light" as const,
  },
} as const;

export type Tokens = typeof tokens;
```

- [ ] **Step 4: Run the test to verify it passes**

```powershell
npm run test -- design-tokens
```

Expected: PASS, 4 tests green.

- [ ] **Step 5: Commit**

```powershell
git add lib/brand/design-tokens.ts tests/design-tokens.test.ts
git commit -m "feat(brand): port DESIGN_SYSTEM.md tokens to TypeScript for email use"
```

---

### Task 4: Write visual-vocabulary.md and the four voice files

**Files:**
- Create: `lib/brand/visual-vocabulary.md`
- Create: `lib/brand/voice/stockist.md`
- Create: `lib/brand/voice/sales-rep.md`
- Create: `lib/brand/voice/contractor.md`
- Create: `lib/brand/voice/architect.md`

These are markdown content files, not code — there's nothing to test directly. They're consumed at runtime by the AI prompt builder (Task 7).

- [ ] **Step 1: Write `lib/brand/visual-vocabulary.md`**

Create the file with the following content:

```markdown
# Olympic Paints — Visual Vocabulary for Trade Emails

This document codifies how Olympic Paints visually presents itself in trade communications. Read alongside `design-tokens.ts` (which covers colours, type, spacing). Where the design tokens define the *rules*, this document defines the *conventions* extracted from the existing collateral.

## 1. Hero image conventions
- Always wrap lifestyle photos in a 3px solid #0D0D0D window frame with 8px border-radius. This frame is a brand device, not a generic border.
- Architectural interiors only. Modern, big windows, premium furniture.
- NEVER use people in lifestyle shots.
- NEVER use close-ups of paint application (brushes mid-stroke, drips, etc).

## 2. Logo placement
- Yellow circle badge (#F5C400) top-left of the hero block. Medium size 48px.
- Stockist / partner logo slot top-right, in a white 36px wrapper. Reserved for co-branded emails.

## 3. Yellow usage rule (load-bearing)
- Yellow is PUNCTUATION, not background.
- Allowed: logo badge, "Price" pill, button fill, headline against dark, banner strip.
- Forbidden: full-bleed yellow surfaces in body areas.
- Exception: max ONE full-yellow hero block per email (Product Promotion uses this).

## 4. Packshot conventions — two styles
- "Hero shot": white background, 3/4 angle, often with roller resting on can. Use in Product Promotion, top-of-fold.
- "In-context shot": packshot composited onto a lifestyle photo, bottom-right at ~30% width. Use in Stockist banner blocks. v1 uses existing baked banner images.

## 5. Product attribute strip
- Black 1px-bordered horizontal strip, 5 monochrome icons + caps labels.
- v1: existing banner images include icons baked in.

## 6. Typography mood
- Product names: Barlow Condensed Black 900, UPPERCASE, 36–56px, yellow on dark / black on light.
- Body: Barlow Regular 15px / 1.65 line-height. Sentence case.
- South African English: colour, organisation, programme, optimise, centre.

## 7. Negative space — what NOT to use
- No drop shadows on text.
- No gradients on headlines.
- No emoji in subject lines.
- No "happy painter with brush" stock photography.
- No exclamation marks in headlines (one allowed per email body if genuinely warranted).

## 8. Tone baseline (before audience-specific voice)
- Direct, factual, dated.
- Lead with what changed and what the reader needs to do.
- South African English; assume the reader knows the paint industry.
```

- [ ] **Step 2: Write `lib/brand/voice/stockist.md`**

```markdown
---
audience_id: stockist
display_name: Stockist
meta_label: At a glance
meta_fields: [SKU, Pack sizes, Trade price (ex VAT), RRP (incl VAT), Lead time, MOQ]
sign_off: Olympic Trade Team
sign_off_email: trade@olympicpaints.co.za
sign_off_phone: 011 555 0100
price_table_columns: [product, pack, trade_was, trade_now, save]
cta_primary_examples: [Place an order, Confirm your stock holding, Acknowledge price change]
cta_secondary_examples: [Download price list, Spec sheet (PDF), Call your rep]
---

# Voice — Stockist (hardware-store buyer)

## Who they are
Decision-maker at a hardware store or paint shop. Cares about margin, trade price, lead time, MOQ, and how fast stock turns. Time-poor. Reads email on a phone between counter sales.

## Voice rules
- Direct, factual. Lead with what changed and what they need to do.
- Use trade language: SKU, MOQ, lead time, RRP, ex VAT.
- NEVER use consumer-aspirational copy ("Inspiring Colour", "transform your space"). They are not the homeowner.
- South African English: colour, organisation, programme, rand (R, not ZAR).
- Headlines are statements, not questions.
```

- [ ] **Step 3: Write `lib/brand/voice/sales-rep.md`**

```markdown
---
audience_id: sales-rep
display_name: Sales Rep
meta_label: Sales talking points
meta_fields: [Margin %, Top 5 accounts to push, Comp vs Dulux, Stock available]
sign_off: Sales Ops
sign_off_email: sales@olympicpaints.co.za
sign_off_phone: 011 555 0100
price_table_columns: [product, pack, trade_was, trade_now, save]
cta_primary_examples: [Open campaign in CRM, See target accounts, Download talking-points PDF]
cta_secondary_examples: [Reply with questions, Book a regional briefing]
---

# Voice — Sales Rep (internal Olympic team)

## Who they are
Olympic-employed sales rep covering a region. Cares about hitting target, knowing what to push this week, and having ammunition for the next stockist visit. Reads email at start of day.

## Voice rules
- Punchy, action-oriented. Bullet-heavy. Subject line should sound like a callout.
- Use internal vocabulary: target accounts, push, comp, margin point.
- It's OK to reference other Olympic products and competitors by name (Dulux, Plascon).
- End the body with one concrete action: "call your top 5 accounts about X this week."
```

- [ ] **Step 4: Write `lib/brand/voice/contractor.md`**

```markdown
---
audience_id: contractor
display_name: Contractor
meta_label: On the job
meta_fields: [Coverage m²/L, Recoat time, Surfaces, Where to buy]
sign_off: Olympic Painter Programme
sign_off_email: painters@olympicpaints.co.za
sign_off_phone: 011 555 0100
price_table_columns: [product, pack, rrp_was, rrp_now, save]
cta_primary_examples: [Find your nearest stockist, View coverage calculator, Request samples]
cta_secondary_examples: [Download application guide, Spec sheet (PDF)]
---

# Voice — Contractor (registered painter)

## Who they are
Working painter or small contractor. Cares about coverage rate, recoat time, suitability for the surface they're on this week, and where to buy locally. Reads email on a phone between jobs.

## Voice rules
- Jobsite-practical. Lead with suitability and coverage.
- Use trade-painter vocabulary: substrate, primer key, dry-film thickness, coverage.
- Prices shown are RRP (what they pay at the shop), not trade price.
- Headlines reference what the product does on a job ("Hides hairline cracks", "Two coats over dark walls").
```

- [ ] **Step 5: Write `lib/brand/voice/architect.md`**

```markdown
---
audience_id: architect
display_name: Architect
meta_label: Specification data
meta_fields: [Finish (sheen %), VOC g/L, DFT μm, Standards]
sign_off: Olympic Specification
sign_off_email: spec@olympicpaints.co.za
sign_off_phone: 011 555 0100
price_table_columns: [product, pack, rrp_was, rrp_now, save]
cta_primary_examples: [Download TDS (PDF), Request a sample, Book a spec consultation]
cta_secondary_examples: [Browse the PlatinumPlus range, View finish chart]
---

# Voice — Architect (specifier)

## Who they are
Architect, designer, or specifier writing paint into a project spec. Cares about finish class, VOC, durability standards, and whether the product passes their compliance test. Reads email at a desk.

## Voice rules
- Technical-precise. Use standards language: sheen %, VOC g/L, DFT μm, SANS / ISO.
- Never colloquial. Never abbreviated.
- Lead with the spec property that matters (Class 2 washability, low VOC).
- Body should reference the TDS, not replace it.
```

- [ ] **Step 6: Commit**

```powershell
git add lib/brand/visual-vocabulary.md lib/brand/voice/
git commit -m "feat(brand): add visual vocabulary + four audience voice files with YAML front-matter"
```

---

### Task 5: products.json + typed reader with Zod validation (TDD)

**Files:**
- Create: `lib/products.json`
- Create: `lib/products.ts`
- Test: `tests/products.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tests/products.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { getAllProducts, getProductById } from "@/lib/products";

describe("products", () => {
  it("loads at least one product from products.json", () => {
    const products = getAllProducts();
    expect(products.length).toBeGreaterThan(0);
  });

  it("validates the Natural Elegance Plus seed product", () => {
    const nep = getProductById("NEP");
    expect(nep).toBeDefined();
    expect(nep?.name).toBe("Natural Elegance Plus");
    expect(nep?.skus.length).toBeGreaterThan(0);
    expect(nep?.skus[0].sku).toMatch(/^NEP-/);
  });

  it("returns undefined for unknown product id", () => {
    expect(getProductById("DOES-NOT-EXIST")).toBeUndefined();
  });

  it("throws on load if products.json drifts from the schema", () => {
    // Schema enforcement is exercised by getAllProducts() on first call.
    // If it returns without throwing, the file is schema-valid.
    expect(() => getAllProducts()).not.toThrow();
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

```powershell
npm run test -- products
```

Expected: FAIL with "Cannot find module".

- [ ] **Step 3: Create `lib/products.json` with one seed product**

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
      { "sku": "NEP-5L-WHT", "pack": "5L", "trade_price": 489, "rrp": 629 },
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

- [ ] **Step 4: Create `lib/products.ts`**

```ts
import { z } from "zod";
import productsData from "./products.json";

const SkuSchema = z.object({
  sku: z.string().min(1),
  pack: z.string().min(1),
  trade_price: z.number().positive(),
  rrp: z.number().positive(),
});

const SpecSchema = z.object({
  sheen_pct: z.number().min(0).max(100).optional(),
  voc_g_per_l: z.number().min(0).optional(),
  coverage_m2_per_l: z.number().positive().optional(),
  recoat_hours: z.number().positive().optional(),
  standards: z.array(z.string()).optional(),
});

const ProductSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  range: z.string().min(1),
  finish: z.string(),
  packshot_url: z.string().startsWith("/assets/"),
  in_context_url: z.string().startsWith("/assets/").optional(),
  skus: z.array(SkuSchema).min(1),
  attributes: z.array(z.string()).length(5),
  spec: SpecSchema.optional(),
  spec_sheet_url: z.string().url().optional(),
});

export type Product = z.infer<typeof ProductSchema>;
export type Sku = z.infer<typeof SkuSchema>;

const ProductsSchema = z.array(ProductSchema);

// Parse at module load — throws at startup if products.json is malformed.
const products: readonly Product[] = ProductsSchema.parse(productsData);

export function getAllProducts(): readonly Product[] {
  return products;
}

export function getProductById(id: string): Product | undefined {
  return products.find((p) => p.id === id);
}
```

- [ ] **Step 5: Run the test to verify it passes**

```powershell
npm run test -- products
```

Expected: PASS, 4 tests green.

- [ ] **Step 6: Commit**

```powershell
git add lib/products.json lib/products.ts tests/products.test.ts
git commit -m "feat(products): seed products.json with Natural Elegance Plus + typed Zod-validated reader"
```

---

## Phase 2: First end-to-end path

### Task 6: Combos matrix + typed reader (TDD)

**Files:**
- Create: `lib/combos.ts`
- Test: `tests/combos.test.ts`

- [ ] **Step 1: Write the failing test**

Create `tests/combos.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { isComboValid, getInvalidComboReason, AUDIENCES, TEMPLATES } from "@/lib/combos";

describe("audience × template combos", () => {
  it("allows Stockist + any template", () => {
    expect(isComboValid("stockist", "product-promotion")).toBe(true);
    expect(isComboValid("stockist", "price-promotion")).toBe(true);
    expect(isComboValid("stockist", "trade-information")).toBe(true);
  });

  it("disallows Architect + Price Promotion with a helpful reason", () => {
    expect(isComboValid("architect", "price-promotion")).toBe(false);
    expect(getInvalidComboReason("architect", "price-promotion")).toMatch(/Trade Information/i);
  });

  it("allows Architect + Product Promotion and + Trade Information", () => {
    expect(isComboValid("architect", "product-promotion")).toBe(true);
    expect(isComboValid("architect", "trade-information")).toBe(true);
  });

  it("exports the audience and template lists for use in UI", () => {
    expect(AUDIENCES).toHaveLength(4);
    expect(TEMPLATES).toHaveLength(3);
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

```powershell
npm run test -- combos
```

Expected: FAIL with "Cannot find module".

- [ ] **Step 3: Write `lib/combos.ts`**

```ts
export const AUDIENCES = ["stockist", "sales-rep", "contractor", "architect"] as const;
export const TEMPLATES = ["product-promotion", "price-promotion", "trade-information"] as const;

export type Audience = (typeof AUDIENCES)[number];
export type Template = (typeof TEMPLATES)[number];

// True = allowed, False = disallowed.
// Any combo not listed here defaults to allowed.
const INVALID_COMBOS: Partial<Record<Audience, Partial<Record<Template, string>>>> = {
  architect: {
    "price-promotion":
      "Architects don't buy paint — they specify it. Use Trade Information for spec-bound pricing notices instead.",
  },
};

export function isComboValid(audience: Audience, template: Template): boolean {
  return INVALID_COMBOS[audience]?.[template] === undefined;
}

export function getInvalidComboReason(audience: Audience, template: Template): string | undefined {
  return INVALID_COMBOS[audience]?.[template];
}

export const AUDIENCE_DISPLAY: Record<Audience, string> = {
  "stockist": "Stockist",
  "sales-rep": "Sales Rep",
  "contractor": "Contractor",
  "architect": "Architect",
};

export const TEMPLATE_DISPLAY: Record<Template, string> = {
  "product-promotion": "Product Promotion",
  "price-promotion": "Price Promotion",
  "trade-information": "Trade Information",
};
```

- [ ] **Step 4: Run the test to verify it passes**

```powershell
npm run test -- combos
```

Expected: PASS, 4 tests green.

- [ ] **Step 5: Commit**

```powershell
git add lib/combos.ts tests/combos.test.ts
git commit -m "feat(combos): audience × template validity matrix with disable reasons"
```

---

### Task 7: Voice file reader (TDD)

**Files:**
- Create: `lib/voice.ts`
- Test: `tests/voice.test.ts`

The voice files in `lib/brand/voice/` have YAML front-matter (audience_id, meta_label, etc.) followed by a markdown body. The reader parses the front-matter and returns a typed object.

- [ ] **Step 1: Install YAML front-matter parser**

```powershell
npm install gray-matter
```

- [ ] **Step 2: Write the failing test**

Create `tests/voice.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { loadVoice } from "@/lib/voice";

describe("voice loader", () => {
  it("loads stockist voice with all front-matter fields", () => {
    const v = loadVoice("stockist");
    expect(v.audience_id).toBe("stockist");
    expect(v.display_name).toBe("Stockist");
    expect(v.meta_label).toBe("At a glance");
    expect(v.meta_fields).toContain("SKU");
    expect(v.sign_off).toBe("Olympic Trade Team");
    expect(v.price_table_columns).toEqual(["product", "pack", "trade_was", "trade_now", "save"]);
  });

  it("loads contractor voice with RRP-based price columns (override)", () => {
    const v = loadVoice("contractor");
    expect(v.price_table_columns).toEqual(["product", "pack", "rrp_was", "rrp_now", "save"]);
  });

  it("includes the markdown body for the AI system prompt", () => {
    const v = loadVoice("stockist");
    expect(v.markdown_body).toContain("Voice rules");
    expect(v.markdown_body).toContain("South African English");
  });
});
```

- [ ] **Step 3: Run the test to confirm it fails**

```powershell
npm run test -- voice
```

Expected: FAIL with "Cannot find module".

- [ ] **Step 4: Write `lib/voice.ts`**

```ts
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { z } from "zod";
import type { Audience } from "./combos";

const VoiceSchema = z.object({
  audience_id: z.string(),
  display_name: z.string(),
  meta_label: z.string(),
  meta_fields: z.array(z.string()),
  sign_off: z.string(),
  sign_off_email: z.string().email(),
  sign_off_phone: z.string(),
  price_table_columns: z.array(z.string()),
  cta_primary_examples: z.array(z.string()).min(1),
  cta_secondary_examples: z.array(z.string()).min(1),
});

export type Voice = z.infer<typeof VoiceSchema> & {
  markdown_body: string;
};

const VOICE_DIR = path.join(process.cwd(), "lib", "brand", "voice");

export function loadVoice(audience: Audience): Voice {
  const filePath = path.join(VOICE_DIR, `${audience}.md`);
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = matter(raw);
  const frontMatter = VoiceSchema.parse(parsed.data);
  return {
    ...frontMatter,
    markdown_body: parsed.content.trim(),
  };
}

export function loadVisualVocabulary(): string {
  const filePath = path.join(process.cwd(), "lib", "brand", "visual-vocabulary.md");
  return fs.readFileSync(filePath, "utf-8");
}
```

- [ ] **Step 5: Run the test to verify it passes**

```powershell
npm run test -- voice
```

Expected: PASS, 3 tests green.

- [ ] **Step 6: Commit**

```powershell
git add lib/voice.ts tests/voice.test.ts package.json package-lock.json
git commit -m "feat(brand): typed voice file loader with YAML front-matter parsing"
```

---

### Task 8: AI output Zod schemas + render-email function (TDD with mocked AI)

**Files:**
- Create: `lib/ai/schemas.ts`
- Create: `lib/ai/render-email.ts`
- Test: `tests/schemas.test.ts`

The AI function takes a form payload, builds the prompt, calls Claude, and returns validated copy. For testing, we test the **schema** rigorously (it's pure logic) and mock the AI call to verify the prompt-building path. We do NOT test against the real API in unit tests.

- [ ] **Step 1: Write the failing schema test**

Create `tests/schemas.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { emailCopySchema, productPromotionInputSchema } from "@/lib/ai/schemas";

describe("AI output schemas", () => {
  it("accepts a well-formed email copy object", () => {
    const ok = emailCopySchema.parse({
      eyebrow: "PlatinumPlus Range · Now Shipping",
      headline: "Natural Elegance Plus is in stock.",
      body: "The silky soft-touch finish is now available in 5L and 20L.",
      cta_primary: "Place an order",
      cta_secondary: "Spec sheet (PDF)",
    });
    expect(ok.headline).toContain("Natural Elegance");
  });

  it("rejects a headline over 120 chars", () => {
    expect(() =>
      emailCopySchema.parse({
        eyebrow: "x",
        headline: "x".repeat(121),
        body: "x",
        cta_primary: "x",
      })
    ).toThrow();
  });

  it("allows cta_secondary to be omitted", () => {
    const ok = emailCopySchema.parse({
      eyebrow: "x", headline: "x", body: "x", cta_primary: "x",
    });
    expect(ok.cta_secondary).toBeUndefined();
  });
});

describe("form input schemas", () => {
  it("validates a Product Promotion input", () => {
    const ok = productPromotionInputSchema.parse({
      template: "product-promotion",
      audience: "stockist",
      product_id: "NEP",
      lead_time: "2 working days",
      ai_notes: "Emphasise the 8-year guarantee.",
    });
    expect(ok.product_id).toBe("NEP");
  });
});
```

- [ ] **Step 2: Run the test to confirm it fails**

```powershell
npm run test -- schemas
```

Expected: FAIL with "Cannot find module".

- [ ] **Step 3: Write `lib/ai/schemas.ts`**

```ts
import { z } from "zod";

// What Claude returns to us — strictly typed, used with generateObject.
export const emailCopySchema = z.object({
  eyebrow: z.string().max(80),
  headline: z.string().max(120),
  body: z.string().max(500),
  cta_primary: z.string().max(40),
  cta_secondary: z.string().max(40).optional(),
});

export type EmailCopy = z.infer<typeof emailCopySchema>;

// Form input schemas — one per template, all share template + audience.
const baseInputSchema = z.object({
  audience: z.enum(["stockist", "sales-rep", "contractor", "architect"]),
  ai_notes: z.string().max(500).optional(),
});

export const productPromotionInputSchema = baseInputSchema.extend({
  template: z.literal("product-promotion"),
  product_id: z.string().min(1),
  lead_time: z.string().min(1),
});

export const pricePromotionInputSchema = baseInputSchema.extend({
  template: z.literal("price-promotion"),
  promo_name: z.string().min(1).max(80),
  valid_from: z.string(), // ISO date
  valid_to: z.string(),
  price_rows: z
    .array(
      z.object({
        product_id: z.string().min(1),
        pack: z.string().min(1),
        was: z.number().positive(),
        now: z.number().positive(),
      })
    )
    .min(1),
  terms_text: z.string().min(1),
});

export const tradeInfoInputSchema = baseInputSchema.extend({
  template: z.literal("trade-information"),
  notice_date: z.string(), // ISO date
  headline_direction: z.string().min(1),
  changing_items: z.array(z.string()).min(1),
  unchanged_items: z.array(z.string()),
  action_required_text: z.string().min(1),
});

export const formInputSchema = z.discriminatedUnion("template", [
  productPromotionInputSchema,
  pricePromotionInputSchema,
  tradeInfoInputSchema,
]);

export type FormInput = z.infer<typeof formInputSchema>;
```

- [ ] **Step 4: Run the test to verify it passes**

```powershell
npm run test -- schemas
```

Expected: PASS, 4 tests green.

- [ ] **Step 5: Write `lib/ai/render-email.ts`**

```ts
import { anthropic } from "@ai-sdk/anthropic";
import { generateObject } from "ai";
import { emailCopySchema, type EmailCopy, type FormInput } from "./schemas";
import { loadVoice, loadVisualVocabulary } from "../voice";
import { getProductById } from "../products";

const MODEL = "claude-sonnet-4-6";

export async function generateEmailCopy(input: FormInput): Promise<EmailCopy> {
  const voice = loadVoice(input.audience);
  const visualVocab = loadVisualVocabulary();

  const system = [
    "You are Olympic Paints' copywriter for trade communications.",
    "Your only job is to write the eyebrow, headline, body, and CTA labels for one email.",
    "You must obey both the visual vocabulary rules and the audience voice rules below.",
    "Return ONLY the JSON object specified by the schema. No commentary.",
    "",
    "=== VISUAL VOCABULARY ===",
    visualVocab,
    "",
    "=== VOICE FOR THIS AUDIENCE ===",
    voice.markdown_body,
    "",
    `Sign off as: ${voice.sign_off}`,
    `Example primary CTAs you may use: ${voice.cta_primary_examples.join(", ")}`,
    `Example secondary CTAs you may use: ${voice.cta_secondary_examples.join(", ")}`,
  ].join("\n");

  const userPrompt = buildUserPrompt(input);

  const { object } = await generateObject({
    model: anthropic(MODEL),
    schema: emailCopySchema,
    system,
    prompt: userPrompt,
    maxRetries: 1,
  });

  return object;
}

function buildUserPrompt(input: FormInput): string {
  switch (input.template) {
    case "product-promotion": {
      const product = getProductById(input.product_id);
      if (!product) throw new Error(`Unknown product: ${input.product_id}`);
      return [
        `Template: Product Promotion`,
        `Product: ${product.name} (range: ${product.range}, finish: ${product.finish})`,
        `Pack sizes: ${product.skus.map((s) => s.pack).join(", ")}`,
        `Lead time: ${input.lead_time}`,
        input.ai_notes ? `Notes from the sender: ${input.ai_notes}` : "",
        ``,
        `Write copy that announces this product is in stock / available for order.`,
      ]
        .filter(Boolean)
        .join("\n");
    }
    case "price-promotion": {
      const rows = input.price_rows
        .map((r) => {
          const product = getProductById(r.product_id);
          const savePct = Math.round((1 - r.now / r.was) * 100);
          return `- ${product?.name ?? r.product_id} ${r.pack}: R${r.was} → R${r.now} (save ${savePct}%)`;
        })
        .join("\n");
      return [
        `Template: Price Promotion`,
        `Promo name: ${input.promo_name}`,
        `Valid: ${input.valid_from} to ${input.valid_to}`,
        `SKUs on promo:`,
        rows,
        `Terms: ${input.terms_text}`,
        input.ai_notes ? `Notes from the sender: ${input.ai_notes}` : "",
        ``,
        `Write copy that drives stock-up orders before the promo ends.`,
      ]
        .filter(Boolean)
        .join("\n");
    }
    case "trade-information": {
      return [
        `Template: Trade Information`,
        `Notice date: ${input.notice_date}`,
        `Headline direction: ${input.headline_direction}`,
        `What's changing:`,
        ...input.changing_items.map((i) => `- ${i}`),
        `What stays the same:`,
        ...input.unchanged_items.map((i) => `- ${i}`),
        `Action required: ${input.action_required_text}`,
        input.ai_notes ? `Notes from the sender: ${input.ai_notes}` : "",
        ``,
        `Write a calm, factual notice. No promotional language.`,
      ]
        .filter(Boolean)
        .join("\n");
    }
  }
}
```

- [ ] **Step 6: Commit**

```powershell
git add lib/ai/ tests/schemas.test.ts
git commit -m "feat(ai): Zod schemas + generateEmailCopy function with audience+template prompt building"
```

---

### Task 9: Shared email components

**Files:**
- Create: `lib/templates/shared/Header.tsx`
- Create: `lib/templates/shared/Footer.tsx`
- Create: `lib/templates/shared/WindowFrame.tsx`
- Create: `lib/templates/shared/MetaBlock.tsx`
- Create: `lib/templates/shared/CtaButton.tsx`

These are React Email components. They produce email-safe HTML when rendered via `@react-email/render`. No tests — they're presentational and tested manually via Task 10's smoke test.

- [ ] **Step 1: Create `lib/templates/shared/Header.tsx`**

```tsx
import { Section, Row, Column, Img, Text } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";

type Props = { dateLabel: string; subLabel?: string };

export function Header({ dateLabel, subLabel = "Olympic Trade" }: Props) {
  return (
    <Section style={{ backgroundColor: tokens.colors.brand.black, padding: "14px 20px" }}>
      <Row>
        <Column style={{ width: 44 }}>
          <Img
            src="https://olympic-email.vercel.app/assets/logo.png"
            width={36}
            height={36}
            alt="Olympic Paints"
            style={{ borderRadius: "50%", display: "block" }}
          />
        </Column>
        <Column>
          <Text style={{
            margin: 0,
            fontFamily: tokens.fonts.display,
            fontWeight: 800,
            fontSize: 13,
            color: tokens.colors.brand.yellow,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}>
            {subLabel}
          </Text>
          <Text style={{
            margin: "2px 0 0",
            fontFamily: tokens.fonts.body,
            fontSize: 10,
            color: tokens.colors.neutralRamp[400],
            letterSpacing: "0.05em",
            textTransform: "uppercase",
          }}>
            {dateLabel}
          </Text>
        </Column>
      </Row>
    </Section>
  );
}
```

- [ ] **Step 2: Create `lib/templates/shared/Footer.tsx`**

```tsx
import { Section, Text, Link } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";

type Props = { signOff: string; signOffEmail: string };

export function Footer({ signOff, signOffEmail }: Props) {
  return (
    <Section style={{
      backgroundColor: tokens.colors.brand.black,
      padding: "20px 24px",
      textAlign: "center",
    }}>
      <Text style={{
        margin: 0,
        fontFamily: tokens.fonts.body,
        fontSize: 11,
        color: tokens.colors.neutralRamp[400],
        lineHeight: 1.6,
      }}>
        Olympic Paints — Inspiring Colour Since 1981<br />
        {signOff} · <Link href={`mailto:${signOffEmail}`} style={{ color: tokens.colors.brand.yellow }}>{signOffEmail}</Link><br />
        <Link href="https://olympicpaints.co.za" style={{ color: tokens.colors.brand.yellow }}>olympicpaints.co.za</Link>
      </Text>
    </Section>
  );
}
```

- [ ] **Step 3: Create `lib/templates/shared/WindowFrame.tsx`**

```tsx
import { Section, Img } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";

type Props = { imageUrl: string; alt: string; height?: number };

export function WindowFrame({ imageUrl, alt, height = 240 }: Props) {
  return (
    <Section style={{ padding: "20px 24px" }}>
      <div style={{
        border: `3px solid ${tokens.colors.brand.black}`,
        borderRadius: `${tokens.radius.md}px`,
        overflow: "hidden",
      }}>
        <Img
          src={imageUrl}
          alt={alt}
          width={552}
          height={height}
          style={{ display: "block", width: "100%", height: "auto" }}
        />
      </div>
    </Section>
  );
}
```

- [ ] **Step 4: Create `lib/templates/shared/MetaBlock.tsx`**

```tsx
import { Section, Text } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";

type Row = { label: string; value: string };
type Props = { label: string; rows: Row[]; accent?: "yellow" | "danger" | "success" };

export function MetaBlock({ label, rows, accent = "yellow" }: Props) {
  const borderColor =
    accent === "yellow" ? tokens.colors.brand.yellow :
    accent === "danger" ? tokens.colors.status.danger :
    tokens.colors.status.success;

  return (
    <Section style={{
      backgroundColor: tokens.colors.neutralRamp[50],
      borderLeft: `4px solid ${borderColor}`,
      padding: "14px 18px",
      margin: "0 24px 20px",
    }}>
      <Text style={{
        margin: "0 0 8px",
        fontFamily: tokens.fonts.display,
        fontWeight: 700,
        fontSize: 10,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: tokens.colors.neutralRamp[600],
      }}>
        {label}
      </Text>
      {rows.map((r) => (
        <Text key={r.label} style={{
          margin: 0, fontFamily: tokens.fonts.body, fontSize: 13, lineHeight: 1.7,
        }}>
          <strong>{r.label}:</strong> {r.value}
        </Text>
      ))}
    </Section>
  );
}
```

- [ ] **Step 5: Create `lib/templates/shared/CtaButton.tsx`**

```tsx
import { Button } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";

type Props = { href: string; label: string; variant?: "primary" | "ghost" };

export function CtaButton({ href, label, variant = "primary" }: Props) {
  const isPrimary = variant === "primary";
  return (
    <Button
      href={href}
      style={{
        backgroundColor: isPrimary ? tokens.colors.brand.yellow : "transparent",
        color: isPrimary ? tokens.colors.brand.black : tokens.colors.brand.navy,
        border: isPrimary ? "none" : `2px solid ${tokens.colors.brand.navy}`,
        borderRadius: `${tokens.radius.pill}px`,
        padding: "11px 22px",
        fontFamily: tokens.fonts.display,
        fontWeight: isPrimary ? 800 : 700,
        fontSize: 13,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        textDecoration: "none",
        marginRight: 8,
      }}
    >
      {label}
    </Button>
  );
}
```

- [ ] **Step 6: Commit**

```powershell
git add lib/templates/shared/
git commit -m "feat(templates): shared email components (Header, Footer, WindowFrame, MetaBlock, CtaButton)"
```

---

### Task 10: Product Promotion template + API route + smoke test

**Files:**
- Create: `lib/templates/product-promotion.tsx`
- Create: `app/api/render-email/route.ts`
- Modify: `.env.example` (verify ANTHROPIC_API_KEY is documented)

- [ ] **Step 1: Create `lib/templates/product-promotion.tsx`**

```tsx
import { Html, Head, Body, Container, Section, Text } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";
import type { Voice } from "@/lib/voice";
import type { Product } from "@/lib/products";
import type { EmailCopy } from "@/lib/ai/schemas";
import { Header } from "./shared/Header";
import { Footer } from "./shared/Footer";
import { WindowFrame } from "./shared/WindowFrame";
import { MetaBlock } from "./shared/MetaBlock";
import { CtaButton } from "./shared/CtaButton";

type Props = {
  voice: Voice;
  copy: EmailCopy;
  product: Product;
  leadTime: string;
  ctaPrimaryUrl: string;
  ctaSecondaryUrl: string;
};

export function ProductPromotion({
  voice, copy, product, leadTime, ctaPrimaryUrl, ctaSecondaryUrl,
}: Props) {
  const firstSku = product.skus[0];
  const dateLabel = `Product Update · ${new Date().toISOString().slice(0, 10)}`;

  return (
    <Html>
      <Head />
      <Body style={{ margin: 0, backgroundColor: tokens.colors.neutralRamp[50] }}>
        <Container style={{
          maxWidth: tokens.email.containerWidthPx,
          backgroundColor: tokens.colors.brand.white,
          fontFamily: tokens.fonts.body,
        }}>
          <Header dateLabel={dateLabel} />

          <WindowFrame
            imageUrl={`https://olympic-email.vercel.app${product.in_context_url ?? product.packshot_url}`}
            alt={product.name}
          />

          <Section style={{ padding: "0 24px 20px" }}>
            <Text style={{
              margin: 0, fontFamily: tokens.fonts.display, fontWeight: 700,
              fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase",
              color: tokens.colors.neutralRamp[600],
            }}>{copy.eyebrow}</Text>
            <Text style={{
              margin: "6px 0 4px", fontFamily: tokens.fonts.display, fontWeight: 900,
              fontSize: 32, lineHeight: 1.05, textTransform: "uppercase",
              color: tokens.colors.brand.black,
            }}>{copy.headline}</Text>
            <Text style={{
              margin: 0, fontSize: 14, lineHeight: 1.6, color: tokens.colors.neutralRamp[800],
            }}>{copy.body}</Text>
          </Section>

          <MetaBlock
            label={voice.meta_label}
            rows={[
              { label: "SKU", value: firstSku.sku },
              { label: "Pack sizes", value: product.skus.map((s) => s.pack).join(", ") },
              { label: "Trade price (5L)", value: `R${firstSku.trade_price} ex VAT` },
              { label: "RRP (5L)", value: `R${firstSku.rrp} incl VAT` },
              { label: "Lead time", value: leadTime },
            ]}
          />

          <Section style={{ padding: "0 24px 24px" }}>
            <CtaButton href={ctaPrimaryUrl} label={copy.cta_primary} />
            {copy.cta_secondary && (
              <CtaButton href={ctaSecondaryUrl} label={copy.cta_secondary} variant="ghost" />
            )}
          </Section>

          <Footer signOff={voice.sign_off} signOffEmail={voice.sign_off_email} />
        </Container>
      </Body>
    </Html>
  );
}
```

- [ ] **Step 2: Create the API route `app/api/render-email/route.ts`**

```ts
import { NextRequest, NextResponse } from "next/server";
import { render } from "@react-email/render";
import { kv } from "@vercel/kv";
import crypto from "crypto";
import { formInputSchema } from "@/lib/ai/schemas";
import { generateEmailCopy } from "@/lib/ai/render-email";
import { loadVoice } from "@/lib/voice";
import { getProductById } from "@/lib/products";
import { ProductPromotion } from "@/lib/templates/product-promotion";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = formInputSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid form input", details: parsed.error.flatten() }, { status: 400 });
  }
  const input = parsed.data;

  // Generate copy via Claude
  const copy = await generateEmailCopy(input);

  // Render template
  let html: string;
  if (input.template === "product-promotion") {
    const product = getProductById(input.product_id);
    if (!product) {
      return NextResponse.json({ error: `Unknown product ${input.product_id}` }, { status: 400 });
    }
    const voice = loadVoice(input.audience);
    html = await render(
      ProductPromotion({
        voice,
        copy,
        product,
        leadTime: input.lead_time,
        ctaPrimaryUrl: "https://olympicpaints.co.za/order",
        ctaSecondaryUrl: product.spec_sheet_url ?? "https://olympicpaints.co.za",
      })
    );
  } else {
    // Price Promotion + Trade Information come in later tasks.
    return NextResponse.json({ error: `Template ${input.template} not implemented yet` }, { status: 501 });
  }

  const previewId = crypto.randomUUID();
  await kv.set(`preview:${previewId}`, html, { ex: 86400 });

  return NextResponse.json({ previewId, copy });
}
```

- [ ] **Step 3: Set the local env var**

Create `.env.local` (NOT committed) with:

```
ANTHROPIC_API_KEY=sk-ant-<your key>
KV_REST_API_URL=<your dev KV url>
KV_REST_API_TOKEN=<your dev KV token>
```

For development without Vercel KV, you can stub KV by setting `KV_REST_API_URL=http://localhost:6379` and running a local Redis-compatible server. Or skip KV in dev by short-circuiting the `kv.set` call.

- [ ] **Step 4: Manual smoke test via curl**

```powershell
npm run dev
```

In another terminal:

```powershell
curl -X POST http://localhost:3000/api/render-email `
  -H "Content-Type: application/json" `
  -d '{\"template\":\"product-promotion\",\"audience\":\"stockist\",\"product_id\":\"NEP\",\"lead_time\":\"2 working days\",\"ai_notes\":\"Emphasise the 8-year guarantee.\"}'
```

Expected: `{"previewId":"<uuid>","copy":{"eyebrow":"...","headline":"...","body":"...","cta_primary":"...","cta_secondary":"..."}}` within ~5–10 seconds.

If you get a 500, check the dev server log — most likely `ANTHROPIC_API_KEY` is missing or KV creds are wrong.

- [ ] **Step 5: Commit**

```powershell
git add lib/templates/product-promotion.tsx app/api/render-email/route.ts
git commit -m "feat(api): render-email POST endpoint with Product Promotion template (end-to-end)"
```

---

## Phase 3: The form

### Task 11: Install shadcn/ui

**Files:**
- Modify: `package.json`, `tailwind.config.ts`
- Create: `components/ui/...` (auto-generated)

- [ ] **Step 1: Initialise shadcn**

```powershell
npx shadcn@latest init
```

Accept defaults: New York style, Slate base colour, CSS variables.

- [ ] **Step 2: Install the form primitives we need**

```powershell
npx shadcn@latest add toggle-group input textarea label button select tooltip
```

- [ ] **Step 3: Verify components landed**

Expected: `components/ui/toggle-group.tsx`, `input.tsx`, `textarea.tsx`, `label.tsx`, `button.tsx`, `select.tsx`, `tooltip.tsx` all exist.

- [ ] **Step 4: Commit**

```powershell
git add components/ui/ components.json package.json package-lock.json app/globals.css
git commit -m "chore: install shadcn/ui primitives (toggle-group, input, textarea, button, select, tooltip)"
```

---

### Task 12: Landing page + products API + compose page skeleton

**Files:**
- Modify: `app/page.tsx`
- Create: `app/api/products/route.ts`
- Create: `app/compose/page.tsx`

- [ ] **Step 1: Create `app/api/products/route.ts`**

```ts
import { NextResponse } from "next/server";
import { getAllProducts } from "@/lib/products";

export async function GET() {
  return NextResponse.json({ products: getAllProducts() });
}
```

- [ ] **Step 2: Replace `app/page.tsx` with a landing page**

```tsx
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white flex flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-5xl font-black uppercase tracking-tight text-[#F5C400]">Olympic Email Studio</h1>
        <p className="mt-3 text-sm text-neutral-400 uppercase tracking-widest">Trade communications, on-brand, in three minutes.</p>
      </div>
      <Link
        href="/compose"
        className="mt-4 inline-block bg-[#F5C400] text-[#0D0D0D] font-bold uppercase tracking-wider px-8 py-3 rounded-full hover:bg-yellow-400"
      >
        Start a campaign →
      </Link>
    </main>
  );
}
```

- [ ] **Step 3: Create `app/compose/page.tsx` skeleton**

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Button } from "@/components/ui/button";
import { AUDIENCES, TEMPLATES, AUDIENCE_DISPLAY, TEMPLATE_DISPLAY, isComboValid, getInvalidComboReason, type Audience, type Template } from "@/lib/combos";
import { ProductPromoFields } from "@/components/ProductPromoFields";
import { PricePromoFields } from "@/components/PricePromoFields";
import { TradeInfoFields } from "@/components/TradeInfoFields";

export default function ComposePage() {
  const router = useRouter();
  const [template, setTemplate] = useState<Template>("product-promotion");
  const [audience, setAudience] = useState<Audience>("stockist");
  const [fields, setFields] = useState<Record<string, unknown>>({});
  const [submitting, setSubmitting] = useState(false);

  const comboInvalid = !isComboValid(audience, template);
  const comboReason = getInvalidComboReason(audience, template);

  async function handleSubmit() {
    setSubmitting(true);
    const res = await fetch("/api/render-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ template, audience, ...fields }),
    });
    const data = await res.json();
    setSubmitting(false);
    if (data.previewId) {
      router.push(`/preview/${data.previewId}`);
    } else {
      alert(`Generation failed: ${data.error}`);
    }
  }

  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white p-6 md:p-10">
      <div className="max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl font-black uppercase text-[#F5C400]">Compose a trade email</h1>

        {/* Step 1: template */}
        <section className="bg-[#161614] border border-[#1e1e1e] rounded-xl p-5">
          <h2 className="text-sm font-bold uppercase tracking-wider mb-3">1 · What kind of email?</h2>
          <ToggleGroup type="single" value={template} onValueChange={(v) => v && setTemplate(v as Template)}>
            {TEMPLATES.map((t) => (
              <ToggleGroupItem key={t} value={t}>{TEMPLATE_DISPLAY[t]}</ToggleGroupItem>
            ))}
          </ToggleGroup>
        </section>

        {/* Step 2: audience */}
        <section className="bg-[#161614] border border-[#1e1e1e] rounded-xl p-5">
          <h2 className="text-sm font-bold uppercase tracking-wider mb-3">2 · Who is this for?</h2>
          <ToggleGroup type="single" value={audience} onValueChange={(v) => v && setAudience(v as Audience)}>
            {AUDIENCES.map((a) => (
              <ToggleGroupItem
                key={a}
                value={a}
                disabled={!isComboValid(a, template)}
                title={!isComboValid(a, template) ? getInvalidComboReason(a, template) : undefined}
              >
                {AUDIENCE_DISPLAY[a]}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          {comboInvalid && (
            <p className="mt-3 text-sm text-red-400">{comboReason}</p>
          )}
        </section>

        {/* Step 3: details */}
        <section className="bg-[#161614] border border-[#F5C400] rounded-xl p-5">
          <h2 className="text-sm font-bold uppercase tracking-wider mb-3">3 · The details</h2>
          {template === "product-promotion" && <ProductPromoFields value={fields} onChange={setFields} />}
          {template === "price-promotion" && <PricePromoFields value={fields} onChange={setFields} />}
          {template === "trade-information" && <TradeInfoFields value={fields} onChange={setFields} />}
        </section>

        <div className="flex justify-end pt-2">
          <Button
            disabled={comboInvalid || submitting}
            onClick={handleSubmit}
            className="bg-[#F5C400] text-[#0D0D0D] hover:bg-yellow-400 font-bold uppercase rounded-full px-7 py-3"
          >
            {submitting ? "Generating…" : "Generate email →"}
          </Button>
        </div>
      </div>
    </main>
  );
}
```

- [ ] **Step 4: Verify it loads (without functional field components yet)**

```powershell
npm run dev
```

Open `http://localhost:3000` → click "Start a campaign". Expect compile errors complaining about missing `ProductPromoFields`, `PricePromoFields`, `TradeInfoFields` — fix in next task.

- [ ] **Step 5: Commit**

```powershell
git add app/page.tsx app/compose/page.tsx app/api/products/route.ts
git commit -m "feat(ui): landing page + compose form skeleton + products GET endpoint"
```

---

### Task 13: Field-set components for the three templates

**Files:**
- Create: `components/ProductPromoFields.tsx`
- Create: `components/PricePromoFields.tsx`
- Create: `components/TradeInfoFields.tsx`

- [ ] **Step 1: Create `components/ProductPromoFields.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Product } from "@/lib/products";

type Props = { value: Record<string, unknown>; onChange: (v: Record<string, unknown>) => void };

export function ProductPromoFields({ value, onChange }: Props) {
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    fetch("/api/products").then((r) => r.json()).then((d) => setProducts(d.products));
  }, []);

  return (
    <div className="space-y-3">
      <div>
        <Label className="text-xs uppercase tracking-wider">Product</Label>
        <Select onValueChange={(v) => onChange({ ...value, product_id: v })}>
          <SelectTrigger><SelectValue placeholder="Pick a product…" /></SelectTrigger>
          <SelectContent>
            {products.map((p) => (
              <SelectItem key={p.id} value={p.id}>{p.name} ({p.range})</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">Lead time</Label>
        <Input
          placeholder="e.g. 2 working days"
          onChange={(e) => onChange({ ...value, lead_time: e.target.value })}
        />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">Optional — anything for Claude to emphasise?</Label>
        <Textarea
          placeholder="e.g. 'mention the 8-year guarantee' — leave blank for default copy"
          onChange={(e) => onChange({ ...value, ai_notes: e.target.value })}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `components/PricePromoFields.tsx`**

```tsx
"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Product } from "@/lib/products";

type Row = { product_id: string; pack: string; was: number; now: number };
type Props = { value: Record<string, unknown>; onChange: (v: Record<string, unknown>) => void };

export function PricePromoFields({ value, onChange }: Props) {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Row[]>([{ product_id: "", pack: "5L", was: 0, now: 0 }]);

  useEffect(() => {
    fetch("/api/products").then((r) => r.json()).then((d) => setProducts(d.products));
  }, []);

  useEffect(() => {
    onChange({ ...value, price_rows: rows });
  }, [rows]);

  function updateRow(i: number, patch: Partial<Row>) {
    setRows(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs uppercase tracking-wider">Promo name</Label>
          <Input placeholder="Winter Trade Promo" onChange={(e) => onChange({ ...value, promo_name: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label className="text-xs uppercase tracking-wider">Valid from</Label>
            <Input type="date" onChange={(e) => onChange({ ...value, valid_from: e.target.value })} />
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider">Valid to</Label>
            <Input type="date" onChange={(e) => onChange({ ...value, valid_to: e.target.value })} />
          </div>
        </div>
      </div>

      <div>
        <Label className="text-xs uppercase tracking-wider mb-2 block">SKUs on promo</Label>
        <div className="space-y-2">
          {rows.map((row, i) => (
            <div key={i} className="grid grid-cols-[2fr_1fr_1fr_1fr_auto] gap-2 items-end">
              <Select onValueChange={(v) => updateRow(i, { product_id: v })}>
                <SelectTrigger><SelectValue placeholder="Product…" /></SelectTrigger>
                <SelectContent>
                  {products.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
              <Input placeholder="5L" defaultValue={row.pack} onChange={(e) => updateRow(i, { pack: e.target.value })} />
              <Input type="number" placeholder="Was (R)" onChange={(e) => updateRow(i, { was: Number(e.target.value) })} />
              <Input type="number" placeholder="Now (R)" onChange={(e) => updateRow(i, { now: Number(e.target.value) })} />
              <Button variant="ghost" onClick={() => setRows(rows.filter((_, idx) => idx !== i))}>×</Button>
            </div>
          ))}
        </div>
        <Button
          variant="outline"
          className="mt-2 w-full"
          onClick={() => setRows([...rows, { product_id: "", pack: "5L", was: 0, now: 0 }])}
        >
          + Add another SKU
        </Button>
      </div>

      <div>
        <Label className="text-xs uppercase tracking-wider">Terms & conditions</Label>
        <Textarea
          placeholder="e.g. Promotional prices ex VAT, valid…"
          onChange={(e) => onChange({ ...value, terms_text: e.target.value })}
        />
      </div>

      <div>
        <Label className="text-xs uppercase tracking-wider">Optional — anything for Claude to emphasise?</Label>
        <Textarea onChange={(e) => onChange({ ...value, ai_notes: e.target.value })} />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `components/TradeInfoFields.tsx`**

```tsx
"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

type Props = { value: Record<string, unknown>; onChange: (v: Record<string, unknown>) => void };

export function TradeInfoFields({ value, onChange }: Props) {
  const [changing, setChanging] = useState("");
  const [unchanged, setUnchanged] = useState("");

  useEffect(() => {
    onChange({
      ...value,
      changing_items: changing.split("\n").filter(Boolean),
      unchanged_items: unchanged.split("\n").filter(Boolean),
    });
  }, [changing, unchanged]);

  return (
    <div className="space-y-3">
      <div>
        <Label className="text-xs uppercase tracking-wider">Notice date</Label>
        <Input type="date" onChange={(e) => onChange({ ...value, notice_date: e.target.value })} />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">What's the notice about? (headline direction)</Label>
        <Input
          placeholder="e.g. New 2026 packaging is rolling out"
          onChange={(e) => onChange({ ...value, headline_direction: e.target.value })}
        />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">What's changing (one item per line)</Label>
        <Textarea rows={4} onChange={(e) => setChanging(e.target.value)} />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">What stays the same (one item per line)</Label>
        <Textarea rows={3} onChange={(e) => setUnchanged(e.target.value)} />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">What you need recipients to do</Label>
        <Textarea
          placeholder="e.g. By 30 June: confirm your scanners read the new barcode."
          onChange={(e) => onChange({ ...value, action_required_text: e.target.value })}
        />
      </div>
      <div>
        <Label className="text-xs uppercase tracking-wider">Optional — anything for Claude to emphasise?</Label>
        <Textarea onChange={(e) => onChange({ ...value, ai_notes: e.target.value })} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Re-run dev and verify the form loads**

```powershell
npm run dev
```

Open `/compose`. Pick each template — fields should render. Try invalid combo (Architect + Price Promotion) — Architect button should be disabled with a tooltip.

- [ ] **Step 5: Commit**

```powershell
git add components/ProductPromoFields.tsx components/PricePromoFields.tsx components/TradeInfoFields.tsx
git commit -m "feat(ui): conditional field-set components for the three templates"
```

---

### Task 14: Preview page

**Files:**
- Create: `app/preview/[id]/page.tsx`
- Create: `components/PreviewActions.tsx`

- [ ] **Step 1: Create `app/preview/[id]/page.tsx`**

```tsx
import { kv } from "@vercel/kv";
import { notFound } from "next/navigation";
import { PreviewActions } from "@/components/PreviewActions";

export default async function PreviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const html = await kv.get<string>(`preview:${id}`);
  if (!html) return notFound();

  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white p-6">
      <div className="max-w-3xl mx-auto space-y-4">
        <PreviewActions previewId={id} html={html} />
        <div className="bg-white rounded-lg overflow-hidden">
          <iframe
            srcDoc={html}
            className="w-full"
            style={{ height: "900px", border: "none" }}
            title="Email preview"
          />
        </div>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Create `components/PreviewActions.tsx`**

```tsx
"use client";

import { Button } from "@/components/ui/button";

type Props = { previewId: string; html: string };

export function PreviewActions({ previewId, html }: Props) {
  function download() {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `olympic-email-${previewId.slice(0, 8)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function copy() {
    navigator.clipboard.writeText(html);
    alert("HTML copied to clipboard — paste into Outlook's HTML editor.");
  }

  return (
    <div className="flex items-center justify-between bg-[#161614] border border-[#1e1e1e] rounded-xl p-4">
      <div className="text-sm text-neutral-400">Preview · paste into Outlook to send</div>
      <div className="flex gap-2">
        <Button onClick={copy} variant="outline">Copy HTML</Button>
        <Button onClick={download} className="bg-[#F5C400] text-[#0D0D0D] hover:bg-yellow-400">Download HTML</Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: End-to-end smoke test**

```powershell
npm run dev
```

Open `http://localhost:3000` → "Start a campaign" → pick Product Promotion, Stockist, Natural Elegance Plus, lead time "2 working days", a note — Generate. Wait 5–10 seconds. Verify you land on `/preview/<uuid>` with a rendered email visible in the iframe, and Download/Copy buttons work.

- [ ] **Step 4: Commit**

```powershell
git add app/preview/[id]/page.tsx components/PreviewActions.tsx
git commit -m "feat(ui): preview page with iframe + Download / Copy actions"
```

---

## Phase 4: The other two templates

### Task 15: Price Promotion template + wire to API

**Files:**
- Create: `lib/templates/price-promotion.tsx`
- Modify: `app/api/render-email/route.ts`

- [ ] **Step 1: Create `lib/templates/price-promotion.tsx`**

```tsx
import { Html, Head, Body, Container, Section, Text, Row, Column } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";
import type { Voice } from "@/lib/voice";
import type { Product } from "@/lib/products";
import type { EmailCopy } from "@/lib/ai/schemas";
import { Header } from "./shared/Header";
import { Footer } from "./shared/Footer";
import { MetaBlock } from "./shared/MetaBlock";
import { CtaButton } from "./shared/CtaButton";

type PriceRow = { product_id: string; pack: string; was: number; now: number };
type Props = {
  voice: Voice;
  copy: EmailCopy;
  promoName: string;
  validFrom: string;
  validTo: string;
  rows: PriceRow[];
  products: Record<string, Product>; // id → product
  termsText: string;
  ctaPrimaryUrl: string;
  ctaSecondaryUrl: string;
};

export function PricePromotion({
  voice, copy, promoName, validFrom, validTo, rows, products, termsText,
  ctaPrimaryUrl, ctaSecondaryUrl,
}: Props) {
  const dateLabel = `Promotional Pricing · Valid ${validFrom} to ${validTo}`;
  const useTradePrice = voice.price_table_columns.includes("trade_now");

  return (
    <Html>
      <Head />
      <Body style={{ margin: 0, backgroundColor: tokens.colors.neutralRamp[50] }}>
        <Container style={{ maxWidth: tokens.email.containerWidthPx, backgroundColor: tokens.colors.brand.white, fontFamily: tokens.fonts.body }}>
          <Header dateLabel={dateLabel} />

          <Section style={{
            backgroundColor: tokens.colors.brand.yellow,
            padding: "10px 20px",
            textAlign: "center",
          }}>
            <Text style={{
              margin: 0, fontFamily: tokens.fonts.display, fontWeight: 800,
              fontSize: 12, letterSpacing: "0.1em", textTransform: "uppercase",
              color: tokens.colors.brand.black,
            }}>★ {promoName} · Valid {validFrom} – {validTo} ★</Text>
          </Section>

          <Section style={{ padding: "20px 24px" }}>
            <Text style={{ margin: 0, fontFamily: tokens.fonts.display, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: tokens.colors.neutralRamp[600] }}>{copy.eyebrow}</Text>
            <Text style={{ margin: "6px 0 4px", fontFamily: tokens.fonts.display, fontWeight: 900, fontSize: 32, lineHeight: 1.05, textTransform: "uppercase", color: tokens.colors.brand.black }}>{copy.headline}</Text>
            <Text style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: tokens.colors.neutralRamp[800] }}>{copy.body}</Text>
          </Section>

          <Section style={{ padding: "0 24px 20px" }}>
            <table width="100%" cellPadding={0} cellSpacing={0} style={{ borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ backgroundColor: tokens.colors.brand.navy, color: tokens.colors.brand.white }}>
                  <th style={{ padding: "10px 12px", textAlign: "left", fontFamily: tokens.fonts.display, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>Product</th>
                  <th style={{ padding: "10px 12px", textAlign: "left", fontFamily: tokens.fonts.display, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>Pack</th>
                  <th style={{ padding: "10px 12px", textAlign: "left", fontFamily: tokens.fonts.display, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>Was</th>
                  <th style={{ padding: "10px 12px", textAlign: "left", fontFamily: tokens.fonts.display, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>Now</th>
                  <th style={{ padding: "10px 12px", textAlign: "left", fontFamily: tokens.fonts.display, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>Save</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => {
                  const product = products[r.product_id];
                  const save = Math.round((1 - r.now / r.was) * 100);
                  return (
                    <tr key={i} style={{ backgroundColor: i % 2 === 1 ? tokens.colors.neutralRamp[50] : "transparent" }}>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${tokens.colors.neutralRamp[100]}` }}>{product?.name ?? r.product_id}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${tokens.colors.neutralRamp[100]}` }}>{r.pack}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${tokens.colors.neutralRamp[100]}`, color: tokens.colors.neutralRamp[400], textDecoration: "line-through" }}>R{r.was}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${tokens.colors.neutralRamp[100]}`, fontWeight: 700 }}>R{r.now}</td>
                      <td style={{ padding: "10px 12px", borderBottom: `1px solid ${tokens.colors.neutralRamp[100]}`, color: tokens.colors.status.success, fontWeight: 700 }}>−{save}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <Text style={{ margin: "8px 0 0", fontSize: 11, color: tokens.colors.neutralRamp[600] }}>
              {useTradePrice ? "Prices ex VAT, trade." : "Prices incl VAT, recommended retail."}
            </Text>
          </Section>

          <MetaBlock label="The fine print" rows={[{ label: "Terms", value: termsText }]} />

          <Section style={{ padding: "0 24px 24px" }}>
            <CtaButton href={ctaPrimaryUrl} label={copy.cta_primary} />
            {copy.cta_secondary && <CtaButton href={ctaSecondaryUrl} label={copy.cta_secondary} variant="ghost" />}
          </Section>

          <Footer signOff={voice.sign_off} signOffEmail={voice.sign_off_email} />
        </Container>
      </Body>
    </Html>
  );
}
```

- [ ] **Step 2: Wire the new template into the API route**

Modify `app/api/render-email/route.ts`. Replace the existing `if (input.template === "product-promotion")` block with a switch:

```ts
// at the top, add imports
import { PricePromotion } from "@/lib/templates/price-promotion";

// in POST, replace the existing template branch:
let html: string;
const voice = loadVoice(input.audience);

if (input.template === "product-promotion") {
  const product = getProductById(input.product_id);
  if (!product) return NextResponse.json({ error: `Unknown product ${input.product_id}` }, { status: 400 });
  html = await render(ProductPromotion({
    voice, copy, product,
    leadTime: input.lead_time,
    ctaPrimaryUrl: "https://olympicpaints.co.za/order",
    ctaSecondaryUrl: product.spec_sheet_url ?? "https://olympicpaints.co.za",
  }));
} else if (input.template === "price-promotion") {
  const productMap: Record<string, NonNullable<ReturnType<typeof getProductById>>> = {};
  for (const row of input.price_rows) {
    const p = getProductById(row.product_id);
    if (!p) return NextResponse.json({ error: `Unknown product ${row.product_id}` }, { status: 400 });
    productMap[row.product_id] = p;
  }
  html = await render(PricePromotion({
    voice, copy,
    promoName: input.promo_name,
    validFrom: input.valid_from,
    validTo: input.valid_to,
    rows: input.price_rows,
    products: productMap,
    termsText: input.terms_text,
    ctaPrimaryUrl: "https://olympicpaints.co.za/order",
    ctaSecondaryUrl: "https://olympicpaints.co.za/price-list",
  }));
} else {
  return NextResponse.json({ error: `Template ${input.template} not implemented yet` }, { status: 501 });
}
```

- [ ] **Step 3: Smoke test Price Promotion via the UI**

```powershell
npm run dev
```

Open `/compose` → Price Promotion → Stockist → fill promo name, dates, one price row, terms — Generate. Verify the preview shows a price table.

- [ ] **Step 4: Commit**

```powershell
git add lib/templates/price-promotion.tsx app/api/render-email/route.ts
git commit -m "feat(templates): Price Promotion template wired through the API"
```

---

### Task 16: Trade Information template + wire to API

**Files:**
- Create: `lib/templates/trade-information.tsx`
- Modify: `app/api/render-email/route.ts`

- [ ] **Step 1: Create `lib/templates/trade-information.tsx`**

```tsx
import { Html, Head, Body, Container, Section, Text } from "@react-email/components";
import { tokens } from "@/lib/brand/design-tokens";
import type { Voice } from "@/lib/voice";
import type { EmailCopy } from "@/lib/ai/schemas";
import { Header } from "./shared/Header";
import { Footer } from "./shared/Footer";
import { MetaBlock } from "./shared/MetaBlock";
import { CtaButton } from "./shared/CtaButton";

type Props = {
  voice: Voice;
  copy: EmailCopy;
  noticeDate: string;
  changingItems: string[];
  unchangedItems: string[];
  actionRequiredText: string;
  ctaPrimaryUrl: string;
  ctaSecondaryUrl: string;
};

function BulletList({ items }: { items: string[] }) {
  return (
    <Section style={{ padding: "0 24px" }}>
      {items.map((item, i) => (
        <Text key={i} style={{
          margin: 0,
          padding: "10px 0 10px 24px",
          position: "relative",
          fontSize: 14,
          color: tokens.colors.neutralRamp[800],
          borderBottom: i < items.length - 1 ? `1px solid ${tokens.colors.neutralRamp[100]}` : "none",
          lineHeight: 1.5,
        }}>
          {/* yellow square pseudo-bullet */}
          <span style={{
            display: "inline-block",
            width: 12, height: 12,
            backgroundColor: tokens.colors.brand.yellow,
            borderRadius: 2,
            marginRight: 12,
            verticalAlign: "middle",
          }} />
          {item}
        </Text>
      ))}
    </Section>
  );
}

export function TradeInformation({
  voice, copy, noticeDate, changingItems, unchangedItems, actionRequiredText,
  ctaPrimaryUrl, ctaSecondaryUrl,
}: Props) {
  const dateLabel = `Trade Notice · ${noticeDate}`;

  return (
    <Html>
      <Head />
      <Body style={{ margin: 0, backgroundColor: tokens.colors.neutralRamp[50] }}>
        <Container style={{ maxWidth: tokens.email.containerWidthPx, backgroundColor: tokens.colors.brand.white, fontFamily: tokens.fonts.body }}>
          <Header dateLabel={dateLabel} />

          <Section style={{ padding: "20px 24px" }}>
            <Text style={{ margin: 0, fontFamily: tokens.fonts.display, fontWeight: 700, fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: tokens.colors.neutralRamp[600] }}>{copy.eyebrow}</Text>
            <Text style={{ margin: "6px 0 4px", fontFamily: tokens.fonts.display, fontWeight: 900, fontSize: 30, lineHeight: 1.05, textTransform: "uppercase", color: tokens.colors.brand.black }}>{copy.headline}</Text>
            <Text style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: tokens.colors.neutralRamp[800] }}>{copy.body}</Text>
          </Section>

          <Section style={{ padding: "0 24px" }}>
            <Text style={{ margin: "20px 0 8px", fontFamily: tokens.fonts.display, fontWeight: 800, fontSize: 16, textTransform: "uppercase", color: tokens.colors.brand.black }}>What's changing</Text>
          </Section>
          <BulletList items={changingItems} />

          {unchangedItems.length > 0 && (
            <>
              <Section style={{ padding: "0 24px" }}>
                <Text style={{ margin: "20px 0 8px", fontFamily: tokens.fonts.display, fontWeight: 800, fontSize: 16, textTransform: "uppercase", color: tokens.colors.brand.black }}>What stays the same</Text>
              </Section>
              <BulletList items={unchangedItems} />
            </>
          )}

          <Section style={{ height: 20 }} />

          <MetaBlock label="What you need to do" rows={[{ label: "Action", value: actionRequiredText }]} />

          <Section style={{ padding: "0 24px 24px" }}>
            <CtaButton href={ctaPrimaryUrl} label={copy.cta_primary} />
            {copy.cta_secondary && <CtaButton href={ctaSecondaryUrl} label={copy.cta_secondary} variant="ghost" />}
          </Section>

          <Footer signOff={voice.sign_off} signOffEmail={voice.sign_off_email} />
        </Container>
      </Body>
    </Html>
  );
}
```

- [ ] **Step 2: Wire into the API route**

In `app/api/render-email/route.ts`, add to the imports:

```ts
import { TradeInformation } from "@/lib/templates/trade-information";
```

Replace the `return NextResponse.json({ error: \`Template ${input.template} not implemented yet\` }, { status: 501 });` with:

```ts
} else if (input.template === "trade-information") {
  html = await render(TradeInformation({
    voice, copy,
    noticeDate: input.notice_date,
    changingItems: input.changing_items,
    unchangedItems: input.unchanged_items,
    actionRequiredText: input.action_required_text,
    ctaPrimaryUrl: "https://olympicpaints.co.za/trade",
    ctaSecondaryUrl: "https://olympicpaints.co.za/faq",
  }));
} else {
  return NextResponse.json({ error: `Unknown template` }, { status: 400 });
}
```

- [ ] **Step 3: Smoke test Trade Information**

```powershell
npm run dev
```

Open `/compose` → Trade Information → Stockist → fill all fields with realistic content (e.g. "New 2026 packaging is rolling out") — Generate. Verify the preview shows bullet lists with yellow square markers and no banner image.

- [ ] **Step 4: Commit**

```powershell
git add lib/templates/trade-information.tsx app/api/render-email/route.ts
git commit -m "feat(templates): Trade Information template wired through the API"
```

---

## Phase 5: The other audience voices

### Task 17: Verify all four voices work across all valid combos

The voice files were written in Task 4. The templates already accept any `voice` prop. This task is end-to-end verification — no new code, just manual checks.

**Files:** none (manual test only)

- [ ] **Step 1: Test matrix**

```powershell
npm run dev
```

For each valid combo, generate one email and read the copy carefully:

| Audience | Product Promotion | Price Promotion | Trade Information |
|---|---|---|---|
| Stockist | ✓ test | ✓ test | ✓ test |
| Sales Rep | ✓ test | ✓ test | ✓ test |
| Contractor | ✓ test | ✓ test (verify it shows RRP, not trade price, in column header text) | ✓ test |
| Architect | ✓ test | — disabled | ✓ test |

For each generated email check:
- Sign-off matches the voice file (Olympic Trade Team / Sales Ops / Olympic Painter Programme / Olympic Specification)
- CTAs use the audience-appropriate vocabulary
- Body language matches (factual for Stockist; punchy for Rep; jobsite-practical for Contractor; technical for Architect)

- [ ] **Step 2: Note any voice-file tweaks needed**

If Claude's copy for any audience feels off (e.g. Architect copy is too casual), edit the corresponding `lib/brand/voice/<audience>.md` and re-test. The voice file is the place to fix tone, not the prompt builder.

- [ ] **Step 3: Commit any voice-file refinements**

```powershell
git add lib/brand/voice/
git commit -m "tune(brand): voice file refinements after end-to-end testing"
```

---

## Phase 6: Auth

### Task 18: Clerk SSO with @olympicpaints.co.za restriction

**Files:**
- Create: `middleware.ts`
- Create: `app/(auth)/sign-in/[[...sign-in]]/page.tsx`
- Create: `app/access-denied/page.tsx`
- Modify: `app/layout.tsx`

- [ ] **Step 1: Create a Clerk application**

Go to `dashboard.clerk.com`, create a new application called "Olympic Email Studio", enable Google + Microsoft as sign-in providers. Copy the publishable + secret keys into `.env.local`:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

- [ ] **Step 2: Wrap the app in ClerkProvider**

Modify `app/layout.tsx`:

```tsx
import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Olympic Email Studio",
  description: "Generate brand-correct Olympic Paints trade emails.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <head>
          <link rel="preconnect" href="https://fonts.googleapis.com" />
          <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
          <link
            href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;800;900&family=Barlow:wght@300;400;500;600&display=swap"
            rel="stylesheet"
          />
        </head>
        <body className="antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

- [ ] **Step 3: Create `middleware.ts`**

```ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isPublic = createRouteMatcher(["/sign-in(.*)", "/access-denied"]);

export default clerkMiddleware(async (auth, req) => {
  if (isPublic(req)) return;

  const { userId, sessionClaims } = await auth();
  if (!userId) {
    const url = req.nextUrl.clone();
    url.pathname = "/sign-in";
    return NextResponse.redirect(url);
  }

  // Domain restriction: pull email from session claims
  const email = (sessionClaims?.email as string | undefined) ?? "";
  if (!email.toLowerCase().endsWith("@olympicpaints.co.za")) {
    const url = req.nextUrl.clone();
    url.pathname = "/access-denied";
    return NextResponse.redirect(url);
  }
});

export const config = {
  matcher: ["/((?!_next|favicon.ico|assets|.*\\..*).*)"],
};
```

Note: for `sessionClaims.email` to be populated, configure your Clerk JWT template to include `"email": "{{user.primary_email_address}}"` (Clerk dashboard → JWT Templates → default).

- [ ] **Step 4: Create the sign-in page**

```tsx
// app/(auth)/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white flex items-center justify-center p-8">
      <SignIn appearance={{ variables: { colorPrimary: "#F5C400" } }} />
    </main>
  );
}
```

- [ ] **Step 5: Create the access-denied page**

```tsx
// app/access-denied/page.tsx
export default function AccessDeniedPage() {
  return (
    <main className="min-h-screen bg-[#0D0D0D] text-white flex flex-col items-center justify-center p-8 gap-4">
      <h1 className="text-3xl font-black uppercase text-[#F5C400]">Access denied</h1>
      <p className="text-sm text-neutral-400 max-w-md text-center">
        Olympic Email Studio is restricted to <strong>@olympicpaints.co.za</strong> accounts.
        Sign in with your Olympic email to continue.
      </p>
    </main>
  );
}
```

- [ ] **Step 6: Smoke test auth**

```powershell
npm run dev
```

Open `http://localhost:3000` — expect redirect to `/sign-in`. Sign in with a non-Olympic Google account — expect redirect to `/access-denied`. Sign in with `@olympicpaints.co.za` — expect to land on the landing page.

- [ ] **Step 7: Commit**

```powershell
git add middleware.ts app/(auth) app/access-denied app/layout.tsx
git commit -m "feat(auth): Clerk SSO with @olympicpaints.co.za domain restriction"
```

---

## Phase 7: Deploy

### Task 19: Asset sync + provision Vercel project

**Files:**
- Create: `scripts/sync-assets.ts`
- Create: `public/assets/logo.png`, `public/assets/packshots/*.png`, `public/assets/banners/*.{jpg,png}`

- [ ] **Step 1: Write `scripts/sync-assets.ts`**

```ts
// One-shot script: copy Olympic assets from OneDrive into public/assets/.
// Run with: npx tsx scripts/sync-assets.ts

import fs from "fs";
import path from "path";

const ONEDRIVE_BASE = "C:\\Users\\quint\\OneDrive\\1.Projects\\1.Olympic Paints\\3.Resources\\9. Brand Assets & Images";
const ONEDRIVE_BANNERS = "C:\\Users\\quint\\OneDrive - Olympic Paints\\2.Areas\\8. Marketing\\Digital\\Olympic Mail (1200 x 325 px)";
const PUBLIC_ASSETS = path.join(process.cwd(), "public", "assets");

const COPIES: Array<{ from: string; to: string }> = [
  { from: path.join(ONEDRIVE_BASE, "Misc Pictures", "Olympic Paints Logo Digital.jpg"), to: path.join(PUBLIC_ASSETS, "logo.png") },
  { from: path.join(ONEDRIVE_BASE, "Packshot Mockups - May 2025", "NATURAL ELEGANCE PLUS v2.png"), to: path.join(PUBLIC_ASSETS, "packshots", "natural-elegance-plus.png") },
  { from: path.join(ONEDRIVE_BANNERS, "1.png"), to: path.join(PUBLIC_ASSETS, "banners", "natural-elegance-banner.jpg") },
];

for (const { from, to } of COPIES) {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
  console.log(`✓ ${path.basename(to)}`);
}
console.log("\nAsset sync complete.");
```

- [ ] **Step 2: Install tsx and run the sync**

```powershell
npm install -D tsx
npx tsx scripts/sync-assets.ts
```

Expected: three files copied.

- [ ] **Step 3: Commit the assets**

```powershell
git add scripts/sync-assets.ts public/assets/ package.json package-lock.json
git commit -m "feat(assets): sync script + seed logo, NEP packshot, NEP banner from OneDrive"
```

- [ ] **Step 4: Provision Vercel project**

```powershell
npx vercel login
npx vercel link
```

Follow prompts to create a new project named `olympic-email-studio` under your Vercel account.

- [ ] **Step 5: Add Vercel KV integration**

In Vercel dashboard → Storage → Create → KV → name it `olympic-email-kv`, connect to the `olympic-email-studio` project. Vercel auto-injects `KV_REST_API_URL` and `KV_REST_API_TOKEN` into the project env.

- [ ] **Step 6: Add remaining env vars in Vercel dashboard**

Add `ANTHROPIC_API_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` to Production + Preview environments.

- [ ] **Step 7: Pull the env vars locally so `npm run dev` works against prod KV**

```powershell
npx vercel env pull .env.local
```

---

### Task 20: First deploy + post-deploy verification

**Files:**
- Modify: `lib/templates/shared/Header.tsx`, `lib/templates/shared/Footer.tsx`, all template files — replace hardcoded `https://olympic-email.vercel.app` with `process.env.NEXT_PUBLIC_APP_URL` so URLs work in preview deploys too.

- [ ] **Step 1: Add NEXT_PUBLIC_APP_URL handling**

Create `lib/app-url.ts`:

```ts
export function appUrl(): string {
  return process.env.NEXT_PUBLIC_APP_URL
    ?? (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");
}
```

Replace every hardcoded `https://olympic-email.vercel.app` in `lib/templates/` with `${appUrl()}` (use ripgrep to find them).

- [ ] **Step 2: Add NEXT_PUBLIC_APP_URL to Vercel env**

In Vercel dashboard: Production = `https://olympic-email.vercel.app`. Leave Preview unset so it falls back to `VERCEL_URL`.

- [ ] **Step 3: Deploy**

```powershell
npx vercel --prod
```

Wait for build to complete. Open the production URL.

- [ ] **Step 4: Post-deploy smoke test**

1. Sign in with an `@olympicpaints.co.za` account → land on `/`.
2. Click "Start a campaign" → `/compose`.
3. Generate one Product Promotion, one Price Promotion, one Trade Information.
4. For each: verify preview renders, images load (open browser devtools, check Network — no broken `/assets/*` requests), Download HTML works, the downloaded `.html` file opens in a browser and shows the same content.

- [ ] **Step 5: Outlook paste test**

Take the downloaded Product Promotion HTML. Open Outlook → New Email → switch to HTML view (Format Text tab → HTML) → paste. Verify:

- Logo renders (image, not broken)
- Yellow circle badge is visible
- Headline is uppercase in a condensed font (fallback to Arial Narrow if Outlook strips Barlow)
- CTA button is yellow with black text
- No raw `<table>` artefacts visible

If any of these fail, note them as v1.1 fix-ups. The most common issue is the logo URL — if `/assets/logo.png` returns 404, you need to re-run `sync-assets.ts` and commit + re-deploy.

- [ ] **Step 6: Commit and tag v1**

```powershell
git add lib/app-url.ts lib/templates/
git commit -m "feat(deploy): app URL helper + production-safe asset URLs"
git tag v1.0.0
git push --tags
```

---

## Notes for the implementing engineer

1. **You're on Windows.** Use PowerShell unless a command is explicitly bash. Watch for `/` vs `\` path separators in scripts that interact with the filesystem.
2. **Most "tests" in this plan are smoke tests, not unit tests.** That's deliberate — for a v1 internal tool where the AI is the brain, manual end-to-end smoke tests catch more real bugs than React Testing Library asserts on form rendering. The actual unit tests (`tests/*.test.ts`) cover pure logic: design tokens, products schema, voice loader, AI output schema, combos matrix. Don't add RTL tests for the form components in v1.
3. **The Anthropic SDK model ID is `claude-sonnet-4-6`** — see `@/lib/ai/render-email.ts`. Do not change this without checking the spec.
4. **The brand rules (visual-vocabulary.md and voice/*.md) are the source of truth for tone.** If Claude produces off-brand copy, fix the markdown files, not the prompt builder.
5. **OneDrive paths are case-sensitive in some tools but not others on Windows.** Stick with the exact casing in `scripts/sync-assets.ts` — that's what the actual folders are named.
6. **Vercel KV in dev:** if you don't have credentials yet, comment out the `await kv.set(...)` in `app/api/render-email/route.ts` and return the HTML directly in the response for local dev. Restore before deploy.
7. **Frequent commits.** Each task ends with a commit. Don't batch — small commits make rollback trivial.

---

## Self-review checklist (done by plan author)

1. **Spec coverage:** Every section of the spec has a task. Architecture (Tasks 1–2, 18–20), brand layer (Tasks 3–4, 7), templates (Tasks 9–10, 15–16), combos (Task 6), form (Tasks 11–13), preview (Task 14), render pipeline (Tasks 7, 8, 10), product data (Task 5), auth (Task 18), deploy (Tasks 19–20). ✓
2. **No placeholders.** Scanned for "TBD"/"TODO"/"implement later"/"handle edge cases" — none present. Each step has the code or command it needs. ✓
3. **Type consistency:** `Voice`, `Product`, `EmailCopy`, `FormInput`, `Audience`, `Template` are defined once (in their source files) and referenced consistently across tasks. The `voice.price_table_columns` field is defined in Task 4's YAML and exercised in Task 7's test and Task 15's template. ✓
4. **Open issue flagged in spec self-review:** form submission mechanism — settled in Task 12 (uses `fetch('/api/render-email')` from a client component, not Server Action). Outlook quirks budget — addressed by Task 20's post-deploy Outlook paste test.
