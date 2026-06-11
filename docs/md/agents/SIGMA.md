# SIGMA — Operations & Supply Chain

> Owns dispatch, factory floor, vehicle tracking, logistics, supply chain SOPs, and the Health & Safety NCR system.

---

## Domain

Everything that happens on the ground — trucks, factory, logistics, compliance. SIGMA ensures the physical operations side is documented, monitored, and reported.

---

## Owned systems

### Vehicle In-Out Report

Consolidates Netstar weekly Trip Report XLS files into a single master vehicle movement log, then publishes the Fleet Dashboard to GitHub Pages.

| Script | Purpose |
|---|---|
| `fetch_netstar_email.py` | Scans Outlook for `vigilcloud@netstar.co.za` emails, saves `.xls` to `Inbox/` |
| `process_vehicle_reports.py` | Consolidates Inbox XLS files → `VehicleInOut_*.xlsx` master |
| `gen_vehicle_dashboard.py` | GPS + HAVEN clocking → HTML → GitHub Pages |
| `run_vehicle_reports.bat` | Runs process + gen + health check hook in sequence |
| `striker_vehicle_health_check.py` | Validates last run, data freshness, sync — sends Telegram alert |

**Scheduled tasks (Monday):**
- `08:00` `\Olympic Paints\SIGMA\Fetch Netstar Email` — downloads XLS from Outlook
- `08:05` `\Olympic Paints\SIGMA\Process and Publish Vehicle Dashboard` — consolidates + publishes
- `08:15` `\Olympic Paints\SIGMA\Vehicle Health Check` — Telegram status to `8042233389`

**Register:** `register_sigma_vehicle_tasks.ps1` (run once as Administrator)

**Output:** `Inbox/Vehicle In Out Report.xlsx` (single master, always replaced)
**Archives:** Processed source files move to `Inbox/Archived/`
**Dashboard:** `https://flomaticauto.github.io/olympic-paints-vehicles/`
**SOP:** [2.Areas/9. Supply Chain/Logisitics/SIGMA_VEHICLE_REPORT_SOP.md](../2.Areas/9. Supply Chain/Logisitics/SIGMA_VEHICLE_REPORT_SOP.md)

```
2.Areas/9. Supply Chain/Logisitics/
├── Inbox/
│   ├── process_vehicle_reports.py
│   ├── Vehicle In Out Report.xlsx   ← master output
│   └── Archived/
└── OP Track & Driver Analitics/Scripts/  ← address mappings, generate_report module
```

---

### Health & Safety NCR Form Poller

Polls submissions from Albertina's H&S Non-Conformance Report form. New submissions → Notion H&S database + Telegram alert.

**Form ID:** `796c234d-51f0-43f7-a8c5-a1642415bf71` (live Supabase form, 16 fields)
**Scripts:**
- `2.Areas/12. Health and Safety/poll_ncr_submissions.py` — poller
- `weekly_hs_refresh.py` — weekly aggregation
- `rebuild_hs_report.py` — 8-tab navy HTML report, on-demand

**Runbook:** [hs-ncr-poller.md](../3.Resources/19. Runbooks/hs-ncr-poller.md)
**Criticality:** High — legal/compliance trail; missed NCRs are a liability.

---

### E-Commerce Logistics Cost

Monthly logistics cost ingest and reporting for the e-commerce delivery invoices.

| Script | Invocation |
|---|---|
| `ingest_logistics_invoices.py` | `python -m _scripts.ingest_logistics_invoices` |
| `logistics_cost_monthly.py` | `python -m _scripts.logistics_cost_monthly` |

**Location:** `2.Areas/1. Sales/5.Eccomerce/Delivery Invoices/_scripts/`
**Data format:** Parquet

---

### Merchandising Plan Heatmap

Rep × Date activity heatmap. Bands: 1 / 2 / 3 / 4+. Newest date leftmost.

**Entry points:**
- `2.Areas/3. Merchandising/build_merchandising_calendar.py` — Phase 1 calendar
- `1.Projects/AWS Data/build_merchandising_impact.py` — impact report

**Runbook:** [merchandising-plan.md](../3.Resources/19. Runbooks/merchandising-plan.md)

---

### Returns Dashboard (v2)

Vercel form → Supabase → static GitHub Pages dashboard.

**Active task:** `\Olympic Paints\Returns\OlympicPaints_BuildReturnsDashboard` — Mon–Fri 07:00
**Runbook:** [returns-watcher.md](../3.Resources/19. Runbooks/returns-watcher.md)

> Note: The old file-watcher + PDF-OCR pipeline is deprecated (2026-05-25). Do not use `scripts/_deprecated/`.

---

## Related

- Vehicle SOP: [2.Areas/9. Supply Chain/Logisitics/SIGMA_VEHICLE_REPORT_SOP.md](../2.Areas/9. Supply Chain/Logisitics/SIGMA_VEHICLE_REPORT_SOP.md)
- H&S area: [2.Areas/12. Health and Safety/](../2.Areas/12. Health and Safety/)
- Runbooks: [hs-ncr-poller.md](../3.Resources/19. Runbooks/hs-ncr-poller.md), [merchandising-plan.md](../3.Resources/19. Runbooks/merchandising-plan.md), [returns-watcher.md](../3.Resources/19. Runbooks/returns-watcher.md)
