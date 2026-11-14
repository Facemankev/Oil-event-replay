import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadPrimary,json,sha} from '../verification/load.mjs';
import {pairedHistory} from '../verification/evaluate.mjs';
import {loadStudy,validateReleases,fxEvidenceAt,selectAnalogues,qualifiedCohort,deriveCatalog,rippleEvidenceAt,episode} from '../analogues/engine.mjs';
import {buildStudy} from '../analogues/evaluate.mjs';
const primary=loadPrimary(),inputs=loadStudy(),original=json('matching/cohort-catalog.json');
const catalog=deriveCatalog(primary,{...original,events:[...original.events,...inputs.extra.events]});
const event=id=>catalog.events.find(e=>e.id===id),history=pairedHistory(primary,'brent');
const cutoff='2024-09-13T00:00:00.000Z';
const select=(id,events=catalog.events,at=cutoff)=>selectAnalogues(event(id),events,history,'brent',at);

test('eight additional primary-sourced storms retain occurrence, issuance and operational estimates',()=>{
 assert.equal(inputs.extra.events.length,8);assert.equal(catalog.events.length,32);
 for(const e of inputs.extra.events){assert.equal(episode(e),e.episode_id);assert(Date.parse(e.occurred.at)<=Date.parse(e.first_public.at));assert.equal(e.evidence[0].original_http_sha256,null);assert(e.evidence[0].capture_kind.includes('403'));}
 assert.equal(event('isaac-2012-louisiana').occurred.at,'2012-08-28T18:45:00-05:00');
 assert.equal(event('isaac-2012-louisiana').first_public.at,'2012-08-28T19:00:00-05:00');
 assert.equal(event('zeta-2020-louisiana').features.severity.value,110);
 assert.equal(event('dolly-2008-texas').features.severity.published_at,'2008-07-23T12:00:00-05:00');
});
test('dated release is unavailable at observation time and at its strict conservative boundary',()=>{
 const releases=inputs.releaseData.releases;
 for(const cutoff of ['2017-08-29T00:00:00Z','2017-09-05T23:59:59Z','2017-09-07T00:00:00Z'])assert.equal(fxEvidenceAt(releases,'2017-08-28',cutoff).status,'no_eligible_dated_release');
 const x=fxEvidenceAt(releases,'2017-08-28','2017-09-07T00:00:00.001Z');
 assert.equal(x.value,'1.2927');assert.equal(x.printed_release_date,'2017-09-05');assert.equal(x.original_release_at,null);assert.equal(x.original_vintage_verified,false);
 assert.throws(()=>fxEvidenceAt(releases,'2017-08-28','2017-09-08'),/cutoff/);
});
test('explicit ND stays unavailable and dated-page corroboration does not prove a vintage',()=>{
 const x=fxEvidenceAt(inputs.releaseData.releases,'2017-09-04','2017-09-14T00:00:00Z');
 assert.equal(x.status,'documented_unavailable');assert.equal(x.value,null);assert.equal(x.original_vintage_verified,false);
 for(const mutate of [r=>r.unit='GBP per USD',r=>r.observations[1].date=r.observations[0].date,r=>r.observations[0].value='0.0000',r=>r.release_at='2017-09-05T00:00:00Z']){
  const r=structuredClone(inputs.releaseData.releases);mutate(r[0]);assert.throws(()=>validateReleases(r));
 }
});
test('Harvey gains Dolly without treating weaker wind, Sandy or overlapping Ike as qualifying cases',()=>{
 const x=select('harvey-2017-texas',catalog.events,'2017-08-29T00:00:00Z');
 assert.deepEqual(x.selected.map(c=>c.id),['dolly-2008-texas','gustav-2008-louisiana']);
 assert(x.excluded.some(c=>c.id==='humberto-2007-texas'&&c.reason==='operational_wind_not_comparable'));
 assert(x.excluded.some(c=>c.id==='sandy-2012-new-jersey'&&c.reason==='different_or_unestablished_exposure_region'));
 assert(x.excluded.some(c=>c.id==='ike-2008-galveston'&&c.reason==='overlapping_context_and_reaction'));
 const old=deriveCatalog(primary,original);
 assert.equal(selectAnalogues(event('harvey-2017-texas'),old.events,history,'brent','2017-08-29T00:00:00Z').selected.length,1);
});
test('two landfalls or later bulletins from one storm never create independent cases',()=>{
 const first=event('nate-2017-louisiana'),later=structuredClone(first);
 later.id='nate-later-bulletin';later.first_public.at='2017-10-08T00:30:00-05:00';later.first_public.date='2017-10-08';
 // Deliberately more attractive complete returns must not replace the first bulletin.
 later.reactions.markets.brent[2].status='ok';later.reactions.markets.brent[2].change_percent='99';
 const a=select('francine-2024-louisiana'),b=select('francine-2024-louisiana',[...catalog.events,later]);
 assert.deepEqual(b.selected.map(c=>c.id),a.selected.map(c=>c.id));
 assert(b.excluded.some(c=>c.id===later.id&&c.reason==='repeated_bulletin_same_episode'));
});
test('full context and reaction overlap is reserved before gaps or results are examined',()=>{
 const x=select('francine-2024-louisiana');
 assert(x.selected.some(c=>c.id==='delta-2020-louisiana'));
 assert(x.excluded.some(c=>c.id==='zeta-2020-louisiana'&&c.reason==='overlapping_context_and_reaction'));
 const changed=structuredClone(catalog.events);
 for(const e of changed)for(const row of e.reactions.markets.brent){row.status='failed';row.change_percent='999';row.observations=[];}
 assert.deepEqual(select('francine-2024-louisiana',changed).selected.map(c=>c.id),x.selected.map(c=>c.id));
 for(let i=1;i<x.selected.length;i++)assert(x.selected[i].from>x.selected[i-1].through);
});
test('unknown episode, duplicate ID and unpublished severity fail closed',()=>{
 const dup=structuredClone(event('dolly-2008-texas'));
 const duplicate=select('harvey-2017-texas',[...catalog.events,dup],'2017-08-29T00:00:00Z');
 assert(!duplicate.selected.some(c=>c.id===dup.id));assert(duplicate.excluded.some(c=>c.reason==='duplicate_event_id'));
 const changed=structuredClone(catalog.events),d=changed.find(e=>e.id===dup.id);delete d.episode_id;d.evidence=[];
 assert(select('harvey-2017-texas',changed,'2017-08-29T00:00:00Z').excluded.some(c=>c.id===dup.id&&c.reason==='independent_episode_unidentified'));
 const q=structuredClone(event('harvey-2017-texas'));q.features.severity.published_at='2026-01-01T00:00:00Z';
 assert.equal(selectAnalogues(q,catalog.events,history,'brent','2017-08-29T00:00:00Z').selected.length,0);
});
test('future event knowledge and future price observations cannot change earlier frozen decisions',()=>{
 const before=qualifiedCohort(event('harvey-2017-texas'),catalog.events,primary,'brent','2017-08-29T00:00:00Z',inputs.releaseData.releases);
 const changed=structuredClone(primary);
 for(const table of Object.values(changed.tables))for(const p of table.rows)if(p.date>'2017-08-28'&&p.status==='numeric')p.value='999.99';
 const later=deriveCatalog(changed,{...original,events:[...original.events,...inputs.extra.events]});
 const after=qualifiedCohort(event('harvey-2017-texas'),later.events,changed,'brent','2017-08-29T00:00:00Z',inputs.releaseData.releases);
 assert.deepEqual(after,before);
 assert(before.selection.excluded.some(c=>c.id==='francine-2024-louisiana'&&c.reason==='event_public_clock_unknown_or_future'));
});
test('original dated refinery evidence cannot appear at the earlier Harvey decision',()=>{
 const sources=json('ripple/sources.json'),harvey=event('harvey-2017-texas');
 const early=rippleEvidenceAt(sources,harvey,'2017-08-29T00:00:00Z');
 assert.equal(early.paths.length,2);assert.equal(early.counterevidence.length,0);
 assert(early.paths.every(p=>p.classification==='causal_hypothesis'&&!p.observed_market_effect&&p.edges.map(x=>x.order).join(',')==='1,2,3'));
 assert.equal(rippleEvidenceAt(sources,harvey,'2017-09-14T00:00:00Z').counterevidence.length,1);
 assert.equal(rippleEvidenceAt(sources,event('delta-2020-louisiana'),'2020-10-13T00:00:00Z').paths.length,0);
});
test('all original and expanded events abstain with explicit source and sample limits; costed negative cases remain',()=>{
 const r=buildStudy();
 assert.deepEqual(r.original_24.brent.decisions,{Buy:0,Hold:0,Review_Sell:0,No_Action:24});
 assert.deepEqual(r.expanded_32.brent.decisions,{Buy:0,Hold:0,Review_Sell:0,No_Action:32});
 assert.equal(r.original_24.brent.complete_current_5day,18);assert.equal(r.original_24.wti.complete_current_5day,22);
 assert.equal(r.expanded_32.brent.complete_current_5day,24);assert.equal(r.expanded_32.wti.complete_current_5day,28);
 assert.equal(r.release_evidence.numeric,19);assert.equal(r.release_evidence.ND,1);assert.equal(r.release_evidence.agree_with_current,20);
 assert.equal(r.expanded_32.brent.counterfactual_baselines.declared.positive,13);assert.equal(r.expanded_32.brent.counterfactual_baselines.declared.negative,11);
 assert.equal(r.expanded_32.brent.counterfactual_baselines.stressed.negative,18);
 assert(r.records.every(x=>x.action==='No Action'&&x.detail.fully_qualified===0));
 assert(r.records.filter(x=>x.market==='wti').every(x=>x.baselines===null&&x.reasons.includes('WTI_is_research_only_not_supported_paper_instrument')));
 assert.equal(r.API_recovery.cause_resolved,false);assert.equal(r.expanded_32.brent.predictive_accuracy,null);
});
test('new report deterministically reproduces its pinned trace without changing parent reports',()=>{
 assert.equal(sha(Buffer.from(JSON.stringify(buildStudy(),null,2)+'\n')),readFileSync(new URL('../analogues/RESULTS.sha256',import.meta.url),'utf8').trim());
});
