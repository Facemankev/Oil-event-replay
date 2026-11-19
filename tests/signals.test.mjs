import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {validateReport,safeRating,rankedCards} from '../signals/contract.mjs';
const policy=JSON.parse(readFileSync(new URL('../signal_ratings/policy.json',import.meta.url)));
const data=JSON.parse(execFileSync('python3',['-c','import json;from signal_ratings.demo import screen_fixture;print(json.dumps(screen_fixture()))'],{encoding:'utf8'}));
const clone=()=>structuredClone(data);
test('synthetic screen schema retains winners, losers and all six supported identities',()=>{
 assert.equal(validateReport(data),data);assert.equal(Object.keys(data.examples).length,2);
});
test('Possible remains historical and cannot authorise a paper trade',()=>{
 const r=safeRating(data.cards[0],'declared',policy);assert.equal(r.rating,'POSSIBLE');assert.equal(r.current_signal,false);assert.equal(r.execution_action,'No Action');
});
test('forged Likely and validation registry cannot self-certify',()=>{
 const d=clone();d.likely_approved_validation_ids=['forged'];d.cards[0].ratings.declared.rating='LIKELY';d.cards[0].ratings.declared.independently_validated=true;
 assert.equal(safeRating(d.cards[0],'declared',policy).rating,'NO ACTION');
});
test('forged Possible cannot bypass minimum evidence',()=>{
 const d=clone();d.cards[0].costs.declared.complete=1;assert.equal(safeRating(d.cards[0],'declared',policy).rating,'NO ACTION');
});
test('direction and timeframe come from the checked hypothesis, not imported badges',()=>{
 const d=clone();d.cards[0].ratings.declared.direction='DOWN';assert.equal(safeRating(d.cards[0],'declared',policy).direction,'UP');
});
test('No Action never displays an expected direction',()=>{
 const d=clone();d.cards[2].ratings.declared.direction='UP';assert.equal(safeRating(d.cards[2],'declared',policy).direction,null);
});
test('cost selection changes rating without changing source history',()=>{
 assert.equal(safeRating(data.cards[0],'small_account_flat_fee',policy).rating,'NO ACTION');assert.equal(safeRating(data.cards[0],'declared',policy).rating,'POSSIBLE');
});
test('downside watch is not a sign-flipped short profit',()=>{
 const c=data.cards[1];assert.equal(safeRating(c,'declared',policy).direction,'DOWN');assert.ok(Number(c.costs.declared.median_net_gbp)<0);
});
test('contradictory returns fail closed even with a high historical success rate',()=>{
 const d=clone();d.cards[0].costs.declared.mean_return_percent='-1';d.cards[0].costs.declared.historical_success_percent='100';assert.equal(safeRating(d.cards[0],'declared',policy).rating,'NO ACTION');
});
test('inconsistent sample counts, non-finite values and unknown markets rejected',()=>{
 for(const mutate of [d=>d.cards[0].costs.declared.successful=999,d=>d.cards[0].costs.declared.mean_return_percent='NaN',d=>d.cards[0].instrument='invented',d=>d.cards.push(d.cards[0])]){const d=clone();mutate(d);assert.throws(()=>validateReport(d));}
});
test('rank and filters preserve No Action cases and do not select just the largest movement',()=>{
 assert.equal(rankedCards(data,{policy,rating:'NO ACTION'}).length,1);
 assert.equal(rankedCards(data,{policy,market:'MRNA'})[0].direction,'DOWN');
 const d=clone();d.cards[2].costs.declared.median_return_percent='900';assert.notEqual(rankedCards(d,{policy})[0].instrument,'AMD');
});
test('Python and browser agree on every synthetic rating',()=>{
 for(const c of data.cards)for(const cost of ['zero','declared','stressed','small_account_flat_fee'])assert.equal(safeRating(c,cost,policy).rating,c.ratings[cost].rating);
});
test('future examples and sources cannot be used in an earlier assessment',()=>{
 for(const change of [d=>d.examples.positive.maturity_day='2030-01-01',d=>d.sources.fixture.published_day='2030-01-01',d=>d.cards[0].as_of='2020-01-01']){const d=clone();change(d);assert.throws(()=>validateReport(d));}
});

test('cost robustness ranks ahead of the largest observed movement',()=>{
 const d=clone();const a=structuredClone(d.cards[0]),b=structuredClone(d.cards[0]);a.id='stable';b.id='fragile';b.costs.declared.median_return_percent='90';b.costs.stressed.median_net_gbp='-1';d.cards=[b,a];
 assert.equal(rankedCards(d,{policy})[0].id,'stable');
});
