# Monthly Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Monthly Reporting" nav tab to `clocking/index.html` that shows per-employee hours aggregated into calendar-month columns for any user-selected date range, with Excel export.

**Architecture:** All changes are confined to one file (`clocking/index.html`). Monthly totals are derived client-side by iterating the existing `D.wk_detail_table` day-level data and bucketing each day's hours into its calendar month. No backend changes.

**Tech Stack:** Vanilla JS, ExcelJS 4.4.0 (already loaded), existing design-system CSS variables.

---

## File Map

| File | Change |
|---|---|
| `clocking/index.html` | Add ~40 lines CSS, ~70 lines HTML, ~300 lines JS. All edits use exact-string `Edit` operations. |

---

## Task 1 — CSS: Main styles for the Monthly tab

**Files:**
- Modify: `clocking/index.html` (CSS `<style>` block, after `.miss-count-badge.zero` rule)

- [ ] **Step 1: Insert monthly CSS block**

Find the exact string:
```
.miss-count-badge.zero{background:var(--color-success-bd)}
```
Insert the following immediately after it (new line):
```css

/* ── MONTH FILTER (Monthly Reporting tab) ─────────────────────── */
.mo-filter-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:var(--color-surface-base);border:1px solid var(--color-border-subtle);border-radius:var(--r-md);padding:10px 12px;margin-bottom:12px}
.mo-filter-label{font-family:var(--font-display);font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--color-text-secondary);margin-right:4px}
.mo-preset{font-family:var(--font-display);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;border:1px solid var(--color-border-default);background:var(--color-surface-sunken);color:var(--color-text-primary);padding:5px 10px;border-radius:var(--r-sm);cursor:pointer}
.mo-preset:hover{background:var(--color-brand-primary);color:var(--color-text-on-brand);border-color:var(--color-brand-primary)}
.mo-divider{width:1px;height:20px;background:var(--color-border-default);margin:0 4px}
.mo-meta{font-size:11px;color:var(--color-text-secondary);font-family:var(--font-body)}
.mo-meta strong{color:var(--color-text-primary);font-weight:700}
#mo-table-wrap{max-height:520px;overflow-y:auto}
#mo-table th{position:sticky;top:0;z-index:2}
```

- [ ] **Step 2: Add responsive override in 768px compact block**

Find the exact string (inside the first `@media (max-width:768px)` block):
```
  .wk-chip{padding:6px 10px;font-size:11px;min-height:36px}
```
Insert immediately after:
```css
  .mo-preset{padding:6px 10px;font-size:11px;min-height:36px}
```

- [ ] **Step 3: Add responsive override in aggressive mobile block**

Find the exact string (inside the second `@media (max-width:768px)` aggressive block):
```
  .wk-preset,.btn-export{min-height:40px;padding:8px 12px}
```
Insert immediately after:
```css
  .mo-preset{min-height:40px;padding:8px 12px}
```

- [ ] **Step 4: Open browser and verify no visual regressions**

Open `http://localhost:60268` (or the Vercel preview URL) and confirm:
- The existing tabs (Overview, Weekly Hours, etc.) look unchanged.
- No console errors.

- [ ] **Step 5: Commit**

```
git add clocking/index.html
git commit -m "style: add Monthly Reporting CSS classes"
```

---

## Task 2 — HTML: Nav button, help text, tab content

**Files:**
- Modify: `clocking/index.html` (nav strip, help panel, tab div)

- [ ] **Step 1: Add nav tab button**

Find the exact string:
```
  <button onclick="showTab('weekly',this)">Weekly Hours</button>
```
Replace with:
```html
  <button onclick="showTab('weekly',this)">Weekly Hours</button>
  <button onclick="showTab('monthly',this)">Monthly Reporting</button>
```

- [ ] **Step 2: Add help panel description**

