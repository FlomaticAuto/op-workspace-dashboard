# Task Scheduler Consolidation + Run-Log Manifest — Design

**Date:** 2026-05-16
**Status:** Approved, ready for implementation plan
**Sub-project:** 1 of 3 (foundation for Olympic Paints management platform)

---

## Context

The Olympic Paints workspace runs ~20+ scheduled Python/PowerShell jobs across multiple agents (PULSE, HAVEN, PRISM, VAULT, etc.). They are scattered across Windows Task Scheduler with no consistent folder, naming, or success-detection convention. Failures are easy to miss; there is no single source of truth for "what's scheduled, when does it run next, did it succeed."

This is sub-project 1 of 3 in building an Olympic Paints management platform. Subsequent sub-projects:

- **#2 — Agent Registry**: `agents_manifest.json` mapping each agent to its scripts, schedules, dashboards.
- **#3 — Control Tower UI**: single page consuming both manifests.

This spec only covers #1.

## Goals

1. All scheduled tasks tied to this repo live under `\Olympic Paints\<AGENT>\<Task Name>` in Windows Task Scheduler.
2. Every run produces a heartbeat with timing, exit code, and optional summary data.
3. Failures trigger a Telegram alert immediately (no daily success digest).
4. A `schedule_manifest.json` provides the single source of truth that sub-project #3's UI will render.

## Non-Goals

