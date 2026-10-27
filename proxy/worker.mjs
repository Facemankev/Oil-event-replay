import {ASSETS,validateQuote} from '../trading/core.mjs';
const json=(body,status,origin)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store','Access-Control-Allow-Origin':origin||'null','Vary':'Origin','X-Content-Type-Options':'nosniff'}});
export async function handle(request,env,fetcher=fetch,now=Date.now()) {
 const origin=request.headers.get('Origin');
 if(!env.FRONTEND_ORIGIN||origin!==env.FRONTEND_ORIGIN)return json({error:'Origin not allowed.'},403);
 if(request.method!=='GET')return json({error:'GET only.'},405,origin);
 const url=new URL(request.url), asset=url.searchParams.get('asset'), a=ASSETS[asset];
 if(url.pathname!=='/quote'||[...url.searchParams.keys()].some(k=>k!=='asset')||url.searchParams.getAll('asset').length!==1||!a?.symbol)return json({error:'Unsupported asset.'},400,origin);
 // Explicit display rights and asset entitlements are required, not inferred from a key.
 if(env.DISPLAY_LICENSE_CONFIRMED!=='yes'||!env.TWELVE_DATA_API_KEY||!env.CURRENT_ASSETS?.split(',').includes(asset)||!env.RATE_LIMITER)return json({error:'Provider or display rights not configured.'},503,origin);
 try {
  const limit=await env.RATE_LIMITER.limit({key:request.headers.get('CF-Connecting-IP')||'unknown'});if(!limit.success)return json({error:'Please wait before refreshing.'},429,origin);
  const get=async(symbol,mic)=>{
   const u=new URL('https://api.twelvedata.com/quote');u.searchParams.set('symbol',symbol);u.searchParams.set('interval','1min');u.searchParams.set('prepost','false');if(mic)u.searchParams.set('mic_code',mic);u.searchParams.set('apikey',env.TWELVE_DATA_API_KEY);
   const r=await fetcher(u,{signal:AbortSignal.timeout(8000),redirect:'error'});if(!r.ok)throw Error('upstream');const body=await r.json();if(body.status==='error')throw Error('provider');return body;
  };
  const raw=await get(a.symbol,a.mic);
  // Require exact identity, explicit currency, timestamp and market-open flag.
  const pence=a.currency==='GBP'&&['GBp','GBX'].includes(raw.currency);
  if(raw.symbol!==a.symbol||raw.mic_code!==a.mic||(!pence&&raw.currency!==a.currency)||raw.is_market_open!==true)throw Error('identity or market');
  const timestamp=new Date(Number(raw.last_quote_at??raw.timestamp)*1000).toISOString();
  let fx={base:'GBP',quote:'GBP',rate:1,timestamp,source:'GBP identity conversion',evidence:'No FX needed: GBP quote'};
  if(a.currency==='USD'){
   const rate=await get('USD/GBP');if(rate.symbol!=='USD/GBP')throw Error('FX identity');
   fx={base:'USD',quote:'GBP',rate:Number(rate.close),timestamp:new Date(Number(rate.last_quote_at??rate.timestamp)*1000).toISOString(),source:'Twelve Data USD/GBP',evidence:`Twelve Data /quote USD/GBP at ${rate.timestamp}`};
  }
  // Delay is a deployment entitlement, never guessed from a free-plan marketing claim.
  const delay=Number(env.QUOTE_DELAY_SECONDS);if(!env.QUOTE_DELAY_SECONDS||!Number.isFinite(delay))throw Error('delay');
  const q={asset,mode:'current',price:Number(raw.close)*(pence?.01:1),currency:a.currency,timestamp,source:'Twelve Data',evidence:`Twelve Data /quote ${a.symbol} ${a.mic} at ${raw.timestamp}; raw ${raw.close} ${raw.currency}${pence?' (pence divided by 100 to GBP)':''}`,gbpPerUnit:fx.rate,fx,delaySeconds:delay,marketStatus:'open',corporateActions:'current-unadjusted'};
  validateQuote(q,asset,'current',null,now);return json(q,200,origin);
 }catch{return json({error:'Fresh sourced quote unavailable. Market may be closed, delayed or not entitled.'},503,origin);}
}
export default {fetch(request,env){return handle(request,env);}};
