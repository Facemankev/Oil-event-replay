"""Add two verified public-domain FX transcriptions beside the unchanged HIST-1 inputs."""
import csv
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from event_history.library import ROOT, load_library, require, instrument, validate_library

HERE = Path(__file__).resolve().parent


def load_free_library():
    data = load_library()
    manifest = json.loads((HERE / 'sources/manifest.json').read_text())
    require(manifest['schema_version'] == 1, 'Unsupported free snapshot version')
    for name, code, unit in [('eurusd', 'eu', 'USD per EUR'), ('usdjpy', 'ja', 'JPY per USD')]:
        info = manifest['sources'][name]
        expected_url = 'https://www.federalreserve.gov/releases/h10/hist/dat00_' + code + '.htm'
        require(info['file'] == 'free_pilot/sources/fed-' + name + '.csv'
                and info['url'] == expected_url and info['unit'] == unit, 'Unexpected FX source identity/units')
        raw = (ROOT / info['file']).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == info['sha256'], 'Free-source bytes changed')
        rows = list(csv.DictReader(raw.decode().splitlines()))
        require(len(rows) == info['rows'] and len({p['date'] for p in rows}) == len(rows), 'Free-source count mismatch')
        require([p['date'] for p in rows] == sorted(p['date'] for p in rows), 'Unordered FX source')
        captured = {p['date'] for p in rows}
        current = date.fromisoformat(info['first'])
        while current <= date.fromisoformat(info['last']):
            if current.weekday() < 5:
                require(current.isoformat() in captured, 'Uncaptured primary weekday')
            current += timedelta(days=1)
        require(sum(p['status'] == 'numeric' for p in rows) == info['numeric'], 'Numeric FX count differs')
        sid = 'free-primary-' + name
        data['instruments'][name] = instrument(name, 'currencies',
            'Federal Reserve H.10 ' + ('EUR/USD' if name == 'eurusd' else 'USD/JPY'), unit,
            'New York noon reference; not executable or a daily exchange close',
            'actual numeric Fed reporting observations; ND retained', sid)
        data['sources'][sid] = dict(id=sid, url=info['url'], publisher='Federal Reserve',
            published_day=None, published_at=None, checked_on=manifest['captured_at'][:10],
            kind='current_primary_table', locator='Printed date in the official historical table',
            summary=unit, capture=manifest['capture_method'], original_http_sha256=None,
            original_version_verified=False, snapshot_sha256=info['sha256'])
        for p in rows:
            require(date.fromisoformat(p['date']).weekday() < 5, 'Unexpected weekday')
            if p['status'] == 'numeric':
                require(Decimal(p['value']).is_finite() and Decimal(p['value']) > 0, 'Invalid FX observation')
            else:
                require(p['status'] == 'ND' and p['value'] == '', 'Unknown missing marker')
            data['observations'].append(dict(instrument=name, date=p['date'],
                value=p['value'] if p['status'] == 'numeric' else None, status=p['status'],
                locator=p['locator'], source_id=sid, snapshot_id=info['sha256'],
                original_available_at=None, original_vintage_verified=False))
    data['free_source_manifest'] = manifest
    for file in ('prices.json', 'news.json', 'sources.json', 'calendar.json'):
        raw = (ROOT / 'equities' / file).read_bytes()
        pins = json.loads((ROOT / 'equities/INPUTS.json').read_text())
        require(hashlib.sha256(raw).hexdigest() == pins[file], 'Legacy equity evidence changed')
    # Secondary candidate quotes remain outside the primary observation table.
    data['legacy_equity_reference'] = json.loads((ROOT / 'equities/prices.json').read_text())
    validate_library(data)
    return data


def coverage(data):
    from event_history.library import GROUPS
    groups = []
    for group in GROUPS:
        symbols = [m for m, s in data['instruments'].items() if s['group'] == group]
        rows = [p for p in data['observations'] if p['instrument'] in symbols]
        groups.append(dict(group=group, instruments=symbols,
            numeric_observations=sum(p['status'] == 'numeric' for p in rows),
            explicit_unavailable=sum(p['status'] != 'numeric' for p in rows),
            reported_reactions=sum(r['instrument'] in symbols for r in data['reported_reactions']),
            retained_secondary_provider_rows=sum((p['symbol'] != 'IXIC' if group == 'technology_equities'
                                                 else p['symbol'] == 'IXIC' if group == 'stock_indices' else False)
                                                for p in data['legacy_equity_reference']['rows']),
            verified_intraday_quotes=0, as_of_qualified_cases=0))
    return dict(events=len(data['events']), observation_rows=len(data['observations']),
        numeric_observations=sum(p['status'] == 'numeric' for p in data['observations']),
        new_FX_numeric=sum(p['instrument'] in ('eurusd','usdjpy') and p['status'] == 'numeric' for p in data['observations']),
        new_FX_unavailable=sum(p['instrument'] in ('eurusd','usdjpy') and p['status'] == 'ND' for p in data['observations']), groups=groups,
        original_availability_verified=False, cost_GBP='0.00', paid_connections=0,
        note='Numeric observations, reported reactions and instrument coverage are distinct. GBP, EUR and JPY reference quotes are not live FX fills.')