Find the exact string:
```
      <strong>Weekly Hours</strong> — Per-employee hours in Wed–Tue weeks. Use the week chips to isolate recent weeks. Export to Excel for payroll.<br>
```
Replace with:
```html
      <strong>Weekly Hours</strong> — Per-employee hours in Wed–Tue weeks. Use the week chips to isolate recent weeks. Export to Excel for payroll.<br>
      <strong>Monthly Reporting</strong> — Per-employee hours aggregated into calendar months. Select any date range with the From/To pickers or use quick presets. Export to Excel for month-end payroll or trend analysis.<br>
```

- [ ] **Step 3: Add monthly tab content div**

Find the exact string:
```
<!-- MISSING -->
```
Insert the entire block immediately before it:
```html
<!-- MONTHLY -->
<div id="tab-monthly" class="tab-content">
  <p class="note" style="margin-top:8px;margin-bottom:10px">Hours are NET of 45 min/day break. Weeks run Wed–Tue; hours for weeks spanning a month boundary are split by day. Values in decimal hours (e.g. 168.0 = 168 h). Miss YTD = total missing clock-outs YTD.</p>
  <div class="controls">
    <input type="text" id="mo-search" placeholder="Search name or ID..." oninput="filterMo()">
    <select id="mo-emp" onchange="filterMo()" title="Employer">
      <option value="">All Employers</option>
      <option value="Olympic Paints">OP — Olympic Paints</option>
      <option value="Primeserve">PS — Primeserve</option>
    </select>
    <select id="mo-miss" onchange="filterMo()" title="Missed clock-outs">
      <option value="">Any miss status</option>
      <option value="missing">Has missed clock-outs</option>
      <option value="clean">No missed clock-outs</option>
    </select>
    <select id="mo-min-hrs" onchange="filterMo()" title="Minimum total hours (visible months)">
      <option value="0">Any hours</option>
      <option value="1">&#8805; 1h</option>
      <option value="40">&#8805; 40h</option>
      <option value="80">&#8805; 80h</option>
      <option value="120">&#8805; 120h</option>
    </select>
  </div>

  <div class="mo-filter-bar">
    <span class="mo-filter-label">Date Range</span>
    <button class="mo-preset" onclick="setMoPreset('this')">This Month</button>
    <button class="mo-preset" onclick="setMoPreset('last')">Last Month</button>
    <button class="mo-preset" onclick="setMoPreset('3m')">Last 3 Months</button>
    <button class="mo-preset" onclick="setMoPreset('ytd')">YTD</button>
    <span class="mo-divider"></span>
    <span style="font-size:11px;color:var(--color-text-secondary)">From</span>
    <input type="date" id="mo-from" style="font-size:11px;padding:4px 8px;border:1px solid var(--color-border-default);background:var(--color-surface-sunken);color:var(--color-text-primary);border-radius:var(--r-sm)">
    <span style="font-size:11px;color:var(--color-text-secondary)">To</span>
    <input type="date" id="mo-to" style="font-size:11px;padding:4px 8px;border:1px solid var(--color-border-default);background:var(--color-surface-sunken);color:var(--color-text-primary);border-radius:var(--r-sm)">
    <button class="mo-preset" onclick="applyMo()" style="background:var(--color-success-bd);color:#fff;border-color:var(--color-success-bd)">Apply</button>
    <div id="mo-meta" class="mo-meta" style="margin-left:auto"></div>
    <button class="btn-export" onclick="exportMo()" title="Download visible rows as Excel">&#8595; Export to Excel</button>
  </div>

  <div class="legend">
    <div class="chip"><div class="chip-dot" style="background:rgba(107,158,208,.3)"></div> Hours present</div>
    <div class="chip"><div class="chip-dot" style="background:#1A3D6E"></div> Period total</div>
    <div class="chip"><div class="chip-dot" style="background:#FDF0A0;border:1px solid #D4A800"></div> Has missed clock-outs</div>
  </div>
  <div id="mo-table-wrap" class="table-wrap"><table id="mo-table"><thead id="mo-thead"></thead><tbody id="mo-body"></tbody></table></div>
</div>

```

- [ ] **Step 4: Open browser, click "Monthly Reporting" tab**