- The control tower UI itself (sub-project #3).
- Agent registry data model (sub-project #2 — this spec only writes `agent` as a string).
- Migrating non-Olympic scheduled tasks (Flomatic, GOD, Timion, personal jobs).
- Storing run history older than the last 100 runs per job (older history stays in per-job log files).
- Replacing the existing `health_check.py` updates page — it can continue running; this work supersedes it once #3 ships.

## Scope (what counts as an "Olympic task")

Any scheduled task whose action invokes a script under:

- `c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\` (Olympic Paints OneDrive workspace)
- `C:\Users\quint\workspace-dashboard\` and `C:\Users\quint\workspace-dashboard\.github\`
- `C:\Users\quint\olympic-paints-*` (any olympic-paints-prefixed repo)
- Any other repo created in service of Olympic Paints automation

Detection during migration is by inspection of each task's Action path.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Windows Task Scheduler                                          │
│  \Olympic Paints\<AGENT>\<Task Name>                             │
│  └─ Action: python run_job.py <job-id> --agent <AGENT> -- <cmd>  │
└─────────────────────────┬────────────────────────────────────────┘
                          │ on every run
                          ▼
            ┌─────────────────────────────┐
            │  run_job.py  (wrapper)      │
            │  - times start/end          │
            │  - captures exit code       │
            │  - reads optional summary   │
            │  - writes heartbeat         │
            │  - Telegram on failure      │
            └──────────────┬──────────────┘
                           │
                           ▼
        C:\Users\quint\.claude\heartbeats\
            <job-id>.json          ← latest run
            <job-id>.history.jsonl ← rolling last 100 runs
            _summary\<job-id>.json ← optional, written by wrapped script

                           │  (read on demand)
                           ▼
            ┌──────────────────────────────────┐
            │  build_schedule_manifest.py      │
            │  - reads Task Scheduler (COM)    │
            │  - reads heartbeats              │
            │  - writes schedule_manifest.json │
            └──────────────┬───────────────────┘
                           ▼
       workspace-dashboard/data/schedule_manifest.json
```

## Folder structure in Task Scheduler

```
\Olympic Paints\
    PULSE\
        Daily Mailer
        Leaderboard
        Hunting Week
        ...
    HAVEN\
        Dashboard Check
        Watcher
    PRISM\
        Weekly Health Report
        Build Schedule Manifest    (new — built in this spec)
    VAULT\
        Sync Claude TODOs
        Meeting Extraction
    STRIKER\
        ...
    SIGMA\
        ...
    BLAZE\
        ...
    FLASH\
        ...
```

Agent classification is determined at migration time by inspecting the script path or by a hand-maintained mapping in `migrate_tasks.ps1`.

---

## Components

### 1. `run_job.py` — universal wrapper

**Location:** `c:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\Olympic Management Platform\scripts\run_job.py`
(subject to refinement; final path decided at implementation time and recorded in the plan)

**Invocation:**

```
python run_job.py <job-id> --agent <AGENT> -- <real command and args...>
```

`<job-id>` is a kebab-case slug (e.g. `pulse-daily-mailer`). `--agent` is one of the canonical agent names. Anything after `--` is the original command.

**Behavior:**

1. Record `started_at` (ISO 8601 with SAST offset).
2. Spawn the wrapped command as a subprocess; capture stdout and stderr.
3. On completion record `finished_at`, `duration_seconds`, `exit_code`.
4. If the wrapped script wrote `C:\Users\quint\.claude\heartbeats\_summary\<job-id>.json`, read and delete it (so it does not persist across runs).
5. Compute `ok` (true if `exit_code == 0`).
6. Capture last 50 lines of stdout and stderr as `stdout_tail` / `stderr_tail`.
7. Write `C:\Users\quint\.claude\heartbeats\<job-id>.json` (atomic write via temp + rename).
8. Append the same record to `C:\Users\quint\.claude\heartbeats\<job-id>.history.jsonl`, then truncate to last 100 entries.
9. If `ok == false`: send Telegram alert containing job id, agent, exit code, last 5 stderr lines, log path. Use the existing PULSE `.env` token (per `feedback_telegram_token_source.md`).
10. Exit with the wrapped command's exit code (so Task Scheduler's `LastTaskResult` still reflects truth).

**Error handling:**

- If the wrapped process is killed (Ctrl+C, timeout, crash): heartbeat is still written with `ok=false` and `exit_code = signal/-1`.
- If `run_job.py` itself crashes: Task Scheduler's `LastTaskResult` will be non-zero, but no heartbeat is written. This is acceptable degradation; the manifest builder reports "no heartbeat" as a distinct state from "heartbeat says failed."
- Logging to OneDrive paths is forbidden (per `feedback_schtasks_logs_outside_onedrive.md`). All heartbeat files live under `C:\Users\quint\.claude\heartbeats\`.

**Heartbeat schema (data contract):**

```json
{
  "job_id": "pulse-daily-mailer",
  "agent": "PULSE",
  "started_at": "2026-05-16T06:00:01+02:00",
  "finished_at": "2026-05-16T06:00:14+02:00",
  "duration_seconds": 13,
  "exit_code": 0,
  "ok": true,
  "stdout_tail": "Sent 4 emails. Done.",
  "stderr_tail": "",
  "summary": { "emails_sent": 4, "errors": 0 }
}
```

`summary` is free-form per job — convention only, no validation. Absent if the wrapped script wrote no summary file.

### 2. `migrate_tasks.ps1` — one-off migration

**Location:** alongside `run_job.py`.

**Behavior:**

1. Enumerate scheduled tasks via `Schedule.Service` COM (not `schtasks` — per `feedback_pulse_task_names_em_dash.md`).
2. Filter to tasks whose Actions reference any in-scope path (see Scope section).
3. For each task:
   - Export current XML.
   - Classify into an agent using a mapping table in the script (e.g. `*pulse*` → PULSE, `*haven*` → HAVEN, etc.). Unknown classification surfaces in the dry-run report and blocks migration of that task until resolved manually.
   - Rewrite the Action: prepend `python run_job.py <job-id> --agent <AGENT> --` to the original command. Working directory preserved.
   - Register the new task under `\Olympic Paints\<AGENT>\<original-name>`.
   - Verify the new task exists and is enabled.
   - Delete the old task only after verification succeeds.
4. Em-dash names are preserved.
5. Default mode is `-DryRun`; `-Apply` is required to make changes. Dry-run prints the full migration plan with old path → new path + new action.
6. Idempotent: re-running on already-migrated tasks is a no-op (detects existing `\Olympic Paints\…` location).

**Rollback:**

Each task's original XML is saved to `C:\Users\quint\.claude\heartbeats\_migration-backups\<timestamp>\<old-path-slug>.xml` before deletion. A `restore_tasks.ps1` companion script reverses the migration from these backups if needed.

### 3. `build_schedule_manifest.py` — manifest builder

**Location:** alongside `run_job.py`.

**Behavior:**

1. Enumerate all tasks under `\Olympic Paints\` via `Schedule.Service` COM.
2. For each task: read name, folder (= agent), triggers, next-run time, enabled state, last-run time, last-result from Task Scheduler.
3. Join with `C:\Users\quint\.claude\heartbeats\<job-id>.json` and the last 10 entries from `<job-id>.history.jsonl`.
4. Write a single `schedule_manifest.json` to `C:\Users\quint\workspace-dashboard\data\schedule_manifest.json`.
5. Self-scheduling: registers as `\Olympic Paints\PRISM\Build Schedule Manifest`, running hourly.

**Manifest schema:**

```json
{
  "generated_at": "2026-05-16T11:00:00+02:00",
  "tasks": [
    {
      "job_id": "pulse-daily-mailer",
      "name": "PULSE — Daily Mailer",
      "agent": "PULSE",
      "task_path": "\\Olympic Paints\\PULSE\\Daily Mailer",
      "enabled": true,
      "schedule_summary": "Weekdays 06:00 SAST",
      "next_run": "2026-05-19T06:00:00+02:00",
      "last_run": {
        "started_at": "2026-05-16T06:00:01+02:00",
        "finished_at": "2026-05-16T06:00:14+02:00",
        "duration_seconds": 13,
        "ok": true,
        "exit_code": 0,
        "summary": { "emails_sent": 4 }
      },
      "history": [ /* last 10 runs, oldest-first */ ],
      "heartbeat_status": "fresh"
    }
  ]
}
```

`heartbeat_status` values:

- `"fresh"` — heartbeat's `finished_at` is more recent than the task's most recent scheduled trigger time.
- `"stale"` — task was due to run (scheduled trigger time has passed) but no newer heartbeat exists. Grace window: 1 hour past expected trigger before flagging stale.
- `"missing"` — Task Scheduler reports a `LastRunTime` after migration completion, but no heartbeat file exists. Indicates the wrapper failed to write a heartbeat (anomaly).
- `"never_run"` — task exists but has no `LastRunTime` and no heartbeat (newly created, hasn't fired yet).

---

## Rollout plan (de-risked)

| Phase | Action | Stop-gate before next phase |
|---|---|---|
| 1 | Build `run_job.py` + unit tests. Pilot on **one** task: `Olympic — Sync Claude TODOs`. | Run 3 days. Heartbeats appear correctly. Manually force a failure and confirm Telegram alert fires. |
| 2 | Migrate PULSE tasks (7 tasks) in one batch via `migrate_tasks.ps1 -Apply`. | One full cycle (1 week) with no regressions. All 7 producing heartbeats. |
| 3 | Migrate remaining agents (HAVEN, PRISM, VAULT, KPI, geo map, etc.) in batches by agent. | All Olympic tasks live under `\Olympic Paints\<AGENT>\`. |
| 4 | Build + schedule `build_schedule_manifest.py` (hourly under `\Olympic Paints\PRISM\Build Schedule Manifest`). | `schedule_manifest.json` exists and is fresh. Ready to hand off to sub-project #2. |

## Testing

- **`run_job.py` unit tests:** success path, non-zero exit, killed subprocess, missing summary file, malformed summary JSON, very long stdout (truncation), heartbeat write atomicity, history rotation at 100 entries.
- **`migrate_tasks.ps1`:** dry-run on real tasks, verify no destructive operation without `-Apply`. Manually verify a single migration end-to-end before bulk runs.
- **`build_schedule_manifest.py`:** snapshot test against a known set of heartbeats; validate schema; verify `heartbeat_status` transitions across `fresh` / `stale` / `missing` / `never_run`.
- **End-to-end:** force a failure on the pilot task during Phase 1 and confirm: (a) Telegram alert, (b) heartbeat has `ok=false`, (c) manifest reflects it within the next hourly build.

## Open questions (defer to implementation plan)

- Exact final path for `run_job.py` and companion scripts inside the Olympic Paints workspace.
- How to bootstrap `run_job.py` itself — currently the only candidate for a task that runs from the OneDrive workspace; alternative is to mirror these scripts under `C:\Users\quint\.claude\scheduled-tasks\` (already exists per env paths).
- Whether existing `.bat` hooks that already update `health_check.py` status should also write `summary.json` for parity, or be left alone.

## Dependencies

- `python` on PATH (used by Task Scheduler today).
- Telegram bot token from `1.Projects/PULSE — Sales & Ops Manager/.env` (`TELEGRAM_BOT_TOKEN`).
- `truststore` and `--use-system-ca` patterns already required on this machine (per memory).
- `Schedule.Service` COM (Windows built-in).

## Out of scope reminder

This spec produces `schedule_manifest.json`. It does **not** produce a UI, an agent registry, or any consolidation of dashboards. Those are sub-projects #2 and #3.
