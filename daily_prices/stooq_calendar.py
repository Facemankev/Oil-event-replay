"""Bounded primary-announcement benchmark calendar; no vendor library or paid feed."""
import json
from datetime import date,timedelta
from pathlib import Path

CALENDAR=json.loads(Path(__file__).with_name('stooq-calendar.json').read_text())
YEARS={int(y) for y in CALENDAR['holidays']}
HOLIDAYS={d for days in CALENDAR['holidays'].values() for d in days}


def is_session(day):
    d=date.fromisoformat(day)
    if d.year not in YEARS:return None
    return d.weekday()<5 and day not in HOLIDAYS


def grid(rows):
    spy=rows['SPY'];start=min(spy);end=max(spy)
    # Outside reviewed years retain the union rather than silently assuming
    # that a SPY/GLD omission is a non-trading day.
    result={d for series in rows.values() for d in series if start<=d<=end and is_session(d) is None}
    d=date.fromisoformat(start)
    while d<=date.fromisoformat(end):
        day=d.isoformat()
        if is_session(day) is True:result.add(day)
        d+=timedelta(days=1)
    return sorted(result)


def verified(days):
    return bool(days) and all(is_session(d) is True for d in days)
