# Zoho Meetings Pull — Olympic Paints

Direct Zoho CRM REST API pull of Meetings (Events module) and linked Accounts.
Replaces the AWS S3 → OneDrive `Meetings_Report_AWS.xlsx` pipeline.

> **Migration note:** Phase 1 (this build) runs **alongside** the AWS pipeline. PULSE keeps reading the existing xlsx. Once parity is confirmed (~5 business days), Phase 2 will switch PULSE's path from `Meetings_Report_AWS.xlsx` to `Meetings_Report.xlsx` (this script's output) and the AWS pipeline gets switched off.

---

## One-time setup

### 1. Register a Self Client in Zoho

1. Sign in to https://api-console.zoho.com (or `.eu` if your CRM is `crm.zoho.eu`) **as the CRM Admin** — sales reps' personal accounts will only see their own meetings.
2. **Add Client → Self Client → Create → OK**.
3. Copy **Client ID** and **Client Secret** somewhere safe.
4. **Generate Code** tab:
   - Scope: `ZohoCRM.modules.events.READ,ZohoCRM.modules.accounts.READ,ZohoCRM.modules.notes.READ,ZohoCRM.modules.leads.READ,ZohoCRM.settings.READ,ZohoCRM.users.READ`
   - Duration: 10 minutes (max)
   - Click Create → copy the grant code

### 2. Configure `.env`

```bash
cp .env.template .env
```

Edit `.env`, paste in:
```
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=XXXXXXXXXXXXXXXXXXXXXX
ZOHO_DC=com                    # or eu / in / com.au
```

### 3. Exchange grant code for refresh token (one-shot)

```bash
pip install requests python-dotenv pandas pyarrow openpyxl
python zoho_auth.py <PASTE_GRANT_CODE_HERE>
```

If it succeeds, `.env` gets the `ZOHO_REFRESH_TOKEN` filled in. The grant code is now spent — that's OK, you'll never need another one. The refresh token is long-lived.

### 4. Smoke-test the client

```bash
python zoho_client.py
```

Should print the first 20 field API names of the Events module. If you see anything from `Event_Title` onward you're authenticated and good.

---

## Running

### Full backfill (every meeting, every account)

```bash
python pull_meetings.py
```

Takes ~1-5 minutes depending on how many meetings exist. Writes:
- `data/meetings.parquet`
- `data/accounts.parquet`
- `data/Meetings_Report.xlsx` (compatibility format)

### Incremental — only what changed recently

```bash
python pull_meetings.py --since 7d
python pull_meetings.py --since 2026-05-01
```

Uses Zoho's `If-Modified-Since` header — much faster for daily/hourly refreshes.

### Discover field API names

If you have custom fields you want to extract (e.g. `Note_Content`, `Cycle_Week`), run:

```bash
python pull_meetings.py --inspect-fields
```

Find the API name of the custom field you want, then add it to the `EVENT_FIELDS` list at the top of `pull_meetings.py`.

---

## Files

| File | Purpose |
|---|---|
| `.env.template` | Copy to `.env` and fill in credentials |
| `.env` | **Never commit** — real credentials live here |
| `zoho_auth.py` | One-shot grant code → refresh token exchange |
| `zoho_client.py` | Reusable Zoho API client (auto token refresh, pagination, rate-limit backoff) |
| `pull_meetings.py` | Main pull script for Events (meetings). Run on a schedule. |
| `pull_leads.py` | Pull every Lead in the CRM (auto-discovers custom fields). Writes `data/leads.parquet`. |
| `data/` | Output parquet + xlsx files (gitignored) |
| `logs/` | Run logs (gitignored) |

---

## Scheduling

For Phase 1 (parallel to AWS pipeline):

```powershell
# Daily refresh at 06:15 — runs before PULSE Daily Mailer at 06:30
schtasks /Create /SC DAILY /ST 06:15 /TN "Zoho Meetings Pull" `
  /TR "python.exe `"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings\pull_meetings.py`" --since 7d" `
  /F
```

For true real-time use cases (e.g. dashboard "refresh now" button), shell out to the same script with `--since 1d` and read the parquet.

### Leads

```powershell
# Daily incremental at 06:10 — runs before the meetings pull
schtasks /Create /SC DAILY /ST 06:10 /TN "Zoho Leads Pull" `
  /TR "python.exe `"C:\Users\quint\OneDrive\1.Projects\1.Olympic Paints\1.Projects\AWS Data\zoho_meetings\pull_leads.py`" --since 7d" `
  /F
```

First run: drop `--since 7d` to do a full backfill, then revert to incremental on the schedule.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No refresh_token in response` from `zoho_auth.py` | Grant code expired (>10 min) or already used | Generate a new grant code in api-console.zoho.com |
| `Token refresh failed` | Refresh token revoked or wrong DC | Check `ZOHO_DC` matches your CRM URL; regenerate Self Client if revoked |
| Sees only some meetings | Authenticated as a non-admin | Re-run the API Console flow as Admin |
| `204 No Content` | No records match — usually normal on first run with `--since` | Check date filter; first ever run should use no filter |
| Custom field missing from output | Not in `EVENT_FIELDS` list | Run `--inspect-fields`, find the API name, add to the list |
| Pagination loop forever | Bug — `more_records` not respected | Check `zoho_client.py` `iter_records` — set `MAX_RETRIES_PER_CALL` lower temporarily |

---

## What this replaces

The existing AWS pipeline (Zoho → S3 → OneDrive) drops `Meetings_Report_AWS.xlsx` multiple times per business day. That file is consumed by every PULSE Task Scheduler job. Once Phase 2 is greenlit:

1. Confirm parity between `Meetings_Report.xlsx` (this script) and `Meetings_Report_AWS.xlsx` (AWS) for ~5 business days.
2. Point PULSE's `MEETINGS_PATH` config at `Meetings_Report.xlsx`.
3. Disable the AWS Make/n8n scenario that drops the old file.
4. Optionally: migrate PULSE consumers to `meetings.parquet` for the perf win.
