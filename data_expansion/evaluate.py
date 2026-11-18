"""Fixed-population before/after SIM/LEARN audit; no refitting to new outcomes."""
from collections import Counter
from decimal import Decimal
from statistics import mean
from free_pilot.data import load_free_library,coverage
from simulations.engine import build_report as simulate
from learning.engine import build_report as learn
from world_events.events import digest
from event_history.library import require
from .library import load_bundle,expanded_library


def ipo_reaction(case):
    if case['reported_first_close'] is None:
        return dict(status='no_completed_listing' if case['status'] in ('withdrawal_requested','suspended_before_listing') else 'missing_reaction',offer_to_first_close_percent=None,direction=None)
    change=(Decimal(case['reported_first_close'])/Decimal(case['offer_price'])-1)*100
    return dict(status='reported_reference_only_not_a_trade',offer_to_first_close_percent=str(change.quantize(Decimal('0.0001'))),
                direction='positive' if change>0 else 'negative' if change<0 else 'flat')


def snapshot(data,sim,learning):
    default=next(r for r in sim['rule_summaries'] if r['rule']=='event_long' and r['horizon']==5 and r['cost']=='declared')
    return dict(events=sim['universe_events'],event_market_pairs=sim['event_market_cases'],
       numeric_daily_references=coverage(data)['numeric_observations'],
       simulation_default=default,simulation_blockers=sim['diagnosis']['blocker_counts'],
       learning=learning['summary'],fold_sizes={k:len(learning['locked'][k+'_event_ids']) for k in ('training','validation')},
       heldout_event_ids=[r['prediction']['event_id'] for r in learning['records']],
       watch_outcomes=[dict(event_id=r['prediction']['event_id'],status=r['outcome']['status'],net_pnl_gbp=r['outcome']['net_pnl_gbp'])
         for r in learning['records'] if r['prediction']['research_action']=='Watch'])


def oil_crosscheck(bundle,data):
    """Context only: different publishers' rounded averages are NOT daily corrections."""
    out=[];seen=set()
    for r in bundle['averages']:
        if r['frequency']!='monthly' or r['instrument']=='wb-gold-average':continue
        key=(r['instrument'],r['period'])
        if key in seen:continue
        seen.add(key);market='brent' if 'brent' in r['instrument'] else 'wti'
        rows=[p for p in data['observations'] if p['instrument']==market and p['date'].startswith(r['period'])]
        prices=[Decimal(p['value']) for p in rows if p['status']=='numeric']
        average=mean(prices) if prices else None
        out.append(dict(instrument=market,period=r['period'],world_bank_published_average=r['value'],
          EIA_numeric_observations=len(prices),EIA_explicit_unavailable=sum(p['status']!='numeric' for p in rows),
          retained_EIA_arithmetic_average=None if average is None else str(average.quantize(Decimal('0.0001'))),
          difference_USD_per_barrel=None if average is None else str((Decimal(r['value'])-average).quantize(Decimal('0.0001'))),
          status='different_aggregation_context_not_reconciliation_or_correction'))
    return sorted(out,key=lambda r:(r['instrument'],r['period']))


