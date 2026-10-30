import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readContext,route,loadJSON} from '../app/context.mjs';
import {storage} from '../trading/storage.mjs';
const events=[{id:'harvey-2017-texas',title:'Real record'}];
test('deep links accept only catalogue records and supported markets/windows',()=>{
 const c=readContext('?event=harvey-2017-texas&market=wti&days=20&title=private',events);
 assert.equal(c.event,events[0]);assert.equal(c.days,20);assert.equal(c.market,'wti');assert.equal(c.missing,false);
 const bad=readContext('?event=%3Cimg%3E&market=evil&days=999',events);
 assert.equal(bad.event,null);assert.equal(bad.missing,true);assert.equal(bad.market,'brent');assert.equal(bad.days,5);
});
test('application paths preserve a GitHub Pages subdirectory and omit free text',()=>{
 const c={...readContext('?event=harvey-2017-texas&market=wti&days=3',events),title:'private research',password:'not transmitted'};
 const url=route('matching/',c,new URL('https://example.org/project/'));
 assert.equal(url.pathname,'/project/matching/');assert.equal(url.search,'?event=harvey-2017-texas&market=wti&days=3');
 assert.equal(route('paper.html',c,new URL('https://example.org/project/')).pathname,'/project/paper.html');
});
test('denied Safari storage supports an honest memory-only practice session',()=>{
 let warnings=0;const s=storage(()=>{throw new DOMException('Denied','SecurityError');},()=>warnings++);
 assert.equal(s.getItem('account'),null);s.setItem('account','ledger');assert.equal(s.getItem('account'),'ledger');
 s.removeItem('account');assert.equal(s.getItem('account'),null);assert.equal(warnings,1);
});
test('quota failure preserves memory state without deleting the persisted ledger',()=>{
 const persisted=new Map([['account','previous backup']]);
 const s=storage(()=>({getItem:k=>persisted.get(k)??null,setItem:()=>{throw Error('quota');},removeItem:()=>{throw Error('quota');}}));
 assert.equal(s.getItem('account'),'previous backup');s.setItem('account','new in-memory ledger');
 assert.equal(s.getItem('account'),'new in-memory ledger');assert.equal(persisted.get('account'),'previous backup');
 s.removeItem('account');assert.equal(s.getItem('account'),null);
});
test('load failures and unsupported exports do not masquerade as an empty sample',async()=>{
 const original=globalThis.fetch;
 try{
  globalThis.fetch=async()=>new Response('unavailable',{status:503});await assert.rejects(loadJSON('unused','Library'),/HTTP 503/);
  globalThis.fetch=async()=>Response.json({schemaVersion:9,events:[]});await assert.rejects(loadJSON('unused','Library'),/Unsupported/);
  globalThis.fetch=async()=>Response.json({schemaVersion:1,events:[]});assert.deepEqual((await loadJSON('unused','Library')).events,[]);
 }finally{globalThis.fetch=original;}
});
test('slow library requests end with a retryable timeout rather than a permanent spinner',async()=>{
 const original=globalThis.fetch;
 try{globalThis.fetch=async(url,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError'))));
 await assert.rejects(loadJSON('unused','Library',5),/too long/);
 }finally{globalThis.fetch=original;}
});
