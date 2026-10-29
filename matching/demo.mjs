/** Reproducible sample queries; hypothetical inputs never become historical facts. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import {analyse} from './analysis.mjs';
const input=fs.readFileSync(new URL('./cohort-catalog.json',import.meta.url));
const catalog=JSON.parse(input);
const base={market:'brent',severity:'',windSpeed:null,occurred:'2026-10-29',publicDate:'2026-10-29'};
const queries=[
 {...base,title:'Hypothetical Gulf storm with 110 mph advisory winds',category:'weather',location:'Gulf of Mexico',mechanism:'landfall',impact:'mixed',windSpeed:110},
 {...base,title:'Hypothetical announced production reduction',category:'production_policy',location:'Global',mechanism:'output_cut',impact:'supply_constraint'},
 {...base,title:'Harvey example at its supporting-publication date',category:'weather',location:'US Texas / Gulf of Mexico',mechanism:'landfall',impact:'mixed',windSpeed:125,occurred:'2017-08-25',publicDate:'2017-08-26',excludeId:'harvey-2017-texas'},
 {...base,title:'No eligible past events before 2000',category:'weather',location:'Gulf of Mexico',mechanism:'landfall',impact:'mixed',occurred:'2000-01-01',publicDate:'2000-01-01'}
];
const data={methodology:'cohort-summary-v1',catalog_sha256:crypto.createHash('sha256').update(input).digest('hex'),
 note:'Queries are explicitly hypothetical or historical demonstrations. No invented events or probability forecasts are added to the historical library.',
 demonstrations:queries.map(query=>({query,opportunities:analyse(query,catalog.events).opportunities.map(({windows,...summary})=>summary)}))};
const text=JSON.stringify(data,null,2)+'\n';
const target=new URL('./DEMONSTRATIONS.json',import.meta.url);
if(process.argv.includes('--check')){
 if(fs.readFileSync(target,'utf8')!==text)throw Error('Demonstration artifact differs from current code/data.');
 console.log('PASS: demonstrations match current catalogue and deterministic summaries');
}else{
 fs.writeFileSync(target,text);
 for(const demo of data.demonstrations){const row=demo.opportunities.find(r=>r.market==='brent'&&r.days===5);console.log(JSON.stringify({event:demo.query.title,comparable:row.comparable_event_count,used:row.percent.count,median:row.percent.median,range:[row.percent.minimum,row.percent.maximum],positive:row.percent.positive,negative:row.percent.negative,evidence:row.evidence}));}
}
