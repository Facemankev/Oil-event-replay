"""SIM-1: real corpus integration plus clearly synthetic arithmetic/chronology fixtures."""
import copy,json,unittest
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from simulations.engine import (plan,measure,portfolio,gbp_point,indexed,build_report,public_view,PROTOCOL,HERE)
from free_pilot.data import load_free_library
from world_events.events import digest


class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real=load_free_library()
        cls.report=build_report(cls.real)

    def fixture(self,prices=None):
        # Synthetic fixture only; not a historical market claim or public example.
        event=copy.deepcopy(self.real['events'][0]);event.update(id='synthetic-fixture',episode_id='fixture',targets=['brent'],
            public_day='2020-01-02',public_at='2020-01-02T10:00:00Z',historical_receipt_at=None)
        data=copy.deepcopy(self.real);data['events']=[event]
        data['sources'][event['publication_source']].update(published_day=event['public_day'],published_at=event['public_at'])
        days=[];d=date(2019,12,24)
        while len(days)<35:
            if d.weekday()<5:days.append(d.isoformat())
            d+=timedelta(days=1)
        future=[d for d in days if d>'2020-01-02']
        values=dict(zip(future,prices or [100,102,104,106,108,110]+[110]*25))
        data['observations']=[dict(instrument=m,date=d,status='numeric',value=str(values.get(d,100) if m=='brent' else 1),
                                  source_id='synthetic-fixture-only',snapshot_id='synthetic') for m in ['brent','gbpusd'] for d in days]
        return event,data

    def test_real_source_report_pins_all_cases_and_strategies(self):
        r=self.report
        self.assertEqual(r['universe_events'],51)
        self.assertEqual(r['event_market_cases'],151)
        self.assertEqual(len(r['rule_summaries']),36)
        self.assertEqual(digest(r),(HERE/'REPORT.sha256').read_text().strip())
        self.assertTrue(all(x['attempts']==151 for x in r['rule_summaries']))
        self.assertEqual(r['supported_entries'],0)
        self.assertEqual(public_view(r),json.loads((HERE/'report.json').read_text()))

    def test_gate_diagnosis_does_not_mistake_abstention_for_losing_edge(self):
        d=self.report['diagnosis']
        self.assertEqual(d['validated_no_action'],51)
        self.assertEqual(d['blocker_counts']['original_news_receipt_and_version_unproven'],51)
        self.assertEqual(d['blocker_counts']['fewer_than_eight_independent_qualified_cases'],50)
        self.assertTrue(all(not r['expected_edge_assessed'] for r in d['records']))

    def test_same_day_is_never_bought_and_exit_counts_subsequent_observations(self):
        e,d=self.fixture();p=plan(e,d,'brent');r=measure(p,d)
        self.assertEqual(r['entry_date'],'2020-01-03')
        self.assertEqual(r['exit_date'],'2020-01-10')
        self.assertEqual([x['action'] for x in r['actions']],['Hypothetical Buy']+['Hypothetical Hold']*4+['Hypothetical Sell'])

    def test_exact_costed_arithmetic_reserves_both_fees_inside_budget(self):
        e,d=self.fixture();r=measure(plan(e,d,'brent'),d)
        expected=(Decimal('5')-Decimal('.02'))/(Decimal('100')*Decimal('1.001'))*Decimal('110')*Decimal('.999')-5
        self.assertEqual(r['net_pnl_gbp'],str(expected.quantize(Decimal('.0001'))))
        self.assertEqual(r['gross_pnl_gbp'],'0.5000')
        self.assertEqual(r['reserved_exit_fee_gbp'],'0.01')

    def test_cost_sensitivities_preserve_dates_and_reduce_net_results(self):
        e,d=self.fixture();p=plan(e,d,'brent')
        rs=[measure(p,d,c) for c in PROTOCOL['costs']]
        self.assertEqual(len({(r['entry_date'],r['exit_date']) for r in rs}),1)
        self.assertEqual([Decimal(r['net_pnl_gbp']) for r in rs],sorted([Decimal(r['net_pnl_gbp']) for r in rs],reverse=True))
        self.assertEqual(rs[-1]['net_outcome'],'negative')

    def test_negative_move_exits_at_actual_observed_price_not_an_invented_stop(self):
        e,d=self.fixture([100,80,90,95,100,110]+[110]*25);r=measure(plan(e,d,'brent'),d)
        self.assertEqual(r['path'][-1]['raw_value'],'80')
        self.assertEqual(r['actions'][-1]['action'],'Hypothetical Sell')
        self.assertEqual(r['net_outcome'],'negative')
        self.assertIn('not_stop_fill',r['reason'])
        self.assertLessEqual(abs(Decimal(r['net_pnl_gbp'])),Decimal('5'))

    def test_future_prices_or_new_cases_cannot_change_an_earlier_plan(self):
        e,d=self.fixture();before=plan(e,d,'brent','momentum_up')
        changed=copy.deepcopy(d)
        for p in changed['observations']:
            if p['date']>'2020-01-02' and p['instrument']=='brent':p['value']='999'
        changed['events'].append(dict(e,id='future-not-a-training-case'))
        self.assertEqual(before,plan(e,changed,'brent','momentum_up'))

    def test_missing_future_FX_keeps_earlier_buy_and_does_not_rewrite_it(self):
        e,d=self.fixture();p=plan(e,d,'brent');before=measure(p,d)
        changed=copy.deepcopy(d)
        changed['observations']=[r for r in changed['observations'] if not (r['instrument']=='gbpusd' and r['date']=='2020-01-07')]
        r=measure(p,changed)
        self.assertEqual(r['status'],'unsettled_reference_path')
        self.assertEqual(r['actions'][0],before['actions'][0])
        self.assertIsNone(r['net_pnl_gbp'])
        self.assertNotIn('Hypothetical Sell',[a['action'] for a in r['actions']])

    def test_entry_missing_FX_is_not_repaired_by_advancing_the_date(self):
        e,d=self.fixture();d['observations']=[r for r in d['observations'] if not (r['instrument']=='gbpusd' and r['date']=='2020-01-03')]
        r=measure(plan(e,d,'brent'),d)
        self.assertEqual(r['reason'],'missing_exact_date_GBP_FX');self.assertEqual(r['actions'],[])

    def test_unavailable_future_window_does_not_erase_earlier_buy(self):
        e,d=self.fixture();d['observations']=[r for r in d['observations'] if r['date']<'2020-01-07']
        r=measure(plan(e,d,'brent'),d)
        self.assertEqual(r['status'],'unsettled_reference_path');self.assertEqual(r['actions'][0]['action'],'Hypothetical Buy')

    def test_rejects_nonpositive_references_and_oversized_or_nonfinite_budgets(self):
        e,d=self.fixture();p=plan(e,d,'brent')
        for allocation in ['6','NaN','-1']:
            with self.assertRaises(Exception):measure(p,d,allocation=allocation)
        for row in d['observations']:
            if row['instrument']=='brent' and row['date']=='2020-01-03':row['value']='-37.63'
        self.assertIn('nonpositive',measure(p,d)['reason'])

    def test_conversion_references_do_not_multiply_independent_oil_signals(self):
        e=next(e for e in self.real['events'] if e['primary_group']=='oil' and 'gbpusd' in e['targets'])
        p=plan(e,self.real,'gbpusd');self.assertEqual(p['status'],'conversion_context_not_independent_signal')
        self.assertEqual(p['hypothetical_intent'],'No Action')

    def test_USD_cash_direction_is_explicit_and_uses_reciprocal_quote(self):
        e,d=self.fixture();rows=indexed(d);rows['gbpusd']['2020-01-03']['value']='1.25'
        point,error=gbp_point(rows,'gbpusd','2020-01-03')
        self.assertIsNone(error);self.assertEqual(Decimal(point['reference_gbp']),Decimal('.8'))

    def test_missing_histories_and_delayed_first_quote_do_not_create_fake_trades(self):
        e,d=self.fixture();d['observations']=[r for r in d['observations'] if r['date']>'2020-01-20']
        r=measure(plan(e,d,'brent'),d);self.assertEqual(r['reason'],'entry_outside_predefined_delay_limit')
        d['observations']=[];self.assertEqual(measure(plan(e,d,'brent'),d)['reason'],'no_later_numeric_price')

    def test_portfolio_blocks_overlapping_episodes_and_unresolved_positions(self):
        e,d=self.fixture();p=plan(e,d,'brent');second=dict(p,event_id='other',episode_id='other',decision_bound='2020-01-04T10:00:00Z')
        r=portfolio([p,second],d);self.assertEqual(r['trades'],1);self.assertEqual(r['excluded_overlap'],1)
        d['observations']=[r for r in d['observations'] if r['date']<'2020-01-07']
        r=portfolio([p,second],d);self.assertTrue(r['unresolved_position']);self.assertIsNone(r['final_cash_gbp'])

    def test_full_default_report_keeps_real_positive_negative_and_missing_cases(self):
        cases=self.report['default_cases'];states={c['outcome'].get('net_outcome') for c in cases}
        self.assertIn('positive',states);self.assertIn('negative',states)
        self.assertTrue(any(c['outcome']['status']!='simulated_reference_path' for c in cases))
        self.assertTrue(all(c['plan']['validated_action']=='No Action' for c in cases))
        self.assertTrue(all(not b['gross_return_percent'] or b['status']=='reference_only' for b in self.report['passive_baselines']))


if __name__=='__main__':unittest.main()
