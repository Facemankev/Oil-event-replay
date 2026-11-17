"""A real bounded pipeline over sourced historical events, never a live alert service."""
from datetime import timedelta
from decimal import Decimal
import hashlib
import json
import time
import subprocess

from event_history.engine import (publication, iso, historical_decision, descriptive_cohort,
                                  response, summarize)
from event_history.library import ROOT, HORIZONS, require
from world_events.events import digest, canonical
from news_pilot.ingest import utc
from .data import load_free_library, coverage
from .providers import SOURCES, normalize, poll, journal

CASES = {
    'harvey': ('harvey-2017-texas', 'oil_events'),
    'nvidia': ('nvidia-2024-q4-outlook', 'company_events'),
    'biogen': ('biogen-2019-futility', 'company_events'),
    'fed': ('fed-2020-emergency-cut', 'company_events'),
    'nvidia_board': ('nvidia-2026-board-replay', 'company_news'),
}
REFERENCE_CUTOFF = '2026-11-17T23:59:59Z'


def detect(record):
    """Deterministic text rules cross-check the curated taxonomy, not a news AI."""
    import re
    text = record['title'] + ' ' + record.get('description', record.get('summary', ''))
    if re.search(r'\blandfall\b', text, re.I):
        return 'weather'
    if re.search(r'\bnvidia\b', text, re.I) and re.search(r'\b(results|earnings)\b', text, re.I):
        return 'earnings'
    if re.search(r'\bnvidia\b', text, re.I) and re.search(r'\b(board|investigat\w*)\b', text, re.I):
        return 'corporate_event'
    if re.search(r'\b(biogen|merck)\b', text, re.I) and re.search(r'\b(stops?|trial|studies)\b', text, re.I):
        return 'drug_development'
    if re.search(r'\bfed\b', text, re.I) and re.search(r'\b(cut|hike|rate|range)\b', text, re.I):
        return 'monetary_policy'
    return None


def display_decimal(value):
    return None if value is None else str(Decimal(str(value)).quantize(Decimal('0.0001')))


def board_query(data, catalog):
    from event_history.library import source_card
    raw = next(a for a in catalog['articles'] if a['id'] == 'board-wire')
    old_sources = json.loads((ROOT/'equities/sources.json').read_text())['sources']
    copied = {**data, 'events': list(data['events']), 'sources': dict(data['sources'])}
    sid = 'free-board-wire'
    copied['sources'][sid] = source_card(sid, old_sources['board_wire'])
    copied['sources'][sid].update(published_day=raw['published_day'], published_at=raw['published_at'])
    event = dict(id='nvidia-2026-board-replay', revision=1, title=raw['title'],
                 category='corporate_event', mechanism='unresolved_inquiry', stage='unresolved_inquiry',
                 primary_group='technology_equities', occurred_day=None,
                 public_day=raw['published_day'], public_at=raw['published_at'],
                 publication_source=sid, source_ids=[sid], episode_id='nvda-board-2026-11-08',
                 location=['US'], impact='company_specific', regime=None, severity=None,
                 targets=['NVDA'], historical_receipt_at=None, first_disclosure_verified=False,
                 summary=raw['summary'], weaknesses=['Attributed allegations are not established findings; company counterpoint retained.'])
    copied['events'].append(event)
    return copied, raw


def legacy_daily_cross_check():
    """Reuse the tested parent equity/calendar engine; do not create an equity fill."""
    script = """
import {loadEquities} from './equities/load.mjs';
import {reactionAt,rippleChecks} from './equities/engine.mjs';
const d=loadEquities(),pub='2026-11-08T20:00:00Z',asOf='2026-11-09T21:01:00Z';
const own=reactionAt(d.prices.rows,d.calendar,'NVDA',pub,asOf);
const peers=rippleChecks(d.prices.rows,d.calendar,pub,asOf);
console.log(JSON.stringify({own,comparisons:peers.comparisons}));
"""
    r = subprocess.run(['node','--input-type=module','-e',script], cwd=ROOT,
                       capture_output=True, text=True, check=True, timeout=30)
    parsed = json.loads(r.stdout)
    return dict(scope='retained secondary daily context only; not live or original-as-of verified',
                publication_at='2026-11-08T20:00:00Z', descriptive_cutoff='2026-11-09T21:01:00Z',
                own_percent=display_decimal(parsed['own']['first_close_percent'].get('exact')),
                peers=[dict(symbol=p['symbol'], percent=display_decimal(p['reaction']['first_close_percent'].get('exact')))
                       for p in parsed['comparisons']],
                baseline_date=parsed['own']['expected_baseline_session'],
                first_close_date=parsed['own']['expected_first_session'],
                opening_quote_status=parsed['own']['first_regular_open']['point']['status'],
                exact_opening_percent=parsed['own']['gap_percent']['exact'],
                verified_exchange_print_timestamps=False, original_availability_verified=False,
                upstream_providers_independent=False, causal_transmission_established=False)