Confirm:
- The tab button appears and is clickable.
- The tab content div appears (empty table, filter controls, date bar with presets).
- No JS errors in the console.

- [ ] **Step 5: Commit**

```
git add clocking/index.html
git commit -m "feat: add Monthly Reporting tab HTML and nav button"
```

---

## Task 3 — JS: showTab dispatch + date helpers + aggregation

**Files:**
- Modify: `clocking/index.html` (JS `<script>` block)

- [ ] **Step 1: Register initMo in showTab dispatch map**

Find the exact string:
```
  ({overview:initOverview,yesterday:initYesterday,daily:initDaily,departments:initDepts,missing:initMissing}[id]||function(){})();
```
Replace with:
```js
  ({overview:initOverview,yesterday:initYesterday,daily:initDaily,departments:initDepts,monthly:initMo,missing:initMissing}[id]||function(){})();
```

- [ ] **Step 2: Insert the Monthly JS block**

Find the exact string:
```
// ── MISSING ───────────────────────────────────────────────────────────
```
Insert the entire block immediately before it:
```js
// ── MONTHLY ───────────────────────────────────────────────────────────

/* ── Date helpers ──────────────────────────────────────────────── */
function parseDateStr(s){
  // s = 'YYYY-MM-DD' → Date at local midnight (avoids UTC-offset gotchas)
  const p=s.split('-').map(Number);
  return new Date(p[0],p[1]-1,p[2]);
}
function fmtMonthLabel(y,m){
  return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]+' '+y;
}
function fmtYMD(dt){
  return dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0')+'-'+String(dt.getDate()).padStart(2,'0');
}
function getMonthsInRange(from,to){
  const months=[];
  let y=from.getFullYear(), m=from.getMonth()+1;
  const ey=to.getFullYear(), em=to.getMonth()+1;
  while(y<ey||(y===ey&&m<=em)){
    months.push({key:y+'-'+String(m).padStart(2,'0'), label:fmtMonthLabel(y,m)});
    m++; if(m>12){m=1;y++;}
  }
  return months;
}

/* ── State ─────────────────────────────────────────────────────── */
let moFromDate=null, moToDate=null, moMonths=[], moAggRows=[];

/* ── Aggregation ───────────────────────────────────────────────── */
const MO_WK_OFFSETS={Wed:0,Thu:1,Fri:2,Sat:3,Sun:4,Mon:5,Tue:6};

function buildMonthlyAgg(from,to){
  const fromMs=from.getTime(), toMs=to.getTime();
  return D.wk_detail_table.map(r=>{
    const months={};
    D.wk_weeks.forEach(function(wk,wi){
      const wkStart=parseDateStr(wk.start);
      const weekData=r.weeks[wi];
      if(!weekData)return;
      Object.keys(MO_WK_OFFSETS).forEach(function(day){
        const offset=MO_WK_OFFSETS[day];
        const dayHrs=(weekData.days&&weekData.days[day])||0;
        if(dayHrs<=0)return;
        const dt=new Date(wkStart.getTime()+offset*86400000);
        if(dt.getTime()<fromMs||dt.getTime()>toMs)return;
        const key=dt.getFullYear()+'-'+String(dt.getMonth()+1).padStart(2,'0');
        months[key]=(months[key]||0)+dayHrs;
      });
    });
    return {employer:r.employer, id:r.id, name:r.name, missYTD:r.missYTD||0, months:months};
  });
}

/* ── Preset + Apply ────────────────────────────────────────────── */
function setMoPreset(p){
  const now=new Date();
  const y=now.getFullYear(), m=now.getMonth();
  let from, to;
  if(p==='this'){
    from=new Date(y,m,1); to=new Date(y,m+1,0);
  } else if(p==='last'){
    from=new Date(y,m-1,1); to=new Date(y,m,0);
  } else if(p==='3m'){
    from=new Date(y,m-2,1); to=new Date(y,m+1,0);
  } else {
    // ytd
    from=new Date(y,0,1); to=new Date(y,m+1,0);
  }
  document.getElementById('mo-from').value=fmtYMD(from);
  document.getElementById('mo-to').value=fmtYMD(to);
  applyMo();
}

function applyMo(){
  const fv=document.getElementById('mo-from').value;
  const tv=document.getElementById('mo-to').value;
  if(!fv||!tv){alert('Please select both a From and To date.');return;}
  const from=parseDateStr(fv), to=parseDateStr(tv);
  if(from>to){alert('End date must be after start date.');return;}
  moFromDate=from; moToDate=to;
  moMonths=getMonthsInRange(from,to);
  moAggRows=buildMonthlyAgg(from,to);
  filterMo();
}

/* ── Filtering + row total ─────────────────────────────────────── */
function moRowTotal(r){
  return moMonths.reduce(function(s,mo){return s+(r.months[mo.key]||0);},0);
}

function getFilteredMoRows(){
  const s=(document.getElementById('mo-search').value||'').toLowerCase();
  const e=document.getElementById('mo-emp').value;
  const miss=document.getElementById('mo-miss').value;
  const minH=parseFloat(document.getElementById('mo-min-hrs').value)||0;
  let rows=moAggRows.slice();
  if(e)rows=rows.filter(function(r){return r.employer===e;});
  if(s)rows=rows.filter(function(r){return r.name.toLowerCase().includes(s)||r.id.toLowerCase().includes(s);});
  if(miss==='missing')rows=rows.filter(function(r){return r.missYTD>0;});
  else if(miss==='clean')rows=rows.filter(function(r){return r.missYTD===0;});
  if(minH>0)rows=rows.filter(function(r){return moRowTotal(r)>=minH;});
  return rows;
}

function filterMo(){
  if(!moMonths.length)return;
  buildMoHeader();
  const rows=getFilteredMoRows();
  renderMo(rows);
  updateMoMeta(rows);
}

/* ── Table header ──────────────────────────────────────────────── */
function buildMoHeader(){
  const thead=document.getElementById('mo-thead');
  let r1='<tr><th rowspan="2">Employer</th><th rowspan="2">ID</th><th rowspan="2">Name</th>';
  moMonths.forEach(function(mo){
    r1+='<th style="background:#1A3D6E;color:#fff;text-align:center;white-space:nowrap;border-bottom:2px solid #F5C400">'+mo.label+'</th>';
  });
  r1+='<th rowspan="2" style="background:#0D2040;color:#F5C400;text-align:center;font-weight:800">Total</th>';
  r1+='<th rowspan="2" style="text-align:center">Miss YTD</th></tr>';
  let r2='<tr>';
  moMonths.forEach(function(){
    r2+='<th style="background:rgba(26,61,110,.7);color:var(--color-text-secondary);text-align:center;font-size:10px">Hours</th>';
  });
  r2+='</tr>';
  thead.innerHTML=r1+r2;
}

/* ── Table body ────────────────────────────────────────────────── */
function renderMo(rows){
  const b=document.getElementById('mo-body');
  b.innerHTML='';
  if(!moMonths.length){
    b.innerHTML='<tr><td colspan="6" style="padding:24px;text-align:center;color:var(--color-text-secondary);font-style:italic">Select a date range and click Apply to load data.</td></tr>';
    return;
  }
  if(!rows.length){
    const cols=3+moMonths.length+2;
    b.innerHTML='<tr><td colspan="'+cols+'" style="padding:24px;text-align:center;color:var(--color-text-secondary);font-style:italic">No employees match the current filter.</td></tr>';
    return;
  }
  rows.forEach(function(r){
    const ps=r.employer==='Primeserve';
    const hasMiss=r.missYTD>0;
    const total=moRowTotal(r);
    let cells='';
    moMonths.forEach(function(mo){
      const h=r.months[mo.key]||0;
      cells+='<td class="center" style="background:rgba(107,158,208,.12);color:var(--color-text-primary);font-size:11px">'+(h>0?h.toFixed(1):'&mdash;')+'</td>';
    });
    b.innerHTML+='<tr class="'+(ps?'primeserve':'')+'">'+
      '<td class="'+(ps?'emp-ps':'emp-op')+'" style="font-weight:800">'+(ps?'PS':'OP')+'</td>'+
      '<td style="font-size:11px;color:var(--color-text-secondary)">'+r.id+'</td>'+
      '<td><strong>'+r.name+'</strong></td>'+
      cells+
      '<td class="center" style="background:#1A3D6E;color:#F5C400;font-weight:800">'+(total>0?total.toFixed(1):'&mdash;')+'</td>'+
      '<td class="center" style="background:'+(hasMiss?'rgba(245,196,0,.18)':'rgba(45,140,122,.15)')+';font-weight:800;color:'+(hasMiss?'var(--color-warning-fg)':'var(--color-success-fg)')+';">'+(r.missYTD||0)+'</td>'+
      '</tr>';
  });
}

/* ── Meta row ──────────────────────────────────────────────────── */
function updateMoMeta(rows){
  const meta=document.getElementById('mo-meta');
  if(!meta)return;
  const opN=rows.filter(function(r){return r.employer==='Olympic Paints';}).length;
  const psN=rows.filter(function(r){return r.employer==='Primeserve';}).length;
  const sumH=rows.reduce(function(s,r){return s+moRowTotal(r);},0);
  const moLbl=moMonths.length?moMonths.map(function(m){return m.label;}).join(', '):'(none)';
  meta.innerHTML='Showing <strong>'+rows.length+'</strong> employees (OP <strong>'+opN+'</strong> &middot; PS <strong>'+psN+'</strong>) &middot; <strong>'+moMonths.length+'</strong> month'+(moMonths.length===1?'':'s')+': '+moLbl+' &middot; visible total <strong>'+sumH.toFixed(1)+'h</strong>';
}

/* ── Init (lazy, once) ─────────────────────────────────────────── */
function initMo(){once('monthly',function(){setMoPreset('last');})}

```

