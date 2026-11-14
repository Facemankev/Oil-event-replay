/** Plain-English demonstrations of real selected cases, not forecasts. */
import {buildStudy} from './evaluate.mjs';
const report=buildStudy();
const wanted=process.argv.slice(2).filter(x=>!x.startsWith('--'));
const ids=wanted.length?wanted:['harvey-2017-texas','delta-2020-louisiana','francine-2024-louisiana'];
for(const id of ids){
 const r=report.records.find(x=>x.event_id===id&&x.market==='brent');
 if(!r)throw Error('Choose a catalog event ID');
 const d=r.detail.descriptive;
 console.log(`\n${id}: Brent at ${r.cutoff}`);
 console.log(`Occurred ${r.occurred_at||'clock unknown'}; supporting bulletin ${r.event_public_at||'clock unknown'}.`);
 console.log(`${r.action}. ${r.detail.selected.length} distinct storm/context candidates; ${d.count} usable current-data reactions; ${r.detail.fully_qualified} fully as-of qualified (minimum ${r.detail.minimum_cases}).`);
 console.log(d.count?`Historical five-observation GBP reaction: median ${d.median.toFixed(2)}%, range ${d.minimum.toFixed(2)}% to ${d.maximum.toFixed(2)}%; ${d.positive} positive / ${d.negative} negative. These are sample counts, not forecast odds.`:'No usable descriptive reaction.');
 for(const c of r.detail.selected)console.log(`- ${c.id}: ${c.reasons.join('; ')}. Limits: ${c.parent_blockers.join(', ')}. ${c.dated_FX_observations}/${c.required_FX_observations} reaction FX rows corroborated by an eligible dated release.`);
 console.log(`Why no paper entry: ${r.reasons.join('; ')}. Opposing crude supply and refinery demand channels can offset each other.`);
 console.log('The event-publication reaction starts before the event anchor; execution baselines start after it. Neither establishes causation, guaranteed profit or an automatic order.');
}
