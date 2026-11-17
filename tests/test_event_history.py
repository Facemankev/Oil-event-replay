"""Real-snapshot integration plus explicitly synthetic transport/price edge cases."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from event_history.library import ROOT, GROUPS, load_library, validate_library, ValidationError
from event_history.database import connect, import_library, read_library
from event_history.engine import (visible_facts, match_history, historical_decision, response,
                                  evaluate, drilldown, summarize, publication, iso)


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_library()
        cls.events = {e['id']: e for e in cls.data['events']}
        (ROOT / 'work').mkdir(exist_ok=True)

    def test_actual_source_counts_and_six_group_coverage(self):
        self.assertEqual(len(self.data['events']), 51)
        self.assertEqual(len(self.data['observations']), 16320)
        self.assertEqual(sum(p['status'] == 'numeric' for p in self.data['observations']), 15618)
        self.assertEqual(len(self.data['reported_reactions']), 13)
        groups = {self.data['instruments'][m]['group'] for e in self.data['events'] for m in e['targets']}
        self.assertEqual(groups, set(GROUPS))

    def test_repeat_import_is_safe_and_readback_is_exact(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            path = Path(tmp) / 'history.sqlite'
            db = connect(path)
            try:
                first = import_library(db, self.data)
                repeated = import_library(db, self.data)
                self.assertEqual(first['inserted_events'], 51)
                self.assertEqual(repeated['reused_events'], 51)
                self.assertEqual(repeated['inserted_observation_rows'], 0)
                self.assertEqual(db.execute('SELECT count(*) FROM observations').fetchone()[0], 16320)
            finally:
                db.close()
            self.assertEqual(read_library(path), self.data)

    def test_conflicting_event_revision_rolls_back_without_overwrite(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            db = connect(Path(tmp) / 'history.sqlite')
            import_library(db, self.data)
            changed = copy.deepcopy(self.data)
            changed['events'][-1]['title'] = 'Reviewed correction fixture'
            with self.assertRaises(ValidationError):
                import_library(db, changed)
            self.assertEqual(db.execute('SELECT count(*) FROM import_runs').fetchone()[0], 1)
            changed['events'][-1]['revision'] = 2
            import_library(db, changed)
            self.assertEqual(db.execute('SELECT count(*) FROM event_versions').fetchone()[0], 52)
            db.close()

    def test_old_dataset_revision_can_be_read_after_an_incremental_event_update(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            path = Path(tmp) / 'history.sqlite'
            db = connect(path)
            initial = import_library(db, self.data)
            changed = copy.deepcopy(self.data)
            changed['events'][-1]['revision'] = 2
            changed['events'][-1]['title'] = 'Revised fixture title'
            import_library(db, changed)
            db.close()
            self.assertEqual(read_library(path, initial['dataset_sha256']), self.data)
            self.assertEqual(read_library(path)['events'][-1]['revision'], 2)

    def test_wrong_database_and_canonical_paths_are_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'work') as tmp:
            path = Path(tmp) / 'other.sqlite'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE unrelated(x)')
            before = path.read_bytes()
            with self.assertRaises(ValidationError):
                connect(path)
            self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(ValidationError):
            connect(ROOT / 'data' / 'prices.sqlite')

    def test_occurrence_supporting_publication_and_actual_receipt_stay_distinct(self):
        event = self.events['pfizer-2020-interim']
        self.assertEqual(event['occurred_day'], '2020-11-08')
        self.assertEqual(event['public_day'], '2020-11-09')
        self.assertIsNone(event['public_at'])  # printed clock has no verified timezone
        self.assertIsNone(event['historical_receipt_at'])
        self.assertIsNone(visible_facts(event, self.data, '2020-11-10T23:59:59Z'))
        self.assertIsNotNone(visible_facts(event, self.data, '2020-11-11T00:00:00Z'))
        self.assertIsNone(visible_facts(event, self.data, '2020-11-11T00:00:00Z', require_receipt=True))
        earlier = drilldown(self.events['tesla-2018-governance'], self.data, '2018-09-30T00:00:00Z')
        self.assertNotIn('settlement', json.dumps(earlier['weaknesses']).lower())

    def test_after_close_timezone_is_not_relabelled_as_a_daytime_announcement(self):
        event = self.events['pfizer-2020-eua']
        self.assertEqual(iso(publication(event, self.data)), '2020-12-12T02:41:00Z')
        self.assertIsNone(visible_facts(event, self.data, '2020-12-11T21:00:00Z'))
        self.assertIsNotNone(visible_facts(event, self.data, '2020-12-12T02:41:00Z'))

    def test_future_fact_price_and_report_mutation_cannot_change_earlier_decision(self):
        event = self.events['harvey-2017-texas']
        cutoff = '2017-08-27T12:00:00Z'
        baseline = historical_decision(event, self.data, 'brent', cutoff)
        changed = copy.deepcopy(self.data)
        for e in changed['events']:
            if e.get('public_day') and e['public_day'] > '2017-08-27':
                e.update(title='FUTURE CONTENT', category='weather', mechanism='landfall',
                         episode_id=event['episode_id'], severity=None)
        for p in changed['observations']:
            if p['date'] >= '2017-08-27':
                p['value'] = '999999.00' if p['status'] == 'numeric' else None
        changed['reported_reactions'].clear()
        self.assertEqual(historical_decision(event, changed, 'brent', cutoff), baseline)

    def test_adding_future_cases_and_prices_cannot_change_earlier_selection(self):
        event = self.events['fed-2020-emergency-cut']
        cutoff = '2020-03-03T16:00:00Z'
        baseline = historical_decision(event, self.data, 'nasdaq_composite', cutoff)
        changed = copy.deepcopy(self.data)
        changed['events'] = [e for e in changed['events'] if not e.get('public_day') or e['public_day'] <= '2020-03-03']
        changed['observations'] = [p for p in changed['observations'] if p['date'] < '2020-03-03']
        self.assertEqual(historical_decision(event, changed, 'nasdaq_composite', cutoff), baseline)

    def test_outcome_blind_ranking_does_not_change_when_past_returns_are_reversed(self):
        event = self.events['harvey-2017-texas']
        cutoff = '2017-08-27T12:00:00Z'
        selected = match_history(event, self.data, 'brent', cutoff)
        changed = copy.deepcopy(self.data)
        for p in changed['observations']:
            if p['status'] == 'numeric':
                p['value'] = str(Decimal('10000') - Decimal(p['value']))
        self.assertEqual(match_history(event, changed, 'brent', cutoff), selected)

    def test_same_drug_policy_episode_is_never_an_independent_analogue(self):
        later = self.events['biogen-2019-reanalysis']
        selected = match_history(later, self.data, 'BIIB', '2019-10-25T00:00:00Z')
        self.assertNotIn('biogen-2019-futility', [m['id'] for m in selected['matches']])
        self.assertIn({'id': 'biogen-2019-futility', 'reason': 'self_or_same_episode'}, selected['excluded'])
        view = drilldown(later, self.data, '2019-10-25T00:00:00Z')
        self.assertIn('biogen-2019-futility', [e['id'] for e in view['related_same_episode']])

    def test_opposite_policy_direction_is_a_weak_cross_check(self):
        event = self.events['boe-2017-november-hike']
        selected = match_history(event, self.data, 'gbpusd', '2017-11-06T00:00:00Z')
        cut = next(m for m in selected['matches'] if m['id'] == 'boe-2016-august-cut')
        self.assertEqual(cut['similarity'], 'Weak')
        self.assertIn('different_mechanism', cut['weaknesses'])
        self.assertNotIn(cut['id'], selected['selected'])

    def test_same_announcement_mechanisms_have_real_earlier_cross_checks_but_no_price_permission(self):
        event = self.events['nvidia-2024-q4-outlook']
        result = match_history(event, self.data, 'NVDA', '2024-02-24T00:00:00Z')
        self.assertEqual({m['id'] for m in result['matches']},
                         {'nvidia-2023-q1-outlook', 'nvidia-2023-q2-outlook'})
        self.assertTrue(all(m['core_comparable'] for m in result['matches']))
        self.assertEqual(result['selected'], [])  # No verified adjusted response schedule.
        earlier = match_history(self.events['biogen-2019-futility'], self.data, 'BIIB', '2019-03-23T00:00:01Z')
        self.assertEqual([m['id'] for m in earlier['matches']], ['merck-2017-epoch'])
        self.assertEqual(earlier['matches'][0]['comparison_instrument'], 'MRK')
        self.assertTrue(any('different_issuer' in gap for gap in earlier['matches'][0]['weaknesses']))
        self.assertEqual(earlier['selected'], [])  # No fabricated MRK-to-BIIB price transfer.

    def test_exact_horizon_prices_and_same_date_FX_formula(self):
        event = self.events['harvey-2017-texas']
        row = response(event, self.data, 'brent', 5, '2026-11-17T00:00:00Z')
        self.assertEqual(len(row['observations']), 6)
        expected = (Decimal(row['end']) / Decimal(row['baseline']) - 1) * 100
        self.assertEqual(Decimal(row['change_percent']), expected)
        self.assertFalse(row['point_in_time_safe'])
        fx = {p['date']: Decimal(p['value']) for p in self.data['observations']
              if p['instrument'] == 'gbpusd' and p['status'] == 'numeric'}
        expected_gbp = ((Decimal(row['end']) / fx[row['end_date']]) /
                        (Decimal(row['baseline']) / fx[row['baseline_date']]) - 1) * 100
        self.assertEqual(Decimal(row['GBP']['change_percent']), expected_gbp)
        # Exact missing intermediate Fed ND cannot be skipped to a later rate.
        ida = response(self.events['ida-2021-louisiana'], self.data, 'brent', 10, '2026-11-17T00:00:00Z')
        self.assertEqual(ida['GBP']['status'], 'missing_exact_date_FX')
        self.assertIn('2021-09-06', ida['GBP']['missing_dates'])

    def test_zero_and_negative_prices_never_become_infinite_or_invented_returns(self):
        changed = copy.deepcopy(self.data)
        event = self.events['harvey-2017-texas']
        original = response(event, changed, 'brent', 1, '2026-11-17T00:00:00Z')
        for value in ('0.00', '-2.00'):
            for p in changed['observations']:
                if p['instrument'] == 'brent' and p['date'] == original['baseline_date']:
                    p['value'] = value
            row = response(event, changed, 'brent', 1, '2026-11-17T00:00:00Z')
            self.assertIsNone(row['change_percent'])
            self.assertIsNotNone(row['absolute_change'])

    def test_missing_adjusted_equity_series_is_not_filled_from_reported_percent(self):
        event = self.events['nvidia-2023-q1-outlook']
        view = drilldown(event, self.data, '2026-11-17T00:00:00Z')
        self.assertTrue(all(r['change_percent'] is None for r in view['reactions']['markets']['NVDA']))
        self.assertEqual(view['reported_reactions'][0]['reported_percent'], '24.37')
        self.assertFalse(view['reported_reactions'][0]['raw_price_series_verified'])

    def test_opposite_gold_and_pharma_reports_and_no_action_policy_hold_are_retained(self):
        reactions = self.data['reported_reactions']
        self.assertEqual({r['reported_percent'] for r in reactions if r['instrument'] == 'gold_futures_reported'}, {'3.1', '-5'})
        self.assertEqual({r['reported_percent'] for r in reactions if r['instrument'] == 'BIIB'}, {'-29.2', '26.11'})
        hold = self.events['fed-2023-june-hold']
        self.assertEqual(hold['severity']['value'], 0)  # Policy size, NOT zero market return.
        self.assertEqual(historical_decision(hold, self.data, 'nasdaq_composite', '2023-06-14T18:00:01Z')['action'], 'No Action')

    def test_malformed_provenance_duplicate_events_and_nonfinite_reports_are_rejected(self):
        for change in ('source', 'duplicate', 'nonfinite', 'receipt'):
            data = copy.deepcopy(self.data)
            if change == 'source':
                data['events'][-1]['publication_source'] = 'missing'
            elif change == 'duplicate':
                data['events'].append(data['events'][0])
            elif change == 'nonfinite':
                data['reported_reactions'][0]['reported_percent'] = 'NaN'
            else:
                data['events'][-1]['historical_receipt_at'] = '2020-01-01T00:00:00Z'
            with self.assertRaises(ValidationError):
                validate_library(data)

    def test_summary_denominators_do_not_count_missing_as_flat(self):
        stats = summarize(['-1', '0', '3', None])
        self.assertEqual(stats, dict(count=3, median='0', minimum='-1', maximum='3', positive=1, negative=1, flat=1))

    def test_response_is_hidden_before_its_end_day_and_no_causal_ripple_is_claimed(self):
        event = self.events['harvey-2017-texas']
        row = response(event, self.data, 'brent', 20, '2017-08-27T00:00:00Z')
        self.assertIsNone(row['change_percent'])
        view = drilldown(event, self.data, '2026-11-17T00:00:00Z')
        self.assertEqual([p['order'] for p in view['ripple_paths']], [1, 2, 3])
        self.assertTrue(all(not p['measured_effect_isolated'] for p in view['ripple_paths']))


if __name__ == '__main__':
    unittest.main()
