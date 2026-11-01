import {gbpQuote} from './model.mjs';
export function drawChart(svg,quotes,event,entry,inspection){
 const width=Math.max(280,Math.round(svg.getBoundingClientRect().width||700)),height=width<640?280:300;
 const L=54,R=20,T=42,B=64,W=width,H=height;
 svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.replaceChildren();
 const ns='http://www.w3.org/2000/svg',add=(tag,attributes={},text)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attributes))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
 if(!quotes.length){svg.setAttribute('aria-label','No sourced price observations available');return;}
 const values=quotes.map(gbpQuote),lo=Math.min(...values),hi=Math.max(...values),pad=Math.max((hi-lo)*.15,.25),low=lo-pad,high=hi+pad;
 const x=i=>L+i*(W-L-R)/Math.max(quotes.length-1,1),y=v=>T+(high-v)*(H-T-B)/(high-low);
 const eventIndex=quotes.findIndex(q=>q.date>event.reactions.anchor),current=quotes[quotes.length-1];
 if(eventIndex>0)add('rect',{x:x(eventIndex-1),y:T,width:x(eventIndex)-x(eventIndex-1),height:H-B-T,class:'event-band'});
 for(let i=0;i<4;i++){const v=low+(high-low)*i/3;add('line',{x1:L,x2:W-R,y1:y(v),y2:y(v),class:'axis'});add('text',{x:L-8,y:y(v)+4,'text-anchor':'end'},'£'+v.toFixed(2));}
 if(eventIndex>=0){add('line',{x1:x(eventIndex),x2:x(eventIndex),y1:T,y2:H-B,class:'event-line'});add('text',{x:Math.min(W-R,x(eventIndex)+6),y:16,'text-anchor':eventIndex>quotes.length*.6?'end':'start'},width<640?'Bulletin: 26 Aug':'Landfall bulletin: 26 Aug UTC');}
 add('polyline',{points:values.map((v,i)=>`${x(i)},${y(v)}`).join(' '),class:'line'});
 const ticks=[0,Math.floor((quotes.length-1)/2),quotes.length-1];if(width>=640)ticks.push(eventIndex,Math.floor((quotes.length-1)*.75));
 [...new Set(ticks.filter(i=>i>=0))].sort((a,b)=>a-b).forEach((i,k,array)=>{const anchor=k===0?'start':k===array.length-1?'end':'middle';const t=i-eventIndex;
  add('text',{x:x(i),y:H-30,'text-anchor':anchor},eventIndex<0?'Before bulletin':`T${t===0?'0':t>0?'+'+t:'−'+Math.abs(t)}`);
  add('text',{x:x(i),y:H-10,'text-anchor':anchor},new Date(quotes[i].date+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}));});
 if(entry){const i=quotes.findIndex(q=>q.date===entry.entry_date);if(i>=0){const c=add('circle',{cx:x(i),cy:y(values[i]),r:6,class:'entry','data-entry-date':entry.entry_date});const title=document.createElementNS(ns,'title');title.textContent=`Paper entry ${entry.entry_date}: £${entry.entry_price_gbp.toFixed(6)}`;c.append(title);}}
 add('circle',{cx:x(quotes.length-1),cy:y(values[values.length-1]),r:5,class:'current','data-current-date':current.date});
 const index=Math.min(Math.max(inspection,0),quotes.length-1);add('circle',{cx:x(index),cy:y(values[index]),r:3,class:'inspect-point','data-inspected-date':quotes[index].date});
 svg.dataset.observedDates=JSON.stringify(quotes.map(q=>q.date));
 svg.setAttribute('aria-label',`GBP-converted Brent reference through ${current.date}: £${gbpQuote(current).toFixed(4)}. Only ${quotes.length} already observed price/FX pairs. ${entry?'Paper entry '+entry.entry_date+'. ':''}No future observations.`);
}
