"""Dated, sourced facts never become inferred historical receipt timestamps."""
import json
from datetime import datetime,time,timezone
from pathlib import Path
from urllib.parse import urlparse
from event_history.library import require

HERE=Path(__file__).resolve().parent
CATEGORIES={'unexplained','plausible','macro','multiple'}


def load_evidence(path=None):
    data=json.loads(Path(path or HERE/'evidence.json').read_text())
    require(data['schema_version']==1,'Unknown evidence schema')
    datetime.fromisoformat(data['researched_at'])
    for key,s in data['sources'].items():
        require(key==s['id'] and s['fact'] and s['publisher'],'Incomplete source')
        u=urlparse(s['url'])
        require(u.scheme=='https' and u.hostname and not u.username and not u.password,'Unsafe citation')
        datetime.fromisoformat(s['published_day'])
        require(s['precision'] in ('timestamp','day_only'),'Unknown publication precision')
        if s['published_at']:
            stamp=datetime.fromisoformat(s['published_at'].replace('Z','+00:00'))
            require(stamp.tzinfo is not None,'Publication timezone required')
            require(s['precision']=='timestamp','Precision drift')
        else:require(s['precision']=='day_only','Invented clock precision')
    for key,r in data['investigations'].items():
        require(r['category'] in CATEGORIES and r['causal_proof'] is False,'Unsupported causal claim')
        require(all(s in data['sources'] for s in r['sources']),'Missing citation')
        require(r['explanation'] and r['weakness'] and r['search'],'Incomplete investigation')
    controls=data['controls']
    require(len({c['id'] for c in controls})==len(controls),'Duplicate control')
    require(data['controls_registered_before_price_evaluation'] is True,'Controls not frozen')
    return data


def relation(source,day):
    """Close-bar evidence ordering only; never a claim it preceded the opening gap."""
    pubday=source['published_day']
    if pubday<day:return 'earlier_publication_receipt_unknown'
    if pubday>day:return 'later_corroboration_not_a_precursor'
    if not source['published_at']:return 'same_day_order_unknown_not_proven_precursor'
    from zoneinfo import ZoneInfo
    local=datetime.fromisoformat(source['published_at'].replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))
    # The library does not claim historical intraday/early-close calendars outside
    # the reviewed calendar. Same-day clocks are informative, never proven warnings.
    return 'same_day_timestamp_requires_session_clock_review'


def explanation(record,evidence):
    found=evidence['investigations'].get(record['id'])
    if not found:
        return dict(category='uninvestigated',confidence='limited',explanation='Not yet researched; retain this movement.',weakness='Outside the bounded top-per-family research budget.',sources=[],causal_proof=False)
    sources=[dict(evidence['sources'][s],timing=relation(evidence['sources'][s],record['date']),actual_historical_receipt_at=None) for s in found['sources']]
    timely=[s for s in sources if s['published_day']<=record['date']]
    category=found['category'] if timely else 'unexplained'
    return dict(found,sources=sources,category=category,confidence='moderate' if timely and category!='unexplained' else 'limited',
                confidence_basis='Source supports a possible association, not a causal estimate or probability. Intraday order and receipt may be unknown.',
                proven_early_warning=False,actual_historical_receipt_at=None)
