"""Real committed seed coverage plus isolated, explicitly synthetic EIA fixtures."""
import copy
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
from historical import prices as p

class PricesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'prices.sqlite'
        self.db = p.open_db(self.path)
        self.addCleanup(self.db.close)
        self.addCleanup(self.tmp.cleanup)

    def snapshot(self, text='Date,Price\n2020-04-20,-36.98\n2020-04-21,0\n2020-04-22,NA\n', kind='eia', time='2026-10-27T10:00:00Z', market='wti'):
        raw=text.encode()
        return dict(market=market,kind=kind,source_url='https://example.org/fixture',revision='TEST FIXTURE ONLY',retrieved_at=time,payload=raw,rows=p.parse_csv(raw))

    def query(self,**kwargs):
        return p.query(self.db,'wti','2020-04-01','2020-04-30',**kwargs)

    def test_actual_seed_backfill_and_repeat_counts(self):
        imported=p.import_snapshots(self.db,[p.seed_snapshot(s) for s in p.SERIES])
        self.assertEqual([r['inserted'] for r in imported],[5231,5137])
        counts=self.db.execute('SELECT count(*) FROM price_observations').fetchone()[0]
        repeat=p.import_snapshots(self.db,[p.seed_snapshot(s) for s in p.SERIES])
        self.assertTrue(all(r['snapshot_reused'] for r in repeat))
        self.assertEqual(counts,10368)
        self.assertEqual(self.db.execute('SELECT count(*) FROM price_observations').fetchone()[0],counts)
        for s,n in [('brent',5231),('wti',5137)]:
            result=p.query(self.db,s,'2006-01-01','2026-10-27')
            self.assertEqual(result['coverage'],dict(count=n,first='2006-01-03',last='2026-10-20',explicit_missing=0))
        # Negative WTI spot observation is preserved from the real committed source.
        real=p.query(self.db,'wti','2020-04-20','2020-04-20')
        self.assertEqual(real['observations'][0]['value'],'-36.98')

    def test_parser_duplicates_missing_zero_negative_and_precision(self):
        rows=p.parse_csv(b'Date,Price\n2020-01-02,1.00\n2020-01-02,1.0\n2020-01-03,0\n2020-01-06,-2.5\n2020-01-07,.\n')
        self.assertEqual(rows,[('2020-01-02','1',None),('2020-01-03','0',None),('2020-01-06','-2.5',None),('2020-01-07',None,'.')])
        for bad in [b'Date,Price\n2020-02-30,5',b'Date,Price\n2020-01-01,NaN',b'Date,Price\n2020-01-01,inf',b'Date,Price\n2020-01-01,5\n2020-01-01,6',b'Date,Close\n2020-01-01,5',b'Date,Price\n2020-01-01,1,2',b'Date,Price\n2020-1-01,5',b'Date,Price\n2020-01-01,hello']:
            with self.subTest(bad=bad),self.assertRaises(p.DataError):p.parse_csv(bad)
        with self.assertRaises(p.DataError):p.parse_csv(b'Date,Price\n2027-01-01,5',retrieved_at='2026-10-27T10:00:00Z')

    def test_revision_history_reversion_missing_and_asof(self):
        first=self.snapshot();second=self.snapshot('Date,Price\n2020-04-20,NA\n2020-04-23,10\n',time='2026-10-27T11:00:00Z')
        p.import_snapshots(self.db,[first]);p.import_snapshots(self.db,[second])
        latest=self.query()
        self.assertEqual(latest['coverage']['count'],2)
        self.assertIsNone(latest['observations'][0]['value'])
        past=self.query(as_of='2026-10-27T10:30:00Z')
        self.assertEqual(past['observations'][0]['value'],'-36.98')
        self.assertFalse(past['point_in_time_safe'])
        self.assertEqual(self.query(as_of='2026-01-01T00:00:00Z')['coverage']['count'],0)
        # A -> B -> A is a real reversion, not an idempotent replay of old A.
        first['retrieved_at']='2026-10-27T12:00:00Z'
        self.assertEqual(p.import_snapshots(self.db,[first])[0]['revised'],1)
        self.assertEqual(self.query()['observations'][0]['value'],'-36.98')
        self.assertEqual(self.db.execute('SELECT count(*) FROM price_snapshots').fetchone()[0],3)

    def test_primary_preference_and_out_of_order_snapshots(self):
        p.import_snapshots(self.db,[self.snapshot()])
        p.import_snapshots(self.db,[self.snapshot('Date,Price\n2020-04-20,100\n',kind='seed',time='2026-10-27T12:00:00Z')])
        p.import_snapshots(self.db,[self.snapshot('Date,Price\n2020-04-20,99\n',time='2026-10-27T09:00:00Z')])
        self.assertEqual(self.query()['observations'][0]['value'],'-36.98')

    def test_atomic_import_rollback_and_unrelated_schema(self):
        item=self.snapshot();bad=self.snapshot(market='brent');bad['source_url']=None
        with self.assertRaises(sqlite3.IntegrityError):p.import_snapshots(self.db,[item,bad])
        self.assertEqual(self.db.execute('SELECT count(*) FROM price_snapshots').fetchone()[0],0)
        other=Path(self.tmp.name)/'other.sqlite'
        with sqlite3.connect(other) as db:db.execute('CREATE TABLE precious(x)')
        with self.assertRaises(p.DataError):p.open_db(other)
        self.db.execute('PRAGMA user_version=99')
        with self.assertRaises(p.DataError):p.open_db(self.path)

    def test_committed_static_export_matches_every_seed_observation(self):
        exported=json.loads((p.ROOT/'data/historical/prices.json').read_text())
        for series in exported['series']:
            seed=p.seed_snapshot(series['series'])
            self.assertEqual([(r['date'],r['value'],r['missing_code']) for r in series['observations']],seed['rows'])
            for r in series['observations']:
                self.assertIn(r['snapshot_id'],series['sources'])
            self.assertEqual(next(iter(series['sources'].values()))['sha256'],__import__('hashlib').sha256(seed['payload']).hexdigest())

    def test_primary_duplicate_pages_and_warning_handling(self):
        def duplicate(url):return self.response([self.row()],2)
        with self.assertRaises(p.DataError):p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=duplicate)
        body=json.loads(self.response([self.row()]))
        body.update(warning='parameter out of range',description='The API can only return 5000 rows; use offset')
        item=p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=lambda u:json.dumps(body).encode())
        self.assertEqual(len(item['rows']),1)
        body['warning']='unexpected source warning'
        with self.assertRaises(p.DataError):p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=lambda u:json.dumps(body).encode())

    def test_empty_range_and_parameterized_queries(self):
        p.import_snapshots(self.db,[self.snapshot()])
        self.assertEqual(p.query(self.db,'wti','2020-04-25','2020-04-26')['observations'],[])
        for start,end in [('2020-04-02','2020-04-01'),("2020-04-01' OR 1=1 --",'2020-04-30')]:
            with self.assertRaises(p.DataError):p.query(self.db,'wti',start,end)
        with self.assertRaises(p.DataError):p.query(self.db,"wti'",'2020-01-01','2020-12-31')

    def test_export_roundtrip_and_source_evidence(self):
        p.import_snapshots(self.db,[self.snapshot()])
        target=Path(self.tmp.name)/'prices.json';p.export(self.db,target)
        data=json.loads(target.read_text())
        result=next(s for s in data['series'] if s['series']=='wti')
        self.assertEqual(result['observations'][0]['value'],'-36.98')
        snapshot=next(iter(result['sources'].values()))
        self.assertEqual(snapshot['source_kind'],'eia')
        self.assertIn('retrieved_at',snapshot)
        self.assertIn('sha256',snapshot)
        self.assertIn('USD/barrel',target.read_text())

    def response(self,rows,total=None):
        return json.dumps({'response':{'frequency':'daily','total':str(total if total is not None else len(rows)),'data':rows},'request':{'params':{'api_key':'fixture-key'}}}).encode()

    def row(self,day='2020-04-20',value='-36.98'):
        return dict(series='RWTC',period=day,value=value,units='Dollars per Barrel')

    def test_eia_pagination_validation_and_secret_redaction(self):
        requests=[]
        def fetch(url):
            params=parse_qs(urlparse(url).query);requests.append(params)
            self.assertEqual(params['facets[series][0]'],['RWTC'])
            self.assertEqual(params['frequency'],['daily'])
            if params['offset']==['0']:return self.response([self.row()],total=2)
            return self.response([self.row('2020-04-21','0')],total=2)
        item=p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=fetch)
        self.assertEqual(len(requests),2);self.assertEqual(requests[1]['offset'],['1'])
        self.assertNotIn(b'fixture-key',item['payload']);self.assertNotIn('fixture-key',item['source_url'])
        self.assertEqual(len(item['rows']),2)
        p.import_snapshots(self.db,[item])
        self.assertNotIn(b'fixture-key',self.db.execute('SELECT payload FROM price_snapshots').fetchone()[0])

    def test_eia_errors_never_fallback_or_partial_write(self):
        bads=[b'<html>error</html>',self.response([]),self.response([{**self.row(),'series':'RBRTE'}]),self.response([{**self.row(),'units':'cents per gallon'}]),self.response([self.row('2030-01-01')]),json.dumps({'error':'fixture-key'}).encode()]
        for bad in bads:
            with self.subTest(bad=bad),self.assertRaises(p.DataError) as caught:
                p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=lambda u:bad)
            self.assertNotIn('fixture-key',str(caught.exception))
        self.assertEqual(self.db.execute('SELECT count(*) FROM price_snapshots').fetchone()[0],0)
        def unstable(url):return self.response([self.row()],2 if parse_qs(urlparse(url).query)['offset']==['0'] else 3)
        with self.assertRaises(p.DataError):p.fetch_eia('wti','2020-04-01','2020-04-30','fixture-key',fetcher=unstable)

    def test_incremental_overlap_and_failed_second_source_preserve_database(self):
        p.import_snapshots(self.db,[self.snapshot(market='brent'),self.snapshot()])
        captured=[]
        def fetch(market,start,end,key):
            captured.append((market,start,end));return self.snapshot('Date,Price\n2020-04-23,2\n',market=market)
        with patch.dict(os.environ,{'EIA_API_KEY':'fixture-key'}),patch.object(p,'fetch_eia',side_effect=fetch),patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(p.main(['--db',str(self.path),'update','--source','eia','--end','2020-05-01','--overlap-days','7']),0)
        self.assertEqual(captured,[('brent','2020-04-15','2020-05-01'),('wti','2020-04-15','2020-05-01')])
        before=self.db.execute('SELECT count(*) FROM price_snapshots').fetchone()[0]
        with patch.dict(os.environ,{'EIA_API_KEY':'fixture-key'}),patch.object(p,'fetch_eia',side_effect=[self.snapshot(),p.DataError('source failed')]),patch('sys.stderr',new_callable=io.StringIO):
            self.assertEqual(p.main(['--db',str(self.path),'update','--source','eia']),1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM price_snapshots').fetchone()[0],before)

if __name__=='__main__':unittest.main()
