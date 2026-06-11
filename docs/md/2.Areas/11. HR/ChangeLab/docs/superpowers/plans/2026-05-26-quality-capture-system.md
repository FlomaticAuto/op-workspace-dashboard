# Olympic Paints Quality Capture System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tablet-based PWA for manufacturing assistants to capture batch quality checks (colour + viscosity), with an admin panel, supervisor dashboard, and Supabase backend — feeding the first-pass quality rate KPI.

**Architecture:** Next.js 14 App Router PWA deployed to Vercel. Supabase for database and row-level security. Three surfaces: (1) tablet app for assistants, (2) admin panel (PIN-protected), (3) supervisor dashboard (read-only). All share one Supabase project.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, Supabase (PostgreSQL + RLS), Vercel, `next-pwa` for PWA manifest.

---

## File Structure

```
quality-capture/
├── app/
│   ├── layout.tsx                    # Root layout, brand fonts, PWA meta
│   ├── page.tsx                      # Redirect → /tablet
│   ├── tablet/
│   │   ├── page.tsx                  # Batch queue (home screen)
│   │   └── batch/[id]/page.tsx       # Check screen for a single batch
│   ├── admin/
│   │   ├── layout.tsx                # PIN gate wrapper
│   │   ├── page.tsx                  # Admin home (section links)
│   │   ├── ford-cups/page.tsx        # Ford cup CRUD
│   │   ├── viscosity-targets/page.tsx# Viscosity target CRUD
│   │   ├── colours/page.tsx          # Colour library CRUD
│   │   ├── staff/page.tsx            # Staff roster CRUD
│   │   └── kpi/page.tsx              # KPI baseline/goal config
│   └── dashboard/
│       └── page.tsx                  # Supervisor read-only dashboard
├── components/
│   ├── ui/
│   │   ├── NavBar.tsx                # Olympic navy nav bar
│   │   ├── StatusPill.tsx            # Pass/Fail/Pending/Queued pills
│   │   ├── ColourSwatch.tsx          # Hex swatch display component
│   │   └── NumPad.tsx                # Touch numpad for viscosity entry
│   ├── tablet/
│   │   ├── BatchQueue.tsx            # Left panel — batch list
│   │   ├── BatchQueueItem.tsx        # Single batch row in queue
│   │   ├── AddBatchModal.tsx         # Modal to add a new batch
│   │   ├── CheckScreen.tsx           # Right panel — 4-card check grid
│   │   ├── ColourCheckCard.tsx       # Card 1+2: colour ref + pass/fail
│   │   ├── ViscosityCard.tsx         # Card 3: Ford cup numpad entry
│   │   └── SignOffCard.tsx           # Card 4: assistant + supervisor select
│   ├── admin/
│   │   ├── PinGate.tsx               # 4-digit PIN entry modal
│   │   ├── AdminTable.tsx            # Reusable CRUD table
│   │   └── AdminForm.tsx             # Reusable add/edit form
│   └── dashboard/
│       ├── KpiRateCard.tsx           # First-pass rate with traffic light
│       ├── BatchTable.tsx            # Full batch list with filters
│       └── ExportButton.tsx          # CSV export
├── lib/
│   ├── supabase/
│   │   ├── client.ts                 # Browser Supabase client
│   │   ├── server.ts                 # Server Supabase client (RSC)
│   │   └── types.ts                  # Generated DB types (supabase gen)
│   ├── constants.ts                  # Product tiers, brand colours, shift times
│   └── kpi.ts                        # first_pass_rate calculation helper
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql    # All tables + RLS policies
├── public/
│   ├── manifest.json                 # PWA manifest
│   └── icons/                        # PWA icons (192, 512)
├── __tests__/
│   ├── lib/kpi.test.ts               # KPI calculation unit tests
│   ├── lib/constants.test.ts         # Tier logic unit tests
│   ├── components/NumPad.test.tsx    # NumPad interaction tests
│   ├── components/ColourSwatch.test.tsx
│   └── components/StatusPill.test.tsx
├── next.config.ts
├── tailwind.config.ts
└── .env.local.example
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `quality-capture/` (project root)
- Create: `next.config.ts`
- Create: `tailwind.config.ts`
- Create: `.env.local.example`
- Create: `public/manifest.json`

- [ ] **Step 1: Scaffold Next.js app**

```bash
cd "C:/Users/quint/OneDrive/1.Projects/1.Olympic Paints/2.Areas/11. HR/ChangeLab"
npx create-next-app@latest quality-capture \
  --typescript --tailwind --eslint --app \
  --no-src-dir --import-alias "@/*"
cd quality-capture
```

- [ ] **Step 2: Install dependencies**

```bash
npm install @supabase/supabase-js @supabase/ssr
npm install next-pwa
npm install --save-dev vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

- [ ] **Step 3: Configure Tailwind with Olympic brand colours**

Replace `tailwind.config.ts` with:

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        olympic: {
          yellow:  '#F5C400',
          navy:    '#1A3D6E',
          black:   '#0D0D0D',
          dark:    '#1A1A1A',
          mid:     '#2C2C2C',
          border:  '#3A3A3A',
          muted:   '#888888',
        },
        pass:    '#27AE60',
        fail:    '#E74C3C',
        pending: '#F39C12',
      },
      screens: {
        tablet: '960px',
      },
    },
  },
  plugins: [],
}
export default config
```

- [ ] **Step 4: Configure Next.js with PWA**

Replace `next.config.ts` with:

```typescript
import type { NextConfig } from 'next'
const withPWA = require('next-pwa')({ dest: 'public', disable: process.env.NODE_ENV === 'development' })

const nextConfig: NextConfig = {
  reactStrictMode: true,
}

