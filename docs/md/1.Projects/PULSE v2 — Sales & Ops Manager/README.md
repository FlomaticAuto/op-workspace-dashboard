# PULSE v2 — Sales & Ops Manager

Re-engineered daily mailer + preview gate. Mobile-first by design.

## Quick start

```powershell
cd "c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\PULSE v2 — Sales & Ops Manager"
python -m pip install -r requirements.txt

# Render today's mailer for everyone in config
python -m pulse render-daily

# Start the preview gate (mobile-friendly, opens on your phone)
python -m pulse preview
# → http://localhost:8765/   (or http://<your-laptop-ip>:8765/ from phone)

# Force-send a single rep without waiting for the gate
python -m pulse send --rep AC

# Inspect today's approval state
python -m pulse status
```

## Folder map

```
pulse/
├── data.py             ← unchanged from v1 (verified correct)
├── payload.py          ← single source for what's in the email
├── render.py           ← Jinja env (1 template, 2 modes)
├── send.py             ← Outlook + Telegram + log
├── preview_server.py   ← Flask :8765 — the gate
├── cli.py              ← python -m pulse <cmd>
└── templates/
    ├── base_email.html.j2       ← inline-styled, mobile responsive
    ├── base_browser.html.j2     ← CSS tokens, theme toggle
    ├── daily.html.j2            ← extends either base
    ├── preview_index.html.j2    ← gate UI
    └── partials/                ← kpi_card, store_row, week_plan, debtors, recovery
```

## Why mobile-first matters here

- **Reps** read PULSE on their phones (Android / iPhone Gmail).
- **Quintus** approves dispatches from his phone via the preview gate.

Every template uses `viewport-fit=cover`, single-column under 768px, ≥16px body font, ≥44px tap targets. Email partials use HTML tables for Outlook compatibility but `<style>` block media queries override to single-column on phones.

## Soft-gate semantics

1. `pulse render-daily` runs at 08:55 → renders to `output/previews/<date>/`
2. `pulse preview` runs at 09:00 → Flask serves at :8765 + 30-min auto-send timer starts
3. Quintus reviews each rep card on his phone. Tap **Approve** / **Veto** / **Send now**.
4. At T+30 (default 09:30): every rep marked `approved` or unmarked (default-is-approved) dispatches via local Outlook. Vetoed reps skip.
5. Send log appends to `output/send_log.json`.

## Test mode

`go_live_reps` in `pulse_config.json` controls live dispatch. Reps **in** the list email at their real address. Reps **not in** the list redirect to `qlategan@gmail.com` and the subject gets a `[TEST]` prefix so you can tell at a glance.

## Tests

```powershell
python -m pytest tests/ -v
```

`test_render.py` proves the same payload renders to both email and browser modes carrying the same business facts. This is the drift-prevention net.

## Migration from old PULSE

See `2026-05-17-pulse-v2-plan.md` — rep-by-rep cutover, AC first, old PULSE keeps running for the others until each migrates.
