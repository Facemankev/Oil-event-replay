"""Anonymous fixed-endpoint adapters. No keys, paid routes, billing or fallback proxies."""
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
from datetime import timedelta

from event_history.library import ROOT, require
from world_events.events import digest
from news_pilot.ingest import fetch, utc, at, later, retry_seconds, safe_header
from verification.sources import Tables, table_rows, parse_html

PARENT = '08aea1b2464969c06f6e53bdc9cc02bef5ff0809'
BASE = 'https://raw.githubusercontent.com/Facemankev/Oil-event-replay/' + PARENT + '/'
SOURCES = {
    'oil_events': dict(url=BASE + 'matching/cohort-catalog.json', kind='retained_event_catalog',
                       file='matching/cohort-catalog.json', publishable=True),
    'company_events': dict(url=BASE + 'event_history/additions.json', kind='retained_event_catalog',
                           file='event_history/additions.json', publishable=True),
    'company_news': dict(url=BASE + 'equities/news.json', kind='retained_event_catalog',
                        file='equities/news.json', publishable=True),
    'fed_eurusd': dict(url='https://www.federalreserve.gov/releases/h10/hist/dat00_eu.htm',
                      kind='fed_eurusd', publishable=True),
    'fed_usdjpy': dict(url='https://www.federalreserve.gov/releases/h10/hist/dat00_ja.htm',
                      kind='fed_usdjpy', publishable=True),
    'eia_brent': dict(url='https://www.eia.gov/dnav/pet/hist/RBRTED.htm', kind='brent', publishable=True),
    'eia_wti': dict(url='https://www.eia.gov/dnav/pet/hist/RWTCD.htm', kind='wti', publishable=True),
    'stooq_nvda': dict(url='https://stooq.com/q/d/l/?s=nvda.us&i=d&d1=20230501&d2=20230630',
                       kind='stooq_csv', publishable=False),
    'stooq_pharma': dict(url='https://stooq.com/q/d/l/?s=biib.us&i=d&d1=20190301&d2=20190430',
                         kind='stooq_csv', publishable=False),
    'stooq_gold': dict(url='https://stooq.com/q/d/l/?s=xauusd&i=d&d1=20200301&d2=20200430',
                       kind='stooq_csv', publishable=False),
    'fred_nasdaq': dict(url='https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=20230501&coed=20230630',
                        kind='fred_csv', publishable=False),
}
MAX_BYTES = 4 * 1024 * 1024


def normalize(source_id, payload):
    require(source_id in SOURCES and isinstance(payload, bytes) and len(payload) <= MAX_BYTES,
            'Unsupported source or oversized response')
    source = SOURCES[source_id]
    kind = source['kind']
    if kind == 'retained_event_catalog':
        data = json.loads(payload)
        expected = json.loads((ROOT / source['file']).read_text())
        require(digest(data) == digest(expected), 'Pinned event catalog fingerprint mismatch')
        return dict(items=len(data.get('events', data.get('articles', []))),
                    payload_kind='curated_historical_research_not_live_issuer_news', data=data)
    if kind in ('brent', 'wti'):
        rows = parse_html(kind, payload, '2006-01-02', '2026-11-06')
    elif kind.startswith('fed_'):
        html = payload.decode('utf-8-sig')
        visible = ' '.join(re.sub('<[^>]*>', ' ', html).split())
        title, unit = ('Historical Rates for the EU Euro', 'Rates in U.S. dollars per EU euro') if kind == 'fed_eurusd' else (
                       'Historical Rates for the Japanese Yen', 'Rates in Japanese yen per U.S. dollar')
        require(title in visible and unit in visible, 'Wrong FX instrument/unit or challenge page')
        parser = Tables(); parser.feed(html)
        rows = [p for cells in parser.rows for p in table_rows('fx', cells)
                if '2006-01-02' <= p['date'] <= '2026-11-13']
        expected = {p['date'] for p in rows}
        require(len(rows) == 5445 and len(expected) == len(rows), 'Incomplete or duplicate FX table')
        from datetime import date
        current = date(2006, 1, 2)
        while current <= date(2026, 11, 13):
            if current.weekday() < 5:
                require(current.isoformat() in expected, 'Uncaptured FX weekday')
            current += timedelta(days=1)
    else:
        text = payload.decode('utf-8-sig')
        lines = list(csv.DictReader(io.StringIO(text)))
        require(lines and len(lines) <= 100000, 'No supported CSV data; challenges/errors are not prices')
        if kind == 'stooq_csv':
            require(set(('Date', 'Open', 'High', 'Low', 'Close')).issubset(lines[0]), 'Unexpected Stooq header')
            rows = []
            for p in lines:
                from event_history.engine import day
                day(p['Date'])
                values = [Decimal(p[k]) for k in ('Open', 'High', 'Low', 'Close')]
                require(all(v.is_finite() and v > 0 for v in values) and
                        values[1] >= max(values) and values[2] <= min(values), 'Invalid OHLC')
                rows.append(dict(date=p['Date'], value=p['Close'], status='numeric'))
        else:
            require(set(lines[0]) == {'observation_date', 'NASDAQCOM'}, 'Unexpected FRED header/instrument')
            from event_history.engine import day
            rows = []
            for p in lines:
                day(p['observation_date']); value=p['NASDAQCOM']
                require(value == '.' or Decimal(value).is_finite() and Decimal(value) > 0, 'Invalid index observation')
                rows.append(dict(date=p['observation_date'], value=None if value == '.' else value,
                                 status='not_reported' if value == '.' else 'numeric'))
        require(len({p['date'] for p in rows}) == len(rows), 'Duplicate provider dates')
    # Metadata only for sources whose price basis/redistribution was not verified.
    return dict(items=len(rows), numeric=sum(p['status'] == 'numeric' for p in rows),
                rows=rows if source['publishable'] else [], public_research_usable=source['publishable'],
                adjustment_basis='not_applicable_spot_or_FX' if source['publishable'] else 'not_verified',
                original_availability_verified=False)


