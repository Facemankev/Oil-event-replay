"""Deterministic plans first, future reference measurements second; no order API."""
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
from statistics import median

from event_history.engine import publication, iso, visible_facts, historical_decision, market_role
from event_history.library import ROOT, require
from free_pilot.data import load_free_library
from world_events.events import digest

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / 'protocol.json').read_text())
D = Decimal


def q(value):
    return None if value is None else str(D(value).quantize(D('0.0001')))


def indexed(data):
    rows = {}
    for p in data['observations']:
        rows.setdefault(p['instrument'], {})[p['date']] = p
    return rows


def gbp_point(rows, market, day):
    """No carry-forward FX, synthetic quote or substitution from another asset."""
    p = rows.get(market, {}).get(day)
    if not p or p['status'] != 'numeric':
        return None, 'missing_numeric_price'
    value = D(p['value'])
    if not value.is_finite() or value <= 0:
        return None, 'nonpositive_price_not_a_supported_fractional_exposure'
    fx = rows.get('gbpusd', {}).get(day)
    if not fx or fx['status'] != 'numeric' or D(fx['value']) <= 0:
        return None, 'missing_exact_date_GBP_FX'
    # A GBP/USD quote is USD per GBP: one USD buys 1/quote GBP.
    if market == 'gbpusd':
        price = 1 / value  # one USD in GBP: explicitly USD cash, not GBP bought with itself
    elif market == 'usdjpy':
        price = 1 / value / D(fx['value'])  # one JPY in GBP, never quote direction reversed
    else:
        price = value / D(fx['value'])
    return dict(date=day, reference_gbp=str(price), raw_value=p['value'],
                raw_unit='JPY per USD' if market == 'usdjpy' else 'USD per GBP' if market == 'gbpusd' else 'USD per unit',
                fx_USD_per_GBP=fx['value'], source_id=p['source_id'],
                snapshot_id=p['snapshot_id'], fx_snapshot_id=fx['snapshot_id']), None


def context(data, market, cutoff):
    rows = indexed(data)
    past = sorted(d for d,p in rows.get(market, {}).items()
                  if d < cutoff[:10] and p['status'] == 'numeric')[-PROTOCOL['context_observations']:]
    points = [gbp_point(rows,market,d)[0] for d in past]
    if len(points) != PROTOCOL['context_observations'] or any(p is None for p in points):
        return dict(status='missing_exact_context', trend=None, points=[])
    move = D(points[-1]['reference_gbp']) / D(points[0]['reference_gbp']) - 1
    return dict(status='current_vintage_context_only', trend='up' if move > 0 else 'down' if move < 0 else 'flat',
                change_percent=q(move*100), past_input_sha256=digest(points),
                points=[p | {'reference_gbp':q(p['reference_gbp'])} for p in points])


def plan(event, data, market, rule='event_long', horizon=5):
    require(rule in PROTOCOL['rules'] and horizon in PROTOCOL['horizons'], 'Unknown predefined strategy')
    require(market in event['targets'], 'Market outside sourced event scope')
    available = publication(event,data)
    if available is None:
        return dict(event_id=event['id'],market=market,rule=rule,horizon=horizon,
                    hypothetical_intent='No Action',status='publication_unknown',decision_bound=None)
    cutoff = iso(available + timedelta(microseconds=1))
    facts = visible_facts(event,data,cutoff)
    ctx = context(data,market,cutoff)
    role=market_role(event,market)
    active = rule == 'event_long' or (rule == 'momentum_up' and ctx['trend'] == 'up') or (
        rule == 'reversal_down' and ctx['trend'] == 'down')
    conversion_only=role=='GBP_conversion_reference_not_a_claimed_FX_shock'
    if conversion_only:active=False
    payload = dict(event_id=event['id'], episode_id=facts['episode_id'], title=facts['title'],
        publication_source=event['publication_source'],
        category=facts['category'], location=facts['location'], mechanism=facts['mechanism'],
        market=market, market_role=role, exposure='GBP-funded USD cash' if market=='gbpusd' else 'unleveraged reference units',
        rule=rule, horizon=horizon, decision_bound=cutoff,
        publication_precision='supporting_timestamp' if event.get('public_at') else 'conservative_day_only_eligibility_bound_not_publication_time',
        context=ctx, hypothetical_intent='Conditional hypothetical Buy' if active else 'No Action',
        status='conversion_context_not_independent_signal' if conversion_only else 'planned' if active else 'rule_does_not_trigger_or_context_missing',
        entry_rule=PROTOCOL['entry'], exit_rule=PROTOCOL['exit'],
        allocation_gbp=PROTOCOL['allocation_gbp'], validated_action='No Action',
        original_availability_verified=False, execution_supported=False,
        protocol_sha256=digest(PROTOCOL))
    return payload | {'plan_sha256':digest(payload)}


