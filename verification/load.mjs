/** Immutable primary visible-table snapshots; no fetching or canonical writes. */
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
export const root=new URL('../',import.meta.url);
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export const json=path=>JSON.parse(readFileSync(new URL(path,root),'utf8'));
const urls={brent:'https://www.eia.gov/dnav/pet/hist/RBRTED.htm',wti:'https://www.eia.gov/dnav/pet/hist/RWTCD.htm',fx:'https://www.federalreserve.gov/releases/h10/hist/dat00_uk.htm'};
export function readCSV(path,expectedHash,header){
 if(!/^verification\/sources\/[a-z0-9-]+\.csv$/.test(path))throw Error('Unexpected primary snapshot path');
 const bytes=readFileSync(new URL(path,root));if(sha(bytes)!==expectedHash)throw Error('Primary snapshot fingerprint mismatch');
 const lines=bytes.toString('utf8').trimEnd().split('\n');
 if(lines.shift()!==header.join(','))throw Error('Unexpected snapshot columns');
 return lines.map(line=>{const cells=line.split(',');if(cells.length!==header.length)throw Error('Unsupported CSV cell structure');return Object.fromEntries(header.map((name,i)=>[name,cells[i]]));});
}
export function loadPrimary(){
 const manifest=json('verification/sources/manifest.json'),tables={};
 if(manifest.schema_version!==1)throw Error('Unsupported snapshot manifest');
 for(const [kind,url] of Object.entries(urls)){
  const info=manifest.sources[kind];if(info.url!==url||info.unit!==(kind==='fx'?'USD per GBP':'USD per barrel'))throw Error('Unexpected primary source URL/unit');
  const rows=readCSV(info.file,info.sha256,['date','value','status','locator']),byDate=new Map();let last='';
  for(const row of rows){
   if(!/^\d{4}-\d{2}-\d{2}$/.test(row.date)||new Date(row.date).toISOString().slice(0,10)!==row.date||row.date<=last)throw Error('Invalid, unordered or duplicate primary date');
   last=row.date;
   if(row.status==='numeric'){
    if(!/^-?\d+\.\d{2,4}$/.test(row.value)||!Number.isFinite(Number(row.value))||(kind==='fx'&&Number(row.value)<=0))throw Error('Invalid primary numeric value');
   }else if(row.value!==''||row.status!==(kind==='fx'?'ND':'blank_primary_cell'))throw Error('Invalid missing-value marker');
   byDate.set(row.date,row);
  }
  if(rows.length!==info.rows||rows.filter(r=>r.status==='numeric').length!==info.numeric||rows[0].date!==info.first||rows.at(-1).date!==info.last)throw Error('Snapshot coverage differs from manifest');
  for(let t=Date.parse(info.first);t<=Date.parse(info.last);t+=86400000){const d=new Date(t);if(d.getUTCDay()>0&&d.getUTCDay()<6&&!byDate.has(d.toISOString().slice(0,10)))throw Error('Primary weekday not captured');}
  tables[kind]={rows,byDate,numeric:rows.filter(r=>r.status==='numeric'),info};
 }
 const ref=manifest.prior_review,claims=readCSV(ref.file,ref.sha256,['market','date','claim','reported_value','api_value_known']);
 if(claims.length!==157||new Set(claims.map(c=>c.market+':'+c.date)).size!==claims.length)throw Error('Invalid PR #19 claim set');
 return {manifest,tables,claims};
}

export function reconcile(primary,canonical){
 const series={};
 for(const original of canonical.series){
  const source=primary.tables[original.series],seed=new Map(original.observations.filter(p=>p.value!==null).map(p=>[p.date,p]));
  const start=original.observations[0].date,end=original.observations.at(-1).date;
  const differences=[],missing=[],matched=[];
  for(const [date,old] of seed){const now=source.byDate.get(date);if(!now||now.status!=='numeric')missing.push({date,seed:old.value,status:now?.status||'not_captured'});else if(Number(now.value)!==Number(old.value))differences.push({date,seed:old.value,primary:now.value,locator:now.locator});else matched.push(date);}
  const gaps=source.numeric.filter(p=>p.date>=start&&p.date<=end&&!seed.has(p.date));
  series[original.series]={seed_numeric:seed.size,matching:matched.length,differences,missing_numeric:missing,
   primary_numeric_gaps_in_seed:gaps,newer_primary_observations:source.numeric.filter(p=>p.date>end).length,
   range:[start,end],primary_unavailable_in_range:source.rows.filter(p=>p.date>=start&&p.date<=end&&p.status!=='numeric').length};
 }
 const claims=primary.claims.map(claim=>{
  const source=primary.tables[claim.market].byDate.get(claim.date);
  const seed=canonical.series.find(s=>s.series===claim.market).observations.find(p=>p.date===claim.date);
  const current=source?.status==='numeric'?source.value:null;
  const status=claim.claim==='different_API_value'?(current!==null&&Number(current)===Number(seed?.value)?'retain_seed_API_difference_not_corroborated':'review_required'):
   claim.claim==='API_only'?(source?.status==='blank_primary_cell'?'explicit_primary_blank_API_value_still_unknown':'review_required'):
   claim.claim==='seed_only'?(current!==null&&Number(current)===Number(seed?.value)?'retain_seed_API_omission_not_a_deletion':'review_required'):'review_required';
  const numeric=primary.tables[claim.market].numeric,index=numeric.findIndex(p=>p.date===claim.date),previous=index>0?numeric[index-1]:null;
  return {...claim,previous_numeric_date:previous?.date??null,previous_primary_value:previous?.value??null,
   reported_value_matches_previous_observation:claim.claim==='different_API_value'&&previous?Number(claim.reported_value)===Number(previous.value):null,seed:seed?.value??null,current_primary:current,locator:source?.locator??null,status,revision_cause:null,original_API_payload_replayed:false};
 });
 return {series,claims,canonical_modified:false,original_API_conflict_cause_resolved:false,
  conclusion:'Current primary publication supports retaining every canonical price. Older API claims cannot establish revisions without their original payload.'};
}
