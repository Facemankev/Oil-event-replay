/** Replay-only controller, composed around PR #2's unchanged accounting core. */
import {newAccount,buy,close,advance,clone,validateQuote} from '../trading/core.mjs';
import {evidenceAt} from './paths.mjs';
import {traceDecision,POLICY} from '../intelligence/engine.mjs';
export const DEFAULT_PLAN=Object.freeze({horizon:5,loss_percent:3,profit_percent:5});
const assert=(ok,message)=>{if(!ok)throw Error(message);};
const finite=x=>typeof x==='number'&&Number.isFinite(x);
export const gbpQuote=q=>q.price*q.gbpPerUnit;
export function validatePlan(plan){
 assert(plan&&[1,3,5,10,20].includes(plan.horizon),'Choose a supported review horizon');
 assert(finite(plan.loss_percent)&&plan.loss_percent>=1&&plan.loss_percent<=50,'Loss review must be 1–50%');
 assert(finite(plan.profit_percent)&&plan.profit_percent>=1&&plan.profit_percent<=100,'Gain review must be 1–100%');
 return {horizon:plan.horizon,loss_percent:plan.loss_percent,profit_percent:plan.profit_percent};
}
export function quoteAt(data,date){
 const row=data.quotes.find(q=>q.date===date);if(!row)return null;
 const source=data.price_sources[row.snapshot_id];if(!source)return null;
 const q={asset:'BRENT',mode:'historical',date,price:Number(row.price),currency:'USD',timestamp:date+'T23:59:59.000Z',
  source:'EIA-derived secondary Brent history',evidence:`data/historical/prices.json, snapshot ${row.snapshot_id}, SHA-256 ${source.sha256}`,
  gbpPerUnit:Number(row.gbpPerUnit),fx:{base:'USD',quote:'GBP',rate:Number(row.gbpPerUnit),date,timestamp:date+'T23:59:59.000Z',
   source:data.sources.fx.publisher,evidence:`ripple/fx-harvey-source.csv SHA-256 ${data.input_hashes.fx}; ${data.sources.fx.url}`},
  delaySeconds:0,marketStatus:'Historical daily observation, not live',corporateActions:'Not applicable to a spot reference',availability:data.availability};
 return validateQuote(q,'BRENT','historical',date);
}
export function observedQuotes(data,cursor){return data.quotes.filter(q=>q.date<=cursor).map(q=>quoteAt(data,q.date));}
export function suggest({evidence,position,entry,quote,elapsed=0}){
 const output=(action,code,reason)=>({action,codes:[code],reason,evidence:evidence.evidence,principal_risk:evidence.principal_risk,paper_only:true});
 if(!quote)return output('No Action','missing_quote','A sourced price and same-date FX are required. No previous quote is substituted.');
 if(!position){
  if(evidence.point_in_time_safe&&evidence.conditional.buy_supported)return output('Consider Buy','supported_paper_comparison','The fixed historical path checks support investigating a virtual entry. This is not a real-trade recommendation or a forecast.');
  return output('No Action','insufficient_entry_evidence','Too few reliable historical paths to support a buy prompt. A manual paper experiment is optional.');
 }
 const change=(gbpQuote(quote)/gbpQuote(position.entry)-1)*100,plan=entry.exit_criteria;
 if(change<=-plan.loss_percent)return output('Review Sell','loss_review',`The observed GBP reference fell ${Math.abs(change).toFixed(2)}% since entry, reaching your ${plan.loss_percent}% loss-review rule.`);
 if(change>=plan.profit_percent)return output('Review Sell','gain_review',`The observed GBP reference rose ${change.toFixed(2)}%, reaching your ${plan.profit_percent}% gain-review rule. It is not a forecast of reversal.`);
 if(elapsed>=plan.horizon)return output('Review Sell','horizon_review',`Your ${plan.horizon}-step review horizon is reached (${elapsed} priced steps). Review the paper position; no reversal is assumed.`);
 const update=evidence.updates.find(u=>!entry.evidence_snapshot.source_ids.includes(u.id));
 if(update)return output('Review Sell','new_source_risk','EIA refinery findings published since entry add crude-demand risk. Review the paper thesis; this does not predict a price fall.');
 if(entry.evidence_snapshot.evidence==='Moderate'&&evidence.evidence==='Limited')return output('Review Sell','evidence_weakened','The comparison evidence has weakened since entry. Review the paper position rather than assuming the original thesis still holds.');
 if(evidence.point_in_time_safe&&evidence.conditional.reversal_supported)return output('Review Sell','supported_path_review','Comparable past paths meet the fixed reversal/stability checks. Review the paper risk; sparse endpoint medians alone cannot trigger this prompt.');
 return output('Hold','no_exit_trigger','No chosen exit-review rule has triggered at this observation. Hold means continue the paper exercise, not evidence that prices will rise.');
}

