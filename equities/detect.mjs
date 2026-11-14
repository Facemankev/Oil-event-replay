/** Inspect curated history or actual local feed receipts with the same detector. */
import {readFileSync} from 'node:fs';
import {loadEquities} from './load.mjs';
import {replayAt,isStamp} from './engine.mjs';
const data=loadEquities(),index=process.argv.indexOf('--as-of');
const asOf=index>=0?process.argv[index+1]:'2026-11-09T21:01:00Z';
if(!isStamp(asOf))throw Error('Choose an explicit --as-of timestamp with timezone');
const input=process.argv.indexOf('--input');
if(input>=0){const incoming=JSON.parse(readFileSync(process.argv[input+1],'utf8'));if(!Array.isArray(incoming.articles))throw Error('Collector news.json expected');data.news=incoming;}
const r=replayAt(data,asOf),out={as_of:r.as_of,market:r.market.state,action:r.action,three_answers:r.card,
 alert:r.alert||null,news_developments:r.detected.events.length,deduplicated_copies:r.detected.duplicates,
 first_close_percent:r.reaction?.first_close_percent||null,
 opening_gap:r.reaction?.gap_percent||null,ripples:r.ripples?.comparisons.map(c=>({symbol:c.symbol,order:c.order,
 observed_close_percent:c.reaction.first_close_percent?.exact??null,relative_to_Nasdaq_pp:c.excess_percentage_points,
 hypothesis:c.hypothesis,causal_effect_established:false})),
 reasons:r.reasons||['no_eligible_company_news'],limitations:'Daily provider marks and scheduled boundaries only; no verified intraday prints, original quote timing or GBP Nvidia execution. Monitor is research, not a trade instruction.'};
console.log(JSON.stringify(out,null,2));
