# Olympic Paints — Quality Capture System
**Design Spec · 26 May 2026 · ChangeLab KPI Initiative**

---

## Purpose

Design and build a tablet-based, in-line quality capture system for manufacturing assistants at Olympic Paints. The system enables assistants to record colour and viscosity checks for each batch during production. Captured data feeds directly into the **first-pass quality rate** — the primary KPI metric for the Product Quality category in the ChangeLab KPI scoreboard.

---

## Context

ChangeLab is running a Culture Realignment programme at Olympic Paints. The KPI framework defines five organisation-level metrics, the first being **Product Quality**. The target is to improve the first-pass quality rate from a baseline of 82% to a goal of 92% by end of 2026. This system is the data-gathering infrastructure for that metric — it does not exist today, and must be built alongside the scoreboard rollout.

---

## Scope

**In scope:**
- Tablet app for in-line batch quality capture (colour + viscosity) — single shared tablet
- Colour reference library (Olympic colour database with hex codes, displayed as visual reference only — no automated tolerance checking)
- Supabase database for batch records and colour library
- Supervisor / Quintus read-only dashboard (web-based)
- Ford cup viscosity entry with target range validation
- Product-tier-aware check flow (Decor/Eclipse/Kalahari vs Master Decorator+ vs Enamel)
- Admin panel for configuring Ford cup types, target ranges, and timing per product tier
- Staff roster: 4 assistants, 4 supervisors (name-based selection on tablet)

**Out of scope (Phase 1):**
- Integration with Zoho CRM or Books
- Automated alerts or notifications on fail
- Full production scheduling / batch pre-loading by supervisor (assistants add batches themselves)
- Mobile phone access
- Automated colour tolerance checking (colour pass/fail is a manual visual judgement by the assistant)

---

## Product Tiers & Check Logic

| Product Tier | Colour Check Method | Viscosity Method | Special Prompt |
|---|---|---|---|
| Decor, Eclipse, Kalahari | Visual comparison vs hex swatch on tablet (manual pass/fail) | Ford cup (seconds entered, auto range check) | None |
| Master Decorator and above | Drawdown per batch + visual vs hex swatch (manual pass/fail) | Ford cup (seconds entered, auto range check) | "Drawdown required" badge + confirmation checkbox |
| Enamel | Visual vs hex swatch post oven-dry (manual pass/fail) | Ford cup (seconds entered, auto range check) | "Oven dry ~5 min" prompt + oven confirmation checkbox |

**Colour tolerance note:** Colour pass/fail is a human visual judgement only. The tablet displays the hex swatch as a reference. There is no automated colour tolerance check in Phase 1 — the assistant decides pass or fail.

A batch is recorded as **first-pass = true** if both colour and viscosity pass on the first submission. Resubmissions are tracked but do not count toward the first-pass rate.

---

## System Architecture

```
Tablet App (PWA or native)
    │
    ├── Colour Library (read) ──────────────┐
    │                                        │
    └── Batch Records (write) ──────────────┤
                                             │
                                        Supabase
                                             │
                                    Supervisor Dashboard (read)
                                    (web app — Quintus + supervisors)
```

### Supabase Tables

**`colours`** — Olympic Paints colour reference library
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `name` | text | e.g. "Autumn Spice" |
| `hex_code` | text | e.g. "#C4843E" — display reference only, no automated tolerance check |
| `product_tier` | text | decor / eclipse / kalahari / master_decorator / enamel |
| `range_code` | text | Olympic range code if applicable |
| `active` | boolean | Hide discontinued colours without deleting |

**`batches`** — One record per batch quality check
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `batch_number` | text | e.g. "#041" |
| `product_tier` | text | FK to product tier |
| `colour_id` | uuid | FK to colours table |
| `line` | text | Production line identifier |
| `shift` | text | morning / afternoon / night |
| `colour_pass` | boolean | True = colour matched reference |
| `colour_notes` | text | Optional assistant notes |
| `viscosity_seconds` | numeric | Ford cup reading |
| `viscosity_pass` | boolean | Calculated: within target range |
| `first_pass` | boolean | True if both checks pass on first submission |
| `assistant_id` | uuid | FK to staff table |
| `supervisor_id` | uuid | FK to staff table |
| `checked_at` | timestamptz | Submission timestamp |
| `oven_dried` | boolean | Enamel only — confirms oven step completed |
| `drawdown_done` | boolean | Master Decorator+ only |

