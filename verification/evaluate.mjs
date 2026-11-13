/** DAT-4: fixed-policy evaluation over primary oil/FX, separate from all accounts. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {loadPrimary,reconcile,json,sha,root} from './load.mjs';
import {cohortTrace,decidePaper,POLICY} from '../intelligence/engine.mjs';
import {baselineTrade,COSTS} from '../intelligence/evaluate.mjs';
import {nextDay} from '../ripple/paths.mjs';
import {validateQuote} from '../trading/core.mjs';

export const HORIZONS=[1,3,5,10,20];
export const COST_SCENARIOS={zero:{fee_gbp_per_leg:0,spread_bps:0,slippage_bps_per_leg:0},declared:COSTS,
 stressed:{fee_gbp_per_leg:.1,spread_bps:30,slippage_bps_per_leg:15}};
const instrument='Unleveraged fractional Brent spot-price reference, converted to GBP';
const pct=(a,b)=>a>0?(b/a-1)*100:null;
const signed=values=>({count:values.length,positive:values.filter(x=>x>0).length,negative:values.filter(x=>x<0).length,flat:values.filter(x=>x===0).length});

export function pairedHistory(primary,market){
 return primary.tables[market].numeric.map(price=>{
  const fx=primary.tables.fx.byDate.get(price.date),available=fx?.status==='numeric';
  return {date:price.date,value:available?String(Number(price.value)/Number(fx.value)):null,
   price_usd:price.value,usd_per_gbp:available?fx.value:null,
   missing_code:available?null:fx?.status||'FX_not_captured',snapshot_id:'derived_'+market+'_fed',
   original_publication_at:null,original_vintage_at:null};
 });
}

function pairSource(primary,market){
 return {source_kind:'derived_primary_EIA_Fed_pair',source_url:primary.tables[market].info.url,
  sha256:sha(primary.tables[market].info.sha256+primary.tables.fx.info.sha256),
  unit:'GBP per reference unit',price_source:primary.tables[market].info,fx_source:primary.tables.fx.info,
  captured_at:primary.manifest.captured_at,verification_scope:'Current primary publications, not original historical availability.',original_publication_times_known:false};
}

/** Source blank cells are unavailable, not prices. Horizons count actual numeric
 * EIA reporting observations; no assertion about an exchange/holiday calendar. */
export function reactionRows(primary,event,market){
 const all=pairedHistory(primary,market),anchor=event.reactions.anchor;
 const before=all.filter(p=>p.date<anchor),after=all.filter(p=>p.date>anchor),baseline=before.at(-1);
 return HORIZONS.map(days=>{
  const window=after.slice(0,days),points=[...(baseline?[baseline]:[]),...window];
  const status=!baseline?'baseline_unavailable':window.length!==days?'insufficient_observations':points.some(p=>p.value===null)?'explicit_missing_fx_observation':'ok';
  const first=baseline?.value===null?null:Number(baseline?.value),last=window.at(-1)?.value===null?null:Number(window.at(-1)?.value);
  return {days,status,verification:'derived_primary_current_vintage',point_in_time_safe:false,
   baseline_date:baseline?.date??null,end_date:window.at(-1)?.date??null,baseline:status==='ok'?String(first):null,
   end:status==='ok'?String(last):null,absolute_change:status==='ok'?String(last-first):null,
   change_percent:status==='ok'&&first>0?pct(first,last).toFixed(4):null,
   observations:points,sources:{['derived_'+market+'_fed']:pairSource(primary,market)}};
 });
}

export function coverage(primary,market,entry,days){
 const prices=primary.tables[market].numeric,index=prices.findIndex(p=>p.date===entry);
 const rows=index<0?[]:prices.slice(index,index+days+1),missing=[];
 for(const price of rows){const fx=primary.tables.fx.byDate.get(price.date);if(fx?.status!=='numeric')missing.push({date:price.date,kind:'FX_'+(fx?.status||'not_captured')});}
 if(rows.length!==days+1)missing.push({date:entry,kind:'insufficient_oil_reporting_observations'});
 const quotes=missing.length?null:rows.map(p=>({date:p.date,price:p.value,gbpPerUnit:1/Number(primary.tables.fx.byDate.get(p.date).value)}));
 return {days,entry_date:entry,end_date:rows.at(-1)?.date??null,observation_count:rows.length,
  current_vintage_complete:missing.length===0,as_of_complete:false,missing,quotes};
}

