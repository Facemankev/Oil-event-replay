"""Synthetic-only SIGNAL-1 safeguards; no owner prices in tests or CI."""
import copy
import json
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
from world_events.events import digest
from signal_ratings.classify import classify, approved_validation, rank_key
from signal_ratings.engine import assess, summarize
from signal_ratings.patterns import matches, select
from signal_ratings.policy import POLICY


def card(direction='UP'):
    sign = 1 if direction == 'UP' else -1
    stats = dict(attempts=20, complete=18, coverage='0.9', distinct_years=5,
                 later_complete=8, control_pairs=15, mean_return_percent=str(sign*4),
                 median_return_percent=str(sign*3), mean_net_gbp=str(sign*0.2),
                 median_net_gbp=str(sign*0.1), later_mean_return_percent=str(sign*3),
                 later_median_return_percent=str(sign*2), median_paired_difference_gbp=str(sign*0.1),
                 median_SPY_excess_pp=str(sign*2), median_net_SPY_excess_gbp=str(sign*0.1),
                 worst_directional_return_percent='-6', historical_success_percent='65')
    return dict(id='NVDA:spike:'+direction+':5', instrument='NVDA', direction=direction,
                horizon=5, validation_id=None, costs={c:copy.deepcopy(stats) for c in POLICY['costs']})


def feature(i=0, **changes):
    row = dict(id='NVDA-2024-01-02', instrument='NVDA', date=f'2024-01-{i+2:02d}',
               data_flags=[], return_span_sessions=1, return_z='4', gap_z='0', volume_ratio='4',
               close_change_percent='8', prior_volatility='0.01', prior_trend='0.10')
    return row | changes


def fixture_report():
    windows = {}
    members = []
    for i, year in enumerate(range(2012, 2026)):
        key = f'synthetic-{i}'
        control = f'control-{i}'
        ret = '-2' if i % 3 == 0 else '4'
        def window(net, day, r):
            outcome = dict(status='simulated_reference_path', net_pnl_gbp=net,
                           total_friction_gbp='0.03', reason='fixed_horizon',entry_date=day,exit_date=day)
            return dict(detection_day=day, maturity_day=day, instrument='NVDA',
                        entry_reaction=dict(change_percent=r, SPY_excess_percentage_points=r,SPY_status='complete'),
                        costs={c:dict(outcome) for c in POLICY['costs']},
                        SPY_costs={c:dict(outcome,net_pnl_gbp='0') for c in POLICY['costs']})
        day=f'{year}-06-01'
        windows[key]=window('-0.10' if i%3==0 else '0.20',day,ret)
        windows[control]=window('-0.20',f'{year}-03-01','-4')
        members.append(dict(window=key,control_window=control,
                            period='later_exploratory_already_examined' if year>=2020 else 'reference_exploratory'))
    return dict(windows=windows,groups=[dict(instrument='NVDA',pattern='spike',horizon=5,members=members)])


