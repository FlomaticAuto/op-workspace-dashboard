# Monthly Reporting — Design Spec
**Date:** 2026-05-27  
**File:** `clocking/index.html`  
**Status:** Approved

---

## Overview

Add a **Monthly Reporting** tab to the Clocking Report dashboard (`/d/clocking`). It mirrors the existing Weekly Hours tab in every respect — same filters, same table structure, same Excel export quality — but aggregates hours into calendar-month buckets rather than Wed–Tue week buckets. The user selects any arbitrary date range with From/To date pickers; the tab automatically derives which calendar months are covered and renders one column per month.

No backend changes are required. All aggregation is done client-side from the existing `wk_detail_table` data (which already stores day-level hours per week).

---

## 1. Nav Tab

Insert a new `<button onclick="showTab('monthly', this)">Monthly Reporting</button>` between the **Weekly Hours** and **Missing Clock Out** buttons in the `<nav>` strip.

Update the "How to use this report" `<details>` panel to include:
> **Monthly Reporting** — Per-employee hours aggregated into calendar months. Select any date range with the From/To pickers. Export to Excel for month-end payroll or trend analysis.

---

## 2. Tab Content (`#tab-monthly`)

### 2a. Info note
```
Hours are NET of 45 min/day break. Weeks run Wed–Tue;
hours for weeks spanning a month boundary are split by day.
Values in decimal hours (e.g. 168.0 = 168 h). Miss YTD = total missing clock-outs YTD.
```

### 2b. Filter controls (identical to Weekly Hours)
Four controls in a `.controls` row:
| Control | Element | Behaviour |
|---|---|---|
| Search | `#mo-search` text input | Filter by name or employee ID (case-insensitive) |
| Employer | `#mo-emp` select | All / Olympic Paints / Primeserve |
| Miss status | `#mo-miss` select | Any / Has missed / No missed |
| Min hours | `#mo-min-hrs` select | Any / ≥ 1h / ≥ 40h / ≥ 80h / ≥ 120h |

Any change to these controls re-renders the table without clearing the date range.

### 2c. Date-range bar (`.mo-filter-bar`)
Layout (left → right):
1. Label "DATE RANGE"
2. Four quick-preset buttons: **This Month**, **Last Month**, **Last 3 Months**, **YTD**
3. Divider
4. "From" label + `#mo-from` date input
5. "To" label + `#mo-to` date input
6. **Apply** button (`applyMo()`) — triggers aggregation and re-render
7. (right-aligned) Meta string: `X months · Y employees · Z.Zh total`
8. **⬇ Export Excel** button (`exportMo()`)

Clicking a quick-preset populates the From/To inputs and immediately calls `applyMo()`.

**Default state on tab open:** "Last Month" preset is applied automatically so the tab always loads with data visible.

### 2d. Meta row (`#mo-meta`)
Updates after each `applyMo()` / filter change:
```
Showing 102 employees (OP 74 · PS 28) · 3 months: Mar 2026, Apr 2026, May 2026 · visible total 23 735.6 h
```

### 2e. Table (`#mo-table-wrap` → `#mo-table`)

**Header — two rows:**
- Row 1: `Employer` (rowspan 2) | `ID` (rowspan 2) | `Name` (rowspan 2) | one `<th>` per month (navy bg, yellow text, yellow bottom border, e.g. "Mar 2026") | `Total` (rowspan 2, dark navy bg, yellow text) | `Miss YTD` (rowspan 2)
- Row 2: one `Hours` sub-header per month

**Body — one row per employee:**
- `OP` / `PS` badge (coloured)
- Employee ID (small, muted)
- Name (bold)
- One decimal-hours cell per month (blue-tinted bg; blank/`—` if zero)
- Total across all visible months (darker blue-tinted bg, bold)
- Miss YTD (yellow-tinted if > 0, green-tinted if 0)

**Empty state:** If no date range applied yet or no matching employees, show a centred italic message.

---

## 3. Aggregation Logic

### 3a. Month list derivation
Given `fromDate` and `toDate` (JS `Date` objects):
1. Walk month-by-month from `(fromDate.year, fromDate.month)` to `(toDate.year, toDate.month)`.
2. Produce array `moMonths`: `[{ key: 'YYYY-MM', label: 'Mar 2026' }, …]`.