function makeQuery(event,market,day){
 return {title:event.title,category:event.category,market,occurred:event.occurred.date,publicDate:nextDay(day),
  location:event.geography,mechanism:event.features.mechanism,impact:event.features.impact,severity:'',excludeId:event.id,
  windSpeed:event.features.severity&&Date.parse(event.features.severity.published_at)<Date.parse(nextDay(day))?event.features.severity.value:null};
}

function quoteFor(primary,market,day){
 const p=primary.tables[market].byDate.get(day),fx=primary.tables.fx.byDate.get(day);
 if(market!=='brent'||p?.status!=='numeric'||Number(p.value)<=0||fx?.status!=='numeric')return null;
 return {asset:'BRENT',mode:'historical',date:day,price:Number(p.value),currency:'USD',timestamp:day+'T23:59:59.000Z',
  source:'EIA primary current-vintage HTML',evidence:primary.tables.brent.info.sha256,gbpPerUnit:1/Number(fx.value),
  fx:{base:'USD',quote:'GBP',rate:1/Number(fx.value),date:day,timestamp:day+'T23:59:59.000Z',
   source:'Federal Reserve H.10 current-vintage table',evidence:primary.tables.fx.info.sha256},delaySeconds:0,
  availability:'Day-end is an educational execution assumption, not a known historical release clock.'};
}

