import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {historicalMatches,historicalSeries,eventRoute,eventHref} from '../ripple/history.mjs';
import {matchingQueryAt,evidenceAt} from '../ripple/paths.mjs';
import {rankMatches} from '../matching/engine.mjs';
const data=JSON.parse(readFileSync(new URL('../ripple/data.json',import.meta.url))),catalog=JSON.parse(readFileSync(new URL('../matching/cohort-catalog.json',import.meta.url)));
const copy=x=>structuredClone(x),cursor=data.start;

test('history reuses the existing matcher; no future/self/opposite or weak storm matches',()=>{
 const actual=historicalMatches(data,catalog,cursor);
 const expected=rankMatches(matchingQueryAt(data,catalog,cursor),catalog.events).filter(m=>m.similarity!=='Weak'&&m.locationMatch);
 assert.deepEqual(actual,expected);
 assert.deepEqual(new Set(actual.map(m=>m.event.id)),new Set(['gustav-2008-louisiana','ike-2008-galveston']));
 assert(actual.every(m=>m.event.id!==data.event_id&&m.event.reactions.anchor<=cursor));
 assert.equal(evidenceAt(data,catalog,cursor).cohort_count,2);
});
test('no-match state is real and independent of observed price movement',()=>{
 const c=copy(catalog);c.events=c.events.filter(e=>e.id===data.event_id);
 assert.deepEqual(historicalMatches(data,c,cursor),[]);
 const altered=copy(catalog);for(const e of altered.events)for(const rows of Object.values(e.reactions.markets))for(const r of rows)r.change_percent='99999';
 assert.deepEqual(historicalMatches(data,altered,cursor).map(m=>m.event.id),historicalMatches(data,catalog,cursor).map(m=>m.event.id));
});
test('each market has its own sourced dated observations, strictly bounded by replay',()=>{
 const event=historicalMatches(data,catalog,cursor)[0].event;
 const brent=historicalSeries(event,'brent',cursor),wti=historicalSeries(event,'wti',cursor);
 assert(brent.points.length>1&&wti.points.length>1);assert.notDeepEqual(brent.points,wti.points);
 assert.equal(new Set(brent.points.map(p=>p.date)).size,brent.points.length);
 assert(brent.points.every(p=>brent.sources[p.snapshot_id]));
 const cutoff=brent.points[2].date;
 assert(historicalSeries(event,'brent',cutoff).points.every(p=>p.date<=cutoff));
 assert.deepEqual(historicalSeries(event,'gold',cursor),{points:[],sources:{}});
});
test('null/empty/unbacked/conflicting prices remain unavailable; no fabricated zero',()=>{
 const event=copy(historicalMatches(data,catalog,cursor)[0].event),rows=event.reactions.markets.brent;
 for(const row of rows){row.observations[0].value=null;row.observations[1].value='';}
 let result=historicalSeries(event,'brent',cursor);assert.equal(result.points[0].value,null);assert.equal(result.points[1].value,null);
 for(const row of rows)row.observations[0].value='-37.63'; // Synthetic unit fixture only: legitimate negative oil must not disappear.
 result=historicalSeries(event,'brent',cursor);assert.equal(result.points[0].value,-37.63);
 rows[0].observations[0].value='99';assert.equal(historicalSeries(event,'brent',cursor).points[0].value,null);
 for(const row of rows)row.sources={};assert(historicalSeries(event,'brent',cursor).points.every(p=>p.value===null));
});
test('event routes encode identifiers and reject malformed or unsupported paths',()=>{
 assert.deepEqual(eventRoute(eventHref('storm / details','wti')),{id:'storm / details',market:'wti'});
 for(const hash of ['#event/%/brent','#event/id/real-trade','#event/id/brent/extra','#history'])assert.equal(eventRoute(hash),null);
});
