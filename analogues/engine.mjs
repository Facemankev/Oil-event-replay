/** INT-2: additive, outcome-blind qualification; no account or UI mutation. */
import {rankMatches,validDay} from '../matching/engine.mjs';
import {median} from '../matching/analysis.mjs';
import {cohortTrace,POLICY,rippleTrace} from '../intelligence/engine.mjs';
import {reactionRows,pairedHistory} from '../verification/evaluate.mjs';
import {json,sha} from '../verification/load.mjs';
import {readFileSync} from 'node:fs';

export const STUDY=Object.freeze({id:'int-2-gulf-v1',minimum:POLICY.min_cases,wind_tolerance_mph:30,
 context_observations:21,day_release_lag_UTC_days:2,policy_id:POLICY.id});
const stamp=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d\d:\d\d)$/.test(x)&&Number.isFinite(Date.parse(x));
const earlier=(x,cutoff)=>stamp(x)&&Date.parse(x)<Date.parse(cutoff);
const datePlus=(day,n)=>new Date(Date.parse(day+'T00:00:00Z')+n*86400000).toISOString();
const gulf=e=>e.exposure_region||(e.category==='weather'&&e.geography.includes('Gulf of Mexico')?'US_Gulf_coast':null);
export const episode=e=>e.episode_id||e.evidence?.map(s=>s.url?.match(/(al\d{6})\./i)?.[1]?.toUpperCase()).find(Boolean)||null;
const stats=values=>({count:values.length,median:median(values),minimum:values.length?Math.min(...values):null,
 maximum:values.length?Math.max(...values):null,positive:values.filter(v=>v>0).length,negative:values.filter(v=>v<0).length,flat:values.filter(v=>v===0).length});

