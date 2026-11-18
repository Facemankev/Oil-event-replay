"""Private, provisional owner-file diagnostics. Never fitting or prospective results."""
import copy
from bisect import bisect_left, bisect_right
from collections import Counter
from decimal import Decimal as D
from datetime import date
from statistics import median

from event_history.engine import publication
from event_history.library import ROOT, require
from free_pilot.data import load_free_library
from simulations.engine import plan, measure, stats, q, PROTOCOL
from world_events.events import digest
from .stooq import ASSETS

HORIZONS=(1,5,20)


def scope(event,symbol):
    if symbol in event['targets']:return 'sourced_direct_target'
    if symbol=='SPY':return 'broad_market_ETF_benchmark_not_Nasdaq_index'
    if symbol=='GLD' and 'gold_futures_reported' in event['targets']:return 'gold_ETF_proxy_not_futures_or_spot'
    return 'descriptive_panel_no_sourced_company_exposure'


def fixed_window(series,spy,bound,horizon,calendar=None):
    """Use one fixed reporting-date union; an absent asset date cannot move the goalposts."""
    days=calendar or sorted(spy); before=bisect_left(days,bound)-1; after=bisect_right(days,bound)
    base=dict(status='missing_window',change_percent=None,spy_change_percent=None,
              excess_percentage_points=None,relative_wealth_percent=None,
              baseline_date=None,end_date=None,trading_calendar_verified=False)
    if before<0 or after+horizon>len(days):return base
    selected=[days[before],*days[after:after+horizon]]
    if ( date.fromisoformat(selected[1])-date.fromisoformat(bound)).days>7:
        return base|dict(status='entry_outside_delay_limit')
    if any((date.fromisoformat(b)-date.fromisoformat(a)).days>7 for a,b in zip(selected,selected[1:])):
        return base|dict(status='unverified_calendar_gap')
    for day in selected:
        if day not in series or day not in spy or series[day]['status']!='numeric' or spy[day]['status']!='numeric':
            return base|dict(status='missing_exact_session_price',missing_date=day)
    first,last=selected[0],selected[-1]
    gain=D(series[last]['close'])/D(series[first]['close'])-1
    benchmark=D(spy[last]['close'])/D(spy[first]['close'])-1
    return base|dict(status='provisional_supplied_reporting_sessions',
        baseline_date=first,end_date=last,change_percent=q(gain*100),
        spy_change_percent=q(benchmark*100),excess_percentage_points=q((gain-benchmark)*100),
        relative_wealth_percent=q(((1+gain)/(1+benchmark)-1)*100),
        basis='as_supplied_Close_adjustments_unknown_not_verified_total_return')


def costed(planned,data,series,spy,cost,calendar=None):
    # Existing SIM entry is next date after conservative publication eligibility.
    # Validate its whole fixed reporting window BEFORE calling SIM, which otherwise
    # counts numeric source observations. No skip/forward-fill for a missing day.
    days=calendar or sorted(spy);i=bisect_right(days,planned['decision_bound'][:10]);h=planned['horizon']
    chosen=days[i:i+h+1]
    if len(chosen)<h+1:return dict(status='not_entered',reason='incomplete_SPY_window',net_pnl_gbp=None)
    for d in chosen:
        if d not in spy or spy[d]['status']!='numeric':
            return dict(status='not_entered',reason='missing_exact_benchmark_session',net_pnl_gbp=None,missing_date=d)
        if d not in series or series[d]['status']!='numeric':
            return dict(status='not_entered',reason='missing_exact_SPY_session_price',net_pnl_gbp=None,missing_date=d)
    outcome=measure(planned,data,cost,risk_exit=False)
    # SIM may never silently choose different dates for this fixed-window study.
    if outcome['status']=='simulated_reference_path':
        require(outcome['entry_date']==chosen[0] and outcome['exit_date']==chosen[-1], 'Session alignment drift')
    return {k:v for k,v in outcome.items() if k not in ('path','actions')}


