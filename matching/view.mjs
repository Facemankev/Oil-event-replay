import {categories,mechanisms,rankMatches,visibleReactions,evidenceStrength} from './engine.mjs';
const $ = id => document.getElementById(id);
const node = (tag,text,cls) => {const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const significance = {
 weather:'Storm landfall can disrupt production, refining and transport, while closures can also reduce demand. The affected infrastructure matters more than the storm label alone.',
 production_policy:'Production decisions can change expected supply. Announced targets differ from actual output, and the market may have anticipated the decision.',
 sanctions:'Energy sanctions can change trade routes, costs and accessible supply. Exceptions, enforcement and implementation dates can matter more than the announcement.',
 conflict:'Conflict can alter supply-risk expectations. Geographic proximity does not establish a physical outage, and these events differ sharply in scope.',
 strategic_stocks:'An emergency stock release changes available supply for a period. Its scale, duration and wider market conditions determine its relevance.',
 demand_shock:'A demand shock can change transport and industrial oil consumption. A formal declaration often follows earlier economic effects and expectations.'
};
const money = raw => raw===null?'Unavailable':Number(raw).toFixed(2);
let catalog, report;
const mechanismMap={weather:['landfall'],production_policy:['output_cut','output_increase','output_hold','production_target','producer_cooperation'],sanctions:['sanctions_restriction','price_cap'],conflict:['physical_attack','armed_conflict'],strategic_stocks:['stock_release'],demand_shock:['pandemic_declaration']};
function mechanismOptions(){
 $('mechanism').replaceChildren(new Option('Unknown / broad category only',''),...mechanismMap[$('category').value].map(k=>new Option(mechanisms[k],k)));
}
function readQuery(){return {title:$('title').value,category:$('category').value,market:$('market').value,
 occurred:$('occurred').value,publicDate:$('public').value,location:$('location').value,
 mechanism:$('mechanism').value,severity:$('severity').value,excludeId:$('example').value};}
function sourceLink(source){const a=node('a',source.publisher);const u=new URL(source.url);if(u.protocol!=='https:')throw Error('Unsafe evidence link');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}
function card(match,q){
 const e=match.event,rows=visibleReactions(match,q,$('verified-only').checked),strength=evidenceStrength(match,rows);
 const section=node('article',undefined,'mr-panel mr-glass mr-stack');section.dataset.event=e.id;
 const head=node('div',undefined,'match-head');head.append(node('h3',e.title),node('span',`${match.similarity} match · ${strength.label} evidence`,'mr-badge'));section.append(head);
 section.append(node('p',e.description));
 const why=node('ul',undefined,'reason-list');match.reasons.forEach(x=>why.append(node('li',x)));section.append(node('h4','Why it matched'),why);
 section.append(node('p',strength.explanation,'mr-note'));
 section.append(node('p',`Occurred: ${e.occurred.at||e.occurred.date}. First public: ${e.first_public.at||e.first_public.date||'not established'} (${e.first_public.status.replaceAll('_',' ')}). Supporting-publication anchor: ${e.reactions.anchor||'unknown'}.`,'mr-note'));
 section.append(node('h4','Historical reaction'));
 const hasProvisional=rows.some(r=>r.status==='ok' && r.verification!=='primary_EIA');
 section.append(node('p',hasProvisional?'Provisional seed prices · primary EIA reconciliation has not succeeded.':$('verified-only').checked?'Primary-only view · unverified price numbers are hidden.':'Prices retain their per-window source status.','notice'));
 const list=node('ul',undefined,'reaction-list');
 for(const r of rows){
  const tile=node('li',undefined,'mr-tile mr-glass');tile.append(node('span',`${r.days} observation ${r.days===1?'day':'days'}`,'mr-label'));
  if(r.status==='ok'){
   const percent=r.change_percent===null?'% undefined':`${Number(r.change_percent)>0?'+':''}${Number(r.change_percent).toFixed(2)}%`;
   tile.append(node('strong',percent),node('span',`${Number(r.absolute_change)>0?'+':''}${money(r.absolute_change)} USD/barrel`,'mr-meta'),node('span',`${r.baseline_date} → ${r.end_date}`,'mr-meta'),node('span',r.verification==='primary_EIA'?'Primary EIA':'Provisional','mr-meta'));
  } else tile.append(node('strong','Unavailable'),node('span',r.status.replaceAll('_',' '),'mr-meta'));
  list.append(tile);
 }
 section.append(list);
 const details=node('details',undefined,'mr-disclosure');details.append(node('summary','Show exact prices, sources and missing evidence'));
 const wrap=node('div',undefined,'mr-table-scroll');const table=node('table',undefined,'mr-table');const header=node('tr');['Days','Baseline','End','Change','Source status'].forEach(x=>header.append(node('th',x)));table.append(header);
 rows.forEach(r=>{const tr=node('tr');[r.days,r.status==='ok'?`${r.baseline_date}: ${r.baseline}`:'Unavailable',r.status==='ok'?`${r.end_date}: ${r.end}`:'Unavailable',r.status==='ok'?`${r.absolute_change} USD/barrel`:'Unavailable',r.status==='ok'?r.verification:r.status].forEach(x=>tr.append(node('td',String(x))));table.append(tr);});wrap.append(table);details.append(wrap);
 const evidence=node('p');for(const s of e.evidence){evidence.append(sourceLink(s),document.createTextNode(` · ${s.published.at||s.published.date||'time unknown'} · ${s.stable_reference}. `));}details.append(evidence);
 const allSources=new Map();rows.forEach(r=>Object.entries(r.sources).forEach(([id,s])=>allSources.set(id,s)));
 allSources.forEach(s=>{const p=node('p',`${s.source_kind} · retrieved ${s.retrieved_at} · SHA-256 ${s.sha256} · `,'mr-note');const a=node('a','Price source');const u=new URL(s.source_url);if(u.protocol==='https:'){a.href=u.href;p.append(a);}details.append(p);});
 details.append(node('p',e.features.basis,'mr-note'));const gaps=node('ul',undefined,'reason-list');match.gaps.forEach(g=>gaps.append(node('li',g)));details.append(gaps);section.append(details);
 section.append(node('h4','Potential significance'),node('p',significance[e.category]+' Compare the short and longer windows above; no minimum move or statistical significance has been established.'));
 section.append(node('h4','Risks and uncertainty'),node('p',e.uncertainty),node('p','A past move does not prove this event caused it or predict the next move. Conditions, anticipation and other news differ. This is not an estimate of a small-stake trading return.','mr-note'));
 return section;
}
function render(event){
 event?.preventDefault();$('error').textContent='';$('results').replaceChildren();
 try{const q=readQuery(),matches=rankMatches(q,catalog.events);$('summary').textContent=`${q.title} · ${q.market.toUpperCase()} · ${matches.length} eligible historical ${matches.length===1?'match':'matches'}. ${matches.length?'Showing up to six; similarity points never use price outcomes.':'No sufficiently comparable events in this small library. Try a broader event detail; no replacement is invented.'}`;
 matches.slice(0,6).forEach(m=>$('results').append(card(m,q)));
 }catch(e){$('summary').textContent='No results shown.';$('error').textContent=e.message;}
}
const scheme=matchMedia('(prefers-color-scheme: dark)');
const isDark=()=>document.documentElement.dataset.theme==='dark'||(!document.documentElement.dataset.theme&&scheme.matches);
const themeLabel=()=>{$('theme').textContent=isDark()?'Use light mode':'Use dark mode';};
$('theme').addEventListener('click',()=>{document.documentElement.dataset.theme=isDark()?'light':'dark';themeLabel();});
scheme.addEventListener('change',themeLabel);themeLabel();
try{
 const responses=await Promise.all([fetch('catalog.json'),fetch('validation-report.json')]);if(responses.some(r=>!r.ok))throw Error('Data files are unavailable.');[catalog,report]=await Promise.all(responses.map(r=>r.json()));
 $('verification').textContent=report.verified?'Primary reconciliation ran; inspect the report and per-window sources for discrepancies. Original publication times remain unknown.':`Primary EIA verification is ${report.status}. All seed-based reactions are provisional. ${catalog.price_counts.brent.toLocaleString()} Brent / ${catalog.price_counts.wti.toLocaleString()} WTI prices; ${catalog.events.length} sourced events.`;
 Object.entries(categories).forEach(([k,v])=>$('category').append(new Option(v,k)));mechanismOptions();$('mechanism').value='landfall';
 catalog.events.forEach(e=>$('example').append(new Option(e.title,e.id)));
 const today=new Date().toISOString().slice(0,10);$('occurred').value=today;$('public').value=today;
 $('category').addEventListener('change',()=>{mechanismOptions();$('example').value='';});
 $('example').addEventListener('change',()=>{const e=catalog.events.find(e=>e.id===$('example').value);if(!e)return;$('title').value=e.title;$('category').value=e.category;mechanismOptions();$('mechanism').value=e.features.mechanism||'';$('location').value=e.geography;$('severity').value='';$('occurred').value=e.occurred.date;$('public').value=e.reactions.anchor||e.occurred.date;render();});
 $('query').addEventListener('submit',render);$('verified-only').addEventListener('change',render);render();
}catch(e){$('verification').textContent='The event library could not load. No results are available.';$('summary').textContent='Serve this page over HTTP with all matching files present.';$('error').textContent=e.message;$('query').querySelector('button').disabled=true;}