export function evaluatePrimary(primary,catalog){
 const histories=Object.fromEntries(['brent','wti'].map(m=>[m,pairedHistory(primary,m)]));
 const derived={...catalog,events:catalog.events.map(e=>({...e,reactions:{...e.reactions,
  markets:Object.fromEntries(['brent','wti'].map(m=>[m,reactionRows(primary,e,m)]))}}))};
 const events=[...derived.events].sort((a,b)=>a.reactions.anchor.localeCompare(b.reactions.anchor)||a.id.localeCompare(b.id)),frozen=[];
 // Frozen, unmodified INT-1 policy; no fit/tuning from following outcomes.
 for(const event of events)for(const market of ['brent','wti']){
  const entry=primary.tables[market].numeric.find(p=>p.date>event.reactions.anchor)?.date;
  if(!entry)throw Error('Primary capture does not include the decision date');
  const query=makeQuery(event,market,entry),cohort=cohortTrace(query,derived.events,histories[market],event.reactions.anchor);
  const quote=quoteFor(primary,market,entry),fatal=[];
  if(market==='wti')fatal.push('WTI_is_research_only_not_supported_paper_instrument');
  if(!quote&&market==='brent')fatal.push('missing_exact_entry_price_or_FX');
  if(quote)try{validateQuote(quote,'BRENT','historical',entry);}catch{fatal.push('invalid_same_instrument_quote');}
  const audit={practicable:fatal.length===0,point_in_time_safe:false,fatal,
   limitations:['original_price_and_FX_publication_vintages_unknown'],primary_price_verified:true,primary_FX_verified:true,
   captured_at:primary.manifest.captured_at,instrument:market==='brent'?instrument:'WTI observation-only reference'};
  const prompt=decidePaper({audit,cohort,budget:{max_allocation_gbp:5},position:null,entry:null,quote,
   evidence:{principal_risk:'Opposing supply/demand, FX, other news and unknown historical publication/vintage evidence.'},instrument,cursor:entry});
  const reasons=[...fatal,...audit.limitations];
  if(cohort.eligible_cases<POLICY.min_cases)reasons.push('fewer_than_eight_as_of_qualified_nonoverlapping_analogues');
  if(cohort.condition.status!=='known')reasons.push('pre_event_condition_window_incomplete');
  frozen.push({event_id:event.id,title:event.title,market,occurred:event.occurred,first_public:event.first_public,
   comparison_anchor:event.reactions.anchor,decision_date:entry,query,action:prompt.action,codes:prompt.codes,reasons,audit,cohort});
 }
 // Outcomes, gaps and baseline sensitivities are attached only after decisions.
 const records=frozen.map(record=>{
  const horizons=Object.fromEntries(HORIZONS.map(n=>[n,coverage(primary,record.market,record.decision_date,n)]));
  const strict=horizons[5],positive=strict.quotes?.every(q=>Number(q.price)>0);
  const baselines=record.market==='brent'&&positive?Object.fromEntries(Object.entries(COST_SCENARIOS).map(([name,costs])=>[name,baselineTrade(strict.quotes,record.decision_date,5,5,costs)])):null;
  const joined=primary.tables[record.market].numeric.filter(p=>primary.tables.fx.byDate.get(p.date)?.status==='numeric')
   .map(p=>({date:p.date,price:p.value,gbpPerUnit:1/Number(primary.tables.fx.byDate.get(p.date).value)}));
  const joint=record.market==='brent'?baselineTrade(joined,record.decision_date):null;
  const delayed=joined.find(q=>q.date>=record.decision_date)?.date;
  const delayedBaseline=record.market==='brent'&&delayed?baselineTrade(joined,delayed):null;
  const oil=primary.tables[record.market].numeric,index=oil.findIndex(p=>p.date===record.decision_date),end=oil[index+5];
  const usd=end?{known_on:end.date,percent:pct(Number(oil[index].value),Number(end.value))}:null;
  return {...record,horizons,usd_outcome:usd,baselines,sensitivity:{five_joint_observations:joint,
   delayed_first_joint_entry:delayedBaseline,entry_delay_days:delayed?Math.round((Date.parse(delayed)-Date.parse(record.decision_date))/86400000):null},
   trade_note:record.market==='wti'?'Coverage/returns only: no WTI paper account or counterfactual executed trade.':strict.current_vintage_complete?'Counterfactual baseline only; the policy did not Buy.':'Incomplete fixed oil-day window: no price or FX substituted.'};
 });
 const markets={};
 for(const market of ['brent','wti']){
  const rows=records.filter(r=>r.market===market),complete=rows.filter(r=>r.horizons[5].current_vintage_complete);
  const decisions={Buy:rows.filter(r=>r.action==='Consider Buy').length,Hold:rows.filter(r=>r.action==='Hold').length,
   Review_Sell:rows.filter(r=>r.action==='Review Sell').length,No_Action:rows.filter(r=>r.action==='No Action').length};
  if(decisions.Buy)throw Error('A supported entry requires reviewed execution evaluation before performance can be reported');
  const reasons=Object.fromEntries([...new Set(rows.flatMap(r=>r.reasons))].map(reason=>[reason,rows.filter(r=>r.reasons.includes(reason)).length]));
  markets[market]={events:rows.length,complete_current_vintage_5day:complete.length,incomplete_current_vintage_5day:rows.length-complete.length,
   complete_as_of_5day:0,entry_FX_unavailable:rows.filter(r=>primary.tables.fx.byDate.get(r.decision_date)?.status!=='numeric').length,
   complete_by_horizon:Object.fromEntries(HORIZONS.map(n=>[n,rows.filter(r=>r.horizons[n].current_vintage_complete).length])),decisions,reasons,
   manual_baseline_counts:Object.fromEntries(Object.keys(COST_SCENARIOS).map(name=>[name,signed(rows.filter(r=>r.baselines).map(r=>r.baselines[name].net_pnl_gbp))])),
   five_joint_observation_baselines:rows.filter(r=>r.sensitivity.five_joint_observations).length,
   deferred_entry_baselines:rows.filter(r=>r.sensitivity.delayed_first_joint_entry).length,
   false_positive_rate:null,no_trade_final_cash_gbp:50,policy_final_cash_gbp:50,
   caution:'Cash-only because all flat decisions abstain. No predictive accuracy established. Hold requires a pre-existing position.'};
 }
 return {method:'dat4-primary-current-vintage-audit-v1',policy:POLICY,events:events.length,market_cases:records.length,
  currency:'GBP reference derived as oil USD divided by Fed USD per GBP; no rounded reciprocal is stored.',markets,
  source_quality:'Verified current primary publications. Original historical publication/vintage completeness is zero, not inferred from observation or capture dates.',
  protocol:'Decide at the first numeric EIA reporting observation strictly after the publication anchor. Freeze decisions before evaluating returns. Fixed horizons count each benchmark’s numeric reporting observations, not an asserted exchange calendar.',
  sensitivity_note:'Joint-day and delayed-entry baselines are explicitly different timing rules, not gap fills or the main fixed-day evaluation.',records};
}

