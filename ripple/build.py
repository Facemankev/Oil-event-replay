"""Derive a small paper-price slice from unchanged Brent and a pinned FX CSV."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build():
    prices_path = ROOT / 'data/historical/prices.json'
    fx_path = ROOT / 'ripple/fx-harvey-source.csv'
    sources_path = ROOT / 'ripple/sources.json'
    source = json.loads(prices_path.read_text())
    market = next(s for s in source['series'] if s['series'] == 'brent')
    sources = json.loads(sources_path.read_text())
    with fx_path.open() as stream:
        raw = list(csv.DictReader(stream))
    if len({r['Date'] for r in raw}) != len(raw) or any(r['Country'] != 'United Kingdom' for r in raw):
        raise ValueError('Duplicate or unexpected FX records')
    rates = {r['Date']: r['Exchange rate'] for r in raw}
    quotes, missing, calendar = [], [], []
    for row in market['observations']:
        day = row['date']
        if not '2017-08-14' <= day <= '2017-09-29':
            continue
        if row['value'] is not None:
            calendar.append(day)
        rate = rates.get(day)
        if row['value'] is None or not rate:
            missing.append({'date': day, 'reason': 'price_missing' if row['value'] is None else 'fx_missing'})
            continue
        if Decimal(row['value']) <= 0 or Decimal(rate) <= 0:
            raise ValueError('Nonpositive quote cannot be used for fractional practice')
        quotes.append({'date': day, 'price': row['value'], 'gbpPerUnit': rate, 'snapshot_id': row['snapshot_id']})
    if not any(q['date'] == '2017-08-28' for q in quotes):
        raise ValueError('Required starting observation unavailable')
    result = {
        'schemaVersion': 1, 'scenario_id': 'harvey-brent-gbp-2017-v1',
        'event_id': 'harvey-2017-texas', 'start': '2017-08-28',
        'instrument': 'Unleveraged fractional Brent spot-price reference, converted to GBP',
        'quotes': quotes, 'market_calendar': calendar, 'missing': missing,
        'price_sources': market['sources'], 'sources': sources,
        'input_hashes': {'prices': digest(prices_path.read_bytes()), 'fx': digest(fx_path.read_bytes()), 'source_cards': digest(sources_path.read_bytes())},
        'availability': 'Educational end-of-day availability assumption. Original price/FX publication clocks and vintages are unknown; not a point-in-time-safe backtest.',
        'point_in_time_safe': False,
    }
    result['snapshot_id'] = digest(json.dumps(result, sort_keys=True, separators=(',', ':')).encode())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    output = ROOT / 'ripple/data.json'
    if args.check:
        if output.read_text() != text:
            raise SystemExit('Ripple data differs from the unchanged source inputs')
    else:
        output.write_text(text)
    print(json.dumps({'quotes': len(result['quotes']), 'missing': result['missing'], 'snapshot_id': result['snapshot_id']}))


if __name__ == '__main__':
    main()
