# Runbook — [Job Name]

> **Last verified:** YYYY-MM-DD
> **Owner:** Quintus
> **Criticality:** [low | medium | high]   *(high = customer/rep facing, silence = incident)*

---

## Purpose

One paragraph. What does this job exist to do, and why does it matter to the business? If this job stopped running for a week, who would notice and what would break?

---

## How it runs

- **Trigger:** [Windows Task Scheduler job name | folder watcher | manual | cron | webhook]
- **Schedule:** [e.g. weekdays 06:00 SAST | every 2h | Mon 08:00]
- **Host machine:** [Quintus laptop | Vercel | GitHub Actions | other]
- **Entry point:** `path\to\script.py` (absolute path from repo root)
- **Invocation:** exact command line, e.g. `python -m scripts.pulse_daily_mailer` *(memory rule: PULSE scripts must use `-m`)*
- **Environment:** which `.env` is loaded, which env vars are required

---

## Inputs

| Source | Path / URL | Format | Refresh cadence |
|---|---|---|---|
| Example | `Output/foo.parquet` | parquet | daily |

What this job *reads*. If any input is missing or stale the job will either crash or produce wrong output — document which.

---

## Outputs

| Destination | Path / URL | Format | Consumer |
|---|---|---|---|
| Example | `Output/foo.html` | HTML | GitHub Pages |

What this job *produces* and who consumes it. If the output doesn't appear, this is your symptom.

---

## Known failure modes

Each failure mode = **Symptom → Cause → Fix**. Add new ones from incident postmortems.

1. **Symptom:** [what you observe]
   **Cause:** [root cause]
   **Fix:** [exact remediation steps]

2. **Symptom:** ...

---

## Logs

- **Primary log:** `C:\Users\quint\.claude\logs\<job>\YYYY-MM-DD.log`
- **Task Scheduler last run code:** `Get-ScheduledTask -TaskName "<name>" | Get-ScheduledTaskInfo`
- **Telegram delivery confirmation:** chat `8042233389`, search for job name

Where to look first when investigating. Reminder: logs must live **outside OneDrive** for scheduled Python jobs (OneDrive sync hangs network calls → -1073741510).

---

## Manual run

Exact commands a human types to re-fire this job, in order. Copy-pasteable.

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\<folder>"
python script.py --flag value
```

If the job has multiple stages, list each. If a dry-run mode exists, note it.

---

## Recent incidents

Append-only log. Newest first. Each entry: date, what broke, what was learned.

- **YYYY-MM-DD** — [one line on what happened and the fix]

---

## Related

- Code: [link to script]
- Memory: [[memory_file_name]]
- Upstream job: [runbook link if this consumes another job's output]
- Downstream job: [runbook link if another job consumes this one's output]
