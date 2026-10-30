"""Derive lightweight coverage from the existing export without changing any data."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = ROOT / 'data/historical/prices.json'
    data = json.loads(source.read_text())
    status = {'schemaVersion': 1, 'source': 'data/historical/prices.json',
              'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'coverage': {s['series']: s['coverage'] for s in data['series']},
              'status': 'provisional_historical_snapshot_not_a_current_feed'}
    output = json.dumps(status, indent=2) + '\n'
    target = ROOT / 'app/data-status.json'
    if args.check:
        if target.read_text() != output:
            raise SystemExit('Coverage report differs from the existing price export')
        print('Coverage metadata matches the unchanged historical export')
    else:
        target.write_text(output)


if __name__ == '__main__':
    main()
