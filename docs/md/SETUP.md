# VAULT Meeting Extraction — Setup & Execution Guide

## Current Status
- **Script:** `vault_meeting_extraction_local.py` ✓ Ready
- **n8n Workflow:** `vault_meeting_extraction_workflow.ts` (reference)
- **Notion Integration:** Verified schema, API patterns confirmed
- **Meeting Database:** 61 entries exist, all empty (no notes/documents)
- **Blocker:** `NOTION_API_TOKEN` environment variable not set

## Prerequisites

### 1. Set the Notion API Token

The token must be in your Windows environment. Choose one method:

**Option A: Environment Variable (.env file)**
```bash
# File: C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\.env
NOTION_API_TOKEN=ntn_your_token_here
```

**Option B: Windows System Environment Variable**
1. Press `Win + X` → Choose "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
   - Variable name: `NOTION_API_TOKEN`
   - Variable value: `ntn_xxxxxxxxxxxxx`
5. Click OK and restart your terminal

**Option C: PowerShell (Temporary for this session)**
```powershell
$env:NOTION_API_TOKEN = "ntn_your_token_here"
python vault_meeting_extraction_local.py
```

### 2. Verify Notion API Token

Your token should:
- Start with `ntn_` prefix
- Be obtained from: https://www.notion.so/my-integrations
- Have permission on: Meeting Database (ID: `247ff48d2bb18009979bd25bac9fe72e`)
- Have permission on: Task Database (ID: `247ff48d2bb1800ca00aca3b59f789eb`)

## Running the Extraction

### Test Run (Last 24 hours)
```bash
python vault_meeting_extraction_local.py
```

### Backfill Run (April 1, 2026 onwards)
```bash
python vault_meeting_extraction_local.py --backfill
```

## Data Issue Discovered

**Finding:** The Meeting Database contains 61 meeting entries, but **all are empty**:
- No meeting notes (Notes field is always empty)
- No linked documents (DOCUMENT DATABASE relation is always empty)
- Only field populated: Title (Name field)

**Action Required:**
1. Populate existing meetings with notes/action items, OR
2. Create new test meetings with content for verification

**Test Meeting Creation:** See instructions below.

---

## Creating Test Data

To verify the extraction works end-to-end, a test meeting with action items needs to be created.

### Current Issue
- Meeting Database `Area` field is a RELATION field (expects page IDs)
- Notion validation requires proper UUID format for relation IDs
- Hardcoded area IDs in script ("area-olympic", etc.) may need UUID format

### Workaround: Create Test Meeting Without Area

```python
import requests
import os

token = os.getenv('NOTION_API_TOKEN')
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

meeting = {
    "parent": {"database_id": "247ff48d2bb18009979bd25bac9fe72e"},
    "properties": {
        "Name": {"title": [{"text": {"content": "TEST: Q2 Planning"}}]},
        "Notes": {"rich_text": [{"text": {"content": "Action: Finalize budget by Friday\nTask: Review timeline by next week\nImplement: Cost analysis by EOD"}}]},
        "Date": {"date": {"start": "2026-04-22"}}
    }
}

r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=meeting)
if r.status_code == 200:
    print(f"Created: {r.json()['id']}")
else:
    print(f"Error: {r.status_code} - {r.text}")
```

---

## Scheduled Execution (Windows Task Scheduler)

Once verified, schedule the script to run daily at 7:00 AM:

### Step 1: Create Task Scheduler Entry
```powershell
# PowerShell (as Administrator)
$taskName = "VAULT-Meeting-Extraction"
$scriptPath = "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\vault_meeting_extraction_local.py"
$pythonPath = "C:\Users\quint\AppData\Local\Programs\Python\Python312\python.exe"

$trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal
```

### Step 2: Verify
```powershell
Get-ScheduledTask -TaskName "VAULT-Meeting-Extraction"
```

### Step 3: Monitor Logs
Logs are written to: `logs/vault_extraction_YYYY-MM-DD.log`

---

## Expected Output

When run successfully:

```
============================================================
VAULT Meeting Extraction Started (backfill=False)
============================================================
Querying meetings from 2026-04-21T00:00:00+00:00 to 2026-04-22T12:34:56+00:00
Found 5 total meetings, 2 in date range
Processing meeting: Q2 Planning (2026-04-22)
  - Found 3 action items
  Created task: Finalize budget (ID: task-001)
  Created task: Review timeline (ID: task-002)
  Created task: Analyze costs (ID: task-003)
============================================================
VAULT Extraction Complete
Processed: 1 meetings
Created: 3 tasks
  → Olympic: 3 tasks
============================================================
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `NOTION_API_TOKEN environment variable not set` | Add token to .env file or system environment |
| `Notion API error: 401` | Token is invalid or expired |
| `No new meetings to process` | All meetings in date range are empty (expected currently) |
| `Failed to create task: ValidationError` | Area field or relation ID format incorrect |
| `0 tasks created from N meetings` | Meeting notes are empty; populate with action items |

