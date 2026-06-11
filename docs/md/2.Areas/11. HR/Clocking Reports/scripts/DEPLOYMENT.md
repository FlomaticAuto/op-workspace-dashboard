# HAVEN Clocking Report Watcher — Deployment Guide

## Status
✅ **Script is ready.** `haven_watcher.py` has been created and tested. Dependencies installed.

## What it does
- Monitors `Inbox/` for new Excel files
- Automatically runs `build_report.py` with `--master` mode when a file is detected
- Logs all activity to `haven_watcher.log`
- Sends completion notifications to Quintus via Slack

## Prerequisites

### 1. Python Dependencies
Already installed:
- `watchdog` (v6.0.0)
- `requests` (already present)

Verify:
```bash
python -c "import watchdog, requests; print('OK')"
```

### 2. Slack Credentials
Set as Windows environment variables:

**SLACK_TOKEN:**
1. Go to Slack workspace settings
2. Create or use an existing bot token with `chat:write` scope
3. Copy the token

**QUINTUS_SLACK_ID:**
1. In Slack, right-click Quintus's profile → Copy user ID (e.g., `U0123ABC456`)

Then set these as environment variables:
```bash
setx SLACK_TOKEN "xoxb-your-token-here"
setx QUINTUS_SLACK_ID "U0123ABC456"
```

Restart any open terminals after setting these.

Verify:
```bash
echo %SLACK_TOKEN%
echo %QUINTUS_SLACK_ID%
```

### 3. Master File
The watcher checks that `Clocking Report YTD.xlsx` exists in `Output/` before processing.

**If the master file is missing:**
- The watcher will start but fail on first report
- You must manually create the YTD file first
- After the first successful run, the script maintains it automatically

## Deployment Options

### Option A: Windows Task Scheduler (Recommended for persistent background running)

1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task:
   - **Name:** `HAVEN Clocking Report Watcher`
   - **Trigger:** At startup
   - **Action:** Start a program
     - Program: `C:\path\to\python.exe`
     - Arguments: `"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts\haven_watcher.py"`
     - Start in: `C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts\`
3. Check "Run whether user is logged in or not" (if running as a service)
4. Enable task

Logs will go to `haven_watcher.log` regardless of how it's launched.

### Option B: Manual/Testing
```bash
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts"
python haven_watcher.py
```

Runs in foreground. Press Ctrl+C to stop.

### Option C: PowerShell Background Job
```powershell
Start-Job -ScriptBlock {
    python "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts\haven_watcher.py"
}
```

## Verification

### Check logs
```bash
cat "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts\haven_watcher.log"
```

### Test file detection
Drop a test Excel file into `Inbox/`:
```bash
echo test > test.xlsx
```
The watcher should detect it, attempt to process it, and log the result.

### Check Slack
When a report is processed, you should receive a Slack DM from the watcher showing:
- Success/failure status
- File processed
- Actions taken

If no Slack message arrives, check:
1. Environment variables are set (`echo %SLACK_TOKEN%`)
2. Token has `chat:write` scope
3. Bot is in Quintus's workspace

## Stopping the Watcher

If running in Task Scheduler:
- Open Task Scheduler → disable the task
- Or: kill the Python process (`taskkill /im python.exe`)

If running manually:
- Press Ctrl+C in the terminal

## Logs Location
```
C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\2.Areas\11. HR\Clocking Reports\scripts\haven_watcher.log
```

Logs include:
- Startup/shutdown messages
- File detection events
- Processing status (success/failure)
- Error details and timeouts
- Slack notification attempts
