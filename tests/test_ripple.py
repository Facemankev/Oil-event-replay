"""Reproducible exact-source slice; original canonical data are immutable."""
import csv
import json
import subprocess
import unittest
from pathlib import Path
from decimal import Decimal
from ripple.build import build

ROOT = Path(__file__).resolve().parents[1]


class RippleDataTests(unittest.TestCase):
    def test_reproducible_export_and_exact_quote_join(self):
        data = build()
        self.assertEqual(data, json.loads((ROOT/'ripple/data.json').read_text()))
        market = next(s for s in json.loads((ROOT/'data/historical/prices.json').read_text())['series'] if s['series']=='brent')
        values = {r['date']:r['value'] for r in market['observations']}
        with (ROOT/'ripple/fx-harvey-source.csv').open() as stream:
            fx = {r['Date']:r['Exchange rate'] for r in csv.DictReader(stream)}
        self.assertEqual(len(data['quotes']),34)
        for q in data['quotes']:
            self.assertEqual(q['price'],values[q['date']])
            self.assertEqual(q['gbpPerUnit'],fx[q['date']])
            self.assertGreater(Decimal(q['gbpPerUnit']),0)
        self.assertEqual(data['missing'],[{'date':'2017-09-04','reason':'fx_missing'}])
        self.assertNotIn('2017-09-04',[q['date'] for q in data['quotes']])

    def test_original_prices_events_engines_and_style_preserved(self):
        for name in ['data/historical/prices.json','data/historical/brent-daily-2006-2026.csv',
                     'data/historical/wti-daily-2006-2026.csv','world_events/seed.json',
                     'matching/engine.mjs','matching/analysis.mjs','trading/core.mjs',
                     'matching/design.css','index.html','app/index.html','paper.html']:
            original = subprocess.check_output(['git','show','6fe59ff:'+name],cwd=ROOT)
            self.assertEqual(original,(ROOT/name).read_bytes(),name)

    def test_update_clock_is_conservative_and_ripples_are_explicit_hypotheses(self):
        sources = build()['sources']
        for source in sources['context']+sources['updates']:
            self.assertGreater(source['available_from'],source['published_day'])
            self.assertEqual(source['precision'],'day')
            self.assertTrue(source['url'].startswith('https://www.eia.gov/'))
        self.assertEqual(sources['updates'][0]['published_day'],'2017-09-11')
        self.assertEqual(sources['updates'][0]['available_from'],'2017-09-12')
        self.assertGreaterEqual(len(sources['ripple_paths']),2)
        for path in sources['ripple_paths']:
            self.assertEqual(path['classification'],'hypothesis')
            self.assertEqual(len(path['stages']),3)
