"""Synthetic-only anomaly, evidence-clock and leakage contracts. No owner prices."""
import copy,json,unittest
from datetime import date,timedelta
from decimal import Decimal as D
from pathlib import Path

from price_catalysts.detector import one_series,rank,distribution,standardized,sessions
from price_catalysts.evidence import load_evidence,relation,explanation
from price_catalysts.replay import epochs,prior_control,rule_for,period,reaction,Evaluator


def bars(n=100,start='2024-01-02'):
    from daily_prices.stooq_calendar import is_session
    d=date.fromisoformat(start);rows=[];value=D(100)
    while len(rows)<n:
        day=d.isoformat();d+=timedelta(days=1)
        if is_session(day) is False:continue
        if date.fromisoformat(day).weekday()>4:continue
        i=len(rows);value*=1+D([1,-2,3,-1,2,-3][i%6])/1000
        rows.append(dict(date=day,status='numeric',open=str(value),high=str(value*D('1.01')),low=str(value*D('.99')),close=str(value),volume='100'))
    return rows


def features(rows):return one_series('NVDA',rows,rows,[r['date'] for r in rows])


class DetectorTests(unittest.TestCase):
    def test_minimum_and_zero_variance(self):
        self.assertEqual(distribution([D(1)]*19),(None,None))
        self.assertIsNone(standardized(D(2),[D(1)]*25))
    def test_current_bar_excluded_from_volume_baseline(self):
        rows=bars();rows[-1]['volume']='5000';r=features(rows)[-1]
        self.assertEqual(r['volume_ratio'],'50.000000');self.assertEqual(r['prior_positive_volume_count'],60)
    def test_blank_volume_is_not_zero_or_inferred(self):
        rows=bars();rows[-1]['volume']=None
        self.assertIsNone(features(rows)[-1]['volume_ratio'])
    def test_missing_close_bar_is_retained_and_breaks_return_interval(self):
        rows=bars();rows[-2]=dict(rows[-2],status='ND',close=None)
        r=features(rows)
        self.assertEqual(len(r),len(rows));self.assertIn('missing_numeric_close',r[-2]['data_flags'])
        self.assertIsNone(r[-1]['close_change_percent']);self.assertIsNone(r[-1]['return_z'])
    def test_prior_volatility_is_not_current_move(self):
        rows=bars();a=features(rows)[-1];rows[-1]['close']=str(D(rows[-2]['close'])*D('1.4'));b=features(rows)[-1]
        self.assertEqual(a['prior_volatility'],b['prior_volatility']);self.assertGreater(D(b['return_z']),3)
    def test_future_prices_never_change_past_features(self):
        rows=bars(110);self.assertEqual(features(rows[:90]),features(rows)[:90])
    def test_gap_uses_open_not_high(self):
        rows=bars();rows[-1]['open']=str(D(rows[-2]['close'])*D('1.2'));rows[-1]['high']='9999'
        self.assertEqual(features(rows)[-1]['overnight_gap_percent'],'20.000000')
    def test_split_or_bad_print_is_retained_and_flagged(self):
        rows=bars();rows[-1]['close']=str(D(rows[-2]['close'])/2);r=features(rows)[-1]
        self.assertIn('possible_corporate_action_or_bad_print_needs_review',r['data_flags']);self.assertTrue(r['trigger'])
    def test_missing_source_bar_cannot_be_one_session_return(self):
        rows=bars();cal=[r['date'] for r in rows];del rows[-2]
        r=one_series('NVDA',rows,rows,cal)[-1];self.assertEqual(r['return_span_sessions'],2);self.assertIsNone(r['return_z'])
    def test_benchmark_must_have_both_exact_dates(self):
        rows=bars();spy=rows[:-1];r=one_series('NVDA',rows,spy,[r['date'] for r in rows])[-1]
        self.assertIsNone(r['SPY_excess_percentage_points']);self.assertIn('missing_exact_SPY_interval',r['data_flags'])
    def test_rank_keeps_both_signs_and_deduplicates_focus(self):
        rows=bars();rows[-1]['close']=str(D(rows[-2]['close'])*D('1.4'))
        rankings,focus=rank({'NVDA':features(rows)})
        self.assertEqual(rankings['NVDA']['rise'][0]['date'],rows[-1]['date'])
        self.assertEqual(len(focus),len({r['id'] for r in focus}));self.assertTrue(rankings['NVDA']['fall'])
    def test_spy_itself_is_not_a_meaningful_active_return_rank(self):
        rankings,focus=rank({'SPY':features(bars())});self.assertEqual(rankings['SPY']['SPY_abnormal'],[])
    def test_instrument_specific_scale(self):
        calm=features(bars())[-1]['prior_volatility'];rows=bars()
        for i,r in enumerate(rows):r['close']=str(D(100)+D(i%2)*20)
        self.assertGreater(D(features(rows)[-1]['prior_volatility']),D(calm)*10)