class RatingTests(unittest.TestCase):
    def test_supporting_history_can_be_possible_but_not_a_trade(self):
        r=classify(card());self.assertEqual(r['rating'],'POSSIBLE')
        self.assertEqual((r['direction'],r['horizon']),('UP',5))
        self.assertFalse(r['current_signal']);self.assertEqual(r['execution_action'],'No Action')
    def test_high_success_rate_alone_cannot_be_likely(self):
        c=card();c['costs']['declared']['historical_success_percent']='100'
        c['independently_validated']=True;c['validation_id']='self-certified'
        r=classify(c);self.assertEqual(r['rating'],'POSSIBLE');self.assertFalse(r['independently_validated'])
    def test_no_approved_independent_validation_exists(self):
        self.assertIsNone(approved_validation('invented',card()['id']))
    def test_poor_net_performance_blocks_even_high_win_rate(self):
        c=card();c['costs']['declared']['median_net_gbp']='-0.1'
        self.assertEqual(classify(c)['rating'],'NO ACTION')
    def test_conflicting_mean_and_median_blocks(self):
        c=card();c['costs']['declared']['mean_return_percent']='-1'
        self.assertEqual(classify(c)['rating'],'NO ACTION')
    def test_small_or_single_year_sample_blocks(self):
        for key,value in [('complete',9),('distinct_years',1),('later_complete',2),('control_pairs',2),('coverage','0.2')]:
            c=card();c['costs']['declared'][key]=value
            self.assertEqual(classify(c)['rating'],'NO ACTION',key)
    def test_underperforming_benchmark_blocks(self):
        for key in ['median_SPY_excess_pp','median_net_SPY_excess_gbp']:
            c=card();c['costs']['declared'][key]='-1'
            self.assertEqual(classify(c)['rating'],'NO ACTION')
    def test_higher_fees_can_remove_possible(self):
        c=card();c['costs']['small_account_flat_fee']['median_net_gbp']='-1'
        self.assertEqual(classify(c)['rating'],'POSSIBLE')
        self.assertEqual(classify(c,'small_account_flat_fee')['rating'],'NO ACTION')
    def test_down_is_defensive_research_not_invented_short_profit(self):
        r=classify(card('DOWN'));self.assertEqual(r['rating'],'POSSIBLE')
        self.assertIn('no short',r['downside_scope']);self.assertEqual(r['execution_action'],'No Action')
    def test_costs_cannot_turn_rising_prices_into_downside_evidence(self):
        c=card('DOWN');c['costs']['declared']['mean_return_percent']='1'
        self.assertEqual(classify(c)['rating'],'NO ACTION')
    def test_spy_self_excess_not_treated_as_alpha(self):
        c=card();c['instrument']='SPY';c['costs']['declared']['median_SPY_excess_pp']='0'
        self.assertEqual(classify(c)['rating'],'POSSIBLE')
    def test_ranking_prefers_evidence_before_largest_return(self):
        a,b=card(),card();a['id']='a';b['id']='b'
        b['costs']['declared']['median_return_percent']='90';b['costs']['declared']['coverage']='0.6'
        for c in [a,b]:c['ratings']={x:classify(c,x) for x in POLICY['costs']}
        self.assertLess(rank_key(a),rank_key(b))
    def test_cost_fragility_precedes_largest_return_in_ranking(self):
        stable,fragile=card(),card();stable['id']='stable';fragile['id']='fragile'
        fragile['costs']['declared']['median_return_percent']='90'
        fragile['costs']['stressed']['median_net_gbp']='-1'
        for c in [stable,fragile]:c['ratings']={cost:classify(c,cost) for cost in POLICY['costs']}
        self.assertLess(rank_key(stable),rank_key(fragile))
    def test_likely_requires_reviewed_clock_bound_robust_artifact(self):
        c=card();c['validation_id']='reviewed-synthetic'
        artifact=dict(candidate_key=c['id'],mode='prospective_independent',
             primary_point_in_time_prices=True,usage_permitted=True,independence_audited=True,
             registered_before_outcomes=True,costs_and_benchmark_audited=True,multiple_testing_reviewed=True,
             training_ended_at='2027-01-01T00:00:00Z',registered_at='2027-01-02T00:00:00Z',
             first_prediction_at='2027-01-03T00:00:00Z',first_outcome_at='2027-01-04T00:00:00Z',completed_at='2027-01-05T00:00:00Z',
             independent_examples=60,time_blocks=4,coverage='0.95',mean_directional_net_stressed='1',
             median_directional_net_stressed='1',benchmark_excess='1',control_excess='1',block_robustness_lower_bound='0.1')
        with tempfile.TemporaryDirectory() as folder:
            here=Path(folder);(here/'proof.json').write_text(json.dumps(artifact))
            def register(a):
                (here/'proof.json').write_text(json.dumps(a))
                (here/'registry.json').write_text(json.dumps(dict(approved_independent_validations={c['validation_id']:dict(artifact='proof.json',sha256=digest(a),policy_sha256=digest(POLICY))})))
            register(artifact)
            from datetime import datetime,timezone
            with patch('signal_ratings.classify.HERE',here), patch('signal_ratings.classify.current_time',return_value=datetime(2028,1,1,tzinfo=timezone.utc)):
                self.assertEqual(classify(c)['rating'],'LIKELY');self.assertEqual(classify(c)['execution_action'],'No Action')
                bad=dict(artifact,first_prediction_at='2027-01-05T00:00:00Z');register(bad)
                self.assertEqual(classify(c)['rating'],'POSSIBLE')
                bad=dict(artifact,benchmark_excess='0');register(bad)
                self.assertEqual(classify(c)['rating'],'POSSIBLE')
                bad=dict(artifact,independent_examples=5);register(bad)
                self.assertEqual(classify(c)['rating'],'POSSIBLE')
                for changes in [dict(primary_point_in_time_prices=False),dict(completed_at='2030-01-01T00:00:00Z'),dict(registered_at='2025-01-01T00:00:00Z'),dict(block_robustness_lower_bound='NaN')]:
                    register(dict(artifact,**changes));self.assertEqual(classify(c)['rating'],'POSSIBLE')


