"""Normalize existing research and verified new fact cards without source writes."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from world_events.events import digest, ValidationError

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
GROUPS = ('oil', 'technology_equities', 'gold', 'pharmaceuticals',
          'stock_indices', 'currencies')
HORIZONS = (1, 3, 5, 10, 20)


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def read_json(path):
    return json.loads((ROOT / path).read_text())


def public_url(value):
    url = urlsplit(value)
    require(url.scheme == 'https' and url.hostname and not url.username
            and not url.password and not url.fragment, 'Public HTTPS source required')
    require(not any(word in url.query.lower() for word in
                    ('key=', 'token=', 'password=', 'secret=')), 'Credential URL refused')


def source_card(id, evidence):
    published = evidence.get('published', {})
    published_at = published.get('at') or evidence.get('published_at')
    return dict(id=id, url=evidence['url'], publisher=evidence.get('publisher', 'See original source'),
                published_day=published.get('date') or (published_at[:10] if published_at else None),
                published_at=published_at,
                checked_on=evidence.get('checked_on') or evidence.get('retrieved_on'),
                kind=evidence.get('quality') or evidence.get('kind', 'linked_evidence'),
                locator=evidence.get('locator', 'See parent evidence card'),
                summary=evidence.get('summary', 'Preserved parent evidence reference.'),
                capture='inherited curated fact card; see unchanged parent module',
                original_http_sha256=None, original_version_verified=False,
                parent_evidence_sha256=digest(evidence))


def instrument(id, group, name, unit, basis, schedule, source=None):
    return dict(id=id, group=group, name=name, unit=unit, basis=basis,
                calendar=schedule, source_id=source,
                original_price_availability_verified=False,
                executable_quote=False, paper_execution_enabled=False)


def instruments():
    values = [
        instrument('brent', 'oil', 'EIA Europe Brent spot FOB', 'USD per barrel',
                   'unadjusted physical spot reference; not a futures contract',
                   'actual numeric EIA reporting observations; not exchange sessions', 'primary-brent'),
        instrument('wti', 'oil', 'EIA Cushing WTI spot FOB', 'USD per barrel',
                   'unadjusted physical spot reference; negative observations retained',
                   'actual numeric EIA reporting observations; not exchange sessions', 'primary-wti'),
        instrument('gbpusd', 'currencies', 'Federal Reserve H.10 GBP/USD reference',
                   'USD per GBP', 'New York noon buying rate; not an executable FX close',
                   'actual numeric Fed reporting observations; ND is explicit', 'primary-fx'),
        instrument('gold_futures_reported', 'gold', 'Reported US gold futures reaction',
                   'reported percent', 'generic GCv1 in news; exact contract unresolved',
                   'no verified contract/session series'),
        instrument('nasdaq_composite', 'stock_indices', 'Nasdaq Composite price index',
                   'index points', 'price index; not total return or a tradable share',
                   'no new historical session series verified'),
    ]
    for symbol, group, name, venue in [
        ('NVDA', 'technology_equities', 'NVIDIA common stock', 'Nasdaq'),
        ('INTC', 'technology_equities', 'Intel common stock', 'Nasdaq'),
        ('EFX', 'technology_equities', 'Equifax common stock (cross-sector corporate case)', 'NYSE'),
        ('TSLA', 'technology_equities', 'Tesla common stock (cross-sector corporate case)', 'Nasdaq'),
        ('BIIB', 'pharmaceuticals', 'Biogen common stock', 'Nasdaq'),
        ('PFE', 'pharmaceuticals', 'Pfizer common stock', 'NYSE'),
    ]:
        row = instrument(symbol, group, name, 'USD per share',
                         'corporate-action-adjusted series unavailable; no basis mixing',
                         'historical session/print schedule unverified')
        row['venue'] = venue
        values.append(row)
    return {item['id']: item for item in values}


def load_library():
    """All parent reads are fingerprinted. Output contains no inferred old receipt."""
    expected = read_json('event_history/INPUTS.json')
    for name, sha in expected.items():
        value = read_json(name)
        require(digest(value) == sha, 'Historical input fingerprint mismatch: ' + name)
    extra = read_json('event_history/additions.json')
    require(extra['schema_version'] == 1, 'Unsupported history schema')
    sources = extra['sources'].copy()
    events = []
    original = read_json('matching/cohort-catalog.json')['events']
    storms = read_json('analogues/events.json')['events']
    for old in original + storms:
        ids = []
        for evidence in old['evidence']:
            id = 'oil-' + evidence['id']
            sources[id] = source_card(id, evidence)
            ids.append(id)
        primary = old['first_public']
        support = next((sources[id] for id in ids if sources[id]['published_at']
                        or sources[id]['published_day']), sources[ids[0]])
        episode = old.get('episode_id')
        if not episode and old['category'] == 'weather':
            import re
            found = re.search(r'/(al\d{6})\.', support['url'], re.I)
            episode = found[1].upper() if found else None
        # Policy stages in one sequence cannot be independent training cases.
        if old['id'].startswith('opec-2016-'):
            episode = 'opec-2016-agreement'
        elif old['id'].startswith('opec-2020-'):
            episode = 'opec-2020-agreement'
        elif old['id'] in ('us-2018-jcpoa', 'us-2018-iran-reimposition'):
            episode = 'iran-us-2018-sanctions'
        episode = episode or old['id']
        feature = old['features']
        severity = feature.get('severity')
        if severity:
            sid = old['id'] + '-scale'
            sources[sid] = source_card(sid, {**severity, 'id': sid, 'published_at': severity['published_at']})
            ids.append(sid)
            severity = dict(scale=severity['scale'], value=severity['value'], source_id=sid)
        events.append(dict(
            id=old['id'], revision=1, title=old['title'], category=old['category'],
            mechanism=feature['mechanism'], primary_group='oil',
            occurred_day=old['occurred']['date'], occurred_at=old['occurred'].get('at'),
            public_day=primary['date'] or support['published_day'],
            public_at=primary.get('at') or support['published_at'],
            publication_source=support['id'], source_ids=ids, episode_id=episode,
            first_disclosure_verified=False,
            first_public_not_established=primary['status'] == 'not_established',
            historical_receipt_at=None,
            location=['US_Gulf_coast'] if old['category'] == 'weather' and 'Gulf of Mexico' in old['geography'] else [old['geography']],
            stage=feature['mechanism'],
            impact=feature['impact'], regime=None, severity=severity,
            targets=['brent', 'wti', 'gbpusd'], summary=old.get('description', old['title']),
            weaknesses=[old['uncertainty'], 'Oil-relevant location is not exposure equivalence; outage and recovery magnitudes are unproven.'],
            parent_path='matching/cohort-catalog.json' if old in original else 'analogues/events.json'))
    company_sources = read_json('equities/sources.json')['sources']
    references = []
    for old in read_json('equities/history.json')['cases']:
        for sid in old['source_ids'] + [p['source_id'] for p in old['prices']]:
            id = 'company-' + sid
            sources[id] = source_card(id, company_sources[sid])
        sid = 'company-' + old['source_ids'][0]
        sources[sid]['published_day'] = old['public_day']
        sources[sid]['published_at'] = old['public_at']
        events.append(dict(
            id=old['id'], revision=1, title=old['title'], category='corporate_event',
            mechanism=old['stage'], primary_group='technology_equities',
            occurred_day=old['occurred_day'], public_day=old['public_day'], public_at=old['public_at'],
            publication_source=sid, episode_id=old['id'], location=old['location'],
            stage=old['stage'], impact='company_specific', regime=None, severity=None,
            targets=[old['symbol']], source_ids=['company-' + s for s in old['source_ids']],
            summary=old['title'], weaknesses=old['weaknesses'], historical_receipt_at=None,
            first_disclosure_verified=False, parent_path='equities/history.json'))
        if len(old['prices']) == 2:
            references.append(dict(event_id=old['id'], instrument=old['symbol'],
                                   points=[{**p, 'source_id': 'company-' + p['source_id']} for p in old['prices']],
                                   basis='parent sourced nominal reference pair, not verified adjusted/session series'))
    events.extend(extra['events'])
    series, rows = {}, []
    manifest = read_json('verification/sources/manifest.json')
    for key, name in [('brent', 'brent'), ('wti', 'wti'), ('fx', 'gbpusd')]:
        info = manifest['sources'][key]
        raw = (ROOT / info['file']).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == info['sha256'], 'Primary source bytes changed')
        id = 'primary-' + key
        sources[id] = dict(id=id, url=info['url'], publisher='Federal Reserve' if key == 'fx' else 'US EIA',
                           published_day=None, published_at=None, checked_on=manifest['captured_at'][:10],
                           kind='current_primary_table', locator='Date/week column; locator in each observation',
                           summary=info['unit'], capture=manifest['capture_method'],
                           original_http_sha256=None, original_version_verified=False,
                           snapshot_sha256=info['sha256'])
        for p in csv.DictReader(raw.decode().splitlines()):
            row = dict(instrument=name, date=p['date'], value=p['value'] if p['status'] == 'numeric' else None,
                       status=p['status'], locator=p['locator'], source_id=id, snapshot_id=info['sha256'],
                       original_available_at=None, original_vintage_verified=False)
            rows.append(row)
        series[name] = info
    data = dict(schema_version=1, sampling=extra['selection'], events=events, sources=sources, instruments=instruments(),
                observations=rows, reported_reactions=extra['reported_reactions'],
                reference_comparisons=references, inputs=expected)
    validate_library(data)
    return data


def validate_library(data):
    from .engine import day, stamp
    from decimal import Decimal
    import math
    require(data.get('schema_version') == 1, 'Unsupported history version')
    ids = set()
    for sid, s in data['sources'].items():
        public_url(s['url'])
        require(sid == s['id'] and s['locator'] and s['capture'], 'Incomplete provenance')
        require(s.get('original_http_sha256') is None, 'A curated card is not original HTTP evidence')
        if s.get('published_day'):
            day(s['published_day'])
        if s.get('published_at'):
            stamp(s['published_at'])
    for e in data['events']:
        require(e['id'] not in ids, 'Duplicate event identifier')
        ids.add(e['id'])
        require(e['revision'] >= 1 and e['primary_group'] in GROUPS, 'Invalid event version/group')
        require(e['episode_id'] and e['mechanism'] and e['stage'] and e['location'], 'Missing comparison features')
        require(e['targets'] and all(m in data['instruments'] for m in e['targets']), 'Unknown instrument')
        require(e['publication_source'] in e['source_ids'] and all(s in data['sources'] for s in e['source_ids']), 'Missing source reference')
        for field in ('occurred_day', 'public_day'):
            if e.get(field):
                day(e[field])
        if e.get('public_at'):
            stamp(e['public_at'])
        require(e['historical_receipt_at'] is None, 'No original historical receipt was obtained')
        s = data['sources'][e['publication_source']]
        require(e['public_at'] == s['published_at'] and e['public_day'] == s['published_day'], 'Source/publication mismatch')
        if e.get('severity'):
            v = e['severity']
            require(v['source_id'] in e['source_ids'] and isinstance(v['value'], (float, int))
                    and not isinstance(v['value'], bool) and math.isfinite(v['value'])
                    and v['value'] >= 0, 'Unsourced magnitude')
    reaction_ids = set()
    for r in data['reported_reactions']:
        require(r['id'] not in reaction_ids, 'Duplicate reported reaction')
        reaction_ids.add(r['id'])
        require(r['event_id'] in ids and r['source_id'] in data['sources'] and
                r['instrument'] in data['instruments'], 'Unlinked reported reaction')
        require(not r['raw_price_series_verified'] and r['original_available_at'] is None,
                'Reported reaction is not a verified price series')
        require(isinstance(r['reported_percent'], str) and Decimal(r['reported_percent']).is_finite(),
                'Finite reported percentage required')
        day(r['observation_day'])
    previous = {}
    for r in data['observations']:
        day(r['date'])
        require(r['instrument'] in data['instruments'] and r['source_id'] in data['sources'], 'Unknown price provenance')
        require(r['date'] > previous.get(r['instrument'], ''), 'Duplicate or unordered price date')
        previous[r['instrument']] = r['date']
        if r['status'] == 'numeric':
            value = Decimal(r['value'])
            require(value.is_finite() and (r['instrument'] != 'gbpusd' or value > 0), 'Invalid price')
        else:
            require(r['value'] is None and r['status'] in ('ND', 'blank_primary_cell'), 'Invalid missing marker')
        require(r['original_available_at'] is None and not r['original_vintage_verified'], 'Vintage evidence was not obtained')
