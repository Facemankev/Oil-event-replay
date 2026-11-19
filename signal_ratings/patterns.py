"""Fixed after-complete-bar predicates. No news discovered later enters a signal."""
from decimal import Decimal as D
from .policy import POLICY

LABELS = {
    'spike': 'A sharp daily rise', 'dip': 'A sharp daily fall',
    'gap_up': 'An unusually large opening rise', 'gap_down': 'An unusually large opening fall',
    'trend_up': 'An established upward trend', 'trend_down': 'An established downward trend',
    'volume_up': 'Unusual volume with a rising price', 'volume_down': 'Unusual volume with a falling price',
    'spike_volume': 'A sharp rise with unusual volume', 'dip_volume': 'A sharp fall with unusual volume',
}


def matches(row):
    bad = {'possible_corporate_action_or_bad_print_needs_review', 'quote_on_reviewed_exchange_closure',
           'missing_numeric_close', 'missing_intermediate_source_bar_or_calendar_uncertain'}
    if bad.intersection(row['data_flags']) or row['return_span_sessions'] != 1:
        return []
    def number(key):
        return D(row[key]) if row.get(key) is not None else None
    z, gap, volume, change = [number(k) for k in ('return_z', 'gap_z', 'volume_ratio', 'close_change_percent')]
    volatility, trend = number('prior_volatility'), number('prior_trend')
    trend_score = trend / (volatility * D(20).sqrt()) if trend is not None and volatility is not None and volatility > 0 else None
    spike, dip = z is not None and z >= 3, z is not None and z <= -3
    high_volume = volume is not None and volume >= 3
    selected = dict(spike=spike, dip=dip, gap_up=gap is not None and gap >= 3,
                    gap_down=gap is not None and gap <= -3,
                    trend_up=trend_score is not None and trend_score >= 1,
                    trend_down=trend_score is not None and trend_score <= -1,
                    volume_up=high_volume and change is not None and change > 0,
                    volume_down=high_volume and change is not None and change < 0,
                    spike_volume=spike and high_volume, dip_volume=dip and high_volume)
    return [p for p in POLICY['patterns'] if selected[p]]


def select(features, calendar):
    """First qualifying row, not the largest later outcome; all patterns retained."""
    index = {day: i for i, day in enumerate(calendar)}
    groups = {(asset, pattern): [] for asset in POLICY['assets'] for pattern in POLICY['patterns']}
    last = {}
    for asset, rows in features.items():
        for row in rows:
            for pattern in matches(row):
                key = (asset, pattern)
                if key not in last or index[row['date']] - last[key] > 20:
                    groups[key].append(row)
                    last[key] = index[row['date']]
    return groups
