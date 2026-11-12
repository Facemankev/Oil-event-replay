/** Reproducible chronological evaluation. Run with Node; never modifies prices. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {cohortTrace,auditReplay,decidePaper,POLICY} from './engine.mjs';
import {quoteAt} from '../ripple/model.mjs';
import {nextDay} from '../ripple/paths.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const read=path=>JSON.parse(readFileSync(resolve(root,path),'utf8'));
const hash=path=>createHash('sha256').update(readFileSync(resolve(root,path))).digest('hex');
const numeric=v=>(typeof v==='number'||typeof v==='string'&&/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(v))&&Number.isFinite(Number(v));
const positive=p=>numeric(p.value)&&Number(p.value)>0&&!p.missing_code;
export const COSTS=Object.freeze({fee_gbp_per_leg:.01,spread_bps:10,slippage_bps_per_leg:5});

/** Costed, observed GBP baseline. Missing FX never uses a prior rate. */
export function baselineTrade(quotes,start,amount=5,horizon=5,costs=COSTS){
 const index=quotes.findIndex(q=>q.date===start),window=index<0?[]:quotes.slice(index,index+horizon+1);
 if(window.length!==horizon+1)return null;
 if(!window.every((q,i)=>numeric(q.price)&&Number(q.price)>0&&numeric(q.gbpPerUnit)&&Number(q.gbpPerUnit)>0&&(!i||q.date>window[i-1].date)))return null;
 const friction=(costs.spread_bps/2+costs.slippage_bps_per_leg)/10000;
 if(![amount,horizon,...Object.values(costs)].every(Number.isFinite)||amount<1||!Number.isInteger(horizon)||horizon<1||Object.values(costs).some(v=>v<0))throw Error('Invalid evaluation parameters');
 if(!Number.isFinite(friction)||friction<0||friction>=1||costs.fee_gbp_per_leg<0||costs.fee_gbp_per_leg>=amount)throw Error('Invalid evaluation cost assumptions');
 const price=q=>Number(q.price)*Number(q.gbpPerUnit),units=(amount-costs.fee_gbp_per_leg)/(price(window[0])*(1+friction));
 const marks=window.map(q=>50-amount+units*price(q)*(1-friction)-costs.fee_gbp_per_leg);
 let peak=50,drawdown=0;for(const value of marks){peak=Math.max(peak,value);drawdown=Math.max(drawdown,(peak-value)/peak*100);}
 const proceeds=units*price(window.at(-1))*(1-friction)-costs.fee_gbp_per_leg;
 return {entry_date:start,exit_date:window.at(-1).date,instrument:'GBP Brent reference',allocation_gbp:amount,
  entry_reference_gbp:price(window[0]),exit_reference_gbp:price(window.at(-1)),net_pnl_gbp:proceeds-amount,
  final_cash_gbp:50-amount+proceeds,max_observed_drawdown_percent:drawdown,costs,observed_dates:window.map(q=>q.date)};
}

