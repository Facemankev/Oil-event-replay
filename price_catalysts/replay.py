"""Fixed post-detection replay, prior-context controls and explicit missing results."""
from bisect import bisect_right
from collections import Counter
from datetime import date,timedelta
from decimal import Decimal as D
from statistics import median
from daily_prices.stooq_study import fixed_window,costed
from free_pilot.data import load_free_library
from simulations.engine import PROTOCOL as COSTS,stats,q
from world_events.events import digest
from .detector import PROTOCOL,sessions,text_number

HORIZONS=tuple(PROTOCOL['replay']['horizons'])


def epochs(features,calendar):
    """Keep the FIRST observable trigger. A later peak cannot choose the entry."""
    index={d:i for i,d in enumerate(calendar)};result=[]
    for symbol,rows in features.items():
        last=None
        for r in rows:
            if not r['trigger']:continue
            if last is not None and index[r['date']]-last<=PROTOCOL['episodes']['cooldown_sessions']:continue
            result.append(r);last=index[r['date']]
    return sorted(result,key=lambda r:(r['date'],r['instrument']))


def rule_for(record):
    z=record['return_z']
    if z is None or abs(D(z))<D(PROTOCOL['features']['anomaly_z']):return None
    return PROTOCOL['replay']['rules'][0 if D(z)>0 else 1]


def prior_control(record,features,calendar):
    """Select only by prior features, with a full 21-session separation; no outcome reads."""
    index={d:i for i,d in enumerate(calendar)};i=index[record['date']]
    if record.get('prior_volatility') is None or record.get('prior_trend') is None:return None
    pool=[]
    for r in features:
        lag=i-index[r['date']]
        if not 22<=lag<=126 or r['trigger'] or r.get('prior_volatility') is None or r.get('prior_trend') is None:continue
        if D(r['prior_volatility'])<=0 or D(record['prior_volatility'])<=0:continue
        # Relative volatility distance plus absolute past trend distance. Neither
        # today's anomaly return nor any subsequent return enters this match.
        score=abs(D(r['prior_volatility'])/D(record['prior_volatility'])-1)+abs(D(r['prior_trend'])-D(record['prior_trend']))
        pool.append((score,digest({'id':r['id']}),r))
    return min(pool,key=lambda x:(x[0],x[1]))[2] if pool else None


def period(day,calendar,horizon=20):
    after=bisect_right(calendar,day);end=after+1+horizon
    if day<=PROTOCOL['replay']['reference_period_through']:
        if end>len(calendar) or calendar[end-1]>PROTOCOL['replay']['reference_period_through']:return 'embargo'
        return 'reference_exploratory'
    first=bisect_right(calendar,PROTOCOL['replay']['reference_period_through'])
    return 'later_exploratory_already_examined' if bisect_right(calendar,day)-first>PROTOCOL['replay']['embargo_sessions'] else 'embargo'


def reaction(series,spy,day,h,calendar):
    # Reuse parent's exact-session arithmetic. The self-reference only obtains
    # the asset return when SPY is absent; never present its zero excess as SPY.
    own=fixed_window(series,series,day,h,calendar);bench=fixed_window(series,spy,day,h,calendar)
    return dict(status=own['status'],change_percent=own['change_percent'],baseline_date=own['baseline_date'],end_date=own['end_date'],
        SPY_status=bench['status'],SPY_change_percent=bench['spy_change_percent'],SPY_excess_percentage_points=bench['excess_percentage_points'],
        relative_wealth_percent=bench['relative_wealth_percent'],calendar_verified=own['trading_calendar_verified'],
        missing_date=own.get('missing_date'),benchmark_missing_date=bench.get('missing_date'))


class Evaluator:
    def __init__(self,selections,data=None):
        self.selections=selections;self.calendar=sessions(selections)
        self.rows={m:{r['date']:r for r in s['rows']} for m,s in selections.items()}
        self.data=data or load_free_library()
        self.fx={r['date']:r for r in self.data['observations'] if r['instrument']=='gbpusd'}
        self.cache={}

    def window(self,symbol,day,h,blocked=False):
        key=symbol,day,h,blocked
        if key in self.cache:return self.cache[key]
        series=self.rows[symbol];spy=self.rows['SPY'];i=bisect_right(self.calendar,day)
        selected=self.calendar[i:i+h+1]
        observations=[self.fx[d] for d in selected if d in self.fx]
        observations += [dict(instrument=symbol,date=d,value=series[d]['close'],status=series[d]['status'],
            source_id='owner-stooq-'+symbol,snapshot_id=self.selections[symbol]['capture']['payload_sha256']) for d in selected if d in series]
        data=dict(observations=observations)
        planned=dict(event_id=symbol+'-'+day,market=symbol,rule='fixed_post_detection_hypothesis',horizon=h,
            hypothetical_intent='No Action' if blocked else 'Conditional hypothetical Buy',
            decision_bound=day+'T23:59:59Z',status='source_action_or_bad_print_unresolved' if blocked else 'exploratory_after_bar_assumption')
        costs={c:costed(planned,data,series,spy,c,self.calendar) for c in COSTS['costs']}
        # Identical funding/costs/window for SPY; raw excess return is not a
        # substitute for a currency-converted, costed benchmark.
        spy_observations=[p for p in observations if p['instrument']=='gbpusd']
        spy_observations += [dict(instrument='SPY',date=d,value=spy[d]['close'],status=spy[d]['status'],source_id='owner-stooq-SPY',snapshot_id=self.selections['SPY']['capture']['payload_sha256']) for d in selected if d in spy]
        spy_costs={c:costed(dict(planned,market='SPY'),dict(observations=spy_observations),spy,spy,c,self.calendar) for c in COSTS['costs']}
        result=dict(horizon=h,reaction=reaction(series,spy,day,h,self.calendar),
            entry_assumption='Complete detection bar D, hypothetical entry at next reporting close, exit H intervals after entry. Unknown actual historical receipt.',
            costs=costs,SPY_costs=spy_costs,
            no_trade_net_pnl_gbp='0',validated_action='No Action',actual_historical_receipt_at=None)
        self.cache[key]=result;return result

    def record(self,record):
        blocked=any(x in record.get('data_flags',[]) for x in ('possible_corporate_action_or_bad_print_needs_review','quote_on_reviewed_exchange_closure','missing_numeric_close'))
        return [self.window(record['instrument'],record['date'],h,blocked) for h in HORIZONS]