def measure(planned, data, cost='declared', allocation=None, cash=None, risk_exit=True):
    """Settle a frozen hypothesis. Its plan is never changed by later observations."""
    require(cost in PROTOCOL['costs'], 'Unknown cost scenario')
    cash = D(PROTOCOL['initial_cash_gbp'] if cash is None else str(cash))
    allocation = D(PROTOCOL['allocation_gbp'] if allocation is None else str(allocation))
    require(cash.is_finite() and allocation.is_finite() and cash > 0 and allocation > 0
            and allocation <= cash * D(PROTOCOL['max_allocation_fraction']), 'Cash/allocation limit')
    base = dict(event_id=planned['event_id'],market=planned['market'],rule=planned['rule'],
        horizon=planned['horizon'],cost=cost,status='not_entered',reason=planned['status'],
        entry_date=None,exit_date=None,net_pnl_gbp=None,gross_pnl_gbp=None,path=[],actions=[])
    if planned['hypothetical_intent'] != 'Conditional hypothetical Buy':
        return base
    market=planned['market']; rows=indexed(data)
    days=sorted(d for d,p in rows.get(market,{}).items()
                if d > planned['decision_bound'][:10] and p['status']=='numeric')
    if not days:
        return base | dict(reason='no_later_numeric_price')
    if (date.fromisoformat(days[0])-date.fromisoformat(planned['decision_bound'][:10])).days > PROTOCOL['max_entry_delay_calendar_days']:
        return base | dict(reason='entry_outside_predefined_delay_limit')
    # Select dates without looking at price direction. Missing FX never shifts entry.
    chosen=days[:planned['horizon']+1]
    first,error=gbp_point(rows,market,chosen[0])
    if error:
        return base | dict(reason=error,missing_date=chosen[0],attempted_entry_date=chosen[0])
    cfg={k:D(v) for k,v in PROTOCOL['costs'][cost].items()}
    fee=cfg['fee_gbp_per_leg']; friction=(cfg['spread_bps']/2+cfg['slippage_bps_per_leg'])/10000
    require(2*fee < allocation and 0 <= friction < 1, 'Unaffordable costs')
    start=D(first['reference_gbp']); units=(allocation-2*fee)/(start*(1+friction))
    # Reserve liquidation cost in all marked values, including the opening day.
    peak=cash; max_dd=D(0); path=[]; actions=[]; reason='fixed_horizon'
    for i,day in enumerate(chosen):
        p,error=gbp_point(rows,market,day)
        if i and (date.fromisoformat(day)-date.fromisoformat(chosen[i-1])).days > PROTOCOL['max_reporting_gap_calendar_days']:
            error='unverified_gap_exceeds_calendar_limit'
        if error:
            return base | dict(status='unsettled_reference_path',reason=error,entry_date=chosen[0],
                               missing_date=day,path=path,actions=actions)
        price=D(p['reference_gbp']); liquid=units*price*(1-friction)
        equity=cash-allocation+liquid
        peak=max(peak,equity); max_dd=max(max_dd,(peak-equity)/peak*100)
        stop=risk_exit and i>0 and price/start-1 <= -D(PROTOCOL['risk_review_loss_fraction'])
        finished=stop or i==planned['horizon']
        action='Hypothetical Buy' if i==0 else 'Hypothetical Sell' if finished else 'Hypothetical Hold'
        path.append(p | dict(reference_gbp=q(price),liquidation_equity_gbp=q(equity),hypothetical_action=action))
        actions.append(dict(date=p['date'],action=action,units=q(units)))
        if finished:
            if stop:reason='loss_review_at_observed_reference_not_stop_fill'
            break
    else:
        return base | dict(status='unsettled_reference_path',reason='incomplete_fixed_window',
                           entry_date=chosen[0],path=path,actions=actions)
    last=price; net=units*last*(1-friction)-allocation
    gross=allocation*(last/start-1)
    return base | dict(status='simulated_reference_path',reason=reason,entry_date=path[0]['date'],
        exit_date=path[-1]['date'],allocation_gbp=str(allocation),initial_cash_gbp=str(cash),reserved_exit_fee_gbp=str(fee),
        net_pnl_gbp=q(net),gross_pnl_gbp=q(gross),total_friction_gbp=q(gross-net),
        net_allocation_return_percent=q(net/allocation*100),gross_return_percent=q(gross/allocation*100),
        final_cash_gbp=q(cash+net),max_observed_drawdown_percent=q(max_dd),path=path,actions=actions,
        net_outcome='positive' if net>0 else 'negative' if net<0 else 'flat',
        calendar='numeric_reporting_observations_not_verified_exchange_sessions',
        skipped_unavailable_dates=[d for d,p in rows[market].items()
                                   if path[0]['date']<=d<=path[-1]['date'] and p['status']!='numeric'],
        costs=PROTOCOL['costs'][cost],executable=False,point_in_time_safe=False)


