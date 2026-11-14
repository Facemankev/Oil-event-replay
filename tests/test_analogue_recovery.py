"""Synthetic transport fixtures test recovery safety, not real historical evidence."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from analogues.inspect_eia import parse_retained, inspect
from historical.prices import DataError


class RecoveryTests(unittest.TestCase):
    def payload(self, data=None, total=2):
        data = data or [dict(period='2016-12-28', value='54.95', series='RBRTE', units='Dollars per Barrel'),
                        dict(period='2016-12-29', value=None, series='RBRTE', units='Dollars per Barrel')]
        return json.dumps([dict(response=dict(frequency='daily', total=total, data=data))]).encode()

    def test_normalized_numeric_and_missing_are_preserved(self):
        p = self.payload()
        self.assertEqual(parse_retained(p, 'brent', hashlib.sha256(p).hexdigest()),
                         [('2016-12-28', '54.95', None), ('2016-12-29', None, 'null')])

    def test_unknown_payload_fails_before_parse_without_echo(self):
        p = b'untrusted private input'
        with self.assertRaises(DataError) as context:
            parse_retained(p, 'brent', '0' * 64)
        self.assertNotIn('private input', str(context.exception))

    def test_duplicate_or_wrong_commodity_cannot_replay(self):
        row = dict(period='2016-12-28', value='54.95', series='RWTC', units='Dollars per Barrel')
        for rows in [[row], [dict(row, series='RBRTE'), dict(row, series='RBRTE')]]:
            p = self.payload(rows, len(rows))
            with self.assertRaises(DataError):
                parse_retained(p, 'brent', hashlib.sha256(p).hexdigest())

    def test_missing_path_is_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'absent.sqlite'
            with self.assertRaises(FileNotFoundError):
                inspect(p)
            self.assertFalse(p.exists())

    def test_existing_database_remains_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'synthetic.sqlite'
            with sqlite3.connect(p) as db:
                db.execute('CREATE TABLE price_snapshots (id, series_id, source_kind, sha256, payload)')
            before = p.read_bytes()
            result = inspect(p)
            self.assertEqual(before, p.read_bytes())
            self.assertTrue(result['read_only'])
            self.assertFalse(result['canonical_modified'])
            self.assertTrue(all(r['status'] == 'expected_original_not_present' for r in result['original_API_evidence']))


if __name__ == '__main__':
    unittest.main()
