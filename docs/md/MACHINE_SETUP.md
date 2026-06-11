# MACHINE_SETUP — Olympic Paints Automation

Setup path for a new Windows machine that needs to run this repo's scheduled automation. Verified 2026-05-23 on Windows 11 Pro / Administrator account. Outlook automation (read + send) re-verified 2026-05-24 on the Administrator box against `quintusl@olympicpaints.co.za`.

The repo lives under `%USERPROFILE%\OneDrive\1.Projects\1.Olympic Paints\` — OneDrive sync handles the actual file delivery. This doc covers everything you have to install or wire up locally.

> Looking for the new-teammate welcome guide instead? See [`ONBOARDING.md`](./ONBOARDING.md).

---

## 1. Install prerequisites

| Tool | Version | How |
|---|---|---|
| Git for Windows | 2.x | git-scm.com installer, or `winget install Git.Git` |
| **Python 3.13.x** | 3.13.0 verified on Administrator box | python.org installer with **PATH + py launcher + pip** ticked. Install to `C:\Python313\` (all-users) so the committed `.bat` wrappers and `register_from_xml.ps1` (which substitutes `py`) resolve to it. If winget is broken on the box: `iwr https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe -OutFile $env:TEMP\py.exe; & $env:TEMP\py.exe /quiet InstallAllUsers=1 TargetDir=C:\Python313 PrependPath=1 Include_launcher=1 Include_pip=1` |
| GitHub CLI | 2.62+ | `winget install GitHub.cli` or .msi from github.com/cli/cli/releases |
| Ollama | 0.24+ | ollama.com installer. After: `ollama pull llama3.2` and `ollama pull nomic-embed-text` |
| Claude Code | 2.1+ | `irm https://claude.ai/install.ps1 \| iex` — installs to `~\.local\bin`; add that dir to user PATH if the installer warns |
| Office (Outlook + Excel) | 365 / 2021 / 2016 | Required for `win32com.client` — HAVEN clocking and PULSE v2 daily mailer both send via Outlook |

---

## 2. Install Python packages

Open a fresh PowerShell so the new Python is on PATH, then:

```powershell
python -m pip install --upgrade pip
python -m pip install pandas openpyxl requests python-dotenv flask flask-cors pyarrow jinja2 pillow truststore pywin32 anthropic watchdog freezegun streamlit plotly python-docx lancedb PyMuPDF tqdm pytest pytest-mock
python C:\Python313\Scripts\pywin32_postinstall.py -install
```

The `pywin32_postinstall` step registers `pythoncom313.dll` / `pywintypes313.dll` in `System32` — required for Outlook automation (HAVEN clocking, PULSE v2 daily mailer, verification emails, merchandiser/H&S attachment download). Per-project `requirements.txt` files (under `1.Projects/*/`, `olympic-vector-db/`, `ollama-dashboard/`) can be installed afterwards if you want isolated venvs.

> **Verify Outlook automation:** `python -c "import win32com.client; o=win32com.client.Dispatch('Outlook.Application'); print(o.GetNamespace('MAPI').Accounts.Item(1).SmtpAddress)"` should print `quintusl@olympicpaints.co.za`. If `ModuleNotFoundError`, re-run the pywin32 install above against `C:\Python313\python.exe` explicitly.

---

## 3. Set environment variables

Edit `<repo>\.env` (already gitignored). Minimum:

```
NOTION_API_TOKEN=ntn_...                # notion.so/my-integrations; share with Olympic Paints DBs
```

Additional `.env`s some scripts read separately:

- `1.Projects\PULSE v2 — Sales & Ops Manager\.env` → `TELEGRAM_BOT_TOKEN` (chat id `8042233389`)
- `3.Resources\17. Strategic Intelligence\_verification\.env` → `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `FORM_ADMIN_SECRET`, `WHATSAPP_WEBHOOK_URL`, `WHATSAPP_WEBHOOK_SECRET`, `WHATSAPP_DEFAULT_TO`
- `1.Projects\AWS Data\.env` (if you have WooCommerce creds) → `WC_URL`, `WC_KEY`, `WC_SECRET`

---

## 4. Authenticate GitHub CLI

```powershell
gh auth login --hostname github.com --git-protocol https --web
# choose the FlomaticAuto account in the browser
```

Without this, dashboard builders run to completion locally but skip the `git push` to GitHub Pages (`olympic-paints-*` repos under `FlomaticAuto`). You'll see `Could not retrieve gh token — skipping push` in the log.

---

## 5. Clone the workspace-dashboard repo

Several scripts (`gen_dashboard.py`, `rebuild_hs_report.py`, `weekly_kaizen.py`, `haven_dashboard_check.py`, `build_report.py`, all PRISM tasks) push to or read from `%USERPROFILE%\workspace-dashboard\`. Note the local folder name is `workspace-dashboard` even though the GitHub repo is named `op-workspace-dashboard`:

```powershell
cd $env:USERPROFILE
gh repo clone FlomaticAuto/op-workspace-dashboard workspace-dashboard
```

Requires `gh` to be authenticated as FlomaticAuto first (§4). The repo contains `scripts/health_check.py`, `scripts/push_clocking_stats.py`, `scripts/portal_trigger_server.py`, and `scripts/olympic_platform/` — all referenced by Olympic schtasks. Without it, those code paths fail silently inside `try/except`.

---

## 6. Register scheduled tasks

**Recommended — universal registrar (one script, all 63 tasks):**

From an **elevated** PowerShell session:

```powershell
cd "$env:USERPROFILE\OneDrive\1.Projects\1.Olympic Paints"

