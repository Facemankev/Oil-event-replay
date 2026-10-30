import {loadJSON,readContext,route} from './context.mjs';
const panel=document.getElementById('research-context');
try{
 const data=await loadJSON('matching/cohort-catalog.json','Research context');
 const c=readContext(location.search,data.events);
 window.dispatchEvent(new CustomEvent('mr:context',{detail:c}));
 if(c.missing){panel.textContent='The requested research event was not found. No event context was attached to this independent exercise.';}
 else if(c.event){
  const p=document.createElement('p');p.textContent=`Research reference: ${c.event.title} · ${c.market.toUpperCase()} · ${c.days} observation days. This is a separate 2016 Brent exercise, not a simulation of this event. WTI practice is unavailable. Research does not initiate a trade.`;
  const a=document.createElement('a');a.textContent='Return to this historical comparison';a.href=route('matching/',c);
  const button=document.createElement('button');button.className='mr-btn';button.textContent='Copy research reference to my practice note';
  button.onclick=()=>{document.getElementById('reason').value=`Research only: ${c.event.title} [${c.event.id}], ${c.market.toUpperCase()}, ${c.days} observation days. Independent 2016 Brent practice; not a prediction.`;button.textContent='Reference copied — no virtual order placed';};
  panel.replaceChildren(p,a,button);
 }else panel.textContent='Independent historical practice: 2016 Brent and GBP only. No selected-event return or WTI trade is simulated.';
}catch{panel.textContent='Research context is unavailable. The independent practice account can still load from its own price and FX sources.';}
