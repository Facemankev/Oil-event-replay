(()=>{
'use strict';
const el=id=>document.getElementById(id), api=window.MarketRippleResearch;
const catalog=window.MarketRippleEvents;
let datasets=window.MarketRippleData.series.map(s=>({...s}));
let chosen=new Set(datasets.map(s=>s.id));let importNumber=0;
const text=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
function link(label,url){const a=text('a',label);a.href=url;a.target='_blank';a.rel='noopener';return a;}
function markets(){
 const box=el('mr-markets');box.replaceChildren(text('legend','Choose markets'));
 for(const ds of datasets){const label=text('label',' '+ds.name+' ');const input=document.createElement('input');input.type='checkbox';input.checked=chosen.has(ds.id);input.onchange=()=>{input.checked?chosen.add(ds.id):chosen.delete(ds.id);render();};label.prepend(input);box.append(label);}
}
function render(){
 const ev=catalog[+el('mr-event').value];
 el('mr-event-info').replaceChildren(text('span',ev.date+' — '+ev.detail+' '),link('Event source',ev.source));
 const selected=datasets.filter(s=>chosen.has(s.id));
 const result=api.compare(selected,ev.date,+el('mr-window').value);
 el('mr-results').replaceChildren();el('mr-sources').replaceChildren();
 el('mr-method').textContent=result.status==='ok'?`${result.start} → ${result.end}. ${result.method} ${selected.length<2?'Choose another market for a comparison.':''}`:result.message;
 if(result.status!=='ok'){const tr=document.createElement('tr'),td=text('td','No comparison available. '+result.message);td.colSpan=5;tr.append(td);el('mr-results').append(tr);return;}
 for(const r of result.results){
  const tr=document.createElement('tr');
  [r.name,r.startPrice.toFixed(2),r.endPrice.toFixed(2),(r.change>=0?'+':'')+r.change.toFixed(2)+'%',String(r.points)].forEach((v,i)=>{const td=text('td',v);if(i===3)td.className=r.change>=0?'up':'down';tr.append(td);});el('mr-results').append(tr);
  const p=text('p',r.name+' — '+r.unit+'. '+r.basis+' Source: ');
  if(/^https:\/\//.test(r.source.url||''))p.append(link(r.source.name,r.source.url));else p.append(text('span',r.source.name));
  p.append(text('span','. '+r.source.verified+(r.source.blobSha?' Snapshot blob: '+r.source.blobSha+'. Retrieved '+window.MarketRippleData.retrievedAt+'.':'')));
  el('mr-sources').append(p);
 }
}
el('mr-event').replaceChildren(...catalog.map((e,i)=>{const o=text('option',e.name);o.value=i;return o;}));
el('mr-window').value='7';
el('mr-event').onchange=render;el('mr-window').onchange=render;
el('mr-file').onchange=async e=>{
 const file=e.target.files?.[0];if(!file)return;
 try {
  const name=el('mr-asset').value.trim(),source=el('mr-source').value.trim();
  if(!name||!source)throw Error('Enter a market name and its source first.');
  if(file.size>5*1024*1024)throw Error('Choose a CSV smaller than 5 MB.');
  const parsed=api.parseCSV(await file.text());
  const id='import-'+(++importNumber);
  datasets.push({id,name,rows:parsed.rows,unit:'Units supplied in your CSV',basis:'User-supplied prices; confirm currency, daily timing and adjustment method with the publisher.',source:{name:source,verified:'User supplied; not independently verified by Market Ripple.'}});
  chosen.add(id);el('mr-status').textContent=`Loaded ${parsed.rows.length} prices for ${name}. Skipped ${parsed.skipped} missing or invalid rows. Files stay in this browser session.`;markets();render();
 }catch(err){el('mr-status').textContent='Could not import: '+err.message;}finally{e.target.value='';}
};
el('mr-clear').onclick=()=>{datasets=datasets.filter(s=>!s.id.startsWith('import-'));chosen=new Set(datasets.map(s=>s.id));el('mr-status').textContent='Imported markets cleared. Built-in example restored.';markets();render();};
markets();render();
})();
