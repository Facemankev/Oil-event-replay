import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {auditReplay,cohortTrace,preconditions,rippleTrace,decidePaper,POLICY} from '../intelligence/engine.mjs';
import {baselineTrade,buildReport,evaluate} from '../intelligence/evaluate.mjs';
import {newRun,current,transact,restoreRun,quoteAt} from '../ripple/model.mjs';
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url)));
const data=read('ripple/data.json'),catalog=read('matching/cohort-catalog.json'),series=read('data/historical/prices.json').series.find(s=>s.series==='brent');
const at='2026-11-12T22:00:00Z',copy=structuredClone,plan={horizon:5,loss_percent:3,profit_percent:5};
const apply=(s,kind,extra={})=>transact(s,{kind,...extra,before:s.account.cursor,at},data,catalog);

test('real trace abstains, preserves source IDs and labels ripple effects as hypotheses',()=>{
 const state=newRun(data,catalog,at),trace=current(state,data,catalog).intelligence;
 assert.equal(state.version,2);assert.equal(state.policy_version,POLICY.id);assert.equal(trace.prompt.action,'No Action');
 assert.equal(trace.audit.practicable,true);assert.equal(trace.audit.point_in_time_safe,false);
 assert.equal(trace.cohort.descriptive_cases,2);assert.equal(trace.cohort.eligible_cases,0);
 assert(trace.blockers.includes('pre_event_conditions_unknown'));
 assert.equal(trace.ripples.length,2);
 assert(trace.ripples.every(r=>r.confidence==='Limited'&&!r.observed_market_effect&&r.edges.length===3&&r.edges.every(e=>e.source_ids.length&&e.counterargument)));
 assert.deepEqual(rippleTrace(data,'2017-08-25'),[]);
 assert(!JSON.stringify(trace).includes('eia-harvey-refinery-update-2017'));
});
test('same-day quote, source, duplicates, identity, FX and numeric integrity fail closed',()=>{
 const q=quoteAt(data,data.start),bad=copy(data);bad.quotes.push(copy(bad.quotes.find(p=>p.date===data.start)));
 assert(auditReplay(bad,data.start,q).fatal.includes('duplicate_price_fx_date'));
 for(const quote of [{...q,asset:'WTI'},{...q,fx:{...q.fx,date:'2017-08-25'}},{...q,price:0},{...q,price:q.price+1},{...q,gbpPerUnit:q.gbpPerUnit+.01},null])assert.equal(auditReplay(data,data.start,quote).practicable,false);
 const missing=copy(data);missing.price_sources={};assert.equal(auditReplay(missing,data.start,q).practicable,false);
 assert.equal(auditReplay(data,'2017-09-04',null).practicable,false);
});
test('future outcomes and future evidence do not alter an earlier decision trace',()=>{
 const state=newRun(data,catalog,at),before=current(state,data,catalog).intelligence,d=copy(data),c=copy(catalog);
 for(const q of d.quotes)if(q.date>data.start){q.price='9999';q.gbpPerUnit='9';}
 for(const event of c.events)if(event.reactions.anchor>data.start){event.title='FUTURE UNIT FIXTURE';for(const row of event.reactions.markets.brent)row.change_percent='9000';}
 assert.deepEqual(current(state,d,c).intelligence,before);
});
test('risk budget treats the full allocation as at risk and persists the entry thesis',()=>{
 const state=newRun(data,catalog,at);assert.throws(()=>apply(state,'buy',{amount:6,plan}),/risk budget/);
 const entered=apply(state,'buy',{amount:5,plan}),entry=entered.entries['1'];
 assert.equal(entry.risk_budget.max_allocation_gbp,5);assert.equal(entry.entry_price_gbp,51.87*.7736);
 assert.equal(entry.entry_thesis.instrument,data.instrument);assert(entry.entry_thesis.invalidation.includes('newly_public_counterevidence'));
 assert.equal(entry.decision_trace.prompt.action,'No Action');assert.equal(current(entered,data,catalog).prompt.action,'Hold');
 let reviewed=entered;for(let i=0;i<5;i++)reviewed=apply(reviewed,'advance');
 assert.equal(reviewed.account.cursor,'2017-09-05');assert.equal(current(reviewed,data,catalog).prompt.action,'Review Sell');
 assert.equal(reviewed.account.positions.length,1);assert.equal(reviewed.account.journal.length,1);
 assert.deepEqual(restoreRun(copy(reviewed),data,catalog),reviewed);
 const forged=copy(reviewed);forged.suggestions[0].decision_trace.budget.max_allocation_gbp=50;
 assert.throws(()=>restoreRun(forged,data,catalog),/differ/);
});
test('PR #26 version-one backups reconstruct exactly without migration or lost positions',()=>{
 const fixture=read('tests/fixtures/int1-legacy-v1.json'),old=fixture.record;
 assert.equal(fixture.source_commit,'20f54bb720ba0f1fbb11a710ec53f6c880c4a284');
 assert.equal(old.version,1);const restored=restoreRun(copy(old),data,catalog);assert.deepEqual(restored,old);
 assert.equal(current(restored,data,catalog).prompt.action,'Hold');assert.equal(apply(restored,'advance').version,1);
});
test('conditions use only prior prices and never fill nulls or duplicates',()=>{
 const history=series.observations,anchor='2017-08-26',result=preconditions(history,anchor);
 assert.equal(result.status,'known');assert(result.observations.every(p=>p.date<anchor));
 const changed=copy(history);for(const p of changed)if(p.date>=anchor)p.value='99999';assert.deepEqual(preconditions(changed,anchor),result);
 const short=result.observations.slice(1);assert.equal(preconditions(short,anchor).status,'unknown');
 const gap=copy(result.observations);gap[5].value=null;assert.equal(preconditions(gap,anchor).status,'unknown');
 assert.equal(preconditions([...result.observations,result.observations[0]],anchor).reason,'duplicate_pre_event_dates');
});

