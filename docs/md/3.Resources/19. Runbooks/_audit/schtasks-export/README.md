# schtasks-export/

Source of truth for every Olympic-Paints-related Windows scheduled task on the canonical machine (quint's box as of 2026-05-24).

The 2026-05-23 install audit on the Administrator box found that **30 of 63 scheduled tasks have no committable registrar script in the repo** — they were registered ad-hoc over time on quint's machine via `schtasks /create` or the Task Scheduler GUI, and would be lost if that machine died. This folder closes that gap: an XML dump per task, plus an `_index.csv` summary, so the tasks can be regenerated anywhere.

## How to refresh

On quint's box (or any machine that has the full task set), from elevated PowerShell:

```powershell
cd "$env:USERPROFILE\OneDrive\1.Projects\1.Olympic Paints\3.Resources\19. Runbooks\_audit"
powershell -NoProfile -ExecutionPolicy Bypass -File .\export_schtasks.ps1
```

Then commit the new/changed XML files. OneDrive will sync them to other machines.

## Files

- `_index.csv` — file → TaskPath / TaskName / State, regenerated on every export
- `<safe-name>.xml` — one file per task, full Task Scheduler XML definition

Filenames are derived from the task path by replacing path separators with `__` and spaces with `_`. Example: `\Olympic Paints\PRISM\OlympicPaints_KPI_Dashboard_Update` → `Olympic_Paints__PRISM__OlympicPaints_KPI_Dashboard_Update.xml`.

## What's next

Once the XMLs land here, the next Claude session can:
1. Read `_index.csv` to see what exists
2. Parse each XML to extract trigger / action / settings
3. Group by domain (PRISM, SIGMA, STRIKER, etc.) and generate one `register_*.ps1` per group
4. Commit those registrars so any machine can rebuild the full task set with one script execution

## Why XML, not just `schtasks /create` commands

The XML is the lossless representation. `schtasks /create` flags can't express everything Task Scheduler supports (multi-trigger tasks, idle conditions, repetition with bounded duration, etc.). Round-tripping through XML keeps every setting intact.
