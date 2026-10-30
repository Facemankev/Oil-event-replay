import {loadJSON, readContext, route} from './context.mjs';
import {categories} from '../matching/engine.mjs';
const $=id=>document.getElementById(id);let data;
function context(){return {event:data.events.find(e=>e.id===$('event').value),market:$('market').value,days:Number($('days').value)};}
function render(){
 const c=context(),e=c.event;$('selected-event').hidden=!e;if(!e)return;
 $('event-title').textContent=e.title;$('event-description').textContent=e.description;
 $('event-times').textContent=`Occurred: ${e.occurred.at||e.occurred.date}. First public: ${e.first_public.at||e.first_public.date||'not established'}. Supporting-publication cutoff: ${e.reactions.anchor||'unknown'}. These dates can differ.`;
 $('event-risk').textContent=e.uncertainty;
 const source=e.evidence[0],a=document.createElement('a');a.textContent=`Supporting source: ${source.publisher}`;
 const u=new URL(source.url);if(u.protocol==='https:'){a.href=u.href;a.rel='noopener noreferrer';}
 $('event-source').replaceChildren(a);
 $('evidence-link').href=route('event-research.html',c);$('matching-link').href=route('matching/',c);
 history.replaceState(null,'',route('app/',c));window.dispatchEvent(new CustomEvent('mr:context',{detail:c}));
}
function choose(preferred){
 const events=data.events.filter(e=>$('category').value==='all'||e.category===$('category').value);
 $('event').replaceChildren(...events.map(e=>new Option(`${e.occurred.date} — ${e.title}`,e.id)));
 if(events.some(e=>e.id===preferred))$('event').value=preferred;render();
}
async function load(){
 $('retry').hidden=true;$('category').disabled=$('event').disabled=true;$('selected-event').hidden=true;
 $('load-status').textContent='Loading the historical event library…';
 try{
  data=await loadJSON('../matching/cohort-catalog.json','Event library');
  if(!data.events.length){$('load-status').textContent='No historical events are available. No examples will be invented.';return;}
  const c=readContext(location.search,data.events);
  $('category').replaceChildren(new Option('All categories','all'),...Object.entries(categories).map(([key,value])=>new Option(value,key)));
  $('market').value=c.market;$('days').value=String(c.days);
  $('load-status').textContent=`${data.events.length} sourced historical events; ${data.price_counts.brent.toLocaleString()} Brent and ${data.price_counts.wti.toLocaleString()} WTI price records. Static historical export, not a current feed. ${c.missing?'The requested event was not found; showing the Harvey example instead.':''}`;
  $('category').disabled=$('event').disabled=false;choose(c.event?.id||'harvey-2017-texas');
 }catch(error){$('load-status').textContent=`Cannot load event research: ${error.message}. No results are shown.`;$('retry').hidden=false;}
}
$('category').onchange=()=>choose();$('event').onchange=render;$('market').onchange=render;$('days').onchange=render;$('retry').onclick=load;
load();
try{
 const status=await loadJSON('data-status.json','Coverage report',15000,d=>d.schemaVersion===1&&d.coverage?.brent&&d.coverage?.wti);
 $('data-freshness').textContent=`Historical coverage ends ${status.coverage.brent.last} for Brent and ${status.coverage.wti.last} for WTI. This snapshot is not a current market feed; later dates are unavailable here.`;
}catch{$('data-freshness').textContent='Coverage metadata is unavailable. Treat the entire export as historical, not as a current price feed.';}