def summarize_case(case, data, catalog):
    require(case in CASES, 'Unknown bounded demonstration case')
    id, _source = CASES[case]
    if case == 'nvidia_board':
        data, raw = board_query(data, catalog)
    else:
        raw = next((r for r in catalog['events'] if r['id'] == id), None)
    require(raw is not None, 'Event missing from pinned catalog')
    event = next(e for e in data['events'] if e['id'] == id)
    detected = detect(raw)
    require(detected == event['category'], 'Unsupported or contradictory event classification')
    historical_cutoff = iso(publication(event, data) + timedelta(microseconds=1))
    # This complete earlier decision is sealed BEFORE any forward response is read.
    decision = historical_decision(event, data, event['targets'][0], historical_cutoff)
    sealed = digest(decision)
    selection = decision['historical_matches']
    cohort = descriptive_cohort(event, data, event['targets'][0], historical_cutoff)
    cases = []
    for match in selection['matches']:
        old = next(e for e in data['events'] if e['id'] == match['id'])
        cases.append(dict(id=old['id'], title=old['title'], score=match['score'],
            instrument=match['comparison_instrument'], selected=old['id'] in selection['selected'],
            reasons=match['reasons'], weaknesses=match['weaknesses'],
            publication_day=old['public_day']))
    # These later measurements describe a historical window, not an earlier input.
    markets = list(dict.fromkeys([*event['targets'], 'eurusd', 'usdjpy']))
    prices = {}
    for market in markets:
        prices[market] = []
        for horizon in HORIZONS:
            measured = response(event, data, market, horizon, REFERENCE_CUTOFF)
            prices[market].append(dict(days=horizon, status=measured['status'],
                baseline_date=measured.get('baseline_date'), end_date=measured.get('end_date'),
                change_percent=display_decimal(measured['change_percent']),
                GBP_change_percent=display_decimal(measured.get('GBP', {}).get('change_percent')),
                GBP_status=measured.get('GBP', {}).get('status'),
                missing_FX_dates=measured.get('GBP', {}).get('missing_dates', []),
                unit=data['instruments'][market]['unit'],
                evidence='current_primary_reference' if measured['observations'] else 'unavailable',
                original_availability_verified=False))
    reported = [r for r in data['reported_reactions'] if r['event_id'] == id]
    source_ids = list(dict.fromkeys([*event['source_ids'],
                                   *[r['source_id'] for r in reported]]))
    sources = [dict(id=s, url=data['sources'][s]['url'],
                    publisher=data['sources'][s]['publisher'], locator=data['sources'][s]['locator'])
               for s in source_ids]
    count = len(cases)
    price_limit = ('Adjusted company prices and executable quotes are missing.'
                   if event['primary_group'] in ('technology_equities', 'pharmaceuticals') else
                   'Historical index and gold daily price windows are incomplete.'
                   if event['primary_group'] in ('stock_indices', 'currencies') else
                   'Daily reference prices are not timestamped executable quotes.')
    reason = (f'{count} earlier event comparisons were located. '
              'Original news and price availability is unproven. ' + price_limit)
    legacy = legacy_daily_cross_check() if case == 'nvidia_board' else None
    return dict(case=case, event_id=id, title=event['title'], detected_category=detected,
        mode='historical_research_replay_not_current_market_news',
        occurred_day=event['occurred_day'], supporting_publication_day=event['public_day'],
        supporting_publication_at=event['public_at'], actual_original_receipt_at=None,
        frozen_historical_cutoff=historical_cutoff, frozen_historical_decision=decision,
        frozen_decision_sha256=sealed, comparable_events=cases,
        selected_episode_count=len(selection['selected']), fully_as_of_qualified=0,
        retrospective_cohort={k: ({name: display_decimal(value) if name in ('median','minimum','maximum') else value
                                   for name,value in v.items()} if isinstance(v, dict) else v)
                              for k,v in cohort.items()},
        dated_reference_reactions=prices, separately_reported_reactions=reported,
        legacy_daily_cross_check=legacy,
        sources=sources, action='No Action',
        three_answers=dict(what_happened='Historical replay: ' + event['title'] + '.',
            likely_outcome='Uncertain. ' + reason,
            suggested_action='No Action. Observe only; this replay cannot support a paper entry or predict a repeat.'),
        trace=['Read and validate a sourced historical event item',
               'Detect its category with deterministic text rules',
               'Freeze prior comparisons without reading later returns',
               'Cross-check dated reference prices, peers and explicit gaps',
               'Produce three answers and journal an observation-only decision'],
        limitations=['Retrospective current-vintage reactions are outside the sealed earlier decision.',
                     'EUR/USD and USD/JPY are context references, not asserted event-caused ripples.',
                     'Daily reporting observations are not intraday quotes or an exchange trading calendar.',
                     'A public catalog receipt does not prove first disclosure or a fresh market-moving event.'])


