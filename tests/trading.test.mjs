import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ASSETS,newAccount,buy,close,advance,restore,historicalQuotes,validateQuote} from '../trading/core.mjs';
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
