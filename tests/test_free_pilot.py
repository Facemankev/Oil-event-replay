"""Free-source integration and explicitly synthetic transport edge cases."""
import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from free_pilot.data import load_free_library, coverage
from free_pilot.providers import SOURCES, MAX_BYTES, normalize, poll, journal
from free_pilot.pipeline import (CASES, build_demo, summarize_case, run_case,
                                 record_observation, detect)
from event_history.database import connect, import_library, read_library
from event_history.library import ROOT, ValidationError
from world_events.events import digest


class FreePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_free_library()
        (ROOT/'work').mkdir(exist_ok=True)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT/'work')
        self.directory = Path(self.tmp.name)/'session'
        self.now = datetime(2026,11,17,21,tzinfo=timezone.utc)
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def clock(self):
        return self.now.isoformat().replace('+00:00','Z')

    def client(self, status=200, payload=None, headers=None):
        raw = payload if payload is not None else (ROOT/SOURCES['company_events']['file']).read_bytes()
        def get(url, request_headers):
            self.calls.append((url,request_headers))
            return status,raw,headers or {}
        return get

    def test_primary_counts_nd_and_quote_directions_are_actual(self):
        counts = coverage(self.data)
        self.assertEqual(counts['observation_rows'],27210)
        self.assertEqual(counts['numeric_observations'],26074)
        self.assertEqual(counts['new_FX_numeric'],10456)
        self.assertEqual(counts['new_FX_unavailable'],434)
        points = {(p['instrument'],p['date']):p for p in self.data['observations']}
        self.assertEqual(points['eurusd','2006-01-03']['value'],'1.1980')
        self.assertEqual(points['usdjpy','2006-01-03']['value'],'116.3400')
        self.assertEqual(self.data['instruments']['usdjpy']['unit'],'JPY per USD')
        self.assertIsNone(points['eurusd','2006-01-02']['value'])
        self.assertFalse(counts['original_availability_verified'])

    def test_repeat_import_and_full_database_readback_preserve_parent_prices(self):
        original = (ROOT/'data/historical/brent-daily.csv').read_bytes() if (ROOT/'data/historical/brent-daily.csv').exists() else (ROOT/'data/brent-brexit-source.csv').read_bytes()
        path=Path(self.tmp.name)/'prices.sqlite'; db=connect(path)
        first=import_library(db,self.data); second=import_library(db,self.data); db.close()
        self.assertEqual(first['inserted_observation_rows'],27210)
        self.assertEqual(second['inserted_observation_rows'],0)
        self.assertEqual(second['reused_events'],51)
        self.assertEqual(read_library(path),self.data)
        current = (ROOT/'data/historical/brent-daily.csv').read_bytes() if (ROOT/'data/historical/brent-daily.csv').exists() else (ROOT/'data/brent-brexit-source.csv').read_bytes()
        self.assertEqual(original,current)

    def test_pinned_catalog_ingestion_rejects_a_changed_title_or_huge_payload(self):
        raw=(ROOT/SOURCES['company_events']['file']).read_bytes()
        self.assertEqual(normalize('company_events',raw)['items'],15)
        data=json.loads(raw);data['events'][0]['title']='Unverified change'
        with self.assertRaises(ValidationError):normalize('company_events',json.dumps(data).encode())
        with self.assertRaises(ValidationError):normalize('company_events',b'x'*(MAX_BYTES+1))

    def test_only_fixed_anonymous_sources_are_callable_no_keys_or_billing(self):
        for source in ('alpha_vantage','twelve_data','eodhd','https://example.org/?api_key=untrusted'):
            with self.assertRaises(ValidationError):poll(self.directory,source,self.client(),self.clock)
        self.assertFalse(self.calls)
        self.assertTrue(all(s['url'].startswith('https://') for s in SOURCES.values()))
        self.assertTrue(all('api_key=' not in s['url'] and 'apikey=' not in s['url'] for s in SOURCES.values()))

    def test_stooq_challenge_and_bad_ohlc_are_not_imported_as_prices(self):
        r=poll(self.directory,'stooq_nvda',self.client(payload=b'<html>Enable JavaScript to verify browser</html>'),self.clock)
        self.assertEqual(r['status'],'invalid_or_challenge_response')
        self.assertIsNone(r['normalized'])
        self.assertFalse((self.directory/'private').exists())
        bad=b'Date,Open,High,Low,Close,Volume\n2023-05-01,2,1,3,2,100\n'
        with self.assertRaises(ValidationError):normalize('stooq_nvda',bad)

    def test_well_formed_secondary_csv_does_not_gain_public_rights_or_adjustment_proof(self):
        raw=b'Date,Open,High,Low,Close,Volume\n2023-05-01,2,3,1,2,100\n'
        r=normalize('stooq_nvda',raw)
        self.assertEqual(r['numeric'],1)
        self.assertEqual(r['rows'],[])
        self.assertFalse(r['public_research_usable'])
        self.assertEqual(r['adjustment_basis'],'not_verified')

    def test_403_and_429_backoff_prevent_retry_loops_and_charges(self):
        r=poll(self.directory,'stooq_gold',self.client(403),self.clock)
        self.now+=timedelta(seconds=61)
        self.assertEqual(poll(self.directory,'stooq_gold',self.client(),self.clock)['status'],'cooldown_no_request')
        self.assertEqual(len(self.calls),1)
        self.assertEqual(r['cost_GBP'],'0.00')
        r=poll(self.directory,'fed_eurusd',self.client(429,headers={'Retry-After':'120'}),self.clock)
        self.now+=timedelta(seconds=119)
        self.assertEqual(poll(self.directory,'fed_eurusd',self.client(),self.clock)['status'],'cooldown_no_request')

    def test_conditional_304_reuses_pinned_evidence_without_freshness_claim(self):
        first=poll(self.directory,'company_events',self.client(headers={'ETag':'"snapshot"'}),self.clock)
        self.now+=timedelta(seconds=61)
        second=poll(self.directory,'company_events',self.client(304,payload=b''),self.clock)
        self.assertEqual(second['status'],'not_modified')
        self.assertEqual(second['normalized']['data'],first['normalized']['data'])
        self.assertEqual(self.calls[-1][1]['If-None-Match'],'"snapshot"')

    def test_clock_regression_imports_no_data_and_keeps_an_hour_backoff(self):
        times=iter(['2026-11-17T21:00:00Z','2026-11-17T20:59:00Z'])
        r=poll(self.directory,'company_events',self.client(),lambda:next(times))
        self.assertEqual(r['status'],'clock_regressed')
        self.assertIsNone(r['normalized'])
        self.assertTrue(r['next_attempt_at'].startswith('2026-11-17T22:00:00'))

    def test_historical_detection_has_real_earlier_comparisons_and_price_gaps(self):
        catalog=json.loads((ROOT/SOURCES['company_events']['file']).read_text())
        r=summarize_case('nvidia',self.data,catalog)
        self.assertEqual(r['detected_category'],'earnings')
        self.assertEqual(len(r['comparable_events']),2)
        self.assertTrue(all(p['change_percent'] is None for p in r['dated_reference_reactions']['NVDA']))
        self.assertEqual(set(r['three_answers']),{'what_happened','likely_outcome','suggested_action'})
        self.assertEqual(r['action'],'No Action')
        self.assertIsNone(detect({'title':'Unrelated text','summary':'No supported event category'}))

    def test_later_prices_and_reports_cannot_change_the_complete_frozen_decision(self):
        catalog=json.loads((ROOT/SOURCES['oil_events']['file']).read_text())
        before=summarize_case('harvey',self.data,catalog)
        changed=copy.deepcopy(self.data)
        for p in changed['observations']:
            if p['date']>'2017-08-26' and p['status']=='numeric':p['value']='9000.00'
        changed['reported_reactions'].clear()
        after=summarize_case('harvey',changed,catalog)
        self.assertEqual(before['frozen_historical_decision'],after['frozen_historical_decision'])
        self.assertEqual(before['frozen_decision_sha256'],after['frozen_decision_sha256'])
        self.assertNotEqual(before['dated_reference_reactions'],after['dated_reference_reactions'])

    def test_actual_local_receipt_and_journal_repeat_are_observation_only(self):
        first=run_case('nvidia',self.directory,data=self.data,clock=self.clock)
        self.now+=timedelta(seconds=61)
        second=run_case('nvidia',self.directory,data=self.data,clock=self.clock)
        self.assertTrue(first['journal']['inserted']);self.assertFalse(second['journal']['inserted'])
        self.assertEqual(first['journal']['first_recorded_at'],second['journal']['first_recorded_at'])
        self.assertFalse(first['ingestion']['network_request'])
        self.assertEqual(first['result']['actual_original_receipt_at'],None)
        self.assertEqual(first['orders'],0);self.assertEqual(first['account_mutations'],0)
        invalid=copy.deepcopy(first['result']);invalid['action']='Buy'
        with self.assertRaises(ValidationError):record_observation(self.directory,invalid,first['ingestion'])

    def test_remote_receipt_requires_a_real_parse_before_any_observation(self):
        r=run_case('nvidia',self.directory,True,data=self.data,clock=self.clock,client=self.client())
        self.assertEqual(r['status'],'observation_recorded')
        self.assertTrue(r['ingestion']['network_request'])
        self.assertFalse(r['continuous_monitoring'])
        failed=run_case('harvey',Path(self.tmp.name)/'blocked',True,data=self.data,clock=self.clock,client=self.client(403))
        self.assertEqual(failed['status'],'source_unavailable_or_cooldown')
        self.assertEqual(failed['action'],'No Action')

    def test_existing_secondary_peer_engine_retains_opposition_and_opening_disagreement(self):
        catalog=json.loads((ROOT/SOURCES['company_news']['file']).read_text())
        r=summarize_case('nvidia_board',self.data,catalog)
        p=r['legacy_daily_cross_check']
        self.assertEqual(p['own_percent'],'-4.2703')
        self.assertTrue(all(float(x['percent'])>0 for x in p['peers']))
        self.assertEqual(p['opening_quote_status'],'conflicting_provider_values')
        self.assertIsNone(p['exact_opening_percent'])
        self.assertEqual(p['baseline_date'],'2026-11-06')
        self.assertEqual(p['first_close_date'],'2026-11-09')
        self.assertFalse(p['verified_exchange_print_timestamps'])
        self.assertFalse(p['causal_transmission_established'])

    def test_unrelated_database_and_outside_journal_are_refused(self):
        self.directory.mkdir()
        path=self.directory/'observations.sqlite'
        with sqlite3.connect(path) as db:db.execute('CREATE TABLE unrelated(x)')
        before=path.read_bytes()
        with self.assertRaises(ValidationError):journal(self.directory)
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaises(ValidationError):journal(ROOT/'data')

    def test_pinned_demo_is_reproducible_five_cases_no_supported_entries(self):
        r=build_demo()
        self.assertEqual(digest(r),(ROOT/'free_pilot/DEMO.sha256').read_text().strip())
        self.assertEqual(len(r['cases']),5)
        self.assertTrue(all(c['action']=='No Action' for c in r['cases']))
        self.assertFalse(r['fresh_financial_news_connected'])
        self.assertEqual(r['cost_GBP'],'0.00')


if __name__=='__main__':unittest.main()
