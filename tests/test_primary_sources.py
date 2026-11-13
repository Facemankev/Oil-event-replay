"""Primary table alignment, explicit missingness and canonical preservation."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import unittest
from verification.sources import ROOT, numeric, table_rows, parse_html, csv_bytes, load_sources


class PrimarySourceTests(unittest.TestCase):
    def test_complete_pinned_snapshot_and_all_original_prices_match(self):
        manifest, sources = load_sources()
        self.assertEqual({k:len(v) for k,v in sources.items()}, dict(brent=5440,wti=5440,fx=5440))
        self.assertEqual(sum(r['status']=='numeric' for r in sources['fx']),5224)
        self.assertFalse(manifest['original_historical_publication_times_known'])
        self.assertIsNone(manifest['sources']['fx']['original_http_sha256'])
        original=json.loads((ROOT/'data/historical/prices.json').read_text())
        counts={}
        for series in original['series']:
            primary={r['date']:r for r in sources[series['series']]}
            for row in series['observations']:
                self.assertEqual(Decimal(row['value']),Decimal(primary[row['date']]['value']))
            counts[series['series']]=len(series['observations'])
        self.assertEqual(counts,dict(brent=5231,wti=5137))

    def test_eia_blank_monday_does_not_shift_tuesday_wednesday_or_thursday(self):
        _,sources=load_sources();values={r['date']:r['value'] for r in sources['brent']}
        dates=['2016-12-26','2016-12-27','2016-12-28','2016-12-29','2016-12-30']
        rows=table_rows('brent',['2016 Dec-26 to Dec-30',*[values[d] for d in dates]])
        self.assertEqual([r['date'] for r in rows],dates)
        self.assertEqual(rows[0]['status'],'blank_primary_cell')
        self.assertEqual(rows[2]['value'],'54.95');self.assertEqual(rows[3]['value'],'54.97')

    def test_cross_year_zero_and_negative_are_values_not_unavailable(self):
        # Synthetic parser fixture only; never inserted into historical research.
        rows=table_rows('wti',['2019 Dec-30 to Jan- 3','1.00','2.00','','0.00','-1.00'])
        self.assertEqual(rows[-1]['date'],'2020-01-03')
        self.assertEqual(rows[-1]['value'],'-1.00');self.assertEqual(rows[-2]['status'],'numeric')
        self.assertEqual(rows[2]['status'],'blank_primary_cell')

    def test_fed_rate_direction_and_unavailable_marker_are_explicit(self):
        self.assertEqual(table_rows('fx',['28-AUG-17','1.2927'])[0]['value'],'1.2927')
        self.assertEqual(table_rows('fx',['4-SEP-17','ND'])[0]['value'],'')
        for value in ['0.0000','-1.0000','NaN','Infinity','true']:
            with self.assertRaises(ValueError):numeric(value,fx=True)

    def test_invalid_column_counts_and_week_labels_fail_instead_of_guessing(self):
        for cells in [['2016 Dec-26 to Dec-30','1.00'],['2016 Dec-27 to Dec-31']+['1.00']*5,['2016 Dec-26 to Jan- 6']+['1.00']*5]:
            with self.assertRaises(ValueError):table_rows('brent',cells)

    def test_minimal_html_fixture_requires_complete_week_and_correct_units(self):
        # Synthetic HTML structure fixture with real date labels; values are not production input.
        heading='<h1>Historical Rates for the Great British Pound</h1><p>Rates in U.S. dollars per Great British Pound</p>'
        rows=['<tr><td>'+str(n)+'-JAN-06</td><td>'+('ND' if n==2 else '1.0000')+'</td></tr>' for n in range(2,7)]
        raw=(heading+'<table>'+''.join(rows)+'</table>').encode()
        parsed=parse_html('fx',raw,'2006-01-02','2006-01-06')
        self.assertEqual(len(parsed),5);self.assertEqual(parsed[0]['status'],'ND')
        self.assertNotIn(b'\r',csv_bytes(parsed))
        with self.assertRaises(ValueError):parse_html('fx',(heading+''.join(rows[:-1])).encode(),'2006-01-02','2006-01-06')
        with self.assertRaises(ValueError):parse_html('fx',raw.replace(b'U.S. dollars per Great British Pound',b'GBP per USD'),'2006-01-02','2006-01-06')

    def test_duplicate_primary_rows_are_rejected(self):
        raw=b'<h1>Europe Brent Spot Price FOB (Dollars per Barrel)</h1>'
        row=b'<tr><td>2006 Jan- 2 to Jan- 6</td>'+b'<td>1.00</td>'*5+b'</tr>'
        with self.assertRaises(ValueError):parse_html('brent',raw+row+row,'2006-01-02','2006-01-06')

    def test_immutable_parent_data_accounts_and_approved_interface(self):
        for name in ['data/historical/prices.json','data/historical/brent-daily-2006-2026.csv','data/historical/wti-daily-2006-2026.csv',
                     'ripple/data.json','ripple/fx-harvey-source.csv','ripple/model.mjs','ripple/ui.mjs','ripple/index.html',
                     'ripple/style.css','matching/design.css','intelligence/engine.mjs','intelligence/REPORT.sha256']:
            original=subprocess.check_output(['git','show','d45f3ff:'+name],cwd=ROOT)
            self.assertEqual(original,(ROOT/name).read_bytes(),name)

    def test_source_csv_bytes_are_protected_for_windows_checkouts(self):
        self.assertIn('verification/sources/*.csv -text',(ROOT/'.gitattributes').read_text())
        for path in (ROOT/'verification/sources').glob('*.csv'):
            self.assertNotIn(b'\r',path.read_bytes())
