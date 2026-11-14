/** Company-news research only. No broker, account mutation, or orders. */
import {createHash} from 'node:crypto';
import {median} from '../matching/analysis.mjs';
import {validDay} from '../matching/engine.mjs';
import {POLICY as OIL_POLICY} from '../intelligence/engine.mjs';
export const POLICY=Object.freeze({id:'evt-1-nvda-v1',minimum_cases:OIL_POLICY.min_cases,
 stale_regular_minutes:60,max_wall_age_days:7,already_moved_percent:3,default_latency_seconds:60});
const hash=s=>createHash('sha256').update(s).digest('hex');
const finite=x=>typeof x==='string'&&/^\d+\.\d{2,4}$/.test(x)&&Number(x)>0&&Number.isFinite(Number(x));
export const isStamp=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d\d:\d\d)$/.test(x)&&Number.isFinite(Date.parse(x));
export const day=validDay;
const stamp=x=>{if(!isStamp(x))throw Error('Explicit timestamp with timezone required');return Date.parse(x);};
const plusDay=(s,n)=>new Date(Date.parse(s+'T00:00:00Z')+n*86400000).toISOString();
const pct=(a,b)=>(b/a-1)*100;
const clean=s=>String(s).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const nyDate=at=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(at));

export function canonicalURL(value){
 const u=new URL(value);
 if(u.protocol!=='https:'||u.username||u.password||u.port)throw Error('Public HTTPS source required');
 for(const key of [...u.searchParams.keys()])if(/^(utm_|fbclid|gclid)/i.test(key))u.searchParams.delete(key);
 if([...u.searchParams.keys()].some(k=>/key|token|secret|signature|password/i.test(k)))throw Error('Credential-bearing source URL rejected');
 u.hash='';return u.href;
}

export function classify(article){
 const text=article.title+' '+article.summary;
 if(!/\b(?:nvidia|nvda)\b/i.test(text))return null;
 const categories=[];
 for(const [name,re] of [
  ['leadership',/\b(?:ceo|chief executive|leadership|resign|interim)\b/i],
  ['governance',/\b(?:board|investigat\w*|disclos\w*|governance|counsel)\b/i],
  ['security',/\b(?:intelligence|security|secrets|breach|cyber\w*)\b/i],
  ['regulatory',/\b(?:regulator\w*|licen[cs]\w*|export|SEC|sanction\w*)\b/i]])if(re.test(text))categories.push(name);
 if(!categories.length)return null;
 return {company:'NVDA',sector:'semiconductors',categories,location:['US'],severity:null,
  allegation_or_inquiry:/\b(?:alleg\w*|report\w*|investigat\w*)\b/i.test(text),
  counterpoint:/no reason to believe|disput\w*|deni\w*|not established|not a finding/i.test(text),
  status:'Attributed reporting/company actions; no finding of espionage inferred.',
  stage:/resign\w*|interim CEO/i.test(text)?'confirmed_departure':'unresolved_inquiry'};
}

export function publicationBoundary(a){
 if(a.published_at){stamp(a.published_at);return {at:new Date(a.published_at).toISOString(),precision:a.precision,basis:'printed_publication_clock_not_proven_first_dissemination'};}
 if(!day(a.published_day))throw Error('Publication date required');
 return {at:plusDay(a.published_day,2),precision:'day',basis:'conservative_day_plus_two_UTC_days; actual clock unknown'};
}

