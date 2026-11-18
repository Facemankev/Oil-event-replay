"""DATA-2 source/SQLite/frequency/leakage regressions; synthetic mutations labelled."""
import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from free_pilot.data import load_free_library
from simulations.engine import plan
from learning.engine import fit
from event_history.library import ROOT
from data_expansion.library import HERE,load_bundle,validate,expanded_library,period_bounds
from data_expansion.database import connect,import_bundle,counts,query,revisions,read_bundle
from data_expansion.evaluate import build_report,ipo_reaction
from data_expansion.probe import probe,ENDPOINTS


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'work').mkdir(exist_ok=True);cls.bundle=load_bundle();cls.data=load_free_library()

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'references.sqlite';self.db=connect(self.path);self.addCleanup(self.db.close)

    def test_primary_capture_counts_known_values_and_no_daily_masquerade(self):
        b=self.bundle;self.assertEqual(len(b['averages']),99)
        self.assertEqual(len({(r['instrument'],r['frequency'],r['period']) for r in b['averages']}),51)
        june=next(r for r in b['averages'] if r['instrument']=='wb-gold-average' and r['period']=='2020-06')
        self.assertEqual(june['value'],'1732');self.assertEqual(june['unit'],'USD/troy_ounce')
        self.assertEqual({s['license'] for s in b['sources'].values()},{'CC-BY-4.0'})
        self.assertFalse(any(s['original_version_verified'] for s in b['sources'].values()))

    def test_import_is_idempotent_and_reads_actual_SQLite_contents(self):
        first=import_bundle(self.db,self.bundle);second=import_bundle(self.db,self.bundle)
        self.assertEqual(first['inserted_rows'],110);self.assertEqual(second['inserted_rows'],0)
        self.assertEqual(second['publication_values'],99);self.assertEqual(second['ipo_versions'],8)
        b=read_bundle(self.db);self.assertEqual(sorted(b['averages'],key=lambda r:(r['instrument'],r['frequency'],r['period'],r['source_id'])),sorted(self.bundle['averages'],key=lambda r:(r['instrument'],r['frequency'],r['period'],r['source_id'])))
        self.assertEqual(len(b['ipos']),8)

    def test_foreign_database_and_canonical_path_are_refused_before_mutation(self):
        other=Path(self.tmp.name)/'other.sqlite'
        with sqlite3.connect(other) as db:db.execute('CREATE TABLE historical_price(value TEXT)')
        before=other.read_bytes()
        with self.assertRaises(Exception):connect(other)
        self.assertEqual(before,other.read_bytes())
        with self.assertRaises(Exception):connect(ROOT/'data'/'must-not-create.sqlite')
        self.assertFalse((ROOT/'data'/'must-not-create.sqlite').exists())

    def test_update_and_delete_are_forbidden_for_original_references(self):
        import_bundle(self.db,self.bundle)
        for table in ('identity','sources','averages','ipo_facts'):
            with self.assertRaises(sqlite3.DatabaseError):self.db.execute('DELETE FROM '+table)
            column='value' if table=='averages' else 'marker' if table=='identity' else 'payload'
            with self.assertRaises(sqlite3.DatabaseError):self.db.execute(f'UPDATE {table} SET {column}={column}')

    def test_changed_cell_needs_new_capture_and_is_atomic(self):
        import_bundle(self.db,self.bundle);before=counts(self.db)
        bad=copy.deepcopy(self.bundle);bad['averages'][0]['value']='999' # synthetic correction under old source
        with self.assertRaises(Exception):import_bundle(self.db,bad)
        self.assertEqual(counts(self.db),before)

    def test_revision_appends_both_versions_without_choosing_a_winner(self):
        import_bundle(self.db,self.bundle);changed=copy.deepcopy(self.bundle)
        sid=changed['averages'][0]['source_id'];changed['sources'][sid]['note']='SYNTHETIC revised capture for append-only test, not published history'
        changed['averages'][0]['value']='999'
        import_bundle(self.db,changed)
        self.assertEqual(counts(self.db)['source_versions'],4)
        self.assertEqual(counts(self.db)['publication_values'],132)
        self.assertEqual(len(revisions(self.db)),1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM averages WHERE value='54.4'").fetchone()[0],3)
        with self.assertRaises(Exception):read_bundle(self.db)

    def test_explicit_frequency_overlap_query_and_missing_months(self):
        import_bundle(self.db,self.bundle)
        rows=query(self.db,'wb-gold-average','monthly','2020-01-01','2020-11-30')
        self.assertEqual(len(rows),9) # June appears in July and September editions
        self.assertEqual(len({r['observation']['period'] for r in rows}),8)
        self.assertEqual(query(self.db,'wb-gold-average','monthly','2020-12-01','2020-12-31'),[])
        with self.assertRaises(Exception):query(self.db,'wb-gold-average','daily','2020-01-01','2020-01-31')
        with self.assertRaises(Exception):query(self.db,'wb-gold-average','monthly','2021-01-01','2020-01-01')
        self.assertEqual(period_bounds('2020-Q1','quarterly'),('2020-01-01','2020-03-31'))

    def test_printed_date_filter_cannot_become_original_vintage_verification(self):
        import_bundle(self.db,self.bundle)
        args=(self.db,'wb-gold-average','monthly','2020-04-01','2020-04-30')
        self.assertEqual(query(*args,as_of='2020-07-01'),[]) # July edition not yet published
        self.assertEqual(len(query(*args,as_of='2020-07-02')),1)
        self.assertEqual(query(*args,as_of='2026-11-18',require_original_vintage=True),[])

    def test_reject_wrong_units_frequency_unlicensed_or_immature_average(self):
        for field,value in [('unit','GBP/share'),('frequency','daily'),('period','2020-12')]:
            b=copy.deepcopy(self.bundle);b['averages'][0][field]=value
            with self.assertRaises(Exception):validate(b)
        b=copy.deepcopy(self.bundle);b['averages'][0].update(frequency='monthly',period='2020-12')
        with self.assertRaises(Exception):validate(b)
        b=copy.deepcopy(self.bundle);next(iter(b['sources'].values()))['license']='free_to_view_only'
        with self.assertRaises(Exception):validate(b)
        b=copy.deepcopy(self.bundle);b['averages'].append(copy.deepcopy(b['averages'][0]))
        with self.assertRaises(Exception):validate(b)

    def test_IPO_units_non_completed_and_unsupported_allocations(self):
        cases={c['id']:c for c in self.bundle['ipos']}
        for key in ('ipo-wework-2019','ipo-ant-2020'):
            c=cases[key];self.assertEqual(ipo_reaction(c)['status'],'no_completed_listing');self.assertIsNone(ipo_reaction(c)['offer_to_first_close_percent'])
        self.assertEqual(ipo_reaction(cases['ipo-uber-2019'])['direction'],'negative')
        self.assertEqual(ipo_reaction(cases['ipo-deliveroo-2021'])['offer_to_first_close_percent'],'-26.2949')
        self.assertEqual(cases['ipo-deliveroo-2021']['unit'],'GBp/share')
        self.assertEqual(ipo_reaction(cases['ipo-etsy-2015'])['status'],'missing_reaction')
        self.assertIsNone(cases['ipo-lyft-2019']['document_day'])
        b=copy.deepcopy(self.bundle);next(c for c in b['ipos'] if c['id']=='ipo-ant-2020')['reported_first_close']='0'
        with self.assertRaises(Exception):validate(b)

    def test_imported_context_cannot_enter_daily_prices_old_events_or_model_fit(self):
        b=copy.deepcopy(self.bundle)
        for r in b['averages']:r['value']='999999' # synthetic future context perturbation
        expanded=expanded_library(self.data,b)
        self.assertEqual(self.data['events'],expanded['events']);self.assertEqual(self.data['observations'],expanded['observations'])
        self.assertEqual(fit(self.data),fit(expanded))
        e=next(e for e in self.data['events'] if e['id']=='opec-2020-april')
        self.assertEqual(plan(e,self.data,'brent'),plan(e,expanded,'brent'))

    def test_IPO_future_outcomes_not_consumed_or_silently_resplit(self):
        b=copy.deepcopy(self.bundle);b['ipos'][0]['evaluation_membership']='heldout_test'
        with self.assertRaises(Exception):expanded_library(self.data,b)
        self.assertTrue(all(c['episode_id'] not in {e['episode_id'] for e in self.data['events']} for c in self.bundle['ipos']))

    def test_access_probe_reports_failures_and_200_without_claiming_prices_or_saving_bodies(self):
        called=[]
        def client(url,headers):
            called.append(url)
            return (403,b'',{'X-Pilot-Transport-Denial':'true'}) if len(called)%2 else (200,b'challenge page',{'Content-Type':'text/html'})
        r=probe(client,lambda:'2026-11-18T08:50:00Z')
        self.assertEqual(called,list(ENDPOINTS.values()));self.assertTrue(all(x['imported_rows']==0 for x in r['receipts']))
        self.assertTrue(r['receipts'][0]['transport_denial']);self.assertNotIn('challenge page',json.dumps(r))
        self.assertIn('not_data',r['receipts'][1]['result'])

    def test_frozen_evaluation_report_reproduces_from_imported_database(self):
        import_bundle(self.db,self.bundle);report=build_report(read_bundle(self.db))
        self.assertEqual(report,json.loads((HERE/'report.json').read_text()))
        self.assertEqual(report['before'],report['after']);self.assertFalse(report['comparison']['predictive_improvement_demonstrated'])
        self.assertEqual(report['after']['simulation_default']['complete'],69)
        self.assertEqual(report['after']['learning']['retained_test_events'],21)
        self.assertEqual(report['after']['learning']['supported_entries'],0)


if __name__=='__main__':unittest.main()