export function buildReport(){
 const primary=loadPrimary(),canonical=json('data/historical/prices.json'),catalog=json('matching/cohort-catalog.json');
 const reconciliation=reconcile(primary,canonical),evaluation=evaluatePrimary(primary,catalog);
 const both=evaluation.records.filter(r=>r.market==='brent').filter(r=>r.horizons[5].current_vintage_complete&&evaluation.records.find(x=>x.event_id===r.event_id&&x.market==='wti').horizons[5].current_vintage_complete).length;
 const legacy=json('ripple/data.json'),fxComparison=legacy.quotes.map(q=>{
  const fx=primary.tables.fx.byDate.get(q.date),rounded=fx?.status==='numeric'?Number((1/Number(fx.value)).toFixed(4)):null;
  return {date:q.date,legacy_gbp_per_usd:q.gbpPerUnit,current_primary_usd_per_gbp:fx?.value||null,
   equal_at_legacy_four_decimal_precision:rounded!==null&&rounded===Number(q.gbpPerUnit),
   action:'Preserve the original paper snapshot; current primary reciprocal is a separate research input.'};
 });
 return {schema_version:1,inputs:{scope:'Parsed JSON serialization; byte fingerprints of source CSVs are retained in the manifest.',manifest:sha(Buffer.from(JSON.stringify(primary.manifest))),
  canonical:sha(Buffer.from(JSON.stringify(canonical))),catalog:sha(Buffer.from(JSON.stringify(catalog)))},
  reconciliation,fx:{source:primary.tables.fx.info,total_rows:primary.tables.fx.rows.length,numeric:primary.tables.fx.numeric.length,
   explicit_ND:primary.tables.fx.rows.length-primary.tables.fx.numeric.length,original_slice_comparison:fxComparison,
   original_slice_equal_at_legacy_precision:fxComparison.filter(r=>r.equal_at_legacy_four_decimal_precision).length,
   original_snapshot_modified:false,original_publication_times_and_vintages_unknown:true},
  summary:{events:24,complete_both_markets_fixed_5day:both,incomplete_both_markets_fixed_5day:24-both,
   complete_as_of:0,Buy:evaluation.markets.brent.decisions.Buy,Hold:evaluation.markets.brent.decisions.Hold,No_Action:evaluation.markets.brent.decisions.No_Action},evaluation};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const report=buildReport(),text=JSON.stringify(report,null,2)+'\n';
 if(process.argv.includes('--check')){
  if(readFileSync(new URL('verification/RESULTS.sha256',root),'utf8').trim()!==sha(Buffer.from(text)))throw Error('DAT-4 result changed: review sources before updating the digest');
 }else if(process.argv.includes('--output')){
  const output=resolve(process.argv[process.argv.indexOf('--output')+1]),work=fileURLToPath(new URL('work/',root));
  if(!output.startsWith(work))throw Error('Full derived reports may be written only to a new file under work/');
  mkdirSync(dirname(output),{recursive:true});writeFileSync(output,text,{flag:'wx'});
 }
 console.log(JSON.stringify({summary:report.summary,primary_oil:Object.fromEntries(Object.entries(report.reconciliation.series).map(([k,v])=>[k,{matched:v.matching,differences:v.differences.length,gaps:v.primary_numeric_gaps_in_seed.length}])),
  fx:{numeric:report.fx.numeric,ND:report.fx.explicit_ND},markets:Object.fromEntries(Object.entries(report.evaluation.markets).map(([k,v])=>[k,{complete:v.complete_current_vintage_5day,incomplete:v.incomplete_current_vintage_5day,by_horizon:v.complete_by_horizon,decisions:v.decisions}]))},null,2));
}
