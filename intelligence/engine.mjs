/** INT-1: deterministic paper-only evidence traces. No I/O or future outcomes. */
import {rankMatches,visibleReactions,validDay} from '../matching/engine.mjs';
import {summarize,median} from '../matching/analysis.mjs';
import {matchingQueryAt} from '../ripple/paths.mjs';
import {validateQuote} from '../trading/core.mjs';

export const POLICY=Object.freeze({id:'int-1-v1',allocation_fraction:.1,min_cases:8,
 horizon:5,max_condition_return_gap:10,max_iqr:5,max_range:15});
const number=v=>(typeof v==='number'||typeof v==='string'&&/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(v))&&Number.isFinite(Number(v));
const change=(a,b)=>a>0?(b/a-1)*100:null;
const stamp=v=>typeof v==='string'&&Number.isFinite(Date.parse(v))&&v.includes('T');
const official=s=>s?.source_kind==='eia_api'&&/^https:\/\/api\.eia\.gov\//.test(s.source_url||'')&&!/[?&](api_key|apiKey)=/i.test(s.source_url);
const hex=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const distribution=values=>{
 values=values.filter(v=>typeof v==='number'&&Number.isFinite(v));
 const sorted=[...values].sort((a,b)=>a-b),n=sorted.length;
 return {count:n,median:median(values),minimum:n?sorted[0]:null,maximum:n?sorted.at(-1):null,
  iqr:n?sorted[Math.floor((n-1)*.75)]-sorted[Math.floor((n-1)*.25)]:null,
  positive:values.filter(v=>v>0).length,negative:values.filter(v=>v<0).length,flat:values.filter(v=>v===0).length};
};

export function auditReplay(data,cursor,quote){
 const fatal=[],limitations=[];
 if(!validDay(cursor))fatal.push('invalid_cursor');
 if(data.quotes.some(q=>!validDay(q.date)))fatal.push('invalid_observation_date');
 const known=data.quotes.filter(q=>validDay(q.date)&&q.date<=cursor),dates=new Set();let previous=null;
 for(const q of known){
  if(dates.has(q.date))fatal.push('duplicate_price_fx_date');dates.add(q.date);
  if(previous&&q.date<=previous)fatal.push('unordered_observations');previous=q.date;
  if(!number(q.price)||Number(q.price)<=0||!number(q.gbpPerUnit)||Number(q.gbpPerUnit)<=0)fatal.push('invalid_price_or_fx');
  const source=data.price_sources[q.snapshot_id];
  if(!source||!hex(source.sha256))fatal.push('missing_price_provenance');
 }
 const exact=known.filter(q=>q.date===cursor);
 if(exact.length!==1)fatal.push('missing_exact_price_fx_pair');
 if(quote&&exact.length===1&&(quote.price!==Number(exact[0].price)||quote.gbpPerUnit!==Number(exact[0].gbpPerUnit)))fatal.push('quote_differs_from_source_pair');
 try{validateQuote(quote,'BRENT','historical',cursor);}catch{fatal.push('instrument_price_fx_mismatch');}
 if(data.instrument!=='Unleveraged fractional Brent spot-price reference, converted to GBP')fatal.push('unsupported_instrument');
 if(!hex(data.input_hashes.prices)||!hex(data.input_hashes.fx)||!hex(data.input_hashes.source_cards))fatal.push('missing_input_fingerprints');
 const cutoff=Date.parse(cursor+'T23:59:59.999Z');
 const primary=known.length>0&&known.every(q=>official(data.price_sources[q.snapshot_id]));
 const fxPrimary=data.sources.fx.verification==='primary_Fed'&&hex(data.sources.fx.upstream_sha256)&&/^https:\/\/(www\.)?federalreserve\.gov\//.test(data.sources.fx.url);
 const clocks=known.every(q=>['available_at','vintage_at','fx_available_at','fx_vintage_at'].every(k=>stamp(q[k])&&Date.parse(q[k])<=cutoff&&Date.parse(q[k])>=Date.parse(q.date+'T00:00:00Z')));
 if(!primary)limitations.push('canonical_prices_provisional');
 if(!clocks||data.point_in_time_safe!==true)limitations.push('original_price_and_fx_vintages_unknown');
 if(!fxPrimary)limitations.push('fx_not_primary_reconciled');
 return {practicable:fatal.length===0,fatal:[...new Set(fatal)],limitations,
  instrument:data.instrument,currency:'GBP',as_of:cursor,known_price_fx_pairs:known.length,
  snapshot_id:data.snapshot_id,input_hashes:data.input_hashes,point_in_time_safe:primary&&fxPrimary&&clocks&&data.point_in_time_safe===true};
}

