const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const api=require('../research/compare.js');
const context={window:{}};vm.runInNewContext(fs.readFileSync('data/research-data.js','utf8'),context);
const seed=JSON.parse(JSON.stringify(context.window.MarketRippleData));
test('Brexit example uses shared June 23 and July 1 observations',()=>{
 const r=api.compare(seed.series,'2016-06-24',7);
 assert.equal(r.status,'ok');assert.equal(r.start,'2016-06-23');assert.equal(r.end,'2016-07-01');
 for(const result of r.results){const s=seed.series.find(s=>s.id===result.id);assert.equal(result.change,(s.rows.find(r=>r[0]==='2016-07-01')[1]/s.rows.find(r=>r[0]==='2016-06-23')[1]-1)*100);}
});
test('committed observations exactly match the downloaded source slices',()=>{
 for(const s of seed.series){const isApple=s.id==='aapl';const csv=fs.readFileSync(isApple?'data/apple-brexit-source.csv':'data/brent-brexit-source.csv','utf8');const expected=csv.trim().split(/\r?\n/).slice(1).map(l=>{const c=l.split(',');return[c[0],+c[isApple?4:1]];});assert.deepEqual(s.rows,expected);assert.match(s.source.blobSha,/^[a-f0-9]{40}$/);}
});
test('missing coverage yields no fabricated result',()=>{
 assert.equal(api.compare(seed.series,'2014-08-08',30).status,'missing');
 assert.equal(api.compare([],'2016-06-24',7).status,'empty');
});
test('different calendars align dates; no shared baseline fails',()=>{
 const series=[{id:'a',name:'A',rows:[['2020-01-01',100],['2020-01-02',110],['2020-01-03',120]]},{id:'b',name:'B',rows:[['2020-01-01',200],['2020-01-03',180],['2020-01-04',190]]}];
 const r=api.compare(series,'2020-01-02',7);assert.equal(r.end,'2020-01-03');assert.equal(r.results[1].change,(180/200-1)*100);
 series[1].rows[0][0]='2019-12-31';assert.equal(api.compare(series,'2020-01-02',7).status,'missing');
});
test('CSV validates real dates, missing and nonpositive values, quoting and order',()=>{
 const r=api.parseCSV('\uFEFFDate,Close,Note\r\n2020-02-29,"100","a,b"\r\n2020-02-30,200,x\r\n2020-03-02,,x\r\n2020-03-03,-1,x\r\n2020-03-04,Infinity,x\r\n2020-02-28,90,x');
 assert.deepEqual(r.rows,[['2020-02-28',90],['2020-02-29',100]]);assert.equal(r.skipped,4);
 assert.throws(()=>api.parseCSV('Date,Close\n2020-01-01,1\n2020-01-01,2'),/Duplicate/);
 assert.throws(()=>api.parseCSV('Date,Close\n"unfinished'),/unfinished/);
 assert.throws(()=>api.compare(seed.series,'2020-02-30',7),/Invalid/);
});
test('all seven legacy oil replay data and implementation are preserved',()=>{
 const {createHash}=require('node:crypto');
 const script=fs.readFileSync('index.html','utf8').split('<script>')[1].split('</script>')[0];
 // SHA-256 of the original replay script at b779ff655a776c8f665e39dcf1d4c49fe1337322.
 assert.equal(createHash('sha256').update(script).digest('hex'),'9fbba1a7f9d8839b68159ef969b0a2d455709da111246c143d11b01035527f0f');
});
