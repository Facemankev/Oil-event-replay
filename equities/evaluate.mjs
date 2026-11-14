/** Frozen chronological company-news replay; observations are not paper fills. */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha,root} from '../verification/load.mjs';
import {loadEquities} from './load.mjs';
import {replayAt} from './engine.mjs';
export const CUT_OFFS=['2026-11-08T19:59:59Z','2026-11-08T20:01:00Z','2026-11-09T14:29:00Z',
 '2026-11-09T14:31:00Z','2026-11-09T15:30:00Z','2026-11-09T21:01:00Z','2026-11-12T15:00:00Z','2026-11-14T12:00:00Z'];
export function buildReport(data=loadEquities()){
 const records=CUT_OFFS.map(asOf=>replayAt(data,asOf));
 const delayed=[0,60,3600,18*3600].map(latencySeconds=>({latency_seconds:latencySeconds,replay:replayAt(data,'2026-11-09T15:30:00Z',{latencySeconds})}));
 const firstClose=records.find(r=>r.as_of==='2026-11-09T21:01:00Z');
 return {method:'evt-1-nvda-company-news-v1',input_hashes:data.hashes,
  summary:{publication_cards:data.news.articles.length,underlying_developments:4,corporate_historical_cases:data.history.cases.length,
   daily_provider_rows:data.prices.rows.length,symbols:['NVDA','AMD','AVGO','MSFT','QQQ','IXIC'],
   replay_cutoffs:records.length,No_Action:records.filter(r=>r.action==='No Action').length,Buy:0,Short:0,paper_trades:0,
   qualified_comparable_cases:0,verified_intraday_reactions:0,first_regular_close_change_percent:firstClose.reaction.first_close_percent.exact,
   opening_price_conflict:firstClose.reaction.first_regular_open.point.status,
   limitations:data.sources.limitations},
  protocol:'Sourced publication plus explicit detector latency, or conservative day-only eligibility. Freeze each decision with only news and nominal daily marks available by that cutoff. No live trade, no guaranteed pattern, no verified intraday claim.',
  first_session:firstClose,latency_sensitivity:delayed,records};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const report=buildReport(),text=JSON.stringify(report,null,2)+'\n';
 if(process.argv.includes('--check')){if(readFileSync(new URL('RESULTS.sha256',import.meta.url),'utf8').trim()!==sha(Buffer.from(text)))throw Error('Company replay changed; review evidence before changing digest');}
 else if(process.argv.includes('--output')){
  const path=resolve(process.argv[process.argv.indexOf('--output')+1]),work=fileURLToPath(new URL('work/',root));
  if(!path.startsWith(work))throw Error('Full reports belong in a new work/ file');mkdirSync(dirname(path),{recursive:true});writeFileSync(path,text,{flag:'wx'});
 }
 console.log(JSON.stringify(report.summary,null,2));
}
