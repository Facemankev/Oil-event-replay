import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadPrimary,reconcile,json,sha,root} from '../verification/load.mjs';
import {buildReport,evaluatePrimary,pairedHistory,coverage} from '../verification/evaluate.mjs';
const primary=loadPrimary(),catalog=json('matching/cohort-catalog.json'),report=buildReport();

test('retained primary sources match every canonical price and preserve disputed-date evidence',()=>{
 assert.equal(report.reconciliation.series.brent.matching,5231);assert.equal(report.reconciliation.series.wti.matching,5137);
 assert.equal(report.reconciliation.series.brent.differences.length,0);assert.equal(report.reconciliation.series.wti.differences.length,0);
 const claims=report.reconciliation.claims;
 assert.equal(claims.filter(c=>c.status==='retain_seed_API_difference_not_corroborated').length,3);
 assert.equal(claims.filter(c=>c.status==='explicit_primary_blank_API_value_still_unknown').length,137);
 assert.equal(claims.filter(c=>c.status==='retain_seed_API_omission_not_a_deletion').length,17);
 assert(claims.filter(c=>c.claim==='different_API_value').every(c=>c.reported_value_matches_previous_observation&&c.revision_cause===null&&!c.original_API_payload_replayed));
 assert.equal(report.reconciliation.original_API_conflict_cause_resolved,false);
});
test('GBP conversion divides by observed USD/GBP; original rounded account rates are untouched',()=>{
 const rows=pairedHistory(primary,'brent'),point=rows.find(p=>p.date==='2017-08-28');
 assert.equal(point.usd_per_gbp,'1.2927');assert.equal(Number(point.value),Number(point.price_usd)/1.2927);
 assert.notEqual(Number(point.value),Number(point.price_usd)*1.2927);
 assert.equal(report.fx.original_slice_equal_at_legacy_precision,34);assert.equal(report.fx.original_snapshot_modified,false);
});
test('ND is neither a zero FX rate nor a previous rate; fixed reporting calendars stay distinct',()=>{
 const point=pairedHistory(primary,'brent').find(p=>p.date==='2017-09-04');
 assert.equal(point.value,null);assert.equal(point.missing_code,'ND');
 assert.equal(coverage(primary,'brent','2017-08-28',5).current_vintage_complete,false);
 assert.equal(coverage(primary,'wti','2017-08-28',5).current_vintage_complete,true);
 assert.equal(coverage(primary,'brent','2017-08-28',5).end_date,'2017-09-04');
});
test('all 24 events get complete/incomplete outcomes on both fixed calendars, never a manufactured signal',()=>{
 assert.deepEqual(report.summary,{events:24,complete_both_markets_fixed_5day:18,incomplete_both_markets_fixed_5day:6,complete_as_of:0,Buy:0,Hold:0,No_Action:24});
 assert.equal(report.evaluation.records.length,48);
 assert.deepEqual(report.evaluation.markets.brent.complete_by_horizon,{'1':23,'3':22,'5':18,'10':15,'20':11});
 assert.deepEqual(report.evaluation.markets.wti.complete_by_horizon,{'1':24,'3':23,'5':22,'10':20,'20':17});
 for(const row of report.evaluation.records){assert.equal(row.action,'No Action');assert.equal(row.audit.point_in_time_safe,false);assert(row.reasons.includes('original_price_and_FX_publication_vintages_unknown'));assert(row.cohort.cases.every(c=>c.id!==row.event_id&&c.end_date<row.query.publicDate));}
});
test('cost sensitivity uses every complete Brent case with identical entry/exit timing',()=>{
 const rows=report.evaluation.records.filter(r=>r.baselines);assert.equal(rows.length,18);
 for(const r of rows){const b=r.baselines;assert(b.zero.net_pnl_gbp>=b.declared.net_pnl_gbp&&b.declared.net_pnl_gbp>=b.stressed.net_pnl_gbp);assert.equal(b.zero.entry_date,b.stressed.entry_date);assert.equal(b.zero.exit_date,b.stressed.exit_date);assert(b.declared.costs.fee_gbp_per_leg>0);}
 assert.equal(report.evaluation.markets.brent.manual_baseline_counts.declared.positive,9);
 assert.equal(report.evaluation.markets.brent.manual_baseline_counts.stressed.positive,5);
 assert.equal(report.evaluation.markets.brent.false_positive_rate,null);
});
test('joint observations and delayed entry are clearly separate sensitivity rules, not filled rates',()=>{
 const harvey=report.evaluation.records.find(r=>r.market==='brent'&&r.event_id==='harvey-2017-texas');
 assert.equal(harvey.baselines,null);assert.equal(harvey.sensitivity.five_joint_observations.exit_date,'2017-09-05');
 const israel=report.evaluation.records.find(r=>r.market==='brent'&&r.event_id==='israel-2023-october');
 assert.equal(israel.decision_date,'2023-10-09');assert.equal(israel.sensitivity.delayed_first_joint_entry.entry_date,'2023-10-10');assert.equal(israel.sensitivity.entry_delay_days,1);
 assert.equal(report.evaluation.markets.brent.five_joint_observation_baselines,23);
 assert.equal(report.evaluation.markets.brent.deferred_entry_baselines,24);
});
test('negative WTI remains an observed price, not a missing value or an invented paper fill',()=>{
 assert.equal(primary.tables.wti.byDate.get('2020-04-20').value,'-36.98');
 const row=report.evaluation.records.find(r=>r.market==='wti'&&r.event_id==='opec-2020-april');
 assert.equal(row.horizons[5].current_vintage_complete,true);assert(row.usd_outcome.percent<-100);
 assert.equal(row.baselines,null);assert(row.reasons.includes('WTI_is_research_only_not_supported_paper_instrument'));
});
test('changing future observations cannot change a prior frozen paper decision',()=>{
 const changed=structuredClone(primary),cutoff='2017-08-28';
 for(const market of ['brent','wti','fx'])for(const row of changed.tables[market].rows)if(row.date>cutoff&&row.status==='numeric')row.value=market==='fx'?'9.9999':'9999.99';
 const after=evaluatePrimary(changed,catalog).records.find(r=>r.market==='brent'&&r.event_id==='harvey-2017-texas');
 const before=report.evaluation.records.find(r=>r.market==='brent'&&r.event_id==='harvey-2017-texas');
 for(const field of ['action','query','codes','audit','cohort','reasons'])assert.deepEqual(after[field],before[field],field);
});
test('report fingerprint reproduces the source and evaluation traces',()=>{
 const bytes=JSON.stringify(buildReport(),null,2)+'\n';assert.equal(sha(Buffer.from(bytes)),readFileSync(new URL('verification/RESULTS.sha256',root),'utf8').trim());
});
