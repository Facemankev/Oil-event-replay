import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sha} from '../verification/load.mjs';
import {loadEquities} from '../equities/load.mjs';
import {classify,newsAt,session,marketState,regularMinutes,pricePoint,reactionAt,historicalCrossCheck,replayAt,canonicalURL} from '../equities/engine.mjs';
import {buildReport} from '../equities/evaluate.mjs';
const data=loadEquities(),sources=data.sources.sources,asOf='2026-11-09T21:01:00Z';
const board=data.news.articles.find(a=>a.id==='board-wire');

test('primary news clocks are separate from occurrence, receipt and disputed assertions',()=>{
 assert.equal(board.published_at,'2026-11-08T15:00:00-05:00');assert.equal(board.actual_first_seen_at,null);
 assert.equal(board.original_vintage_verified,false);
 const c=classify(board);assert.deepEqual(c.categories,['leadership','governance','security']);assert(c.allegation_or_inquiry&&c.counterpoint);assert.equal(c.severity,null);
 assert.equal(classify({title:'NVDA announces an export licence restriction',summary:'New regulatory requirement.'}).categories.includes('regulatory'),true);
 assert.equal(classify({title:'An unrelated company has a CEO investigation',summary:'No matched issuer.'}),null);
});
test('the early replay does not know a later board inquiry, response or leadership change',()=>{
 const before=replayAt(data,'2026-11-08T19:59:59Z');
 assert.equal(before.detected.events.length,1);assert(!before.card.what_happened.includes('board opens'));
 assert(!before.card.what_happened.includes('resigned'));
 const sunday=replayAt(data,'2026-11-08T20:01:00Z');assert.equal(sunday.detected.events.length,2);
 assert(sunday.card.what_happened.includes('no reason to believe'));assert(!sunday.card.what_happened.includes('resigned'));
 const monday=replayAt(data,asOf);assert(!monday.detected.events.some(e=>/counsel-update|ceo-transition/.test(e.first_article_id)));
 assert.equal(monday.detected.events.at(-1).actual_first_seen_at,null);
});
test('actual receipt and explicitly dated revisions cannot be backdated to publication',()=>{
 const captured={...board,actual_first_seen_at:'2026-11-14T10:00:00Z'};
 assert.equal(newsAt([captured],sources,asOf).events.length,0);
 const corrected={...board,updated_at:'2026-11-12T15:00:00Z'};
 assert.equal(newsAt([corrected],sources,asOf).events.length,0);
 assert.throws(()=>newsAt([{...board,updated_at:'2026-11-07T00:00:00Z'}],sources,asOf),/precede/);
});
test('syndicated issuer copies and tracking URLs never inflate independent reports',()=>{
 const r=newsAt(data.news.articles,sources,'2026-11-11T12:00:00Z');
 const e=r.events.find(e=>e.first_article_id==='board-wire');assert.equal(e.copies.length,3);assert.equal(e.source_family_count,1);assert.equal(r.duplicates,2);
 assert.equal(canonicalURL(board.url+'?utm_source=repost'),board.url);
 const repeated={...board,id:'reprinted',published_at:'2026-11-09T15:00:00Z'};
 const repeatedResult=newsAt([board,repeated],sources,asOf);
 assert.equal(repeatedResult.events.length,1);assert.equal(repeatedResult.events[0].timing.at,'2026-11-08T20:00:00.000Z');
 assert.throws(()=>canonicalURL('https://nvidianews.nvidia.com/news/x?api_key=untrusted'),/Credential/);
});
test('news source identity is checked and unknown/credentialed sources fail closed',()=>{
 assert.throws(()=>newsAt([{...board,source_id:'unknown'}],sources,asOf),/source/);
 assert.throws(()=>newsAt([{...board,url:'https://example.org/nvidia'}],sources,asOf),/identity/);
 assert.throws(()=>newsAt([{...board,url:'https://someone:private@example.org/'}],sources,asOf),/HTTPS/);
 assert.throws(()=>newsAt([board],sources,asOf,{latencySeconds:-1}),/latency/);
});
test('regular-market schedule handles weekend, daylight saving, holiday, early close and unknown year',()=>{
 const c=data.calendar;
 assert.equal(session(c,'2026-07-06').open,'2026-07-06T13:30:00.000Z');
 assert.equal(session(c,'2026-11-09').open,'2026-11-09T14:30:00.000Z');
 assert.equal(session(c,'2026-11-27').close,'2026-11-27T18:00:00.000Z');
 assert.equal(session(c,'2026-11-26').closed,true);assert.equal(session(c,'2026-11-08').closed,true);
 assert.equal(marketState(c,'2026-11-08T20:01:00Z').next_open,'2026-11-09T14:30:00.000Z');
 assert.equal(marketState(c,'2026-11-09T14:29:59Z').state,'regular_closed');
 assert.equal(marketState(c,'2026-11-09T14:30:00Z').state,'regular_open');
 assert.equal(marketState(c,'2026-11-09T21:00:00Z').state,'regular_closed');
 assert.equal(marketState(c,'2025-11-09T15:00:00Z').state,'unknown_calendar');
 assert.equal(regularMinutes(c,board.published_at,'2026-11-09T14:31:00Z'),1);
});
test('future daily closes never appear as intraday or opening prices; a delayed mid-session story needs a real intraday baseline',()=>{
 const early=reactionAt(data.prices.rows,data.calendar,'NVDA',board.published_at,'2026-11-09T14:31:00Z');
 assert.equal(early.first_regular_close,null);assert.equal(early.first_close_percent,null);
 assert.equal(early.intraday_reaction_status,'unavailable_no_timestamped_intraday_quotes');
 const intraday=reactionAt(data.prices.rows,data.calendar,'NVDA','2026-11-09T15:00:00Z',asOf);
 assert.equal(intraday.first_regular_open,null);assert.equal(intraday.first_close_percent,null);
 assert.equal(intraday.regular_news_baseline,'daily_open_precedes_news; intraday_baseline_missing');
 assert.equal(intraday.daily_context_close_percent,early.baseline? (178.67/186.64-1)*100:null);
});
test('missing expected sessions are not skipped and day-only release eligibility is not an exact news clock',()=>{
 const rows=data.prices.rows.filter(r=>r.date!=='2026-11-09');
 const r=reactionAt(rows,data.calendar,'NVDA',board.published_at,'2026-11-10T21:01:00Z');
 assert.equal(r.expected_first_session,'2026-11-09');assert.equal(r.first_regular_open,null);assert.equal(r.first_regular_close,null);
 const noBaseline=reactionAt(data.prices.rows.filter(r=>r.date!=='2026-11-06'),data.calendar,'NVDA',board.published_at,asOf);
 assert.equal(noBaseline.baseline,null);assert.equal(noBaseline.first_close_percent,null);
 const later=replayAt(data,'2026-11-12T15:00:00Z');
 assert.equal(later.news_publication.precision,'day');assert.equal(later.reaction.first_close_percent,null);
 assert.equal(later.reaction.regular_news_baseline,'news_clock_unknown_initial_reaction_unavailable');
});
test('one-cent opening disagreement is retained, never averaged, rounded away or used as a fill',()=>{
 const p=pricePoint(data.prices.rows,'NVDA','2026-11-09','open');
 assert.equal(p.status,'conflicting_provider_values');assert.equal(p.value,null);assert.equal(p.minimum,173.06);assert.equal(p.maximum,173.07);
 assert.equal(p.verified_exchange_print_at,null);assert.equal(p.original_available_at,null);
 const r=replayAt(data,'2026-11-09T14:31:00Z');assert(r.alert.already_moved);assert.equal(r.action,'No Action');
 assert.equal(r.reaction.open_to_close_percent,null);
 const missing=pricePoint(data.prices.rows,'NVDA','2026-11-08','close');assert.equal(missing.status,'missing');assert.equal(missing.value,null);
});
test('basis mismatch and duplicate provider rows cannot masquerade as independent price agreement',()=>{
 const changed=structuredClone(data.prices.rows),r=changed.find(x=>x.symbol==='NVDA'&&x.date==='2026-11-09');
 r.basis='different_split_adjustment';assert.throws(()=>pricePoint(changed,'NVDA','2026-11-09','close'),/incompatible/);
 const row=data.prices.rows.find(x=>x.symbol==='NVDA'&&x.date==='2026-11-09');
 assert.throws(()=>pricePoint([...data.prices.rows,row],'NVDA','2026-11-09','close'),/incompatible/);
});
test('measured close reaction and market-relative ripples retain opposing signs without causal claims',()=>{
 const r=replayAt(data,asOf);
 assert(Math.abs(r.reaction.first_close_percent.exact-(-4.270252893270465))<1e-8);
 assert(r.ripples.baseline.first_close_percent.exact>2.7);
 for(const c of r.ripples.comparisons){assert(c.reaction.first_close_percent.exact>0);assert.equal(c.classification,'unproven_transmission_hypothesis');}
 assert.equal(r.ripples.causal_effect_established,false);assert.equal(r.reaction.complete_original_as_of,false);
});
test('stale-news detection uses trading minutes and an explicit wall-age cap; late alert never assumes a short',()=>{
 const sunday=replayAt(data,'2026-11-08T20:01:00Z');assert.equal(sunday.alert.regular_minutes_since_publication,0);assert.equal(sunday.alert.status,'research_monitor');
 const close=replayAt(data,asOf);assert.equal(close.alert.status,'stale_context_only');assert.equal(close.alert.actual_historical_alert_proven,false);
 for(const latencySeconds of [0,60,3600,18*3600]){
  const r=replayAt(data,'2026-11-09T15:30:00Z',{latencySeconds});assert.equal(r.action,'No Action');assert.equal(r.paper_trades,0);
 }
});
test('four real corporate cross-checks have transparent mismatches and no qualifying trading cohort',()=>{
 const h=replayAt(data,asOf).historical_cross_check;
 assert.equal(h.matches.length,4);assert.equal(h.qualified_count,0);assert.equal(h.minimum,8);
 assert.equal(h.descriptive.count,3);assert(h.matches.every(e=>e.weaknesses.length&&e.blockers.includes('comparable_severity_unestablished')));
 const h20=h.matches.find(e=>e.id==='nvidia-2025-h20');assert.equal(h20.occurrence_day,'2025-04-09');assert.equal(h20.publication_day,'2025-04-15');
 assert.equal(h.matches.find(e=>e.symbol==='TSLA').reference_close_change_percent,null);
 assert(h.matches.some(e=>e.blockers.includes('different_procedural_stage')));
});
test('historical ranking is outcome-blind; duplicate/future cases and future settlement updates do not become prior evidence',()=>{
 const q=classify(board),h=historicalCrossCheck(q,data.history.cases,sources,asOf),changed=structuredClone(data.history.cases);
 for(const e of changed)for(const p of e.prices)p.close=p.close==='1.00'?'999.00':'1.00';
 const after=historicalCrossCheck(q,changed,sources,asOf);assert.deepEqual(after.matches.map(e=>e.id),h.matches.map(e=>e.id));assert.deepEqual(after.matches.map(e=>e.score),h.matches.map(e=>e.score));
 const future={...data.history.cases[0],id:'future',public_day:'2026-12-01',public_at:'2026-12-01T14:00:00Z'};
 const dup=historicalCrossCheck(q,[...data.history.cases,data.history.cases[0],future],sources,asOf);
 assert.equal(dup.matches.length,4);assert(dup.excluded.some(e=>e.reason==='duplicate_historical_episode'));assert(dup.excluded.some(e=>e.reason==='historical_event_not_yet_public'));
 const old=historicalCrossCheck(q,data.history.cases,sources,'2018-09-30T12:00:00Z').matches.find(e=>e.symbol==='TSLA');assert.equal(old.updates.length,0);
});
test('mutating later news and unobserved daily fields cannot change an earlier decision or reaction',()=>{
 const early='2026-11-09T14:31:00Z',before=replayAt(data,early),changed=structuredClone(data);
 for(const r of changed.prices.rows){if(r.date>'2026-11-09')r.open='999.99';if(r.date>='2026-11-09')r.close='999.99';}
 for(const a of changed.news.articles)if(a.published_day>'2026-11-09')a.summary='NVIDIA CEO resigns amid a regulatory restriction.';
 const after=replayAt(changed,early);
 assert.deepEqual(after,before);
});
test('all eight frozen cutoffs preserve the three-answer contract, abstain and reproduce the report',()=>{
 const r=buildReport();assert.equal(r.summary.No_Action,8);assert.equal(r.summary.Buy,0);assert.equal(r.summary.Short,0);assert.equal(r.summary.paper_trades,0);
 assert.equal(r.summary.daily_provider_rows,66);assert.equal(r.summary.verified_intraday_reactions,0);
 for(const record of r.records)assert.deepEqual(Object.keys(record.card),['what_happened','likely_outcome','suggested_action','historical_details']);
 assert.equal(sha(Buffer.from(JSON.stringify(r,null,2)+'\n')),readFileSync(new URL('../equities/RESULTS.sha256',import.meta.url),'utf8').trim());
});