# Preview what will be registered:
powershell -NoProfile -ExecutionPolicy Bypass -File .\register_from_xml.ps1 -DryRun

# Actually register:
powershell -NoProfile -ExecutionPolicy Bypass -File .\register_from_xml.ps1
```

`register_from_xml.ps1` reads `3.Resources/19. Runbooks/_audit/schtasks-export/_index.csv` and recreates every scheduled task from its committed XML definition. Idempotent (`-Force`), substitutes the original author's `C:\Users\quint\...` paths with `$env:USERPROFILE` automatically, supports `-Filter '<regex>'` to selectively register a subset (e.g. `-Filter 'PRISM'`). 63 tasks register in under a second.

To refresh the XMLs after schedule changes on the canonical box:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\3.Resources\19. Runbooks\_audit\export_schtasks.ps1"
# then commit the updated XMLs
```

**Older alternative — individual registrar scripts** (still work, kept for reference; the universal registrar covers all the same tasks plus the ~30 ad-hoc ones quint's box had built up over time):

```powershell
$root = "$env:USERPROFILE\OneDrive\1.Projects\1.Olympic Paints"

# 7 existing registrars
& "$root\register_scheduled_task.ps1"
& "$root\register_weekly_kaizen.ps1"
& "$root\1.Projects\Returns KPI System\register_returns_scheduler.ps1"
& "$root\1.Projects\AWS Data\register_account_health_tasks.ps1"
& "$root\1.Projects\Weekly Sales Report\scheduler\register.ps1"
& "$root\1.Projects\PULSE v2 — Sales & Ops Manager\scheduler\register.ps1"
& "$root\3.Resources\17. Strategic Intelligence\_verification\register_ci_reminders_task.ps1"

# 5 new registrars (added 2026-05-23)
& "$root\2.Areas\11. HR\Clocking Reports\scripts\register_haven_tasks.ps1"
& "$root\2.Areas\12. Health and Safety\register_hs_tasks.ps1"
& "$root\2.Areas\3. Merchandising\register_merch_calendar.ps1"
& "$root\register_notion_todos_sync.ps1"
& "$root\register_weekly_dashboards.ps1"

# APEX system health monitor (added 2026-06-03)
& "$root\agents\register_apex_health_monitor.ps1"
```

> ⚠️ **The APEX health monitor is new (2026-06-03) and is NOT yet in the universal
> registrar's XML export.** On the canonical box, after running
> `agents\register_apex_health_monitor.ps1` once, re-export so every box inherits it via
> `register_from_xml.ps1`:
> ```powershell
> powershell -NoProfile -ExecutionPolicy Bypass -File ".\3.Resources\19. Runbooks\_audit\export_schtasks.ps1"
> ```
> The monitor is path-agnostic (`$env:USERPROFILE` / `~` / `Path(__file__)`) and **stdlib-only**,
> so it needs no edits or extra packages to run under the Administrator account. It reads the
> platform's `~/workspace-dashboard/data/schedule_manifest.json` (produced hourly by
> `PRISM \ Build Schedule Manifest`), so that task must be registered and have run at least once.

Two more individual registrars exist locally but their parent project folders are gitignored — they're covered by the universal registrar too, so this only matters if you're using the individual-script approach:

- `1.Projects\AWS Data\register_ecommerce_tasks.ps1` — Dashboard Build (weekdays 07:30) + Email Digest (weekdays 08:00)
- `1.Projects\Returns KPI System\register_returns_watcher.ps1` — Returns Folder Watcher (AtLogOn, continuous)

After running the universal registrar, you should have **63 tasks** across `\Olympic Paints\*`, `\PULSE\*`, `\PULSE v2\*`, and loose `\Olympic *` / `\HAVEN *` paths. See [`3.Resources/19. Runbooks/RUNBOOKS.md`](./3.Resources/19.%20Runbooks/RUNBOOKS.md) for the per-job runbook index.

---

## 7. Verify the install

```powershell
# Python deps load
python -c "import pandas, openpyxl, win32com.client, anthropic, watchdog, streamlit, lancedb, fitz, plotly; print('OK')"

# Scheduled task count (~63 expected after running the universal registrar)
(schtasks /query /fo CSV /nh | Select-String -Pattern 'olympic|pulse|haven|prism|striker|sigma|vault|flash' -CaseSensitive:$false).Count

# Low-blast-radius spot-check (builds HTML locally, push silently skipped without gh auth)
schtasks /run /tn "\Olympic Paints\Merchandising\Merchandising Calendar"
Start-Sleep 30
Get-Content "$env:USERPROFILE\.claude\logs\merchandising\calendar.log" -Tail 10
```