### 3b. Per-employee monthly hours
For each employee row `r` in `D.wk_detail_table`:
```
moRow = { employer, id, name, missYTD, months: {} }
for each week index i in D.wk_weeks:
  weekStart = parseDate(D.wk_weeks[i].start)   // Wednesday
  for each day d of WK_DAYS (offsets 0–6):
    actualDate = weekStart + d days
    if actualDate >= fromDate AND actualDate <= toDate:
      monthKey = YYYY-MM of actualDate
      moRow.months[monthKey] = (moRow.months[monthKey] || 0) + r.weeks[i].days[d]
```

`D.wk_weeks[i].start` is a `YYYY-MM-DD` string.  
`WK_DAYS = ['Wed','Thu','Fri','Sat','Sun','Mon','Tue']` → offsets 0–6.

### 3c. State variables
```js
let moFromDate = null;   // Date | null
let moToDate   = null;   // Date | null
let moMonths   = [];     // [{ key, label }]
let moAggRows  = [];     // aggregated rows (full set, pre-filter)
```

`applyMo()` recomputes `moMonths` and `moAggRows`, then calls `filterMo()`.  
`filterMo()` applies the four filter controls to `moAggRows`, then calls `renderMo()`.

---

## 4. Excel Export (`exportMo()`)

Uses the existing ExcelJS library (already loaded on the page).

**Workbook metadata:** creator `Olympic Paints — HR`, sheet name `Monthly Hours`, tab colour yellow.

**Sheet structure:**

| Row | Content |
|---|---|
| 1 | Title: `OLYMPIC PAINTS — Monthly Hours Report` (full-width merge, navy bg, yellow bold text) |
| 2 | Subtitle: `Period: {from} – {to}  \|  Generated: {date}  \|  Employer: {filter}  \|  Employees: {n}` |
| 3 | *(blank spacer)* |
| 4 | Column headers: Employer / ID / Name / [month labels…] / Total / Miss YTD |
| 5+ | Data rows (one per employee) |
| Last | Totals row: navy bg, yellow bold, column sums per month + grand total |

**Column widths:** Employer 10, ID 12, Name 28, each month 14, Total 12, Miss YTD 12.

**Frozen panes:** columns A–C (xSplit: 3), rows 1–4 (ySplit: 4).

**Print settings:** landscape, fit-to-1-page-wide, A4.

**Footer:** `&LOlympic Paints &C Monthly Hours Report &R Page &P of &N`

**Filename:** `Olympic_Paints_Monthly_Hours_{from}_{to}.xlsx`  
Example: `Olympic_Paints_Monthly_Hours_2026-03-01_2026-05-27.xlsx`

---

## 5. Styling

Reuse all existing CSS classes. New classes needed:

| Class | Purpose |
|---|---|
| `.mo-filter-bar` | Date-range bar (same structure as `.wk-filter-bar`) |
| `.mo-preset` | Quick-preset buttons (same as `.wk-preset`) |
| `#mo-table-wrap` | Scrollable table container (same as `#wk-table-wrap`) |
| `#mo-meta` | Meta text below the date bar |

No new tokens or colours. All month-column cells use the same blue-tint pattern as week-day cells in Weekly Hours.

---

## 6. Edge Cases

| Scenario | Behaviour |
|---|---|
| No weeks overlap the selected date range | Empty state message: *"No data found for the selected date range."* |
| Employee has zero hours in a month | Cell shows `—` (not `0`) |
| Date range spans only one month | Table renders with a single month column |
| `toDate` < `fromDate` | `Apply` button shows `alert('End date must be after start date.')` and does nothing |
| Employee has no data in `wk_detail_table` for any week | Row excluded (same as Weekly Hours — `minH > 0` filter handles this, or they show as all-blank rows) |

---

## 7. Files Changed

| File | Change |
|---|---|
| `clocking/index.html` | All changes. CSS additions (~40 lines), HTML additions (~60 lines), JS additions (~250 lines). No other files change. |

---

## 8. Out of Scope

- No per-month missed clock-out count (only Miss YTD, same as Weekly Hours)
- No monthly trend chart (can be added in a future iteration)
- No backend changes to `push_clocking_stats.py` or the report generator
- No change to other tabs
