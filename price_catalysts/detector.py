"""Past-only per-instrument features. Rankings are discovery, never predictions."""
import json
from collections import deque
from datetime import date,timedelta
from decimal import Decimal as D
from pathlib import Path
from statistics import median

from daily_prices.stooq_calendar import is_session,verified
from event_history.library import require
from world_events.events import digest

HERE=Path(__file__).resolve().parent
PROTOCOL=json.loads((HERE/'protocol.json').read_text())
require(digest(PROTOCOL)==(HERE/'PROTOCOL.sha256').read_text().strip(),'Research protocol changed')


def text_number(x):
    return None if x is None else str(x.quantize(D('0.000001')))


def distribution(values):
    nums=[v for v in values if v is not None]
    if len(nums)<PROTOCOL['features']['minimum_history']:return None,None
    avg=sum(nums)/len(nums)
    sd=(sum((x-avg)**2 for x in nums)/(len(nums)-1)).sqrt()
    return avg,sd


def standardized(value,past):
    avg,sd=distribution(past)
    return None if value is None or sd is None or sd==0 else (value-avg)/sd


def sessions(selections):
    points={r['date'] for s in selections.values() for r in s['rows']}
    start=date.fromisoformat(min(points));end=date.fromisoformat(max(points))
    # Announced calendars are only reviewed for 2023-2026. Before that,
    # the union exposes observed gaps without declaring shared gaps holidays.
    out={d for d in points if is_session(d) is None}
    while start<=end:
        day=start.isoformat()
        if is_session(day) is True:out.add(day)
        start+=timedelta(days=1)
    return sorted(out)


def one_series(symbol,points,spy_points,calendar):
    idx={d:i for i,d in enumerate(calendar)};spy={r['date']:r for r in spy_points}
    by_day={r['date']:r for r in points};raw_returns=deque(maxlen=60);raw_gaps=deque(maxlen=60)
    active_returns=deque(maxlen=60);volumes=deque(maxlen=60);output=[]
    previous=None
    for r in points:
        day=r['date'];flags=[];ret=gap=active=None;span=None
        if is_session(day) is False:flags.append('quote_on_reviewed_exchange_closure')
        numeric=r['status']=='numeric' and r.get('close') is not None
        if not numeric:flags.append('missing_numeric_close')
        close=D(r['close']) if numeric else None
        raw_move=None
        if previous is not None and numeric:
            prior=previous['date'];span=idx.get(day,0)-idx.get(prior,0)
            raw_move=close/D(previous['close'])-1
            if span!=1:flags.append('missing_intermediate_source_bar_or_calendar_uncertain')
            if span==1 and not flags:
                ret=raw_move
                if r.get('open') is not None:gap=D(r['open'])/D(previous['close'])-1
                a=spy.get(day);b=spy.get(prior)
                if a and b and a['status']==b['status']=='numeric':
                    active=ret-(D(a['close'])/D(b['close'])-1)
                else:flags.append('missing_exact_SPY_interval')
        volume=None if r.get('volume') is None else D(r['volume'])
        past_volume=[x for x in volumes if x is not None and x>0]
        ratio=volume/median(past_volume) if volume is not None and len(past_volume)>=20 else None
        rz=standardized(ret,raw_returns);gz=standardized(gap,raw_gaps);az=standardized(active,active_returns)
        multi={};_,sd=distribution(raw_returns)
        for h in PROTOCOL['features']['multi_session_horizons']:
            pos=idx.get(day,-1);days=calendar[max(0,pos-h):pos+1]
            complete=len(days)==h+1 and all(d in by_day and by_day[d]['status']=='numeric' for d in days)
            move=close/D(by_day[days[0]]['close'])-1 if complete else None
            score=move/(sd*D(h).sqrt()) if move is not None and sd is not None and sd>0 else None
            multi[str(h)]=dict(change_percent=text_number(None if move is None else move*100),z=text_number(score))
        if ret is not None and any(abs((1+ret)-x)<=D('0.02')*x for x in (D('.1'),D('.2'),D('.25'),D('.333333'),D('.5'),D('2'),D('3'),D('4'),D('5'),D('10'))):
            flags.append('possible_corporate_action_or_bad_print_needs_review')
        scores=[x for x in (rz,gz,az) if x is not None]
        scores += [D(v['z']) for v in multi.values() if v['z'] is not None]
        trigger=any(abs(x)>=D(PROTOCOL['features']['anomaly_z']) for x in scores) or ratio is not None and ratio>=D(PROTOCOL['features']['volume_ratio'])
        prior_trend=None
        if previous is not None and idx.get(previous['date'],-1)>=20:
            older=by_day.get(calendar[idx[previous['date']]-20])
            if older and older['status']=='numeric':
                prior_trend=D(previous['close'])/D(older['close'])-1
        output.append(dict(id=symbol+'-'+day,instrument=symbol,date=day,
            prior_volatility=text_number(sd),prior_trend=text_number(prior_trend),
            close_change_percent=text_number(None if raw_move is None else raw_move*100),return_span_sessions=span,
            overnight_gap_percent=text_number(None if gap is None else gap*100),return_z=text_number(rz),gap_z=text_number(gz),
            SPY_excess_percentage_points=text_number(None if active is None else active*100),SPY_active_z=text_number(az),
            volume_ratio=text_number(ratio),prior_positive_volume_count=len(past_volume),prior_return_count=sum(v is not None for v in raw_returns),
            multi_session=multi,trigger=bool(trigger),data_flags=flags,
            calendar_verified=verified([previous['date'],day]) if previous else False,
            original_available_at=None,actual_historical_detection_at=None,
            detection_assumption='Only after the complete source bar; historical receipt was not recorded.',
            basis='Owner supplied Close/OHLC/Volume; adjustments/source authentication unverified; no re-adjustment.'))
        raw_returns.append(ret);raw_gaps.append(gap);active_returns.append(active);volumes.append(volume)
        previous=r if numeric else None
    return output


