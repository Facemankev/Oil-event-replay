import {readFileSync} from 'node:fs';
import {sha} from '../verification/load.mjs';
import {day,isStamp,canonicalURL,publicationBoundary} from './engine.mjs';
const read=name=>JSON.parse(readFileSync(new URL(name,import.meta.url),'utf8'));
export function loadEquities(){
 const hashes=read('INPUTS.json'),names=['calendar.json','history.json','news.json','prices.json','sources.json'];
 if(Object.keys(hashes).sort().join(',')!==names.join(','))throw Error('Missing equity source fingerprint');
 const data={};for(const name of names){const bytes=readFileSync(new URL(name,import.meta.url));if(sha(bytes)!==hashes[name])throw Error('Equity source fingerprint mismatch');data[name.slice(0,-5)]=JSON.parse(bytes);if(data[name.slice(0,-5)].schema_version!==1)throw Error('Invalid equity schema');}
 for(const s of Object.values(data.sources.sources))canonicalURL(s.url);
 const keys=new Set();
 for(const r of data.prices.rows){
  const key=r.symbol+':'+r.date+':'+r.source_id;
  if(keys.has(key)||!day(r.date)||!data.sources.sources[r.source_id]||!['NVDA','AMD','AVGO','MSFT','QQQ','IXIC'].includes(r.symbol)||
   ![r.open,r.close].every(v=>typeof v==='string'&&/^\d+\.\d{2}$/.test(v)&&Number(v)>0))throw Error('Invalid equity table row');keys.add(key);
 }
 const ids=new Set();for(const a of data.news.articles){if(ids.has(a.id)||!data.sources.sources[a.source_id]||a.actual_first_seen_at!==null||a.original_vintage_verified!==false)throw Error('Invalid curated news');ids.add(a.id);publicationBoundary(a);}
 for(const e of data.history.cases){if(!day(e.public_day)||e.public_at&&!isStamp(e.public_at)||e.source_ids.some(s=>!data.sources.sources[s])||e.prices.some(p=>!day(p.date)||!data.sources.sources[p.source_id]))throw Error('Invalid corporate history');}
 return {...data,hashes};
}