export function loadStudy(){
 const hashes=json('analogues/INPUTS.json');
 if(Object.keys(hashes).sort().join(',')!=='api-evidence.json,events.json,releases.json')throw Error('Missing INT-2 source fingerprint');
 for(const [name,digest] of Object.entries(hashes))if(!['events.json','releases.json','api-evidence.json'].includes(name)||
  sha(readFileSync(new URL(name,import.meta.url)))!==digest)throw Error('INT-2 source fingerprint mismatch');
 const extra=json('analogues/events.json'),releaseData=json('analogues/releases.json');
 if(extra.schema_version!==1||releaseData.schema_version!==1)throw Error('Unsupported INT-2 schema');
 const ids=new Set(json('matching/cohort-catalog.json').events.map(e=>e.id));
 for(const e of extra.events){
  if(ids.has(e.id)||!/^AL\d{6}$/.test(e.episode_id)||gulf(e)!=='US_Gulf_coast'||e.category!=='weather'||
   e.features.mechanism!=='landfall'||!validDay(e.reactions.anchor)||!stamp(e.occurred.at)||!stamp(e.first_public.at)||
   Date.parse(e.occurred.at)>Date.parse(e.first_public.at)||e.reactions.anchor!==e.first_public.date||
   !stamp(e.features.severity.published_at)||Date.parse(e.features.severity.published_at)>Date.parse(e.first_public.at)||
   e.features.severity.scale!=='advisory_maximum_sustained_wind_mph'||!Number.isFinite(e.features.severity.value)||e.features.severity.value<=0||e.features.severity.value>250||
   !e.evidence.length||e.evidence.some(s=>!/^https:\/\/www\.nhc\.noaa\.gov\/archive\//.test(s.url)||s.original_http_sha256!==null))throw Error('Invalid sourced storm');
  ids.add(e.id);
 }
 validateReleases(releaseData.releases);
 return {extra,releaseData,hashes};
}

export function validateReleases(releases){
 const ids=new Set();
 for(const r of releases){
  if(ids.has(r.id)||!validDay(r.release_date)||r.url!=='https://www.federalreserve.gov/releases/h10/'+r.release_date.replaceAll('-','')+'/'||
   r.unit!=='USD per GBP'||r.precision!=='day'||r.release_at!==null||r.release_timezone!==null||r.original_vintage_at!==null||r.original_http_sha256!==null||r.observations.length!==5)throw Error('Invalid dated FX release');
  ids.add(r.id);let previous='';
  for(const p of r.observations){
   if(!validDay(p.date)||p.date<=previous||p.date>=r.release_date||
    !(p.status==='ND'&&p.value===null||p.status==='numeric'&&typeof p.value==='string'&&/^\d+\.\d{4}$/.test(p.value)&&Number(p.value)>0))throw Error('Invalid dated FX observation');
   previous=p.date;
  }
 }
}

/** Dated page corroboration only. It cannot manufacture an original vintage. */
export function fxEvidenceAt(releases,date,cutoff){
 if(!validDay(date)||!stamp(cutoff))throw Error('Explicit UTC/offset cutoff and valid observation date required');
 const eligible=releases.filter(r=>earlier(datePlus(r.release_date,STUDY.day_release_lag_UTC_days),cutoff)&&r.observations.some(p=>p.date===date))
  .sort((a,b)=>a.release_date.localeCompare(b.release_date)||a.id.localeCompare(b.id));
 const release=eligible.at(-1);
 if(!release)return {status:'no_eligible_dated_release',date,value:null,original_vintage_verified:false};
 const point=release.observations.find(p=>p.date===date);
 return {status:point.status==='ND'?'documented_unavailable':'dated_release_numeric',date,value:point.value,
  release_id:release.id,source_url:release.url,printed_release_date:release.release_date,
  conservative_eligible_after:datePlus(release.release_date,STUDY.day_release_lag_UTC_days),
  original_release_at:null,original_vintage_verified:false};
}

export function deriveCatalog(primary,catalog){
 return {...catalog,events:catalog.events.map(e=>({...e,reactions:{...e.reactions,markets:Object.fromEntries(['brent','wti'].map(m=>[m,reactionRows(primary,e,m)]))}}))};
}

/** Select chronology/episode/context intervals before reading any returns.
 * Failed prices or conditions do not cause a later overlapping case to replace it. */
export function selectAnalogues(event,events,history,market,cutoff,horizon=POLICY.horizon){
 if(!stamp(cutoff)||!['brent','wti'].includes(market)||![1,3,5,10,20].includes(horizon))throw Error('Invalid study cutoff/market/horizon');
 const day=cutoff.slice(0,10),severity=event.features.severity;
 const query={title:event.title,category:event.category,market,occurred:event.occurred.date,publicDate:day,
  location:event.geography,mechanism:event.features.mechanism,impact:event.features.impact,severity:'',excludeId:event.id,
  windSpeed:severity&&earlier(severity.published_at,cutoff)?severity.value:null};
 const matches=new Map(rankMatches(query,events).map(m=>[m.event.id,m]));
 const excluded=[],candidates=[],seen=new Set(),duplicates=new Set(events.filter((e,i)=>events.findIndex(x=>x.id===e.id)!==i).map(e=>e.id));
 const publicOrder=e=>Date.parse(e.first_public.at||e.first_public.date||e.reactions.anchor+'T00:00:00Z');
 const ordered=[...events].sort((a,b)=>publicOrder(a)-publicOrder(b)||a.id.localeCompare(b.id));
 for(const e of ordered){
  let reason=null;const ep=episode(e),m=matches.get(e.id),row=e.reactions.markets[market]?.find(r=>r.days===horizon);
  if(duplicates.has(e.id))reason='duplicate_event_id';
  else if(e.id===event.id||ep&&ep===episode(event))reason='same_episode_or_self';
  else if(e.category!==event.category||!e.affected_commodities.includes(market))reason='different_category_or_commodity';
  else if(!earlier(e.first_public.at,cutoff)||e.first_public.precision!=='minute')reason='event_public_clock_unknown_or_future';
  else if(!ep)reason='independent_episode_unidentified';
  else if(seen.has(ep))reason='repeated_bulletin_same_episode';
  else {
   // Earliest located bulletin represents the episode even if it fails later checks.
   seen.add(ep);
   if(e.features.mechanism!==event.features.mechanism)reason='different_mechanism';
   else if(!gulf(event)||gulf(e)!==gulf(event))reason='different_or_unestablished_exposure_region';
   else if(query.windSpeed===null||!m?.knownSeverity)reason='operational_scale_unknown_at_cutoff';
   else if(!m.severityMatch)reason='operational_wind_not_comparable';
   else if(!row?.end_date||!earlier(row.end_date+'T23:59:59.999Z',cutoff))reason='reaction_not_yet_observed';
   else {
    // Dates come from raw numeric oil observations; ND FX does not shorten the context.
    const prior=history.filter(p=>p.date<e.reactions.anchor).slice(-STUDY.context_observations);
    if(prior.length!==STUDY.context_observations)reason='insufficient_context_dates';
    else candidates.push({id:e.id,episode_id:ep,from:prior[0].date,through:row.end_date,match:m});
   }
  }
  if(reason)excluded.push({id:e.id,reason});
 }
 candidates.sort((a,b)=>a.from.localeCompare(b.from)||a.id.localeCompare(b.id));
 const selected=[];let end=null;
 for(const c of candidates){if(end&&c.from<=end)excluded.push({id:c.id,reason:'overlapping_context_and_reaction'});else{selected.push(c);end=c.through;}}
 return {query,selected,excluded,independence_proven:false,
  caution:'One case per storm and non-overlapping windows reduce duplication; they do not establish statistical independence or remove other news.'};
}

export function qualifiedCohort(event,events,primary,market,cutoff,releases){
 const history=pairedHistory(primary,market),selection=selectAnalogues(event,events,history,market,cutoff),ids=new Set(selection.selected.map(c=>c.id));
 const cohort=cohortTrace(selection.query,events.filter(e=>ids.has(e.id)),history,event.reactions.anchor);
 const selected=selection.selected.map(c=>{
  const row=events.find(e=>e.id===c.id).reactions.markets[market].find(r=>r.days===POLICY.horizon);
  const fx=row.observations.map(p=>fxEvidenceAt(releases,p.date,cutoff)),parent=cohort.cases.find(x=>x.id===c.id);
  return {id:c.id,episode_id:c.episode_id,context_from:c.from,reaction_through:c.through,similarity_score:c.match.score,
   reasons:c.match.reasons,weaknesses:[...c.match.gaps,'Winds do not quantify oil outages, flooding or recovery.','Mixed supply/refining exposure; no causal isolation.'],
   parent_blockers:parent?.blockers||[row.status==='ok'?'missing_or_invalid_reaction_path':row.status],
   condition_compatible_current:!!parent&&parent.blockers.every(b=>b==='primary_as_of_prices_unproven'),
   dated_FX_observations:fx.filter(p=>p.status==='dated_release_numeric').length,required_FX_observations:row.observations.length,
   fx_release_evidence:fx,fully_as_of_qualified:parent?.eligible===true};
 });
 return {selection:{...selection,selected:selection.selected.map(({match,...c})=>c)},cohort,selected,
  fully_qualified:selected.filter(c=>c.fully_as_of_qualified).length,
  descriptive:stats(cohort.cases.map(c=>c.observed_percent).filter(x=>x!==null)),minimum_cases:STUDY.minimum,
  evidence:'Limited',point_in_time_safe:false};
}

export function rippleEvidenceAt(sources,event,cutoff){
 if(!stamp(cutoff))throw Error('Explicit cutoff required');
 const available=s=>earlier(datePlus(s.published_day,STUDY.day_release_lag_UTC_days),cutoff);
 const known=[...sources.context,...sources.updates].filter(available);
 if(event.id!=='harvey-2017-texas')return {paths:[],sources:[],limitation:'Harvey-specific infrastructure evidence is not transferred to another storm as an observed fact.'};
 const data={event_id:event.id,sources:{...sources,context:sources.context.filter(available)}};
 return {paths:rippleTrace(data,cutoff.slice(0,10)),sources:known,
  counterevidence:known.filter(s=>sources.updates.some(u=>u.id===s.id)),
  limitation:'First, second and third-order paths are hypotheses. Source-dated exposure is not a measured downstream price effect.'};
}
