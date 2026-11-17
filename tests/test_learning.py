"""LEARN-1 real-corpus integration and explicitly synthetic learning controls."""
import copy,json,sqlite3,tempfile,unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from learning.engine import (PROTOCOL,HERE,fit,prediction,prepare,assess,build_report,public_view,select_events)
from learning.journal import connect,record_predictions,record_settlements
from learning.__main__ import run
from free_pilot.data import load_free_library
from event_history.library import ROOT
from event_history.engine import publication
from world_events.events import digest


class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_free_library();cls.prepared=prepare(cls.data);cls.report=build_report(cls.data)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.directory=Path(self.tmp.name)/'journal'
        self.addCleanup(self.tmp.cleanup)

    def synthetic(self):
        # Synthetic rising paths ONLY for algorithm tests, never published as history.
        data=copy.deepcopy(self.data);data['events']=[];data['observations']=[]
        base=copy.deepcopy(self.data['events'][0])
        for year in range(2010,2023):
            bound=date(year,1,4);sid=f'synthetic-only-{year}'
            source=copy.deepcopy(data['sources'][base['publication_source']]);source.update(id=sid,published_day=bound.isoformat(),published_at=bound.isoformat()+'T12:00:00Z')
            data['sources'][sid]=source
            e=copy.deepcopy(base);e.update(id=sid,episode_id=sid,publication_source=sid,source_ids=[sid],
                public_day=bound.isoformat(),public_at=source['published_at'],targets=['brent'],category='weather',primary_group='oil')
            data['events'].append(e)
            days=[];day=bound-timedelta(days=12)
            while len(days)<55:
                if day.weekday()<5:days.append(day.isoformat())
                day+=timedelta(days=1)
            for i,day in enumerate(days):
                for market,value in [('brent',str(100+2*i)),('gbpusd','1')]:
                    data['observations'].append(dict(instrument=market,date=day,status='numeric',value=value,
                        source_id=sid,snapshot_id='synthetic-only'))
        return data

    def test_real_report_reproduces_counts_and_refuses_a_forecast(self):
        r=self.report;s=r['summary']
        self.assertEqual(digest(r),(HERE/'REPORT.sha256').read_text().strip())
        self.assertEqual(public_view(r),json.loads((HERE/'report.json').read_text()))
        self.assertEqual((s['retained_test_events'],s['research_watch'],s['research_no_action']),(21,4,17))
        self.assertEqual((s['positive'],s['negative'],s['missing_or_unsettled_signals']),(1,1,2))
        self.assertEqual(s['qualified_candidate_cohorts'],0);self.assertFalse(s['repeatable_pattern_established'])
        self.assertIsNone(s['calibration']);self.assertEqual(s['supported_entries'],0)

    def test_all_candidate_training_and_validation_outcomes_mature_before_boundaries(self):
        for model in self.prepared['locked']['models'].values():
            for m in model['training_candidates']:
                self.assertTrue(all(d<PROTOCOL['validation_from'] for d in m['outcome_end_dates']))
            for v in model['validation_candidates']:
                self.assertTrue(all(d<PROTOCOL['test_from'] for d in v['validation']['outcome_end_dates']))
        self.assertEqual(self.prepared['locked']['test_outcomes_used'],0)

    def test_test_prices_features_and_new_test_cases_cannot_change_fitting(self):
        changed=copy.deepcopy(self.data)
        for p in changed['observations']:
            if p['date']>=PROTOCOL['test_from'] and p['status']=='numeric':p['value']='99.99'
        for e in changed['events']:
            if publication(e,changed).date().isoformat()>=PROTOCOL['test_from']:
                e.update(title='Future text mutation',category='invented_future_label',location=['ZZ'])
        extra=copy.deepcopy(next(e for e in self.data['events'] if e['id']=='ida-2021-louisiana'));extra['id']='future-duplicate'
        changed['events'].append(extra)
        self.assertEqual(fit(self.data),fit(changed))

    def test_mutating_validation_never_changes_training_candidate_metrics(self):
        changed=copy.deepcopy(self.data)
        for p in changed['observations']:
            if PROTOCOL['validation_from']<=p['date']<PROTOCOL['test_from'] and p['status']=='numeric':p['value']='95.00'
        after=fit(changed)
        for key,m in self.prepared['locked']['models'].items():
            self.assertEqual(m['training_candidates'],after['models'][key]['training_candidates'])

    def test_future_mutations_preserve_the_complete_earlier_prediction_identity(self):
        event=next(e for e in self.data['events'] if e['id']=='opec-2020-april')
        before=prediction(event,self.data,self.prepared['locked']);changed=copy.deepcopy(self.data)
        for p in changed['observations']:
            if p['date']>before['simulated_decision_bound'][:10] and p['status']=='numeric':p['value']='200.00'
        after=prediction(event,changed,fit(changed))
        self.assertEqual(before,after)

    def test_a_working_synthetic_learner_can_qualify_but_never_enables_execution(self):
        data=self.synthetic();r=build_report(data)
        models=r['locked']['models'];self.assertTrue(models['brent/weather']['selected'])
        self.assertGreater(r['summary']['research_watch'],0)
        self.assertTrue(all(row['prediction']['validated_action']=='No Action' for row in r['records']))
        self.assertTrue(all(row['prediction']['probability'] is None for row in r['records']))
        self.assertFalse(r['summary']['repeatable_pattern_established'])

    def test_embargo_episode_and_boundary_purge_are_outcome_blind(self):
        data=self.synthetic();old=copy.deepcopy(data['events'][0]);old.update(id='same-episode-copy')
        data['events'].append(old)
        selected,excluded=select_events(data,'2010-01-01','2016-01-01')
        self.assertEqual(len(selected),6);self.assertTrue(any(x['reason']=='same_episode_or_context_response_embargo' for x in excluded))
        e=copy.deepcopy(data['events'][0]);sid='late-fixture';data['sources'][sid]={**data['sources'][e['publication_source']], 'published_day':'2015-12-20','published_at':'2015-12-20T12:00:00Z'}
        e.update(id=sid,episode_id=sid,publication_source=sid);data['events'].append(e)
        self.assertIn('fold_boundary_maturity_purge',[x['reason'] for x in select_events(data,'2010-01-01','2016-01-01')[1]])

    def test_no_future_or_unrelated_category_becomes_a_model(self):
        event=next(e for e in self.data['events'] if e['id']=='nvidia-2024-q4-outlook')
        p=prediction(event,self.data,self.prepared['locked'])
        self.assertEqual(p['research_action'],'No Action');self.assertIsNone(p['rule'])
        self.assertEqual(p['reason'],'no_prior_same_market_category_model')

    def test_missing_marks_are_unknown_not_losing_or_profitable_labels(self):
        records=self.report['records'];missing=[r for r in records if r['prediction']['research_action']=='Watch' and r['outcome']['status']!='simulated_reference_path']
        self.assertEqual(len(missing),2);self.assertTrue(all(r['outcome']['net_pnl_gbp'] is None for r in missing))
        self.assertEqual(self.report['summary']['directional_false_positives'],1)

    def test_frozen_plan_is_used_during_assessment(self):
        with patch('learning.engine.plan',side_effect=AssertionError('Baseline is the only post-lock plan')):
            # Candidate settlement itself must not reconstruct/reclassify the frozen signal.
            p=self.prepared;one=copy.deepcopy(p)
            index=next(i for i,x in enumerate(p['predictions']) if x['event_id']=='opec-2020-april')
            for k in ['events','predictions','plans']:one[k]=[p[k][index]]
            # Supply only a fixed baseline plan through a controlled wrapper.
        from simulations.engine import plan as fixed_plan
        with patch('learning.engine.plan',wraps=fixed_plan) as spy:
            assess(one,self.data)
            self.assertEqual(spy.call_count,1)
            self.assertEqual(spy.call_args.args[-2:],('event_long',5))

    def test_prices_after_report_cutoff_cannot_settle_or_change_holdout_outcomes(self):
        changed=copy.deepcopy(self.data)
        template=copy.deepcopy(next(r for r in changed['observations'] if r['instrument']=='brent'))
        template.update(date='2026-11-18',value='99999',status='numeric')
        changed['observations'].append(template)
        self.assertEqual(assess(self.prepared,self.data),assess(self.prepared,changed))

    def test_committed_predictions_precede_any_test_outcome_read(self):
        def checked(prepared,data):
            db=connect(self.directory)
            try:self.assertEqual(db.execute('SELECT count(*) FROM predictions').fetchone()[0],len(prepared['predictions']))
            finally:db.close()
            return assess(prepared,data)
        r,j=run(self.data,self.directory,clock=lambda:'2026-11-17T23:30:00Z',assessor=checked)
        self.assertEqual(j['predictions']['new_predictions'],21)
        self.assertEqual(j['settlements']['new_settlements'],21)
        db=connect(self.directory)
        self.assertTrue(all(row[0]=='2026-11-17T23:30:00Z' for row in db.execute('SELECT recorded_at FROM predictions')))
        db.close()

    def test_repeat_run_deduplicates_and_never_changes_first_record_time(self):
        first=record_predictions(self.directory,self.prepared,clock=lambda:'2026-11-17T23:30:00Z')
        second=record_predictions(self.directory,self.prepared,clock=lambda:'2026-11-17T23:31:00Z')
        self.assertEqual(first['new_predictions'],21);self.assertEqual(second['new_predictions'],0)
        db=connect(self.directory);self.assertEqual({r[0] for r in db.execute('SELECT recorded_at FROM predictions')},{'2026-11-17T23:30:00Z'});db.close()

    def test_journal_triggers_refuse_updates_deletes_and_forged_predictions(self):
        record_predictions(self.directory,self.prepared)
        db=connect(self.directory)
        for sql in ['DELETE FROM predictions','UPDATE predictions SET payload=\'{}\'','DELETE FROM models']:
            with self.assertRaises(sqlite3.DatabaseError):db.execute(sql)
        db.close();bad=copy.deepcopy(self.prepared);bad['predictions'][0]['validated_action']='Buy'
        with self.assertRaises(Exception):record_predictions(self.directory,bad)

    def test_revised_later_outcome_appends_without_overwriting_prediction_or_old_outcome(self):
        record_predictions(self.directory,self.prepared);assessed=assess(self.prepared,self.data)
        first=record_settlements(self.directory,assessed)
        changed=copy.deepcopy(assessed);changed['records'][0]['outcome']['revision_note']='Synthetic revision test only'
        second=record_settlements(self.directory,changed)
        self.assertEqual(first['new_settlements'],21);self.assertEqual(second['new_settlements'],1)
        db=connect(self.directory);self.assertEqual(db.execute('SELECT count(*) FROM predictions').fetchone()[0],21);self.assertEqual(db.execute('SELECT count(*) FROM settlements').fetchone()[0],22);db.close()

    def test_settlement_requires_prior_prediction_and_other_databases_are_preserved(self):
        with self.assertRaises(Exception):record_settlements(self.directory,assess(self.prepared,self.data))
        other=Path(self.tmp.name)/'unrelated';other.mkdir();path=other/'predictions.sqlite'
        with sqlite3.connect(path) as db:db.execute('CREATE TABLE unrelated(x)')
        before=path.read_bytes()
        with self.assertRaises(Exception):connect(other)
        self.assertEqual(path.read_bytes(),before)
        with self.assertRaises(Exception):connect(ROOT/'data')


if __name__=='__main__':unittest.main()