**`staff`** — Assistants and supervisors
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `name` | text | Display name |
| `role` | text | assistant / supervisor / admin |
| `active` | boolean | |

**Fixed roster (Phase 1):** 4 assistants + 4 supervisors. Selected by name tap on the tablet — no login/password required for assistants. Admin panel access requires a PIN.

**`ford_cups`** — Ford cup configurations (managed via Admin Panel)
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `name` | text | e.g. "Ford Cup #4", "Zahn Cup #2" |
| `orifice_mm` | numeric | Cup orifice diameter in mm |
| `notes` | text | Optional description |
| `active` | boolean | |

**`viscosity_targets`** — Ford cup target ranges per product tier (managed via Admin Panel)
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `product_tier` | text | decor / eclipse / kalahari / master_decorator / enamel |
| `ford_cup_id` | uuid | FK to ford_cups — which cup to use |
| `min_seconds` | numeric | Lower bound (pass threshold) |
| `max_seconds` | numeric | Upper bound (pass threshold) |
| `notes` | text | e.g. "Measure at 23°C" |
| `updated_at` | timestamptz | Track when ranges were last changed |
| `updated_by` | uuid | FK to staff — who changed it |

---

## Tablet App

### Platform
Progressive Web App (PWA) served from Vercel or similar. Accessed on a single dedicated 10-inch Android tablet shared across the production floor. No app store required — bookmark to home screen.

**Hardware:** 1 tablet total. Shared between all 4 assistants across shifts.

### Brand & Visual Design
The app uses the **Olympic Paints brand colour system** exclusively:

| Token | Hex | Usage |
|---|---|---|
| Olympic Yellow | `#F5C400` | Primary accent, active states, submit button, selected highlights |
| Olympic Navy | `#1A3D6E` | Navigation bar, panel headers, section labels |
| Black | `#0D0D0D` | App background |
| Dark surface | `#1A1A1A` | Cards and panels |
| Mid surface | `#2C2C2C` | Secondary surfaces, queue panel |
| Border | `#3A3A3A` | Dividers and outlines |
| White | `#FFFFFF` | Primary text |
| Muted text | `#888888` | Secondary/label text |
| Pass green | `#27AE60` | Pass result states |
| Fail red | `#E74C3C` | Fail result states |
| Pending amber | `#F39C12` | Pending / in-progress states |

### Layout — 10" Landscape (960×600px)

```
┌─────────────────────────────────────────────────────────────────┐
│  [OLYMPIC] Quality Capture          Line 2 · Morning · 09:14   │  ← Navy nav bar, yellow logo
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│  TODAY'S BATCHES │  Batch #041 — Master Decorator              │
│  ─────────────── │  Autumn Spice · 200L · Line 2               │
│  #039 Decor ✓    │  ─────────────────────────────────────────  │
│  #040 Eclipse ✓  │  [Colour Ref]    [Colour Result]            │
│  #041 Master ●   │  hex swatch      PASS / FAIL buttons         │
│  #042 Enamel     │                  notes field                 │
│                  │  [Viscosity]     [Sign Off]                  │
│  + Add Batch     │  numpad entry    assistant + supervisor      │
│                  │                                              │
│                  │  ─────────────────────────────────────────  │
│                  │  All 4 checks required    [Submit Batch ›]  │
└──────────────────┴──────────────────────────────────────────────┘
```

### Screen Flow

1. **Home / Queue** — shows today's batches for the line with status pills (Queued / Checking / Pass / Fail). Tap any batch to open it.
2. **Check Screen** — 4-card grid (see layout above). All 4 cards must be completed before Submit is enabled.
3. **Confirmation** — brief success state, batch marked as submitted, queue updates.

