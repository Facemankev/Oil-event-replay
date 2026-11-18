"""Fabricated controls only. Supplied Stooq prices never enter GitHub/CI fixtures."""
import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch

from event_history.library import ROOT
from daily_prices.stooq import ASSETS,capture_for,parse_supplied,inspect_folder,policy,validate_private_capture,save_private
from daily_prices.database import connect,import_capture,query
from daily_prices.stooq_study import fixed_window,costed,build_study,scope
from daily_prices.evaluate import build_report


class StooqPrivateTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'work').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.days=[];d=date(2015,1,5)
        while len(self.days)<40:
            if d.weekday()<5:self.days.append(d.isoformat())
            d+=timedelta(days=1)
        lines=['Date,Open,High,Low,Close,Volume']
        for i,d in enumerate(self.days):lines.append(f'{d},{100+i},{102+i},{98+i},{100+i},'+('' if i==0 else '100'))
        self.raw=('\n'.join(lines)+'\n').encode()
        for name,venue,kind in ASSETS.values():(self.folder/name).write_bytes(self.raw)
        self.c=capture_for('NVDA',self.raw,'2026-11-18T22:00:00Z')
        self.rows=parse_supplied(self.raw,self.c)
        self.series={r['date']:r for r in self.rows}

    def verified_control_policy(self):
        p=policy();p.update(status='reviewed_private_quarantine_only',private_research_permitted=True,reviewed_source_document_sha256='0'*64,
            price_adjustments_verified=True,adjustment_basis='split_adjusted_only',adjustment_evidence='SYNTHETIC test policy',
            provenance_verified=True,provenance_evidence='SYNTHETIC test policy')
        return p # fake licence state only within a mocked, temporary test

    def test_all_six_inspected_without_creating_price_database(self):
        r,s=inspect_folder(self.folder,'2026-11-18T22:00:00Z')
        self.assertEqual(r['rows_inspected'],240);self.assertEqual(r['rows_imported'],0)
        self.assertEqual(set(s),set(ASSETS));self.assertFalse(r['adjustment_basis_verified'])
        self.assertFalse(list(self.folder.glob('*.sqlite')))

    def test_exact_bytes_and_original_locators_survive_blank_volume(self):
        self.assertEqual(self.rows[0]['source_row'],2);self.assertIsNone(self.rows[0]['volume'])
        self.assertEqual(self.rows[0]['source_fields']['Volume'],'')
        self.assertIsNone(self.rows[0]['adjusted_close']);self.assertIsNone(self.c['original_downloaded_at'])
        with self.assertRaises(ValueError):parse_supplied(self.raw+b'\n',self.c)

    def test_unknown_permission_is_blocked_but_reviewed_quarantine_CLI_works(self):
        p=policy();p['private_research_permitted']=False
        with patch('daily_prices.stooq.policy',return_value=p):
            with self.assertRaisesRegex(ValueError,'rights unverified'):validate_private_capture(self.c)
        output=self.folder/'private.json';db=self.folder/'prices.sqlite'
        r=subprocess.run([sys.executable,'-m','daily_prices.stooq','import','--folder',str(self.folder),'--db',str(db),'--output',str(output)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(db.exists())
        self.assertEqual(json.loads(output.read_text())['rows_imported'],240)
        self.assertNotIn('Close',r.stdout)

    def test_rights_cannot_be_self_asserted_in_capture(self):
        c=copy.deepcopy(self.c);c['rights']=self.verified_control_policy()
        with self.assertRaises(ValueError):validate_private_capture(c)

    def test_reviewed_private_scope_uses_existing_append_only_importer(self):
        p=self.verified_control_policy();c=copy.deepcopy(self.c);c['rights']=p;c['adjustment_basis']=p['adjustment_basis']
        db=connect(self.folder/'private.sqlite');self.addCleanup(db.close)
        with patch('daily_prices.stooq.policy',return_value=p):
            a=import_capture(db,c,self.rows,self.raw);b=import_capture(db,c,self.rows,self.raw)
            self.assertEqual(a['inserted_observations'],40);self.assertEqual(b['inserted_observations'],0)
            self.assertEqual(query(db,a['capture_id'],self.days[0],self.days[1])['rows'][0]['close'],'100')
            with self.assertRaises(sqlite3.DatabaseError):db.execute('DELETE FROM observations')

    def test_private_data_cannot_enter_public_report(self):
        with self.assertRaisesRegex(ValueError,'Private source data'):build_report({'NVDA':dict(capture=self.c,rows=self.rows)})

    def test_native_proxy_identity_cannot_become_spot_gold_or_index(self):
        p=self.verified_control_policy()
        with patch('daily_prices.stooq.policy',return_value=p):
            c=capture_for('GLD',self.raw,'2026-11-18T22:00:00Z');validate_private_capture(c)
            self.assertEqual(c['asset_kind'],'gold_etf_proxy')
            c['instrument']='gold_futures_reported'
            with self.assertRaises(ValueError):validate_private_capture(c)

    def test_bad_prices_duplicate_dates_weekends_or_unknown_schema_fail(self):
        variants=[self.raw.replace(b',100,102,98,100,',b',100,90,98,100,',1),
                  self.raw+self.raw.splitlines()[1]+b'\n',
                  self.raw.replace(b'2015-01-05',b'2015-01-04'),
                  self.raw.replace(b'Close',b'Adj Close'),
                  self.raw.replace(b',100,102,98,100,',b',100,102,98,NaN,',1)]
        for raw in variants:
            c=capture_for('NVDA',raw,'2026-11-18T22:00:00Z')
            with self.assertRaises(ValueError):parse_supplied(raw,c)

    def test_future_dates_fail_and_no_old_receipt_is_invented(self):
        c=copy.deepcopy(self.c);c['retrieved_at']='2015-01-04T12:00:00Z'
        with self.assertRaises(ValueError):parse_supplied(self.raw,c)
        self.assertIsNone(self.c['original_available_at']);self.assertFalse(self.c['original_vintage_verified'])

    def test_horizons_and_benchmark_use_identical_exact_dates(self):
        for h in (1,5,20):
            r=fixed_window(self.series,self.series,self.days[0],h)
            self.assertEqual(r['end_date'],None) # no pre-event close
            r=fixed_window(self.series,self.series,self.days[1],h)
            self.assertEqual(r['end_date'],self.days[h+1]);self.assertEqual(r['relative_wealth_percent'],'0.0000')
            self.assertEqual(r['excess_percentage_points'],'0.0000')

    def test_missing_asset_or_benchmark_never_moves_end_date(self):
        missing=dict(self.series);del missing[self.days[2]]
        self.assertEqual(fixed_window(missing,self.series,self.days[1],5)['status'],'missing_exact_session_price')
        # A day in another supplied security but absent in both ETFs is still
        # part of the empirical union, so it cannot be miscalled a holiday.
        r=fixed_window(self.series,missing,self.days[1],5,sorted(self.series))
        self.assertEqual(r['status'],'missing_exact_session_price');self.assertEqual(r['missing_date'],self.days[2])

    def test_publication_scopes_never_substitute_peers_or_ETFs(self):
        e=dict(targets=['NVDA','gold_futures_reported'])
        self.assertEqual(scope(e,'NVDA'),'sourced_direct_target')
        self.assertEqual(scope(e,'AMD'),'descriptive_panel_no_sourced_company_exposure')
        self.assertEqual(scope(e,'GLD'),'gold_ETF_proxy_not_futures_or_spot')
        self.assertIn('benchmark_not_Nasdaq',scope(e,'SPY'))

    def test_costed_path_uses_existing_fee_engine_and_keeps_losses(self):
        from simulations.engine import PROTOCOL
        planned=dict(event_id='synthetic-control',market='NVDA',rule='event_long',horizon=5,
                     hypothetical_intent='Conditional hypothetical Buy',status='planned',decision_bound=self.days[1]+'T12:00:00Z')
        points=[dict(instrument='NVDA',date=r['date'],value=r['close'],status='numeric',source_id='synthetic-control',snapshot_id='control') for r in self.rows]
        points += [dict(instrument='gbpusd',date=r['date'],value='1.25',status='numeric',source_id='synthetic-control',snapshot_id='control') for r in self.rows]
        data=dict(observations=points)
        zero=costed(planned,data,self.series,self.series,'zero')
        fee=costed(planned,data,self.series,self.series,'small_account_flat_fee')
        self.assertEqual(zero['status'],'simulated_reference_path');self.assertGreater(float(zero['net_pnl_gbp']),0)
        self.assertLess(float(fee['net_pnl_gbp']),0);self.assertEqual(fee['exit_date'],self.days[7])
        missing=copy.deepcopy(data);missing['observations']=[p for p in points if not(p['instrument']=='gbpusd' and p['date']==self.days[3])]
        r=costed(planned,missing,self.series,self.series,'declared')
        self.assertEqual(r['reason'],'missing_exact_date_GBP_FX');self.assertNotEqual(r['status'],'simulated_reference_path')

    def test_private_reports_refuse_public_paths_and_overwriting(self):
        with self.assertRaises(ValueError):save_private(ROOT/'daily_prices'/'forbidden.json',{})
        p=self.folder/'report.json';save_private(p,{'test':'synthetic'})
        with self.assertRaises(FileExistsError):save_private(p,{})
        self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_complete_study_preserves_inputs_holdout_and_private_projection(self):
        from world_events.events import digest
        from daily_prices.stooq import public_summary
        inspection,selections=inspect_folder(self.folder,'2026-11-18T22:00:00Z')
        event=dict(id='synthetic-event',episode_id='synthetic-episode',title='SYNTHETIC control',
            targets=['NVDA'],primary_group='technology_equities',category='earnings',location=['US'],
            mechanism='control',publication_source='synthetic-release',public_at=None,public_day=self.days[1])
        fx=[dict(instrument='gbpusd',date=d,value='1.25',status='numeric',source_id='control',snapshot_id='control') for d in self.days]
        data=dict(events=[event],observations=fx,instruments={'gbpusd':{},'NVDA':{}},
            sources={'synthetic-release':dict(published_day=self.days[1],published_at=None)})
        before=digest(data);r=build_study(selections,inspection,data)
        self.assertEqual(before,digest(data));self.assertEqual(r['newly_covered_direct_event_pairs'],1)
        self.assertEqual(r['new_eligible_historical_examples'],0)
        self.assertFalse(r['learning_holdout']['trained_or_tuned']);self.assertEqual(r['learning_holdout']['genuinely_new_predictions'],0)
        view=json.dumps(public_summary(r))
        self.assertNotIn('net_pnl_gbp',view);self.assertNotIn('payload_sha256',view);self.assertNotIn('change_percent',view)
        self.assertEqual(public_summary(r)['actual_price_or_return_values_published'],0)

    def test_unknown_adjustments_and_provenance_can_never_be_marked_approved(self):
        for field in ('price_adjustments_verified','provenance_verified'):
            p=self.verified_control_policy();p[field]=False
            c=copy.deepcopy(self.c);c['rights']=p;c['adjustment_basis']=p['adjustment_basis']
            with patch('daily_prices.stooq.policy',return_value=p):
                validate_private_capture(c)
                c['canonical_prices_approved']=True
                with self.assertRaises(ValueError):validate_private_capture(c)

    def test_official_calendar_keeps_early_close_and_adds_special_closure(self):
        from daily_prices.stooq_calendar import is_session
        self.assertTrue(is_session('2024-07-03'))
        self.assertFalse(is_session('2024-07-04'))
        self.assertFalse(is_session('2025-01-09'))
        self.assertIsNone(is_session('2011-02-17'))

    def test_shared_missing_day_in_reviewed_year_is_not_a_holiday(self):
        from daily_prices.stooq_calendar import grid
        # Fabricated input omits a real, officially scheduled benchmark day.
        points={'2023-12-29':{},'2024-01-02':{},'2024-01-04':{}}
        days=grid({'SPY':points,'NVDA':points})
        self.assertEqual(days,['2023-12-29','2024-01-02','2024-01-03','2024-01-04'])
        series={d:dict(status='numeric',close='100') for d in points}
        result=fixed_window(series,series,'2024-01-02',1,days)
        self.assertEqual(result['status'],'missing_exact_session_price');self.assertEqual(result['missing_date'],'2024-01-03')
        self.assertEqual(fixed_window(series,series,'2024-01-03',1,days)['status'],'provisional_supplied_reporting_sessions')


if __name__=='__main__':unittest.main()
