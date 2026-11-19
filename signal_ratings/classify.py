"""Research rating is independent of permission to trade."""
import json
from decimal import Decimal as D
from .policy import HERE, POLICY
from world_events.events import digest


def current_time():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def approved_validation(validation_id, key):
    """Only reviewed repository artifacts can attest independence, never caller flags."""
    registry = json.loads((HERE / 'registry.json').read_text())
    entry = registry['approved_independent_validations'].get(validation_id)
    if not entry:
        return None
    path = (HERE / entry['artifact']).resolve()
    if not path.is_relative_to(HERE) or not path.is_file():
        return None
    artifact = json.loads(path.read_text())
    if digest(artifact) != entry['sha256'] or entry['policy_sha256'] != digest(POLICY):
        return None
    required = ('primary_point_in_time_prices', 'usage_permitted', 'independence_audited',
                'registered_before_outcomes', 'costs_and_benchmark_audited', 'multiple_testing_reviewed')
    if artifact.get('candidate_key') != key or artifact.get('mode') != 'prospective_independent':
        return None
    if not all(artifact.get(k) is True for k in required):
        return None
    from datetime import datetime
    try:
        clocks = [datetime.fromisoformat(artifact[k].replace('Z', '+00:00')) for k in
                  ('training_ended_at', 'registered_at', 'first_prediction_at', 'first_outcome_at')]
        if not all(c.tzinfo is not None for c in clocks) or not all(a < b for a, b in zip(clocks, clocks[1:])):
            return None
        registered_policy = datetime.fromisoformat(POLICY['registered_at'].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(artifact['completed_at'].replace('Z', '+00:00'))
        if clocks[1] < registered_policy or completed.tzinfo is None or not clocks[-1] < completed <= current_time():
            return None
        if artifact['independent_examples'] < POLICY['likely']['min_independent']:
            return None
        if artifact['time_blocks'] < POLICY['likely']['min_time_blocks']:
            return None
        if D(artifact['coverage']) < D(POLICY['likely']['min_coverage']):
            return None
        # Reviewed robustness must survive stress costs, SPY and matched controls.
        if any(not D(artifact[k]).is_finite() or D(artifact[k]) <= 0 for k in ('mean_directional_net_stressed',
               'median_directional_net_stressed', 'benchmark_excess', 'control_excess',
               'block_robustness_lower_bound')):
            return None
    except (KeyError, ValueError, TypeError, ArithmeticError):
        return None
    return artifact


def classify(card, cost='declared'):
    """Classify a frozen historical hypothesis; no success-rate-to-probability conversion."""
    stats = card['costs'][cost]
    rule = POLICY['possible']
    reasons = []
    if stats['complete'] < rule['min_complete']:
        reasons.append('Too few complete historical examples.')
    if D(stats['coverage']) < D(rule['min_coverage']):
        reasons.append('Too many examples lack exact prices, benchmark or exchange-rate data.')
    if stats['distinct_years'] < rule['min_distinct_years']:
        reasons.append('The sample covers too few different years.')
    if stats['later_complete'] < rule['min_later_complete']:
        reasons.append('Too few complete examples in the later, already examined period.')
    if stats['control_pairs'] < rule['min_control_pairs']:
        reasons.append('Too few comparable periods without an unusual price/volume signal.')
    direction = 1 if card['direction'] == 'UP' else -1
    for field, message in (
        ('mean_return_percent', 'Average historical movement does not support this direction.'),
        ('median_return_percent', 'The middle historical outcome does not support this direction.'),
        ('mean_net_gbp', 'Average performance after these costs conflicts with the hypothesis.'),
        ('median_net_gbp', 'Typical performance after these costs conflicts with the hypothesis.'),
        ('later_mean_return_percent', 'Later examined examples do not support this direction.'),
        ('later_median_return_percent', 'The later middle outcome conflicts with this direction.'),
        ('median_paired_difference_gbp', 'Matched quiet periods do not support an advantage.')):
        if stats[field] is None or direction * D(stats[field]) <= 0:
            reasons.append(message)
    if card['instrument'] != 'SPY':
        if stats['median_SPY_excess_pp'] is None or direction * D(stats['median_SPY_excess_pp']) <= 0:
            reasons.append('The typical movement does not support this direction relative to SPY.')
        if stats['median_net_SPY_excess_gbp'] is None or direction * D(stats['median_net_SPY_excess_gbp']) <= 0:
            reasons.append('After-cost performance against SPY does not support this direction.')
    else:
        # Self-relative excess is always zero, not a measured stock-selection edge.
        if stats['median_SPY_excess_pp'] is None:
            reasons.append('An exact SPY reference is unavailable.')
    rating = 'NO ACTION' if reasons else 'POSSIBLE'
    validation = approved_validation(card.get('validation_id'), card['id'])
    if rating == 'POSSIBLE' and validation is not None:
        rating = 'LIKELY'
    return dict(rating=rating, direction=card['direction'] if rating != 'NO ACTION' else None,
                horizon=card['horizon'] if rating != 'NO ACTION' else None,
                reasons=reasons or ['A fixed historical hypothesis has supporting, exploratory results.'],
                independently_validated=validation is not None,
                historical_success_is_forecast_probability=False,
                current_signal=False, execution_action='No Action',
                confirmation=['Verify adjusted prices, original availability and realistic instrument costs.',
                              'Find timely, corroborated company or market evidence for a genuinely new event.',
                              'Lock a new paper prediction before its outcome and validate independent episodes.'],
                downside_scope='DOWN means watch for downside risk; no short-profit or short-order model.' if direction < 0 else None,
                label='Independently validated pattern; no current signal' if rating == 'LIKELY'
                      else 'Exploratory historical pattern' if rating == 'POSSIBLE'
                      else 'Insufficient or conflicting historical evidence')


def rank_key(card, cost='declared'):
    result = card['ratings'][cost]
    stats = card['costs'][cost]
    grade = {'LIKELY': 2, 'POSSIBLE': 1, 'NO ACTION': 0}[result['rating']]
    adverse = abs(min(D(0), D(stats['worst_directional_return_percent'] or '0')))
    return (-grade, -D(stats['coverage']), -min(stats['complete'], 100),
            -stats['distinct_years'], -stats['control_pairs'], adverse,
            -abs(D(stats['median_return_percent'] or '0')), card['id'])
