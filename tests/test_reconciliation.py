"""Actual supplied report and official table evidence; no network or credentials."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from historical import prices as p
from historical import reconcile as r


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((r.DIRECTORY/'eia-verification-new.json').read_text())
        self.web = json.loads((r.DIRECTORY/'web-evidence.json').read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report_file(self, report):
        path = self.root/'report.json';path.write_text(json.dumps(report));return path

    def test_actual_review_counts_and_reproducible_artifact(self):
        result = r.review()
        self.assertEqual(result['summary'], {'seed_numeric_observations':10368,
            'reported_matching_values':10348,'reported_value_differences':3,'primary_value_conflicts':3,
            'API_only_rows':137,'API_only_rows_blank_on_HTML':137,
            'seed_only_rows_supported_by_HTML':17,'confirmed_numeric_seed_gaps_from_HTML':0,
            'prices_changed':0,'prices_added':0,'prices_deleted':0})
        self.assertEqual(json.dumps(result,indent=2,allow_nan=False)+'\n',(r.DIRECTORY/'REVIEW.json').read_text())
        self.assertFalse(result['raw_primary_snapshot_checked_here'])
        self.assertFalse(result['canonical_data_changed'])
        self.assertFalse(result['automatic_apply_supported'])
        self.assertIsNone(result['confirmed_revision_times'])
        self.assertEqual(result['report_sha256'],'4b0b690b2a12096789386519dc82d86700b7c9dfa41d68e36a3ba31190ce618b')

    def test_three_API_changes_are_held_not_blindly_applied(self):
        changes = r.review()['series']['brent']['value_differences']
        self.assertEqual([(v['date'],v['seed_value'],v['reported_API_value'],v['HTML_value']) for v in changes],
            [('2016-12-28','54.95','53.93','54.95'),('2016-12-29','54.97','54.95','54.97'),('2018-04-16','72.05','73.18','72.05')])
        self.assertTrue(all(v['recommended_action']=='retain_seed_pending_source_resolution' and not v['applied'] for v in changes))
        self.assertEqual(r.review()['series']['wti']['value_differences'],[])

    def test_missing_dates_are_not_deleted_filled_or_assumed_holidays(self):
        dates = [v for s in r.review()['series'].values() for v in s['date_review']]
        API_only = [v for v in dates if v['origin']=='API_only']
        self.assertEqual(len(API_only),137)
        self.assertTrue(all(v['HTML_value'] is None and v['API_value_state']=='unknown_from_summary' for v in API_only))
        self.assertTrue(all(v['recommended_action']=='leave_missing_no_filling' for v in API_only))
        omitted = [v for v in dates if v['origin']=='seed_only']
        self.assertTrue(all(v['HTML_value']==v['seed_value'] and v['recommended_action']=='retain_seed_no_deletion' for v in omitted))
        holidays = [v for v in API_only if v['calendar_label']]
        self.assertEqual(len(holidays),7)
        self.assertTrue(all(not v['holiday_closure_confirmed'] for v in dates))

    def test_wrong_seed_status_counts_dates_or_prices_fail_closed(self):
        mutations = [lambda x:x.update(primary_reconciliation_succeeded=False),
            lambda x:x.update(verified=True),
            lambda x:x['series']['brent'].update(seed_sha256='0'*64),
            lambda x:x['series']['brent']['primary_comparison'].update(equal_values=5222),
            lambda x:x['series']['brent']['primary_comparison']['missing_from_seed'].append('2030-01-01'),
            lambda x:x['series']['brent']['primary_comparison']['discrepancies'][0].update(seed='1'),
            lambda x:x['series']['brent']['primary_comparison']['missing_from_primary'].append('2014-09-30')]
        for mutation in mutations:
            report=copy.deepcopy(self.report);mutation(report)
            with self.subTest(mutation=mutation),self.assertRaises((p.DataError,ValueError)):
                r.validate_report(report)

    def test_evidence_calendar_and_duplicate_cells_are_validated(self):
        for change in [lambda x:x['rows'][0].update(week_start='2020-01-01'),
                       lambda x:x['rows'][0].update(url='https://example.org/not-EIA'),
                       lambda x:x['rows'].append(x['rows'][0])]:
            web=copy.deepcopy(self.web);change(web)
            with self.assertRaises(p.DataError):r.web_cells(web)

    def primary_fixture(self, extra_value=None):
        """Full-size synthetic transport fixture; never publish as fetched data."""
        report=copy.deepcopy(self.report)
        db=p.open_db(self.root/'audit.sqlite')
        seeds=r.validate_report(report)
        snapshots=[]
        for i,market in enumerate(p.SERIES):
            changes={v['date']:v['primary'] for v in report['series'][market]['primary_comparison']['discrepancies']}
            omit=set(report['series'][market]['primary_comparison']['missing_from_primary'])
            records=[{'period':d,'value':changes.get(d,v),'series':p.SERIES[market][1],'units':'Dollars per Barrel'} for d,v in seeds[market].items() if d not in omit]
            records += [{'period':d,'value':extra_value,'series':p.SERIES[market][1],'units':'Dollars per Barrel'} for d in report['series'][market]['primary_comparison']['missing_from_seed']]
            payload=json.dumps([{'response':{'frequency':'daily','total':len(records),'data':records}}]).encode()
            report['series'][market]['primary_sha256']=r.digest(payload)
            rows=p.validate_rows([(v['period'],v['value']) for v in records])
            snapshots.append(dict(market=market,kind='eia',source_url=p.ENDPOINT,
                revision='SYNTHETIC TEST FIXTURE ONLY',retrieved_at=report['primary_retrieved_at'][i],payload=payload,rows=rows))
        p.import_snapshots(db,snapshots);db.close()
        return report,self.root/'audit.sqlite'

    def test_optional_audit_snapshot_distinguishes_explicit_null_without_key_or_writes(self):
        report,path=self.primary_fixture()
        before=path.read_bytes()
        result=r.review(self.report_file(report),primary_db=path)
        dates=[v for s in result['series'].values() for v in s['date_review'] if v['origin']=='API_only']
        self.assertTrue(result['raw_primary_snapshot_checked_here'])
        self.assertTrue(all(v['classification']=='explicit_API_missing_and_HTML_blank' for v in dates))
        self.assertTrue(all(v['API_value_state']=='explicit_missing' for v in dates))
        self.assertEqual(path.read_bytes(),before)
        # A database from another fetch must not be treated as this report's evidence.
        with self.assertRaises(p.DataError):r.review(primary_db=path)

    def test_numeric_zero_and_negative_API_only_rows_are_conflicts_not_holiday_fills(self):
        for value in ['0','-1']:
            report,path=self.primary_fixture(extra_value=value)
            result=r.review(self.report_file(report),primary_db=path)
            dates=[v for s in result['series'].values() for v in s['date_review'] if v['origin']=='API_only']
            self.assertTrue(all(v['API_value_state']=='numeric' and v['API_value']==value for v in dates))
            self.assertTrue(all(v['classification']=='primary_source_conflict' and v['recommended_action']=='leave_missing_no_filling' for v in dates))
            self.assertFalse(result['canonical_data_changed'])
            path.unlink()

    def test_tampered_primary_payload_or_stored_rows_rejected(self):
        for target in ['payload','rows']:
            report,path=self.primary_fixture()
            db=p.open_db(path)
            if target=='payload':db.execute("UPDATE price_snapshots SET payload=?",(b'[]',))
            else:db.execute("UPDATE price_observations SET value='999' WHERE observation_date='2006-01-03'")
            db.close()
            with self.subTest(target=target),self.assertRaises(p.DataError):
                r.review(self.report_file(report),primary_db=path)
            path.unlink()

    def test_CLI_refuses_existing_outputs_and_never_changes_source_data(self):
        paths=[r.ROOT/'data/historical/brent-daily-2006-2026.csv',r.ROOT/'data/historical/wti-daily-2006-2026.csv',r.ROOT/'data/historical/prices.json']
        hashes={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        out=self.root/'review.json'
        command=[sys.executable,'-m','historical.reconcile','--output',str(out)]
        subprocess.run(command,cwd=r.ROOT,check=True,capture_output=True)
        first=out.read_bytes()
        self.assertEqual(subprocess.run(command,cwd=r.ROOT,capture_output=True).returncode,2)
        self.assertEqual(out.read_bytes(),first)
        for path,sha in hashes.items():self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),sha)


if __name__=='__main__':unittest.main()