- [ ] **Step 3: Open browser, click "Monthly Reporting" tab**

Expected results:
- Tab activates and shows the filter controls and date bar.
- Preset "Last Month" fires automatically → From/To inputs populate with the first and last day of the previous calendar month.
- The monthly table renders with one column per month (should be just one month for "Last Month").
- The meta row below the date bar reads: `Showing 102 employees (OP 74 · PS 28) · 1 month: Apr 2026 · visible total X.Xh` (values will vary).
- No console errors.

- [ ] **Step 4: Manually verify date-range Apply**

1. Change From to `2026-03-01`, To to `2026-05-27`, click Apply.
2. Expected: 3 month columns appear — "Mar 2026", "Apr 2026", "May 2026".
3. Spot-check one employee: open Weekly Hours, sum that employee's hours that fall in March, compare to the Monthly Reporting value. They should match within rounding (0.1h tolerance due to decimal precision).

- [ ] **Step 5: Test edge cases in browser console**

Open DevTools console and run:
```js
// Test: from > to should alert, not crash
document.getElementById('mo-from').value='2026-05-01';
document.getElementById('mo-to').value='2026-03-01';
applyMo();
// Expected: alert "End date must be after start date."

// Test: date range with no data (future dates)
document.getElementById('mo-from').value='2027-01-01';
document.getElementById('mo-to').value='2027-03-31';
applyMo();
// Expected: table shows "No employees match the current filter." (all rows have 0 total, minH=0 so rows still show but cells are all —)
// Note: rows will appear with all — cells and 0 total. That's acceptable.
```

