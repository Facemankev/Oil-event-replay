"""Private fixed-pattern aggregation with strict maturity cutoffs and shared SIM costs."""
from bisect import bisect_right
from collections import Counter
from decimal import Decimal as D
from statistics import median

from event_history.library import require
from price_catalysts.detector import sessions
from price_catalysts.evidence import load_evidence, explanation
from price_catalysts.replay import Evaluator, prior_control, period, reaction
from simulations.engine import PROTOCOL as SIM, q
from world_events.events import digest
from .classify import classify, rank_key
from .patterns import select, LABELS
from .policy import POLICY


def average(values):
    return q(sum(values) / len(values)) if values else None


def middle(values):
    return q(median(values)) if values else None


def summarize(members, windows, direction, cost):
    """Same complete cohort for rates, price returns, FX/costs and SPY; missing stays counted."""
    sign = D(1 if direction == 'UP' else -1)
    good, pairs, missing = [], [], Counter()
    for member in members:
        window = windows[member['window']]
        outcome = window['costs'][cost]
        price = window['entry_reaction']
        if (outcome['status'] != 'simulated_reference_path'
                or window['SPY_costs'][cost]['status'] != 'simulated_reference_path'
                or price['SPY_excess_percentage_points'] is None):
            missing[outcome.get('reason', price['SPY_status'])] += 1
            continue
        good.append((member, window))
        control = windows.get(member['control_window'])
        if control and control['costs'][cost]['status'] == 'simulated_reference_path':
            pairs.append(D(outcome['net_pnl_gbp']) - D(control['costs'][cost]['net_pnl_gbp']))
    returns = [D(w['entry_reaction']['change_percent']) for _, w in good]
    excess = [D(w['entry_reaction']['SPY_excess_percentage_points']) for _, w in good]
    nets = [D(w['costs'][cost]['net_pnl_gbp']) for _, w in good]
    net_excess = [D(w['costs'][cost]['net_pnl_gbp']) - D(w['SPY_costs'][cost]['net_pnl_gbp']) for _, w in good]
    friction = [D(w['costs'][cost]['total_friction_gbp']) for _, w in good]
    later = [D(w['entry_reaction']['change_percent']) for m, w in good if m['period'] == 'later_exploratory_already_examined']
    count = len(good)
    successes = sum(sign * value > 0 for value in returns)
    failures = sum(sign * value < 0 for value in returns)
    return dict(attempts=len(members), complete=count, missing=len(members) - count,
                coverage=q(D(count) / len(members)) if members else '0',
                nonoverlapping_windows=count, independent_examples_verified=0,
                distinct_years=len({w['detection_day'][:4] for _, w in good}),
                successful=successes, unsuccessful=failures, unchanged=count-successes-failures,
                historical_success_percent=q(D(successes) / count * 100) if count else None,
                historical_failure_percent=q(D(failures) / count * 100) if count else None,
                success_definition='Observed USD entry-to-exit price direction, not net profit or a forecast probability.',
                mean_return_percent=average(returns), median_return_percent=middle(returns),
                minimum_return_percent=q(min(returns)) if returns else None,
                maximum_return_percent=q(max(returns)) if returns else None,
                worst_directional_return_percent=q(min(sign * r for r in returns)) if returns else None,
                mean_SPY_excess_pp=average(excess), median_SPY_excess_pp=middle(excess),
                mean_net_gbp=average(nets), median_net_gbp=middle(nets),
                mean_net_SPY_excess_gbp=average(net_excess), median_net_SPY_excess_gbp=middle(net_excess),
                net_winning=sum(v > 0 for v in nets), net_losing=sum(v < 0 for v in nets),
                mean_estimated_friction_gbp=average(friction), cost_assumptions=SIM['costs'][cost],
                allocation_gbp=SIM['allocation_gbp'], costs_are_illustrative_not_broker_quote=True,
                later_complete=len(later), later_mean_return_percent=average(later), later_median_return_percent=middle(later),
                control_pairs=len(pairs), missing_control_pairs=count-len(pairs),
                mean_paired_difference_gbp=average(pairs), median_paired_difference_gbp=middle(pairs),
                missing_reasons=dict(sorted(missing.items())),
                short_profit_modelled=False, price_basis='As-supplied Close; adjustment method and original vintage unverified.')


