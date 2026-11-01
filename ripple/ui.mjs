import {loadJSON} from '../app/context.mjs';
import {storage} from '../trading/storage.mjs';
import {newRun,restoreRun,transact,current,quoteAt,observedQuotes,gbpQuote,validatePlan} from './model.mjs';
import {evidenceAt} from './paths.mjs';
import {drawChart} from './chart.mjs';
const $=id=>document.getElementById(id),key='market-ripple-ripple-practice-v1';
const money=x=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP'}).format(x);
const day=d=>new Date(d+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
const percent=n=>n===null?'Unavailable':`${n>0?'+':''}${n.toFixed(2)}%`;
const node=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
let data,catalog,run,rawBackup,inspection=0,loaded=false,locked=false;
const store=storage(()=>window.localStorage,()=>{$('storage').hidden=false;$('storage').textContent='Browser storage unavailable: memory-only practice. Export before closing or reloading.';});
function safeLink(label,url){const a=node('a',label),u=new URL(url);if(u.protocol!=='https:'||u.username||u.password)throw Error('Unsupported source link');a.href=u.href;a.rel='noopener noreferrer';return a;}
function screen(){const decision=location.hash==='#decision';$('screen-opportunities').hidden=!loaded||decision;$('screen-decision').hidden=!loaded||!decision;
 $('nav-opportunities').setAttribute('aria-current',decision?'false':'page');$('nav-decision').setAttribute('aria-current',decision?'page':'false');if(loaded&&decision)chart();}
function contextSources(evidence){const event=catalog.events.find(e=>e.id===data.event_id);return [...event.evidence.map(s=>({id:s.id,publisher:s.publisher,url:s.url,summary:s.summary,published:s.published.at||s.published.date})),
 ...[...data.sources.context,...data.sources.updates].filter(s=>evidence.source_ids.includes(s.id)).map(s=>({...s,published:s.published_day}))];}
function evidenceView(container,evidence){
 container.replaceChildren();
 container.append(node('p',`${evidence.cohort_count} non-overlapping five-day comparisons: median ${percent(evidence.cohort_median)}; ${evidence.cohort_outcomes.positive} positive, ${evidence.cohort_outcomes.negative} negative, ${evidence.cohort_outcomes.flat} flat. This is a selected sample, not future odds.`));
 const p=evidence.conditional;container.append(node('p',`${p.count} usable full historical ${p.count===1?'path':'paths'} at Brent observation step ${p.phase}. Over the following ${p.ahead} historical steps: median ${percent(p.median_percent)}, range ${percent(p.minimum)} to ${percent(p.maximum)}. ${p.reversed} rose then fell. ${p.reversal_supported?'Fixed stability gates passed; still not a prediction.':'No sufficiently supported reversal pattern.'}`));
 container.append(node('p','Historical paths are USD Brent reporting observations, not your GBP portfolio. They exclude self/future events and overlapping windows. GBP practice requires exact price/FX dates. Sparse paths and current price vintages cannot establish a fully point-in-time backtest.'));
 for(const source of contextSources(evidence)){const line=node('p');line.append(safeLink(source.publisher,source.url),document.createTextNode(` — published ${source.published}. ${source.summary}`));container.append(line);}
 container.append(node('p',evidence.limitations),node('p','Supported path prompts require at least eight complete, non-overlapping comparisons, primary/as-of evidence and dispersion/stability checks. These exploratory rules are not calibrated probabilities.'));
}
function chart(){
 if(!data)return;const cursor=run?.account.cursor||data.start,quotes=observedQuotes(data,cursor),position=run?.account.positions[0],entry=position?run.entries[position.id]:null;
 inspection=Math.min(inspection,quotes.length-1);$('inspect').max=String(quotes.length-1);$('inspect').value=String(inspection);
 const q=quotes[inspection];$('inspection').textContent=q?`${day(q.date)}: ${money(gbpQuote(q))}. Inspection only; trades use the current replay observation.`:'No available observation.';
 drawChart($('price-chart'),quotes,catalog.events.find(e=>e.id===data.event_id),entry,inspection);
 $('price-rows').replaceChildren();for(const q of quotes){const tr=node('tr');[q.date,q.price.toFixed(2),q.gbpPerUnit.toFixed(4),gbpQuote(q).toFixed(6)].forEach(value=>tr.append(node('td',value)));$('price-rows').append(tr);}
}
function render(){
 if(!loaded)return;
 const cursor=run?.account.cursor||data.start,evidence=evidenceAt(data,catalog,cursor),event=catalog.events.find(e=>e.id===data.event_id);
 $('opportunity-state').textContent=evidence.point_in_time_safe&&evidence.conditional.buy_supported?'One paper-research candidate meets the fixed comparison gates. No real-trade recommendation.':'No sufficiently supported opportunities. Explore one paper scenario.';
 $('freshness').textContent=`Landfall: 25 Aug 2017. Replay as of ${day(cursor)}.`;
 $('replay-date').textContent=`Historical replay: ${day(cursor)} (simulated day-end)`;
 evidenceView($('opportunity-evidence'),evidence);evidenceView($('decision-evidence'),evidence);
 const quote=quoteAt(data,cursor);$('price').textContent=money(gbpQuote(quote));
 $('price-sources').replaceChildren();for(const s of Object.values(data.price_sources)){$('price-sources').append(safeLink('Existing Brent source snapshot',s.source_url),node('p',`SHA-256 ${s.sha256}; source kind ${s.source_kind}.`));}
 $('price-sources').append(safeLink('Pinned FX snapshot',data.sources.fx.url),node('p',data.sources.fx.method));
 const a=run?current(run,data,catalog):null,position=a?.position;
 $('value-label').textContent=position?'Virtual position value':'Virtual cash';$('position-value').textContent=money(position?position.units*gbpQuote(quote):(run?.account.cash??50));
 $('cash').textContent=run?`Cash ${money(run.account.cash)}; realised ${money(run.account.realised)}`:'Saved practice needs verification';
 $('action-title').textContent=a?.prompt.action||'No Action';$('action-reason').textContent=a?.prompt.reason||'The saved ledger is locked until you export, restore or explicitly reset it.';
 $('action-evidence').textContent=`${evidence.evidence} evidence`;$('action-risk').textContent='Principal risk: '+evidence.principal_risk;
 $('position-summary').textContent=position?`Entry ${day(a.entry.entry_date)} at ${money(a.entry.entry_price_gbp)}. Plan: ${a.entry.exit_criteria.horizon} steps, −${a.entry.exit_criteria.loss_percent}% / +${a.entry.exit_criteria.profit_percent}%; review only.`:'All funds and units are virtual. This unleveraged spot reference is not a purchasable security.';
 $('entry-controls').hidden=!!position;$('buy').disabled=locked||!run||!quote;$('sell').hidden=!position;$('sell').disabled=locked||!position||!quote;
 $('next').disabled=locked||!run||cursor===data.quotes[data.quotes.length-1].date;
 $('next-note').textContent=cursor===data.quotes[data.quotes.length-1].date?'End of supplied observations. No later prices invented.':'Manual replay; no live monitoring.';
 $('accept-hold').hidden=a?.prompt.action!=='Hold';
 const review=run?.suggestions.find(s=>s.id===run.current_review),responded=review?.responses.some(r=>['dismissed','accepted_hold'].includes(r.choice));
 $('dismiss').disabled=locked||!review||responded;$('accept-hold').disabled=locked||responded;
 $('review-response').textContent=review?.responses.length?'Recorded: '+review.responses[review.responses.length-1].choice.replaceAll('_',' '):'';
 $('backup').disabled=!run&&!rawBackup;$('reset').disabled=!run&&!rawBackup;
 $('review-log').replaceChildren();for(const review of run?.suggestions.slice().reverse()||[]){const tr=node('tr');
  const outcome=review.outcome?`${money(review.outcome.realised_gbp)} realised; known ${review.outcome.known_at}`:'Not yet observed';
  [review.as_of,`${review.action}: ${review.reason}`,review.responses.map(r=>`${r.choice.replaceAll('_',' ')} (${r.recorded_at})`).join('; ')||'Pending',outcome].forEach(value=>tr.append(node('td',value)));$('review-log').append(tr);}
 chart();screen();
}
function commit(next){const text=JSON.stringify(next);store.setItem(key,text);rawBackup=text;run=next;inspection=observedQuotes(data,run.account.cursor).length-1;render();}
function act(kind,extra={}){try{if(locked||!run)throw Error('Saved practice is locked');commit(transact(run,{kind,...extra,before:run.account.cursor,at:new Date().toISOString()},data,catalog));$('status').textContent='';}catch(error){$('status').textContent=error.message;}}
function download(){const value=run?JSON.stringify(run,null,2):rawBackup;if(!value)return;const url=URL.createObjectURL(new Blob([value],{type:'application/json'})),a=node('a');a.href=url;a.download='market-ripple-harvey-practice-v1.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function load(){
 loaded=false;locked=false;run=null;$('retry').hidden=true;$('status').textContent='Loading sourced replay data…';screen();
 try{
  [data,catalog]=await Promise.all([loadJSON('data.json','Paper replay',15000,d=>d.schemaVersion===1&&Array.isArray(d.quotes)),loadJSON('../matching/cohort-catalog.json','Historical catalogue')]);
  if(!data.quotes.length||!quoteAt(data,data.start))throw Error('No matching sourced price/FX observations. No practice prices will be invented.');
  $('ripples').replaceChildren();for(const path of data.sources.ripple_paths){const block=node('div'),title=node('p',path.id==='production'?'Possible supply ripple':'Possible refining and demand ripple');title.className='path-title';block.append(title);const list=node('ol');list.className='ripple-flow';
   path.stages.forEach((stage,i)=>{const item=node('li'),order=node('span',['1st','2nd','3rd'][i]+' order');order.className='order';item.append(order,document.createTextNode(stage));list.append(item);});block.append(list);$('ripples').append(block);}
  rawBackup=store.getItem(key);
  if(rawBackup){try{run=restoreRun(JSON.parse(rawBackup),data,catalog);}catch(error){locked=true;$('status').textContent='Saved practice could not be verified: '+error.message+'. Export it before restoring or resetting.';}}
  else{run=newRun(data,catalog);commit(run);}
  loaded=true;if(!locked)$('status').textContent='';inspection=observedQuotes(data,run?.account.cursor||data.start).length-1;render();
 }catch(error){loaded=false;$('status').textContent='Cannot load this replay: '+error.message;$('retry').hidden=false;screen();}
}
$('next').onclick=()=>act('advance');$('dismiss').onclick=()=>act('respond',{choice:'dismissed'});$('accept-hold').onclick=()=>act('respond',{choice:'accepted_hold'});
$('buy').onclick=()=>{try{const plan=validatePlan({horizon:Number($('horizon').value),loss_percent:Number($('loss').value),profit_percent:Number($('profit').value)}),amount=Number($('amount').value);const q=quoteAt(data,run.account.cursor);
 if(!Number.isFinite(amount)||amount<1||Math.abs(Math.round(amount*100)-amount*100)>1e-7||amount>run.account.cash)throw Error('Choose a virtual amount of £1 or more, in pennies, within your cash.');
 if(confirm(`Confirm ${money(amount)} VIRTUAL buy on ${run.account.cursor} at GBP reference ${gbpQuote(q).toFixed(6)}? Evidence is ${current(run,data,catalog).evidence.evidence}. Review after ${plan.horizon} priced steps, −${plan.loss_percent}% / +${plan.profit_percent}%. Zero fees/spread/slippage assumed. Manual educational choice; not a recommended or real trade.`))act('buy',{amount,plan});else act('respond',{choice:'cancelled_buy'});
 }catch(error){$('status').textContent=error.message;}};
$('amount').oninput=()=>{$('buy').textContent=`Try a ${money(Number($('amount').value)||0)} virtual buy`;};
$('sell').onclick=()=>{if(confirm(`Confirm VIRTUAL close at the sourced GBP reference on ${run.account.cursor}? No real order is placed.`))act('close');else act('respond',{choice:'cancelled_sell'});};
$('inspect').oninput=()=>{inspection=Number($('inspect').value);chart();};$('backup').onclick=download;
$('restore').onchange=async event=>{try{const file=event.target.files[0];if(!file||file.size>2000000)throw Error('Choose a replay backup smaller than 2 MB');const restored=restoreRun(JSON.parse(await file.text()),data,catalog);if(!confirm('Replace this replay practice with the verified backup? Export the current practice first.'))return;locked=false;commit(restored);$('status').textContent='Verified backup restored.';}catch(error){$('status').textContent='Restore rejected: '+error.message;}finally{event.target.value='';}};
$('reset').onclick=()=>{if(confirm('Reset only this Harvey replay? Export first. Earlier paper accounts are separate.')){locked=false;commit(newRun(data,catalog));$('status').textContent='This replay was reset. No earlier account was changed.';}};
$('retry').onclick=load;window.addEventListener('hashchange',screen);window.addEventListener('resize',()=>{if(loaded)chart();});
load();