def stats(outcomes):
    good=[r for r in outcomes if r['status']=='simulated_reference_path']
    vals=[D(r['net_pnl_gbp']) for r in good]
    return dict(attempts=len(outcomes),complete=len(good),missing_or_not_triggered=len(outcomes)-len(good),
        positive=sum(r['net_outcome']=='positive' for r in good),negative=sum(r['net_outcome']=='negative' for r in good),
        flat=sum(r['net_outcome']=='flat' for r in good),
        median_net_pnl_gbp=q(median(vals)) if vals else None,
        minimum_net_pnl_gbp=q(min(vals)) if vals else None,maximum_net_pnl_gbp=q(max(vals)) if vals else None,
        reasons=dict(sorted(Counter(r['reason'] for r in outcomes if r['status']!='simulated_reference_path').items())))


def portfolio(plans, data, cost='declared'):
    """One position, one episode, no reinvestment of future proceeds before exit."""
    cash=D(PROTOCOL['initial_cash_gbp']); peak=cash; drawdown=D(0)
    busy_until=None; episodes=set(); records=[]; equity=[]; unresolved=False
    for p in sorted(plans,key=lambda p:(p.get('decision_bound') or '9999',p['event_id'],p['market'])):
        if p['hypothetical_intent']!='Conditional hypothetical Buy':
            records.append(dict(event_id=p['event_id'],status='no_signal'));continue
        # Block at signal time, rather than inspecting the rejected event's future return.
        if unresolved or p.get('episode_id') in episodes or busy_until and p['decision_bound'][:10]<=busy_until:
            records.append(dict(event_id=p['event_id'],status='overlap_or_same_episode'));continue
        allocation=min(D(PROTOCOL['allocation_gbp']),cash*D(PROTOCOL['max_allocation_fraction']))
        r=measure(p,data,cost,allocation,cash)
        for point in r['path']:
            value=D(point['liquidation_equity_gbp']);peak=max(peak,value)
            drawdown=max(drawdown,(peak-value)/peak*100)
            equity.append(dict(date=point['date'],cash_if_liquidated_gbp=point['liquidation_equity_gbp']))
        if r['status']=='simulated_reference_path':
            cash+=D(r['net_pnl_gbp']);busy_until=r['exit_date'];episodes.add(p['episode_id'])
        if r['status']=='unsettled_reference_path':unresolved=True
        records.append(r)
    return dict(unresolved_position=unresolved,initial_cash_gbp=PROTOCOL['initial_cash_gbp'],final_cash_gbp=None if unresolved else q(cash),net_pnl_gbp=None if unresolved else q(cash-D(PROTOCOL['initial_cash_gbp'])),
                max_observed_drawdown_percent=q(drawdown),trades=sum(r.get('status')=='simulated_reference_path' for r in records),
                excluded_overlap=sum(r.get('status')=='overlap_or_same_episode' for r in records),records=records,equity=equity)


def diagnosis(data):
    counters=Counter();records=[]
    for event in data['events']:
        available=publication(event,data)
        if available is None:continue
        d=historical_decision(event,data,event['targets'][0],iso(available+timedelta(microseconds=1)))
        counters.update(d['reasons'])
        records.append(dict(event_id=event['id'],action=d['action'],blockers=d['reasons'],
                            selected_analogues=len(d['historical_matches']['selected']),qualified_cases=d['qualified_cases'],
                            expected_edge_assessed=False,
                            note='Execution/provenance gates precede any edge estimate; abstention is not a measured losing forecast.'))
    return dict(events=len(records),validated_buy=0,validated_no_action=len(records),blocker_counts=dict(sorted(counters.items())),records=records)