class PatternTests(unittest.TestCase):
    def test_spikes_trends_volume_and_combination_all_detected(self):
        self.assertEqual(set(matches(feature())),{'spike','trend_up','volume_up','spike_volume'})
    def test_negative_and_gap_conditions(self):
        row=feature(return_z='-4',gap_z='-5',close_change_percent='-8',prior_trend='-0.10')
        self.assertEqual(set(matches(row)),{'dip','gap_down','trend_down','volume_down','dip_volume'})
    def test_missing_and_split_anomalies_never_become_patterns(self):
        for flag in ['missing_numeric_close','possible_corporate_action_or_bad_print_needs_review']:
            self.assertEqual(matches(feature(data_flags=[flag])),[])
    def test_volume_absent_never_fabricated(self):
        self.assertNotIn('spike_volume',matches(feature(volume_ratio=None)))
    def test_first_qualifying_bar_is_not_later_peak(self):
        rows=[feature(i,return_z=str(4+i)) for i in range(25)];calendar=[r['date'] for r in rows]
        selected=select({'NVDA':rows},calendar)[('NVDA','spike')]
        self.assertEqual([r['date'] for r in selected],[rows[0]['date'],rows[21]['date']])


class AggregationTests(unittest.TestCase):
    def test_success_rate_is_observed_direction_not_probability(self):
        r=fixture_report();s=summarize(r['groups'][0]['members'],r['windows'],'UP','declared')
        self.assertEqual(s['successful']+s['unsuccessful']+s['unchanged'],s['complete'])
        self.assertIn('not net profit',s['success_definition']);self.assertIsNotNone(s['mean_return_percent'])
    def test_missing_cost_or_fx_stays_in_denominator(self):
        r=fixture_report();r['windows']['synthetic-0']['costs']['declared']=dict(status='not_entered',reason='missing_exact_date_GBP_FX')
        s=summarize(r['groups'][0]['members'],r['windows'],'UP','declared')
        self.assertEqual((s['attempts'],s['complete'],s['missing']),(14,13,1))
    def test_only_matured_outcomes_can_influence_earlier_assessment(self):
        r=fixture_report();before=digest(assess(r,'2020-01-01'))
        r['windows']['synthetic-13']['entry_reaction']['change_percent']='99999'
        r['windows']['synthetic-13']['costs']['declared']['net_pnl_gbp']='99999'
        self.assertEqual(before,digest(assess(r,'2020-01-01')))
    def test_outcome_on_cutoff_day_is_not_available_before_close(self):
        r=fixture_report();c=assess(r,'2012-06-01')[0]
        self.assertEqual(c['costs']['declared']['attempts'],0)
    def test_future_catalyst_tags_never_change_rating(self):
        r=fixture_report();before=digest(assess(r,'2026-01-01'))
        r['source_facts']={'future':dict(title='Future headline',published_at='2030-01-01')}
        self.assertEqual(before,digest(assess(r,'2026-01-01')))
    def test_down_successes_do_not_invent_short_pnl(self):
        r=fixture_report();s=summarize(r['groups'][0]['members'],r['windows'],'DOWN','declared')
        self.assertEqual(s['successful'],5);self.assertFalse(s['short_profit_modelled'])
        self.assertGreater(D(s['mean_net_gbp']),0) # Existing long engine, not sign-flipped profit.



