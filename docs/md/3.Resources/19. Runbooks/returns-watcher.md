# Runbook — Returns Manager Folder Watcher

> **⚠️ DEPRECATED — 2026-05-25**
> **Replaced by:** `build_returns_dashboard.py` (v2 pipeline: Vercel form → Supabase → static GitHub Pages dashboard)
> **See:** `docs/superpowers/plans/2026-05-19-returns-manager-v2.md` and `register_returns_scheduler.ps1`

---

The file-watcher + PDF-OCR pipeline has been retired. No Streamlit app, no folder watcher, no PDF scanning.

**Old entry points (deleted/archived):**
- `scripts/returns_watcher.py` → moved to `scripts/_deprecated/`
- `scripts/ingest_returns_scan.py` → moved to `scripts/_deprecated/`
- `scripts/returns_app.py` → moved to `scripts/_deprecated/`
- `scripts/returns_db.py` → moved to `scripts/_deprecated/`
- `register_returns_watcher.ps1` → deleted

**Scheduled task removed:** `\Olympic Paints\Returns\Returns Folder Watcher`

**Active scheduled task (v2):** `\Olympic Paints\Returns\OlympicPaints_BuildReturnsDashboard` — runs Mon–Fri 07:00, registered via `register_returns_scheduler.ps1`

---

## v2 Architecture

| Step | Component |
|---|---|
| Intake | Next.js form on Vercel → Supabase `form_submissions` |
| Builder | `scripts/build_returns_dashboard.py` (daily, Task Scheduler) |
| Output | GitHub Pages: `https://flomaticauto.github.io/olympic-paints-returns/` |
| Notifications | Supervisor emails via Outlook (win32com) + Telegram |