function assess(state,data,catalog){
 const cursor=state.account.cursor,evidence=evidenceAt(data,catalog,cursor),quote=quoteAt(data,cursor);
 const position=state.account.positions[0],entry=position?state.entries[position.id]:null;
 const dates=data.quotes.map(q=>q.date),elapsed=position?dates.indexOf(cursor)-dates.indexOf(position.entry.date):0;
 const intelligence=traceDecision({data,catalog,cursor,quote,account:state.account,position,entry,elapsed,evidence});
 const prompt=state.version===1?suggest({evidence,quote,position,entry,elapsed}):intelligence.prompt;
 return {evidence,quote,position,entry,elapsed,prompt,intelligence};
}
export function current(state,data,catalog){return assess(state,data,catalog);}
function logReview(state,data,catalog,at){
 const a=assess(state,data,catalog),key=[state.account.cursor,a.position?.id||'flat',a.prompt.action,...a.prompt.codes,...a.evidence.source_ids].join('|');
 if(!state.suggestions.some(s=>s.id===key))state.suggestions.push({id:key,as_of:state.account.cursor,recorded_at:at,
  position_id:a.position?.id||null,action:a.prompt.action,codes:a.prompt.codes,reason:a.prompt.reason,
  evidence_snapshot:clone(a.evidence),responses:[],outcome:null});
 if(state.version===2){const review=state.suggestions.find(s=>s.id===key);review.decision_trace=clone(a.intelligence);}
 state.current_review=key;
}
const latest=state=>state.suggestions.find(s=>s.id===state.current_review);
function response(state,choice,op){
 latest(state).responses.push({choice,recorded_at:op.at,as_of:state.account.cursor});
}
function initial(data,catalog,at,version=2){
 assert(quoteAt(data,data.start),'No starting price and FX');
 const state={version,scenario_id:data.scenario_id,data_snapshot:data.snapshot_id,
  account:newAccount(50,'historical',data.start),entries:{},suggestions:[],operations:[]};
 if(version===2)state.policy_version=POLICY.id;
 const operation={kind:'start',at,before:data.start};state.operations.push(operation);logReview(state,data,catalog,at);return state;
}
export function newRun(data,catalog,at=new Date().toISOString()){
 assert(Number.isFinite(Date.parse(at)),'Invalid browser timestamp');return initial(data,catalog,at);
}
export function transact(previous,operation,data,catalog){
 assert(previous.operations.length<1000,'Export and reset: this practice has reached its operation limit');
 const state=clone(previous),op=clone(operation);
 assert(Number.isFinite(Date.parse(op.at))&&op.before===state.account.cursor,'Invalid operation time or replay order');
 const a=assess(state,data,catalog),review=latest(state);
 if(op.kind==='buy'){
  assert(!a.position,'One virtual position at a time');
  const plan=validatePlan(op.plan);
  if(state.version===2){
   assert(a.intelligence.audit.practicable,'Price/FX evidence failed; no paper entry');
   assert(op.amount<=a.intelligence.budget.max_allocation_gbp,`Paper risk budget allows at most £${a.intelligence.budget.max_allocation_gbp.toFixed(2)}. Full allocation is at risk; review rules are not guaranteed stops.`);
  }
  state.account=buy(state.account,'BRENT',op.amount,a.quote,'Manual historical paper experiment; mixed Gulf production/refining hypothesis',Date.parse(op.at));
  const p=state.account.positions[0];
  state.entries[p.id]={event_id:data.event_id,hypothesis:'Gulf production and refining disruption can pull crude prices in opposing directions.',
   selected_market:'Brent spot reference converted to GBP',instrument:data.instrument,entered_at:op.at,entry_date:state.account.cursor,
   entry_price_usd:a.quote.price,entry_fx:a.quote.gbpPerUnit,entry_price_gbp:gbpQuote(a.quote),exit_criteria:plan,
   evidence_snapshot:clone(a.evidence),source_references:[...a.evidence.source_ids,a.quote.evidence,a.quote.fx.evidence],
   data_snapshot:data.snapshot_id,outcome:null};
  if(state.version===2)Object.assign(state.entries[p.id],{risk_budget:clone(a.intelligence.budget),entry_thesis:clone(a.intelligence.thesis),decision_trace:clone(a.intelligence)});
  review.linked_entry_id=p.id;response(state,a.prompt.action==='Consider Buy'?'accepted_paper_buy':'manual_entry_despite_no_buy_prompt',op);
 }else if(op.kind==='advance'){
  state.account=advance(state.account,data.quotes.map(q=>q.date));
 }else if(op.kind==='close'){
  assert(a.position,'No open virtual position');
  if(state.version===2)assert(a.intelligence.audit.practicable&&a.prompt.codes[0]!=='position_instrument_mismatch','Same-instrument quote evidence is required to close');
  state.account=close(state.account,a.position.id,a.quote,Date.parse(op.at));
  response(state,a.prompt.action==='Review Sell'?'accepted_paper_sell':'manual_paper_exit',op);
  const trade=state.account.journal[state.account.journal.length-1];
  const outcome={known_at:state.account.cursor,recorded_at:op.at,close_price_gbp:gbpQuote(a.quote),proceeds_gbp:trade.amountGBP,
   realised_gbp:trade.amountGBP-a.position.cost,change_percent:(gbpQuote(a.quote)/gbpQuote(a.position.entry)-1)*100};
  state.entries[a.position.id].outcome=outcome;
  for(const suggestion of state.suggestions)if(suggestion.position_id===a.position.id||suggestion.linked_entry_id===a.position.id)suggestion.outcome=clone(outcome);
 }else if(op.kind==='respond'){
  assert(['dismissed','accepted_hold','cancelled_buy','cancelled_sell'].includes(op.choice),'Unsupported review response');
  if(op.choice==='accepted_hold')assert(a.prompt.action==='Hold','There is no Hold review to accept');
  assert(!review.responses.some(r=>r.choice===op.choice),'This response is already recorded');response(state,op.choice,op);
 }else throw Error('Unsupported replay operation');
 state.operations.push(op);logReview(state,data,catalog,op.at);return state;
}
export function restoreRun(raw,data,catalog){
 assert(raw&&[1,2].includes(raw.version)&&raw.scenario_id===data.scenario_id&&raw.data_snapshot===data.snapshot_id,'Unsupported backup or changed source snapshot; the saved record is not overwritten');
 assert(Array.isArray(raw.operations)&&raw.operations.length>0&&raw.operations.length<=1000,'Invalid operation ledger');
 const first=raw.operations[0];assert(first.kind==='start'&&first.before===data.start&&Number.isFinite(Date.parse(first.at)),'Invalid starting record');
 if(raw.version===2)assert(raw.policy_version===POLICY.id,'Unsupported paper decision policy; saved record preserved');
 let state=initial(data,catalog,first.at,raw.version);
 for(const op of raw.operations.slice(1))state=transact(state,op,data,catalog);
 for(const key of ['account','entries','suggestions','current_review'])assert(JSON.stringify(raw[key])===JSON.stringify(state[key]),'Backup balances, source evidence or review log differ from their reproducible ledger');
 return state;
}