/** Only observations strictly before publication; thresholds are fixed, not fitted. */
export function preconditions(history,anchor){
 const points=history.filter(p=>validDay(p.date)&&p.date<anchor&&number(p.value)&&Number(p.value)>0).sort((a,b)=>a.date.localeCompare(b.date));
 if(new Set(points.map(p=>p.date)).size!==points.length)return {status:'unknown',reason:'duplicate_pre_event_dates'};
 const recent=points.slice(-21);
 if(recent.length<21)return {status:'unknown',reason:'fewer_than_21_pre_event_observations'};
 // Explicit unavailable observations in the window invalidate the condition.
 const start=recent[0].date;
 if(history.some(p=>p.date>=start&&p.date<anchor&&(!number(p.value)||p.missing_code)))return {status:'unknown',reason:'missing_pre_event_observation'};
 const returns=recent.slice(1).map((p,i)=>change(Number(recent[i].value),Number(p.value))),mean=returns.reduce((a,b)=>a+b,0)/returns.length;
 return {status:'known',through:recent.at(-1).date,from:recent[0].date,
  pre5_percent:change(Number(recent.at(-6).value),Number(recent.at(-1).value)),
  volatility:Math.sqrt(returns.reduce((a,v)=>a+(v-mean)**2,0)/returns.length),
  observations:recent.map(p=>({date:p.date,value:p.value,snapshot_id:p.snapshot_id}))};
}

function asOfPrices(row,cutoff){
 return row.verification==='primary_EIA'&&row.point_in_time_safe===true&&row.observations.every(p=>
  stamp(p.available_at)&&stamp(p.vintage_at)&&Date.parse(p.available_at)<Date.parse(cutoff)&&Date.parse(p.vintage_at)<Date.parse(cutoff)&&
  Date.parse(p.available_at)>=Date.parse(p.date+'T00:00:00Z')&&Date.parse(p.vintage_at)>=Date.parse(p.date+'T00:00:00Z')&&
  official(row.sources[p.snapshot_id])&&hex(row.sources[p.snapshot_id]?.sha256));
}