export function evaluate(catalog,priceSeries,replay){
 const history=priceSeries.observations,events=[...catalog.events].filter(e=>e.reactions.anchor).sort((a,b)=>a.reactions.anchor.localeCompare(b.reactions.anchor)||a.id.localeCompare(b.id));
 const decisions=[];
 // Freeze all decisions before reading any held-out outcome.
 for(const event of events){
  const day=history.find(p=>p.date>event.reactions.anchor&&positive(p))?.date;
  const query={title:event.title,category:event.category,market:'brent',occurred:event.occurred.date,
   publicDate:day?nextDay(day):nextDay(event.reactions.anchor),location:event.geography,
   mechanism:event.features.mechanism,impact:event.features.impact,severity:'',excludeId:event.id,
   windSpeed:event.features.severity&&Date.parse(event.features.severity.published_at)<Date.parse((day||event.reactions.anchor)+'T23:59:59Z')?event.features.severity.value:null};
  const past=history.filter(p=>p.date<(day?nextDay(day):event.reactions.anchor));
  const cohort=cohortTrace(query,catalog.events,past,event.reactions.anchor);
  const quote=day?quoteAt(replay,day):null;
  const audit=quote?auditReplay(replay,day,quote):{practicable:false,point_in_time_safe:false,fatal:['no_exact_gbp_price_fx_pair'],limitations:['canonical_prices_provisional','original_vintages_unknown']};
  const prompt=decidePaper({audit,cohort,budget:{max_allocation_gbp:5},position:null,quote,
   evidence:{principal_risk:'Supply/demand effects and other news can oppose each other.'},instrument:replay.instrument,cursor:day});
  decisions.push({event_id:event.id,occurred:event.occurred,first_public:event.first_public,comparison_anchor:event.reactions.anchor,
   decision_day:day||null,query,action:prompt.action,codes:prompt.codes,audit,cohort});
 }
 const records=decisions.map(decision=>{
  const baseline=decision.decision_day?baselineTrade(replay.quotes,decision.decision_day):null;
  const index=history.findIndex(p=>p.date===decision.decision_day),future=index<0?[]:history.slice(index,index+6);
  const outcome=future.length===6&&future.every(positive)?{known_on:future.at(-1).date,
   brent_usd_percent:(Number(future.at(-1).value)/Number(future[0].value)-1)*100,
   interpretation:'Retrospective benchmark outcome, not GBP trading P&L or an input to this decision.'}:null;
  return {...decision,outcome,simple_baseline:baseline};
 });
 const entries=records.filter(r=>r.action==='Consider Buy'),baselines=records.filter(r=>r.simple_baseline),outcomes=records.filter(r=>r.outcome);
 // Current production evidence must abstain. Do not manufacture fills for a
 // future supported policy: execution requires a separate reviewed evaluator.
 if(entries.length)throw Error('Supported signals require reviewed costed execution evaluation before reporting strategy performance');
 return {method:'int-1-walk-forward-v1',policy:POLICY,market:'brent',instrument:replay.instrument,
  protocol:{test_order:'Publication-anchor chronology; each case is held out from its own training cohort.',horizon:5,
   entry:'First Brent observation strictly after the evidence anchor; GBP practice requires exact same-date FX.',
   baseline:'No-trade cash and fixed £5 entry/5 jointly priced steps, selected without outcomes.',
   costs:COSTS,missed_positive_threshold_percent:1,thresholds_fitted:false,point_in_time_safe:false},
  summary:{events:records.length,priced_gbp_cases:baselines.length,observed_usd_outcomes:outcomes.length,
   abstentions:records.length,entries:0,false_positives:null,false_positive_note:'Undefined: zero supported entries, not proof of accuracy.',
   negative_examples:outcomes.filter(r=>r.outcome.brent_usd_percent<0).length,
   abstained_positive_examples:outcomes.filter(r=>r.outcome.brent_usd_percent>1).length,
   unpriced_or_incomplete_gbp_cases:records.length-baselines.length,
   strategy:{final_cash_gbp:50,net_pnl_gbp:0,max_observed_drawdown_percent:0,interpretation:'Cash only because every signal abstained; no predictive performance established.'},
   no_trade:{final_cash_gbp:50,net_pnl_gbp:0},simple_baselines:baselines.map(r=>({event_id:r.event_id,...r.simple_baseline}))},
  limitations:['Retrospective source vintages, not a fully point-in-time backtest.','24 selected research records, not an exhaustive news feed; unrecorded events cannot be measured.',
   'Non-overlap reduces repeated windows but does not prove independence.','GBP FX coverage exists only for the supplied 2017 slice; no WTI GBP trades or fabricated FX.',
   'Prior-window comparison is not an event-free control. Costs are declared assumptions, not executable quotes.'],records};
}

export function buildReport(){
 const replay=read('ripple/data.json'),catalog=read('matching/cohort-catalog.json'),prices=read('data/historical/prices.json');
 const names={prices:'data/historical/prices.json',fx:'ripple/fx-harvey-source.csv',source_cards:'ripple/sources.json'};
 for(const [key,path] of Object.entries(names))if(hash(path)!==replay.input_hashes[key])throw Error('Changed input snapshot: '+path);
 const brent=prices.series.find(s=>s.series==='brent');
 return {schema_version:1,canonical_observation_count:prices.series.reduce((n,s)=>n+s.observations.filter(p=>p.value!==null).length,0),
  inputs:Object.fromEntries([...Object.values(names),'ripple/data.json','matching/cohort-catalog.json','intelligence/eia-review.json'].map(p=>[p,hash(p)])),
  eia_review:read('intelligence/eia-review.json'),evaluation:evaluate(catalog,brent,replay)};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const report=buildReport(),text=JSON.stringify(report,null,2)+'\n';
 if(process.argv.includes('--check')){
  if(readFileSync(resolve(root,'intelligence/REPORT.sha256'),'utf8').trim()!==createHash('sha256').update(text).digest('hex'))throw Error('INT-1 report differs; review inputs and regenerate explicitly');
 }else if(process.argv.includes('--output')){
  const path=resolve(process.argv[process.argv.indexOf('--output')+1]);
  const protectedDirs=['data','historical','world_events','matching','ripple','trading'];
  if(protectedDirs.some(d=>path===resolve(root,d)||path.startsWith(resolve(root,d)+'/')))throw Error('Refusing a canonical/source output path');
  mkdirSync(dirname(path),{recursive:true});writeFileSync(path,text,{flag:'wx'});
 }
 console.log(JSON.stringify({canonical_observations:report.canonical_observation_count,...report.evaluation.summary},null,2));
}
