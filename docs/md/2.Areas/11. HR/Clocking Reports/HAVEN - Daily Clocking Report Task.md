# Haven — Daily Clocking Report Responsibility

**Owner:** Haven  
**Frequency:** Every working day (morning)  
**Purpose:** Keep the master Clocking Report up to date with all biometric punch data — month-to-date and year-to-date.

---

## What this file is

The master Clocking Report (`Output/Clocking Report (DD.MM.YYYY).xlsx`) is the **single source of truth** for all clocking data. Every time it is updated, new data is added to it — nothing is lost. The date in the filename simply reflects when it was last updated.

It contains five sheets:
| Sheet | What it shows |
|---|---|
| Clocking Report | Every employee's clock-in / clock-out per day |
| Summary by Date | Daily headcounts, total hours, missing clock-outs |
| Summary by Department | Department-level totals across the full period |
| Missing Clock Out | All single-punch records (clock-in only) |
| Raw Data | Every source punch row — used for future merges |

---

## Daily task — step by step

### Step 1 — Check the Inbox
Open this folder:
```
2.Areas/11. HR/Clocking Reports/Inbox/
```
If there is a new `Transaction*.xlsx` file here, proceed to Step 2.  
If the Inbox is empty, there is nothing to do today.

### Step 2 — Find the current master file
Open this folder:
```
2.Areas/11. HR/Clocking Reports/Output/
```
Identify the most recent `Clocking Report (DD.MM.YYYY).xlsx` — this is the master file you will update.

### Step 3 — Run the update script
Open a terminal / Command Prompt and run:

```
python "2.Areas/11. HR/Clocking Reports/scripts/build_report.py" ^
  --input  "2.Areas/11. HR/Clocking Reports/Inbox/Transaction FILENAME.xlsx" ^
  --master "2.Areas/11. HR/Clocking Reports/Output/Clocking Report (DD.MM.YYYY).xlsx" ^
  --output "2.Areas/11. HR/Clocking Reports/Output/"
```

Replace:
- `Transaction FILENAME.xlsx` with the actual filename in Inbox
- `DD.MM.YYYY` in `--master` with the date on the current master file

The script will automatically:
- Merge the new punches into the accumulated master data (duplicates are ignored)
- Rebuild all five sheets over the full period
- Save a new file: `Clocking Report (TODAY'S DATE).xlsx`
- Move the previous master file to `Output/Archived/` — so only the latest file remains in `Output/`

### Step 4 — Verify the output
Open the new `Clocking Report (DD.MM.YYYY).xlsx` in Output and confirm:
- The period label at the top now includes today's new dates
- Row counts look correct (more rows than before)
- The Missing Clock Out sheet flags anything that needs follow-up with staff

### Step 5 — Move the processed inbox file
Move the Transaction file from `Inbox/` to `Processed/` so it is clear it has been handled.

---

## File paths (reference)

| Location | Path |
|---|---|
| Inbox (new files arrive here) | `2.Areas/11. HR/Clocking Reports/Inbox/` |
| Output (current master — one file only) | `2.Areas/11. HR/Clocking Reports/Output/` |
| Archived (previous masters) | `2.Areas/11. HR/Clocking Reports/Output/Archived/` |
| Processed (handled inbox files) | `2.Areas/11. HR/Clocking Reports/Processed/` |
| Script | `2.Areas/11. HR/Clocking Reports/scripts/build_report.py` |

---

## Notes

- The master file is **month-to-date and year-to-date** — it always contains all data from the start of the year.
- If a Transaction file covers dates already in the master, those punches are automatically deduplicated — no double-counting.
- The `Output/` folder should always contain **exactly one** Clocking Report file — the current master. If you see more than one, the older ones should be moved to `Output/Archived/`.
- If you are ever unsure which file is the master, take the one with the **latest date** in the filename.
- If the script fails, check that Python is installed and the `pandas` and `openpyxl` libraries are available (`pip install pandas openpyxl`).