export function cohortTrace(query,events,history=[],anchor=query.occurred){
 const asOfHistory=history.filter(p=>p.date<query.publicDate);
 const duplicates=new Set(events.filter((e,i)=>events.findIndex(x=>x.id===e.id)!==i).map(e=>e.id));
 const matches=rankMatches(query,events.filter(e=>!duplicates.has(e.id))),base=summarize(matches,query,POLICY.horizon),condition=preconditions(asOfHistory,anchor),cases=[],excluded=[...base.excluded,...[...duplicates].map(id=>({id,reason:'duplicate_event_id'}))];
 // Existing matcher and chronological non-overlap selection run before outcomes.
 let previousContextEnd=null;
 for(const id of base.included_ids){
  const match=matches.find(m=>m.event.id===id),row=visibleReactions(match,query).find(r=>r.days===POLICY.horizon);
  const past=preconditions(asOfHistory,match.event.reactions.anchor);
  const conditionMatch=condition.status==='known'&&past.status==='known'&&
   Math.abs(condition.pre5_percent-past.pre5_percent)<=POLICY.max_condition_return_gap&&
   (condition.volatility===0?past.volatility===0:past.volatility/condition.volatility>=.5&&past.volatility/condition.volatility<=2);
  const blockers=[];
  if(past.status==='known'){
   if(previousContextEnd&&past.from<=previousContextEnd)blockers.push('overlapping_condition_and_reaction_window');
   else previousContextEnd=row.end_date;
  }
  if(!conditionMatch)blockers.push('pre_event_conditions_missing_or_different');
  if(!match.severityMatch)blockers.push('scale_not_comparable');
  if(match.event.first_public.precision!=='minute'||match.event.first_public.status==='not_established')blockers.push('first_public_clock_unknown');
  const points=row.observations;
  const complete=points.length===POLICY.horizon+1&&points.every((p,i)=>validDay(p.date)&&number(p.value)&&Number(p.value)>0&&!p.missing_code&&(!i||p.date>points[i-1].date))&&points[0].date===row.baseline_date&&points.at(-1).date===row.end_date;
  const consistent=complete&&Math.abs(change(Number(points[0].value),Number(points.at(-1).value))-Number(row.change_percent))<=.0001;
  if(!consistent)blockers.push('incomplete_or_inconsistent_price_path');
  if(!asOfPrices(row,query.publicDate+'T00:00:00Z'))blockers.push('primary_as_of_prices_unproven');
  const baseline=past.status==='known'?past.pre5_percent:null;
  cases.push({id,score:match.score,reasons:match.reasons,gaps:match.gaps,scale_match:match.severityMatch,
   baseline_date:row.baseline_date,end_date:row.end_date,observed_percent:consistent?Number(row.change_percent):null,
   prior_window_percent:baseline,baseline_adjusted_percent:baseline===null?null:Number(row.change_percent)-baseline,
   condition:past,blockers,eligible:blockers.length===0,sources:row.sources});
 }
 const eligible=cases.filter(c=>c.eligible),values=eligible.map(c=>c.baseline_adjusted_percent),stats=distribution(values);
 const stable=values.length>=POLICY.min_cases&&[values.slice(0,Math.floor(values.length/2)),values.slice(Math.floor(values.length/2))].every(v=>median(v)>1)&&values.every((_,i)=>median(values.filter((_,j)=>i!==j))>1);
 const supported=stable&&stats.median>1&&stats.positive>=Math.ceil(values.length*.75)&&stats.iqr<=POLICY.max_iqr&&stats.maximum-stats.minimum<=POLICY.max_range;
 return {query,condition,descriptive_cases:cases.length,eligible_cases:eligible.length,cases,excluded,
  observed:distribution(cases.map(c=>c.observed_percent)),baseline_adjusted:stats,
  buy_supported:supported,evidence:eligible.length>=POLICY.min_cases&&stats.iqr<=POLICY.max_iqr&&stats.maximum-stats.minimum<=POLICY.max_range?'Moderate':'Limited',independence_proven:false,
  status:eligible.length<POLICY.min_cases?'insufficient_evidence':supported?'exploratory_support':'mixed_or_unstable',
  baseline_note:'Prior five-observation return, not a proven event-free control or causal excess return.',
  warning:'Non-overlap does not establish independence. Historical counts are not forecast odds.'};
}

export function rippleTrace(data,cursor){
 const available=data.sources.context.filter(s=>s.available_from<=cursor);
 const definitions=[
  ['production','brent_crude','upward','Production disruption may constrain crude supply.','Refinery demand losses and other producers may offset it.'],
  ['refining','brent_crude','downward','Reduced refinery inputs may reduce crude demand.','Production shutdowns may outweigh that demand loss.']];
 return definitions.filter(([id])=>data.sources.ripple_paths.some(p=>p.id===id&&available.some(s=>s.id===p.source_id))).map(([id,market,direction,mechanism,counterargument])=>{
  const source=data.sources.ripple_paths.find(p=>p.id===id).source_id;
  return {id,event_id:data.event_id,classification:'causal_hypothesis',confidence:'Limited',observed_market_effect:false,
   edges:[{order:1,from:data.event_id,to:market,direction,mechanism,source_ids:[source],counterargument},
    {order:2,from:market,to:'fuel_supply_and_costs',direction:'ambiguous',mechanism:'Crude and fuel availability may diverge.',source_ids:[source],counterargument:'Inventories, imports and refining capacity can offset effects.'},
    {order:3,from:'fuel_supply_and_costs',to:'transport_business_costs',direction:'ambiguous',mechanism:'Fuel costs may affect transport margins.',source_ids:[source],counterargument:'Hedging, pricing and demand may offset costs; no transport prices supplied.'}]};
 });
}

export function riskBudget(account,quote){
 const equity=account.cash+account.positions.reduce((sum,p)=>sum+p.units*quote.price*quote.gbpPerUnit,0);
 return {max_allocation_gbp:Math.floor(Math.max(0,Math.min(account.initial,equity))*POLICY.allocation_fraction*100)/100,
  allocation_fraction:POLICY.allocation_fraction,basis:'Full allocation is at risk. A review threshold is not a guaranteed stop loss.'};
}

