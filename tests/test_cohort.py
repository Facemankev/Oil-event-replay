"""New horizons reuse PR #16 calculations and preserve both data foundations."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from matching import build,traits
from world_events import events

ROOT=Path(__file__).resolve().parents[1]
class CohortTests(unittest.TestCase):
    def setUp(self):
        self.events=events.load_seed()
        self.event=next(e for e in self.events if e['id']=='ike-2008-galveston')
        self.series={s['series']:s for s in json.loads((ROOT/'data/historical/prices.json').read_text())['series']}

    def test_requested_horizons_preserve_exact_observations_and_missing_rules(self):
        actual=build.reactions(self.event,self.series,(1,3,5,10,20))
        for market,rows in actual['markets'].items():
            self.assertEqual([r['days'] for r in rows],[1,3,5,10,20])
            source=self.series[market]['observations']
            after=[r for r in source if r['date']>'2008-09-13']
            for row in rows:
                self.assertEqual(row['end_date'],after[row['days']-1]['date'])
                self.assertEqual(row['end'],after[row['days']-1]['value'])
                self.assertEqual(row['verification'],'provisional_seed')
                self.assertFalse(row['point_in_time_safe'])
        missing=copy.deepcopy(self.series)
        next(r for r in missing['wti']['observations'] if r['date']=='2008-09-15')['value']=None
        self.assertTrue(all(r['status']=='explicit_missing_observation' for r in build.reactions(self.event,missing,(1,3,5,10,20))['markets']['wti']))
        for horizon in [(0,), (True,), (3,1), (1,1), (31,)]:
            with self.assertRaises(events.ValidationError):build.reactions(self.event,self.series,horizon)

    def test_six_measurements_are_pinned_contemporaneous_primary_facts(self):
        records=traits.load(ROOT/'matching/traits.json');self.assertEqual(len(records),6)
        for event in self.events:
            extra=traits.attach(event,build.MECHANISMS[event['id']],records)
            if event['category']=='weather':
                self.assertIsNotNone(extra['severity'])
                lag=(events.instant(event['first_public']['at'])-events.instant(extra['severity']['published_at'])).total_seconds()
                self.assertTrue(0<=lag<=6*3600)
            else:self.assertIsNone(extra['severity'])
        self.assertEqual(records['harvey-2017-texas']['value'],125) # 16:00 advisory, not later best-track/landfall wind.
        changed=copy.deepcopy(self.event);changed['revision']=2
        with self.assertRaises(events.ValidationError):traits.attach(changed,'landfall',records)

    def test_tampered_measurements_fail_and_original_seed_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            data=json.loads((ROOT/'matching/traits.json').read_text());data['measurements'][0]['value']=200
            path=Path(folder)/'traits.json';path.write_text(json.dumps(data))
            with self.assertRaises(events.ValidationError):traits.load(path)
        original=json.loads((ROOT/'world_events/seed.json').read_text())['events']
        self.assertTrue(all('severity' not in e for e in original))
        self.assertEqual((ROOT/'matching/design.css').read_bytes(),(ROOT/'.claude/skills/market-ripple-design/design.css').read_bytes())

if __name__=='__main__':unittest.main()