def journal(directory):
    path = Path(directory).resolve()
    require(path.is_relative_to((ROOT / 'work').resolve()) and path != (ROOT / 'work').resolve(),
            'Dedicated work/ journal required')
    path.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path / 'observations.sqlite', timeout=15)
    db.row_factory = sqlite3.Row
    version = db.execute('PRAGMA user_version').fetchone()[0]
    app = db.execute('PRAGMA application_id').fetchone()[0]
    if version == 0 and app == 0:
        require(not db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0],
                'Unrelated database refused')
        db.executescript('''BEGIN IMMEDIATE;
          CREATE TABLE budget(source TEXT PRIMARY KEY,next_at TEXT,etag TEXT,payload_sha TEXT);
          CREATE TABLE receipts(id INTEGER PRIMARY KEY,source TEXT,received TEXT,status TEXT,http_status INTEGER,payload_sha TEXT);
          CREATE TABLE decisions(id TEXT PRIMARY KEY,event_id TEXT,first_recorded_at TEXT,payload TEXT NOT NULL);
          PRAGMA application_id=40001; PRAGMA user_version=4001; COMMIT;''')
    else:
        require(version == 4001 and app == 40001, 'Unsupported free-pilot journal')
    return path, db


def poll(directory, source_id, client=fetch, clock=utc):
    require(source_id in SOURCES, 'No anonymous free endpoint: keyed/paid providers are disabled')
    source = SOURCES[source_id]
    path, db = journal(directory)
    started = clock()
    try:
        db.execute('BEGIN IMMEDIATE')
        prior = db.execute('SELECT * FROM budget WHERE source=?', (source_id,)).fetchone()
        if prior and at(started) < at(prior['next_at']):
            db.rollback()
            return dict(source=source_id, status='cooldown_no_request', network_request=False, cost_GBP='0.00')
        db.execute('INSERT INTO budget(source,next_at) VALUES(?,?) ON CONFLICT(source) DO UPDATE SET next_at=excluded.next_at',
                   (source_id, later(started, 60)))
        db.commit()
        headers = {'If-None-Match': prior['etag']} if prior and prior['etag'] else {}
        try:
            status, payload, response_headers = client(source['url'], headers)
        except Exception:
            status, payload, response_headers = 0, b'', {}
        received = clock()
        state = 'http_' + str(status)
        sha, normalized = None, None
        if at(received) < at(started):
            state = 'clock_regressed'
        elif status == 304 and prior and prior['payload_sha']:
            sha = prior['payload_sha']
            cached = path / 'private' / (sha + '.json')
            if cached.exists():
                normalized = normalize(source_id, cached.read_bytes())
                state = 'not_modified'
        elif status == 200:
            try:
                normalized = normalize(source_id, payload)
                sha = hashlib.sha256(payload).hexdigest()
                state = 'ok' if source['publishable'] else 'accessible_but_terms_or_basis_unverified'
                if source['kind'] == 'retained_event_catalog':
                    folder = path / 'private'; folder.mkdir(exist_ok=True)
                    target = folder / (sha + '.json')
                    if not target.exists():
                        target.write_bytes(payload)
            except (ValueError, KeyError, TypeError, UnicodeError, ArithmeticError):
                state = 'invalid_or_challenge_response'
                normalized = None
        delay = 60
        if status in (401, 403) or state in ('invalid_or_challenge_response', 'clock_regressed'):
            delay = 3600
        elif status == 429:
            delay = retry_seconds(safe_header(response_headers, 'Retry-After'), received)
        elif status == 0 or status >= 500 or 300 <= status < 400 and status != 304:
            delay = 300
        try:
            deadline = later(max(started, received, key=at), delay)
        except (OverflowError, ValueError):
            deadline = '9999-12-31T23:59:59.999999Z'
        etag = safe_header(response_headers, 'ETag') if state == 'ok' else prior['etag'] if prior else None
        cache_sha = sha if state == 'ok' and source['kind'] == 'retained_event_catalog' else prior['payload_sha'] if prior else None
        db.execute('UPDATE budget SET next_at=?,etag=?,payload_sha=? WHERE source=?', (deadline, etag, cache_sha, source_id))
        db.execute('INSERT INTO receipts(source,received,status,http_status,payload_sha) VALUES(?,?,?,?,?)',
                   (source_id, received, state, status, sha))
        db.commit()
        return dict(source=source_id, url=source['url'], status=state, http_status=status,
                    received_at=received, payload_sha256=sha, network_request=True,
                    normalized=normalized, cost_GBP='0.00', next_attempt_at=deadline,
                    transport_denial=safe_header(response_headers, 'X-Pilot-Transport-Denial') == 'true')
    finally:
        db.close()
