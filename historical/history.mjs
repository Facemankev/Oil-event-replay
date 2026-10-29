const $=id=>document.getElementById(id);
let catalog;
const add=(parent,tag,text)=>{const n=document.createElement(tag);n.textContent=text;parent.append(n);return n;};
function render(event){
 event?.preventDefault();
 if(!catalog)return;
 const from=$('from').value,to=$('to').value;
 $('prices').replaceChildren();$('provenance').replaceChildren();$('limit').textContent='';
 if(!from||!to||from>to){$('status').textContent='Choose valid dates with the start on or before the end.';return;}
 const series=catalog.series.find(s=>s.series===$('series').value);
 const rows=series.observations.filter(r=>r.date>=from&&r.date<=to);
 const numeric=rows.filter(r=>r.value!==null);
 $('status').textContent=`${series.name}: ${numeric.length} numeric observations and ${rows.length-numeric.length} explicit missing observations in ${from} → ${to}. Export coverage: ${series.coverage.first} → ${series.coverage.last} (${series.coverage.count} prices).`;
 for(const [id,source] of Object.entries(series.sources)){
  add($('provenance'),'p',`Source kind: ${source.source_kind==='eia'?'Primary EIA API retrieval':'Secondary EIA-derived seed; primary reconciliation pending'}. Retrieved by importer: ${source.retrieved_at}. Original source retrieval date: ${source.source_retrieved_on||'not supplied'}. Snapshot ${source.snapshot_id||id}. SHA-256 ${source.sha256}. Revision: ${source.source_revision}.`);
  if(source.source_url.startsWith('https://')){const a=add($('provenance'),'a','Source snapshot location');a.href=source.source_url;a.rel='noopener';}
 }
 for(const r of rows.slice(0,500)){
  const tr=document.createElement('tr');add(tr,'td',r.date);add(tr,'td',r.value===null?`Missing (${r.missing_code})`:r.value);add(tr,'td',series.sources[r.snapshot_id].snapshot_id.slice(0,12));$('prices').append(tr);
 }
 if(!rows.length){const tr=document.createElement('tr');const td=add(tr,'td','No reported observations in this range.');td.colSpan=3;$('prices').append(tr);}
 if(rows.length>500)$('limit').textContent='Showing the first 500 observations. Narrow the dates or download the full export; the counts above include the full selected range.';
}
$('range').addEventListener('submit',render);
try{
 const res=await fetch('data/historical/prices.json');if(!res.ok)throw Error('Static export is unavailable');
 catalog=await res.json();if(catalog.schemaVersion!==1||!Array.isArray(catalog.series))throw Error('Unsupported export');
 $('query').disabled=false;render();
}catch(e){$('status').textContent='Could not load historical data: '+e.message+'. The original research lab is still available via the link above.';}