// All synthetic records below are UNIT FIXTURES ONLY, never event research or performance.
function supportedFixture(){
 const events=[],history=[];
 for(const year of [2000,2001,2002,2003,2004,2005,2006,2007,2010]){
  for(let n=1;n<=21;n++)history.push({date:`${year}-05-${String(n).padStart(2,'0')}`,value:'100',snapshot_id:'unit'});
  if(year===2010)continue;
  const e=copy(catalog.events[0]);e.id='unit-only-'+year;e.occurred.date=`${year}-06-01`;
  e.first_public={status:'earliest_located_not_exhaustive',precision:'minute',date:e.occurred.date,at:e.occurred.date+'T12:00:00Z'};
  e.features.severity.published_at=e.first_public.at;e.reactions.anchor=e.occurred.date;
  const dates=[`${year}-05-31`,...['02','03','04','07','08'].map(d=>`${year}-06-${d}`)];
  const row={days:5,status:'ok',verification:'primary_EIA',point_in_time_safe:true,baseline_date:dates[0],end_date:dates.at(-1),baseline:'100',end:'107',absolute_change:'7',change_percent:'7',
   sources:{unit:{source_kind:'eia_api',source_url:'https://api.eia.gov/v2/petroleum/pri/spt/data/',sha256:'a'.repeat(64)}},observations:dates.map((date,i)=>({date,value:String(100+i*1.4),snapshot_id:'unit',available_at:date+'T23:00:00Z',vintage_at:date+'T23:00:00Z'}))};
  e.reactions.markets.brent=[row];events.push(e);
 }
 return {events,history,query:{title:'UNIT FIXTURE',category:'weather',market:'brent',occurred:'2010-06-01',publicDate:'2010-06-03',location:'Gulf of Mexico',mechanism:'landfall',impact:'mixed',windSpeed:110,severity:''}};
}
test('Buy needs eight condition/scale/source/clock qualified non-overlapping cases',()=>{
 const f=supportedFixture(),cohort=cohortTrace(f.query,f.events,f.history);
 assert.equal(cohort.eligible_cases,8);assert.equal(cohort.buy_supported,true);
 const input={audit:{practicable:true,point_in_time_safe:true},cohort,budget:{max_allocation_gbp:5},evidence:{principal_risk:'UNIT ONLY'}};
 assert.equal(decidePaper(input).action,'Consider Buy');
 assert.equal(decidePaper({...input,audit:{practicable:true,point_in_time_safe:false}}).action,'No Action');
 assert.equal(decidePaper({...input,budget:{max_allocation_gbp:.5}}).action,'No Action');
 for(const mutation of [e=>e.reactions.markets.brent[0].point_in_time_safe=false,e=>e.reactions.markets.brent[0].observations[2].value=null,e=>e.features.severity.value=200,e=>e.reactions.markets.brent[0].end_date='2030-01-01']){
  const changed=copy(f.events);mutation(changed[0]);assert.equal(cohortTrace(f.query,changed,f.history).buy_supported,false);
 }
 const duplicated=[...f.events,copy(f.events[0])];assert.equal(cohortTrace(f.query,duplicated,f.history).eligible_cases,7);
 const overlap=copy(f.events);overlap[1].reactions=copy(overlap[0].reactions);assert.equal(cohortTrace(f.query,overlap,f.history).buy_supported,false);
});
test('unstable or opposing historical outcomes cannot become an attractive gain forecast',()=>{
 const f=supportedFixture();for(const e of f.events){const row=e.reactions.markets.brent[0];row.end='93';row.absolute_change='-7';row.change_percent='-7';row.observations.at(-1).value='93';}
 const cohort=cohortTrace(f.query,f.events,f.history);assert.equal(cohort.buy_supported,false);assert.equal(cohort.baseline_adjusted.negative,8);assert.equal(cohort.evidence,'Moderate');
});
test('same instrument and newly-public invalidation reviews are position-aware',()=>{
 let state=apply(newRun(data,catalog,at),'buy',{amount:5,plan:{horizon:20,loss_percent:50,profit_percent:100}});
 while(state.account.cursor<'2017-09-11')state=apply(state,'advance');assert.equal(current(state,data,catalog).prompt.action,'Hold');
 state=apply(state,'advance');assert.deepEqual(current(state,data,catalog).prompt.codes,['new_source_risk']);
 const invalid=copy(state);invalid.entries['1'].instrument='WTI';assert.deepEqual(current(invalid,data,catalog).prompt.codes,['position_instrument_mismatch']);assert.throws(()=>apply(invalid,'close'),/Same-instrument/);
});
test('chronological report covers all real cases, negative outcomes, abstentions and honest FX coverage',()=>{
 const report=buildReport();assert.equal(report.canonical_observation_count,10368);
 const e=report.evaluation;assert.equal(e.summary.events,24);assert.equal(e.summary.abstentions,24);assert.equal(e.summary.entries,0);
 assert.equal(e.summary.priced_gbp_cases,1);assert.equal(e.summary.unpriced_or_incomplete_gbp_cases,23);
 assert.equal(e.summary.negative_examples,16);assert.equal(e.summary.abstained_positive_examples,7);assert.equal(e.summary.false_positives,null);
 assert(e.records.every(r=>r.cohort.cases.every(c=>c.id!==r.event_id&&c.end_date<r.query.publicDate)));
 assert(e.records.every(r=>r.outcome===null||r.outcome.known_on>r.decision_day));
 assert(e.summary.simple_baselines[0].net_pnl_gbp<.1355746);assert.equal(e.summary.strategy.final_cash_gbp,50);
 const truncated=copy(series);truncated.observations=truncated.observations.filter(p=>p.date<='2017-08-28');
 const before=e.records.find(r=>r.event_id===data.event_id),after=evaluate(catalog,truncated,data).records.find(r=>r.event_id===data.event_id);
 assert.deepEqual(after.cohort,before.cohort);assert.equal(after.action,before.action);
});
test('known condition/reaction overlap is excluded before considering movement',()=>{
 const event=catalog.events.find(e=>e.id===data.event_id),query={title:event.title,category:event.category,market:'brent',occurred:event.occurred.date,publicDate:'2017-08-29',location:'Gulf of Mexico',mechanism:'landfall',impact:'mixed',windSpeed:125,severity:'',excludeId:event.id};
 const cohort=cohortTrace(query,catalog.events,series.observations,event.reactions.anchor);
 assert(cohort.cases.find(c=>c.id==='ike-2008-galveston').blockers.includes('overlapping_condition_and_reaction_window'));
});
test('costed baseline requires exact FX observations and reports costs/drawdown without hidden fills',()=>{
 const costed=baselineTrade(data.quotes,'2017-08-28'),free=baselineTrade(data.quotes,'2017-08-28',5,5,{fee_gbp_per_leg:0,spread_bps:0,slippage_bps_per_leg:0});
 assert(costed.net_pnl_gbp<free.net_pnl_gbp);assert(costed.max_observed_drawdown_percent>0);
 assert.equal(costed.exit_date,'2017-09-05');assert(!costed.observed_dates.includes('2017-09-04'));
 assert.equal(baselineTrade(data.quotes,'2017-09-04'),null);assert.equal(baselineTrade(data.quotes,'2017-09-29'),null);
});
