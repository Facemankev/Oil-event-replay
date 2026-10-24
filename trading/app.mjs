import {ASSETS,validateQuote,newAccount,buy,close,advance,restore,historicalQuotes} from './core.mjs';
const $=id=>document.getElementById(id), key='market-ripple-practice-v2', oldKey='market-ripple-practice-v1';
const money=n=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP'}).format(n);
const message=s=>{$('message').textContent=s;};
let account, history=[], dates=[], quotes={}, generation=0, busy=false;
const say=(parent,text,tag='p')=>{const el=document.createElement(tag);el.textContent=text;parent.append(el);return el;};
function download(value,name){const url=URL.createObjectURL(new Blob([value],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function commit(next){localStorage.setItem(key,JSON.stringify(next));account=next;render();}
function available(asset){try{return validateQuote(quotes[asset],asset,account.mode,account.cursor);}catch{return null;}}
function label(q){if(q.mode==='historical')return `${q.price.toFixed(4)} ${q.currency} per reference unit · ${q.source} · Observation date: ${q.date}; intraday timestamp unavailable. Historical daily data, not live. Market: historical observation. FX: 1 USD = £${q.gbpPerUnit.toFixed(6)} (${q.fx.source}, observation date ${q.fx.date}). Both are treated as available at replay day end; original publication time unknown. Evidence: ${q.evidence}; ${q.fx.evidence}`;return `${q.price.toFixed(4)} ${q.currency} per unit · ${q.source} · Quote: ${q.timestamp} · Delay: ${q.mode==='historical'?'historical daily data, not live':q.delaySeconds+' seconds'} · Market: ${q.marketStatus}. FX: 1 ${q.currency} = £${q.gbpPerUnit.toFixed(6)} (${q.fx.source}, ${q.fx.timestamp}). Evidence: ${q.evidence}; ${q.fx.evidence}`;}
function render(){
 $('welcome').hidden=!!account;$('account').hidden=!account;$('backup').disabled=!account;$('reset').disabled=!account;if(!account)return;
 $('modeTitle').textContent=account.mode==='historical'?'Historical practice — not today’s market':'Current paper trading';
 $('clock').textContent=account.mode==='historical'?`Replay day: ${account.cursor}. Only move forward.`:'Refresh to retrieve provider quotes. Trades require an open market and fresh price and FX data.';
 $('method').textContent=account.mode==='historical'?'Brent is a spot oil benchmark, not shares or a purchasable fund. This is an unleveraged fractional oil-price exercise. Daily price and FX observations are treated as available at day end; original publication times are unknown. You already know this period’s history, so this is not an unbiased strategy backtest. Missing days and holidays are skipped; no prices are filled in.':'Current mode supports intraday practice only. Holdings across trading dates require corporate-action reconciliation and cannot be closed here. No split or dividend adjustments are guessed.';
 $('next').hidden=account.mode!=='historical';$('next').disabled=busy||account.cursor===dates.at(-1);
 const asset=$('asset').value,q=available(asset);
 $('quote').textContent=q?label(q):explanation(asset);
 $('buy').disabled=busy||!q;$('refresh').disabled=busy;
 let value=0, missing=false;const container=$('positions');container.replaceChildren();
 for(const p of account.positions){const mark=available(p.asset),div=document.createElement('div');div.className='position';say(div,`${ASSETS[p.asset].name} · ${p.units.toFixed(8)} fractional units · Cost ${money(p.cost)}`,'h3');
 let canClose=!!mark;if(mark){const v=p.units*mark.price*mark.gbpPerUnit;value+=v;say(div,`Value ${money(v)} · Gain/loss ${money(v-p.cost)}. ${label(mark)}`);
 if(account.mode==='current'&&p.entry.timestamp.slice(0,10)!==mark.timestamp.slice(0,10)){canClose=false;say(div,'Corporate-action reconciliation required before closing: this position crosses trading dates.');missing=true;}}
 else{missing=true;say(div,'Current valuation unavailable. Refresh for a sourced price; previous prices are not used to close.');}
 const button=say(div,'Close virtually','button');button.disabled=busy||!canClose;button.onclick=()=>run(()=>commit(close(account,p.id,quotes[p.asset])));container.append(div);}
 if(!account.positions.length)say(container,'No open positions yet.');
 $('summary').textContent=`Virtual cash ${money(account.cash)} · Positions ${missing?'unavailable':money(value)} · Account total ${missing?'unavailable':money(account.cash+value)} · Closed profit/loss ${money(account.realised)}`;
 $('journal').replaceChildren();for(const j of account.journal.slice().reverse()){say($('journal'),`${j.action==='buy'?'Bought':'Closed'} ${ASSETS[j.asset].name} · ${money(j.amountGBP)} · ${j.orderTimestamp}${j.replayDate?' · Replay '+j.replayDate:''} · ${j.reason||''}`);}
}
function explanation(asset){
 if(asset==='FX')return 'FX is used only to convert your virtual pounds. Speculative currency trading is unavailable in beginner mode.';
 if(account.mode==='historical'&&asset!=='BRENT')return 'Historical practice currently supports Brent only. Apple’s secondary history has unresolved reuse rights; UK shares, ETFs and gold do not have licensed built-in histories. No substitute price will be invented.';
 if(asset==='BRENT')return 'No current spot-oil provider is configured. Oil benchmarks are not purchasable shares; futures and derivatives are excluded.';
 return window.MARKET_RIPPLE_PRICE_PROXY?'No usable quote: market closed, provider unavailable, stale data, or asset not licensed. Refresh to try again.':'Current quotes are unavailable. The owner must deploy and configure a licensed price provider. Historical practice works without setup.';
}
function endpoint(){const raw=window.MARKET_RIPPLE_PRICE_PROXY;if(!raw)throw Error('Current provider is not configured. Choose Historical practice.');const u=new URL(raw);if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash)throw Error('Invalid provider URL. An HTTPS price proxy is required.');return u;}
async function refresh(){
 const ticket=++generation;quotes={};busy=true;render();
 try{
 if(account.mode==='historical'){const q=history.find(q=>q.date===account.cursor);if(q)quotes.BRENT=q;}
 else {const assets=new Set([$ ('asset').value,...account.positions.map(p=>p.asset)]);const results=await Promise.allSettled([...assets].filter(a=>ASSETS[a].symbol).map(async asset=>{const u=endpoint();u.searchParams.set('asset',asset);const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);try{const res=await fetch(u,{signal:controller.signal,credentials:'omit',cache:'no-store',redirect:'error'});if(!res.ok)throw Error('Provider unavailable.');const q=await res.json();validateQuote(q,asset,'current',null);return [asset,q];}finally{clearTimeout(timer);}}));
 if(ticket!==generation)return;for(const r of results)if(r.status==='fulfilled')quotes[r.value[0]]=r.value[1];}
 }catch(e){message(e.message);}finally{if(ticket===generation){busy=false;render();}}
}
function run(fn){try{fn();}catch(e){message(e.message);render();}}
function checkedRestore(raw){const a=restore(raw,dates);if(a.mode==='historical')for(const j of a.journal){const expected=history.find(q=>q.date===j.replayDate);if(JSON.stringify(j.quote)!==JSON.stringify(expected))throw Error('Historical backup quote differs from the committed source data.');}return a;}
for(const [id,a] of Object.entries(ASSETS)){const option=document.createElement('option');option.value=id;option.textContent=a.name;$('asset').append(option);}
$('start').onclick=()=>run(()=>{commit(newAccount(Number($('initial').value),$('mode').value,dates[0]));refresh();});
$('buy').onclick=()=>run(()=>{commit(buy(account,$('asset').value,Number($('amount').value),quotes[$('asset').value],$('reason').value));message('Virtual buy recorded. Move forward or refresh to see a sourced valuation.');});
$('next').onclick=()=>run(()=>{commit(advance(account,dates));refresh();});
$('asset').onchange=()=>refresh();$('refresh').onclick=()=>refresh();
$('backup').onclick=()=>account&&download(JSON.stringify(account,null,2),'market-ripple-paper-v2.json');
$('restore').onchange=async e=>{try{const file=e.target.files[0];if(!file||file.size>5000000)throw Error('Backup must be smaller than 5 MB.');const a=checkedRestore(JSON.parse(await file.text()));if(!confirm('Replace this practice account with the backup?'))return;commit(a);await refresh();message('Backup restored. Quotes refreshed from the current data source.');}catch(e){message('Restore failed: '+e.message);}finally{$('restore').value='';}};
$('reset').onclick=()=>run(()=>{if(confirm('Delete the version 2 account? Export a backup first.')){localStorage.removeItem(key);account=null;quotes={};generation++;busy=false;render();}});
$('legacyBackup').onclick=()=>download(localStorage.getItem(oldKey),'market-ripple-legacy-manual.json');
try{
 $('start').disabled=true;
 const responses=await Promise.all(['data/brent-brexit-source.csv','data/gbp-usd-brexit-source.csv'].map(async url=>{const r=await fetch(url);if(!r.ok)throw Error('Historical source data unavailable.');return r.text();}));
 history=historicalQuotes(...responses);dates=history.map(q=>q.date);if(!dates.length)throw Error('No matching price and FX observations.');
 $('legacy').hidden=$('legacyBackup').hidden=!localStorage.getItem(oldKey);
 const saved=localStorage.getItem(key);if(saved){try{account=checkedRestore(JSON.parse(saved));}catch(e){message('Saved account could not be loaded: '+e.message+' Your stored data has not been deleted.');}}
 $('start').disabled=false;render();if(account)await refresh();
}catch(e){message('Cannot start: '+e.message);}
// Quotes can expire while a tab is idle. Recheck controls, and always validate on trade.
setInterval(()=>{if(account&&!busy)render();},10000);