class PrivateOutputTests(unittest.TestCase):
    def test_dashboard_stays_private_and_cannot_overwrite(self):
        from signal_ratings.demo import screen_fixture
        from signal_ratings.view import render_screen,ROOT
        (ROOT/'work').mkdir(exist_ok=True)
        with self.assertRaises(ValueError):render_screen(ROOT/'signals'/'forbidden.html',screen_fixture())
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            path=Path(folder)/'screen.html';render_screen(path,screen_fixture())
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):render_screen(path,screen_fixture())
    def test_data_cannot_close_the_json_script_element(self):
        from signal_ratings.demo import screen_fixture
        from signal_ratings.view import render_screen,ROOT
        data=screen_fixture();data['limitations']=['</script><script>attack()</script>']
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            path=Path(folder)/'screen.html';render_screen(path,data)
            self.assertNotIn('</script><script>attack()',path.read_text())
            self.assertIn('\\u003c/script',path.read_text())
    def test_no_source_or_execution_policy_was_weakened(self):
        from daily_prices.stooq import policy
        p=policy();self.assertFalse(p['redistribution_permitted']);self.assertFalse(p['model_training_permitted'])
        self.assertFalse(p['price_adjustments_verified']);self.assertTrue(p['private_quarantine_only'])
        for direction in ['UP','DOWN']:
            c=card(direction)
            for cost in POLICY['costs']:self.assertEqual(classify(c,cost)['execution_action'],'No Action')
    def test_retrospective_catalysts_are_not_fabricated_earlier_features(self):
        from signal_ratings.catalysts import catalogue
        ledger=dict(ledger=[dict(investigation_focus=True,instrument='NVDA',date='2024-01-02',close_change_percent='4',
              evidence=dict(sources=[{'id':'amd-2002'},{'id':'amd-outlook'}],category='multiple',explanation='SYNTHETIC',weakness='SYNTHETIC',confidence='limited'))])
        groups=catalogue(ledger)
        self.assertEqual(len(groups),1);self.assertEqual(len(groups[0]['cases']),1)
        self.assertIn('not independent validation',groups[0]['cases'][0]['selection'])
    def test_unexplained_catalysts_remain_visible(self):
        from signal_ratings.catalysts import catalogue
        ledger=dict(ledger=[dict(investigation_focus=True,instrument='NVDA',date='2024-01-02',close_change_percent='4',
              evidence=dict(sources=[],category='unexplained',explanation='Unknown.',weakness='No reliable source.',confidence='limited'))])
        self.assertEqual(catalogue(ledger)[0]['context'],'Unexplained or later-only evidence')
    def test_appending_future_bars_does_not_reselect_past_pattern_episodes(self):
        rows=[feature(i) for i in range(25)];calendar=[r['date'] for r in rows]
        short=select({'NVDA':rows[:20]},calendar[:20])[('NVDA','spike')]
        long=select({'NVDA':rows},calendar)[('NVDA','spike')]
        self.assertEqual(short,[r for r in long if r['date']<=rows[19]['date']])


if __name__=='__main__':unittest.main()
