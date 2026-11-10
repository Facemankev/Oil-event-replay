/** UI drilldown over the existing deterministic matcher; no new event/price data. */
import {rankMatches,validDay} from '../matching/engine.mjs';
import {matchingQueryAt} from './paths.mjs';

export function historicalMatches(data,catalog,cursor){
 const query=matchingQueryAt(data,catalog,cursor);
 return rankMatches(query,catalog.events).filter(m=>m.similarity!=='Weak'&&(!m.locationRequired||m.locationMatch));
}
export function eventRoute(hash){
 const match=/^#event\/([^/]+)\/(brent|wti)$/.exec(hash);
 if(!match)return null;
 try{return {id:decodeURIComponent(match[1]),market:match[2]};}catch{return null;}
}
export const eventHref=(id,market='brent')=>`#event/${encodeURIComponent(id)}/${market}`;

export function historicalSeries(event,market,cursor){
 if(!['brent','wti'].includes(market)||!validDay(cursor))return {points:[],sources:{}};
 const byDate=new Map(),sources={};
 for(const row of event.reactions.markets[market]||[]){
  for(const p of row.observations||[]){
   if(!validDay(p.date)||p.date>cursor)continue;
   const source=row.sources?.[p.snapshot_id];
   const value=p.value!==null&&p.value!==undefined&&String(p.value).trim()!==''&&!p.missing_code&&source&&Number.isFinite(Number(p.value))?Number(p.value):null;
   const point={date:p.date,value,snapshot_id:p.snapshot_id};
   // Conflicting versions are unavailable, never silently chosen or averaged.
   if(byDate.has(p.date)&&byDate.get(p.date).value!==value)point.value=null;
   byDate.set(p.date,point);
   if(source)sources[p.snapshot_id]=source;
  }
 }
 return {points:[...byDate.values()].sort((a,b)=>a.date.localeCompare(b.date)),sources};
}

export function drawHistoricalChart(svg,points,event,market){
 const width=Math.max(280,Math.round(svg.getBoundingClientRect().width||700)),height=280;
 svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.replaceChildren();
 const add=(tag,attributes,text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attributes))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
 const priced=points.filter(p=>p.value!==null);
 svg.dataset.observedDates=JSON.stringify(priced.map(p=>p.date));
 svg.dataset.market=market;svg.dataset.anchor=event.reactions.anchor;
 if(!priced.length){svg.setAttribute('aria-label','No sourced observations available for this event and market.');add('text',{x:20,y:70},'No sourced prices available');return;}
 const low=Math.min(...priced.map(p=>p.value)),high=Math.max(...priced.map(p=>p.value)),pad=Math.max((high-low)*.15,.5);
 const start=Date.parse(points[0].date),end=Date.parse(points.at(-1).date),L=54,R=20,T=36,B=58;
 const x=d=>L+(Date.parse(d)-start)*(width-L-R)/Math.max(end-start,86400000);
 const y=v=>T+(high+pad-v)*(height-T-B)/(high-low+2*pad);
 for(let i=0;i<4;i++){const v=low-pad+(high-low+2*pad)*i/3;add('line',{x1:L,x2:width-R,y1:y(v),y2:y(v),class:'axis'});add('text',{x:L-7,y:y(v)+4,'text-anchor':'end'},'$'+v.toFixed(0));}
 const anchor=event.reactions.anchor;
 if(Date.parse(anchor)>=start&&Date.parse(anchor)<=end){add('line',{x1:x(anchor),x2:x(anchor),y1:T,y2:height-B,class:'event-line'});add('text',{x:Math.min(x(anchor)+5,width-R),y:18},'Public record');}
 let segment=[];const flush=()=>{if(segment.length)add('polyline',{points:segment.join(' '),class:'line'});segment=[];};
 for(const p of points){if(p.value===null){flush();continue;}segment.push(`${x(p.date)},${y(p.value)}`);const c=add('circle',{cx:x(p.date),cy:y(p.value),r:2.5,class:'inspect-point'});const t=document.createElementNS(svg.namespaceURI,'title');t.textContent=`${p.date}: $${p.value.toFixed(2)} per barrel`;c.append(t);}flush();
 const ticks=[points[0],points[Math.floor((points.length-1)/2)],points.at(-1)];
 [...new Map(ticks.map(p=>[p.date,p])).values()].forEach((p,i,a)=>{const attributes={x:x(p.date),'text-anchor':i===0?'start':i===a.length-1?'end':'middle'};add('text',{...attributes,y:height-28},p.date.slice(5));add('text',{...attributes,y:height-10},p.date.slice(0,4));});
 svg.setAttribute('aria-label',`${market==='brent'?'Brent':'WTI'} historical USD per barrel, ${priced[0].date} to ${priced.at(-1).date}; public record ${anchor}. ${priced.length} sourced observations. Provisional; not a prediction or a GBP paper fill.`);
}