### Touch Design
- All interactive targets minimum 44×44px
- Pass/Fail buttons full-width, high contrast
- Numpad for viscosity — no keyboard popup
- No swipe gestures — tap only

### Product-Tier Conditional Logic
- **Master Decorator+**: show "Drawdown Required" badge in header; show drawdown confirmation checkbox in Colour Ref card before Pass/Fail enabled
- **Enamel**: show "Oven dry ~5 min before colour check" warning banner; show oven confirmation checkbox before colour Pass/Fail enabled. Enamel has no other special quality check beyond oven-dry colour.
- **Decor / Eclipse / Kalahari**: standard flow, no additional prompts

---

## Admin Panel

A PIN-protected screen accessible from the tablet nav bar (or via desktop browser). Used by Quintus or a designated supervisor to configure the system without developer involvement.

### Admin Panel Sections

**1. Ford Cup Configuration**
- Add / edit / deactivate Ford cup types (name, orifice size, notes)
- E.g. add "Ford Cup #4", "Zahn Cup #2", custom cup types

**2. Viscosity Targets**
- Per product tier: select which Ford cup to use, set min/max seconds, add notes (e.g. temperature conditions)
- Changes are timestamped and attributed to the admin who made them
- History of changes visible (so if a range is adjusted, the reason can be noted)

**3. Colour Library**
- Add / edit / deactivate colours
- Fields: name, hex code, product tier, Olympic range code
- Hex code is display-only — no tolerance range needed

**4. Staff Roster**
- Add / edit / deactivate assistants and supervisors
- Set role (assistant / supervisor)
- No passwords — names appear in tap-to-select lists on the tablet

**5. KPI Reference Values**
- Set the baseline (82%) and goal (92%) for the first-pass quality rate
- These are used in the supervisor dashboard traffic-light display

### Admin Access
- PIN-protected (4-digit PIN, set at setup)
- No role-based permissions in Phase 1 — PIN holder has full admin access
- Accessible from tablet or desktop browser

---

## Supervisor Dashboard

Simple read-only web page (desktop/tablet browser). Shows:
- Today's batches with full check details
- Running first-pass quality rate for the day and current month
- Fail flags highlighted (colour and/or viscosity fail noted separately)
- Filter by line, shift, product tier, date range
- Export to CSV for monthly KPI reporting

Access: Supabase row-level security — supervisors and Quintus only.

---

## Fail Handling

When a batch fails (colour, viscosity, or both):
- The result is recorded as-is
- The batch status in the queue shows **FAIL** (red pill)
- The supervisor dashboard flags it
- The assistant can continue to the next batch — no blocking action required
- No automated notification in Phase 1

This keeps the floor workflow uninterrupted while giving supervisors visibility.

---

## KPI Integration

The **first-pass quality rate** is calculated as:

```
first_pass_rate = COUNT(batches WHERE first_pass = true) / COUNT(all batches) × 100
```

This can be queried directly from Supabase and pulled into the monthly scoreboard update. The baseline (82%) and goal (92%) are fixed reference points stored separately and used for the traffic-light indicator on the ChangeLab scoreboard.

---

## Rollout Plan

| Phase | Deliverable | Target |
|---|---|---|
| 1 | Build Supabase schema + Admin Panel. Quintus configures Ford cup types, viscosity targets, and colour library. Enter 4 assistants + 4 supervisors. | June 2026 |
| 2 | Build tablet app (batch queue + check screen). Pilot with assistants. Supervisor dashboard live. | June 2026 |
| 3 | All assistants trained. First-pass rate feeds monthly KPI scoreboard from July floor gathering. | July 2026 |

---

## Open Questions (to resolve before build)

1. **Ford cup target ranges** — what are the acceptable min/max seconds per product tier? These will be entered via the Admin Panel, but must be confirmed with the production team before the pilot goes live.
2. **Assistant and supervisor names** — the 4 assistants and 4 supervisors need to be named for the staff roster. To be confirmed by Quintus.
3. **Admin PIN** — who holds the admin PIN? Quintus only, or also a designated supervisor?

---

*Spec written by Claude Code · ChangeLab KPI Initiative · Olympic Paints · May 2026*
