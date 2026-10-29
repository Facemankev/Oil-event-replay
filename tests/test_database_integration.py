"""Exercise the real DAT-3 SQLite export at the EVT-1 adapter boundary."""
import json
from pathlib import Path
import tempfile
import unittest

from historical import prices
from world_events import events, research


class DatabaseIntegrationTests(unittest.TestCase):
    def test_real_import_repeat_export_and_all_event_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            price_path = root / "prices.sqlite"
            event_path = root / "events.sqlite"
            price_db = prices.open_db(price_path)
            event_db = events.connect(event_path)
            self.addCleanup(price_db.close)
            self.addCleanup(event_db.close)
            snapshots = [prices.seed_snapshot(m) for m in research.MARKETS]
            first = prices.import_snapshots(price_db, snapshots)
            self.assertEqual([s["inserted"] for s in first], [5231, 5137])
            repeat = prices.import_snapshots(price_db, snapshots)
            self.assertTrue(all(s["snapshot_reused"] for s in repeat))
            self.assertEqual(price_db.execute("SELECT count(*) FROM price_snapshots").fetchone()[0], 2)
            records = events.load_seed()
            self.assertEqual(events.import_records(event_db, records)["inserted"], 24)
            self.assertEqual(events.import_records(event_db, records)["reused"], 24)
            records = events.list_events(event_db)
            output = root / "prices.json"
            coverage = prices.export(price_db, output, end="2026-10-20")
            self.assertEqual([coverage[m]["count"] for m in research.MARKETS], [5231, 5137])
            actual = research.JSONPrices(output)
            baseline = research.CSVPrices()
            for record in records:
                with self.subTest(event=record["id"]):
                    joined = research.compare(record, actual)
                    expected = research.compare(record, baseline)
                    self.assertEqual(joined["status"], "ok")
                    # Compare dates, values, missingness and results; provenance
                    # correctly differs between a CSV and a SQLite export.
                    for key in ("series", "pre_dates", "post_dates", "calendar", "publication_anchor_date"):
                        self.assertEqual(joined[key], expected[key])
                    self.assertFalse(joined["backtest_eligible"])
                    self.assertFalse(joined["point_in_time_safe"])
                    for metadata in joined["price_sources"].values():
                        self.assertTrue(metadata["sources"])
                        self.assertTrue(all(s["source_kind"] == "seed" for s in metadata["sources"].values()))
            target = root / "events.json"
            summary = research.export(records, actual, target)
            self.assertEqual(summary["successful_comparisons"], 24)
            content = json.loads(target.read_text())
            self.assertEqual(sum(len(c["series"]) for c in content["comparisons"]), 48)
            self.assertEqual(dict(actual.rows["wti"])["2020-04-20"], research.Decimal("-36.98"))
            for db in (price_db, event_db):
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            # Schema versions deliberately differ; accidental cross-use must
            # fail without overwriting either database.
            with self.assertRaises(events.ValidationError):
                events.connect(price_path)
            with self.assertRaises(prices.DataError):
                prices.open_db(event_path)


if __name__ == "__main__":
    unittest.main()
