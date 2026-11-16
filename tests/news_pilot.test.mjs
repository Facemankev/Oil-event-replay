import {test} from 'node:test';
import assert from 'node:assert/strict';
import {analyze,classifyShock} from '../news_pilot/analyze.mjs';
const item={title:'NVIDIA board investigation',summary:'Reported allegations; no reason to believe secrets compromised.',
 body_text:'Reported allegations; no reason to believe secrets compromised.',url:'https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors',
 source_id:'nvidia_news',source_family:'NVIDIA/newsroom',source_kind:'company_news',company:'NVDA',content_sha256:'a'.repeat(64),
 published_at:'2026-11-08T20:00:00Z',updated_at:null,first_seen_at:'2026-11-08T20:01:00Z'};

test('fresh real-clock receipt can produce only a local research monitor with historical checks',()=>{
 const r=analyze([item],'2026-11-08T20:01:30Z'),c=r.cards[0];
 assert.equal(c.freshness,'fresh_under_publisher_clock_assumption');assert.equal(c.receipt_to_card_seconds,30);
 assert.equal(c.publication_to_card_seconds,90);assert.equal(c.historical_cross_check.matches.length,4);
 assert.equal(c.action,'No Action');assert.equal(r.external_alerts_sent,0);assert.equal(r.continuous_monitoring,false);
 assert.deepEqual(Object.keys(c.three_answers),['what_happened','likely_outcome','suggested_action']);
});
test('future receipts and future revisions cannot enter an earlier card',()=>{
 assert.equal(analyze([item],'2026-11-08T20:00:30Z').cards.length,0);
 assert.equal(analyze([{...item,updated_at:'2026-11-10T00:00:00Z'}],'2026-11-08T20:02:00Z').cards.length,0);
 const revised={...item,content_sha256:'b'.repeat(64),first_seen_at:'2026-11-09T15:00:00Z',title:'NVIDIA new counterpoint'};
 assert.deepEqual(analyze([item,revised],'2026-11-08T20:02:00Z').cards,analyze([item],'2026-11-08T20:02:00Z').cards);
});
test('metadata changes and repeated copies never reset original freshness or multiply a case',()=>{
 const same={...item,first_seen_at:'2026-11-09T16:00:00Z',published_at:'2026-11-09T15:59:00Z'};
 const r=analyze([item,same],'2026-11-09T16:01:00Z');
 assert.equal(r.cards.length,1);assert.equal(r.cards[0].published_at,item.published_at);
 assert.equal(r.cards[0].freshness,'stale_or_original_publication_unknown');
});
test('updated-only software feed is neither original publication nor a financial shock',()=>{
 const a={...item,source_id:'nvidia_releases',url:'https://github.com/NVIDIA/TensorRT-LLM/releases/tag/test',source_kind:'product_release',
  title:'v-test',body_text:'Software features include security optimisations.',published_at:null,updated_at:'2026-11-08T20:00:00Z'};
 const c=analyze([a],'2026-11-08T20:02:00Z').cards[0];
 assert.equal(c.classification.type,'company_product_update');assert.equal(c.classification.materiality,'unestablished');
 assert.equal(c.publication_to_card_seconds,null);assert.equal(c.alert_status,'context_only');assert.equal(c.historical_cross_check.matches.length,0);
});
test('wider-market shocks are classified separately; broad supply words never infer a storm analogue',()=>{
 assert.deepEqual(classifyShock({title:'Central bank interest rate decision',summary:'Monetary policy update',company:null}).categories,['monetary_policy']);
 const oil={...item,source_id:'fed_news',company:null,source_kind:'wider_market',url:'https://www.federalreserve.gov/newsevents/pressreleases/test.htm',title:'Oil supply disruption',body_text:'Petroleum production shutdown',summary:'Oil supply disruption'};
 const c=analyze([oil],'2026-11-08T20:02:00Z').cards[0];assert.equal(c.classification.type,'wider_market');assert(c.macro_cross_check.every(m=>m.similarity==='Weak'));assert.equal(c.action,'No Action');
});
test('later counterpoint is retained with earlier allegation rather than counted as another independent article',()=>{
 const revision={...item,body_text:'Company denies the report.',summary:'Company denies the report.',first_seen_at:'2026-11-08T20:02:00Z',content_sha256:'b'.repeat(64)};
 const c=analyze([item,revision],'2026-11-08T20:03:00Z').cards[0];
 assert.equal(c.versions.length,2);assert.equal(c.contradictory_claim_or_counterpoint,true);assert(c.three_answers.what_happened.includes('counterpoints'));
});
test('opposing historical daily peer moves remain a limited cross-check, never timestamped live prices',()=>{
 const c=analyze([item],'2026-11-09T21:01:00Z').cards[0],p=c.peer_price_check;
 assert.equal(p.status,'timestamped_peer_quotes_unavailable');assert(p.descriptive_cross_check.own_percent<0);
 assert(p.descriptive_cross_check.peers.some(x=>x.symbol==='AMD'&&x.percent>0));assert.equal(p.descriptive_cross_check.causal_effect_established,false);
 const early=analyze([item],'2026-11-08T20:02:00Z').cards[0];assert.equal(early.peer_price_check.descriptive_cross_check.own_percent,null);
 assert(!early.peer_price_check.latest_retained_daily_date||early.peer_price_check.latest_retained_daily_date<'2026-11-08');
});
test('spoofed publisher, unapproved endpoint and credentialed URL are rejected',()=>{
 assert.throws(()=>analyze([{...item,source_id:'unknown'}],'2026-11-08T20:02:00Z'),/source/);
 assert.throws(()=>analyze([{...item,url:'https://example.org/nvidia'}],'2026-11-08T20:02:00Z'),/article/);
 assert.throws(()=>analyze([{...item,url:item.url+'?api_key=untrusted'}],'2026-11-08T20:02:00Z'),/URL/);
});

test('later publication metadata cannot upgrade an originally unknown publication clock',()=>{
 const first={...item,published_at:null},later={...item,first_seen_at:'2026-11-08T20:02:00Z',content_sha256:'c'.repeat(64)};
 const c=analyze([first,later],'2026-11-08T20:03:00Z').cards[0];assert.equal(c.published_at,null);assert.equal(c.alert_status,'context_only');
});
test('registered syndicated issuer copies are one source family despite different wording',()=>{
 const copy={...item,url:'https://investor.nvidia.com/news/press-release-details/2026/Statement-from-NVIDIA-Board-of-Directors/default.aspx',content_sha256:'d'.repeat(64),summary:'Company response to attributed allegations.'};
 const r=analyze([item,copy],'2026-11-08T20:03:00Z');assert.equal(r.cards.length,1);assert.equal(r.cards[0].source_family_count,1);assert.equal(r.cards[0].versions.length,2);
});
