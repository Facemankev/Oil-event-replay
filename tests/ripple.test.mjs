import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {newRun,current,transact,restoreRun,quoteAt,observedQuotes,gbpQuote,suggest,validatePlan} from '../ripple/model.mjs';
import {evidenceAt,conditionalPaths} from '../ripple/paths.mjs';
const data=JSON.parse(readFileSync(new URL('../ripple/data.json',import.meta.url))),catalog=JSON.parse(readFileSync(new URL('../matching/cohort-catalog.json',import.meta.url)));
const at='2026-11-01T21:00:00Z',copy=x=>JSON.parse(JSON.stringify(x));
const start=()=>newRun(data,catalog,at);
const apply=(state,kind,extra={})=>transact(state,{kind,...extra,before:state.account.cursor,at},data,catalog);
const plan={horizon:5,loss_percent:3,profit_percent:5};

test('chart and accounting share genuine same-date GBP quotes; no FX fill',()=>{
 const q=quoteAt(data,'2017-08-28');assert.equal(q.price,51.87);assert.equal(q.gbpPerUnit,.7736);assert.equal(gbpQuote(q),51.87*.7736);
 assert.equal(data.quotes.length,34);assert.equal(quoteAt(data,'2017-09-04'),null);
 const known=observedQuotes(data,'2017-08-28');assert(known.every(q=>q.date<='2017-08-28'));assert.equal(known.at(-1).date,'2017-08-28');
});
test('weak real sample gives No Action, with zero automatic virtual orders',()=>{
 const s=start(),a=current(s,data,catalog);assert.equal(a.prompt.action,'No Action');assert.equal(s.account.positions.length,0);assert.equal(s.account.journal.length,0);
 assert.equal(a.evidence.cohort_count,2);assert.equal(a.evidence.conditional.count,1);assert.equal(a.evidence.conditional.reversal_supported,false);assert.equal(a.evidence.evidence,'Limited');
 assert.throws(()=>evidenceAt(data,catalog,'2017-08-25'),/not available/);
});
test('entry pins the hypothesis, price/FX, sources, evidence and immutable exit plan',()=>{
 const s=apply(start(),'buy',{amount:5,plan}),p=s.account.positions[0],e=s.entries[p.id];
 assert.equal(s.account.cash,45);assert.equal(p.units,5/gbpQuote(quoteAt(data,s.account.cursor)));assert.equal(e.entry_price_gbp,gbpQuote(p.entry));
 assert.equal(e.entry_date,'2017-08-28');assert.equal(e.event_id,data.event_id);assert(e.hypothesis.includes('refining'));assert.deepEqual(e.exit_criteria,plan);
 assert.equal(e.evidence_snapshot.as_of,s.account.cursor);assert(e.source_references.some(x=>x.includes('SHA-256')));assert.equal(e.data_snapshot,data.snapshot_id);
 assert(e.evidence_snapshot.sources.every(source=>source.url.startsWith('https://')&&source.published));
 assert.equal(current(s,data,catalog).prompt.action,'Hold');assert.throws(()=>apply(s,'buy',{amount:5,plan}),/One virtual/);
});
test('no automatic day-three sell: chosen fifth priced step causes a review only',()=>{
 let s=apply(start(),'buy',{amount:5,plan});
 for(let i=1;i<=4;i++){s=apply(s,'advance');assert.equal(current(s,data,catalog).prompt.action,'Hold');}
 assert.equal(s.account.cursor,'2017-09-01');s=apply(s,'advance');assert.equal(s.account.cursor,'2017-09-05');
 assert.deepEqual(current(s,data,catalog).prompt.codes,['horizon_review']);assert.equal(s.account.positions.length,1);assert.equal(s.account.journal.length,1);
 assert(s.suggestions.every(r=>r.outcome===null));
 s=apply(s,'close');assert.equal(s.account.positions.length,0);assert(Math.abs(s.account.cash-50.13557452337451)<.00001);
 assert(s.suggestions.filter(r=>r.position_id||r.linked_entry_id).every(r=>r.outcome.known_at==='2017-09-05'));
});
test('review responses persist without duplicate prompts or implicit trades',()=>{
 let s=apply(start(),'buy',{amount:5,plan});const count=s.suggestions.length;
 s=apply(s,'respond',{choice:'accepted_hold'});assert.equal(s.suggestions.length,count);assert.equal(s.account.journal.length,1);
 assert.throws(()=>apply(s,'respond',{choice:'accepted_hold'}),/already recorded/);
 s=apply(s,'advance');s=apply(s,'respond',{choice:'dismissed'});assert(s.suggestions.at(-1).responses.some(r=>r.choice==='dismissed'));
 const restored=restoreRun(copy(s),data,catalog);assert.deepEqual(restored,s);
});
test('observed loss/gain rules justify reviews without pretending to predict reversal',()=>{
 const s=apply(start(),'buy',{amount:5,plan}),a=current(s,data,catalog);
 for(const [factor,code] of [[.96,'loss_review'],[1.06,'gain_review']]){
  const prompt=suggest({...a,quote:{...a.quote,price:a.quote.price*factor}});assert.equal(prompt.action,'Review Sell');assert.deepEqual(prompt.codes,[code]);
 }
 assert.equal(suggest({...a,quote:null}).action,'No Action');
 for(const bad of [{...plan,horizon:2},{...plan,loss_percent:0},{...plan,profit_percent:Infinity}])assert.throws(()=>validatePlan(bad));
});
test('genuine September findings become eligible after publication, never their measured week',()=>{
 const before=evidenceAt(data,catalog,'2017-09-11'),after=evidenceAt(data,catalog,'2017-09-12');
 assert.equal(before.updates.length,0);assert.equal(after.updates.length,1);assert.equal(after.updates[0].available_from,'2017-09-12');
 let s=apply(start(),'buy',{amount:5,plan:{horizon:20,loss_percent:50,profit_percent:100}});
 while(s.account.cursor<'2017-09-11')s=apply(s,'advance');assert.equal(current(s,data,catalog).prompt.action,'Hold');
 s=apply(s,'advance');assert.equal(s.account.cursor,'2017-09-12');assert.deepEqual(current(s,data,catalog).prompt.codes,['new_source_risk']);
 assert(!s.entries['1'].source_references.includes(after.updates[0].id));
});