def assess(report, as_of):
    """A historical assessment can only use completed earlier outcomes, never future results."""
    windows = report['windows']
    cards = []
    for group in report['groups']:
        members = [m for m in group['members'] if windows[m['window']]['maturity_day'] < as_of
                   and windows[m['window']]['detection_day'] < as_of
                   and m['period'] != 'embargo']
        for direction in POLICY['directions']:
            key = f"{group['instrument']}:{group['pattern']}:{direction}:{group['horizon']}"
            card = dict(id=key, instrument=group['instrument'], pattern=group['pattern'],
                        title=LABELS[group['pattern']], direction=direction, horizon=group['horizon'],
                        as_of=as_of, research_scope='exploratory_examined_history', validation_id=None,
                        member_ids=[m['window'] for m in members], control_ids=[m['control_window'] for m in members],
                        costs={c:summarize(members, windows, direction, c) for c in POLICY['costs']})
            card['ratings'] = {c:classify(card, c) for c in POLICY['costs']}
            cards.append(card)
    cards.sort(key=rank_key)
    return cards


def build(scan, selections, ledger, as_of, data=None):
    require(scan['capture_fingerprints'] == {s:r['capture']['payload_sha256'] for s,r in selections.items()},
            'Scan does not match the explicitly selected captures')
    require(ledger['capture_fingerprints'] == scan['capture_fingerprints'], 'Parent ledger capture mismatch')
    evaluator = Evaluator(selections, data)
    calendar = evaluator.calendar
    index = {d:i for i,d in enumerate(calendar)}
    evidence = load_evidence()
    groups, windows, control_cache = [], {}, {}

    def measure(row, horizon):
        key = f"{row['id']}:{horizon}"
        if key in windows:
            return key
        entry = bisect_right(calendar, row['date'])
        if entry + horizon >= len(calendar):
            return None  # No outcome available yet; recorded as pending below, not shifted.
        window = evaluator.window(row['instrument'], row['date'], horizon)
        window = dict(window, detection_day=row['date'], instrument=row['instrument'],
                      maturity_day=calendar[entry+horizon],
                      entry_reaction=reaction(evaluator.rows[row['instrument']], evaluator.rows['SPY'],
                                              calendar[entry], horizon, calendar),
                      evidence=explanation(row, evidence),
                      retrospective_catalyst_tags_not_decision_inputs=True)
        windows[key] = window
        return key

    pending = []
    for (asset, pattern), rows in select(scan['features'], calendar).items():
        members_by_horizon = {h:[] for h in POLICY['horizons']}
        for row in rows:
            if row['id'] not in control_cache:
                control_cache[row['id']] = prior_control(row, scan['features'][asset], calendar)
            control = control_cache[row['id']]
            for h in POLICY['horizons']:
                key = measure(row, h)
                if key is None:
                    pending.append(dict(instrument=asset, pattern=pattern, horizon=h, date=row['date'],
                                        reason='Full later window not available; excluded from matured statistics.'))
                    continue
                control_key = measure(control, h) if control else None
                members_by_horizon[h].append(dict(window=key, control_window=control_key,
                                                   period=period(row['date'], calendar)))
        for h, members in members_by_horizon.items():
            groups.append(dict(instrument=asset, pattern=pattern, horizon=h, members=members))
    result = dict(schema_version=1, kind='PRIVATE_SIGNAL1_EXPLORATORY', policy=POLICY,
                  policy_sha256=digest(POLICY), source_rows=scan['source_rows'],
                  capture_fingerprints=scan['capture_fingerprints'], groups=groups, windows=windows,
                  pending=pending, issuer_controls=ledger['independent_catalyst_controls'],
                  issuer_control_summary=ledger['independent_control_summary'],
                  source_facts=evidence['sources'], all_history_previously_examined=True,
                  holdout_changed=False, trained_model=False, approved_current_signals=0,
                  current_market=dict(rating='NO ACTION', reason='No verified fresh news/price feed or qualified current signal. Historical patterns do not establish a current event.',
                                      direction=None, horizon=None, execution_action='No Action'),
                  limitations=['Private current-vintage files; adjustments, original receipt and executable prices unverified.',
                               'All histories already examined; Possible is exploratory, never an untouched test or a forecast.',
                               'Non-overlapping windows are not proven independent. Patterns and horizons share episodes.',
                               'Historical success means observed direction, not forecast probability; DOWN is risk watch, never a modelled short profit.',
                               'Catalyst tags were researched after price discovery and never enter earlier signal selection or rating.',
                               'Matched quiet periods and issuer-calendar controls are different comparisons; no quiet future returns were selected.',
                               'Pre-2023 calendar is an unverified supplied-date union; no missing prices or FX are filled.',
                               'No source promotion, original writes, account mutations, live orders, public price results or paid services.'])
    result['as_of'] = as_of
    result['cards'] = assess(result, as_of)
    result['rating_counts'] = {cost:dict(Counter(c['ratings'][cost]['rating'] for c in result['cards'])) for cost in POLICY['costs']}
    return result
