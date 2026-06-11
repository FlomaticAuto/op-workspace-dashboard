# Runbook — APEX Daily Health Digest

> **Last verified:** 2026-06-03
> **Owner:** Quintus
> **Criticality:** high   *(this is the watchdog — if it is silent, you are blind to the whole platform)*

---

## Purpose

The Olympic Platform (`op-workspace-dashboard/scripts/olympic_platform/`) already wraps every
task with `run_job.py`, writes heartbeats, rebuilds `schedule_manifest.json` hourly, and pings
Telegram the moment a wrapped job fails. What it deliberately does **not** do (per its own
README) is a *daily success digest* or a dead-man's switch. This job is exactly that, and
nothing more. Once or twice a day it reads the platform's manifest and answers: across every
scheduled task, what is red / stale / never-run right now — and is the platform itself alive?

If this stopped, you'd lose the daily "all green / here's what's broken" summary and the
single most important alert: **the box is down.**

---

## How it runs

- **Trigger:** Windows Task Scheduler — `\Olympic Paints\APEX\APEX Health Monitor AM` and `... PM`
- **Schedule:** Mon–Fri 09:30 and 18:00 SAST
- **Host machine:** the production box (same box as the platform)
- **Entry point:** `agents/apex_health_monitor.py`
- **Invocation:** `python "…\agents\apex_health_monitor.py"` (stdlib only — no dependencies)
- **Environment:** `TELEGRAM_BOT_TOKEN` (env, or the PULSE `.env`). Optional `OLYMPIC_SCHEDULE_MANIFEST` to point at a non-default manifest path.

---

## Inputs

| Source | Path | Format | Refresh cadence |
|---|---|---|---|
| Platform manifest | `~/workspace-dashboard/data/schedule_manifest.json` | JSON | hourly (PRISM \ Build Schedule Manifest) |
| Criticality overlay | `agents/job_criticality.json` | JSON | by hand, rarely |

The digest never enumerates Task Scheduler itself and never runs any job — it only reads the
manifest the platform already produces. Per task it derives a status from the heartbeat
(`ok` / `stale`) when present, otherwise from Task Scheduler's own `last_task_result`
(`0` = ok, `267011` = never-run, any other non-zero = FAIL).

---

## Outputs

| Destination | Path / URL | Format | Consumer |
|---|---|---|---|
| Telegram | chat `8042233389` | text | Quintus |

Statuses: **OK** / **OK_NO_HB** (Task Scheduler success, job not yet wrapped with a heartbeat) /
**STALE** / **FAIL** / **NEVER_RUN** / **RUNNING** / **DISABLED**. Problems are listed first,
sorted by criticality from `job_criticality.json`.

---

## Known failure modes

1. **Symptom:** Digest reports a job FAIL that you believe is fine.
   **Cause:** Task Scheduler recorded a non-zero `last_task_result` (e.g. `0x80070002` = the
   script/python path moved). The job genuinely failed at the OS level even if it "used to work".
   **Fix:** Check the task's action path and last run in Task Scheduler; fix the path or re-register.

2. **Symptom:** Many jobs show OK_NO_HB.
   **Cause:** Those tasks aren't wrapped with `run_job.py` yet, so there's no heartbeat — the
   digest is trusting Task Scheduler's exit code. That's fine, just lower-fidelity.
   **Fix:** Migrate them to the wrapper (platform `migrate_tasks.ps1`) when convenient.

3. **Symptom:** "DEAD-MAN'S SWITCH: schedule_manifest.json is N h old."
   **Cause:** The hourly `Build Schedule Manifest` task stopped — or the box is off / asleep.
   **Fix:** This is the alert working. Check the box is on; check `PRISM \ Build Schedule Manifest`.

4. **Symptom:** No digest at all by ~09:45 on a weekday.
   **Cause:** Box down, or the APEX task was deleted.
   **Fix:** `Get-ScheduledTask -TaskPath "\Olympic Paints\APEX\*" | Get-ScheduledTaskInfo`.

---

## Logs

- **Primary log:** `C:\Users\quint\.claude\logs\apex-health\` (redirect in the task if desired)
- **Task last run:** `Get-ScheduledTask -TaskName "APEX Health Monitor AM" | Get-ScheduledTaskInfo`
- **Telegram:** chat `8042233389`, search "APEX Daily Digest"

---

## Manual run

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\agents"

python apex_health_monitor.py --dry-run      # print the digest, send nothing
python apex_health_monitor.py                # send it now
python apex_health_monitor.py --quiet        # send only if something is red/stale
```

Register (once, as Administrator):

```powershell
powershell -ExecutionPolicy Bypass -File "agents\register_apex_health_monitor.ps1"
```

---

## Recent incidents

- **2026-06-03** — Reconciled with the existing Olympic Platform. Originally built against a
  hand-written `jobs.yaml` + artifact mtimes; rebuilt to read the platform's
  `schedule_manifest.json` instead (no duplicate system). First dry-run against week-old
  manifest data surfaced 9 tasks with non-zero Task Scheduler results (CI reminders, account-
  health reminder, returns dashboard, below-RB, sales dashboard, etc.) — failures with no daily
  summary before this existed.

---

## Related

- Code: [`agents/apex_health_monitor.py`](../../agents/apex_health_monitor.py), [`agents/job_criticality.json`](../../agents/job_criticality.json)
- Platform: `op-workspace-dashboard/scripts/olympic_platform/` (`run_job.py`, `build_schedule_manifest.py`, `heartbeat.py`, `README.md`)
- Supervisor profile: [`agents/APEX.md`](../../agents/APEX.md)
- Shared services: [`PLATFORM_SERVICES.md`](../../PLATFORM_SERVICES.md)