- [ ] **Step 6: Commit**

```
git add clocking/index.html
git commit -m "feat: Monthly Reporting JS — helpers, aggregation, render, init"
```

---

## Task 4 — JS: exportMo() Excel export

**Files:**
- Modify: `clocking/index.html` (JS block, after the `initMo` function and its closing blank line)

- [ ] **Step 1: Insert exportMo() function**

Find the exact string (the last line of the Monthly JS block you just inserted):
```
function initMo(){once('monthly',function(){setMoPreset('last');})}

```
Replace with:
```js
function initMo(){once('monthly',function(){setMoPreset('last');})}

async function exportMo(){
  const rows=getFilteredMoRows();
  if(!moMonths.length){alert('Select a date range and click Apply before exporting.');return;}
  if(!rows.length){alert('No employees match the current filter.');return;}

  const AN='FF1A3D6E',AY='FFF5C400',AD='FF0D2040',AW='FFFFFFFF',AT='FF2D8C7A';
  const wb=new ExcelJS.Workbook();
  wb.creator='Olympic Paints — HR';
  wb.lastModifiedBy='Clocking Dashboard';
  wb.created=new Date();
  const ws=wb.addWorksheet('Monthly Hours',{
    properties:{tabColor:{argb:AY}},
    views:[{state:'frozen',xSplit:3,ySplit:3}]
  });

  // Filters description
  const empF=document.getElementById('mo-emp').value;
  const missF=document.getElementById('mo-miss').value;
  const minHF=parseFloat(document.getElementById('mo-min-hrs').value)||0;
  const searchF=document.getElementById('mo-search').value;
  const filters=[];
  if(empF)filters.push('Employer: '+(empF==='Olympic Paints'?'OP (Olympic Paints)':'PS (Primeserve)'));
  if(missF)filters.push('Miss: '+missF);
  if(minHF)filters.push('Min hrs: ≥'+minHF+'h');
  if(searchF)filters.push('Search: "'+searchF+'"');
  const filterStr=filters.length?filters.join(' | '):'All employees';

  const TC=3+moMonths.length+2; // total columns

  // Row 1 — Title
  ws.mergeCells(1,1,1,TC);
  const t1=ws.getCell(1,1);
  t1.value='OLYMPIC PAINTS — Monthly Hours Report';
  t1.font={bold:true,size:14,color:{argb:AY},name:'Calibri'};
  t1.fill={type:'pattern',pattern:'solid',fgColor:{argb:AN}};
  t1.alignment={vertical:'middle',horizontal:'left'};
  ws.getRow(1).height=26;

  // Row 2 — Subtitle
  ws.mergeCells(2,1,2,TC);
  const t2=ws.getCell(2,1);
  t2.value='Period: '+document.getElementById('mo-from').value+' – '+document.getElementById('mo-to').value+'  |  Generated: '+new Date().toISOString().slice(0,10)+'  |  '+filterStr+'  |  Employees: '+rows.length;
  t2.font={size:9,color:{argb:'FF9ABADB'},italic:true};
  t2.fill={type:'pattern',pattern:'solid',fgColor:{argb:AD}};
  t2.alignment={vertical:'middle',horizontal:'left'};
  ws.getRow(2).height=16;

  // Row 3 — Column headers
  ws.getRow(3).height=20;
  const hdrs=['Employer','ID','Name'].concat(moMonths.map(function(m){return m.label;})).concat(['Total','Miss YTD']);
  hdrs.forEach(function(h,i){
    const c=ws.getCell(3,i+1);
    c.value=h;
    const isMo=i>=3&&i<3+moMonths.length;
    const isTot=i===3+moMonths.length;
    c.fill={type:'pattern',pattern:'solid',fgColor:{argb:isTot?AD:AN}};
    c.font={bold:true,color:{argb:(isMo||isTot)?AY:AW},size:10};
    c.alignment={horizontal:'center',vertical:'middle'};
    c.border=thinBorder('FF2A4A7E');
  });

  // Column widths
  ws.getColumn(1).width=12;
  ws.getColumn(2).width=14;
  ws.getColumn(3).width=28;
  moMonths.forEach(function(_,i){ws.getColumn(4+i).width=14;});
  ws.getColumn(4+moMonths.length).width=12;
  ws.getColumn(4+moMonths.length+1).width=12;

  // Data rows (start at row 4)
  rows.forEach(function(r,ri){
    const rn=4+ri;
    ws.getRow(rn).height=16;
    const ps=r.employer==='Primeserve';
    const hasMiss=r.missYTD>0;
    const total=moRowTotal(r);
    const bg=ri%2===0?'FF1A1A18':'FF111110';

    var ec=ws.getCell(rn,1);
    ec.value=ps?'PS':'OP';
    ec.font={bold:true,color:{argb:ps?'FF2D8C7A':'FF6B9ED0'},size:10};
    ec.fill={type:'pattern',pattern:'solid',fgColor:{argb:bg}};
    ec.alignment={horizontal:'center'};

    var ic=ws.getCell(rn,2);
    ic.value=r.id;
    ic.font={size:9,color:{argb:'FF888888'}};
    ic.fill={type:'pattern',pattern:'solid',fgColor:{argb:bg}};

    var nc=ws.getCell(rn,3);
    nc.value=r.name;
    nc.font={bold:true,size:10};
    nc.fill={type:'pattern',pattern:'solid',fgColor:{argb:bg}};

    moMonths.forEach(function(mo,mi){
      const h=r.months[mo.key]||0;
      var mc=ws.getCell(rn,4+mi);
      mc.value=h>0?Math.round(h*100)/100:null;
      mc.numFmt='0.0';
      mc.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FF1A2A40'}};
      mc.alignment={horizontal:'center'};
      mc.font={size:10};
    });

    var tc=ws.getCell(rn,4+moMonths.length);
    tc.value=total>0?Math.round(total*100)/100:null;
    tc.numFmt='0.0';
    tc.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FF162A50'}};
    tc.font={bold:true,size:10,color:{argb:AW}};
    tc.alignment={horizontal:'center'};

    var xc=ws.getCell(rn,4+moMonths.length+1);
    xc.value=r.missYTD||0;
    xc.fill={type:'pattern',pattern:'solid',fgColor:{argb:hasMiss?'FF2A2000':'FF001A14'}};
    xc.font={bold:true,size:10,color:{argb:hasMiss?AY:AT}};
    xc.alignment={horizontal:'center'};
  });

  // Totals row
  const tn=4+rows.length;
  ws.getRow(tn).height=18;
  ws.mergeCells(tn,1,tn,3);
  var tl=ws.getCell(tn,1);
  tl.value='TOTALS';
  tl.font={bold:true,color:{argb:AW},size:11};
  tl.fill={type:'pattern',pattern:'solid',fgColor:{argb:AN}};
  tl.alignment={horizontal:'center'};

  moMonths.forEach(function(mo,mi){
    const colSum=rows.reduce(function(s,r){return s+(r.months[mo.key]||0);},0);
    var tc=ws.getCell(tn,4+mi);
    tc.value=Math.round(colSum*100)/100;
    tc.numFmt='0.0';
    tc.fill={type:'pattern',pattern:'solid',fgColor:{argb:AN}};
    tc.font={bold:true,color:{argb:AY},size:10};
    tc.alignment={horizontal:'center'};
  });

  const grand=rows.reduce(function(s,r){return s+moRowTotal(r);},0);
  var gc=ws.getCell(tn,4+moMonths.length);
  gc.value=Math.round(grand*100)/100;
  gc.numFmt='0.0';
  gc.fill={type:'pattern',pattern:'solid',fgColor:{argb:AN}};
  gc.font={bold:true,color:{argb:AY},size:11};
  gc.alignment={horizontal:'center'};

  // Last Miss YTD total cell (blank — miss YTD is not summed)
  var mx=ws.getCell(tn,4+moMonths.length+1);
  mx.fill={type:'pattern',pattern:'solid',fgColor:{argb:AN}};

  // Page setup
  ws.pageSetup={
    paperSize:9,orientation:'landscape',fitToPage:true,fitToWidth:1,fitToHeight:0,
    margins:{left:0.4,right:0.4,top:0.5,bottom:0.5,header:0.3,footer:0.3},
    printTitlesRow:'1:3'
  };
  ws.headerFooter.oddFooter='&LOlympic Paints&CMonthly Hours Report&RPage &P of &N';

  // Download
  const buf=await wb.xlsx.writeBuffer();
  const blob=new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  const fromTag=document.getElementById('mo-from').value;
  const toTag=document.getElementById('mo-to').value;
  a.href=url;
  a.download='Olympic_Paints_Monthly_Hours_'+fromTag+'_'+toTag+'.xlsx';
  document.body.appendChild(a);a.click();document.body.removeChild(a);
  setTimeout(function(){URL.revokeObjectURL(url);},1500);
}

```

