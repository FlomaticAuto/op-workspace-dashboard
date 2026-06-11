# AI Workload Monitor + Nightly Report — Replication Runbook

Use this to replicate the perfmon collector and nightly HTML report
(published to GitHub Pages) onto another PC. Each PC should publish
to its **own** GitHub repo — otherwise two PCs overwrite each other's
`index.html` every night.

---

## Prerequisites on the new PC

- [ ] Windows 10/11
- [ ] PowerShell 5.1+ (built-in on Windows 11)
- [ ] Administrator account
- [ ] Git for Windows installed — `winget install Git.Git`
- [ ] GitHub CLI installed — `winget install GitHub.cli`
- [ ] OneDrive synced (so the scripts in
      `C:\Users\<you>\OneDrive\AIWorkloadReport\` are available).
      Otherwise copy these three files manually:
  - `Setup-AIWorkloadMonitor.ps1`
  - `Setup-ReportAutomation.ps1`
  - `Generate-AIReport.ps1`

---

## One-time GitHub auth (per PC, NOT as admin)

```powershell
gh auth login
# - Pick: github.com
# - Pick: HTTPS
# - Pick: Login with a web browser
# - Authenticate as the GitHub account that should own the per-PC repo
gh auth status     # confirm "Active account: true"
```

**Multi-account note:** if you have multiple gh accounts on this PC,
note which username should publish the report. The nightly script
pulls that user's token explicitly via
`gh auth token --user <username>`.

---

## Pick a repo name for THIS PC

Convention: `ai-workload-report-<pc-shortname>`

Examples:
- `ai-workload-report-laptop`
- `ai-workload-report-dev-tower`
- `ai-workload-report-qx`

Live URL will be `https://<owner>.github.io/<repo-name>/`.

---

## Edit two scripts before running

In `C:\Users\<you>\OneDrive\AIWorkloadReport\Setup-ReportAutomation.ps1`:

```powershell
$RepoOwner = "FlomaticAuto"           # GitHub account/org
$RepoName  = "ai-workload-report"     # <-- change to your unique name
```

If the gh user that should push is **not** `FlomaticAuto`, also edit
`Generate-AIReport.ps1`:

```powershell
$token = gh auth token --user FlomaticAuto
# -> replace FlomaticAuto with your gh username
```

---

## Step 1 — Install the perfmon collector

Right-click PowerShell → **Run as Administrator**

```powershell
cd "C:\Users\<you>\OneDrive"
.\Setup-AIWorkloadMonitor.ps1
```

Expected: `[OK] Monitoring STARTED` and a scheduled task
`Start AI Workload Monitor` registered under `\Flomatic\`.

Verify:
```powershell
logman query AI_Workload_Monitor   # Status: Running
```

---

## Step 2 — Create the report repo + nightly task

Same elevated PowerShell:

```powershell
cd "C:\Users\<you>\OneDrive\AIWorkloadReport"
.\Setup-ReportAutomation.ps1
```

Expected:
```
[OK] Repo created
[OK] Cloned
[OK] Initial commit pushed
[OK] GitHub Pages enabled
[OK] Generator copied to C:\Flomatic\Generate-AIReport.ps1
[OK] Task registered: \Flomatic\Generate AI Workload Report
```

---

## Step 3 — Run once to verify

```powershell
& "C:\Flomatic\Generate-AIReport.ps1"
```

Expected last lines:
```
[HH:MM:SS] Pushed.
[HH:MM:SS] Done in ~10-15s.
```

Visit `https://<owner>.github.io/<repo-name>/`
(GitHub Pages may take 30-90s to publish the first time.)

---

## Step 4 — Confirm the nightly schedule

```powershell
Get-ScheduledTask -TaskPath "\Flomatic\" `
    -TaskName "Generate AI Workload Report" |
    Get-ScheduledTaskInfo | Select LastRunTime, NextRunTime
```

`NextRunTime` should be today (or tomorrow) at **23:55:00**.

---

## Gotchas the scripts already handle — DO NOT "fix" these

- The perfmon collector writes a file literally named
  `AI_Monitor_%datetime%.blg` (logman doesn't expand the placeholder).
  The nightly script renames it to a real timestamp before restarting
  the collector — **don't delete the rename block**.
- Scheduled task trigger uses an explicit `[datetime]` object, not the
  string `"23:55"`, because the string form can be misparsed to a
  different hour on some locales.
- `git push` uses an in-URL OAuth token from gh's keyring so it
  survives Windows Credential Manager caching the wrong account.

---

## Routine commands

Trigger a report manually:
```powershell
Start-ScheduledTask -TaskPath "\Flomatic\" `
    -TaskName "Generate AI Workload Report"
```

Stop monitoring (e.g. before maintenance):
```powershell
logman stop AI_Workload_Monitor
```

Convert latest `.blg` to CSV by hand:
```powershell
relog "C:\PerfLogs\AI_Workload\*.blg" -f CSV `
      -o "C:\PerfLogs\AI_Workload\export.csv"
```

---

## Uninstall on a PC

```powershell
logman stop AI_Workload_Monitor
logman delete AI_Workload_Monitor
Unregister-ScheduledTask -TaskPath "\Flomatic\" `
    -TaskName "Start AI Workload Monitor" -Confirm:$false
Unregister-ScheduledTask -TaskPath "\Flomatic\" `
    -TaskName "Generate AI Workload Report" -Confirm:$false
Remove-Item C:\PerfLogs\AI_Workload -Recurse -Force
Remove-Item C:\Flomatic -Recurse -Force
# (Optional) delete the GitHub repo:
gh repo delete <owner>/<repo-name> --yes
```
