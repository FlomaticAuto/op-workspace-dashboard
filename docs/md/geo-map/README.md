# Olympic Paints — Geo Map

Interactive Leaflet map of customer accounts, sales-rep coverage, stockist locations, and recent merchandising visits across Limpopo, Gauteng, Free State, Mpumalanga, and Botswana.

**Live URL** (after Vercel link-up): https://olympic-paints-geo-map.vercel.app

## Layers

| Layer | Source | Notes |
|---|---|---|
| Customer accounts | `Accounts Store Status.xlsx` joined to `Sales_Invoices_All.parquet` | Colour by rep / revenue / area; size by NET revenue in the selected window |
| Visit heatmap | `Meetings_Report.xlsx` (Zoho check-ins) | Density scaled to the selected time window |
| Stockist locator | Filter on `Status` = Trading / Active / Stockist | Public-facing view |
| Rep overlap zones | Computed client-side from last 90 days of visits | Highlights stores visited by 2+ different reps within an adjustable 25–150 km radius (default 75 km) |

## Time windows

A single dropdown drives both revenue display and heatmap density:

| Option | Revenue scope | Heatmap window |
|---|---|---|
| This quarter | Current FY quarter | 91 days |
| This financial year | FY-to-date (Mar 1 →) | 365 days |
| Trailing 12 months *(default)* | Rolling 365 days | 365 days |
| Since Mar 2024 | Full parquet history | 2 years (visit dataset cap) |

Olympic Paints FY runs **March 1 → end of February**.

## Update flow

1. Run the data prep script:
   ```
   python scripts/build_geo_data.py
   ```
   This rebuilds `data/accounts.json` (~460 points) and `data/visits.json` (~1.3k visits).
2. Commit and push to `main`. Vercel auto-deploys.

## Files

```
index.html              Leaflet map page (static, no framework)
data/accounts.json      Customer geocodes + revenue
data/visits.json        Merchandising check-in coords
scripts/build_geo_data.py   Rebuilds both JSON files
logo.jpg                Olympic Paints brand mark
```

## Stack

- Leaflet 1.9.4 (map)
- leaflet.markercluster 1.5.3 (clustering)
- leaflet.heat 0.2.0 (heatmap)
- CartoDB Voyager / Dark Matter (base tiles)
- Barlow / Barlow Condensed (Google Fonts)

No build step. No framework. Static HTML.

## Data caveats

- 460 of 695 accounts have parseable lat/lng coordinates. The remaining accounts are either missing geo data or have invalid coordinate strings.
- Revenue figures are **NET of VAT**, signed by document type (`INVOICE +1`, `CRNOTE −1`).
- Sales-account join is `Account Site → accno`. ~390 accounts have revenue data; the rest map at zero revenue.
- Visit heatmap covers the **last 90 days only** to keep the file small and the gradient meaningful.