def build_report(data=None):
    require((HERE/'PROTOCOL.sha256').read_text().strip()==digest(PROTOCOL), 'Protocol changed; review before repinning')
    data=data or load_free_library()
    events=sorted(data['events'],key=lambda e:(publication(e,data),e['id']))
    # Freeze every rule before measuring ANY subsequent return.
    plans=[plan(e,data,m,r,h) for e in events for m in e['targets']
           for r in PROTOCOL['rules'] for h in PROTOCOL['horizons']]
    default=[];summaries=[];portfolios=[]
    for rule in PROTOCOL['rules']:
        for horizon in PROTOCOL['horizons']:
            selected=[p for p in plans if p['rule']==rule and p['horizon']==horizon]
            for cost in PROTOCOL['costs']:
                outcomes=[measure(p,data,cost) for p in selected]
                summaries.append(dict(rule=rule,horizon=horizon,cost=cost,**stats(outcomes)))
                if rule==PROTOCOL['default_rule'] and horizon==PROTOCOL['default_horizon'] and cost==PROTOCOL['default_cost']:
                    default=[dict(plan=p,outcome=o,buy_and_hold_same_window=measure(p,data,cost,risk_exit=False)) for p,o in zip(selected,outcomes)]
            port=portfolio(selected,data)
            portfolios.append(dict(rule=rule,horizon=horizon,**{k:v for k,v in port.items() if k!='records'}))
    # Broad passive baseline uses one continuous source window, not a sum of event wins.
    baselines=[]; rows=indexed(data)
    for market in ('brent','wti','eurusd'):
        days=sorted(d for d,p in rows.get(market,{}).items() if p['status']=='numeric')
        points=[gbp_point(rows,market,d)[0] for d in days]
        valid=bool(points) and all(p is not None for p in points)
        baselines.append(dict(market=market,status='unsupported_continuous_path' if not valid else 'reference_only',
            start=days[0] if days else None,end=days[-1] if days else None,
            reason='Every intermediate exact-date FX and positive reference is required; no repairing missing dates.',
            gross_return_percent=q((D(points[-1]['reference_gbp'])/D(points[0]['reference_gbp'])-1)*100) if valid else None))
    return dict(schema_version=1,kind=PROTOCOL['kind'],protocol=PROTOCOL,protocol_sha256=digest(PROTOCOL),
        universe_events=len(events),event_market_cases=len(default),diagnosis=diagnosis(data),
        rule_summaries=summaries,portfolios=portfolios,default_cases=default,
        no_trade=dict(initial_cash_gbp='50',final_cash_gbp='50',net_pnl_gbp='0',drawdown_percent='0'),
        passive_baselines=baselines,source_links=[dict(id=s['id'],url=s['url'],publisher=s['publisher']) for s in data['sources'].values()],
        supported_entries=0,orders=0,account_mutations=0,cost_GBP='0.00',
        limitations=['Retrospective hypothesis only. No executable product, point-in-time availability or predictive edge is established.',
                    'Oil spot and FX noon references are not exchange opening/closing fills. No roll, dividends, interest or tax is invented.',
                    'Reporting observations are not exchange sessions; blank/ND days are not automatically holidays.',
                    'Selected event corpus has selection/survivorship and regime bias; overlap controls do not prove independence.',
                    'All nine rules and four illustrative cost scenarios are retained. SIM-1 performs no fitting or winner selection.',
                    'No IPO allocation, unsupported share/gold quote, short sale, leverage or practice-account mutation.'])


def public_view(report):
    """Small static review projection; full window fingerprints stay in local traces."""
    projected={k:v for k,v in report.items() if k not in ('default_cases','portfolios')}
    projected['portfolios']=[{k:v for k,v in p.items() if k!='equity'} for p in report['portfolios']]
    cases=[]
    for c in report['default_cases']:
        p=c['plan']
        view={k:v for k,v in p.items() if k not in ('context','plan_sha256','protocol_sha256')}
        def outcome(o):
            result=dict(o)
            result['path']=[{k:v for k,v in point.items() if k not in ('snapshot_id','fx_snapshot_id')} for point in o['path']]
            return result
        baseline={k:v for k,v in c['buy_and_hold_same_window'].items() if k not in ('path','actions','skipped_unavailable_dates')}
        cases.append(dict(plan=view,outcome=outcome(c['outcome']),buy_and_hold_same_window=baseline))
    projected['default_cases']=cases
    projected['trace_scope']='Full calculation traces and per-window fingerprints are local work/ output. This public projection retains all cases, results, source identifiers, raw references, dated actions and aggregate statistics.'
    return projected
