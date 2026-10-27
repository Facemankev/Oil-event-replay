import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ASSETS,newAccount,buy,close,advance,restore,historicalQuotes,validateQuote} from '../trading/core.mjs';
import {handle} from '../proxy/worker.mjs';
const history=historicalQuotes(readFileSync(new URL('../data/brent-brexit-source.csv',import.meta.url),'utf8'),readFileSync(new URL('../data/gbp-usd-brexit-source.csv',import.meta.url),'utf8'));
const dates=history.map(q=>q.date), q=history[0];
const now=Date.parse('2026-10-23T14:30:30Z');
const live=(changes={})=>({asset:'AAPL',mode:'current',price:100,currency:'USD',timestamp:new Date(now-30000).toISOString(),source:'Test provider',evidence:'fixture: not live market data',gbpPerUnit:.8,fx:{base:'USD',quote:'GBP',rate:.8,timestamp:new Date(now-30000).toISOString(),source:'Test FX',evidence:'fixture'},delaySeconds:0,marketStatus:'open',corporateActions:'current-unadjusted',...changes});
test('authentic source join, direction of FX and missing holiday handling',()=>{
 assert.equal(q.price,48.87);assert.equal(q.gbpPerUnit,.6805);assert.equal(q.date,'2016-05-25');
 assert(!dates.includes('2016-05-30'));assert(!dates.includes('2016-07-04'));
 const a=buy(newAccount(), 'BRENT',5,q);assert.equal(a.cash,45);assert.equal(a.positions[0].units,5/(48.87*.6805));
 assert.equal(a.journal[0].quote.fx.evidence,q.fx.evidence);assert.equal(a.journal[0].assumptions.feeGBP,0);
});
test('£1 fractional allocation, cash limits, penny validation and no shorts',()=>{
 assert.doesNotThrow(()=>newAccount(1.1));
 const a=buy(newAccount(),'BRENT',1,q);assert(a.positions[0].units>0&&a.positions[0].units<1);
 for(const amount of [0,.99,-5,NaN,Infinity,51,1.001])assert.throws(()=>buy(newAccount(),'BRENT',amount,q));
 assert.throws(()=>buy(newAccount(),'FX',5,q));assert.throws(()=>buy(newAccount(),'UNKNOWN',5,q));
});
test('sourced close, forward replay only, realised accounting and conservation',()=>{
 let a=buy(newAccount(),'BRENT',5,q);const first=a.positions[0];
 assert.throws(()=>close(a,first.id,{...q,price:NaN}));
 a=advance(a,dates);assert.equal(a.cursor,dates[1]);assert.throws(()=>close(a,first.id,q));
 a=close(a,first.id,history[1]);const proceeds=first.units*history[1].price*history[1].gbpPerUnit;
 assert.equal(a.positions.length,0);assert.equal(a.cash,45+proceeds);assert.equal(a.realised,proceeds-5);
 assert(Math.abs(a.cash-a.initial-a.realised)<1e-10);assert.throws(()=>advance({...a,cursor:dates.at(-1)},dates));
});
test('reject stale, missing, future, closed and misidentified quotes and FX',()=>{
 validateQuote(live(),'AAPL','current',null,now);
 for(const patch of [{timestamp:new Date(now-121000).toISOString()},{timestamp:new Date(now+31000).toISOString()},{marketStatus:'closed'},{marketStatus:'unknown'},{currency:'GBP'},{source:''},{evidence:''},{delaySeconds:NaN},{delaySeconds:901},{corporateActions:'adjusted'},{fx:{...live().fx,timestamp:new Date(now-121000).toISOString()}},{fx:{...live().fx,base:'GBP'}},{gbpPerUnit:1}])assert.throws(()=>validateQuote(live(patch),'AAPL','current',null,now));
 validateQuote(live({delaySeconds:900,timestamp:new Date(now-900000).toISOString()}),'AAPL','current',null,now);
 assert.throws(()=>validateQuote(live({delaySeconds:900,timestamp:new Date(now-1021000).toISOString()}),'AAPL','current',null,now));
 assert.throws(()=>buy(newAccount(),'AAPL',5,live()));
});
test('cross-day holdings fail closed pending corporate action reconciliation',()=>{
 const a=buy(newAccount(50,'current'),'AAPL',5,live(),'',now);
 assert.throws(()=>close(a,'1',live({timestamp:'2026-10-24T14:30:00Z',fx:{...live().fx,timestamp:'2026-10-24T14:30:00Z'}}),Date.parse('2026-10-24T14:30:30Z')),/corporate-action/);
 assert.equal(close(a,'1',live(),now).cash,50);
});
test('restore replays accounting, ignores forged cash, rejects invalid ledgers',()=>{
 const a=buy(newAccount(),'BRENT',5,q,'<img src=x onerror=alert(1)>');const b={...a,cash:9999,positions:[]};
 assert.deepEqual(restore(b,dates),a);
 for(const bad of [{...a,version:1},{...a,cursor:'2010-01-01'},{...a,journal:[{action:'evil'}]},{...a,journal:[{...a.journal[0],amountGBP:-5}]}])assert.throws(()=>restore(bad,dates));
});
const env={FRONTEND_ORIGIN:'https://example.github.io',DISPLAY_LICENSE_CONFIRMED:'yes',CURRENT_ASSETS:'AAPL,ULVR',TWELVE_DATA_API_KEY:'test-secret-never-return',QUOTE_DELAY_SECONDS:'0',RATE_LIMITER:{limit:async()=>({success:true})}};
const request=(url='https://proxy.example/quote?asset=AAPL',origin=env.FRONTEND_ORIGIN,method='GET')=>new Request(url,{method,headers:{Origin:origin}});
function upstream(modify=x=>x){return async u=>{assert.equal(u.origin,'https://api.twelvedata.com');assert.equal(u.searchParams.get('interval'),'1min');const symbol=u.searchParams.get('symbol');return Response.json(modify({symbol,mic_code:symbol==='ULVR'?'XLON':'XNAS',currency:'USD',timestamp:now/1000-30,close:symbol==='USD/GBP'?'0.8':'100',is_market_open:true}));};}
test('proxy works with genuine provider contract, hides key, normalizes FX',async()=>{
 const r=await handle(request(),env,upstream(),now);assert.equal(r.status,200);const body=await r.text();assert(!body.includes(env.TWELVE_DATA_API_KEY));const q=JSON.parse(body);assert.equal(q.gbpPerUnit,.8);assert.equal(q.price,100);assert.equal(r.headers.get('Cache-Control'),'no-store');validateQuote(q,'AAPL','current',null,now);
});
test('proxy denies unauthorized origins, SSRF, wrong methods, missing setup and quota',async()=>{
 const never=()=>{throw Error('must not fetch');};
 for(const [req,e,status] of [[request(undefined,'https://evil.example'),env,403],[request(undefined,undefined,'POST'),env,405],[request('https://proxy.example/quote?asset=https://evil.example'),env,400],[request('https://proxy.example/quote?asset=AAPL&url=https://evil.example'),env,400],[request(),{...env,DISPLAY_LICENSE_CONFIRMED:'no'},503],[request(),{...env,TWELVE_DATA_API_KEY:''},503],[request(),{...env,RATE_LIMITER:null},503],[request(),{...env,RATE_LIMITER:{limit:async()=>({success:false})}},429]])assert.equal((await handle(req,e,never,now)).status,status);
});
test('proxy rejects stale/closed/malformed upstream and redacts upstream errors',async()=>{
 for(const f of [upstream(x=>({...x,is_market_open:false})),upstream(x=>({...x,currency:'EUR'})),upstream(x=>({...x,timestamp:now/1000-500})),upstream(x=>({...x,close:'NaN'})),async()=>{throw Error(env.TWELVE_DATA_API_KEY);},async()=>Response.json({status:'error',message:env.TWELVE_DATA_API_KEY})]){
 const r=await handle(request(),env,f,now);assert.equal(r.status,503);assert(!(await r.text()).includes(env.TWELVE_DATA_API_KEY));}
});

test('UK quotes normalize pence without treating pence as pounds',async()=>{
 const r=await handle(request('https://proxy.example/quote?asset=ULVR'),env,upstream(x=>({...x,currency:'GBp',close:'4500'})),now);
 assert.equal(r.status,200);const q=await r.json();assert.equal(q.price,45);assert.equal(q.currency,'GBP');assert.equal(q.gbpPerUnit,1);assert.match(q.evidence,/pence divided by 100/);
});