def build_report(bundle=None):
    bundle=bundle or load_bundle()
    bundle=dict(bundle,averages=sorted(bundle['averages'],key=lambda r:(r['instrument'],r['period'],r['source_id'])),
                ipos=sorted(bundle['ipos'],key=lambda r:(r['event_day'],r['id'])))
    before=load_free_library();after=expanded_library(before,bundle)
    require(before['events']==after['events'] and before['observations']==after['observations'],'Typed reference import must preserve original evaluation population and daily quotes')
    s0=simulate(before);l0=learn(before)
    # Actually execute both engines again with the imported typed context attached.
    # No manual copied counts, extra IPOs, shifted boundary, or replacement test set.
    s1=simulate(after);l1=learn(after)
    b=snapshot(before,s0,l0);a=snapshot(after,s1,l1)
    require(b['heldout_event_ids']==a['heldout_event_ids'],'Consumed holdout membership changed')
    require(s0['protocol']==s1['protocol'] and l0['protocol']==l1['protocol'],'Frozen evaluation rules changed')
    reactions=[dict(id=c['id'],episode_id=c['episode_id'],event_day=c['event_day'],document_day=c['document_day'],
      first_session=c['first_session'],unit=c['unit'],offer_price=c['offer_price'],reported_first_close=c['reported_first_close'],
      evaluation_membership=c['evaluation_membership'],**ipo_reaction(c),
      historical_research_partition='pre_2016' if c['event_day']<'2016-01-01' else '2016_2019' if c['event_day']<'2020-01-01' else '2020_onward',
      original_vintage_verified=False,sources=[c['event_source']['url']]+([c['reaction_source']['url']] if c['reaction_source'] else [])) for c in bundle['ipos']]
    periods={(r['instrument'],r['frequency'],r['period']) for r in bundle['averages']}
    revisions={}
    for r in bundle['averages']:revisions.setdefault((r['instrument'],r['frequency'],r['period']),set()).add(Decimal(r['value']))
    return dict(schema_version=1,kind='data_2_reference_expansion_fixed_population_audit',checked_on='2026-11-18',
      imported=dict(publication_values=len(bundle['averages']),distinct_asset_periods=len(periods),
        by_instrument={m:dict(publication_values=sum(r['instrument']==m for r in bundle['averages']),distinct_periods=sum(p[0]==m for p in periods),
          monthly_periods=sum(p[0]==m and p[1]=='monthly' for p in periods)) for m in sorted({r['instrument'] for r in bundle['averages']})},
        ipo_episodes=len(bundle['ipos']),ipo_outcome_counts=dict(sorted(Counter(r['direction'] or r['status'] for r in reactions).items())),
        new_daily_security_quotes=0,new_verified_original_vintages=0,conflicting_published_periods=sum(len(v)>1 for v in revisions.values())),
      before=b,after=a,comparison=dict(exact_simulation_results_unchanged=digest(s0)==digest(s1),
        exact_learning_results_unchanged=digest(l0)==digest(l1),heldout_membership_unchanged=b['heldout_event_ids']==a['heldout_event_ids'],
        new_settled_simulation_cases=a['simulation_default']['complete']-b['simulation_default']['complete'],
        new_settled_learning_signals=a['learning']['settled_diagnostic_hypotheses']-b['learning']['settled_diagnostic_hypotheses'],
        new_supported_entries=0,predictive_improvement_demonstrated=False,
        reason='Published period averages and IPO facts add reference context; they cannot replace absent daily adjusted histories, original timestamps or executable quotes. Unchanged performance is a negative result, not evidence of a successful predictor.'),
      ipo_research_reserve=reactions,oil_average_crosscheck=oil_crosscheck(bundle,before),
      safeguards=dict(frozen_old_population=True,new_ipo_cases_used_for_fitting=0,new_ipo_cases_used_for_evaluation=0,account_mutations=0,orders=0,cost_GBP='0.00'),
      limitations=['Primary World Bank numerical tables, CC-BY 4.0 with attribution; visible transcription, not original PDF/XLS HTTP bytes.',
        'Publication editions overlap; annual, quarter and monthly cells are not independent daily samples. No forward-filling or daily session reconstruction.',
        'Original availability/version unverified even for a printed historical edition. As-of document filtering alone cannot prove a point-in-time backtest.',
        'IPO cases are manually curated contrasts, not an unbiased cohort. First-day reported closes/offer prices do not establish retail allocations, ongoing returns, corporate actions or survivorship coverage.',
        'Complete daily adjusted Nvidia/AMD/biotech/index/gold histories remain unconnected under verified public-use terms; no paid/free-tier account assumed.',
        'Prior heldout outcomes are already examined; rerun is a regression audit, not an independent prospective validation. No predictive performance improvement or calibrated accuracy established.'])
