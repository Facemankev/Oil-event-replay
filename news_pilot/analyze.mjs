/** Local research card only; do not deliver messages or call accounting. */
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {classify,marketState,regularMinutes,historicalCrossCheck,isStamp,rippleChecks,reactionAt} from '../equities/engine.mjs';
import {loadEquities} from '../equities/load.mjs';
import {json} from '../verification/load.mjs';
const registry=JSON.parse(readFileSync(new URL('registry.json',import.meta.url),'utf8'));
const time=s=>{if(!isStamp(s))throw Error('Explicit timestamp required');return Date.parse(s);};
const canonical=u=>{const url=new URL(u);if(url.protocol!=='https:'||url.username||url.password||/key|token|secret|password/i.test(url.search))throw Error('Public source URL required');url.hash='';for(const k of [...url.searchParams.keys()])if(k.startsWith('utm_'))url.searchParams.delete(k);return url.href;};

export function classifyShock(article){
 if(article.source_kind==='product_release')return {company:article.company,type:'company_product_update',sector:'semiconductors',categories:['product_release'],location:['US'],severity:null,stage:'product_update',materiality:'unestablished'};
 const text=article.title+' '+(article.body_text||article.summary),company=article.company==='NVDA'?classify({title:'NVIDIA '+article.title,summary:article.body_text||article.summary}):null;
 if(company)return {...company,type:'company_specific',materiality:'unestablished'};
 const categories=[];
 if(/\b(central bank|interest rate|federal funds|monetary policy)\b/i.test(text))categories.push('monetary_policy');
 if(/\b(oil|brent|wti|petroleum)\b/i.test(text)&&/\b(supply|shutdown|disruption|output|production)\b/i.test(text))categories.push('commodity_supply');
 if(/\b(tariff|sanction|export restriction|trade restriction)\b/i.test(text))categories.push('trade_restriction');
 return categories.length?{company:null,type:'wider_market',categories,materiality:'unestablished',severity:null}:null;
}

export function analyze(articles,asOf,data=loadEquities()){
 const cutoff=time(asOf),excluded=[],groups=new Map();
 for(const a of articles){
  if(time(a.first_seen_at)>cutoff){excluded.push({reason:'future_receipt'});continue;}
  const source=registry[a.source_id];if(!source)throw Error('Unregistered pilot source');
  const url=canonical(a.url);if(![source.link_prefix,...source.alternate_article_prefixes||[]].some(prefix=>url.startsWith(prefix))||new URL(url).search)throw Error('Unapproved pilot article');
  const clocks=[a.published_at,a.updated_at].filter(Boolean).map(time);
  if(clocks.some(t=>t>cutoff)){excluded.push({reason:'future_declared_publication_or_update'});continue;}
  const knownIssuerCopies=new Set(['https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors','https://investor.nvidia.com/news/press-release-details/2026/Statement-from-NVIDIA-Board-of-Directors/default.aspx','https://www.nasdaq.com/press-release/statement-nvidia-board-directors-2026-11-08']);
  const family=knownIssuerCopies.has(url)?'nvda-board-2026-11-08':url;
  if(!groups.has(family))groups.set(family,[]);groups.get(family).push({...a,company:source.company,source_kind:source.kind});
 }
 const cards=[];
 for(const versions of groups.values()){
  versions.sort((a,b)=>time(a.first_seen_at)-time(b.first_seen_at));
  const a=versions.at(-1),allText=versions.map(v=>v.body_text||v.summary).join(' ');
  const shock=classifyShock({...a,body_text:allText});if(!shock)continue;
  const publications=versions.map(v=>v.published_at).filter(Boolean).sort((x,y)=>time(x)-time(y));
  const publication=versions[0].published_at?publications[0]:null,age=publication?(cutoff-time(publication))/1000:null;
  const tradingAge=publication?regularMinutes(data.calendar,publication,asOf):null;
  const stale=age===null||age>7*86400||tradingAge===null||tradingAge>60;
  const history=shock.company==='NVDA'?historicalCrossCheck(shock,data.history.cases,data.sources.sources,asOf):{matches:[],qualified_count:0,minimum:8};
  const macro=shock.categories.includes('commodity_supply')?json('matching/cohort-catalog.json').events
   .filter(e=>e.first_public.at&&time(e.first_public.at)<cutoff&&['weather','production_policy','sanctions','conflict'].includes(e.category))
   .map(e=>({id:e.id,similarity:'Weak',reason:'Oil-supply words alone do not establish event mechanism, location, direction or severity.'})):[];
  const counterpoint=/deni\w*|disput\w*|no reason to believe|not established|not a finding/i.test(allText);
  let descriptive=null;
  if(publication&&shock.company==='NVDA'){
   const r=rippleChecks(data.prices.rows,data.calendar,publication,asOf),own=reactionAt(data.prices.rows,data.calendar,'NVDA',publication,asOf);
   descriptive={scope:'retained current-vintage daily context only; not live or original-as-of verified',
    own_percent:own.first_close_percent?.exact??null,opening_gap_range:own.gap_percent,
    peers:r.comparisons.map(c=>({symbol:c.symbol,percent:c.reaction.first_close_percent?.exact??null})),
    causal_effect_established:false};
  }
  const contradiction=/alleg\w*|report\w*|investigat\w*/i.test(allText)&&counterpoint;
  cards.push({source_url:canonical(a.url),source_family:a.source_family,source_family_count:1,title:a.title,source_kind:a.source_kind,
   first_seen_at:versions[0].first_seen_at,latest_version_first_seen_at:a.first_seen_at,published_at:publication,updated_at:a.updated_at,
   versions:versions.map(v=>({content_sha256:v.content_sha256,first_seen_at:v.first_seen_at,published_at:v.published_at,updated_at:v.updated_at})),
   publication_to_card_seconds:age,receipt_to_card_seconds:(cutoff-time(a.first_seen_at))/1000,
   freshness:stale?'stale_or_original_publication_unknown':'fresh_under_publisher_clock_assumption',regular_minutes_age:tradingAge,
   classification:shock,historical_cross_check:history,macro_cross_check:macro,contradictory_claim_or_counterpoint:contradiction,
   peer_price_check:{status:'timestamped_peer_quotes_unavailable',descriptive_cross_check:descriptive,latest_retained_daily_date:data.prices.rows.filter(r=>r.date<asOf.slice(0,10)).map(r=>r.date).sort().at(-1)||null,
    caution:'Prior daily moves are not current peer evidence. No opposite/confirming live direction is inferred.'},
   action:'No Action',alert_status:stale?'context_only':'research_monitor',
   reasons:['materiality_unestablished','historical_support_unqualified','verified_timestamped_equity_quotes_unavailable','no_supported_equity_execution'],
   three_answers:{what_happened:a.title+(contradiction?' — attributed claims and counterpoints both retained.':''),
    likely_outcome:'Uncertain. Historical similarity and market transmission are unproven.',
    suggested_action:'Monitor / No Action. No supported paper entry or automatic order.'}});
 }
 return {as_of:asOf,market:marketState(data.calendar,asOf),received_versions:groups.size,excluded,
  cards,Buy:0,paper_trades:0,continuous_monitoring:false,external_alerts_sent:0,
  warning:'Local analysis of observed receipts, not a continuously operated or delivered alert service. Publisher time is not first dissemination; updated-only items do not prove fresh news.'};
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const input=JSON.parse(readFileSync(0,'utf8'));console.log(JSON.stringify(analyze(input.articles,input.as_of)));
}