export function traceDecision({data,catalog,cursor,quote,account,position,entry,elapsed=0,evidence,history}){
 const audit=auditReplay(data,cursor,quote),query=matchingQueryAt(data,catalog,cursor),event=catalog.events.find(e=>e.id===data.event_id);
 if(!stamp(event.features.severity?.published_at)||Date.parse(event.features.severity.published_at)>=Date.parse(query.publicDate+'T00:00:00Z'))query.windSpeed=null;
 const usableHistory=history||data.quotes.filter(q=>q.date<=cursor).map(q=>({date:q.date,value:q.price,snapshot_id:q.snapshot_id}));
 const cohort=cohortTrace(query,catalog.events,usableHistory,event.reactions.anchor),budget=audit.practicable?riskBudget(account,quote):null;
 const blockers=[...audit.fatal,...audit.limitations];
 if(cohort.eligible_cases<POLICY.min_cases)blockers.push('fewer_than_eight_eligible_nonoverlapping_cases');
 if(cohort.condition.status!=='known')blockers.push('pre_event_conditions_unknown');
 const prompt=decidePaper({audit,cohort,budget,position,entry,quote,elapsed,evidence,instrument:data.instrument,cursor});
 return {policy:POLICY,as_of:cursor,event_id:data.event_id,audit,cohort,budget,blockers,ripples:rippleTrace(data,cursor),prompt,
  thesis:{instrument:data.instrument,event_id:data.event_id,source_ids:evidence.source_ids,
   invalidation:['invalid_quote_or_fx','instrument_changed','comparison_support_weakened','newly_public_counterevidence'],
   review_only:true,no_automatic_order:true}};
}

export function decidePaper({audit,cohort,budget,position,entry,quote,elapsed=0,evidence,instrument,cursor}){
 const result=(action,code,reason)=>({action,codes:[code],reason,evidence:cohort.evidence,principal_risk:evidence.principal_risk,paper_only:true});
 let prompt;
 if(!audit.practicable)prompt=result('No Action','data_quality_block','Price, FX or source identity failed validation. No virtual fill is supported.');
 else if(position&&(position.asset!=='BRENT'||entry?.instrument!==instrument||position.entry.date>cursor))prompt=result('No Action','position_instrument_mismatch','Position and review must use the same dated GBP Brent reference.');
 else if(!position&&(!budget||budget.max_allocation_gbp<1))prompt=result('No Action','insufficient_risk_budget','The full-allocation paper risk budget is below the minimum virtual amount.');
 else if(!position)prompt=cohort.buy_supported&&audit.point_in_time_safe?result('Consider Buy','supported_paper_comparison','Comparable as-of evidence supports investigating a budgeted virtual entry; not a forecast.'):result('No Action','insufficient_entry_evidence','Too few source-verified, condition-matched comparisons. Prices and publication vintages remain provisional; manual paper practice is optional.');
 else{
  const move=change(position.entry.price*position.entry.gbpPerUnit,quote.price*quote.gbpPerUnit),plan=entry.exit_criteria;
  if(move<=-plan.loss_percent)prompt=result('Review Sell','loss_review',`The observed GBP reference reached your ${plan.loss_percent}% loss-review rule; daily gaps can exceed it.`);
  else if(move>=plan.profit_percent)prompt=result('Review Sell','gain_review',`The observed GBP reference reached your ${plan.profit_percent}% gain-review rule; this is not a reversal prediction.`);
  else if(elapsed>=plan.horizon)prompt=result('Review Sell','horizon_review',`Your ${plan.horizon}-step review horizon is reached (${elapsed} priced steps). Closing remains your explicit choice.`);
  else if(evidence.updates.some(u=>!entry.evidence_snapshot.source_ids.includes(u.id)))prompt=result('Review Sell','new_source_risk','Newly public refinery evidence adds risk to the paper thesis; it does not predict a fall.');
  else if((entry.decision_trace?.cohort.evidence||entry.evidence_snapshot.evidence)==='Moderate'&&cohort.evidence==='Limited')prompt=result('Review Sell','evidence_weakened','Entry comparison support has weakened. Review the paper risk.');
  else prompt=result('Hold','no_exit_trigger','No saved exit-review rule has triggered. Hold continues the paper exercise; it does not forecast a rise.');
 }
 return prompt;
}