def build_study(selections,inspection,data=None):
    data=data or load_free_library()
    require(set(selections)==set(ASSETS),'All six files required; no missing benchmark substitution')
    require(all(not s['capture']['synthetic_control'] for s in selections.values()),'Synthetic controls cannot be published as actual diagnostics')
    # Keep identities in a separate hypothesis panel, never edit parent targets.
    original=digest(data);rows={m:{r['date']:r for r in s['rows']} for m,s in selections.items()}
    spy=rows['SPY'];cases=[];cost_summaries=[]
    calendar=sorted({d for r in rows.values() for d in r if min(spy)<=d<=max(spy)})
    fx=[p for p in data['observations'] if p['instrument']=='gbpusd']
    for symbol in ASSETS:
        c=selections[symbol]['capture'];working=copy.deepcopy(data)
        working['observations']=fx+[dict(instrument=symbol,date=r['date'],value=r['close'],
            status='numeric' if r['status']=='numeric' else 'ND',source_id='owner-stooq-'+symbol,
            snapshot_id=c['payload_sha256'],original_available_at=None,original_vintage_verified=False)
            for r in selections[symbol]['rows']]
        working['instruments'][symbol]=dict(id=symbol,group='private_reference',name=symbol,
            executable_quote=False,paper_execution_enabled=False)
        for event in data['events']:
            available=publication(event,data)
            for h in HORIZONS:
                record=dict(event_id=event['id'],episode_id=event['episode_id'],instrument=symbol,
                    sourced_targets=event['targets'],scope=scope(event,symbol),horizon=h,
                    supporting_publication_at=event.get('public_at'),supporting_publication_day=event.get('public_day'),
                    occurrence_day=event.get('occurred_day'),actual_historical_receipt_at=None,
                    validated_action='No Action',new_independent_event=False)
                if available is None:
                    cases.append(record|dict(reaction=dict(status='publication_unknown'),costs={}));continue
                boundary=available.date().isoformat()
                reaction=fixed_window(rows[symbol],spy,boundary,h,calendar)
                publication_day=event.get('public_day')
                day_reaction=fixed_window(rows[symbol],spy,publication_day,h,calendar) if publication_day else dict(status='publication_day_unknown')
                # A hypothetical exposure is explicitly not a claim that the
                # historical source identified this particular company/ETF.
                hypothetical={**event,'targets':[symbol]}
                planned=plan(hypothetical,working,symbol,'event_long',h)
                outcomes={cost:costed(planned,working,rows[symbol],spy,cost,calendar) for cost in PROTOCOL['costs']}
                cases.append(record|dict(eligibility_bound=planned['decision_bound'],
                    hypothetical_exposure_override=symbol not in event['targets'],reaction=reaction,
                    supporting_publication_day_reaction=day_reaction,
                    reaction_timing_note='Eligibility-window and publication-day windows are separate. Day-only timing cannot isolate an intraday first reaction.',costs=outcomes))
        for h in HORIZONS:
            for category in sorted({r['scope'] for r in cases if r['instrument']==symbol}):
                selected=[r for r in cases if r['instrument']==symbol and r['horizon']==h and r['scope']==category]
                for cost in PROTOCOL['costs']:
                    outcomes=[r.get('costs',{}).get(cost,dict(status='not_entered',reason='publication_unknown')) for r in selected]
                    cost_summaries.append(dict(instrument=symbol,horizon=h,scope=category,cost=cost,**stats(outcomes)))
    require(digest(data)==original,'Parent research mutated')
    direct=[r for r in cases if r['scope']=='sourced_direct_target']
    covered=[r for r in direct if r['reaction']['status']=='provisional_supplied_reporting_sessions']
    # Structural/data coverage can improve without making any trade eligible.
    return dict(schema_version=1,kind='PRIVATE_PROVISIONAL_retrospective_owner_file_review',
        rows_imported=0,inspection=inspection,study_horizons=list(HORIZONS),
        protocol=dict(selection='All six securities across all retained events; exposure scopes remain separate. No selecting winners or adding invented events.',
          reaction='Last supplied reporting date before eligibility day to 1/5/20th union reporting date strictly after it. Day-only publication uses retained conservative two-day bound.',
          costed='SIM-1 fixed post-eligibility close-to-close exposures for 1/5/20 subsequent union reporting dates; risk_exit=False. All four original illustrative cost assumptions.',
          benchmark='Same exact start/end dates. Percentage-point excess and compounded relative wealth are separate. SPY is an ETF, not Nasdaq Composite.',
          calendar='Union of supplied dates within SPY coverage; missing benchmark observations block windows. Shared gaps and independent exchange schedule remain unverified.',
          price_basis='As-supplied Close. Do not label unadjusted, split-adjusted, dividend-adjusted or total return without evidence.'),
        exploratory_protocol_registered_before_outcome_inspection=False,
        event_count=len(data['events']),panel_pairs=len(data['events'])*len(ASSETS),
        newly_covered_direct_event_pairs=len({(r['event_id'],r['instrument']) for r in covered}),
        newly_covered_direct_horizon_windows=len(covered),
        new_eligible_historical_examples=0,new_independent_events=0,new_supported_buys=0,
        eligibility_blockers=['Private quarantine only; no open/public/application/training licence.',
          'Provider identity/download clock and adjustment basis unverified.',
          'No independent exchange-session calendar; no original availability/executable product evidence.',
          'Existing inspected events and repeated horizons/peers are not new independent validation.'],
        learning_holdout=dict(changed=False,trained_or_tuned=False,original_report_sha256=(ROOT/'learning/REPORT.sha256').read_text().strip(),
          genuinely_new_predictions=0,prospective_outcomes=0),
        parent_simulation=dict(changed=False,report_sha256=(ROOT/'simulations/REPORT.sha256').read_text().strip(),
          note='Original benchmark/report unchanged; new provisional diagnostics stay separate.'),
        cost_summaries=cost_summaries,cases=cases,
        limitations=['Reference ratios and illustrative fees are not executable fills or predictions.',
          'Same-event information may have been anticipated; reaction does not establish causation.',
          'No new AMD/MRNA/BMY historical event facts are invented from share-price files.',
          'GLD carries ETF expenses/tracking/currency risks and is not physical gold or a futures contract.',
          'Do not publish raw files, database, source-row traces or this private detailed report to GitHub.'])
