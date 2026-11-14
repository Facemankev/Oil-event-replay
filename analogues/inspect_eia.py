"""Recover only a known sanitized EIA snapshot from an owner-selected local DB.

Read-only URI + query_only; no migrations, fetching, keys or raw-payload output.
Expected fingerprints come from the immutable PR 19 review, not caller input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
from decimal import Decimal
from historical.prices import SERIES, MAX_PAYLOAD, validate_rows, DataError

EXPECTED = json.loads(Path(__file__).with_name('api-evidence.json').read_text())['expected_payload_sha256']


def parse_retained(payload, market, expected):
    if not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD or hashlib.sha256(payload).hexdigest() != expected:
        raise DataError('Original sanitized payload fingerprint not matched')
    try:
        pages = json.loads(payload)
        if not isinstance(pages, list) or not pages:
            raise ValueError()
        records, total = [], None
        for page in pages:
            response = page['response']
            count = int(response['total'])
            if response['frequency'] != 'daily' or count < 1 or count > 100000 or total is not None and count != total:
                raise ValueError()
            total = count
            for row in response['data']:
                if row['series'] != SERIES[market][1] or row['units'] not in {'Dollars per Barrel', '$/BBL', '$/bbl'}:
                    raise ValueError()
                records.append((row['period'], row['value']))
        rows = validate_rows(records)
        if len(rows) != total or len(records) != total:
            raise ValueError()
        return rows
    except Exception:
        # Never echo input, request metadata, DB errors or credential-bearing text.
        raise DataError('Retained snapshot failed safe replay validation') from None


def inspect(path):
    path = Path(path).resolve(strict=True)
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('PRAGMA trusted_schema=OFF')
        result = []
        for market, expected in EXPECTED.items():
            # Bounded lookup; inspect only the known original snapshot, never dump a DB.
            rows = db.execute('SELECT id,payload FROM price_snapshots WHERE series_id=? AND source_kind=? AND sha256=? LIMIT 2',
                              (market, 'eia', expected)).fetchall()
            if not rows:
                result.append(dict(market=market, status='expected_original_not_present'))
                continue
            parsed = parse_retained(rows[0][1], market, expected)
            stored = db.execute('SELECT observation_date,value,missing_code FROM price_observations WHERE snapshot_id=? ORDER BY observation_date', (rows[0][0],)).fetchall()
            # Replay-vs-stored mismatch is evidence of a parser/storage issue, not a revision.
            equal = parsed == [tuple(r) for r in stored]
            current = {}
            import csv
            with (Path(__file__).parents[1] / 'verification' / 'sources' / ('eia-' + market + '.csv')).open() as f:
                current = {r['date']: r for r in csv.DictReader(f)}
            numeric = [(day, value) for day, value, missing in parsed if value is not None]
            matching = sum(current.get(day, {}).get('status') == 'numeric' and Decimal(current[day]['value']) == Decimal(value) for day, value in numeric)
            result.append(dict(market=market, status='expected_sanitized_payload_replayed', sha256=expected,
                               observations=len(parsed), numeric=len(numeric), stored_rows_match_replay=equal,
                               numeric_matching_current_table=matching, revision_cause=None))
        return dict(read_only=True, network_used=False, original_API_evidence=result,
                    canonical_modified=False, revision_cause_established=False)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.db), indent=2))
    except Exception:
        parser.exit(1, 'Read-only evidence inspection failed; no database changed and input details suppressed.\n')


if __name__ == '__main__':
    main()