Expected: imports print `OK`, count is ~63, log ends with `Done.` after writing `index.html` to `%USERPROFILE%\olympic-paints-merchandising-calendar\`.

---

## 8. Known gaps (carry these forward)

1. **PULSE Leaderboard / Scorecard** (Runbook #4, #5) — modules don't exist in `pulse/`. No schtasks yet. Needs spec + implementation before scheduling.
2. **Meeting Minutes Extractor** — task registered, but `run_meeting_extractor.bat` has a `PAUSED` early-exit block (added 2026-05-14). Remove the block to resume. Also change `C:\Python313\python.exe` to `python` (the bat still references a Python install path that isn't generalized).
3. **Notion Todos Sync** — schtasks fires cleanly but exits `rc=1` until `todos.md` exists in `~\.claude\projects\<slug>\memory\`. The file is created automatically the first time Claude Code writes a todo via TodoWrite on this machine.
4. **`gh auth` as FlomaticAuto** — see §4 above. Required for any GitHub Pages publish step.
5. **`workspace-dashboard` repo** — resolved 2026-05-24: `FlomaticAuto/op-workspace-dashboard`, cloned locally as `~/workspace-dashboard`. See §5 above for the exact command.
6. **Logs MUST live outside OneDrive** — all scheduled-task logs go to `%USERPROFILE%\.claude\logs\<job>\`. Don't move them into OneDrive; the sync lock hangs the schtasks-launched Python and Task Scheduler kills the process tree with `STATUS_CONTROL_C_EXIT` (`-1073741510`).

7. **Duplicate scheduled tasks on this Administrator box** — During the 2026-05-23/24 audit, several jobs were registered twice at different TaskPaths before quint's full task set was imported via the universal registrar. The duplicates fire on independent schedules and double-process the same work. Pick one per pair to disable/delete (manual triage):

   | Likely mid-session duplicate | Quint's canonical version |
   |---|---|
   | `\Olympic Paints\Notion Todos Sync` | `\Olympic Paints\VAULT\Sync Claude TODOs` |
   | `\Olympic Paints\HAVEN\Weekly Dashboard Check` | `\Olympic Paints\HAVEN\HAVEN Clocking Report Daily` |
   | `\Olympic Paints\HAVEN\Folder Watcher` | `\Olympic Paints\HAVEN\HAVEN Fetch Clocking Email` (different role; review before deleting) |
   | `\Olympic Paints\Merchandising\Merchandising Calendar` | `\Olympic - Merchandising Calendar Rebuild` |
   | `\Olympic Paints\E-Commerce\Email Digest` | `\Olympic Paints\FLASH\OlympicPaints_EmailECommerceDashboard` |
   | `\Olympic Paints\E-Commerce\Dashboard Build` | `\OlympicPaints_Ecommerce_Dashboard_Refresh` |
   | `\Olympic Paints\H&S\Weekly Refresh` | `\Olympic Paints\SIGMA\H&S Weekly Refresh` |
   | `\Olympic Paints\Olympic Paints - Meeting Minutes Extractor` | `\Olympic Paints\VAULT\Olympic Paints - Meeting Minutes Extractor` |
   | `\Olympic Paints\Olympic Paints - Weekly Kaizen` | `\Olympic Paints\VAULT\Olympic Paints - Kaizen Daily Sync` (review cadence — might be intentionally different) |

---

## References

- [`3.Resources/19. Runbooks/RUNBOOKS.md`](./3.Resources/19.%20Runbooks/RUNBOOKS.md) — canonical per-job runbook index (22 jobs)
- `~/workspace-dashboard/data/schedule_manifest.json` — auto-generated task list + health (source of truth)
- [`agents/apex_health_monitor.py`](./agents/apex_health_monitor.py) — daily health digest + dead-man's switch (reads the manifest)
- `op-workspace-dashboard/scripts/olympic_platform/README.md` — the platform operator guide
- [`CLAUDE.md`](./CLAUDE.md) — repo navigation hub
- [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) — HTML/dashboard styling rules
- [`OPERATIONS_RUNBOOK.md`](./OPERATIONS_RUNBOOK.md) — repo-wide deployment overview
- Claude Code memory dir: `~\.claude\projects\c--Users-*-OneDrive-1-Projects-1-Olympic-Paints\memory\`

---

## Session changelog (2026-05-23)

Commits made during the onboarding session that produced this doc, newest first:

| Commit | What |
|---|---|
| `aef3d16` | feat(ci-verification): add wholesaler tracking + WhatsApp notifications |
| `62787b4` | fix(paths): generalize hardcoded `C:\Users\quint` paths in 11 scheduled python scripts |
| `9296fb3` | feat(scheduler): register the 10 missing Runbook jobs as scheduled tasks (5 new registrars) |
| `89da20c` | fix(scheduler): use `$env:USERPROFILE` / `%USERPROFILE%` instead of hardcoded `C:\Users\quint` (7 registrar scripts + 2 .bats) |