// Synthetic UNIT FIXTURES test support gates; never used as production price data.
const fixturePath=(id,direction=-1)=>({id,end_date:`${2000+id}-01-31`,primary:true,precise:true,severity:true,point_in_time_safe:true,
 points:Array.from({length:21},(_,i)=>({date:`${2000+id}-01-${String(i+1).padStart(2,'0')}`,value:String(i<3?100+i:i<6?104:104+direction*4+(id%3)*.1)}))});
test('conditional reversal requires complete, sourced, stable non-overlapping historical paths',()=>{
 const paths=Array.from({length:8},(_,i)=>fixturePath(i));const result=conditionalPaths(paths,3);
 assert.equal(result.count,8);assert.equal(result.reversed,8);assert.equal(result.reversal_supported,true);assert.equal(result.evidence,'Moderate');
 assert.equal(conditionalPaths(paths.slice(0,7),3).reversal_supported,false);
 for(const field of ['primary','precise','severity','point_in_time_safe'])assert.equal(conditionalPaths(paths.map((p,i)=>i? p:{...p,[field]:false}),3).reversal_supported,false);
 const wild=copy(paths);wild[0].points[6].value='10';assert.equal(conditionalPaths(wild,3).reversal_supported,false);
 assert.equal(conditionalPaths(paths,19).count,0);assert.equal(conditionalPaths(paths,19).median_percent,null);
});
test('Consider Buy is paper-only and needs support plus original as-of evidence',()=>{
 const summary=conditionalPaths(Array.from({length:8},(_,i)=>fixturePath(i,1)),3);assert.equal(summary.buy_supported,true);
 const evidence={evidence:'Moderate',principal_risk:'UNIT FIXTURE',point_in_time_safe:true,conditional:summary};
 const prompt=suggest({evidence,quote:quoteAt(data,data.start)});assert.equal(prompt.action,'Consider Buy');assert.equal(prompt.paper_only,true);
 assert.equal(suggest({evidence:{...evidence,point_in_time_safe:false},quote:quoteAt(data,data.start)}).action,'No Action');
 const mixed=Array.from({length:8},(_,i)=>fixturePath(i,i<4?-1:1));assert.equal(conditionalPaths(mixed,3).reversal_supported,false);
});
test('future prices, FX and future events cannot change current chart, evidence or review',()=>{
 const altered=copy(data),cat=copy(catalog);for(const q of altered.quotes)if(q.date>data.start){q.price='99999';q.gbpPerUnit='.0001';}
 for(const e of cat.events)if(e.reactions.anchor>data.start){e.description='Future text';for(const market of Object.values(e.reactions.markets))for(const r of market){r.change_percent=99999;r.absolute_change='99999';}}
 assert.deepEqual(observedQuotes(altered,data.start),observedQuotes(data,data.start));
 assert.deepEqual(evidenceAt(altered,cat,data.start),evidenceAt(data,catalog,data.start));
 assert.deepEqual(current(start(),altered,cat),current(start(),data,catalog));
});
test('missing/invalid historical path values are excluded, never treated as zero',()=>{
 const cat=copy(catalog),gustav=cat.events.find(e=>e.id==='gustav-2008-louisiana');
 gustav.reactions.markets.brent.find(r=>r.days===20).observations[3].value=null;
 const a=evidenceAt(data,cat,data.start);assert.equal(a.conditional.count,0);assert.equal(a.conditional.median_percent,null);assert.equal(a.conditional.reversal_supported,false);
});
test('backup reconstruction rejects altered quotes, review evidence, replay ordering or source revisions',()=>{
 let s=apply(start(),'buy',{amount:5,plan});s=apply(s,'advance');assert.deepEqual(restoreRun(copy(s),data,catalog),s);
 for(const mutate of [r=>r.account.cash=5000,r=>r.entries['1'].entry_fx=1,r=>r.suggestions[0].evidence_snapshot.cohort_count=99,
  r=>r.operations[1].before='2017-09-29',r=>r.data_snapshot='wrong']){const bad=copy(s);mutate(bad);assert.throws(()=>restoreRun(bad,data,catalog));}
 assert.throws(()=>transact(s,{kind:'advance',before:'2017-08-14',at},data,catalog),/replay order/);
});
