/** Reproducible bounded study, deliberately separate from saved paper accounts. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {loadPrimary,json,sha,root} from '../verification/load.mjs';
import {evaluatePrimary} from '../verification/evaluate.mjs';
import {decidePaper,POLICY} from '../intelligence/engine.mjs';
import {loadStudy,deriveCatalog,qualifiedCohort,rippleEvidenceAt,fxEvidenceAt,STUDY} from './engine.mjs';
const instrument='Unleveraged fractional Brent spot-price reference, converted to GBP';
const sign=xs=>({count:xs.length,positive:xs.filter(x=>x>0).length,negative:xs.filter(x=>x<0).length,flat:xs.filter(x=>x===0).length});
const counts=rows=>({Buy:rows.filter(r=>r.action==='Consider Buy').length,Hold:rows.filter(r=>r.action==='Hold').length,
 Review_Sell:rows.filter(r=>r.action==='Review Sell').length,No_Action:rows.filter(r=>r.action==='No Action').length});

export function buildStudy(primary=loadPrimary(),original=json('matching/cohort-catalog.json'),inputs=loadStudy()){
 const catalog={...original,events:[...original.events,...inputs.extra.events]},derived=deriveCatalog(primary,catalog);
 // Reuse DAT-4's unchanged chronological policy/execution/cost definitions.
 const parent=evaluatePrimary(primary,catalog),originalIds=new Set(original.events.map(e=>e.id));
 // New decision records are frozen before we attach following outcome/baseline fields.
 const frozen=parent.records.map(row=>{
  const event=derived.events.find(e=>e.id===row.event_id),cutoff=new Date(Date.parse(row.query.publicDate+'T00:00:00Z')).toISOString();
  const detail=qualifiedCohort(event,derived.events,primary,row.market,cutoff,inputs.releaseData.releases);
  const prompt=decidePaper({audit:row.audit,cohort:detail.cohort,budget:{max_allocation_gbp:5},position:null,entry:null,quote:null,
   evidence:{principal_risk:'Unknown original vintages, small selected samples and opposing supply/refining channels.'},instrument,cursor:row.decision_date});
  if(prompt.action==='Consider Buy')throw Error('Supported entry requires a separately reviewed execution evaluation');
  const reasons=[...row.audit.fatal,...row.audit.limitations];
  if(detail.fully_qualified<POLICY.min_cases)reasons.push('fewer_than_eight_fully_qualified_independent_episode_candidates');
  if(detail.cohort.condition.status!=='known')reasons.push('pre_event_condition_window_incomplete');
  return {event_id:event.id,market:row.market,original_24:originalIds.has(event.id),cutoff,decision_date:row.decision_date,
   event_public_at:event.first_public.at,occurred_at:event.occurred.at,action:prompt.action,reasons,detail,
   entry_FX_release:fxEvidenceAt(inputs.releaseData.releases,row.decision_date,cutoff),
   ripple_evidence:rippleEvidenceAt(json('ripple/sources.json'),event,cutoff)};
 });
 const records=frozen.map(r=>{const p=parent.records.find(x=>x.event_id===r.event_id&&x.market===r.market);return {...r,horizons:p.horizons,baselines:p.baselines};});
 const summarize=rows=>Object.fromEntries(['brent','wti'].map(m=>{
  const rr=rows.filter(r=>r.market===m);
  return [m,{events:rr.length,decisions:counts(rr),complete_current_5day:rr.filter(r=>r.horizons[5].current_vintage_complete).length,
   complete_by_horizon:Object.fromEntries([1,3,5,10,20].map(n=>[n,rr.filter(r=>r.horizons[n].current_vintage_complete).length])),
   fully_as_of:0,most_selected_nonoverlapping_episodes:Math.max(...rr.map(r=>r.detail.selected.length)),
   case_comparisons_with_valid_current_paths:rr.reduce((n,r)=>n+r.detail.descriptive.count,0),
   selected_case_comparisons:rr.reduce((n,r)=>n+r.detail.selected.length,0),
   condition_compatible_current_comparisons:rr.reduce((n,r)=>n+r.detail.selected.filter(c=>c.condition_compatible_current).length,0),
   comparisons_with_any_dated_FX_release:rr.reduce((n,r)=>n+r.detail.selected.filter(c=>c.dated_FX_observations>0).length,0),
   reasons:Object.fromEntries([...new Set(rr.flatMap(r=>r.reasons))].map(reason=>[reason,rr.filter(r=>r.reasons.includes(reason)).length])),
   counterfactual_baselines:Object.fromEntries(['zero','declared','stressed'].map(cost=>[cost,sign(rr.filter(r=>r.baselines).map(r=>r.baselines[cost].net_pnl_gbp))])),
   policy_trades:0,policy_final_cash_gbp:50,predictive_accuracy:null}];
 }));
 const releaseRows=inputs.releaseData.releases.flatMap(r=>r.observations.map(p=>({release_id:r.id,...p,
  agrees_with_current:primary.tables.fx.byDate.get(p.date)?.status===p.status&&(p.status==='ND'||primary.tables.fx.byDate.get(p.date)?.value===p.value)})));
 return {method:STUDY,inputs:inputs.hashes,original_24:summarize(records.filter(r=>r.original_24)),expanded_32:summarize(records),
  events:{original:original.events.length,added:inputs.extra.events.length,total:catalog.events.length,
   warning:inputs.extra.selection},
  release_evidence:{dated_releases:inputs.releaseData.releases.length,observations:releaseRows.length,numeric:releaseRows.filter(p=>p.status==='numeric').length,
   ND:releaseRows.filter(p=>p.status==='ND').length,agree_with_current:releaseRows.filter(p=>p.agrees_with_current).length,
   original_vintage_verified:0,rows:releaseRows},
  API_recovery:json('analogues/api-evidence.json'),
  protocol:'Outcome-blind mechanism, US-Gulf exposure, operational wind within 30 mph; one earliest located supporting bulletin per storm; chronological non-overlapping 21-observation context plus five-observation reaction. Unchanged INT-1 condition, sample and dispersion rules. Dates/releases are not backdated; unknown oil vintages still block entries.',
  conclusion:'No supported paper opportunity. Current-vintage coverage and dated-page corroboration are distinct from evidence actually known at a historical decision. No policy trade, predictive accuracy, original revision cause or statistical independence is established.',records};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const report=buildStudy(),text=JSON.stringify(report,null,2)+'\n';
 if(process.argv.includes('--check')){
  if(readFileSync(new URL('RESULTS.sha256',import.meta.url),'utf8').trim()!==sha(Buffer.from(text)))throw Error('INT-2 report changed: review before updating digest');
 }else if(process.argv.includes('--output')){
  const output=resolve(process.argv[process.argv.indexOf('--output')+1]),work=fileURLToPath(new URL('work/',root));
  if(!output.startsWith(work))throw Error('Full reports belong only in a new local work/ file');
  mkdirSync(dirname(output),{recursive:true});writeFileSync(output,text,{flag:'wx'});
 }
 console.log(JSON.stringify({events:report.events,original_24:report.original_24,expanded_32:report.expanded_32,releases:{...report.release_evidence,rows:undefined}},null,2));
}
