/** Cohort summaries and bounded research priority, not forecasts or trade P&L. */
import {rankMatches,visibleReactions,validateQuery} from './engine.mjs';
export const HORIZONS=Object.freeze([1,3,5,10,20]);
export const median=values=>{
  if(!values.length)return null;
  const ordered=[...values].sort((a,b)=>a-b),middle=Math.floor(ordered.length/2);
  return ordered.length%2?ordered[middle]:(ordered[middle-1]+ordered[middle])/2;
};
const finite=value=>(typeof value==='number'||(typeof value==='string'&&/^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/.test(value)))&&Number.isFinite(Number(value));
const distribution=(values,directions=values)=>({count:values.length,median:median(values),minimum:values.length?Math.min(...values):null,
 maximum:values.length?Math.max(...values):null,positive:directions.filter(v=>v>0).length,
 negative:directions.filter(v=>v<0).length,flat:directions.filter(v=>v===0).length});

export function summarize(matches,query,horizon,{verifiedOnly=false}={}){
  validateQuery(query);
  if(!HORIZONS.includes(horizon))throw Error('Unsupported summary horizon.');
  const comparable=matches.filter(m=>m.similarity!=='Weak'&&(!m.locationRequired||m.locationMatch));
  const candidates=[],excluded=[];
  for(const match of comparable){
    const row=visibleReactions(match,query,verifiedOnly).find(r=>r.days===horizon);
    if(!row || row.status!=='ok' || !finite(row.absolute_change) || (row.change_percent!==null && !finite(row.change_percent))){
      excluded.push({id:match.event.id,reason:row?.status||'missing_horizon'});continue;
    }
    candidates.push({match,row});
  }
  // Choose chronological, non-overlapping windows BEFORE examining outcomes.
  // This reduces duplicate episodes without claiming statistical independence.
  candidates.sort((a,b)=>a.row.baseline_date.localeCompare(b.row.baseline_date)||a.match.event.id.localeCompare(b.match.event.id,'en'));
  const included=[];
  let previousEnd=null;
  for(const item of candidates){
    if(previousEnd && item.row.baseline_date<=previousEnd){
      excluded.push({id:item.match.event.id,reason:'overlapping_price_window'});continue;
    }
    included.push(item);previousEnd=item.row.end_date;
  }
  const percent=included.filter(x=>finite(x.row.change_percent)).map(x=>Number(x.row.change_percent));
  const absolute=included.map(x=>Number(x.row.absolute_change));
  const primary=included.filter(x=>x.row.verification==='primary_EIA').length;
  const precise=included.filter(x=>x.match.event.first_public.precision==='minute' && x.match.event.first_public.status!=='not_established').length;
  const severityKnown=included.filter(x=>x.match.severityMatch).length;
  const pct=distribution(percent,included.filter(x=>finite(x.row.change_percent)).map(x=>Number(x.row.absolute_change))),usd=distribution(absolute);
  const risks=[];
  if(included.length<3)risks.push('Fewer than three non-overlapping price windows');
  if(primary<included.length)risks.push('Prices remain provisional pending the EIA reconciliation review');
  if(precise<included.length)risks.push('Some first-public clocks are imprecise or unestablished');
  if(severityKnown<included.length)risks.push('Comparable severity is missing for some matches');
  if(pct.positive && pct.negative)risks.push('Past price directions were mixed');
  if(pct.count && pct.maximum-pct.minimum>20)risks.push('Observed percentage range exceeds 20 points');
  if(excluded.some(x=>x.reason==='overlapping_price_window'))risks.push('Overlapping windows were excluded; events can still be correlated');
  if(percent.length<absolute.length)risks.push('Some percentage changes are undefined for nonpositive starting prices');
  risks.push('Non-overlapping events can still share the same market regime or other news');
  risks.push('Current historical vintages and unknown price publication clocks prevent a point-in-time backtest');
  const evidence=included.length>=3 && primary===included.length && precise===included.length && severityKnown===included.length?'Moderate':'Limited';
  // Evidence tier always wins. Within a tier, support and risk dominate a
  // bounded, sign-neutral movement component (0–4 points). No expected gain.
  const riskPenalty=(included.length<3?4:0)+(primary<included.length?2:0)+(precise<included.length?2:0)+
    (severityKnown<included.length?1:0)+(pct.positive&&pct.negative?2:0)+(pct.count&&pct.maximum-pct.minimum>20?3:0);
  const movementComponent=pct.median===null?0:Math.min(Math.abs(pct.median),10)*0.4;
  const priority=Number((Math.min(included.length,5)*3+movementComponent-riskPenalty).toFixed(4));
  return {market:query.market,days:horizon,eligible_event_count:matches.length,comparable_event_count:comparable.length,
    weak_excluded:matches.filter(m=>m.similarity==='Weak').length,location_excluded:matches.filter(m=>m.similarity!=='Weak'&&m.locationRequired&&!m.locationMatch).length,window_count:included.length,percent:pct,absolute:usd,
    undefined_percent_count:absolute.length-percent.length,primary_window_count:primary,
    precise_event_count:precise,severity_matched_count:severityKnown,evidence,evidence_rank:evidence==='Moderate'?1:0,
    risks,risk_penalty:riskPenalty,movement_component:movementComponent,research_priority:priority,
    included_ids:included.map(x=>x.match.event.id),excluded,
    windows:included.map(({match,row})=>({event_id:match.event.id,baseline_date:row.baseline_date,end_date:row.end_date,
      baseline:row.baseline,end:row.end,absolute_change:row.absolute_change,change_percent:row.change_percent,
      verification:row.verification,sources:row.sources})),
    point_in_time_safe:false,interpretation:'Descriptive selected-sample history; positive/negative counts are not future probabilities.'};
}

export function analyse(query,events,options={}){
  validateQuery(query);
  const opportunities=[],matchesByMarket={};
  for(const market of ['brent','wti']){
    const q={...query,market};const matches=rankMatches(q,events);matchesByMarket[market]=matches;
    for(const days of HORIZONS)opportunities.push(summarize(matches,q,days,options));
  }
  opportunities.sort((a,b)=>b.evidence_rank-a.evidence_rank || Number(b.percent.count>0)-Number(a.percent.count>0) ||
    b.research_priority-a.research_priority || a.market.localeCompare(b.market,'en') || a.days-b.days);
  return {methodology:'cohort-summary-v1',query,opportunities,matchesByMarket,
    ranking_note:'Evidence first; then non-overlapping support, risk penalties and a capped sign-neutral historical movement component. Not predicted gain.'};
}
