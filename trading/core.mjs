// Pure accounting and quote policy, shared by the static app and tests.
export const ASSETS = Object.freeze({
  BRENT: {name:'Brent oil price practice', currency:'USD', historical:true, reference:true},
  AAPL: {name:'Apple shares', currency:'USD', symbol:'AAPL', mic:'XNAS'},
  SPY: {name:'US shares ETF (SPY)', currency:'USD', symbol:'SPY', mic:'ARCX'},
  GLD: {name:'Gold ETF (GLD)', currency:'USD', symbol:'GLD', mic:'ARCX'},
  ULVR: {name:'UK shares (Unilever)', currency:'GBP', symbol:'ULVR', mic:'XLON'},
  FX: {name:'Pound / US dollar', currency:'USD', observation:true}
});
export const ASSUMPTIONS = Object.freeze({feeGBP:0, spreadBps:0, slippageBps:0, fractional:true, description:'Zero fees, spread and slippage; educational reference fills, not executable broker prices. No dividends or interest.'});
const positive = n => typeof n === 'number' && Number.isFinite(n) && n > 0;
const fail = message => {throw Error(message);};
export const clone = a => JSON.parse(JSON.stringify(a));
export function validateQuote(q, asset, mode, cursor, now=Date.now()) {
  const a=ASSETS[asset];
  if(!a || a.observation) fail('This market is for observation only; no currency speculation in beginner mode.');
  if(!q || q.asset!==asset || q.mode!==mode || q.currency!==a.currency || !positive(q.price) || !positive(q.gbpPerUnit) || !q.source || !q.evidence || !q.fx?.source || !q.fx.evidence) fail('A sourced quote and GBP conversion are required.');
  if(!positive(q.price*q.gbpPerUnit)) fail('Invalid converted price.');
  if(q.fx.base!==q.currency || q.fx.quote!=='GBP' || q.gbpPerUnit!==q.fx.rate || (q.currency==='GBP' && q.fx.rate!==1)) fail('Unsupported currency conversion.');
  if(!Number.isFinite(q.delaySeconds) || q.delaySeconds<0) fail('Unknown quote delay.');
  const ts=Date.parse(q.timestamp), fxTs=Date.parse(q.fx.timestamp);
  if(!Number.isFinite(ts)||!Number.isFinite(fxTs)) fail('Missing quote timestamps.');
  if(mode==='historical') {
    if(!a.historical || q.date!==cursor || q.fx.date!==cursor || q.timestamp!==cursor+'T23:59:59.000Z' || q.fx.timestamp!==q.timestamp) fail('Historical prices must match this replay day.');
  } else if(mode==='current') {
    if(a.reference || q.marketStatus!=='open') fail('Market closed or status unavailable. Try again during market hours.');
    if(q.delaySeconds>900 || now-ts>q.delaySeconds*1000+120000 || now-ts < -30000 || (q.currency!=='GBP' && now-fxTs>120000) || now-fxTs < -30000) fail('Quote or FX rate is stale. Refresh before trading.');
    if(q.corporateActions!=='current-unadjusted') fail('Unsupported corporate-action basis.');
  } else fail('Unsupported mode.');
  return q;
}
export function newAccount(initial=50, mode='historical', cursor='2016-05-25') {
  if(!positive(initial)||initial<1||initial>10000000||Math.abs(Math.round(initial*100)-initial*100)>1e-7) fail('Choose a budget from £1 to £10 million, in pennies.');
  if(!['historical','current'].includes(mode)) fail('Invalid mode.');
  return {version:2, initial, mode, cursor, cash:initial, realised:0, positions:[], journal:[]};
}
export function buy(account, asset, amount, q, reason='', now=Date.now()) {
  validateQuote(q,asset,account.mode,account.cursor,now);
  if(!positive(amount)||amount<1||Math.abs(amount*100-Math.round(amount*100))>1e-7||amount>account.cash) fail('Invest £1 or more, in pennies, within your available cash.');
  const a=clone(account), units=amount/(q.price*q.gbpPerUnit);
  if(!positive(units)) fail('Invalid fractional units.');
  const id=String(a.journal.length+1);
  a.positions.push({id,asset,units,cost:amount,entry:clone(q)});a.cash-=amount;
  a.journal.push({action:'buy',id,asset,units,amountGBP:amount,quote:clone(q),orderTimestamp:new Date(now).toISOString(),replayDate:a.mode==='historical'?a.cursor:null,assumptions:ASSUMPTIONS,reason:String(reason).slice(0,1000)});
  return a;
}
export function close(account,id,q,now=Date.now()) {
  const p=account.positions.find(p=>p.id===id);if(!p) fail('Position not found.');
  validateQuote(q,p.asset,account.mode,account.cursor,now);
  // Current holdings are blocked across date boundaries: no split/dividend guesswork.
  if(account.mode==='current' && p.entry.timestamp.slice(0,10)!==q.timestamp.slice(0,10)) fail('This holding needs corporate-action reconciliation. Export your backup; closing is blocked across trading dates.');
  if(Date.parse(q.timestamp)<Date.parse(p.entry.timestamp)) fail('A close cannot precede its buy.');
  const a=clone(account), proceeds=p.units*q.price*q.gbpPerUnit;
  if(!positive(proceeds)||!Number.isFinite(a.cash+proceeds)) fail('Invalid proceeds.');
  a.cash+=proceeds;a.realised+=proceeds-p.cost;a.positions=a.positions.filter(x=>x.id!==id);
  a.journal.push({action:'close',id,asset:p.asset,units:p.units,amountGBP:proceeds,costGBP:p.cost,quote:clone(q),orderTimestamp:new Date(now).toISOString(),replayDate:a.mode==='historical'?a.cursor:null,assumptions:ASSUMPTIONS});return a;
}
export function advance(a,dates) {
  if(a.mode!=='historical') fail('Only historical practice has replay days.');
  const next=dates[dates.indexOf(a.cursor)+1];if(!next) fail('End of available history. Export or reset to start again.');
  return {...clone(a),cursor:next};
}
// Restore by replaying a bounded transaction ledger, rather than trusting balances/HTML.
export function restore(raw, dates) {
  if(!raw || raw.version!==2 || !Array.isArray(raw.journal)||raw.journal.length>5000) fail('Unsupported backup. Keep old v1 backups separately; manual prices cannot be verified.');
  let a=newAccount(raw.initial,raw.mode,dates[0]);
  for(const j of raw.journal) {
    if(!j || !Number.isFinite(Date.parse(j.orderTimestamp))) fail('Invalid journal.');
    if(a.mode==='historical') {
      if(!dates.includes(j.replayDate)||j.replayDate<a.cursor) fail('Replay cannot move backwards.');a.cursor=j.replayDate;
    }
    if(j.action==='buy') a=buy(a,j.asset,j.amountGBP,j.quote,j.reason,Date.parse(j.orderTimestamp));
    else if(j.action==='close') a=close(a,j.id,j.quote,Date.parse(j.orderTimestamp));
    else fail('Unknown transaction.');
  }
  if(a.mode==='historical') {if(!dates.includes(raw.cursor)||raw.cursor<a.cursor) fail('Invalid replay date.');a.cursor=raw.cursor;}
  return a;
}
export function historicalQuotes(csv,fxCsv) {
  const fx=new Map(fxCsv.trim().split(/\r?\n/).slice(1).map(s=>s.split(',')).filter(r=>positive(Number(r[2]))).map(r=>[r[0],Number(r[2])]));
  return csv.trim().split(/\r?\n/).slice(1).map(s=>s.split(',')).filter(r=>fx.has(r[0])&&positive(Number(r[1]))).map(([date,price])=>({asset:'BRENT',mode:'historical',date,price:Number(price),currency:'USD',timestamp:date+'T23:59:59.000Z',source:'EIA via datasets/oil-prices',evidence:'data/brent-brexit-source.csv (upstream blob 183a6e25c91f33d0db3cc48238354d03fa164723)',gbpPerUnit:fx.get(date),fx:{base:'USD',quote:'GBP',rate:fx.get(date),date,timestamp:date+'T23:59:59.000Z',source:'Federal Reserve DEXUSUK, inverted by datasets/exchange-rates',evidence:'data/gbp-usd-brexit-source.csv (upstream blob ed5f4b490edb0ec0585e40d019c73c33fb03948d)'},delaySeconds:0,marketStatus:'historical daily observation; intraday time unavailable',corporateActions:'not applicable to spot reference',availability:'Daily observations treated as available at end of day for this exercise; original publication time unknown.'}));
}