const knownBoardSources=new Set(['board_wire','board_primary','board_ir']);
export function newsAt(articles,sources,asOf,{latencySeconds=POLICY.default_latency_seconds}={}){
 const cutoff=stamp(asOf);if(!Number.isFinite(latencySeconds)||latencySeconds<0||latencySeconds>30*86400)throw Error('Invalid detector latency');
 const groups=new Map(),excluded=[];
 for(const a of articles){
  if(!a||typeof a.title!=='string'||a.title.length>500||typeof a.summary!=='string'||a.summary.length>2000)throw Error('Invalid bounded news input');
  const source=sources[a.source_id];if(!source)throw Error('Unknown news source');
  const url=canonicalURL(a.url);
  const sourceURL=canonicalURL(source.url);
  if(source.kind==='issuer_feed'){
   if(new URL(url).hostname!=='nvidianews.nvidia.com')throw Error('Unapproved issuer feed article');
  }else if(url!==sourceURL)throw Error('Source identity mismatch');
  const timing=publicationBoundary(a),published=Date.parse(timing.at),received=a.actual_first_seen_at?stamp(a.actual_first_seen_at):null;
  const version=a.updated_at?stamp(a.updated_at):published;
  if(version<published)throw Error('News update cannot precede publication');
  const available=Math.max(version+latencySeconds*1000,received??0);
  if(available>cutoff){excluded.push({id:a.id,reason:'not_yet_available'});continue;}
  const classification=classify(a);if(!classification){excluded.push({id:a.id,reason:'not_NVDA_corporate_news'});continue;}
  // Curated issuer-copy family is trusted only for the three registered matching URLs.
  const registeredBoardURL=url==='https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors';
  const family=knownBoardSources.has(a.source_id)||registeredBoardURL?'issuer:nvda-board-2026-11-08':hash(url);
  const entry={...a,url,classification,timing,available_at:new Date(available).toISOString(),
   latency_seconds:latencySeconds,availability_mode:received===null?'simulated_detection; actual historical receipt unknown':'captured_receipt',
   independent_corroboration:false};
  if(!groups.has(family))groups.set(family,[]);groups.get(family).push(entry);
 }
 const events=[...groups.entries()].map(([id,copies])=>{
  copies.sort((a,b)=>Date.parse(a.available_at)-Date.parse(b.available_at)||a.id.localeCompare(b.id));
  const latest=copies.at(-1),first=copies[0];
  return {...latest,id,first_article_id:first.id,timing:first.timing,available_at:first.available_at,
   latest_version_available_at:latest.available_at,
   classification:{...latest.classification,counterpoint:copies.some(c=>c.classification.counterpoint)},
   copies:copies.map(c=>({id:c.id,source_id:c.source_id,url:c.url,available_at:c.available_at,title:c.title,summary:c.summary})),
   source_family_count:1,duplicate_copies:copies.length-1};
 }).sort((a,b)=>Date.parse(a.available_at)-Date.parse(b.available_at)||a.id.localeCompare(b.id));
 return {events,excluded,duplicates:events.reduce((n,e)=>n+e.duplicate_copies,0),
  caveat:'Replay receipt latency is an explicit assumption unless actual_first_seen_at exists; current pages do not certify original versions.'};
}

/** Official 2026 regular schedule; never infer missing historical years or halts. */
export function session(calendar,date){
 if(!day(date)||Number(date.slice(0,4))!==calendar.year)return null;
 const weekday=new Date(date+'T12:00:00Z').getUTCDay();
 if(weekday===0||weekday===6||calendar.holidays.includes(date))return {date,open:null,close:null,closed:true};
 const nyStamp=time=>{
  const offset=new Intl.DateTimeFormat('en-US',{timeZone:calendar.timezone,timeZoneName:'shortOffset'}).formatToParts(new Date(date+'T12:00:00Z')).find(p=>p.type==='timeZoneName').value;
  const match=offset.match(/^GMT([+-])(\d{1,2})(?::(\d{2}))?$/);if(!match)throw Error('Unsupported exchange timezone offset');
  const mins=(Number(match[2])*60+Number(match[3]||0))*(match[1]==='-'?-1:1);
  return new Date(Date.parse(date+'T'+time+':00Z')-mins*60000).toISOString();
 };
 return {date,open:nyStamp(calendar.regular_open),close:nyStamp(calendar.early_closes[date]||calendar.regular_close),closed:false,
  timing_basis:'verified scheduled regular-session boundary; not a verified individual exchange print',source_id:calendar.source_id};
}
export function marketState(calendar,asOf){
 const at=stamp(asOf),s=session(calendar,nyDate(at));
 if(!s)return {state:'unknown_calendar',next_open:null};
 let next=null;
 for(let i=0;i<12;i++){const d=plusDay(s.date,i).slice(0,10),candidate=session(calendar,d);if(candidate?.open&&Date.parse(candidate.open)>at){next=candidate.open;break;}}
 return {...s,state:!s.closed&&at>=Date.parse(s.open)&&at<Date.parse(s.close)?'regular_open':'regular_closed',next_open:next,
  caution:'Extended-hours products, unexpected closures and individual halts are not modelled.'};
}
export function regularMinutes(calendar,from,to){
 const start=stamp(from),end=stamp(to);if(end<start)throw Error('Backwards replay');
 let date=nyDate(start),minutes=0;
 for(let i=0;i<370&&date<=nyDate(end);i++,date=plusDay(date,1).slice(0,10)){
  const s=session(calendar,date);if(!s)return null;
  if(s.open)minutes+=Math.max(0,Math.min(end,Date.parse(s.close))-Math.max(start,Date.parse(s.open)))/60000;
 }
 return minutes;
}