class EvidenceTests(unittest.TestCase):
    def test_sources_and_complete_quarter_pool(self):
        data=load_evidence();pool=data['controls'];self.assertEqual(len(pool),18)
        for s in ['NVDA','AMD','MRNA','BMY']:self.assertEqual(sum(c['instrument']==s and c['category']=='earnings' for c in pool),4)
        self.assertTrue(all('change_percent' not in c for c in pool))
    def test_later_story_is_not_a_precursor(self):
        self.assertEqual(relation({'published_day':'2024-02-02'},'2024-02-01'),'later_corroboration_not_a_precursor')
    def test_same_day_unknown_clock_does_not_become_early_warning(self):
        self.assertIn('not_proven_precursor',relation({'published_day':'2024-02-01','published_at':None},'2024-02-01'))
    def test_unexplained_and_uninvestigated_are_retained(self):
        e=load_evidence();self.assertEqual(explanation({'id':'unknown','date':'2024-01-01'},e)['category'],'uninvestigated')
        self.assertEqual(explanation({'id':'BMY-2000-04-19','date':'2000-04-19'},e)['category'],'unexplained')
    def test_contemporaneous_publication_is_not_actual_receipt(self):
        e=load_evidence();r=explanation({'id':'AMD-2016-04-22','date':'2016-04-22'},e)
        self.assertFalse(r['proven_early_warning']);self.assertIsNone(r['actual_historical_receipt_at'])


class ReplayTests(unittest.TestCase):
    def test_first_trigger_not_largest_later_peak(self):
        rows=features(bars(100))
        for i,r in enumerate(rows):r['trigger']=i in [30,31,50,51]
        self.assertEqual([x['date'] for x in epochs({'NVDA':rows},[r['date'] for r in rows])],[rows[30]['date'],rows[51]['date']])
    def test_rule_does_not_force_every_volume_spike_to_buy(self):
        self.assertIsNone(rule_for({'return_z':'0.2'}));self.assertEqual(rule_for({'return_z':'-4'}),'long_after_negative_close_anomaly')
    def test_context_control_does_not_read_current_or_future_return(self):
        rows=features(bars(180));target=rows[-1];cal=[r['date'] for r in rows];before=copy.deepcopy(rows)
        a=prior_control(target,rows,cal)
        for r in rows:r['close_change_percent']='999';r['future_return']='999'
        self.assertEqual(a['id'],prior_control(target,rows,cal)['id']);self.assertGreater(cal.index(target['date'])-cal.index(a['date']),21)
    def test_missing_benchmark_does_not_shift_date(self):
        rows=bars();series={r['date']:r for r in rows};spy=dict(series);del spy[rows[71]['date']]
        r=reaction(series,spy,rows[70]['date'],5,[r['date'] for r in rows])
        self.assertIsNotNone(r['change_percent']);self.assertIsNone(r['SPY_change_percent']);self.assertEqual(r['benchmark_missing_date'],rows[71]['date'])
    def test_post_detection_fill_is_next_close_and_exact_horizon(self):
        rows=bars();selections={s:dict(rows=rows,capture={'payload_sha256':'synthetic'}) for s in ['NVDA','AMD','MRNA','BMY','SPY','GLD']}
        fx=[dict(instrument='gbpusd',date=r['date'],value='1.25',status='numeric',source_id='synthetic',snapshot_id='synthetic') for r in rows]
        e=Evaluator(selections,{'observations':fx});r=e.window('NVDA',rows[70]['date'],5)
        for c,o in r['costs'].items():
            self.assertEqual(o['entry_date'],rows[71]['date']);self.assertEqual(o['exit_date'],rows[76]['date'])
        self.assertEqual(r['validated_action'],'No Action')
    def test_missing_fx_blocks_without_retry(self):
        rows=bars();selections={s:dict(rows=rows,capture={'payload_sha256':'synthetic'}) for s in ['NVDA','AMD','MRNA','BMY','SPY','GLD']}
        e=Evaluator(selections,{'observations':[]});r=e.window('NVDA',rows[70]['date'],1)
        self.assertEqual(r['costs']['declared']['reason'],'missing_exact_date_GBP_FX')
    def test_embargo_at_reference_boundary(self):
        cal=[r['date'] for r in bars(100,'2019-11-01')]
        self.assertEqual(period('2019-12-20',cal),'embargo');self.assertEqual(period('2020-01-02',cal),'embargo')



class PrivateLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from price_catalysts.demo import synthetic_report
        cls.report=synthetic_report()

    def test_public_projection_has_only_counts_no_returns_or_source_traces(self):
        from price_catalysts.ledger import audit
        public=json.dumps(audit(self.report))
        for key in ['close_change_percent','net_pnl_gbp','capture_fingerprints','published_at','subsequent','maximum_net_pnl_gbp']:
            self.assertNotIn(key,public)
        self.assertEqual(audit(self.report)['published_price_return_or_PNL_values'],0)

    def test_private_render_refuses_public_path_and_overwriting(self):
        from price_catalysts.view import render_private
        from event_history.library import ROOT
        import tempfile
        with self.assertRaises(ValueError):render_private(ROOT/'price_catalysts'/'forbidden.html',self.report)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            p=Path(folder)/'ledger.html';render_private(p,self.report)
            self.assertEqual(p.stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):render_private(p,self.report)

    def test_inline_json_is_safe_from_closing_script_injection(self):
        from price_catalysts.view import render_private
        from event_history.library import ROOT
        import tempfile
        r=copy.deepcopy(self.report);r['limitations']=['</script><script>attack()</script>']
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            p=Path(folder)/'ledger.html';render_private(p,r)
            self.assertNotIn('</script><script>attack',p.read_text());self.assertIn('\\u003c/script',p.read_text())

    def test_original_learning_and_simulation_reports_stay_separate(self):
        self.assertFalse(self.report['holdout_changed']);self.assertEqual(self.report['prospective_predictions'],0)
        self.assertEqual(self.report['validated_buys'],0);self.assertFalse(self.report['continuous_monitor_deployed'])
        self.assertEqual(set(self.report['parent_report_fingerprints']),{'learning','simulations'})

    def test_fee_sensitivity_keeps_negative_outcomes(self):
        windows=[w for r in self.report['ledger'] for w in r['subsequent']]
        comparable=[w for w in windows if w['costs']['zero']['status']==w['costs']['small_account_flat_fee']['status']=='simulated_reference_path']
        self.assertTrue(comparable)
        for w in comparable:self.assertGreater(D(w['costs']['zero']['net_pnl_gbp']),D(w['costs']['small_account_flat_fee']['net_pnl_gbp']))
        self.assertTrue(any(w['costs']['small_account_flat_fee']['net_outcome']=='negative' for w in comparable))

    def test_paired_control_coverage_keeps_missing_pairs(self):
        from price_catalysts.replay import paired_controls
        self.assertEqual(self.report['replay']['paired_context_comparisons'],paired_controls(self.report['replay']['cases']))
        self.assertTrue(all(r['complete_pairs']+r['missing_pairs']==r['attempts'] for r in self.report['replay']['paired_context_comparisons']))

    def test_unresearched_candidates_are_not_dropped_from_denominator(self):
        self.assertGreater(len(self.report['ledger']),0)
        self.assertTrue(any(r['evidence']['category']=='uninvestigated' for r in self.report['ledger']))
        self.assertTrue(all(r['validated_action']=='No Action' for r in self.report['ledger']))

    def test_private_source_database_is_read_only_and_explicit(self):
        from daily_prices.stooq import ASSETS,capture_for,parse_supplied
        from daily_prices.database import connect,import_capture
        from price_catalysts.data import load
        from event_history.library import ROOT
        import hashlib,tempfile
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            folder=Path(folder);dbpath=folder/'prices.sqlite';manifest=folder/'manifest.json'
            raw=b'Date,Open,High,Low,Close,Volume\n2024-01-02,100,101,99,100,10\n';imports=[]
            db=connect(dbpath)
            for symbol in ASSETS:
                capture=capture_for(symbol,raw,'2026-11-19T08:00:00Z')
                imports.append(import_capture(db,capture,parse_supplied(raw,capture),raw))
            db.close();manifest.write_text(json.dumps({'imports':imports}));before=hashlib.sha256(dbpath.read_bytes()).hexdigest()
            self.assertEqual(set(load(dbpath,manifest)),set(ASSETS));self.assertEqual(before,hashlib.sha256(dbpath.read_bytes()).hexdigest())
            manifest.write_text(json.dumps({'imports':imports+[imports[0]]}))
            with self.assertRaisesRegex(ValueError,'duplicate'):load(dbpath,manifest)


if __name__=='__main__':unittest.main()