def summary(cases):
    result=[]
    for p in ('reference_exploratory','later_exploratory_already_examined','embargo'):
        for rule in PROTOCOL['replay']['rules']:
            pool=[r for r in cases if r['period']==p and r['rule']==rule]
            for h in HORIZONS:
                for cost in COSTS['costs']:
                    for lane in ('signal','context_control'):
                        outcomes=[];bench=[]
                        for r in pool:
                            w=next((w for w in r[lane] if w['horizon']==h),None)
                            outcomes.append(w['costs'][cost] if w else dict(status='not_entered',reason='no_past_context_control',net_pnl_gbp=None))
                            bench.append(w['SPY_costs'][cost] if w else dict(status='not_entered',reason='no_past_context_control',net_pnl_gbp=None))
                        paired=[D(a['net_pnl_gbp'])-D(b['net_pnl_gbp']) for a,b in zip(outcomes,bench) if a['status']==b['status']=='simulated_reference_path']
                        result.append(dict(period=p,rule=rule,horizon=h,cost=cost,lane=lane,**stats(outcomes),SPY_complete_pairs=len(paired),
                            median_net_excess_vs_SPY_gbp=q(median(paired)) if paired else None))
    return result


def paired_controls(cases):
    results=[]
    for p in ('reference_exploratory','later_exploratory_already_examined','embargo'):
        for rule in PROTOCOL['replay']['rules']:
            pool=[r for r in cases if r['period']==p and r['rule']==rule]
            for h in HORIZONS:
                for cost in COSTS['costs']:
                    differences=[]
                    for r in pool:
                        a=next(w for w in r['signal'] if w['horizon']==h)['costs'][cost]
                        b=next((w for w in r['context_control'] if w['horizon']==h),None)
                        if b is not None and a['status']==b['costs'][cost]['status']=='simulated_reference_path':
                            differences.append(D(a['net_pnl_gbp'])-D(b['costs'][cost]['net_pnl_gbp']))
                    results.append(dict(period=p,rule=rule,horizon=h,cost=cost,attempts=len(pool),complete_pairs=len(differences),
                        missing_pairs=len(pool)-len(differences),signal_better=sum(x>0 for x in differences),signal_worse=sum(x<0 for x in differences),
                        equal=sum(x==0 for x in differences),median_paired_net_difference_gbp=q(median(differences)) if differences else None))
    return results


def replay(scan,evaluator):
    all_epochs=epochs(scan['features'],evaluator.calendar);cases=[]
    for r in all_epochs:
        rule=rule_for(r)
        if rule is None:continue
        control=prior_control(r,scan['features'][r['instrument']],evaluator.calendar)
        cases.append(dict(id=r['id'],instrument=r['instrument'],date=r['date'],rule=rule,period=period(r['date'],evaluator.calendar),
            context_control_id=control['id'] if control else None,signal=evaluator.record(r),context_control=evaluator.record(control) if control else []))
    ids=[r['context_control_id'] for r in cases if r['context_control_id']]
    return dict(kind='fixed_rules_exploratory_not_validated_prediction',trigger_bars=sum(r['trigger'] for rows in scan['features'].values() for r in rows),
        first_trigger_episodes=len(all_epochs),daily_anomaly_rule_cases=len(cases),cases=cases,summaries=summary(cases),
        paired_context_comparisons=paired_controls(cases),
        instrument_summaries={s:summary([r for r in cases if r['instrument']==s]) for s in scan['features']},
        reused_context_controls=len(ids)-len(set(ids)),actual_prospective_predictions=0,qualified_buys=0,
        limitations=['Complete bar needed; no return from the already realised move is booked as a trade.',
          'All historical slices were exposed to discovery. Later results are exploratory, not an untouched test.',
          'Source availability, adjustments, corporate actions and surviving-asset selection remain unresolved.',
          'Episodes in different assets share macro conditions; reused/overlapping control windows are not independent trials.',
          'Pre-2023 calendar is supplied-date union, so shared gaps can remain undetected.',
          'No model fitting, probabilities, threshold/rule/horizon tuning or winner promotion. Fees are sensitivities, not broker quotes.'])
