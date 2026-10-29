import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {rankMatches,visibleReactions,evidenceStrength,validateQuery} from '../matching/engine.mjs';
const catalog=JSON.parse(fs.readFileSync(new URL('../matching/catalog.json',import.meta.url)));
const q={title:'Hypothetical Gulf storm',category:'weather',market:'wti',location:'Texas Gulf of Mexico',
 mechanism:'landfall',severity:'',occurred:'2026-10-29',publicDate:'2026-10-29'};
test('closest category/commodity/mechanism/location first, deterministic ties',()=>{
 const matches=rankMatches(q,catalog.events);assert.equal(matches.length,6);
 assert.equal(matches[0].event.id,'harvey-2017-texas');
 assert.ok(matches[0].reasons.some(x=>x.includes('Location')));
 assert.deepEqual(matches,rankMatches(q,[...catalog.events].reverse()));
 assert.equal(matches.find(x=>x.event.id==='sandy-2012-new-jersey').similarity,'Partial');
});
test('price movements never change rank or make a closer match',()=>{
 const changed=structuredClone(catalog.events);
 changed.forEach(e=>Object.values(e.reactions.markets).flat().forEach(r=>r.change_percent='999999'));
 assert.deepEqual(rankMatches(q,catalog.events).map(m=>[m.event.id,m.score]),rankMatches(q,changed).map(m=>[m.event.id,m.score]));
});
test('opposite policy, unsupported market and mismatched category blocked',()=>{
 const query={...q,category:'production_policy',mechanism:'output_increase',location:'Austria'};
 const matches=rankMatches(query,catalog.events);
 assert.ok(matches.every(m=>!['output_cut','output_hold'].includes(m.event.features.mechanism)));
 assert.throws(()=>rankMatches({...q,market:'gold'},catalog.events));
 assert.throws(()=>rankMatches({...q,mechanism:'output_cut'},catalog.events));
 assert.throws(()=>rankMatches({...q,category:'__proto__'},catalog.events));
});
test('unknown severity never rewarded; broad matches weak and limited',()=>{
 assert.deepEqual(rankMatches(q,catalog.events).map(x=>x.score),rankMatches({...q,severity:'high'},catalog.events).map(x=>x.score));
 const weak=rankMatches({...q,mechanism:'',location:''},catalog.events)[0];
 assert.equal(weak.similarity,'Weak');assert.equal(evidenceStrength(weak,visibleReactions(weak,q)).label,'Limited');
});
test('exclude self and future disclosures; future reaction data hidden',()=>{
 const past={...q,publicDate:'2017-08-26',occurred:'2017-08-25',excludeId:'harvey-2017-texas'};
 const matches=rankMatches(past,catalog.events);assert.ok(matches.every(m=>m.event.id!==past.excludeId&&m.event.reactions.anchor<past.publicDate));
 assert.equal(rankMatches({...q,publicDate:'2000-01-01',occurred:'2000-01-01'},catalog.events).length,0);
 const near={...q,publicDate:'2008-09-16'};const ike=rankMatches(near,catalog.events).find(m=>m.event.id==='ike-2008-galveston');
 const rows=visibleReactions(ike,near);assert.equal(rows[0].status,'ok');assert.equal(rows[1].status,'not_available_at_query_date');assert.equal(rows[1].change_percent,null);
});
test('verified-only hides all provisional numbers; no Strong evidence invented',()=>{
 const match=rankMatches(q,catalog.events)[0];const rows=visibleReactions(match,q,true);
 assert.ok(rows.every(r=>r.status==='primary_verification_required'&&r.change_percent===null&&r.absolute_change===null));
 assert.equal(evidenceStrength(match,rows).label,'Limited');
 const primary=visibleReactions(match,q).map(r=>({...r,verification:'primary_EIA'}));
 assert.equal(evidenceStrength(match,primary).label,'Moderate');
});
test('invalid dates and sparse queries rejected; title never interpreted as facts',()=>{
 for(const date of ['2026-02-30','2026-13-01','2026-1-01','NaN'])assert.throws(()=>validateQuery({...q,publicDate:date}));
 assert.throws(()=>validateQuery({...q,title:''}));
 assert.deepEqual(rankMatches(q,catalog.events).map(m=>m.score),rankMatches({...q,title:'A totally different unparsed description'},catalog.events).map(m=>m.score));
});
