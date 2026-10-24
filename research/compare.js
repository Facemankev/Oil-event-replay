/* Pure research functions shared by the browser, tests and a future assistant. */
(function(root) {
'use strict';
const validDate = s => /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s+'T00:00:00Z')) && new Date(s+'T00:00:00Z').toISOString().slice(0,10) === s;
const day = s => Date.parse(s+'T00:00:00Z');
function parseCSV(text) {
  const records=[]; let row=[], cell='', quoted=false;
  text=text.replace(/^\uFEFF/,'');
  for(let i=0;i<=text.length;i++) {
    const c=text[i];
    if(c==='"') { if(quoted && text[i+1]==='"') {cell+='"';i++;} else quoted=!quoted; }
    else if(!quoted && (c===',' || c==='\n' || c===undefined)) {
      row.push(cell.trim());cell='';
      if(c!==',') {if(row.some(Boolean))records.push(row);row=[];}
    } else if(c!==undefined && (c!=='\r'||quoted))cell+=c;
  }
  if(quoted)throw Error('A quoted CSV field is unfinished.');
  const header=(records.shift()||[]).map(s=>s.toLowerCase());
  const di=header.findIndex(s=>['date','observation_date'].includes(s));
  const pi=header.findIndex(s=>['close','price','value','adj close','adjusted close'].includes(s));
  if(di<0||pi<0)throw Error('CSV needs Date and Close (or Price) columns.');
  const map=new Map();let skipped=0;
  for(const r of records) {
    const date=r[di], raw=r[pi], value=Number(raw);
    if(!validDate(date||'') || !raw || !Number.isFinite(value)||value<=0) {skipped++;continue;}
    if(map.has(date))throw Error('Duplicate date '+date+'. Keep one observation per day.');
    map.set(date,value);
  }
  if(map.size<2)throw Error('Include at least two valid positive prices.');
  return {rows:[...map].sort((a,b)=>a[0].localeCompare(b[0])),skipped};
}
function compare(series,eventDate,windowDays) {
  if(!validDate(eventDate)||![7,30,90].includes(windowDays))throw Error('Invalid event date or comparison window.');
  if(!series.length)return {status:'empty',message:'Choose at least two markets to compare.'};
  const filtered=series.map(s=>({...s,rows:s.rows.filter(r=>validDate(r[0])&&Number.isFinite(r[1])&&r[1]>0&&Math.abs(day(r[0])-day(eventDate))<=windowDays*86400000)}));
  const missing=filtered.filter(s=>!s.rows.some(r=>r[0]<eventDate)||!s.rows.some(r=>r[0]>=eventDate));
  if(missing.length)return {status:'missing',message:'Need prices before and on or after this event for: '+missing.map(s=>s.name).join(', ')+'. Try another event, import history, or deselect these markets.'};
  const maps=filtered.map(s=>new Map(s.rows));
  const common=[...maps[0].keys()].filter(date=>maps.every(m=>m.has(date))).sort();
  const start=common.filter(d=>d<eventDate).at(-1),end=common.filter(d=>d>=eventDate).at(-1);
  if(!start||!end)return {status:'missing',message:'These markets have no matching dates on both sides of the event. No prices have been filled in.'};
  return {status:'ok',eventDate,windowDays,start,end,method:'Last shared date before the event to last shared date within the selected window after it.',results:filtered.map((s,i)=>({id:s.id,name:s.name,source:s.source,basis:s.basis,unit:s.unit,startPrice:maps[i].get(start),endPrice:maps[i].get(end),change:(maps[i].get(end)/maps[i].get(start)-1)*100,points:s.rows.length,sharedPoints:common.length}))};
}
const api={validDate,parseCSV,compare};
if(typeof module!=='undefined')module.exports=api;
else root.MarketRippleResearch=api;
})(typeof window!=='undefined'?window:globalThis);
