# Decommissioning the AWS Meetings Pipeline — Final Steps

> **Status as of 2026-05-13:** Every code consumer has been migrated to the direct Zoho REST API. The two AWS xlsx files have been moved to `3.Resources/16.Sales and Other data/Zoho/_DEPRECATED_use_zoho_meetings_API_instead/`. The Task Scheduler entry runs the API pull weekdays at 06:15.
>
> **What's left:** disable the upstream automations that *create* the AWS files. Until you do this, they'll keep writing to the (now-empty) Zoho folder. The new files won't break, but you'll waste compute + Zoho quota and confuse future readers.

---

## What "the AWS pipeline" actually is

Three independent components, each running on a schedule:

1. **Zoho scheduled report export** — Inside Zoho CRM there are two saved Reports configured to export on a schedule:
   - "Meetings Report AWS"
   - "Meetings Report AWS Merchandising"

   These export to **S3 bucket `op-sales-share-raw-layer/Zoho_Reports/`** as CSV.

2. **S3 → OneDrive sync** — Something (probably Make.com or n8n; possibly a manual download in some cases) picks up the CSV from S3 and writes the xlsx into our OneDrive folder.

3. **QuickSight data sources** *(adjacent, not blocking — see "Optional" below)* — There are archived QuickSight manifests at `1.Projects/AWS Data/Archive/OP_Zoho_Store_Visit_Report*.json` that point at the same S3 CSV. If QuickSight is still active and consuming those, leave the S3 export running until QuickSight is also migrated/retired.

---

## Step-by-step shutdown

### 1. Disable the Zoho scheduled report (the source)

1. Log in to Zoho CRM **as the admin who originally set this up** (probably Sejal or yourself).
2. Navigate to **Reports** → **All Reports** → search for "Meetings Report AWS" and "Meetings Report AWS Merchandising".
3. For each report, open it → click the **⋯** (more) menu → **Schedule Report**.
4. Click **Delete Schedule** (or **Disable**). Do NOT delete the report itself — leaving it around lets us restart easily if we ever need to.
5. Repeat for the merchandising sibling.

### 2. Disable the S3 → OneDrive automation

This is the layer that moves data from `op-sales-share-raw-layer/Zoho_Reports/` to our OneDrive folder. Where to look:

- **Make.com** — sign in, find the scenario named something like "Olympic Paints — Zoho S3 to OneDrive". Toggle it **OFF**. Do not delete; leaving it disabled means we can re-enable if needed.
- **n8n** — same idea, find the workflow, deactivate.
- **AWS Lambda / EventBridge** — if there's a Lambda hooked to an S3 PUT event on the bucket, disable the trigger.

If you don't know which platform owns this, check:
- Your Make.com dashboard for scenarios touching `Olympic Paints`
- The `op-sales-share-raw-layer` bucket's notification configuration

### 3. (Optional) S3 bucket retention

The bucket `op-sales-share-raw-layer/Zoho_Reports/` will stop receiving new CSVs once Step 1 is done. The existing historical CSVs can stay as an archive — they're harmless. If you want to clean up:

```bash
aws s3 ls s3://op-sales-share-raw-layer/Zoho_Reports/
# Then delete or move to a Glacier tier if storage cost matters
```

### 4. (Optional) Update QuickSight if still in use

If anything in QuickSight is still pointing at the S3 CSV, it will start showing stale data once Step 1 is done. The two archived manifests at `1.Projects/AWS Data/Archive/OP_Zoho_Store_Visit_Report*.json` are *probably* dead — confirm with whoever last touched QuickSight.

---

## Rollback plan (if something breaks)

Phase the shutdown:

1. **First week** — leave the AWS pipeline running but rename the .xlsx outputs (e.g. `_DEPRECATED_Meetings_Report_AWS.xlsx`) so nothing reads them. Monitor PULSE, dashboards.
2. **Second week** — if no errors, disable the Make.com / S3 sync (Step 2 above).
3. **Third week** — disable the Zoho scheduled export (Step 1).

If anything regresses:
- The deprecated xlsx files are still at `3.Resources/16.Sales and Other data/Zoho/_DEPRECATED_use_zoho_meetings_API_instead/`. You can move them back to the original location to temporarily restore the old data source.
- Each migrated consumer has an inline comment `# Migrated 2026-05-13 from Zoho/Meetings_Report_AWS.xlsx` — easy to grep, easy to revert if you really need to.

---

## How to verify the new pipeline is working

```powershell
# Check the scheduled task ran this morning
schtasks /Query /TN "Olympic Paints - Zoho Meetings Pull" /V /FO LIST | findstr "Last Run"

# Look at the log
notepad "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings\logs\scheduled.log"

# Confirm the xlsx is recent
dir "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings\data"
```

The xlsx mtime should be today (or this morning), and the row count should be slightly higher than yesterday as new meetings come in.

If something fails, run the pull manually to see the error:

```powershell
cd "C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings"
python pull_meetings.py --since 7d
```