- [ ] **Step 2: Test the export in browser**

1. Open Monthly Reporting tab.
2. Click "Last 3 Months" preset → Apply fires automatically.
3. Click "⬇ Export to Excel".
4. Open the downloaded file and verify:
   - Sheet name is "Monthly Hours".
   - Row 1: Dark navy background, yellow "OLYMPIC PAINTS — Monthly Hours Report" title.
   - Row 2: Dark background, subtitle with period, generated date, employee count.
   - Row 3: Column headers — Employer / ID / Name / [month labels in yellow on navy] / Total / Miss YTD.
   - Data rows alternate backgrounds, OP in blue, PS in teal.
   - Totals row at the bottom in navy with yellow sums.
   - Filename follows `Olympic_Paints_Monthly_Hours_YYYY-MM-DD_YYYY-MM-DD.xlsx` pattern.
   - Columns A–C are frozen.

- [ ] **Step 3: Test export with filters applied**

1. Set Employer filter to "OP — Olympic Paints".
2. Export again.
3. Verify only OP employees appear in the file.

- [ ] **Step 4: Commit**

```
git add clocking/index.html
git commit -m "feat: Monthly Reporting Excel export (exportMo)"
```

---

## Task 5 — Final verification and deploy

**Files:**
- No further code changes.

- [ ] **Step 1: Full tab regression check**