def record_observation(directory, result, receipt):
    path, db = journal(directory)
    try:
        key = digest(dict(event=result['event_id'], decision=result['frozen_decision_sha256'],
                          protocol='DATA-FREE-1/1', policy=digest(result)))
        when = receipt['received_at']
        db.execute('BEGIN IMMEDIATE')
        prior = db.execute('SELECT first_recorded_at FROM decisions WHERE id=?', (key,)).fetchone()
        require(result['action'] == 'No Action', 'Observation-only journal refuses entry decisions')
        if prior is None:
            payload = dict(result=result, receipt=receipt, account_mutations=0, orders=0)
            db.execute('INSERT INTO decisions VALUES(?,?,?,?)',
                       (key, result['event_id'], when, canonical(payload)))
        db.commit()
        return dict(id=key, inserted=prior is None,
                    first_recorded_at=prior[0] if prior else when, orders=0, account_mutations=0)
    finally:
        db.close()


def run_case(case, directory, live_fetch=False, data=None, clock=utc, client=None):
    require(case in CASES, 'Unknown demonstration case')
    start = time.perf_counter()
    data = data or load_free_library()
    _id, source = CASES[case]
    if live_fetch:
        kwargs = dict(clock=clock)
        if client is not None:
            kwargs['client'] = client
        receipt = poll(directory, source, **kwargs)
        if receipt.get('normalized') is None:
            return dict(status='source_unavailable_or_cooldown', ingestion={k:v for k,v in receipt.items() if k!='normalized'},
                        action='No Action', cost_GBP='0.00', orders=0, account_mutations=0)
        catalog = receipt.pop('normalized')['data']
        receipt['origin'] = 'actual_anonymous_HTTP_receipt_of_pinned_historical_research_catalog'
    else:
        raw = (ROOT / SOURCES[source]['file']).read_bytes()
        catalog = normalize(source, raw)['data']
        receipt = dict(source=source, received_at=clock(), network_request=False,
                       payload_sha256=hashlib.sha256(raw).hexdigest(),
                       origin='actual_local_read_of_retained_historical_research_catalog')
    result = summarize_case(case, data, catalog)
    entry = record_observation(directory, result, receipt)
    return dict(schema_version=1, status='observation_recorded', result=result,
                ingestion=receipt, journal=entry,
                local_processing_ms=round((time.perf_counter()-start)*1000,3),
                cost_GBP='0.00', orders=0, account_mutations=0, continuous_monitoring=False,
                publication_to_useful_alert_latency_seconds=None)


def build_demo():
    data = load_free_library()
    cases = []
    for key, (_, source) in CASES.items():
        catalog = json.loads((ROOT / SOURCES[source]['file']).read_text())
        cases.append(summarize_case(key, data, catalog))
    return dict(schema_version=1, kind='reproducible_historical_process_demonstration',
                prepared_on='2026-11-17', coverage=coverage(data), cases=cases,
                paper_only=True, cost_GBP='0.00', supported_entries=0,
                fresh_financial_news_connected=False, continuous_monitoring=False,
                warning='Historical research replay. Missing prices and original availability remain unknown. No guarantees, live alert or executable recommendation.')
