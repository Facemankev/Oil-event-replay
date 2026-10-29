"""Real database integration and failure-oriented reaction/reconciliation checks."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from historical import prices
from world_events import events
from matching import build, validate_prices

ROOT = Path(__file__).resolve().parents[1]


class MatchingDataTests(unittest.TestCase):
    def setUp(self):
        self.seed = events.load_seed()
        self.event = next(e for e in self.seed if e['id'] == 'ike-2008-galveston')
        self.series = {s['series']: s for s in json.loads((ROOT/'data/historical/prices.json').read_text())['series']}

    def test_actual_horizons_and_provenance(self):
        result = build.reactions(self.event, self.series)
        self.assertEqual(result['anchor'], '2008-09-13')
        rows = result['markets']['brent']
        self.assertEqual([r['days'] for r in rows], [1,3,7,14,30])
        self.assertEqual(rows[0]['baseline'], '94.37')
        self.assertEqual(rows[0]['end_date'], '2008-09-15')
        source = {r['date']: r['value'] for r in self.series['brent']['observations']}
        for row in rows:
            self.assertEqual(row['status'], 'ok')
            self.assertEqual(len(row['observations']), row['days']+1)
            self.assertEqual(row['end'], source[row['end_date']])
            self.assertEqual(row['verification'], 'provisional_seed')
            self.assertFalse(row['point_in_time_safe'])
            self.assertTrue(row['sources'])

    def test_missing_observations_and_insufficient_tail(self):
        series = copy.deepcopy(self.series)
        r = next(r for r in series['brent']['observations'] if r['date']=='2008-09-15')
        r['value'] = None; r['missing_code'] = 'NA'
        windows = build.reactions(self.event,series)['markets']['brent']
        self.assertTrue(all(w['status']=='explicit_missing_observation' for w in windows))
        self.assertTrue(all(w['change_percent'] is None for w in windows))
        series['brent']['observations'] = [r for r in series['brent']['observations'] if r['date']<='2008-09-15']
        self.assertEqual(build.reactions(self.event,series)['markets']['brent'][1]['status'],'insufficient_observations')

    def test_zero_negative_unknown_and_late_evidence(self):
        for value in ['0','-36.98']:
            series = copy.deepcopy(self.series)
            next(r for r in series['brent']['observations'] if r['date']=='2008-09-12')['value']=value
            row = build.reactions(self.event,series)['markets']['brent'][0]
            self.assertEqual(row['status'],'ok');self.assertIsNone(row['change_percent'])
            self.assertIsNotNone(row['absolute_change'])
        late = next(e for e in self.seed if e['id']=='saudi-2019-abqaiq')
        self.assertEqual(build.reactions(late,self.series)['anchor'],'2019-09-23')
        unknown = copy.deepcopy(late)
        unknown['evidence'][0]['published']={'date':None,'at':None,'timezone':None,'precision':'unknown'}
        self.assertTrue(all(r['status']=='publication_time_unknown' for r in build.reactions(unknown,self.series)['markets']['wti']))

    def test_primary_status_requires_all_rows_primary(self):
        series=copy.deepcopy(self.series)
        for m in series:
            for s in series[m]['sources'].values():s['source_kind']='eia'
        self.assertEqual(build.reactions(self.event,series)['markets']['wti'][0]['verification'],'primary_EIA')
        # A single seed observation in a mixed window prevents a primary badge.
        row=next(r for r in series['wti']['observations'] if r['date']=='2008-09-15')
        series['wti']['sources']['seed']={'source_kind':'seed'};row['snapshot_id']='seed'
        self.assertEqual(build.reactions(self.event,series)['markets']['wti'][0]['verification'],'provisional_seed')

    def test_real_two_database_build(self):
        with tempfile.TemporaryDirectory() as directory:
            pp=Path(directory)/'prices.sqlite';ep=Path(directory)/'events.sqlite'
            db=prices.open_db(pp)
            try:prices.import_snapshots(db,[prices.seed_snapshot(m) for m in prices.SERIES])
            finally:db.close()
            db=events.connect(ep)
            try:events.import_records(db,self.seed)
            finally:db.close()
            data=build.build(pp,ep)
            self.assertEqual(len(data['events']),24)
            self.assertEqual(data['price_counts'],{'brent':5231,'wti':5137})
            windows=[w for e in data['events'] for rows in e['reactions']['markets'].values() for w in rows]
            self.assertEqual(len(windows),240)
            self.assertTrue(all(w['status']=='ok' for w in windows))
            self.assertTrue(all(w['verification']=='provisional_seed' for w in windows))
            self.assertTrue(all(e['features']['severity'] is None for e in data['events']))

    def test_reconciliation_exact_differences(self):
        comparison=validate_prices.differences([('2020-01-01','0',None),('2020-01-02','1',None)],
            [('2020-01-01','-1',None),('2020-01-03','2',None)])
        self.assertEqual(comparison['missing_from_seed'],['2020-01-03'])
        self.assertEqual(comparison['missing_from_primary'],['2020-01-02'])
        self.assertEqual(comparison['discrepancies'],[{'date':'2020-01-01','seed':'0','primary':'-1'}])
        self.assertEqual(comparison['equal_values'],0)

    def test_primary_failure_never_claims_verified_or_leaks(self):
        with patch.dict(os.environ,{},clear=True):
            result=validate_prices.audit(True)
            self.assertEqual(result['status'],'blocked');self.assertFalse(result['verified'])
            self.assertTrue(all(s['primary_comparison'] is None for s in result['series'].values()))
        # Fixture credential and exception are deliberately never returned.
        with patch.dict(os.environ,{'EIA_API_KEY':'x'}),patch.object(prices,'fetch_eia',side_effect=prices.DataError('x')):
            result=validate_prices.audit(True)
            self.assertFalse(result['verified']);self.assertNotIn('x',json.dumps(result))

    def test_primary_success_and_discrepancies_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            def fetched(market, start, end, key):
                snapshot=prices.seed_snapshot(market)
                snapshot['kind']='eia'
                return snapshot
            with patch.dict(os.environ,{'EIA_API_KEY':'x'}),patch.object(prices,'fetch_eia',side_effect=fetched),patch.object(validate_prices,'ROOT',Path(directory)):
                result=validate_prices.audit(True)
                self.assertTrue(result['primary_reconciliation_succeeded'])
                self.assertTrue(result['verified'])
                self.assertEqual(result['status'],'reconciled')
            def changed(market,start,end,key):
                snapshot=fetched(market,start,end,key)
                first=snapshot['rows'][0]
                snapshot['rows'][0]=(first[0],'1',None)
                return snapshot
            with patch.dict(os.environ,{'EIA_API_KEY':'x'}),patch.object(prices,'fetch_eia',side_effect=changed),patch.object(validate_prices,'ROOT',Path(directory)):
                result=validate_prices.audit(True)
                self.assertTrue(result['primary_reconciliation_succeeded'])
                self.assertFalse(result['verified'])
                self.assertEqual(result['status'],'reconciled_with_differences')
                self.assertEqual(len(result['series']['brent']['primary_comparison']['discrepancies']),1)

    def test_stale_baseline_blocks_reaction_and_design_is_original(self):
        series=copy.deepcopy(self.series)
        series['brent']['observations']=[r for r in series['brent']['observations'] if r['date']<'2008-08-01' or r['date']>'2008-09-13']
        windows=build.reactions(self.event,series)['markets']['brent']
        self.assertTrue(all(w['status']=='baseline_too_old' and w['absolute_change'] is None for w in windows))
        self.assertEqual((ROOT/'matching/design.css').read_bytes(),(ROOT/'.claude/skills/market-ripple-design/design.css').read_bytes())


if __name__=='__main__':unittest.main()
