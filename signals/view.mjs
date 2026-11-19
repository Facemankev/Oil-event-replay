import {MARKETS,COSTS,validateReport,safeRating,rankedCards} from './contract.mjs';
const el=id=>document.getElementById(id);
const put=(id,text)=>{el(id).textContent=String(text)};
const state={report:null,policy:null,rows:[],selected:null,limit:12};
const numeric=(value,suffix='',signed=false)=>value===null||value===undefined?'Unavailable':`${signed&&Number(value)>0?'+':''}${Number(value).toFixed(2)}${suffix}`;
function sourceLink(parent,source){
 if(!source)return;
 try{const u=new URL(source.url);if(u.protocol!=='https:'||u.username||u.password)return;
 const a=document.createElement('a');a.href=u.href;a.textContent=source.title;a.target='_blank';a.rel='noopener noreferrer';parent.append(a)}catch{}
}
function items(id,values){el(id).replaceChildren();for(const text of values){const li=document.createElement('li');li.textContent=text;el(id).append(li)}}
function filters(){return {market:el('market').value,horizon:el('horizon').value,cost:el('cost').value,rating:el('rating-filter').value,policy:state.policy}}
function renderExamples(){
 const c=state.selected;if(!c)return;const cost=el('cost').value,sign=c.direction==='UP'?1:-1;
 el('examples').replaceChildren();let shown=0;
 for(const id of c.example_ids){const w=state.report.examples[id];if(!w)continue;
 const directional=sign*Number(w.change_percent);const filter=el('example-filter').value;
 if(filter==='successful'&&directional<=0||filter==='unsuccessful'&&directional>=0)continue;
 const li=document.createElement('li');const text=document.createElement('p');const o=w.costs[cost];
 text.textContent=`${w.instrument}, signal ${w.date}; later entry ${o.entry_date||'unavailable'} to ${o.exit_date||'unavailable'}. Price ${numeric(w.change_percent,'%',true)}; SPY excess ${numeric(w.SPY_excess_pp,' pp',true)}; hypothetical long net £${numeric(o.net_pnl_gbp,'',true)}. ${directional>0?'Successful direction':directional<0?'Unsuccessful direction':'Unchanged price'}.`;
 li.append(text);const news=document.createElement('p');news.textContent=w.catalyst.explanation+' '+w.catalyst.weakness+' Retrospective cross-check; not an input to the earlier signal.';li.append(news);
 for(const source of w.catalyst.sources){const s=state.report.sources[source];const line=document.createElement('p');sourceLink(line,s);if(s)line.append(document.createTextNode(` — ${s.publisher}, ${s.published_day}; ${s.published_at||'intraday publication clock unknown'}. Original receipt unknown.`));li.append(line)}
 el('examples').append(li);shown++;
 }
 if(!shown){const li=document.createElement('li');li.textContent='No displayed example matches this outcome filter. Missing evidence is not replaced.';el('examples').append(li)}
 put('example-note',`${shown} bounded examples shown from ${c.full_matured_examples} matured attempts. ${c.example_selection}`);
}
function showCard(card){
 state.selected=card;el('opportunity').hidden=!card;if(!card)return;
 const cost=el('cost').value,r=safeRating(card,cost,state.policy),s=card.costs[cost];
 put('signal-rating',r.rating);put('signal-window',r.direction?`${r.direction==='UP'?'↑ UP':'↓ DOWN'} · ${r.horizon} trading session${r.horizon===1?'':'s'}`:'Direction uncertain');
 put('what',`${card.instrument}: ${card.title.toLowerCase()} in past examples.`);
 put('outcome',r.direction?`${r.direction==='UP'?'↑ UP':'↓ DOWN'} ${card.hypothesis_kind==='reversal'?'reversal':'follow-through'} hypothesis over ${r.horizon} session${r.horizon===1?'':'s'} — exploratory.`:'Uncertain: the tested direction lacks sufficient support.');
 put('action',r.rating==='NO ACTION'?'NO ACTION':card.direction==='DOWN'?'POSSIBLE — Watch downside risk':'POSSIBLE — Watch for confirmation');
 put('caveat','Historical research only, not a current forecast. No paper entry or sale is authorised by this rating.');
 put('sample',`${s.complete} complete examples from ${s.attempts} matured attempts across ${s.distinct_years} years. ${s.missing} missing; ${s.control_pairs} matched quiet-period comparisons. Non-overlapping windows are not proven independent.`);
 put('success-definition',s.success_definition+' Previously examined periods are not untouched validation.');
 const stats=[['Successful direction examples',`${s.successful} (${numeric(s.historical_success_percent,'%')})`],['Unsuccessful direction examples',`${s.unsuccessful} (${numeric(s.historical_failure_percent,'%')})`],['Unchanged examples',s.unchanged],['Average / median price return',`${numeric(s.mean_return_percent,'%',true)} / ${numeric(s.median_return_percent,'%',true)}`],['Range of price returns',`${numeric(s.minimum_return_percent,'%',true)} to ${numeric(s.maximum_return_percent,'%',true)}`],['Average / median excess over SPY',`${numeric(s.mean_SPY_excess_pp,' pp',true)} / ${numeric(s.median_SPY_excess_pp,' pp',true)}`],['Average / median long net GBP',`£${numeric(s.mean_net_gbp,'',true)} / £${numeric(s.median_net_gbp,'',true)}`],['Median after-cost excess over SPY',`£${numeric(s.median_net_SPY_excess_gbp,'',true)}`],['Long outcomes after costs',`${s.net_winning} positive; ${s.net_losing} negative`],['Median long net minus quiet-period control',`£${numeric(s.median_paired_difference_gbp,'',true)}`],['Later examined sample',`${s.later_complete}; median price ${numeric(s.later_median_return_percent,'%',true)}`],['Mean estimated trading friction',`£${numeric(s.mean_estimated_friction_gbp)} on £${s.allocation_gbp}`]];
 el('stats').replaceChildren();for(const [label,value] of stats){const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;div.append(dt,dd);el('stats').append(div)}
 const fees=s.cost_assumptions;put('cost-note',`Illustrative costs, not a broker quote: £${fees.fee_gbp_per_leg} each way, ${fees.spread_bps} basis points full spread and ${fees.slippage_bps_per_leg} basis points slippage each way. Exact-date GBP/USD; no invented missing rates. ${card.instrument==='SPY'?'SPY compared with itself has zero excess; this is not an alpha claim.':''}`);
 items('reasons',r.reasons);items('confirmations',r.confirmation);
 renderExamples();
}
function renderRanked(){
 if(!state.report)return;
 state.rows=rankedCards(state.report,filters());const cost=el('cost').value;
 const counts={};for(const c of state.report.cards){const rating=safeRating(c,cost,state.policy).rating;counts[rating]=(counts[rating]||0)+1}
 put('counts',`${counts.POSSIBLE||0} POSSIBLE; ${counts['NO ACTION']||0} NO ACTION; ${counts.LIKELY||0} LIKELY across overlapping hypotheses. ${state.rows.length} match these filters.`);
 el('ranked').replaceChildren();el('empty').hidden=state.rows.length>0;
 if(!state.rows.some(c=>c.id===state.selected?.id))showCard(state.rows[0]||null);else showCard(state.rows.find(c=>c.id===state.selected.id));
 for(const c of state.rows.slice(0,state.limit)){const li=document.createElement('li'),button=document.createElement('button');button.type='button';button.dataset.card=c.id;button.setAttribute('aria-pressed',String(c.id===state.selected?.id));
 const name=document.createElement('span');name.textContent=`${c.instrument}: ${c.title}`;const meta=document.createElement('span');meta.className='rank-meta';meta.textContent=`${safeRating(c,cost,state.policy).rating} · ${c.direction} hypothesis · ${c.horizon} session${c.horizon===1?'':'s'} · ${c.costs[cost].complete} complete examples`;
 button.append(name,meta);button.addEventListener('click',()=>{showCard(c);for(const b of el('ranked').querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.card===c.id))});li.append(button);el('ranked').append(li)}
 el('show-more').hidden=state.rows.length<=state.limit;
}
function loadReport(data){
 state.report=validateReport(data);state.selected=null;state.limit=12;
 put('status',data.synthetic?'SYNTHETIC demonstration — fabricated test examples, not market evidence.':'Private historical analysis loaded locally. No current signal or trade permission.');
 put('scope',`Historical assessment ${data.as_of}. Prices and original availability remain unverified.`);
 put('coverage',`Assessment date ${data.as_of}; ${data.source_rows.toLocaleString()} observations. All historical periods were already examined. ${data.pending_count} unfinished windows remain pending. ${data.source_profile}`);
 items('limitations',data.limitations);el('research').hidden=false;document.querySelector('footer').append(el('file-panel'));
 el('issuer-controls').replaceChildren();for(const c of data.issuer_controls){const li=document.createElement('li');li.append(document.createTextNode(`${c.instrument}, ${c.publication_day}: `));sourceLink(li,c.source);if(c.reactions){const text=document.createElement('p');text.textContent='Publication-day close follow-through (not intraday causation): '+c.reactions.map(r=>r.horizon+' sessions '+numeric(r.change_percent,'%',true)).join('; ');li.append(text)}el('issuer-controls').append(li)}
 el('catalyst-contexts').replaceChildren();for(const group of data.catalyst_catalogue||[]){const li=document.createElement('li');const heading=document.createElement('strong');heading.textContent=group.context;li.append(heading);for(const c of group.cases){const p=document.createElement('p');p.textContent=`${c.instrument}, ${c.date}, observed discovery move ${numeric(c.observed_discovery_change_percent,'%',true)}: ${c.explanation} ${c.weakness}`;li.append(p);for(const id of c.sources){const line=document.createElement('p');sourceLink(line,data.sources[id]);li.append(line)}}el('catalyst-contexts').append(li)}
 renderRanked();
}
for(const market of MARKETS){const option=document.createElement('option');option.value=market;option.textContent=market;el('market').append(option)}
for(const id of ['market','horizon','cost','rating-filter'])el(id).addEventListener('change',()=>{state.limit=12;renderRanked()});
el('example-filter').addEventListener('change',renderExamples);el('show-more').addEventListener('click',()=>{state.limit+=12;renderRanked()});
for(const b of document.querySelectorAll('[data-theme]'))b.addEventListener('click',()=>{document.documentElement.dataset.theme=b.dataset.theme;for(const x of document.querySelectorAll('[data-theme]'))x.setAttribute('aria-pressed',String(x===b))});
for(const id of ['historical','current'])el(id+'-mode').addEventListener('click',()=>{el('history').hidden=id!=='historical';el('current').hidden=id!=='current';el('historical-mode').setAttribute('aria-pressed',String(id==='historical'));el('current-mode').setAttribute('aria-pressed',String(id==='current'))});
el('private-file').addEventListener('change',async event=>{try{const file=event.target.files[0];if(!file)return;if(file.size>16000000)throw new Error('Choose the compact screen JSON, not the full private analysis.');loadReport(JSON.parse(await file.text()))}catch(e){state.report=null;el('research').hidden=true;el('status').after(el('file-panel'));put('status','Could not load private evidence: '+e.message)}});
async function start(){try{const embedded=document.getElementById('embedded-policy');state.policy=embedded?JSON.parse(embedded.textContent):await (await fetch('../signal_ratings/policy.json')).json();if(state.policy.version!=='SIGNAL-1/1')throw new Error('Unsupported evidence policy');const data=document.getElementById('embedded-report');if(data)loadReport(JSON.parse(data.textContent))}catch(e){el('research').hidden=true;put('status','Could not load the registered policy/evidence: '+e.message)}}
start();
