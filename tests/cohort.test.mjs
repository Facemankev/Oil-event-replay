import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {rankMatches} from '../matching/engine.mjs';
import {analyse,summarize,median,HORIZONS} from '../matching/analysis.mjs';
const catalog=JSON.parse(fs.readFileSync(new URL('../matching/cohort-catalog.json',import.meta.url)));
const q={title:'Hypothetical Gulf storm',category:'weather',market:'brent',location:'Gulf of Mexico',mechanism:'landfall',impact:'mixed',severity:'',windSpeed:null,occurred:'2026-10-29',publicDate:'2026-10-29'};
const cohort=(query=q,days=5)=>analyse(query,catalog.events).opportunities.find(x=>x.market===query.market&&x.days===days);
test('new horizons, counts, medians and signed outcomes use actual library data',()=>{
 assert.deepEqual(HORIZONS,[1,3,5,10,20]);const s=cohort();
 assert.equal(s.eligible_event_count,6);assert.equal(s.comparable_event_count,5);assert.equal(s.location_excluded,1);
 assert.equal(s.window_count,5);assert.equal(s.percent.count,s.percent.positive+s.percent.negative+s.percent.flat);
 assert.equal(s.percent.median,median(s.windows.map(w=>Number(w.change_percent))));
 assert.equal(s.percent.minimum,Math.min(...s.windows.map(w=>Number(w.change_percent))));
 assert.equal(s.percent.maximum,Math.max(...s.windows.map(w=>Number(w.change_percent))));
 assert.equal(s.evidence,'Limited');assert.equal(s.primary_window_count,0);
});
test('overlapping windows are excluded chronologically before outcomes are inspected',()=>{
 const s=cohort(q,20);assert.equal(s.comparable_event_count,5);assert.equal(s.window_count,4);
 assert.ok(s.excluded.some(e=>e.id==='ike-2008-galveston'&&e.reason==='overlapping_price_window'));
 const changed=structuredClone(catalog.events);changed.find(e=>e.id==='ike-2008-galveston').reactions.markets.brent.find(r=>r.days===20).change_percent='999999';
 const result=analyse(q,changed).opportunities.find(x=>x.market==='brent'&&x.days===20);
 assert.deepEqual(result.included_ids,s.included_ids);assert.deepEqual(result.percent,s.percent);
});
test('severity uses known-at, sourced same-unit wind; economic severity is never fabricated',()=>{
 const matches=rankMatches({...q,windSpeed:110},catalog.events);
 const gustav=matches.find(m=>m.event.id==='gustav-2008-louisiana');assert.ok(gustav.severityMatch);
 assert.equal(matches.find(m=>m.event.id==='ida-2021-louisiana').similarity,'Weak');
 assert.equal(cohort({...q,windSpeed:110}).comparable_event_count,3);
 const future=structuredClone(catalog.events);future.find(e=>e.id==='gustav-2008-louisiana').features.severity.published_at='2099-01-01T00:00:00Z';
 assert.equal(rankMatches({...q,windSpeed:110},future).find(m=>m.event.id==='gustav-2008-louisiana').severityMatch,false);
 assert.throws(()=>rankMatches({...q,windSpeed:NaN},catalog.events));
});
test('impact hypotheses cannot match known opposite supply actions',()=>{
 const matches=rankMatches({...q,category:'production_policy',mechanism:'',impact:'supply_expansion',windSpeed:null},catalog.events);
 assert.ok(matches.every(m=>m.event.features.impact!=='supply_constraint'));
 assert.ok(matches.some(m=>m.event.id==='opec-2021-july'));
});
test('no-match and verified-only have null estimates and honest denominators',()=>{
 const empty=cohort({...q,publicDate:'2000-01-01',occurred:'2000-01-01'});assert.equal(empty.percent.count,0);assert.equal(empty.percent.median,null);
 const primary=analyse(q,catalog.events,{verifiedOnly:true}).opportunities;
 assert.ok(primary.every(s=>s.window_count===0&&s.percent.median===null));
});
test('historical cutoffs and self exclusion protect every statistic and ranking input',()=>{
 const historical={...q,excludeId:'harvey-2017-texas',occurred:'2017-08-25',publicDate:'2017-08-26'};
 const old=analyse(historical,catalog.events);
 assert.ok(old.opportunities.every(s=>!s.included_ids.includes(historical.excludeId)&&s.windows.every(w=>w.end_date<historical.publicDate)));
 const changed=structuredClone(catalog.events);
 for(const event of changed)for(const row of Object.values(event.reactions.markets).flat())if(row.end_date>=historical.publicDate){row.change_percent='99999';row.absolute_change='99999';}
 assert.deepEqual(analyse(historical,changed).opportunities,old.opportunities);
});
test('undefined percentages retain absolute moves; invalid numbers cannot become zero',()=>{
 const matches=rankMatches(q,catalog.events).filter(m=>m.event.id==='gustav-2008-louisiana');
 const fixture=structuredClone(matches);const row=fixture[0].event.reactions.markets.brent.find(r=>r.days===5);
 row.change_percent=null;row.absolute_change='-1';let s=summarize(fixture,q,5);
 assert.equal(s.absolute.median,-1);assert.equal(s.percent.median,null);assert.equal(s.undefined_percent_count,1);
 row.absolute_change=' ';s=summarize(fixture,q,5);assert.equal(s.window_count,0);
 row.absolute_change=true;s=summarize(fixture,q,5);assert.equal(s.window_count,0);
});
test('movement relevance is bounded and sign-neutral; stronger evidence always ranks first',()=>{
 const fake=structuredClone(catalog.events);
 for(const event of fake){event.first_public.precision='minute';event.first_public.status='earliest_located_not_exhaustive';
 for(const row of event.reactions.markets.brent){row.verification='primary_EIA';row.change_percent='0.1';}
 for(const row of event.reactions.markets.wti)row.change_percent='99999';}
 const result=analyse({...q,windSpeed:140},fake).opportunities;
 const moderate=result.find(x=>x.evidence==='Moderate');assert.ok(moderate);assert.equal(result[0].evidence,'Moderate');
 const s=cohort();const upside=structuredClone(rankMatches(q,catalog.events));
 for(const m of upside)for(const r of m.event.reactions.markets.brent){r.change_percent='100000';r.absolute_change='100000';}
 const large=summarize(upside,q,5);assert.ok(large.movement_component<=4);
 const downside=structuredClone(upside);for(const m of downside)for(const r of m.event.reactions.markets.brent){r.change_percent='-100000';r.absolute_change='-100000';}
 assert.equal(summarize(downside,q,5).movement_component,large.movement_component);
});
test('deterministic order and exact even/odd medians',()=>{
 assert.equal(median([4,1,2,3]),2.5);assert.equal(median([9,-1,3]),3);assert.equal(median([]),null);
 assert.deepEqual(analyse(q,[...catalog.events].reverse()).opportunities,analyse(q,catalog.events).opportunities);
});