module.exports = withPWA(nextConfig)
```

- [ ] **Step 5: Create PWA manifest**

Create `public/manifest.json`:

```json
{
  "name": "Olympic Paints Quality Capture",
  "short_name": "Quality",
  "start_url": "/tablet",
  "display": "standalone",
  "orientation": "landscape",
  "background_color": "#0D0D0D",
  "theme_color": "#1A3D6E",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

- [ ] **Step 6: Create `.env.local.example`**

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
ADMIN_PIN_HASH=your-bcrypt-hash-of-4-digit-pin
```

- [ ] **Step 7: Configure Vitest**

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: true,
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, '.') },
  },
})
```

Create `vitest.setup.ts`:

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 8: Commit scaffold**

```bash
git init
git add .
git commit -m "chore: scaffold Next.js PWA with Olympic brand colours"
```

---

## Task 2: Supabase Schema & Migrations

**Files:**
- Create: `supabase/migrations/001_initial_schema.sql`
- Create: `lib/supabase/client.ts`
- Create: `lib/supabase/server.ts`
- Create: `lib/constants.ts`

- [ ] **Step 1: Create Supabase project**

Go to https://supabase.com → New project. Name it `olympic-quality-capture`. Note the project URL and anon key. Copy to `.env.local` (from `.env.local.example`).

- [ ] **Step 2: Write the migration**

Create `supabase/migrations/001_initial_schema.sql`:

```sql
-- Enable UUID extension
create extension if not exists "pgcrypto";

-- STAFF
create table staff (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  role text not null check (role in ('assistant', 'supervisor', 'admin')),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- FORD CUPS
create table ford_cups (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  orifice_mm numeric,
  notes text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- VISCOSITY TARGETS
create table viscosity_targets (
  id uuid primary key default gen_random_uuid(),
  product_tier text not null check (product_tier in (
    'decor', 'eclipse', 'kalahari', 'master_decorator', 'enamel'
  )),
  ford_cup_id uuid references ford_cups(id),
  min_seconds numeric not null,
  max_seconds numeric not null,
  notes text,
  updated_at timestamptz not null default now(),
  updated_by uuid references staff(id)
);

-- COLOURS
create table colours (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  hex_code text not null,
  product_tier text not null check (product_tier in (
    'decor', 'eclipse', 'kalahari', 'master_decorator', 'enamel'
  )),
  range_code text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- KPI CONFIG
create table kpi_config (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  value numeric not null,
  updated_at timestamptz not null default now()
);
-- seed baseline and goal
insert into kpi_config (key, value) values ('baseline', 82), ('goal', 92);

-- BATCHES
create table batches (
  id uuid primary key default gen_random_uuid(),
  batch_number text not null,
  product_tier text not null check (product_tier in (
    'decor', 'eclipse', 'kalahari', 'master_decorator', 'enamel'
  )),
  colour_id uuid references colours(id),
  shift text not null check (shift in ('morning', 'afternoon', 'night')),
  colour_pass boolean,
  colour_notes text,
  viscosity_seconds numeric,
  viscosity_pass boolean,
  first_pass boolean,
  oven_dried boolean,
  drawdown_done boolean,
  assistant_id uuid references staff(id),
  supervisor_id uuid references staff(id),
  checked_at timestamptz,
  created_at timestamptz not null default now()
);

-- ROW LEVEL SECURITY
alter table batches enable row level security;
alter table staff enable row level security;
alter table colours enable row level security;
alter table ford_cups enable row level security;
alter table viscosity_targets enable row level security;
alter table kpi_config enable row level security;

-- Public read for tablet app (anon key)
create policy "anon can read colours" on colours for select using (active = true);
create policy "anon can read staff" on staff for select using (active = true);
create policy "anon can read ford_cups" on ford_cups for select using (active = true);
create policy "anon can read viscosity_targets" on viscosity_targets for select using (true);
create policy "anon can read kpi_config" on kpi_config for select using (true);
create policy "anon can insert batches" on batches for insert with check (true);
create policy "anon can read batches" on batches for select using (true);

-- Allow all updates via service role (used by admin panel server actions)
```

- [ ] **Step 3: Apply migration via Supabase dashboard**

Go to Supabase → SQL Editor → paste `001_initial_schema.sql` → Run.

Verify tables exist: `staff`, `ford_cups`, `viscosity_targets`, `colours`, `kpi_config`, `batches`.

- [ ] **Step 4: Create browser Supabase client**

Create `lib/supabase/client.ts`:

```typescript
import { createBrowserClient } from '@supabase/ssr'
import type { Database } from './types'

export function createClient() {
  return createBrowserClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

- [ ] **Step 5: Create server Supabase client**

Create `lib/supabase/server.ts`:

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { Database } from './types'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

- [ ] **Step 6: Create constants**

Create `lib/constants.ts`:

```typescript
export const PRODUCT_TIERS = [
  'decor',
  'eclipse',
  'kalahari',
  'master_decorator',
  'enamel',
] as const

export type ProductTier = typeof PRODUCT_TIERS[number]

export const TIER_LABELS: Record<ProductTier, string> = {
  decor:             'Decor',
  eclipse:           'Eclipse',
  kalahari:          'Kalahari',
  master_decorator:  'Master Decorator',
  enamel:            'Enamel',
}

// Tiers that require a drawdown before colour check
export const DRAWDOWN_TIERS: ProductTier[] = ['master_decorator']

// Tiers that require oven-dry before colour check
export const OVEN_TIERS: ProductTier[] = ['enamel']

export const SHIFTS = ['morning', 'afternoon', 'night'] as const
export type Shift = typeof SHIFTS[number]

export const BRAND = {
  yellow:  '#F5C400',
  navy:    '#1A3D6E',
  black:   '#0D0D0D',
  dark:    '#1A1A1A',
  mid:     '#2C2C2C',
  border:  '#3A3A3A',
  muted:   '#888888',
  pass:    '#27AE60',
  fail:    '#E74C3C',
  pending: '#F39C12',
} as const
```

- [ ] **Step 7: Generate Supabase types**

```bash
npx supabase gen types typescript \
  --project-id YOUR_PROJECT_ID \
  --schema public > lib/supabase/types.ts
```

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: supabase schema, migrations, clients, and constants"
```

---

## Task 3: KPI Helper & Unit Tests

**Files:**
- Create: `lib/kpi.ts`
- Create: `__tests__/lib/kpi.test.ts`
- Create: `__tests__/lib/constants.test.ts`

- [ ] **Step 1: Write failing KPI tests**

Create `__tests__/lib/kpi.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { calcFirstPassRate, getTrafficLight } from '@/lib/kpi'

describe('calcFirstPassRate', () => {
  it('returns 100 when all batches pass', () => {
    expect(calcFirstPassRate(10, 10)).toBe(100)
  })

  it('returns 0 when no batches pass', () => {
    expect(calcFirstPassRate(0, 10)).toBe(0)
  })

  it('returns correct percentage', () => {
    expect(calcFirstPassRate(82, 100)).toBe(82)
  })

  it('returns null when total is 0 (no data)', () => {
    expect(calcFirstPassRate(0, 0)).toBeNull()
  })

  it('rounds to one decimal place', () => {
    expect(calcFirstPassRate(1, 3)).toBe(33.3)
  })
})

describe('getTrafficLight', () => {
  it('returns green when rate >= goal', () => {
    expect(getTrafficLight(92, 82, 92)).toBe('green')
  })

  it('returns amber when rate >= baseline but below goal', () => {
    expect(getTrafficLight(85, 82, 92)).toBe('amber')
  })

  it('returns red when rate < baseline', () => {
    expect(getTrafficLight(70, 82, 92)).toBe('red')
  })

  it('returns red when rate is null', () => {
    expect(getTrafficLight(null, 82, 92)).toBe('red')
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
npx vitest run __tests__/lib/kpi.test.ts
```

Expected: FAIL — `Cannot find module '@/lib/kpi'`

- [ ] **Step 3: Write failing constants tests**

Create `__tests__/lib/constants.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { DRAWDOWN_TIERS, OVEN_TIERS, requiresDrawdown, requiresOven } from '@/lib/constants'

describe('requiresDrawdown', () => {
  it('returns true for master_decorator', () => {
    expect(requiresDrawdown('master_decorator')).toBe(true)
  })
  it('returns false for decor', () => {
    expect(requiresDrawdown('decor')).toBe(false)
  })
  it('returns false for enamel', () => {
    expect(requiresDrawdown('enamel')).toBe(false)
  })
})

describe('requiresOven', () => {
  it('returns true for enamel', () => {
    expect(requiresOven('enamel')).toBe(true)
  })
  it('returns false for master_decorator', () => {
    expect(requiresOven('master_decorator')).toBe(false)
  })
})
```

- [ ] **Step 4: Run constants tests — verify they fail**

```bash
npx vitest run __tests__/lib/constants.test.ts
```

Expected: FAIL — `requiresDrawdown is not exported`

- [ ] **Step 5: Implement `lib/kpi.ts`**

Create `lib/kpi.ts`:

```typescript
export function calcFirstPassRate(passed: number, total: number): number | null {
  if (total === 0) return null
  return Math.round((passed / total) * 1000) / 10
}

export type TrafficLight = 'green' | 'amber' | 'red'

export function getTrafficLight(
  rate: number | null,
  baseline: number,
  goal: number
): TrafficLight {
  if (rate === null || rate < baseline) return 'red'
  if (rate >= goal) return 'green'
  return 'amber'
}
```

- [ ] **Step 6: Add helper functions to `lib/constants.ts`**

Append to the bottom of `lib/constants.ts`:

```typescript
export function requiresDrawdown(tier: ProductTier): boolean {
  return DRAWDOWN_TIERS.includes(tier)
}

export function requiresOven(tier: ProductTier): boolean {
  return OVEN_TIERS.includes(tier)
}
```

- [ ] **Step 7: Run all tests — verify they pass**

```bash
npx vitest run
```

Expected: All 12 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: kpi helpers and constants with full test coverage"
```

---

## Task 4: Shared UI Components

**Files:**
- Create: `components/ui/NavBar.tsx`
- Create: `components/ui/StatusPill.tsx`
- Create: `components/ui/ColourSwatch.tsx`
- Create: `components/ui/NumPad.tsx`
- Create: `__tests__/components/StatusPill.test.tsx`
- Create: `__tests__/components/ColourSwatch.test.tsx`
- Create: `__tests__/components/NumPad.test.tsx`

- [ ] **Step 1: Write failing component tests**

Create `__tests__/components/StatusPill.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusPill } from '@/components/ui/StatusPill'

describe('StatusPill', () => {
  it('renders "Pass" with green style', () => {
    render(<StatusPill status="pass" />)
    expect(screen.getByText('Pass')).toBeInTheDocument()
  })
  it('renders "Fail" with red style', () => {
    render(<StatusPill status="fail" />)
    expect(screen.getByText('Fail')).toBeInTheDocument()
  })
  it('renders "Pending" with amber style', () => {
    render(<StatusPill status="pending" />)
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })
  it('renders "Queued" with grey style', () => {
    render(<StatusPill status="queued" />)
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })
})
```

Create `__tests__/components/ColourSwatch.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ColourSwatch } from '@/components/ui/ColourSwatch'

describe('ColourSwatch', () => {
  it('renders colour name', () => {
    render(<ColourSwatch name="Autumn Spice" hexCode="#C4843E" />)
    expect(screen.getByText('Autumn Spice')).toBeInTheDocument()
  })
  it('renders hex code', () => {
    render(<ColourSwatch name="Autumn Spice" hexCode="#C4843E" />)
    expect(screen.getByText('#C4843E')).toBeInTheDocument()
  })
})
```

Create `__tests__/components/NumPad.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { NumPad } from '@/components/ui/NumPad'

