/** Conditional paths are descriptive past samples, never next-day probabilities. */
import {rankMatches,visibleReactions} from '../matching/engine.mjs';
import {summarize,median} from '../matching/analysis.mjs';
export const nextDay=day=>new Date(Date.parse(day+'T00:00:00Z')+86400000).toISOString().slice(0,10);
const pct=(a,b)=>(b/a-1)*100;
const positive=x=>Number.isFinite(Number(x))&&Number(x)>0;
const quantile=(sorted,p)=>sorted.length?sorted[Math.floor((sorted.length-1)*p)]:null;

export function conditionalPaths(paths,phase,ahead=3){
 if(!Number.isInteger(phase)||phase<0||!Number.isInteger(ahead)||ahead<1)throw Error('Invalid path phase');
 const rows=[];
 for(const path of paths){
  const before=path.points[Math.max(0,phase-2)],now=path.points[phase],after=path.points[phase+ahead];
  if(!before||!now||!after||![before,now,after].every(p=>positive(p.value)))continue;
  const prior=pct(Number(before.value),Number(now.value)),forward=pct(Number(now.value),Number(after.value));
  rows.push({id:path.id,prior_percent:prior,forward_percent:forward,reversed:prior>0&&forward<0,
    known_by:path.end_date,primary:path.primary,precise:path.precise,severity:path.severity,point_in_time_safe:path.point_in_time_safe===true});
 }
 const values=rows.map(r=>r.forward_percent),ordered=[...values].sort((a,b)=>a-b),middle=median(values);
 const iqr=rows.length?quantile(ordered,.75)-quantile(ordered,.25):null;
 const halves=[values.slice(0,Math.floor(values.length/2)),values.slice(Math.floor(values.length/2))];
 const stableSign=sign=>rows.length>=8&&halves.every(v=>sign*median(v)>0)&&values.every((v,i)=>sign*median(values.filter((_,j)=>i!==j))>0);
 const quality=rows.length>=8&&rows.every(r=>r.primary&&r.precise&&r.severity&&r.point_in_time_safe);
 const dispersion=rows.length>0&&iqr<=5&&ordered[ordered.length-1]-ordered[0]<=15;
 const negative=values.filter(v=>v<0).length,positiveCount=values.filter(v=>v>0).length,reversed=rows.filter(r=>r.reversed).length;
 return {phase,ahead,count:rows.length,rows,median_percent:middle,minimum:ordered[0]??null,maximum:ordered[ordered.length-1]??null,
  iqr,positive:positiveCount,negative,flat:values.length-positiveCount-negative,reversed,
  reversal_supported:quality&&dispersion&&middle<-1&&reversed>=Math.ceil(rows.length*.75)&&stableSign(-1),
  buy_supported:quality&&dispersion&&middle>1&&positiveCount>=Math.ceil(rows.length*.75)&&stableSign(1),
  evidence:quality&&dispersion?'Moderate':'Limited',
  note:'Fixed exploratory gates: 8 complete non-overlapping paths; primary prices, clocks, severity and point-in-time evidence; IQR ≤5pp, range ≤15pp; consistent chronological halves/leave-one-out medians and ≥75% signed examples. These are not calibrated odds.'};
}

export function matchingQueryAt(data,catalog,cursor){
 const event=catalog.events.find(e=>e.id===data.event_id);
 if(!event||!event.reactions.anchor||event.reactions.anchor>=nextDay(cursor))throw Error('Event evidence is not available on this replay date');
 return {title:event.title,category:event.category,market:'brent',occurred:event.occurred.date,publicDate:nextDay(cursor),
  location:'Gulf of Mexico',mechanism:event.features.mechanism,severity:'',impact:event.features.impact,
  windSpeed:event.features.severity?.value??null,excludeId:event.id};
}

export function evidenceAt(data,catalog,cursor){
 const query=matchingQueryAt(data,catalog,cursor),event=catalog.events.find(e=>e.id===data.event_id);
 const matches=rankMatches(query,catalog.events),cohort=summarize(matches,query,20);
 const paths=[];
 for(const id of cohort.included_ids){
  const match=matches.find(m=>m.event.id===id),row=visibleReactions(match,query).find(r=>r.days===20);
  if(!row||row.status!=='ok'||row.end_date>cursor)continue;
  const points=row.observations.filter(p=>p.date<=cursor);
  if(points.length!==21||!points.every(p=>positive(p.value)))continue;
  paths.push({id,end_date:row.end_date,points,primary:row.verification==='primary_EIA',precise:match.event.first_public.precision==='minute'&&match.event.first_public.status!=='not_established',
   severity:match.severityMatch,point_in_time_safe:row.point_in_time_safe===true});
 }
 const phase=data.market_calendar.filter(d=>d>event.reactions.anchor&&d<=cursor).length;
 const updates=data.sources.updates.filter(s=>s.available_from<=cursor);
 const context=data.sources.context.filter(s=>s.available_from<=cursor);
 const publicSources=event.evidence.filter(s=>s.published.at?new Date(s.published.at).toISOString().slice(0,10)<=cursor:s.published.date&&nextDay(s.published.date)<=cursor);
 const sources=[...publicSources.map(s=>({id:s.id,publisher:s.publisher,url:s.url,published:s.published.at||s.published.date,card_sha256:s.sha256,summary:s.summary})),
  ...[...context,...updates].map(s=>({id:s.id,publisher:s.publisher,url:s.url,published:s.published_day,available_from:s.available_from,card_file_sha256:data.input_hashes.source_cards,summary:s.summary}))];
 const conditional=conditionalPaths(paths,phase);
 const five=summarize(matches,query,5);
 return {event_id:event.id,as_of:cursor,conditional,cohort_count:five.window_count,cohort_median:five.percent.median,
  cohort_outcomes:{positive:five.percent.positive,negative:five.percent.negative,flat:five.percent.flat},
  source_ids:sources.map(s=>s.id),sources,updates:updates.map(s=>({id:s.id,summary:s.summary,url:s.url,available_from:s.available_from})),
  evidence:conditional.evidence,principal_risk:'Production, refining demand and GBP/USD can pull the reference price in different directions.',
  point_in_time_safe:false,limitations:'Small selected sample, provisional prices, missing original publication/vintage evidence. No supported predictive reversal claim.'};
}
