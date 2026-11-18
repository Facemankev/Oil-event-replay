"""CI policy, no-empty-pass behavior and failure propagation without live services."""
import json,subprocess,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from ci.run_browser import ROOT,suites,run_suite,summary

class GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'work').mkdir(exist_ok=True)

    def test_every_PR_and_update_including_drafts_and_stacked_bases_is_covered(self):
        # JSON is a YAML subset; parse the actual workflow without another dependency.
        w=json.loads((ROOT/'.github/workflows/required-checks.yml').read_text())
        trigger=w['on']['pull_request']
        self.assertIn('opened',trigger['types']);self.assertIn('synchronize',trigger['types'])
        self.assertNotIn('branches',trigger);self.assertNotIn('paths',trigger)
        self.assertNotIn('pull_request_target',w['on'])
        self.assertEqual(w['permissions'],{'contents':'read'})
        for job in ('offline','browser'):
            checkout=next(s for s in w['jobs'][job]['steps'] if s.get('uses')=='actions/checkout@v4')
            self.assertEqual(checkout['with']['fetch-depth'],0)
        gate=w['jobs']['required'];self.assertEqual(gate['needs'],['offline','browser'])
        self.assertEqual(gate['name'],'Market Ripple required checks')
        self.assertEqual(gate['if'],'${{ always() }}')
        self.assertNotIn('continue-on-error',json.dumps(w))
        browser=w['jobs']['browser']
        self.assertEqual(browser['timeout-minutes'],35)
        install=next(s for s in browser['steps'] if s.get('name')=='Install pinned real browser engine')
        run=next(s for s in browser['steps'] if s.get('name')=='All required fixture-only browser suites')
        self.assertEqual(install['timeout-minutes'],25);self.assertEqual(run['timeout-minutes'],8)
        self.assertRegex(browser['container']['image'],r'^mcr\.microsoft\.com/playwright/python:v1\.64\.1-noble@sha256:[a-f0-9]{64}$')
        self.assertEqual(browser['env']['PLAYWRIGHT_BROWSERS_PATH'],'/ms-playwright')
        self.assertIn('playwright==1.64.1',install['run'])
        self.assertIn('executable.is_file()',install['run'])
        self.assertNotIn('playwright install --with-deps',install['run'])

    def test_matching_export_uses_the_databases_built_by_this_job(self):
        from ci.offline_checks import commands
        planned=commands()
        price=next(c[c.index('--db')+1] for c in planned if 'historical' in c)
        events=next(c[c.index('--db')+1] for c in planned if 'world_events' in c)
        exports=[c for c in planned if 'matching.build' in c]
        self.assertTrue(exports)
        for c in exports:
            self.assertEqual(c[c.index('--prices-db')+1],price)
            self.assertEqual(c[c.index('--events-db')+1],events)

    def test_required_features_have_explicit_both_engine_suites(self):
        for engine in ('chromium','webkit'):
            names={s['name'] for s in suites(engine)}
            self.assertTrue({'three-answers','free-data','simulations','learning','all-page-profiles'}.issubset(names))
        with self.assertRaises(ValueError):suites('fake')

    def test_unregistered_IPO_frontend_fails_instead_of_silently_skipping(self):
        original=Path.exists
        with patch('pathlib.Path.exists',lambda p:True if str(p)==str(ROOT/'ipo') else original(p)):
            with self.assertRaises(ValueError):suites('webkit')

    def test_nonzero_child_and_timeout_are_failed_with_reproduction_and_logs(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
            output=Path(folder);suite=dict(name='controlled',file='tests/learning_browser_test.py',engines=['chromium','webkit'])
            r=run_suite('webkit',suite,output,client=lambda *a,**k:SimpleNamespace(returncode=7))
            self.assertEqual(r['exit_code'],7);self.assertEqual(r['status'],'failed')
            self.assertIn('--only controlled',r['reproduce'])
            def timeout(*a,**kw):raise subprocess.TimeoutExpired(a[0],1)
            r=run_suite('webkit',suite,output,client=timeout)
            self.assertEqual(r['exit_code'],124);self.assertIn('failed',summary([r]))
            self.assertTrue((output/'controlled/test.log').is_file())

if __name__=='__main__':unittest.main()