describe('NumPad', () => {
  it('calls onChange when a digit is tapped', () => {
    const onChange = vi.fn()
    render(<NumPad value="" onChange={onChange} />)
    fireEvent.click(screen.getByText('5'))
    expect(onChange).toHaveBeenCalledWith('5')
  })

  it('calls onChange with empty string when backspace tapped', () => {
    const onChange = vi.fn()
    render(<NumPad value="28" onChange={onChange} />)
    fireEvent.click(screen.getByText('⌫'))
    expect(onChange).toHaveBeenCalledWith('2')
  })

  it('does not exceed 4 digits', () => {
    const onChange = vi.fn()
    render(<NumPad value="1234" onChange={onChange} />)
    fireEvent.click(screen.getByText('5'))
    expect(onChange).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
npx vitest run __tests__/components/
```

Expected: FAIL — components not found.

- [ ] **Step 3: Create `NavBar.tsx`**

Create `components/ui/NavBar.tsx`:

```typescript
interface NavBarProps {
  shift?: string
  time?: string
}

export function NavBar({ shift, time }: NavBarProps) {
  return (
    <nav className="h-13 bg-olympic-navy flex items-center justify-between px-5 flex-shrink-0">
      <div className="flex items-center gap-3">
        <span className="bg-white text-olympic-navy font-black text-xs px-2 py-1 rounded tracking-widest">
          OLYMPIC
        </span>
        <span className="text-white font-semibold text-sm tracking-wide">
          Quality Capture
        </span>
      </div>
      {(shift || time) && (
        <div className="text-white/75 text-xs text-right leading-relaxed">
          {shift && <div>{shift}</div>}
          {time && <div>{time}</div>}
        </div>
      )}
    </nav>
  )
}
```

- [ ] **Step 4: Create `StatusPill.tsx`**

Create `components/ui/StatusPill.tsx`:

```typescript
export type BatchStatus = 'pass' | 'fail' | 'pending' | 'queued'

const STATUS_CONFIG: Record<BatchStatus, { label: string; className: string }> = {
  pass:    { label: 'Pass',    className: 'bg-pass text-white' },
  fail:    { label: 'Fail',    className: 'bg-fail text-white' },
  pending: { label: 'Pending', className: 'bg-pending text-white' },
  queued:  { label: 'Queued',  className: 'bg-olympic-border text-olympic-muted' },
}

interface StatusPillProps {
  status: BatchStatus
}

export function StatusPill({ status }: StatusPillProps) {
  const { label, className } = STATUS_CONFIG[status]
  return (
    <span className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-wide ${className}`}>
      {label}
    </span>
  )
}
```

- [ ] **Step 5: Create `ColourSwatch.tsx`**

Create `components/ui/ColourSwatch.tsx`:

```typescript
interface ColourSwatchProps {
  name: string
  hexCode: string
}

export function ColourSwatch({ name, hexCode }: ColourSwatchProps) {
  return (
    <div className="flex items-center gap-3">
      <div
        className="w-14 h-14 rounded-md border-2 border-olympic-border flex-shrink-0"
        style={{ background: hexCode }}
        aria-label={`Colour swatch for ${name}`}
      />
      <div>
        <div className="text-white font-bold text-sm">{name}</div>
        <div className="text-olympic-muted text-xs font-mono">{hexCode}</div>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create `NumPad.tsx`**

Create `components/ui/NumPad.tsx`:

```typescript
interface NumPadProps {
  value: string
  onChange: (value: string) => void
  maxDigits?: number
}

const KEYS = ['1','2','3','⌫','4','5','6','.','7','8','9','0']

export function NumPad({ value, onChange, maxDigits = 4 }: NumPadProps) {
  function handleKey(key: string) {
    if (key === '⌫') {
      onChange(value.slice(0, -1))
      return
    }
    if (value.length >= maxDigits) return
    onChange(value + key)
  }

  return (
    <div className="grid grid-cols-4 gap-1">
      {KEYS.map((key) => (
        <button
          key={key}
          onClick={() => handleKey(key)}
          className={`
            rounded py-2 text-sm font-semibold text-white min-h-[44px]
            ${key === '⌫' || key === '.' ? 'bg-olympic-border' : 'bg-olympic-light'}
            active:opacity-70
          `}
        >
          {key}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 7: Run all tests — verify they pass**

```bash
npx vitest run
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: shared UI components — NavBar, StatusPill, ColourSwatch, NumPad"
```

---

## Task 5: Tablet App — Batch Queue

**Files:**
- Create: `app/tablet/page.tsx`
- Create: `components/tablet/BatchQueue.tsx`
- Create: `components/tablet/BatchQueueItem.tsx`
- Create: `components/tablet/AddBatchModal.tsx`

- [ ] **Step 1: Create the root layout**

Replace `app/layout.tsx`:

```typescript
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Olympic Paints — Quality Capture',
  manifest: '/manifest.json',
  themeColor: '#1A3D6E',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-olympic-black text-white antialiased overflow-hidden">
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 2: Create `BatchQueueItem.tsx`**

Create `components/tablet/BatchQueueItem.tsx`:

```typescript
import { StatusPill, type BatchStatus } from '@/components/ui/StatusPill'
import { TIER_LABELS, type ProductTier } from '@/lib/constants'

export interface BatchQueueItemData {
  id: string
  batch_number: string
  product_tier: ProductTier
  colour_name?: string
  status: BatchStatus
  created_at: string
}

interface BatchQueueItemProps {
  batch: BatchQueueItemData
  isActive: boolean
  onSelect: (id: string) => void
}

export function BatchQueueItem({ batch, isActive, onSelect }: BatchQueueItemProps) {
  return (
    <button
      onClick={() => onSelect(batch.id)}
      className={`
        w-full rounded-md px-3 py-2.5 flex justify-between items-center
        border-2 text-left transition-colors
        ${isActive
          ? 'border-olympic-yellow bg-olympic-yellow/10'
          : 'border-transparent bg-olympic-light hover:border-olympic-border'}
      `}
    >
      <div>
        <div className="text-white text-xs font-semibold">
          {batch.batch_number} — {TIER_LABELS[batch.product_tier]}
        </div>
        {batch.colour_name && (
          <div className="text-olympic-muted text-[10px] mt-0.5">{batch.colour_name}</div>
        )}
      </div>
      <StatusPill status={batch.status} />
    </button>
  )
}
```

- [ ] **Step 3: Create `AddBatchModal.tsx`**

Create `components/tablet/AddBatchModal.tsx`:

```typescript
'use client'
import { useState } from 'react'
import { PRODUCT_TIERS, TIER_LABELS, SHIFTS, type ProductTier, type Shift } from '@/lib/constants'

interface AddBatchModalProps {
  colours: { id: string; name: string; product_tier: ProductTier }[]
  onAdd: (data: {
    batch_number: string
    product_tier: ProductTier
    colour_id: string
    shift: Shift
  }) => void
  onClose: () => void
}

export function AddBatchModal({ colours, onAdd, onClose }: AddBatchModalProps) {
  const [batchNumber, setBatchNumber] = useState('')
  const [tier, setTier] = useState<ProductTier>('decor')
  const [colourId, setColourId] = useState('')
  const [shift, setShift] = useState<Shift>('morning')

  const filteredColours = colours.filter(c => c.product_tier === tier)

  function handleSubmit() {
    if (!batchNumber || !colourId) return
    onAdd({ batch_number: batchNumber, product_tier: tier, colour_id: colourId, shift })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-olympic-mid border border-olympic-border rounded-xl p-6 w-96 flex flex-col gap-4">
        <h2 className="text-white font-bold text-base">Add New Batch</h2>

        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Batch Number</span>
          <input
            className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm"
            placeholder="#043"
            value={batchNumber}
            onChange={e => setBatchNumber(e.target.value)}
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Product Tier</span>
          <select
            className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm"
            value={tier}
            onChange={e => { setTier(e.target.value as ProductTier); setColourId('') }}
          >
            {PRODUCT_TIERS.map(t => (
              <option key={t} value={t}>{TIER_LABELS[t]}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Colour</span>
          <select
            className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm"
            value={colourId}
            onChange={e => setColourId(e.target.value)}
          >
            <option value="">Select colour…</option>
            {filteredColours.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Shift</span>
          <select
            className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm"
            value={shift}
            onChange={e => setShift(e.target.value as Shift)}
          >
            {SHIFTS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
        </label>

        <div className="flex gap-3 mt-2">
          <button onClick={onClose} className="flex-1 py-2 rounded border border-olympic-border text-olympic-muted text-sm">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!batchNumber || !colourId}
            className="flex-1 py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-40"
          >
            Add Batch
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create `BatchQueue.tsx`**

Create `components/tablet/BatchQueue.tsx`:

```typescript
'use client'
import { useState } from 'react'
import { BatchQueueItem, type BatchQueueItemData } from './BatchQueueItem'
import { AddBatchModal } from './AddBatchModal'
import type { ProductTier, Shift } from '@/lib/constants'

interface BatchQueueProps {
  batches: BatchQueueItemData[]
  activeBatchId: string | null
  onSelect: (id: string) => void
  colours: { id: string; name: string; product_tier: ProductTier }[]
  onAddBatch: (data: {
    batch_number: string
    product_tier: ProductTier
    colour_id: string
    shift: Shift
  }) => void
}

export function BatchQueue({ batches, activeBatchId, onSelect, colours, onAddBatch }: BatchQueueProps) {
  const [showAdd, setShowAdd] = useState(false)

  return (
    <div className="w-[300px] bg-olympic-mid border-r border-olympic-border flex flex-col flex-shrink-0">
      <div className="px-4 py-3 border-b border-olympic-border">
        <h3 className="text-white text-xs font-bold uppercase tracking-widest">Today's Batches</h3>
        <p className="text-olympic-muted text-[10px] mt-0.5">Tap a batch to check</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-1.5">
        {batches.map(b => (
          <BatchQueueItem
            key={b.id}
            batch={b}
            isActive={b.id === activeBatchId}
            onSelect={onSelect}
          />
        ))}
      </div>

      <button
        onClick={() => setShowAdd(true)}
        className="m-2 border-2 border-dashed border-olympic-border rounded-md py-2.5 text-olympic-muted text-xs text-center hover:border-olympic-yellow hover:text-olympic-yellow transition-colors"
      >
        + Add Batch
      </button>

      {showAdd && (
        <AddBatchModal
          colours={colours}
          onAdd={onAddBatch}
          onClose={() => setShowAdd(false)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 5: Create tablet home page**

Create `app/tablet/page.tsx`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { TabletApp } from './TabletApp'

export default async function TabletPage() {
  const supabase = await createClient()

  const [{ data: batches }, { data: colours }, { data: staff }] = await Promise.all([
    supabase
      .from('batches')
      .select('*, colours(name)')
      .gte('created_at', new Date().toISOString().split('T')[0])
      .order('created_at', { ascending: true }),
    supabase.from('colours').select('id, name, product_tier').eq('active', true),
    supabase.from('staff').select('id, name, role').eq('active', true),
  ])

  return (
    <TabletApp
      initialBatches={batches ?? []}
      colours={colours ?? []}
      staff={staff ?? []}
    />
  )
}
```

Create `app/tablet/TabletApp.tsx` (client wrapper):

```typescript
'use client'
import { useState } from 'react'
import { NavBar } from '@/components/ui/NavBar'
import { BatchQueue } from '@/components/tablet/BatchQueue'
import type { ProductTier, Shift } from '@/lib/constants'

// Minimal type — full type from supabase/types.ts
interface Batch {
  id: string
  batch_number: string
  product_tier: ProductTier
  shift: string
  colour_pass: boolean | null
  viscosity_pass: boolean | null
  first_pass: boolean | null
  checked_at: string | null
  colours?: { name: string } | null
}

interface TabletAppProps {
  initialBatches: Batch[]
  colours: { id: string; name: string; product_tier: ProductTier }[]
  staff: { id: string; name: string; role: string }[]
}

function getBatchStatus(b: Batch) {
  if (b.checked_at) return b.first_pass ? 'pass' : 'fail'
  if (b.colour_pass !== null || b.viscosity_pass !== null) return 'pending'
  return 'queued'
}

export function TabletApp({ initialBatches, colours, staff }: TabletAppProps) {
  const [batches, setBatches] = useState(initialBatches)
  const [activeBatchId, setActiveBatchId] = useState<string | null>(
    initialBatches.find(b => !b.checked_at)?.id ?? null
  )

  const now = new Date()
  const shiftLabel = `Line 1 · ${now.toLocaleDateString('en-ZA', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}`
  const timeLabel = now.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' })

  async function handleAddBatch(data: { batch_number: string; product_tier: ProductTier; colour_id: string; shift: Shift }) {
    const res = await fetch('/api/batches', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } })
    const newBatch = await res.json()
    setBatches(prev => [...prev, newBatch])
    setActiveBatchId(newBatch.id)
  }

  const queueItems = batches.map(b => ({
    id: b.id,
    batch_number: b.batch_number,
    product_tier: b.product_tier,
    colour_name: b.colours?.name,
    status: getBatchStatus(b),
    created_at: '',
  }))

  return (
    <div className="flex flex-col h-screen">
      <NavBar shift={shiftLabel} time={timeLabel} />
      <div className="flex flex-1 overflow-hidden">
        <BatchQueue
          batches={queueItems}
          activeBatchId={activeBatchId}
          onSelect={setActiveBatchId}
          colours={colours}
          onAddBatch={handleAddBatch}
        />
        <div className="flex-1 flex items-center justify-center text-olympic-muted text-sm">
          {activeBatchId ? 'Check screen coming in Task 6' : 'Select or add a batch to begin'}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Create batch POST API route**

Create `app/api/batches/route.ts`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  const supabase = await createClient()
  const body = await req.json()
  const { data, error } = await supabase
    .from('batches')
    .insert({
      batch_number: body.batch_number,
      product_tier: body.product_tier,
      colour_id: body.colour_id,
      shift: body.shift,
    })
    .select('*, colours(name)')
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
```

- [ ] **Step 7: Run the dev server and verify the queue renders**

```bash
npm run dev
```

Open http://localhost:3000/tablet in a browser at 960px wide. You should see the navy navbar, the left batch queue panel with "+ Add Batch", and a placeholder on the right.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: tablet batch queue with add-batch modal"
```

---

## Task 6: Tablet App — Check Screen

**Files:**
- Create: `components/tablet/CheckScreen.tsx`
- Create: `components/tablet/ColourCheckCard.tsx`
- Create: `components/tablet/ViscosityCard.tsx`
- Create: `components/tablet/SignOffCard.tsx`
- Modify: `app/tablet/TabletApp.tsx`

- [ ] **Step 1: Create `ColourCheckCard.tsx`**

Create `components/tablet/ColourCheckCard.tsx`:

```typescript
'use client'
import { ColourSwatch } from '@/components/ui/ColourSwatch'
import { requiresDrawdown, requiresOven, type ProductTier } from '@/lib/constants'

interface ColourCheckCardProps {
  productTier: ProductTier
  colourName: string
  hexCode: string
  colourPass: boolean | null
  colourNotes: string
  drawdownDone: boolean
  ovenDried: boolean
  onPassChange: (pass: boolean) => void
  onNotesChange: (notes: string) => void
  onDrawdownChange: (done: boolean) => void
  onOvenChange: (done: boolean) => void
}

export function ColourCheckCard({
  productTier, colourName, hexCode,
  colourPass, colourNotes,
  drawdownDone, ovenDried,
  onPassChange, onNotesChange, onDrawdownChange, onOvenChange,
}: ColourCheckCardProps) {
  const needsDrawdown = requiresDrawdown(productTier)
  const needsOven = requiresOven(productTier)
  const gateBlocked = (needsDrawdown && !drawdownDone) || (needsOven && !ovenDried)

  return (
    <div className="bg-olympic-dark p-4 flex flex-col gap-3">
      <span className="text-olympic-muted text-[10px] uppercase tracking-widest font-semibold">
        Colour Check
      </span>

      <ColourSwatch name={colourName} hexCode={hexCode} />

      {needsOven && (
        <label className="flex items-center gap-2 bg-pending/10 border border-pending/30 rounded p-2 cursor-pointer">
          <input type="checkbox" checked={ovenDried} onChange={e => onOvenChange(e.target.checked)} className="accent-pending w-4 h-4" />
          <span className="text-pending text-xs font-semibold">Oven dry complete (~5 min) ✓</span>
        </label>
      )}

      {needsDrawdown && (
        <label className="flex items-center gap-2 bg-olympic-mid border border-olympic-border rounded p-2 cursor-pointer">
          <input type="checkbox" checked={drawdownDone} onChange={e => onDrawdownChange(e.target.checked)} className="accent-olympic-yellow w-4 h-4" />
          <span className="text-white text-xs">Drawdown completed ✓</span>
        </label>
      )}

      <div className={`flex gap-2 ${gateBlocked ? 'opacity-30 pointer-events-none' : ''}`}>
        <button
          onClick={() => onPassChange(true)}
          className={`flex-1 py-3 rounded text-base font-bold transition-all ${colourPass === true ? 'bg-pass ring-2 ring-white' : 'bg-pass/50'} text-white`}
        >
          ✓ PASS
        </button>
        <button
          onClick={() => onPassChange(false)}
          className={`flex-1 py-3 rounded text-base font-bold transition-all ${colourPass === false ? 'bg-fail ring-2 ring-white' : 'bg-fail/50'} text-white`}
        >
          ✗ FAIL
        </button>
      </div>

      <textarea
        placeholder="Notes (optional)…"
        value={colourNotes}
        onChange={e => onNotesChange(e.target.value)}
        className="bg-black/40 border border-olympic-border rounded p-2 text-white text-xs resize-none h-14 placeholder:text-olympic-muted"
      />
    </div>
  )
}
```

- [ ] **Step 2: Create `ViscosityCard.tsx`**

Create `components/tablet/ViscosityCard.tsx`:

```typescript
'use client'
import { NumPad } from '@/components/ui/NumPad'

interface ViscosityCardProps {
  viscositySeconds: string
  minSeconds: number | null
  maxSeconds: number | null
  cupName: string | null
  onChange: (value: string) => void
}

export function ViscosityCard({ viscositySeconds, minSeconds, maxSeconds, cupName, onChange }: ViscosityCardProps) {
  const numVal = parseFloat(viscositySeconds)
  const inRange = !isNaN(numVal) && minSeconds !== null && maxSeconds !== null
    ? numVal >= minSeconds && numVal <= maxSeconds
    : null

  return (
    <div className="bg-olympic-dark p-4 flex flex-col gap-3">
      <span className="text-olympic-muted text-[10px] uppercase tracking-widest font-semibold">
        Viscosity {cupName ? `— ${cupName}` : ''}
      </span>

      <div className="bg-black border-2 border-olympic-border rounded px-4 py-3 font-mono text-2xl font-bold tracking-widest"
        style={{ color: inRange === null ? '#888' : inRange ? '#27AE60' : '#E74C3C' }}
      >
        {viscositySeconds || '—'} {viscositySeconds ? 'sec' : ''}
      </div>

      {minSeconds !== null && maxSeconds !== null && (
        <div className="text-[10px]" style={{ color: inRange === null ? '#888' : inRange ? '#27AE60' : '#E74C3C' }}>
          Target range: {minSeconds}–{maxSeconds} sec
          {inRange === true && ' · ✓ In range'}
          {inRange === false && ' · ✗ Out of range'}
        </div>
      )}

      <NumPad value={viscositySeconds} onChange={onChange} maxDigits={4} />
    </div>
  )
}
```

- [ ] **Step 3: Create `SignOffCard.tsx`**

Create `components/tablet/SignOffCard.tsx`:

```typescript
'use client'

interface StaffMember {
  id: string
  name: string
  role: string
}

interface SignOffCardProps {
  staff: StaffMember[]
  assistantId: string | null
  supervisorId: string | null
  onAssistantChange: (id: string) => void
  onSupervisorChange: (id: string) => void
}

export function SignOffCard({ staff, assistantId, supervisorId, onAssistantChange, onSupervisorChange }: SignOffCardProps) {
  const assistants = staff.filter(s => s.role === 'assistant')
  const supervisors = staff.filter(s => s.role === 'supervisor')

  return (
    <div className="bg-olympic-dark p-4 flex flex-col gap-3">
      <span className="text-olympic-muted text-[10px] uppercase tracking-widest font-semibold">
        Sign Off
      </span>

      <div className="flex flex-col gap-1">
        <span className="text-olympic-muted text-xs">Assistant</span>
        <div className="grid grid-cols-2 gap-1">
          {assistants.map(a => (
            <button
              key={a.id}
              onClick={() => onAssistantChange(a.id)}
              className={`py-2 px-3 rounded text-xs font-semibold transition-colors min-h-[44px] ${
                assistantId === a.id
                  ? 'bg-olympic-yellow text-olympic-black'
                  : 'bg-olympic-light text-white'
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-olympic-muted text-xs">Supervisor</span>
        <div className="grid grid-cols-2 gap-1">
          {supervisors.map(s => (
            <button
              key={s.id}
              onClick={() => onSupervisorChange(s.id)}
              className={`py-2 px-3 rounded text-xs font-semibold transition-colors min-h-[44px] ${
                supervisorId === s.id
                  ? 'bg-olympic-navy text-white'
                  : 'bg-olympic-light text-white'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create `CheckScreen.tsx`**

Create `components/tablet/CheckScreen.tsx`:

```typescript
'use client'
import { useState, useEffect } from 'react'
import { ColourCheckCard } from './ColourCheckCard'
import { ViscosityCard } from './ViscosityCard'
import { SignOffCard } from './SignOffCard'
import { requiresDrawdown, requiresOven, type ProductTier } from '@/lib/constants'

interface ViscosityTarget {
  min_seconds: number
  max_seconds: number
  ford_cups: { name: string } | null
}

interface CheckScreenProps {
  batchId: string
  batchNumber: string
  productTier: ProductTier
  colourName: string
  hexCode: string
  viscosityTarget: ViscosityTarget | null
  staff: { id: string; name: string; role: string }[]
  onSubmit: () => void
}

export function CheckScreen({
  batchId, batchNumber, productTier,
  colourName, hexCode,
  viscosityTarget, staff, onSubmit,
}: CheckScreenProps) {
  const [colourPass, setColourPass] = useState<boolean | null>(null)
  const [colourNotes, setColourNotes] = useState('')
  const [drawdownDone, setDrawdownDone] = useState(false)
  const [ovenDried, setOvenDried] = useState(false)
  const [viscositySeconds, setViscositySeconds] = useState('')
  const [assistantId, setAssistantId] = useState<string | null>(null)
  const [supervisorId, setSupervisorId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const viscNum = parseFloat(viscositySeconds)
  const viscosityPass = !isNaN(viscNum) && viscosityTarget
    ? viscNum >= viscosityTarget.min_seconds && viscNum <= viscosityTarget.max_seconds
    : null

  const canSubmit =
    colourPass !== null &&
    viscosityPass !== null &&
    assistantId !== null &&
    supervisorId !== null &&
    (!requiresDrawdown(productTier) || drawdownDone) &&
    (!requiresOven(productTier) || ovenDried)

  async function handleSubmit() {
    if (!canSubmit) return
    setSubmitting(true)
    await fetch(`/api/batches/${batchId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        colour_pass: colourPass,
        colour_notes: colourNotes,
        viscosity_seconds: parseFloat(viscositySeconds),
        viscosity_pass: viscosityPass,
        first_pass: colourPass && viscosityPass,
        assistant_id: assistantId,
        supervisor_id: supervisorId,
        drawdown_done: drawdownDone,
        oven_dried: ovenDried,
        checked_at: new Date().toISOString(),
      }),
    })
    setSubmitting(false)
    onSubmit()
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="px-5 py-3 border-b border-olympic-border flex justify-between items-start">
        <div>
          <h2 className="text-white font-bold text-base">{batchNumber} — {productTier.replace('_', ' ')}</h2>
          <p className="text-olympic-muted text-xs mt-0.5">{colourName}</p>
        </div>
        {requiresDrawdown(productTier) && (
          <span className="bg-olympic-yellow text-olympic-black text-[9px] font-bold px-2.5 py-1 rounded uppercase tracking-widest">
            Drawdown Required
          </span>
        )}
        {requiresOven(productTier) && (
          <span className="bg-pending text-white text-[9px] font-bold px-2.5 py-1 rounded uppercase tracking-widest">
            Oven Dry First
          </span>
        )}
      </div>

      <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-px bg-olympic-border overflow-hidden">
        <ColourCheckCard
          productTier={productTier}
          colourName={colourName}
          hexCode={hexCode}
          colourPass={colourPass}
          colourNotes={colourNotes}
          drawdownDone={drawdownDone}
          ovenDried={ovenDried}
          onPassChange={setColourPass}
          onNotesChange={setColourNotes}
          onDrawdownChange={setDrawdownDone}
          onOvenChange={setOvenDried}
        />
        <ViscosityCard
          viscositySeconds={viscositySeconds}
          minSeconds={viscosityTarget?.min_seconds ?? null}
          maxSeconds={viscosityTarget?.max_seconds ?? null}
          cupName={viscosityTarget?.ford_cups?.name ?? null}
          onChange={setViscositySeconds}
        />
        <SignOffCard
          staff={staff}
          assistantId={assistantId}
          supervisorId={supervisorId}
          onAssistantChange={setAssistantId}
          onSupervisorChange={setSupervisorId}
        />
        <div className="bg-olympic-dark p-4 flex flex-col justify-end">
          <div className="text-olympic-muted text-xs mb-3">
            {canSubmit ? '✓ Ready to submit' : 'Complete all checks to submit'}
          </div>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
            className="w-full py-3 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-30 transition-opacity"
          >
            {submitting ? 'Submitting…' : 'Submit Batch ›'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Create PATCH batch API route**

Create `app/api/batches/[id]/route.ts`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  const supabase = await createClient()
  const body = await req.json()
  const { data, error } = await supabase
    .from('batches')
    .update(body)
    .eq('id', params.id)
    .select('*, colours(name)')
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
```

- [ ] **Step 6: Wire `CheckScreen` into `TabletApp.tsx`**

Replace the placeholder `div` in `app/tablet/TabletApp.tsx` with:

```typescript
// Add to imports at top:
import { CheckScreen } from '@/components/tablet/CheckScreen'

// Replace the placeholder div with:
{activeBatchId ? (() => {
  const activeBatch = batches.find(b => b.id === activeBatchId)
  if (!activeBatch) return null
  // viscosityTarget would be fetched from context — placeholder for now
  return (
    <CheckScreen
      batchId={activeBatch.id}
      batchNumber={activeBatch.batch_number}
      productTier={activeBatch.product_tier}
      colourName={activeBatch.colours?.name ?? ''}
      hexCode="#888888" // will be resolved in Task 7
      viscosityTarget={null} // will be resolved in Task 7
      staff={staff}
      onSubmit={() => {
        setBatches(prev => prev.map(b =>
          b.id === activeBatchId ? { ...b, checked_at: new Date().toISOString() } : b
        ))
      }}
    />
  )
})() : (
  <div className="flex-1 flex items-center justify-center text-olympic-muted text-sm">
    Select or add a batch to begin
  </div>
)}
```

- [ ] **Step 7: Verify tablet app end-to-end in browser**

```bash
npm run dev
```

Open http://localhost:3000/tablet at 960px width. Add a batch, tap it — the check screen should open with all 4 cards. Try submitting without completing all checks — Submit button should remain disabled.

- [ ] **Step 8: Commit**

```bash
git add .
git commit -m "feat: tablet check screen — colour, viscosity, sign-off, submit"
```

---

## Task 7: Colour & Viscosity Data Wiring

**Files:**
- Modify: `app/tablet/page.tsx`
- Modify: `app/tablet/TabletApp.tsx`

- [ ] **Step 1: Fetch colour hex codes and viscosity targets in the page**

Replace `app/tablet/page.tsx`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { TabletApp } from './TabletApp'

export default async function TabletPage() {
  const supabase = await createClient()

  const [
    { data: batches },
    { data: colours },
    { data: staff },
    { data: viscosityTargets },
  ] = await Promise.all([
    supabase
      .from('batches')
      .select('*, colours(name, hex_code)')
      .gte('created_at', new Date().toISOString().split('T')[0])
      .order('created_at', { ascending: true }),
    supabase.from('colours').select('id, name, hex_code, product_tier').eq('active', true),
    supabase.from('staff').select('id, name, role').eq('active', true),
    supabase.from('viscosity_targets').select('*, ford_cups(name)'),
  ])

  return (
    <TabletApp
      initialBatches={batches ?? []}
      colours={colours ?? []}
      staff={staff ?? []}
      viscosityTargets={viscosityTargets ?? []}
    />
  )
}
```

- [ ] **Step 2: Update `TabletApp.tsx` to wire colour hex and viscosity targets**

In `app/tablet/TabletApp.tsx`, update the props interface and the CheckScreen rendering:

```typescript
// Add viscosityTargets to props interface:
interface TabletAppProps {
  initialBatches: Batch[]
  colours: { id: string; name: string; hex_code: string; product_tier: ProductTier }[]
  staff: { id: string; name: string; role: string }[]
  viscosityTargets: {
    product_tier: string
    min_seconds: number
    max_seconds: number
    ford_cups: { name: string } | null
  }[]
}

// In TabletApp component, resolve hex and viscosityTarget for the active batch:
const activeBatch = batches.find(b => b.id === activeBatchId)
const activeColour = activeBatch
  ? colours.find(c => c.id === activeBatch.colour_id)
  : null
const activeViscosityTarget = activeBatch
  ? viscosityTargets.find(t => t.product_tier === activeBatch.product_tier) ?? null
  : null

// Pass to CheckScreen:
hexCode={activeColour?.hex_code ?? '#888888'}
viscosityTarget={activeViscosityTarget}
```

- [ ] **Step 3: Verify colour swatch and viscosity range appear correctly**

```bash
npm run dev
```

Open /tablet, add a batch with a colour that has a hex code in the DB. Open the check screen — the colour swatch should show the real colour. If viscosity targets are configured in the DB, the range label should appear.

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: wire colour hex and viscosity targets into check screen"
```

---

## Task 8: Admin Panel

**Files:**
- Create: `app/admin/layout.tsx`
- Create: `app/admin/page.tsx`
- Create: `components/admin/PinGate.tsx`
- Create: `components/admin/AdminTable.tsx`
- Create: `components/admin/AdminForm.tsx`
- Create: `app/admin/ford-cups/page.tsx`
- Create: `app/admin/viscosity-targets/page.tsx`
- Create: `app/admin/colours/page.tsx`
- Create: `app/admin/staff/page.tsx`
- Create: `app/admin/kpi/page.tsx`
- Create: `app/api/admin/[table]/route.ts`

- [ ] **Step 1: Create the PIN gate component**

Create `components/admin/PinGate.tsx`:

```typescript
'use client'
import { useState } from 'react'

const CORRECT_PIN = process.env.NEXT_PUBLIC_ADMIN_PIN ?? '1234'

interface PinGateProps {
  onUnlock: () => void
}

export function PinGate({ onUnlock }: PinGateProps) {
  const [pin, setPin] = useState('')
  const [error, setError] = useState(false)

  function handleKey(key: string) {
    if (key === '⌫') { setPin(p => p.slice(0, -1)); return }
    if (pin.length >= 4) return
    const next = pin + key
    setPin(next)
    if (next.length === 4) {
      if (next === CORRECT_PIN) { onUnlock() }
      else { setError(true); setTimeout(() => { setPin(''); setError(false) }, 800) }
    }
  }

  const keys = ['1','2','3','4','5','6','7','8','9','⌫','0','✓']

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6">
      <div className="text-olympic-muted text-xs uppercase tracking-widest">Admin PIN</div>
      <div className="flex gap-3">
        {[0,1,2,3].map(i => (
          <div key={i} className={`w-4 h-4 rounded-full border-2 transition-colors ${
            error ? 'border-fail bg-fail' : pin.length > i ? 'border-olympic-yellow bg-olympic-yellow' : 'border-olympic-border'
          }`} />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 w-48">
        {keys.map(key => (
          <button
            key={key}
            onClick={() => handleKey(key)}
            className="bg-olympic-mid border border-olympic-border rounded-lg py-3 text-white font-bold text-lg min-h-[44px] active:opacity-70"
          >
            {key}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create admin layout with PIN gate**

Create `app/admin/layout.tsx`:

```typescript
'use client'
import { useState } from 'react'
import { PinGate } from '@/components/admin/PinGate'
import { NavBar } from '@/components/ui/NavBar'
import Link from 'next/link'

const NAV_LINKS = [
  { href: '/admin/ford-cups',          label: 'Ford Cups' },
  { href: '/admin/viscosity-targets',  label: 'Viscosity' },
  { href: '/admin/colours',            label: 'Colours' },
  { href: '/admin/staff',              label: 'Staff' },
  { href: '/admin/kpi',                label: 'KPI Config' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const [unlocked, setUnlocked] = useState(false)

  if (!unlocked) return <PinGate onUnlock={() => setUnlocked(true)} />

  return (
    <div className="flex flex-col min-h-screen">
      <NavBar shift="Admin Panel" />
      <div className="flex flex-1">
        <nav className="w-48 bg-olympic-mid border-r border-olympic-border p-4 flex flex-col gap-1">
          {NAV_LINKS.map(l => (
            <Link key={l.href} href={l.href}
              className="text-olympic-muted text-sm py-2 px-3 rounded hover:bg-olympic-light hover:text-white transition-colors"
            >
              {l.label}
            </Link>
          ))}
          <Link href="/tablet" className="mt-auto text-olympic-muted text-xs py-2 px-3">
            ← Back to tablet
          </Link>
        </nav>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create reusable `AdminTable.tsx`**

Create `components/admin/AdminTable.tsx`:

```typescript
interface Column<T> {
  key: keyof T | string
  label: string
  render?: (row: T) => React.ReactNode
}

interface AdminTableProps<T extends { id: string; active?: boolean }> {
  columns: Column<T>[]
  rows: T[]
  onEdit: (row: T) => void
  onToggleActive: (id: string, active: boolean) => void
}

export function AdminTable<T extends { id: string; active?: boolean }>({
  columns, rows, onEdit, onToggleActive,
}: AdminTableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-olympic-border">
            {columns.map(c => (
              <th key={String(c.key)} className="text-left text-olympic-muted text-xs uppercase tracking-widest py-2 px-3">
                {c.label}
              </th>
            ))}
            <th className="text-left text-olympic-muted text-xs uppercase tracking-widest py-2 px-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.id} className={`border-b border-olympic-border/50 ${!row.active ? 'opacity-40' : ''}`}>
              {columns.map(c => (
                <td key={String(c.key)} className="py-2 px-3 text-white">
                  {c.render ? c.render(row) : String((row as any)[c.key] ?? '')}
                </td>
              ))}
              <td className="py-2 px-3 flex gap-2">
                <button onClick={() => onEdit(row)} className="text-xs text-olympic-yellow hover:underline">Edit</button>
                <button
                  onClick={() => onToggleActive(row.id, !row.active)}
                  className="text-xs text-olympic-muted hover:underline"
                >
                  {row.active ? 'Deactivate' : 'Activate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 4: Create generic admin API route**

Create `app/api/admin/[table]/route.ts`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

const ALLOWED_TABLES = ['ford_cups', 'viscosity_targets', 'colours', 'staff', 'kpi_config'] as const
type AllowedTable = typeof ALLOWED_TABLES[number]

export async function GET(req: Request, { params }: { params: { table: string } }) {
  if (!ALLOWED_TABLES.includes(params.table as AllowedTable))
    return NextResponse.json({ error: 'Not allowed' }, { status: 403 })
  const supabase = await createClient()
  const { data, error } = await supabase.from(params.table as AllowedTable).select('*').order('created_at', { ascending: false })
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(req: Request, { params }: { params: { table: string } }) {
  if (!ALLOWED_TABLES.includes(params.table as AllowedTable))
    return NextResponse.json({ error: 'Not allowed' }, { status: 403 })
  const supabase = await createClient()
  const body = await req.json()
  const { data, error } = await supabase.from(params.table as AllowedTable).insert(body).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function PATCH(req: Request, { params }: { params: { table: string } }) {
  if (!ALLOWED_TABLES.includes(params.table as AllowedTable))
    return NextResponse.json({ error: 'Not allowed' }, { status: 403 })
  const supabase = await createClient()
  const body = await req.json()
  const { id, ...updates } = body
  const { data, error } = await supabase.from(params.table as AllowedTable).update({ ...updates, updated_at: new Date().toISOString() }).eq('id', id).select().single()
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
```

- [ ] **Step 5: Create Ford Cups admin page**

Create `app/admin/ford-cups/page.tsx`:

```typescript
'use client'
import { useEffect, useState } from 'react'
import { AdminTable } from '@/components/admin/AdminTable'

interface FordCup { id: string; name: string; orifice_mm: number | null; notes: string | null; active: boolean }

export default function FordCupsPage() {
  const [cups, setCups] = useState<FordCup[]>([])
  const [name, setName] = useState(''); const [orifice, setOrifice] = useState(''); const [notes, setNotes] = useState('')
  const [editId, setEditId] = useState<string | null>(null)

  useEffect(() => { fetch('/api/admin/ford_cups').then(r => r.json()).then(setCups) }, [])

  async function handleSave() {
    const method = editId ? 'PATCH' : 'POST'
    const body = editId ? { id: editId, name, orifice_mm: orifice ? parseFloat(orifice) : null, notes } : { name, orifice_mm: orifice ? parseFloat(orifice) : null, notes }
    const res = await fetch('/api/admin/ford_cups', { method, body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } })
    const saved = await res.json()
    setCups(prev => editId ? prev.map(c => c.id === editId ? saved : c) : [saved, ...prev])
    setName(''); setOrifice(''); setNotes(''); setEditId(null)
  }

  async function handleToggle(id: string, active: boolean) {
    await fetch('/api/admin/ford_cups', { method: 'PATCH', body: JSON.stringify({ id, active }), headers: { 'Content-Type': 'application/json' } })
    setCups(prev => prev.map(c => c.id === id ? { ...c, active } : c))
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-white font-bold text-lg">Ford Cup Configuration</h1>
      <div className="bg-olympic-mid border border-olympic-border rounded-lg p-4 flex flex-col gap-3 max-w-md">
        <h2 className="text-white text-sm font-semibold">{editId ? 'Edit Cup' : 'Add Cup'}</h2>
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Name (e.g. Ford Cup #4)" value={name} onChange={e => setName(e.target.value)} />
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Orifice (mm)" value={orifice} onChange={e => setOrifice(e.target.value)} type="number" />
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Notes (optional)" value={notes} onChange={e => setNotes(e.target.value)} />
        <button onClick={handleSave} disabled={!name} className="py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-40">
          {editId ? 'Save Changes' : 'Add Cup'}
        </button>
      </div>
      <AdminTable
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'orifice_mm', label: 'Orifice (mm)' },
          { key: 'notes', label: 'Notes' },
        ]}
        rows={cups}
        onEdit={row => { setEditId(row.id); setName(row.name); setOrifice(String(row.orifice_mm ?? '')); setNotes(row.notes ?? '') }}
        onToggleActive={handleToggle}
      />
    </div>
  )
}
```

- [ ] **Step 6: Create remaining admin pages (Viscosity, Colours, Staff, KPI)**

Create `app/admin/viscosity-targets/page.tsx`:

```typescript
'use client'
import { useEffect, useState } from 'react'
import { AdminTable } from '@/components/admin/AdminTable'
import { PRODUCT_TIERS, TIER_LABELS } from '@/lib/constants'

interface ViscosityTarget { id: string; product_tier: string; ford_cup_id: string; min_seconds: number; max_seconds: number; notes: string | null; active: boolean; updated_at: string }
interface FordCup { id: string; name: string }

export default function ViscosityTargetsPage() {
  const [targets, setTargets] = useState<ViscosityTarget[]>([])
  const [cups, setCups] = useState<FordCup[]>([])
  const [tier, setTier] = useState(PRODUCT_TIERS[0])
  const [cupId, setCupId] = useState('')
  const [min, setMin] = useState(''); const [max, setMax] = useState(''); const [notes, setNotes] = useState('')
  const [editId, setEditId] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/admin/viscosity_targets').then(r => r.json()).then(setTargets)
    fetch('/api/admin/ford_cups').then(r => r.json()).then(d => { setCups(d.filter((c: any) => c.active)); if (d.length) setCupId(d[0].id) })
  }, [])

  async function handleSave() {
    const body = { ...(editId ? { id: editId } : {}), product_tier: tier, ford_cup_id: cupId, min_seconds: parseFloat(min), max_seconds: parseFloat(max), notes, updated_at: new Date().toISOString() }
    const res = await fetch('/api/admin/viscosity_targets', { method: editId ? 'PATCH' : 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } })
    const saved = await res.json()
    setTargets(prev => editId ? prev.map(t => t.id === editId ? saved : t) : [saved, ...prev])
    setMin(''); setMax(''); setNotes(''); setEditId(null)
  }

  async function handleToggle(id: string, active: boolean) {
    await fetch('/api/admin/viscosity_targets', { method: 'PATCH', body: JSON.stringify({ id, active }), headers: { 'Content-Type': 'application/json' } })
    setTargets(prev => prev.map(t => t.id === id ? { ...t, active } : t))
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-white font-bold text-lg">Viscosity Targets</h1>
      <div className="bg-olympic-mid border border-olympic-border rounded-lg p-4 flex flex-col gap-3 max-w-md">
        <h2 className="text-white text-sm font-semibold">{editId ? 'Edit Target' : 'Add Target'}</h2>
        <select className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" value={tier} onChange={e => setTier(e.target.value as any)}>
          {PRODUCT_TIERS.map(t => <option key={t} value={t}>{TIER_LABELS[t]}</option>)}
        </select>
        <select className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" value={cupId} onChange={e => setCupId(e.target.value)}>
          {cups.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div className="flex gap-2">
          <input className="flex-1 bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Min sec" value={min} onChange={e => setMin(e.target.value)} type="number" />
          <input className="flex-1 bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Max sec" value={max} onChange={e => setMax(e.target.value)} type="number" />
        </div>
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Notes (e.g. Measure at 23°C)" value={notes} onChange={e => setNotes(e.target.value)} />
        <button onClick={handleSave} disabled={!min || !max || !cupId} className="py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-40">
          {editId ? 'Save Changes' : 'Add Target'}
        </button>
      </div>
      <AdminTable
        columns={[
          { key: 'product_tier', label: 'Tier', render: r => TIER_LABELS[r.product_tier as any] },
          { key: 'min_seconds', label: 'Min (sec)' },
          { key: 'max_seconds', label: 'Max (sec)' },
          { key: 'notes', label: 'Notes' },
          { key: 'updated_at', label: 'Last Updated', render: r => new Date(r.updated_at).toLocaleDateString('en-ZA') },
        ]}
        rows={targets}
        onEdit={row => { setEditId(row.id); setTier(row.product_tier as any); setCupId(row.ford_cup_id); setMin(String(row.min_seconds)); setMax(String(row.max_seconds)); setNotes(row.notes ?? '') }}
        onToggleActive={handleToggle}
      />
    </div>
  )
}
```

Create `app/admin/colours/page.tsx`:

```typescript
'use client'
import { useEffect, useState } from 'react'
import { AdminTable } from '@/components/admin/AdminTable'
import { PRODUCT_TIERS, TIER_LABELS, type ProductTier } from '@/lib/constants'

interface Colour { id: string; name: string; hex_code: string; product_tier: ProductTier; range_code: string | null; active: boolean }

export default function ColoursPage() {
  const [colours, setColours] = useState<Colour[]>([])
  const [name, setName] = useState(''); const [hex, setHex] = useState('#'); const [tier, setTier] = useState<ProductTier>('decor'); const [rangeCode, setRangeCode] = useState(''); const [editId, setEditId] = useState<string | null>(null)

  useEffect(() => { fetch('/api/admin/colours').then(r => r.json()).then(setColours) }, [])

  async function handleSave() {
    const body = { ...(editId ? { id: editId } : {}), name, hex_code: hex, product_tier: tier, range_code: rangeCode || null }
    const res = await fetch('/api/admin/colours', { method: editId ? 'PATCH' : 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } })
    const saved = await res.json()
    setColours(prev => editId ? prev.map(c => c.id === editId ? saved : c) : [saved, ...prev])
    setName(''); setHex('#'); setRangeCode(''); setEditId(null)
  }

  async function handleToggle(id: string, active: boolean) {
    await fetch('/api/admin/colours', { method: 'PATCH', body: JSON.stringify({ id, active }), headers: { 'Content-Type': 'application/json' } })
    setColours(prev => prev.map(c => c.id === id ? { ...c, active } : c))
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-white font-bold text-lg">Colour Library</h1>
      <div className="bg-olympic-mid border border-olympic-border rounded-lg p-4 flex flex-col gap-3 max-w-md">
        <h2 className="text-white text-sm font-semibold">{editId ? 'Edit Colour' : 'Add Colour'}</h2>
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Colour name" value={name} onChange={e => setName(e.target.value)} />
        <div className="flex gap-2 items-center">
          <input className="flex-1 bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm font-mono" placeholder="#C4843E" value={hex} onChange={e => setHex(e.target.value)} />
          <div className="w-10 h-10 rounded border-2 border-olympic-border flex-shrink-0" style={{ background: hex }} />
        </div>
        <select className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" value={tier} onChange={e => setTier(e.target.value as ProductTier)}>
          {PRODUCT_TIERS.map(t => <option key={t} value={t}>{TIER_LABELS[t]}</option>)}
        </select>
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Range code (optional)" value={rangeCode} onChange={e => setRangeCode(e.target.value)} />
        <button onClick={handleSave} disabled={!name || !hex} className="py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-40">
          {editId ? 'Save Changes' : 'Add Colour'}
        </button>
      </div>
      <AdminTable
        columns={[
          { key: 'hex_code', label: 'Swatch', render: r => <div className="w-6 h-6 rounded" style={{ background: r.hex_code }} /> },
          { key: 'name', label: 'Name' },
          { key: 'hex_code', label: 'Hex' },
          { key: 'product_tier', label: 'Tier', render: r => TIER_LABELS[r.product_tier] },
          { key: 'range_code', label: 'Range Code' },
        ]}
        rows={colours}
        onEdit={row => { setEditId(row.id); setName(row.name); setHex(row.hex_code); setTier(row.product_tier); setRangeCode(row.range_code ?? '') }}
        onToggleActive={handleToggle}
      />
    </div>
  )
}
```

Create `app/admin/staff/page.tsx`:

```typescript
'use client'
import { useEffect, useState } from 'react'
import { AdminTable } from '@/components/admin/AdminTable'

interface StaffMember { id: string; name: string; role: string; active: boolean }

export default function StaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [name, setName] = useState(''); const [role, setRole] = useState<'assistant' | 'supervisor'>('assistant'); const [editId, setEditId] = useState<string | null>(null)

  useEffect(() => { fetch('/api/admin/staff').then(r => r.json()).then(setStaff) }, [])

  async function handleSave() {
    const body = { ...(editId ? { id: editId } : {}), name, role }
    const res = await fetch('/api/admin/staff', { method: editId ? 'PATCH' : 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } })
    const saved = await res.json()
    setStaff(prev => editId ? prev.map(s => s.id === editId ? saved : s) : [saved, ...prev])
    setName(''); setEditId(null)
  }

  async function handleToggle(id: string, active: boolean) {
    await fetch('/api/admin/staff', { method: 'PATCH', body: JSON.stringify({ id, active }), headers: { 'Content-Type': 'application/json' } })
    setStaff(prev => prev.map(s => s.id === id ? { ...s, active } : s))
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-white font-bold text-lg">Staff Roster</h1>
      <p className="text-olympic-muted text-sm">4 assistants + 4 supervisors. Names appear in tap-to-select lists on the tablet.</p>
      <div className="bg-olympic-mid border border-olympic-border rounded-lg p-4 flex flex-col gap-3 max-w-md">
        <h2 className="text-white text-sm font-semibold">{editId ? 'Edit Staff Member' : 'Add Staff Member'}</h2>
        <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
        <div className="flex gap-2">
          {(['assistant', 'supervisor'] as const).map(r => (
            <button key={r} onClick={() => setRole(r)} className={`flex-1 py-2 rounded text-sm font-semibold capitalize ${role === r ? 'bg-olympic-yellow text-olympic-black' : 'bg-olympic-light text-white'}`}>{r}</button>
          ))}
        </div>
        <button onClick={handleSave} disabled={!name} className="py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm disabled:opacity-40">
          {editId ? 'Save Changes' : 'Add Staff Member'}
        </button>
      </div>
      <AdminTable
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'role', label: 'Role', render: r => <span className="capitalize">{r.role}</span> },
        ]}
        rows={staff}
        onEdit={row => { setEditId(row.id); setName(row.name); setRole(row.role as any) }}
        onToggleActive={handleToggle}
      />
    </div>
  )
}
```

Create `app/admin/kpi/page.tsx`:

```typescript
'use client'
import { useEffect, useState } from 'react'

export default function KpiConfigPage() {
  const [baseline, setBaseline] = useState('82')
  const [goal, setGoal] = useState('92')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetch('/api/admin/kpi_config').then(r => r.json()).then((rows: { key: string; value: number }[]) => {
      rows.forEach(r => { if (r.key === 'baseline') setBaseline(String(r.value)); if (r.key === 'goal') setGoal(String(r.value)) })
    })
  }, [])

  async function handleSave() {
    await Promise.all([
      fetch('/api/admin/kpi_config', { method: 'PATCH', body: JSON.stringify({ key: 'baseline', value: parseFloat(baseline) }), headers: { 'Content-Type': 'application/json' } }),
      fetch('/api/admin/kpi_config', { method: 'PATCH', body: JSON.stringify({ key: 'goal', value: parseFloat(goal) }), headers: { 'Content-Type': 'application/json' } }),
    ])
    setSaved(true); setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="flex flex-col gap-6 max-w-md">
      <h1 className="text-white font-bold text-lg">KPI Reference Values</h1>
      <p className="text-olympic-muted text-sm">Used in the supervisor dashboard traffic-light display for the first-pass quality rate.</p>
      <div className="bg-olympic-mid border border-olympic-border rounded-lg p-4 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Baseline (%)</span>
          <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" type="number" value={baseline} onChange={e => setBaseline(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-olympic-muted text-xs uppercase tracking-widest">Goal (%)</span>
          <input className="bg-olympic-dark border border-olympic-border rounded px-3 py-2 text-white text-sm" type="number" value={goal} onChange={e => setGoal(e.target.value)} />
        </label>
        <button onClick={handleSave} className="py-2 rounded bg-olympic-yellow text-olympic-black font-bold text-sm">
          {saved ? '✓ Saved' : 'Save Values'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 7: Update PATCH in admin API to support kpi_config key-based update**

In `app/api/admin/[table]/route.ts`, update the PATCH handler to support `kpi_config` updates by `key` instead of `id`:

```typescript
export async function PATCH(req: Request, { params }: { params: { table: string } }) {
  if (!ALLOWED_TABLES.includes(params.table as AllowedTable))
    return NextResponse.json({ error: 'Not allowed' }, { status: 403 })
  const supabase = await createClient()
  const body = await req.json()
  const updates: any = { ...body, updated_at: new Date().toISOString() }

  // kpi_config uses 'key' as the lookup, not 'id'
  const lookupField = params.table === 'kpi_config' ? 'key' : 'id'
  const lookupValue = params.table === 'kpi_config' ? body.key : body.id
  delete updates[lookupField]

  const { data, error } = await supabase
    .from(params.table as AllowedTable)
    .update(updates)
    .eq(lookupField, lookupValue)
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
```

- [ ] **Step 8: Create admin home page**

Create `app/admin/page.tsx`:

```typescript
import Link from 'next/link'

const sections = [
  { href: '/admin/ford-cups',         label: 'Ford Cups',         desc: 'Configure cup types and orifice sizes' },
  { href: '/admin/viscosity-targets',  label: 'Viscosity Targets', desc: 'Set min/max seconds per product tier' },
  { href: '/admin/colours',            label: 'Colour Library',    desc: 'Add and manage Olympic colour references' },
  { href: '/admin/staff',              label: 'Staff Roster',      desc: 'Manage assistants and supervisors' },
  { href: '/admin/kpi',                label: 'KPI Config',        desc: 'Set baseline and goal for the scoreboard' },
]

export default function AdminHome() {
  return (
    <div className="flex flex-col gap-4 max-w-xl">
      <h1 className="text-white font-bold text-lg">Admin Panel</h1>
      {sections.map(s => (
        <Link key={s.href} href={s.href} className="bg-olympic-mid border border-olympic-border rounded-lg p-4 hover:border-olympic-yellow transition-colors">
          <div className="text-white font-semibold text-sm">{s.label}</div>
          <div className="text-olympic-muted text-xs mt-0.5">{s.desc}</div>
        </Link>
      ))}
    </div>
  )
}
```

- [ ] **Step 9: Test admin panel end-to-end**

```bash
npm run dev
```

Navigate to http://localhost:3000/admin. Enter PIN (default `1234` until `.env.local` is configured). Verify:
- All 5 sections load
- Add a Ford Cup → appears in table
- Add a viscosity target with that cup → appears in table
- Add a colour → hex swatch preview shows in the form
- Add 4 staff members (2 assistant, 2 supervisor)
- Update KPI baseline/goal → saved confirmation appears

- [ ] **Step 10: Commit**

```bash
git add .
git commit -m "feat: admin panel — ford cups, viscosity targets, colours, staff, KPI config"
```

---

## Task 9: Supervisor Dashboard

**Files:**
- Create: `app/dashboard/page.tsx`
- Create: `components/dashboard/KpiRateCard.tsx`
- Create: `components/dashboard/BatchTable.tsx`
- Create: `components/dashboard/ExportButton.tsx`

- [ ] **Step 1: Create `KpiRateCard.tsx`**

Create `components/dashboard/KpiRateCard.tsx`:

```typescript
import { calcFirstPassRate, getTrafficLight } from '@/lib/kpi'

interface KpiRateCardProps {
  passed: number
  total: number
  baseline: number
  goal: number
  label: string
}

const LIGHT_COLOURS = { green: '#27AE60', amber: '#F39C12', red: '#E74C3C' }
const LIGHT_LABELS = { green: '↑ On track', amber: '→ Improving', red: '↓ Below baseline' }

export function KpiRateCard({ passed, total, baseline, goal, label }: KpiRateCardProps) {
  const rate = calcFirstPassRate(passed, total)
  const light = getTrafficLight(rate, baseline, goal)

  return (
    <div className="bg-olympic-mid border border-olympic-border rounded-xl p-5 flex flex-col gap-2">
      <span className="text-olympic-muted text-xs uppercase tracking-widest">{label}</span>
      <div className="flex items-end gap-3">
        <span className="text-white text-4xl font-black">
          {rate !== null ? `${rate}%` : '—'}
        </span>
        <span className="text-olympic-muted text-sm mb-1">{total} batches</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full" style={{ background: LIGHT_COLOURS[light] }} />
        <span className="text-xs" style={{ color: LIGHT_COLOURS[light] }}>{LIGHT_LABELS[light]}</span>
      </div>
      <div className="text-olympic-muted text-xs mt-1">
        Baseline: {baseline}% · Goal: {goal}%
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create `ExportButton.tsx`**

Create `components/dashboard/ExportButton.tsx`:

```typescript
'use client'

interface Batch {
  batch_number: string
  product_tier: string
  shift: string
  colour_pass: boolean | null
  colour_notes: string | null
  viscosity_seconds: number | null
  viscosity_pass: boolean | null
  first_pass: boolean | null
  checked_at: string | null
  colours?: { name: string } | null
  assistant?: { name: string } | null
  supervisor?: { name: string } | null
}

export function ExportButton({ batches }: { batches: Batch[] }) {
  function handleExport() {
    const headers = ['Batch','Product','Colour','Shift','Colour Pass','Viscosity (sec)','Viscosity Pass','First Pass','Checked At','Assistant','Supervisor','Notes']
    const rows = batches.map(b => [
      b.batch_number, b.product_tier, b.colours?.name ?? '', b.shift,
      b.colour_pass === null ? '' : b.colour_pass ? 'PASS' : 'FAIL',
      b.viscosity_seconds ?? '',
      b.viscosity_pass === null ? '' : b.viscosity_pass ? 'PASS' : 'FAIL',
      b.first_pass === null ? '' : b.first_pass ? 'PASS' : 'FAIL',
      b.checked_at ? new Date(b.checked_at).toLocaleString('en-ZA') : '',
      b.assistant?.name ?? '', b.supervisor?.name ?? '',
      b.colour_notes ?? '',
    ])
    const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `quality-${new Date().toISOString().split('T')[0]}.csv`
    a.click(); URL.revokeObjectURL(url)
  }

  return (
    <button onClick={handleExport} className="px-4 py-2 rounded border border-olympic-border text-olympic-muted text-sm hover:border-olympic-yellow hover:text-olympic-yellow transition-colors">
      Export CSV
    </button>
  )
}
```

- [ ] **Step 3: Create `BatchTable.tsx`**

Create `components/dashboard/BatchTable.tsx`:

```typescript
'use client'
import { useState } from 'react'
import { StatusPill } from '@/components/ui/StatusPill'
import { TIER_LABELS, type ProductTier } from '@/lib/constants'

interface Batch {
  id: string
  batch_number: string
  product_tier: ProductTier
  shift: string
  colour_pass: boolean | null
  colour_notes: string | null
  viscosity_seconds: number | null
  viscosity_pass: boolean | null
  first_pass: boolean | null
  checked_at: string | null
  colours?: { name: string } | null
  assistant?: { name: string } | null
  supervisor?: { name: string } | null
}

export function BatchTable({ batches }: { batches: Batch[] }) {
  const [filterTier, setFilterTier] = useState('')
  const [filterResult, setFilterResult] = useState('')

  const filtered = batches.filter(b => {
    if (filterTier && b.product_tier !== filterTier) return false
    if (filterResult === 'pass' && !b.first_pass) return false
    if (filterResult === 'fail' && b.first_pass !== false) return false
    if (filterResult === 'pending' && b.checked_at) return false
    return true
  })

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        <select className="bg-olympic-mid border border-olympic-border rounded px-3 py-1.5 text-white text-xs" value={filterTier} onChange={e => setFilterTier(e.target.value)}>
          <option value="">All tiers</option>
          {Object.entries(TIER_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="bg-olympic-mid border border-olympic-border rounded px-3 py-1.5 text-white text-xs" value={filterResult} onChange={e => setFilterResult(e.target.value)}>
          <option value="">All results</option>
          <option value="pass">Pass</option>
          <option value="fail">Fail</option>
          <option value="pending">Pending</option>
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="border-b border-olympic-border">
              {['Batch','Product','Colour','Shift','Colour','Viscosity','First Pass','Time','Assistant','Supervisor'].map(h => (
                <th key={h} className="text-left text-olympic-muted uppercase tracking-widest py-2 px-2 text-[10px]">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(b => (
              <tr key={b.id} className="border-b border-olympic-border/30 hover:bg-olympic-mid/50">
                <td className="py-2 px-2 text-white font-mono">{b.batch_number}</td>
                <td className="py-2 px-2 text-white">{TIER_LABELS[b.product_tier]}</td>
                <td className="py-2 px-2 text-olympic-muted">{b.colours?.name ?? '—'}</td>
                <td className="py-2 px-2 text-olympic-muted capitalize">{b.shift}</td>
                <td className="py-2 px-2"><StatusPill status={b.colour_pass === null ? 'queued' : b.colour_pass ? 'pass' : 'fail'} /></td>
                <td className="py-2 px-2">
                  {b.viscosity_seconds != null ? (
                    <span style={{ color: b.viscosity_pass ? '#27AE60' : '#E74C3C' }}>{b.viscosity_seconds}s</span>
                  ) : '—'}
                </td>
                <td className="py-2 px-2"><StatusPill status={b.first_pass === null ? (b.checked_at ? 'fail' : 'queued') : b.first_pass ? 'pass' : 'fail'} /></td>
                <td className="py-2 px-2 text-olympic-muted">{b.checked_at ? new Date(b.checked_at).toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                <td className="py-2 px-2 text-olympic-muted">{b.assistant?.name ?? '—'}</td>
                <td className="py-2 px-2 text-olympic-muted">{b.supervisor?.name ?? '—'}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={10} className="py-6 text-center text-olympic-muted text-xs">No batches match the current filter</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create dashboard page**

Create `app/dashboard/page.tsx`:

```typescript
import { createClient } from '@/lib/supabase/server'
import { KpiRateCard } from '@/components/dashboard/KpiRateCard'
import { BatchTable } from '@/components/dashboard/BatchTable'
import { ExportButton } from '@/components/dashboard/ExportButton'
import { NavBar } from '@/components/ui/NavBar'

export default async function DashboardPage() {
  const supabase = await createClient()
  const today = new Date().toISOString().split('T')[0]
  const firstOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString()

  const [{ data: todayBatches }, { data: monthBatches }, { data: kpiConfig }] = await Promise.all([
    supabase
      .from('batches')
      .select('*, colours(name), assistant:staff!assistant_id(name), supervisor:staff!supervisor_id(name)')
      .gte('created_at', today)
      .order('created_at', { ascending: false }),
    supabase
      .from('batches')
      .select('first_pass, checked_at')
      .gte('created_at', firstOfMonth)
      .not('checked_at', 'is', null),
    supabase.from('kpi_config').select('key, value'),
  ])

  const baseline = kpiConfig?.find(k => k.key === 'baseline')?.value ?? 82
  const goal = kpiConfig?.find(k => k.key === 'goal')?.value ?? 92

  const todayChecked = (todayBatches ?? []).filter(b => b.checked_at)
  const todayPassed = todayChecked.filter(b => b.first_pass).length
  const monthChecked = (monthBatches ?? []).length
  const monthPassed = (monthBatches ?? []).filter(b => b.first_pass).length

  return (
    <div className="flex flex-col min-h-screen bg-olympic-black">
      <NavBar shift="Supervisor Dashboard" />
      <main className="p-6 flex flex-col gap-6 max-w-6xl mx-auto w-full">
        <div className="flex items-center justify-between">
          <h1 className="text-white font-bold text-xl">Quality Dashboard</h1>
          <ExportButton batches={todayBatches ?? []} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <KpiRateCard
            passed={todayPassed}
            total={todayChecked.length}
            baseline={baseline}
            goal={goal}
            label="Today's First-Pass Rate"
          />
          <KpiRateCard
            passed={monthPassed}
            total={monthChecked}
            baseline={baseline}
            goal={goal}
            label="This Month's First-Pass Rate"
          />
        </div>

        <div className="bg-olympic-mid border border-olympic-border rounded-xl p-5">
          <h2 className="text-white font-semibold text-sm mb-4">Today's Batches</h2>
          <BatchTable batches={todayBatches ?? []} />
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 5: Run all tests and verify dashboard**

```bash
npx vitest run
npm run dev
```

Open http://localhost:3000/dashboard. Verify:
- KPI rate cards show today's and monthly rates
- Traffic light shows green/amber/red correctly
- Batch table filters work
- Export CSV downloads a file with correct headers

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: supervisor dashboard — KPI rate cards, batch table, CSV export"
```

---

## Task 10: Deploy to Vercel

**Files:**
- Create: `.env.local` (from `.env.local.example`, not committed)
- Modify: `next.config.ts` (add ADMIN_PIN_HASH env)

- [ ] **Step 1: Push to GitHub**

```bash
git remote add origin https://github.com/YOUR_ORG/olympic-quality-capture.git
git push -u origin main
```

- [ ] **Step 2: Create Vercel project**

Go to https://vercel.com → Import repository → `olympic-quality-capture`.

- [ ] **Step 3: Set environment variables in Vercel**

In Vercel project settings → Environment Variables, add:

```
NEXT_PUBLIC_SUPABASE_URL         = https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY    = your-anon-key
NEXT_PUBLIC_ADMIN_PIN            = your-4-digit-pin
```

- [ ] **Step 4: Deploy**

```bash
# Vercel auto-deploys on push. Or manually:
npx vercel --prod
```

- [ ] **Step 5: Verify production deployment**

Open the Vercel URL on a 10-inch tablet in landscape mode. Verify:
- `/tablet` loads and is usable with touch
- `/admin` PIN gate works
- `/dashboard` shows correct data
- PWA "Add to Home Screen" prompt appears on Android tablet

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "chore: deployment config and env documentation"
git push
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| Tablet app — batch queue | Task 5 |
| Tablet app — check screen | Task 6 |
| Colour reference library (display only) | Tasks 2, 7, 8 |
| Ford cup viscosity entry + range validation | Task 6 (ViscosityCard) |
| Product-tier conditional logic (drawdown, oven) | Tasks 3, 6 |
| Admin panel — Ford cup config | Task 8 |
| Admin panel — viscosity targets | Task 8 |
| Admin panel — colour library | Task 8 |
| Admin panel — staff roster | Task 8 |
| Admin panel — KPI reference values | Task 8 |
| PIN-protected admin | Task 8 |
| Supervisor dashboard — KPI rate + traffic light | Task 9 |
| Supervisor dashboard — batch table + filters | Task 9 |
| Supervisor dashboard — CSV export | Task 9 |
| Supabase schema (all 6 tables) | Task 2 |
| Olympic brand colours throughout | Tasks 1, 4 |
| 10" landscape layout | Tasks 1, 5 |
| Touch targets ≥44px | Tasks 4, 5, 6 |
| First-pass rate KPI calculation | Task 3 |
| PWA / home screen bookmark | Tasks 1, 10 |
| Vercel deployment | Task 10 |

All spec requirements covered. ✓

---

*Plan written by Claude Code · ChangeLab KPI Initiative · Olympic Paints · 26 May 2026*