def rank(features):
    out={};focus={}
    for symbol,rows in features.items():
        def number(r,key):return None if r.get(key) is None else D(r[key])
        families={
          'rise':lambda r:number(r,'close_change_percent') if r['return_span_sessions']==1 and (number(r,'close_change_percent') or 0)>0 else None,
          'fall':lambda r:-number(r,'close_change_percent') if r['return_span_sessions']==1 and (number(r,'close_change_percent') or 0)<0 else None,
          'overnight_gap':lambda r:abs(number(r,'overnight_gap_percent')) if number(r,'overnight_gap_percent') is not None else None,
          'volume':lambda r:number(r,'volume_ratio'),
          'SPY_abnormal':lambda r:abs(number(r,'SPY_excess_percentage_points')) if symbol!='SPY' and number(r,'SPY_excess_percentage_points') is not None else None,
          'multi_session':lambda r:max([abs(D(v['z'])) for v in r['multi_session'].values() if v['z'] is not None],default=None),
        }
        out[symbol]={}
        for family,score in families.items():
            candidates=[(score(r),r) for r in rows if score(r) is not None]
            chosen=sorted(candidates,key=lambda pair:(-pair[0],pair[1]['date']))[:PROTOCOL['ranking']['top_per_family']]
            out[symbol][family]=[dict(r,ranking_family=family,rank=i+1,ranking_score=text_number(value),research_lane='outcome_selected_retrospective_discovery') for i,(value,r) in enumerate(chosen)]
            for value,r in chosen[:PROTOCOL['ranking']['investigate_top_per_family']]:
                item=focus.setdefault(r['id'],dict(r,selected_by=[]))
                item['selected_by'].append(family)
    return out,list(sorted(focus.values(),key=lambda r:(r['instrument'],r['date'])))


def detect(selections):
    calendar=sessions(selections)
    features={symbol:one_series(symbol,s['rows'],selections['SPY']['rows'],calendar) for symbol,s in selections.items()}
    rankings,focus=rank(features)
    return dict(kind='PRIVATE_OUTCOME_SELECTED_price_discovery',protocol=PROTOCOL,
        capture_fingerprints={symbol:s['capture']['payload_sha256'] for symbol,s in selections.items()},
        source_rows=sum(len(s['rows']) for s in selections.values()),features=features,rankings=rankings,focus=focus,
        untouched_historical_validation=False,prospective_predictions=0,
        limitations=['Ranks use realized bar movements; they are not a forecast or causal explanation.',
          'Volume adjustments, splits/dividends, bad prints, surviving-asset selection and missing benchmark/calendar evidence remain unresolved.',
          'No data, percentages, detailed ledger or price rows may be published as public app/CI data.'])