export function pricePoint(rows,symbol,date,kind){
 if(!['open','close'].includes(kind))throw Error('Unsupported price kind');
 const selected=rows.filter(r=>r.symbol===symbol&&r.date===date);
 if(!selected.length)return {status:'missing',symbol,date,kind,value:null};
 if(selected.some(r=>!finite(r[kind]))||new Set(selected.map(r=>r.basis)).size!==1||new Set(selected.map(r=>r.unit)).size!==1||new Set(selected.map(r=>r.source_id)).size!==selected.length)throw Error('Invalid or incompatible price evidence');
 const values=[...new Set(selected.map(r=>Number(r[kind])))];
 return {status:values.length===1?'current_provider_value':'conflicting_provider_values',symbol,date,kind,
  value:values.length===1?values[0]:null,minimum:Math.min(...values),maximum:Math.max(...values),
  sources:selected.map(r=>({source_id:r.source_id,value:r[kind]})),provider_count:selected.length,
  basis:selected[0].basis,unit:selected[0].unit,verified_exchange_print_at:null,original_available_at:null,
  quality:'Secondary current-vintage daily marks; provider agreement does not establish independent upstreams or execution.'};
}

/** No daily high/low is relabelled as an intraday observation. */
export function reactionAt(rows,calendar,symbol,newsTime,asOf,{precision='minute'}={}){
 const anchor=stamp(newsTime),cutoff=stamp(asOf);
 if(cutoff<anchor)throw Error('Reaction cutoff precedes news');
 const dates=[...new Set(rows.filter(r=>r.symbol===symbol).map(r=>r.date))].sort(),marks=[];
 for(const date of dates){const s=session(calendar,date);if(!s||s.closed)continue;
  for(const kind of ['open','close'])marks.push({at:s[kind],point:pricePoint(rows,symbol,date,kind)});
 }
 const localDay=nyDate(anchor);let baselineSession=null,firstSession=null;
 for(let i=0;i<12;i++){const s=session(calendar,plusDay(localDay,-i).slice(0,10));if(s?.close&&Date.parse(s.close)<anchor){baselineSession=s;break;}}
 for(let i=0;i<12;i++){const s=session(calendar,plusDay(localDay,i).slice(0,10));if(s?.close&&Date.parse(s.close)>anchor){firstSession=s;break;}}
 const before=baselineSession?marks.find(m=>m.point.kind==='close'&&m.at===baselineSession.close):null;
 const clockKnown=precision!=='day';
 const regularAtNews=marketState(calendar,newsTime).state==='regular_open';
 const first=regularAtNews||!clockKnown?null:marks.find(m=>m.point.kind==='open'&&m.at===firstSession?.open&&Date.parse(m.at)>anchor&&Date.parse(m.at)<=cutoff);
 const close=clockKnown&&firstSession?.close&&Date.parse(firstSession.close)<=cutoff?marks.find(m=>m.point.kind==='close'&&m.at===firstSession.close):null;
 const base=before?.point.value;
 const range=p=>clockKnown&&!regularAtNews&&base&&p&&p.point.minimum!=null?{minimum:pct(base,p.point.minimum),maximum:pct(base,p.point.maximum),exact:p.point.value===null?null:pct(base,p.point.value)}:null;
 return {symbol,news_at:newsTime,as_of:asOf,baseline:before||null,first_regular_open:first||null,first_regular_close:close||null,
  gap_percent:range(first),first_close_percent:range(close),
  daily_context_close_percent:base&&close?.point.value?pct(base,close.point.value):null,
  open_to_close_percent:first&&close&&first.point.value&&close.point.value?pct(first.point.value,close.point.value):null,
  intraday_reaction_status:'unavailable_no_timestamped_intraday_quotes',
  regular_news_baseline:!clockKnown?'news_clock_unknown_initial_reaction_unavailable':regularAtNews?'daily_open_precedes_news; intraday_baseline_missing':'outside_regular_session',
  expected_baseline_session:baselineSession?.date??null,expected_first_session:firstSession?.date??null,
  complete_original_as_of:false,verified_exchange_print_timestamps:false,
  interpretation:'Retrospective daily-mark comparison under verified scheduled session boundaries. Original quote availability/prints are unverified; not an executable reaction or causal estimate.'};
}

