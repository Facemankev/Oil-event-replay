const $=id=>document.getElementById(id);
const add=(parent,tag,value)=>{const n=document.createElement(tag);n.textContent=value;parent.append(n);return n;};
let data;
const temporal=t=>t.precision==='unknown'?'Unknown':(t.at||`${t.date} (clock unknown)`)+(t.timezone?` [${t.timezone}]`:' [timezone unknown]');
function choose(){
 const selected=$('category').value;
 const events=data.events.filter(e=>selected==='all'||e.category===selected);
 $('event').replaceChildren();
 for(const event of events){const o=add($('event'),'option',`${event.occurred.date} — ${event.title}`);o.value=event.id;}
 render();
}
function render(){
 const event=data.events.find(e=>e.id===$('event').value);
 const comparison=data.comparisons.find(c=>c.event_id===event.id);
 $('title').textContent=event.title;
 $('description').textContent=event.description;
 $('geography').textContent=`Region: ${event.geography}. Category: ${event.category.replaceAll('_',' ')}.`;
 $('occurrence').textContent='Occurred: '+temporal(event.occurred)+(event.occurred.approximate?' (contemporaneous approximate estimate)':'');
 $('first-public').textContent=event.first_public.status==='not_established'?'First-public timing: not established. Do not substitute the occurrence date.':'Earliest supporting publication located: '+temporal(event.first_public)+'. Not certified as globally first.';
 $('alignment').textContent=comparison.publication_anchor_date?`Comparison publication date: ${comparison.publication_anchor_date}. ${comparison.alignment_note}. Calendar difference from occurrence date label: ${comparison.evidence_lag_calendar_days} days.`:'No comparison: publication timing is unknown.';
 $('uncertainty').textContent=event.uncertainty;
 $('confidence').textContent='Descriptive research only. This event/price pairing is not eligible for a point-in-time backtest. '+(comparison.status==='ok'?'Both windows have the required shared observations.':comparison.status.replaceAll('_',' '));
 $('results').replaceChildren();$('observations').replaceChildren();
 for(const s of comparison.series){const tr=document.createElement('tr');for(const v of [s.series.toUpperCase(),`${s.baseline} (${s.baseline_date})`,`${s.end} (${s.end_date})`,s.absolute_change,s.change_percent===null?'Undefined for nonpositive baseline':s.change_percent+'%'])add(tr,'td',v);$('results').append(tr);}
 if(comparison.series.length===2){
  const [brent,wti]=comparison.series;
  for(const side of ['pre','post'])for(let i=0;i<brent[side+'_rows'].length;i++){
   const tr=document.createElement('tr');for(const v of [side==='pre'?'Before publication':'After publication',brent[side+'_rows'][i][0],brent[side+'_rows'][i][1],wti[side+'_rows'][i][1]])add(tr,'td',v);$('observations').append(tr);
  }
 }
 $('price-evidence').textContent=JSON.stringify({methodology:comparison.methodology,calendar:comparison.calendar,prices:comparison.price_sources},null,2);
 $('evidence').replaceChildren();
 for(const source of event.evidence){
  const div=document.createElement('div');
  add(div,'p',`${source.publisher}. ${source.stable_reference}. Evidence quality: ${source.quality.replaceAll('_',' ')}.`);
  add(div,'p','Published: '+temporal(source.published)+'. Checked '+source.checked_on+'.');
  add(div,'p',source.summary);
  try{const u=new URL(source.url);if(u.protocol==='https:'&&!u.username&&!u.password){const a=add(div,'a','Read the supporting source');a.href=u.href;a.rel='noopener';}}
  catch{}
  add(div,'p','Curated evidence-card SHA-256: '+source.sha256);
  $('evidence').append(div);
 }
}
try{
 const response=await fetch('data/world-event-research.json');if(!response.ok)throw Error('Research export unavailable');
 data=await response.json();if(data.schemaVersion!==1||!Array.isArray(data.events)||!Array.isArray(data.comparisons))throw Error('Unsupported export');
 for(const category of [...new Set(data.events.map(e=>e.category))].sort()){const option=add($('category'),'option',category.replaceAll('_',' '));option.value=category;}
 $('status').textContent=`${data.summary.events} events, ${data.summary.successful_comparisons} completed two-benchmark comparisons. ${data.summary.first_public_not_established} first-public times remain unestablished; ${data.summary.minute_public_evidence} supporting publications have minute stamps.`;
 $('event').disabled=false;$('category').onchange=choose;$('event').onchange=render;choose();
}catch(error){$('status').textContent='Cannot load event research: '+error.message+'. The existing dashboard remains available via the link above.';}
