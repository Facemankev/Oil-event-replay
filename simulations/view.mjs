const $=id=>document.getElementById(id);
const money=v=>v===null||v===undefined?'Unavailable':`${Number(v)<0?'−':''}£${Math.abs(Number(v)).toFixed(2)}`;
function text(tag,value){const n=document.createElement(tag);n.textContent=value;return n;}
function row(values){const r=document.createElement('tr');for(const v of values)r.append(text('td',v));return r;}
export function draw(points){
 const svg=$('chart');svg.replaceChildren();if(!points.length){svg.append(text('title','No complete price path'));return;}
 const ns='http://www.w3.org/2000/svg',values=points.map(p=>Number(p.liquidation_equity_gbp)),low=Math.min(...values)-.1,high=Math.max(...values)+.1;
 const x=i=>70+i*(600/Math.max(1,points.length-1)),y=v=>205-(v-low)/(high-low)*150;
 const add=(tag,attrs,value)=>{const n=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(value)n.textContent=value;svg.append(n);return n;};
 add('title',{},`Hypothetical account if liquidated from ${points[0].date} to ${points.at(-1).date}; not a forecast`);
 add('line',{x1:70,x2:70,y1:40,y2:210,class:'chart-event'});
 add('text',{x:75,y:25,class:'chart-label'},'Hypothetical entry');
 add('text',{x:3,y:55,class:'chart-label'},money(high));add('text',{x:3,y:205,class:'chart-label'},money(low));
 add('polyline',{points:points.map((p,i)=>`${x(i)},${y(values[i])}`).join(' '),class:'chart-line'});
 points.forEach((p,i)=>{const c=add('circle',{cx:x(i),cy:y(values[i]),r:i===0||i===points.length-1?4:2,fill:'currentColor'});const t=document.createElementNS(ns,'title');t.textContent=`${p.date}: ${money(p.liquidation_equity_gbp)}`;c.append(t);});
 add('text',{x:70,y:240,class:'chart-label','text-anchor':'start'},points[0].date);add('text',{x:670,y:240,class:'chart-label','text-anchor':'end'},points.at(-1).date);
}
export function render(data,index){
 const c=data.default_cases[index];if(!c)throw Error('Missing case');const p=c.plan,o=c.outcome;
 $('what').textContent=`${p.title}. Reference: ${p.market}${p.exposure?' — '+p.exposure:''}.`;
 $('when').textContent=`Supporting publication eligibility bound: ${p.decision_bound}. Original historical availability is unproven. Entry dates are strictly later than this bound.`;
 $('meaning').textContent=o.status==='simulated_reference_path'?`This fixed hypothetical rule produced ${money(o.net_pnl_gbp)} net (${money(o.gross_pnl_gbp)} before costs) on a £5 budget. ${o.net_outcome==='positive'?'This example gained.':'This example lost or was flat.'} It does not establish a repeatable strategy.`:`No settled result: ${o.reason.replaceAll('_',' ')}. Missing future marks keep the earlier hypothesis visible; no closing price is invented.`;
 $('costs').textContent='Default: 1p fee each leg, 10 basis points full spread, 5 basis points slippage each leg. Both fees are reserved inside the £5 budget. Higher-cost scenarios and all losing/missing cases remain below. No broker tariff or executable oil product is supplied.';
 $('path').replaceChildren(...o.path.map(p=>row([p.date,p.raw_value+' / '+p.raw_unit,money(p.reference_gbp),money(p.liquidation_equity_gbp),p.hypothetical_action])));draw(o.path);
 const s=data.source_links.filter(s=>s.id===p.publication_source||o.path.some(p=>p.source_id===s.id));$('sources').replaceChildren('Source: ');
 for(const source of s){const u=new URL(source.url);if(u.protocol!=='https:'||u.username||u.password)throw Error('Unsafe source');const a=text('a',source.publisher);a.href=u.href;a.rel='noopener noreferrer';$('sources').append(a,' ');}
 if(o.path.length)$('sources').append('Exact-date GBP conversion: Federal Reserve H.10. No original publication-clock or exchange-fill verification.');
 $('coverage').textContent=`${data.universe_events} events; ${data.event_market_cases} targeted event/market cases, including missing histories and conversion-only context. Results from overlapping markets are not independent. No-trade baseline: £50 unchanged. Same-window costed buy-and-hold and one-position portfolio records are included in report.json.`;
 $('strategies').replaceChildren(...data.rule_summaries.map(s=>row([`${s.rule.replaceAll('_',' ')} / ${s.horizon}`,s.cost,`${s.complete} / ${s.attempts}`,`${s.positive} / ${s.negative} / ${s.flat}`,money(s.median_net_pnl_gbp)])));
 $('limits').textContent=data.limitations.join(' ');
 $('action').textContent='No Action';$('suggestion').textContent='Explore the hypothetical Buy, Hold and Sell path only. Original availability, tradable products and a tested edge remain unproven. Your practice account is unchanged.';
 $('answers').hidden=false;
}
async function start(){
 let data=null;
 try{const r=await fetch('report.json');if(!r.ok)throw Error('Missing report');data=await r.json();if(data.kind!=='retrospective_hypothesis_only'||data.supported_entries!==0)throw Error('Wrong report');
 $('case').replaceChildren(...data.default_cases.map((c,i)=>{const o=text('option',`${c.plan.title} — ${c.plan.market}`);o.value=String(i);return o;}));$('case').disabled=false;
 const first=data.default_cases.findIndex(c=>c.outcome.status==='simulated_reference_path');$('case').value=String(Math.max(0,first));
 $('case').addEventListener('change',()=>render(data,Number($('case').value)));
 $('opt-in').addEventListener('change',()=>{const on=$('opt-in').checked;$('controls').hidden=!on;$('answers').hidden=!on;$('load-status').textContent=on?'Retrospective hypothesis only. No validated trade or account action.':'Research is off. The validated engine remains No Action.';if(on)render(data,Number($('case').value));});
 }catch{$('opt-in').disabled=true;$('controls').hidden=true;$('answers').hidden=true;$('load-status').textContent='The sourced report could not load. No hypothetical or validated action is available.';}
}
if(typeof document!=='undefined'){
 for(const b of document.querySelectorAll('[data-theme]'))b.addEventListener('click',()=>{document.documentElement.dataset.theme=b.dataset.theme;for(const x of document.querySelectorAll('[data-theme]'))x.setAttribute('aria-pressed',String(x===b));});
 start();
}