export function historicalCrossCheck(query,cases,sources,asOf){
 const cutoff=stamp(asOf),seen=new Set(),matches=[],excluded=[];
 for(const e of [...cases].sort((a,b)=>a.public_day.localeCompare(b.public_day)||a.id.localeCompare(b.id))){
  if(seen.has(e.id)){excluded.push({id:e.id,reason:'duplicate_historical_episode'});continue;}seen.add(e.id);
  const available=e.public_at?stamp(e.public_at):Date.parse(plusDay(e.public_day,2));
  if(available>=cutoff){excluded.push({id:e.id,reason:'historical_event_not_yet_public'});continue;}
  if(e.source_ids.some(id=>!sources[id]))throw Error('Missing historical source');
  const shared=e.categories.filter(c=>query.categories.includes(c)),reasons=[];
  if(!shared.length){excluded.push({id:e.id,reason:'different_corporate_event_category'});continue;}
  let score=shared.length*3;reasons.push('Shared categories: '+shared.join(', '));
  if(e.symbol===query.company){score+=3;reasons.push('Same company');}
  if(e.sector===query.sector){score+=2;reasons.push('Same semiconductor sector');}
  const sameStage=e.stage===query.stage;if(sameStage){score+=2;reasons.push('Same procedural stage');}
  const known=e.prices.filter(p=>Date.parse(p.date+'T23:59:59.999Z')<cutoff);
  const returnPercent=known.length===2&&known.every(p=>finite(p.close))?pct(Number(known[0].close),Number(known[1].close)):null;
  const blockers=['fewer_than_eight_qualified_equity_episodes','original_price_vintage_and_print_times_unverified'];
  if(!sameStage)blockers.push('different_procedural_stage');
  if(!query.severity||!e.severity)blockers.push('comparable_severity_unestablished');
  if(returnPercent===null)blockers.push('price_comparison_missing');
  matches.push({id:e.id,title:e.title,symbol:e.symbol,score,reasons,weaknesses:e.weaknesses,source_ids:e.source_ids,
   publication_at:e.public_at,publication_day:e.public_day,occurrence_day:e.occurred_day,
   prices:known,reference_close_change_percent:returnPercent,
   reaction_timing:e.public_at?'Dated publication clock; referenced closes, not an intraday causal estimate.':'Reference closing-day comparison only; precise publication clock unestablished.',
   updates:(e.updates||[]).filter(u=>Date.parse(plusDay(u.public_day,2))<cutoff),
   similarity:sameStage?'Partial':'Weak',blockers,qualified:false});
 }
 matches.sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id));
 const values=matches.map(m=>m.reference_close_change_percent).filter(v=>v!==null);
 return {matches,excluded,qualified_count:0,minimum:POLICY.minimum_cases,descriptive:{count:values.length,median:median(values),
  positive:values.filter(x=>x>0).length,negative:values.filter(x=>x<0).length,range:values.length?[Math.min(...values),Math.max(...values)]:null},
  warning:'Small selected mechanism cross-check, not forecast odds. Weak/procedurally different examples are not an eligible cohort; returns never affect matching rank.'};
}