Open the dashboard and verify each tab still works:
- Overview → charts and KPI tiles render.
- Yesterday → missed employees list renders.
- Daily Attendance → chart and table render.
- Departments → chart and table render.
- Weekly Hours → week chips, table, export all work.
- Monthly Reporting → see steps below.
- Missing Clock Out → search and table render.

- [ ] **Step 2: Monthly Reporting — all preset buttons**

Click each preset and confirm the date inputs and table update correctly:
| Preset | Expected From | Expected To |
|---|---|---|
| This Month | 2026-05-01 | 2026-05-31 |
| Last Month | 2026-04-01 | 2026-04-30 |
| Last 3 Months | 2026-03-01 | 2026-05-31 |
| YTD | 2026-01-01 | 2026-05-31 |

*(Dates will differ based on today's date; today is 2026-05-27.)*

- [ ] **Step 3: Monthly Reporting — filter controls**

With any date range applied:
1. Type a name fragment in the search box → table filters live.
2. Select "PS — Primeserve" → only Primeserve rows show.
3. Select "Has missed clock-outs" → only employees with missYTD > 0 show.
4. Select "≥ 80h" min hours → only employees with ≥ 80 h in the visible period show.
5. Clear all filters → all employees return.

- [ ] **Step 4: Mobile layout check**

Resize browser to 375px width and confirm:
- Date bar wraps gracefully (preset buttons and date inputs stack).
- Monthly table h-scrolls within its container.
- No overflow or broken layout.

- [ ] **Step 5: Push and deploy**

```
git push origin master
```

Vercel will auto-deploy. Confirm the live URL `https://olympic-paints-portal.vercel.app/d/clocking` shows the Monthly Reporting tab within a few minutes.

- [ ] **Step 6: Smoke test on live URL**

Open `https://olympic-paints-portal.vercel.app/d/clocking` and:
1. Click Monthly Reporting tab.
2. Confirm Last Month data loads.
3. Export Excel and confirm download.
