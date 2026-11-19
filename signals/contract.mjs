// Local reports cannot grant trade permission or self-certify independent validation.
export const MARKETS=Object.freeze(['NVDA','AMD','MRNA','BMY','SPY','GLD']);
export const COSTS=Object.freeze(['zero','declared','stressed','small_account_flat_fee']);
export function validateReport(data){
 if(data?.kind!=='PRIVATE_SIGNAL1_SCREEN'||data.schema_version!==1||data.all_history_previously_examined!==true)throw new Error('Expected an examined historical SIGNAL-1 screen report.');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(data.as_of)||!Number.isFinite(Date.parse(data.as_of))||!Number.isSafeInteger(data.source_rows)||data.source_rows<0)throw new Error('Invalid assessment date or source count.');
 if(!Array.isArray(data.cards)||data.cards.length>2000||!data.examples||!data.sources||!Array.isArray(data.issuer_controls)||!Array.isArray(data.limitations))throw new Error('Incomplete historical evidence.');
 const ids=new Set();
 for(const card of data.cards){
  if(ids.has(card.id)||!MARKETS.includes(card.instrument)||!['UP','DOWN'].includes(card.direction)||![1,5,20].includes(card.horizon)||!Array.isArray(card.example_ids))throw new Error('Invalid or duplicate historical hypothesis.');
  ids.add(card.id);
  if(card.as_of!==data.as_of||card.example_ids.some(id=>!data.examples[id]))throw new Error('Evidence does not match this assessment.');
  for(const cost of COSTS){const s=card.costs?.[cost],r=card.ratings?.[cost];
   if(!s||!r||!['NO ACTION','POSSIBLE','LIKELY'].includes(r.rating)||!Array.isArray(r.reasons)||!Array.isArray(r.confirmation))throw new Error('Missing cost or rating evidence.');
   for(const k of ['attempts','complete','missing','successful','unsuccessful','unchanged','control_pairs','distinct_years'])if(!Number.isSafeInteger(s[k])||s[k]<0)throw new Error('Invalid sample counts.');
   if(s.complete+s.missing!==s.attempts||s.successful+s.unsuccessful+s.unchanged!==s.complete||s.control_pairs>s.complete)throw new Error('Inconsistent historical sample counts.');
   if(Math.abs(Number(s.coverage)-(s.attempts?s.complete/s.attempts:0))>0.0002)throw new Error('Inconsistent evidence coverage.');
   for(const [k,v] of Object.entries(s))if((/percent$|_pp$|_gbp$/.test(k)||k==='coverage')&&v!==null&&!Number.isFinite(Number(v)))throw new Error('Invalid historical metric.');
  }
 }
 for(const e of Object.values(data.examples))if(!e.maturity_day||e.maturity_day>=data.as_of||e.date>e.maturity_day)throw new Error('Future or unmatured example in historical evidence.');
 for(const s of Object.values(data.sources))if(s.published_day>=data.as_of)throw new Error('Future source cannot support this assessment.');
 return data;
}
export function safeRating(card,cost,policy){
 const r=card.ratings[cost];
 // There is no reviewed independent validation in this release. An imported
 // flag, registry array or forged LIKELY badge cannot add it.
 if(r.rating==='LIKELY')return {...r,rating:'NO ACTION',direction:null,horizon:null,reasons:['This file cannot establish reviewed independent validation.']};
 const s=card.costs[cost],p=policy.possible,sign=card.direction==='UP'?1:-1;
 const fields=['mean_return_percent','median_return_percent','mean_net_gbp','median_net_gbp','later_mean_return_percent','later_median_return_percent','median_paired_difference_gbp'];
 const supported=s.complete>=p.min_complete&&Number(s.coverage)>=Number(p.min_coverage)&&s.distinct_years>=p.min_distinct_years&&s.later_complete>=p.min_later_complete&&s.control_pairs>=p.min_control_pairs&&fields.every(k=>s[k]!==null&&Number.isFinite(Number(s[k]))&&sign*Number(s[k])>0)&&(card.instrument==='SPY'||['median_SPY_excess_pp','median_net_SPY_excess_gbp'].every(k=>s[k]!==null&&sign*Number(s[k])>0));
 if(r.rating==='POSSIBLE'&&!supported)return {...r,rating:'NO ACTION',direction:null,horizon:null,reasons:['This file does not satisfy the registered evidence checks.'],execution_action:'No Action',current_signal:false};
 return {...r,direction:r.rating==='POSSIBLE'?card.direction:null,horizon:r.rating==='POSSIBLE'?card.horizon:null,current_signal:false,execution_action:'No Action',historical_success_is_forecast_probability:false};
}
export function rankedCards(data,{market='all',horizon='all',cost='declared',rating='all',policy}={}){
 if(!COSTS.includes(cost))throw new Error('Unknown cost scenario.');
 const grade={'NO ACTION':0,'POSSIBLE':1,'LIKELY':2};
 const rows=data.cards.filter(c=>(market==='all'||c.instrument===market)&&(horizon==='all'||c.horizon===Number(horizon))&&(rating==='all'||safeRating(c,cost,policy).rating===rating));
 return rows.sort((a,b)=>{const x=a.costs[cost],y=b.costs[cost];
  const ax=[grade[safeRating(a,cost,policy).rating],Number(x.coverage),Math.min(x.complete,100),x.distinct_years,x.control_pairs,-Math.abs(Math.min(0,Number(x.worst_directional_return_percent||0))),Math.abs(Number(x.median_return_percent||0))];
  const by=[grade[safeRating(b,cost,policy).rating],Number(y.coverage),Math.min(y.complete,100),y.distinct_years,y.control_pairs,-Math.abs(Math.min(0,Number(y.worst_directional_return_percent||0))),Math.abs(Number(y.median_return_percent||0))];
  for(let i=0;i<ax.length;i++)if(ax[i]!==by[i])return by[i]-ax[i];
  return a.id.localeCompare(b.id);
 });
}
