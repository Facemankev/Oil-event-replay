"""Event evidence, revisions and deterministic oil joins; no network required."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from world_events import events as e
from world_events import research as r

class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=e.load_seed()
        cls.by_id={x['id']:x for x in cls.records}
        cls.prices=r.CSVPrices()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)

    def record(self,id='ike-2008-galveston'):
        return copy.deepcopy(self.by_id[id])

    def rehash(self,record):
        for s in record['evidence']:s['sha256']=e.digest({k:v for k,v in s.items() if k!='sha256'})
        return record

    def test_seed_coverage_and_real_source_evidence(self):
        self.assertEqual(len(self.records),24)
        self.assertEqual(len({x['category'] for x in self.records}),6)
        self.assertEqual(sum(x['first_public']['status']=='not_established' for x in self.records),4)
        self.assertEqual(sum(x['evidence'][0]['published']['precision']=='minute' for x in self.records),6)
        for item in self.records:
            self.assertEqual(item['revision'],1)
            self.assertTrue(item['evidence'][0]['stable_reference'])
            self.assertIn(item['evidence'][0]['quality'],e.QUALITIES)
            self.assertEqual(item['affected_commodities'],['brent','wti'])

    def test_timestamps_unknown_date_only_timezone_and_ambiguity(self):
        ike=self.record();e.validate_record(ike)
        self.assertEqual(e.instant(ike['first_public']['at']).hour,2)
        changes=[lambda x:x['first_public'].update(at='2008-09-13T02:30:00'),
                 lambda x:x['first_public'].update(timezone='Europe/London'),
                 lambda x:x['occurred'].update(date='2008-02-30'),
                 lambda x:x['occurred'].update(timezone='Not/AZone'),
                 lambda x:x['first_public'].update(date=None),
                 lambda x:x['first_public'].update(status='verified_global_first')]
        for change in changes:
            record=self.record();change(record)
            with self.subTest(change=change),self.assertRaises(e.ValidationError):e.validate_record(record)
        # A date-only release cannot quietly become midnight UTC.
        item=self.record('opec-2014-target');item['first_public']['at']='2014-11-27T00:00:00+00:00'
        with self.assertRaises(e.ValidationError):e.validate_record(item)
        unknown=self.record('saudi-2019-abqaiq');unknown['first_public']['date']='2019-09-14'
        with self.assertRaises(e.ValidationError):e.validate_record(unknown)
        # DST fold needs an offset that really maps to that named local zone.
        t={'date':'2021-11-07','at':'2021-11-07T01:30:00-04:00','timezone':'America/New_York','precision':'minute'}
        e.timing(t);t['at']='2021-11-07T01:30:00-05:00';e.timing(t)
        t['at']='2021-11-07T01:30:00+00:00'
        with self.assertRaises(e.ValidationError):e.timing(t)

    def test_source_quality_refs_and_tampering_fail(self):
        for field,value in [('quality','unverified'),('url','javascript:alert(1)'),('publisher',''),('sha256','0'*64),('stable_reference','')]:
            item=self.record();item['evidence'][0][field]=value
            with self.subTest(field=field),self.assertRaises(e.ValidationError):e.validate_record(item)
        item=self.record();item['public_evidence']='missing'
        with self.assertRaises(e.ValidationError):e.validate_record(item)
        item=self.record();item['evidence'][0]['quality']='official_report';self.rehash(item)
        with self.assertRaises(e.ValidationError):e.validate_record(item)

    def test_atomic_import_duplicates_idempotence_and_revisions(self):
        db=e.connect(Path(self.tmp.name)/'events.sqlite');self.addCleanup(db.close)
        self.assertEqual(e.import_records(db,self.records),{'inserted':24,'reused':0,'current_events':24})
        self.assertEqual(e.import_records(db,self.records),{'inserted':0,'reused':24,'current_events':24})
        item=self.record();item['description']='A corrected neutral description.'
        with self.assertRaises(e.ValidationError):e.import_records(db,[item])
        item['revision']=2;e.import_records(db,[item])
        current=next(x for x in e.list_events(db) if x['id']==item['id'])
        self.assertEqual(current['revision'],2)
        self.assertEqual(db.execute('SELECT count(*) FROM world_event_versions').fetchone()[0],25)
        e.import_records(db,[self.record()]);self.assertEqual(next(x for x in e.list_events(db) if x['id']==item['id'])['revision'],2)
        with self.assertRaises(e.ValidationError):e.import_records(db,[item,item])
        # A valid new ID followed by an invalid revision must roll back both.
        fresh=self.record();fresh['id']='test-new-event';bad=self.record('gustav-2008-louisiana');bad['revision']=3
        with self.assertRaises(e.ValidationError):e.import_records(db,[fresh,bad])
        self.assertFalse(db.execute('SELECT 1 FROM world_event_versions WHERE event_id=?',('test-new-event',)).fetchone())
        self.assertEqual(len(e.list_events(db,'weather')),6)
        with self.assertRaises(e.ValidationError):e.list_events(db,"weather' OR 1=1")

    def test_dataset_duplicate_and_schema_errors(self):
        path=Path(self.tmp.name)/'seed.json'
        for body in [{'schema_version':99,'events':self.records},{'schema_version':1,'events':[self.record(),self.record()]}]:
            path.write_text(json.dumps(body))
            with self.assertRaises(e.ValidationError):e.load_seed(path)
        other=Path(self.tmp.name)/'other.sqlite'
        with sqlite3.connect(other) as db:db.execute('CREATE TABLE prices(x)')
        with self.assertRaises(e.ValidationError):e.connect(other)

    def test_actual_shared_calendar_and_reproducible_ike_result(self):
        result=r.compare(self.record(),self.prices)
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['publication_anchor_date'],'2008-09-13')
        self.assertEqual(result['pre_dates'][-1],'2008-09-12')
        self.assertEqual(result['post_dates'][0],'2008-09-15')
        self.assertEqual(result['post_dates'][-1],'2008-09-19')
        self.assertEqual([(s['baseline'],s['end'],s['change_percent']) for s in result['series']],[('94.37','93.46','-0.9643'),('101.19','104.05','2.8264')])
        self.assertEqual(result,r.compare(self.record(),self.prices))
        self.assertFalse(result['backtest_eligible'])
        self.assertFalse(result['point_in_time_safe'])

    def test_publication_alignment_never_backdates_retrospective_evidence(self):
        result=r.compare(self.record('saudi-2019-abqaiq'),self.prices)
        self.assertEqual(result['occurrence_date'],'2019-09-14')
        self.assertEqual(result['publication_anchor_date'],'2019-09-23')
        self.assertEqual(result['evidence_lag_calendar_days'],9)
        self.assertNotIn('2019-09-16',result['post_dates'])
        # Harvey's local Friday-night bulletin belongs to Saturday in UTC.
        harvey=r.compare(self.record('harvey-2017-texas'),self.prices)
        self.assertEqual(harvey['publication_anchor_date'],'2017-08-26')
        self.assertEqual(harvey['post_dates'][0],'2017-08-28')
        item=self.record('saudi-2019-abqaiq');item['evidence'][0]['published']={'date':None,'at':None,'timezone':None,'precision':'unknown','approximate':False};self.rehash(item)
        result=r.compare(item,self.prices)
        self.assertEqual(result['status'],'publication_time_unknown')
        self.assertEqual(result['series'],[])

    def test_missing_nonpositive_and_insufficient_prices(self):
        class FixturePrices(r.PriceStore):
            metadata={'fixture':'synthetic test values only'}
            rows={'brent':[('2008-09-12',r.Decimal('0')),('2008-09-15',r.Decimal('-1'))],
                  'wti':[('2008-09-12',r.Decimal('1')),('2008-09-15',None)]}
        prices=FixturePrices()
        result=r.compare(self.record(),prices,1,1)
        self.assertEqual(result['status'],'insufficient_shared_observations')
        self.assertIn('2008-09-15',result['calendar']['explicit_missing']['wti'])
        prices.rows['wti'][1]=('2008-09-15',r.Decimal('2'))
        result=r.compare(self.record(),prices,1,1)
        self.assertIsNone(result['series'][0]['change_percent'])
        self.assertEqual(result['series'][0]['absolute_change'],'-1')
        prices.rows['brent'][0]=('2008-09-12',r.Decimal('-2'))
        result=r.compare(self.record(),prices,1,1)
        self.assertIsNone(result['series'][0]['change_percent'])
        self.assertEqual(result['series'][0]['absolute_change'],'1')
        for n in [0,21,True]:
            with self.assertRaises(e.ValidationError):r.compare(self.record(),prices,n,1)

    def test_price_manifest_and_dat3_shape_adapter(self):
        # Real seed values wrapped in the documented external JSON boundary.
        # No PR #12 code/module is imported or required.
        content={'schemaVersion':1,'series':[]}
        for market in r.MARKETS:
            content['series'].append({'series':market,'unit':'USD/barrel','sources':{'s0':{'source_kind':'seed','sha256':self.prices.metadata[market]['sha256']}},'observations':[{'date':d,'value':str(v) if v is not None else None,'snapshot_id':'s0'} for d,v in self.prices.rows[market]]})
        path=Path(self.tmp.name)/'prices.json';path.write_text(json.dumps(content))
        adapter=r.JSONPrices(path)
        self.assertEqual(r.compare(self.record(),adapter)['series'],r.compare(self.record(),self.prices)['series'])
        content['series'][0]['unit']='GBP/barrel';path.write_text(json.dumps(content))
        with self.assertRaises(e.ValidationError):r.JSONPrices(path)
        for bad in [[('2020-01-01','1'),('2020-01-01','2')],[('2020-02-30','1')],[('2020-01-01','NaN')]]:
            with self.assertRaises(e.ValidationError):r.normalize(bad)
        self.assertEqual(r.value('-36.98'),r.Decimal('-36.98'))

    def test_committed_export_and_seed_are_in_sync(self):
        path=Path(self.tmp.name)/'export.json'
        summary=r.export(self.records,self.prices,path)
        self.assertEqual(summary,{'events':24,'successful_comparisons':24,'first_public_not_established':4,'minute_public_evidence':6,'backtest_eligible':0})
        self.assertEqual(path.read_bytes(),(e.ROOT/'data/world-event-research.json').read_bytes())

if __name__=='__main__':unittest.main()