export function rippleChecks(rows,calendar,anchor,asOf,options={}){
 const benchmark=reactionAt(rows,calendar,'IXIC',anchor,asOf,options),base=benchmark.first_close_percent?.exact;
 const hypotheses={AMD:'Competitor substitution might benefit other chip suppliers; customer switching is not established.',
 AVGO:'Alternative AI infrastructure exposure may differ from Nvidia; product demand and own news can dominate.',
 MSFT:'AI procurement and infrastructure spending could be affected later; there is no verified transmission to this price move.',
 QQQ:'Broad technology exposure provides context; it holds Nvidia and is not an independent control.'};
 return {baseline:benchmark,comparisons:Object.entries(hypotheses).map(([symbol,hypothesis])=>{
  const reaction=reactionAt(rows,calendar,symbol,anchor,asOf,options),move=reaction.first_close_percent?.exact;
  return {symbol,order:symbol==='MSFT'?3:2,hypothesis,classification:'unproven_transmission_hypothesis',reaction,
   excess_percentage_points:move!==null&&move!==undefined&&base!==null&&base!==undefined?move-base:null,
   caution:'Same-window relative move is not risk-adjusted abnormal return, attribution or a forecast.'};
 }),causal_effect_established:false};
}

export function replayAt(data,asOf,options={}){
 const detected=newsAt(data.news.articles,data.sources.sources,asOf,options),state=marketState(data.calendar,asOf),latest=detected.events.at(-1);
 if(!latest)return {as_of:asOf,detected,market:state,card:{what_happened:'No eligible Nvidia corporate news at this cutoff.',likely_outcome:'Insufficient evidence.',suggested_action:'Monitor / No Action',historical_details:[]},action:'No Action',paper_trades:0};
 const age=regularMinutes(data.calendar,latest.timing.at,asOf),wall=(stamp(asOf)-stamp(latest.timing.at))/86400000;
 const stale=age===null||age>POLICY.stale_regular_minutes||wall>POLICY.max_wall_age_days;
 const history=historicalCrossCheck(latest.classification,data.history.cases,data.sources.sources,asOf);
 const reaction=reactionAt(data.prices.rows,data.calendar,'NVDA',latest.timing.at,asOf,{precision:latest.timing.precision});
 const gap=reaction.gap_percent,alreadyMoved=gap&&gap.minimum*gap.maximum>0?Math.min(Math.abs(gap.minimum),Math.abs(gap.maximum))>=POLICY.already_moved_percent:false;
 const reasons=['NVDA_not_enabled_in_existing_GBP_paper_instrument_model','qualified_corporate_history_insufficient',
  'original_equity_quote_availability_and_exchange_print_timestamps_unverified'];
 if(state.state!=='regular_open')reasons.push('regular_market_closed_or_calendar_unknown');
 if(stale)reasons.push('stale_or_unestablished_news_age');
 if(alreadyMoved)reasons.push('opening_move_already_visible_under_nominal_daily_mark_assumption');
 if(latest.classification.counterpoint)reasons.push('disputed_allegation_or_company_counterpoint');
 const ripples=rippleChecks(data.prices.rows,data.calendar,latest.timing.at,asOf,{precision:latest.timing.precision});
 return {policy:POLICY,as_of:asOf,detected,market:state,latest_news_id:latest.id,news_publication:latest.timing,
  alert:{status:stale?'stale_context_only':'research_monitor',regular_minutes_since_publication:age,wall_days_since_publication:wall,
   availability_mode:latest.availability_mode,actual_historical_alert_proven:false,already_moved:alreadyMoved},
  historical_cross_check:history,reaction,ripples,action:'No Action',paper_trades:0,reasons,
  card:{what_happened:latest.summary,
   likely_outcome:`Uncertain. ${history.matches.length} sourced historical cross-checks; ${history.qualified_count} qualified. Other news and company responses may change the picture.`,
   suggested_action:'Monitor / No Action. A decline does not establish a short or a Buy; no supported GBP Nvidia paper execution is enabled.',historical_details:history.matches},
  evidence:'Limited',warning:'Allegations remain attributed; an investigation is not a finding. No correlation is called causation, no later headline enters an earlier cutoff.'};
}
