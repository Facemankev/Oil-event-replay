"""Outcome-blind comparisons and separately labelled retrospective measurements."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from statistics import median

from .library import GROUPS, HORIZONS, require

UTC = timezone.utc


def day(value):
    require(isinstance(value, str) and date.fromisoformat(value).isoformat() == value,
            'ISO observation date required')
    return value


def stamp(value):
    require(isinstance(value, str) and 'T' in value, 'Explicit timestamp required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.utcoffset() is not None, 'Explicit timezone required')
    return parsed.astimezone(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def eligible(source):
    if source.get('published_at'):
        return stamp(source['published_at'])
    if source.get('published_day'):
        # Deliberately conservative eligibility bound, never a claimed publication clock.
        return datetime.fromisoformat(day(source['published_day'])).replace(tzinfo=UTC) + timedelta(days=2)
    return None


def publication(event, data):
    return eligible(data['sources'][event['publication_source']])


def anchor(event):
    return (stamp(event['public_at']).date().isoformat()
            if event.get('public_at') else event.get('public_day'))


def visible_facts(event, data, as_of, require_receipt=False):
    """Filter clocks BEFORE projecting facts; outcomes are never projected."""
    cutoff = stamp(as_of)
    available = publication(event, data)
    if available is None or available > cutoff:
        return None
    if require_receipt and (not event.get('historical_receipt_at') or
                            stamp(event['historical_receipt_at']) > cutoff):
        return None
    scale = event.get('severity')
    if scale:
        ids = {scale['source_id'], *scale.get('supporting_source_ids', [])}
        clocks = [eligible(data['sources'][id]) for id in ids]
        scale = scale if all(known is not None and known <= cutoff for known in clocks) else None
    return {key: event.get(key) for key in
            ('id', 'title', 'category', 'mechanism', 'stage', 'impact', 'regime',
             'location', 'primary_group', 'episode_id', 'targets')} | {
                 'severity': scale,
                 'market_context': {'status': 'original_as_of_context_unverified',
                                    'price_trend_used_in_matching': False}}


def schedule(data, instrument):
    return [p['date'] for p in data['observations']
            if p['instrument'] == instrument and p['status'] == 'numeric']


def window_dates(event, data, instrument, horizon, through=None):
    """Dates only: selecting an interval cannot inspect its eventual price return."""
    require(horizon in HORIZONS and instrument in data['instruments'], 'Invalid horizon/instrument')
    boundary = anchor(event)
    if not boundary:
        return None
    dates = schedule(data, instrument)
    if through:
        dates = [d for d in dates if d <= through]
    prior = [d for d in dates if d < boundary]
    following = [d for d in dates if d > boundary]
    if not prior or len(following) < horizon:
        return None
    return dict(baseline=prior[-1], end=following[horizon - 1],
                path=[prior[-1], *following[:horizon]],
                context_from=prior[-21] if len(prior) >= 21 else None)


def _similarity(query, candidate):
    score = 0
    reasons, weaknesses = [], []
    for field, weight in [('category', 30), ('mechanism', 30), ('stage', 15)]:
        if query[field] == candidate[field]:
            score += weight
            reasons.append('same_' + field + ': ' + str(query[field]))
        else:
            weaknesses.append('different_' + field)
    if set(query['location']) & set(candidate['location']):
        score += 10
        reasons.append('shared_recorded_location')
    else:
        weaknesses.append('different_or_unmatched_location')
    a, b = query['severity'], candidate['severity']
    if a and b and a['scale'] == b['scale']:
        tolerance = 30 if a['scale'] == 'advisory_maximum_sustained_wind_mph' else 25
        if abs(a['value'] - b['value']) <= tolerance:
            score += 10
            reasons.append('comparable_recorded_scale')
        else:
            weaknesses.append('different_scale_magnitude')
    else:
        weaknesses.append('severity_unavailable_or_different_scale')
    if query['regime'] and candidate['regime'] == query['regime']:
        score += 5
        reasons.append('same_sourced_regime_label')
    else:
        weaknesses.append('different_or_unestablished_regime')
    if query['category'] == 'drug_development':
        weaknesses.append('A shared broad trial stage does not establish the same drug mechanism, patient population or endpoint.')
    core = (query['category'] == candidate['category'] and
            query['mechanism'] == candidate['mechanism'] and
            query['stage'] == candidate['stage'] and
            'different_or_unmatched_location' not in weaknesses and
            'different_scale_magnitude' not in weaknesses)
    return dict(score=score, similarity='Limited' if core else 'Weak',
                reasons=reasons, weaknesses=weaknesses, core_comparable=core)


def match_history(event, data, instrument, as_of, horizon=5):
    cutoff = stamp(as_of)
    query = visible_facts(event, data, as_of)
    if query is None:
        return dict(matches=[], selected=[], excluded=[{'reason': 'query_not_public_by_cutoff'}])
    require(instrument in query['targets'], 'Instrument outside recorded event scope')
    matches, excluded = [], []
    for other in sorted(data['events'], key=lambda e: (publication(e, data) or datetime.max.replace(tzinfo=UTC), e['id'])):
        facts = visible_facts(other, data, as_of)
        # Even the existence/episode of a future case cannot alter an earlier decision.
        if facts is None or publication(other, data) >= cutoff:
            continue
        if other['id'] == event['id'] or facts['episode_id'] == event['episode_id']:
            excluded.append(dict(id=other['id'], reason='self_or_same_episode'))
            continue
        # Filter before accessing future text/features; mutations cannot leak backwards.
        comparison_instrument = instrument if instrument in facts['targets'] else None
        group = data['instruments'][instrument]['group']
        if comparison_instrument is None and group in ('technology_equities', 'pharmaceuticals'):
            comparison_instrument = next((m for m in facts['targets']
                                          if data['instruments'][m]['group'] == group), None)
        if comparison_instrument is None or facts['category'] != query['category']:
            excluded.append(dict(id=other['id'], reason='different_category_or_instrument'))
            continue
        dates = window_dates(other, data, comparison_instrument, horizon,
                             (cutoff.date() - timedelta(days=1)).isoformat())
        result = _similarity(query, facts)
        if comparison_instrument != instrument:
            result['weaknesses'].append('different_issuer; only its own price response can be measured, never transferred to the query stock')
        if not dates or not dates['context_from']:
            result['weaknesses'].append('verified_response_schedule_unavailable')
        elif stamp(dates['end'] + 'T23:59:59.999999Z') >= cutoff:
            excluded.append(dict(id=other['id'], reason='response_window_not_mature'))
            continue
        matches.append(dict(id=other['id'], episode_id=other['episode_id'],
                            comparison_instrument=comparison_instrument,
                            public_after=iso(publication(other, data)), dates=dates, **result))
    # Chronological interval/episode selection is frozen before any outcome is read.
    chosen, episodes, end = [], set(), None
    candidates = [m for m in matches if m['core_comparable'] and m['dates'] and m['dates']['context_from']]
    candidates.sort(key=lambda m: (m['dates']['context_from'], m['id']))
    for item in candidates:
        if item['episode_id'] in episodes:
            excluded.append(dict(id=item['id'], reason='one_case_per_episode'))
        elif end and item['dates']['context_from'] <= end:
            excluded.append(dict(id=item['id'], reason='overlapping_context_and_response'))
        else:
            chosen.append(item['id'])
            episodes.add(item['episode_id'])
            end = item['dates']['end']
    matches.sort(key=lambda m: (-m['score'], m['public_after'], m['id']))
    return dict(matches=matches, selected=chosen, excluded=excluded,
                independence_established=False,
                selection_note='Outcome-blind taxonomy and dates; 21 prior reporting observations plus response window; one episode. This does not prove statistical independence.')


def historical_decision(event, data, instrument, as_of):
    facts = visible_facts(event, data, as_of)
    if facts is None:
        return dict(event_id=event['id'], as_of=as_of, action='No Action',
                    reasons=['event_not_public_by_cutoff'], historical_matches=[])
    matched = match_history(event, data, instrument, as_of)
    blockers = ['original_news_receipt_and_version_unproven',
                'original_price_and_FX_availability_unproven',
                'no_verified_executable_quote_or_instrument']
    if len(matched['selected']) < 8:
        blockers.append('fewer_than_eight_independent_qualified_cases')
    return dict(event_id=event['id'], as_of=as_of, action='No Action',
                facts=facts, historical_matches=matched, evidence='Limited', reasons=blockers,
                qualified_cases=0, point_in_time_safe=False,
                three_answers=dict(what_happened=facts['title'],
                                   likely_outcome='Uncertain. Comparable cases are limited and original evidence availability is unproven.',
                                   suggested_action='No Action. Historical patterns do not guarantee a repeat or support a paper entry.'))


def response(event, data, instrument, horizon, as_of):
    """Current-vintage description, kept OUTSIDE the historical decision function."""
    cutoff = stamp(as_of)
    dates = window_dates(event, data, instrument, horizon,
                         (cutoff.date() - timedelta(days=1)).isoformat())
    result = dict(instrument=instrument, days=horizon, status='price_series_or_window_unavailable',
                  change_percent=None, absolute_change=None, observations=[],
                  point_in_time_safe=False, verification='current_primary_table_only',
                  calendar=data['instruments'][instrument]['calendar'],
                  alignment='Last numeric day before the publication UTC day to Nth numeric day strictly after it; not an intraday reaction or tradable entry.')
    if not dates:
        return result
    if stamp(dates['end'] + 'T23:59:59.999999Z') > cutoff:
        result['status'] = 'response_not_yet_observed'
        return result
    points = {p['date']: p for p in data['observations'] if p['instrument'] == instrument
              and p['date'] in dates['path'] and p['date'] <= cutoff.date().isoformat()}
    path = [points[d] for d in dates['path']]
    start, end = Decimal(path[0]['value']), Decimal(path[-1]['value'])
    result.update(status='ok', baseline_date=dates['baseline'], end_date=dates['end'],
                  baseline=str(start), end=str(end), absolute_change=str(end - start), observations=path)
    if start > 0 and end > 0:
        result['change_percent'] = str((end / start - 1) * 100)
    else:
        result['status'] = 'nonpositive_price_percent_unavailable'
    if instrument in ('brent', 'wti'):
        fx = {p['date']: p for p in data['observations'] if p['instrument'] == 'gbpusd'}
        missing = [d for d in dates['path'] if not fx.get(d) or fx[d]['status'] != 'numeric']
        result['GBP'] = dict(status='missing_exact_date_FX' if missing else 'complete_current_reference_path',
                             missing_dates=missing, change_percent=None, executable=False)
        if not missing and start > 0 and end > 0:
            start_gbp = start / Decimal(fx[dates['baseline']]['value'])
            end_gbp = end / Decimal(fx[dates['end']]['value'])
            result['GBP']['change_percent'] = str((end_gbp / start_gbp - 1) * 100)
    return result


def summarize(values):
    numeric = [Decimal(str(v)) for v in values if v is not None]
    return dict(count=len(numeric), median=str(median(numeric)) if numeric else None,
                minimum=str(min(numeric)) if numeric else None, maximum=str(max(numeric)) if numeric else None,
                positive=sum(v > 0 for v in numeric), negative=sum(v < 0 for v in numeric),
                flat=sum(v == 0 for v in numeric))


def pre_event_context(event, data, instrument):
    points = [p for p in data['observations'] if p['instrument'] == instrument
              and p['status'] == 'numeric' and anchor(event) and p['date'] < anchor(event)][-21:]
    trend = None
    if len(points) == 21 and all(Decimal(p['value']) > 0 for p in points):
        trend = str((Decimal(points[-1]['value']) / Decimal(points[0]['value']) - 1) * 100)
    return dict(observations=len(points), from_date=points[0]['date'] if points else None,
                through_date=points[-1]['date'] if points else None, prior_20_observation_change=trend,
                scope='current-vintage descriptive context; not original-as-of evidence or a ranking input')


def descriptive_cohort(event, data, instrument, decision_cutoff):
    selection = match_history(event, data, instrument, decision_cutoff)
    selected = [e for e in data['events'] if e['id'] in selection['selected']]
    instruments = {m['id']: m['comparison_instrument'] for m in selection['matches']}
    rows = [response(e, data, instruments[e['id']], 5, decision_cutoff) for e in selected]
    return dict(selection_cutoff=decision_cutoff, selected_cases=len(selected), qualified_as_of_cases=0,
                current_vintage_reference=summarize(r['change_percent'] for r in rows),
                current_vintage_GBP=summarize(r.get('GBP', {}).get('change_percent') for r in rows),
                excluded_or_missing_paths=len(rows) - sum(r['change_percent'] is not None for r in rows),
                case_ids=[e['id'] for e in selected],
                caution='Retrospective description of the frozen selection, outside the decision. Unknown original vintages prevent historical trading inference; reported news percentages are not pooled.')


def ripple_paths(event):
    group = event['primary_group']
    if group == 'oil':
        channels = [('crude_supply_and_refinery_demand', ['brent', 'wti']),
                    ('GBP_reference_conversion_can_offset_USD_moves', ['gbpusd']),
                    ('downstream_inflation_and_consumption', [])]
    elif group in ('technology_equities', 'pharmaceuticals'):
        direct = [m for m in event['targets'] if m.isupper()]
        channels = [('issuer_specific_news', direct),
                    ('index_exposure_and_sector_or_risk_rotation', ['nasdaq_composite', 'gold_futures_reported']),
                    ('wider_demand_currency_and_input_cost_feedback', ['brent', 'wti', 'gbpusd'])]
    else:
        channels = [('policy_or_political_repricing', ['gbpusd', 'nasdaq_composite', 'gold_futures_reported']),
                    ('demand_and_USD_commodity_valuation', ['brent', 'wti']),
                    ('downstream_business_and_consumer_feedback', [])]
    return [dict(order=i, channel=channel, instruments=markets,
                 status='mechanism_hypothesis_not_demonstrated_causation',
                 measured_effect_isolated=False, historical_forecast=False)
            for i, (channel, markets) in enumerate(channels, 1)]


def market_role(event, instrument):
    if event['primary_group'] == 'oil' and instrument == 'gbpusd':
        return 'GBP_conversion_reference_not_a_claimed_FX_shock'
    if instrument in ('brent', 'wti') and event['primary_group'] == 'oil':
        return 'direct_reference_exposure'
    if instrument == event['targets'][0]:
        return 'direct_reference_exposure'
    return 'cross_market_research_hypothesis'


def drilldown(event, data, as_of):
    visible = visible_facts(event, data, as_of)
    if visible is None:
        return None
    reactions = {m: [response(event, data, m, h, as_of) for h in HORIZONS] for m in event['targets']}
    # Existing historicalSeries reader needs sourced snapshot IDs, dates and missing markers.
    price_sources = {s.get('snapshot_sha256'): dict(source_url=s['url'],
                     source_kind='current_primary_table', original_available_at=None)
                     for s in data['sources'].values() if s.get('snapshot_sha256')}
    for rows in reactions.values():
        for row in rows:
            row['sources'] = price_sources
            row['observations'] = [{**p, 'missing_code': None} for p in row['observations']]
    reports = [r for r in data['reported_reactions'] if r['event_id'] == event['id']
               and eligible(data['sources'][r['source_id']]) <= stamp(as_of)]
    references = [r for r in data['reference_comparisons'] if r['event_id'] == event['id']
                  and all(p['date'] < stamp(as_of).date().isoformat() for p in r['points'])]
    enriched_references = []
    for ref in references:
        a, b = [Decimal(p['close']) for p in ref['points']]
        ref = ref.copy()
        ref['percent'] = str((b / a - 1) * 100)
        enriched_references.append(ref)
    related = [dict(id=e['id'], title=e['title'], public_day=e['public_day'], stage=e['stage'])
               for e in data['events'] if e['episode_id'] == event['episode_id'] and e['id'] != event['id']
               and visible_facts(e, data, as_of) is not None]
    checked = [data['sources'][s].get('checked_on') for s in event['source_ids']]
    curation_day = max([d for d in checked if d] or ['2026-11-17'])
    notes = (event['weaknesses'] if stamp(as_of).date().isoformat() >= curation_day else
             ['Retrospective case notes hidden at this cutoff; original source versions are unverified.'])
    return dict(id=event['id'], title=event['title'], category=event['category'],
                geography=' / '.join(event['location']), occurred=dict(date=event['occurred_day'], at=event.get('occurred_at')),
                first_public=dict(date=event['public_day'], at=event['public_at'],
                                  status='supporting_publication_not_proven_first_disclosure'),
                actual_historical_receipt_at=None, facts=visible,
                evidence=[data['sources'][s] for s in event['source_ids']],
                weaknesses=notes, related_same_episode=related,
                reactions=dict(anchor=anchor(event), markets=reactions),
                market_roles={m: market_role(event, m) for m in event['targets']},
                reported_reactions=reports, reference_comparisons=enriched_references,
                pre_event_context={m: pre_event_context(event, data, m) for m in event['targets']},
                ripple_paths=ripple_paths(event),
                existing_UI_routes=[dict(id=event['id'], market=m) for m in ('brent', 'wti')
                                    if m in reactions and event.get('parent_path') == 'matching/cohort-catalog.json'],
                wider_asset_UI_enabled=False, causal_effect_established=False,
                ripple_note='Direct exposure, related markets and wider feedback are first/second/third-order research hypotheses. Co-movement or opposition does not establish transmission or causation.')


def evaluate(data, as_of='2026-11-17T23:59:59Z'):
    stamp(as_of)
    decisions, views = [], []
    # Seal every decision before computing ANY forward price response.
    for event in data['events']:
        available = publication(event, data)
        if available is None or available > stamp(as_of):
            continue
        cutoff = iso(available + timedelta(microseconds=1))
        decisions.append(historical_decision(event, data, event['targets'][0], cutoff))
    for event in data['events']:
        view = drilldown(event, data, as_of)
        if view:
            available = publication(event, data)
            view['frozen_selection_descriptive_cohort'] = descriptive_cohort(
                event, data, event['targets'][0], iso(available + timedelta(microseconds=1)))
            views.append(view)
    coverage = []
    for group in GROUPS:
        markets = [m for m, i in data['instruments'].items() if i['group'] == group]
        linked = [v for v in views if any(m in v['reactions']['markets'] for m in markets)]
        reported = [r for v in linked for r in v['reported_reactions'] if r['instrument'] in markets]
        coverage.append(dict(group=group, primary_events=sum(v['facts']['primary_group'] == group for v in views),
                             linked_events=len(linked), instruments=markets,
                             conversion_reference_links=sum(v['market_roles'].get(m) == 'GBP_conversion_reference_not_a_claimed_FX_shock'
                                                            for v in linked for m in markets),
                             statistics_scope='Coverage distribution across mixed events/instruments, not a comparable cohort or forecast. Linked counts overlap across groups.',
                             numeric_observations=sum(p['instrument'] in markets and p['status'] == 'numeric' for p in data['observations']),
                             reported_session_reactions=len(reported),
                             reported_signs=summarize(r['reported_percent'] for r in reported),
                             computed_horizons={str(h): summarize(r['change_percent'] for v in linked
                                 for m, rows in v['reactions']['markets'].items() if m in markets for r in rows if r['days'] == h)
                                 for h in HORIZONS},
                             as_of_qualified_cases=0, evidence='Limited'))
    return dict(schema_version=1, contract='HIST-1/read-only/1', as_of=as_of,
                event_count=len(data['events']), visible_events=len(views), sampling=data['sampling'], coverage=coverage,
                decisions=decisions, decisions_summary={'Buy': 0, 'No Action': len(decisions), 'paper_trades': 0},
                view_historical_events=views, point_in_time_safe=False,
                cost_assumptions=dict(scope='Historical gross reference reactions only; no net strategy return or executable trade.',
                                      inherited_declared_example=dict(fee_GBP_per_leg='0.01', full_spread_bp=10, slippage_bp_per_leg=5),
                                      provider_actual_costs_verified=False),
                limitations=['Selected case library, not all historical events or a representative strategy test.',
                             'Current-vintage price descriptions and rounded news-reported reactions are different evidence types.',
                             'No original historical receipt/version/price availability proof; no supported paper entry.',
                             'FRED removed LBMA gold; S&P reproduction restricted; adjusted share series and exact calendars missing.',
                             'LIVE-1 #37 can consume this read-only contract; no live provider or continuous monitoring added.'])
