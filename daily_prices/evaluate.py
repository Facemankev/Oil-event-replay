"""Original regression, expanded retrospective diagnostics, and new evaluation are distinct."""
import copy,json
from collections import Counter
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
from event_history.library import require,ROOT
from event_history.engine import publication
from free_pilot.data import load_free_library,coverage
from simulations.engine import build_report as simulate
from learning.engine import build_report as learn
from world_events.events import digest
from .database import select_captures

HERE=Path(__file__).resolve().parent
PROTOCOL=json.loads((HERE/'protocol.json').read_text())
require((HERE/'PROTOCOL.sha256').read_text().strip()==digest(PROTOCOL),'Evaluation protocol changed without a reviewed version')


def enrich(data,selections):
    """Only exact USD identities with provider adjustments reach exploratory models.

    Raw quotes/ETF proxies/non-USD data remain queryable and auditable; they cannot
    be mislabeled as another asset or converted with an invented FX observation.
    """
    out=copy.deepcopy(data);admitted=[];blocked=[]
    for market,series in selections.items():
        c=series['capture'];rows=series['rows']
        reasons=[]
        if c['synthetic_control']:reasons.append('synthetic_control_not_market_history')
        if market not in out['instruments']:reasons.append('no_exact_existing_instrument_identity')
        if c['currency']!='USD' or c['unit']!='per_share':reasons.append('missing_supported_exact_currency_or_unit_conversion')
        if c['asset_kind']!='equity':reasons.append('proxy_or_index_must_not_replace_a_target_stock')
        if any(r['status']=='numeric' and r['adjusted_close'] is None for r in rows):reasons.append('provider_adjusted_series_or_actions_unavailable')
        # A later import cannot silently replace any retained source quote.
        if any(p['instrument']==market for p in out['observations']):reasons.append('existing_series_requires_explicit_difference_review')
        if reasons:
            blocked.append(dict(instrument=market,reasons=reasons));continue
        sid='data3-'+market;out['sources'][sid]=dict(id=sid,url=c['url'],publisher=c['publisher'],published_day=None,published_at=None,
          checked_on=c['retrieved_at'][:10],kind='current_daily_provider_reference',original_version_verified=False)
        for r in rows:
            out['observations'].append(dict(instrument=market,date=r['date'],value=r['adjusted_close'] if r['status']=='numeric' else None,
              status='numeric' if r['status']=='numeric' else 'ND',source_id=sid,snapshot_id=digest(c),
              original_available_at=None,original_vintage_verified=False,price_basis='provider_adjusted_current_vintage_reference_not_a_fill'))
        admitted.append(market)
    return out,dict(added_instruments=admitted,blocked=blocked,
      note='Provider-adjusted references support retrospective ratios only; reference units are not historical executable share allocations. No raw/adjusted/provider splicing or inferred corporate adjustments.')


def summary(data,sim,l):
    default=next(s for s in sim['rule_summaries'] if (s['rule'],s['horizon'],s['cost'])==('event_long',5,'declared'))
    return dict(events=sim['universe_events'],event_market_pairs=sim['event_market_cases'],
      numeric_daily_observations=sum(p['status']=='numeric' for p in data['observations']),
      default_simulation=default,learning=l['summary'],test_event_ids=[r['prediction']['event_id'] for r in l['records']],
      training_event_ids=l['locked']['training_event_ids'],validation_event_ids=l['locked']['validation_event_ids'],
      blocked_decisions=sim['diagnosis']['blocker_counts'],
      independent_training_cohorts=l['locked']['multiple_testing']['training_cohorts'])


def daily_paths(events,selections):
    """Coverage/reactions, no offer allocations, inferred sessions or causal claims."""
    results=[]
    for e in events:
        for market in e['targets']:
            s=selections.get(market);bound=e.get('eligibility_day') or (e.get('public_at') or '')[:10] or e.get('public_day')
            if not s:
                results.append(dict(event_id=e['id'],episode_id=e['episode_id'],instrument=market,status='missing_exact_daily_series',horizons={}));continue
            c=s['capture'];points=s['rows'];eligible=[r for r in points if bound and r['date']>bound]
            horizons={}
            for h in (1,3,5,10,20):
                chosen=eligible[:h+1]
                if len(chosen)<h+1:status='incomplete_window'
                elif any(r['status']!='numeric' for r in chosen):status='explicit_unavailable_observation_not_a_holiday'
                elif (date.fromisoformat(chosen[0]['date'])-date.fromisoformat(bound)).days>7:status='entry_outside_predefined_delay_limit'
                elif any((date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days>7 for a,b in zip(chosen,chosen[1:])):status='unverified_calendar_gap'
                else:status='observed_daily_reference_window_not_verified_sessions'
                adjusted=all(r.get('adjusted_close') is not None for r in chosen)
                basis='provider_adjusted_close' if adjusted else 'unadjusted_close_not_total_return'
                change=(Decimal(chosen[-1]['adjusted_close' if adjusted else 'close'])/Decimal(chosen[0]['adjusted_close' if adjusted else 'close'])-1)*100 if status.startswith('observed_') else None
                horizons[str(h)]=dict(status=status,change_percent=None if change is None else str(change.quantize(Decimal('0.0001'))),basis=basis,
                  entry_date=chosen[0]['date'] if chosen else None,exit_date=chosen[-1]['date'] if status.startswith('observed_') else None,
                  trading_session_calendar_verified=False,currency=c['currency'],causal_effect_established=False)
            results.append(dict(event_id=e['id'],episode_id=e['episode_id'],instrument=market,status='daily_reference_present',horizons=horizons))
    return results


def ipo_coverage(selections):
    cases=json.loads((ROOT/'data_expansion/sources/ipo-facts.json').read_text())['cases'];results=[]
    for c in cases:
        row=dict(event_id=c['id'],episode_id=c['episode_id'],symbol=c['symbol'],source_status=c['status'],
          status='missing_daily_price_series',horizons={})
        if c['status'] in ('withdrawal_requested','suspended_before_listing'):
            row['status']='uncompleted_listing_no_invented_fill'
        elif c['document_day'] is None:
            row['status']='original_publication_day_unknown'
        elif c['symbol'] in selections and (selections[c['symbol']]['capture']['symbol']!=c['symbol'] or selections[c['symbol']]['capture']['currency']!=c['unit'].split('/')[0] or selections[c['symbol']]['capture']['venue'].casefold()!=c['exchange'].casefold()):
            row['status']='wrong_currency_venue_or_security_identity'
        elif c['symbol'] in selections:
            # Same conservative day-only bound as the retained engine. Do not buy
            # at the offer price or claim a historical allocation/opening fill.
            from event_history.engine import eligible
            bound=eligible(dict(published_day=c['document_day'])).date().isoformat()
            event=dict(id=c['id'],episode_id=c['episode_id'],targets=[c['symbol']],eligibility_day=bound)
            computed=daily_paths([event],selections)[0]
            row.update(status=computed['status'],horizons=computed['horizons'])
        results.append(row)
    complete=sum(r['horizons'].get('5',{}).get('status')=='observed_daily_reference_window_not_verified_sessions' for r in results)
    return dict(events=len(cases),five_observation_reference_windows=complete,used_for_new_validation=False,records=results,
       note='DATA-2 contrast cases were already inspected. These are exploratory close-reference windows after a conservative publication bound, not offer allocations, total-return guarantees or new holdout results.')


def build_report(selections=None,new_evaluation=None):
    selections=selections or {}
    require(all(s['capture'].get('usage_scope')!='private_research' for s in selections.values()),'Private source data cannot enter a public report')
    require(all(not s['capture']['synthetic_control'] for s in selections.values()),'Synthetic controls cannot enter a published historical evaluation')
    before=load_free_library();after,admission=enrich(before,selections)
    s0=simulate(before);l0=learn(before)
    require(digest(s0)==(ROOT/'simulations/REPORT.sha256').read_text().strip(),'Original SIM report changed')
    require(digest(l0)==(ROOT/'learning/REPORT.sha256').read_text().strip(),'Original LEARN report changed')
    s1=simulate(after);l1=learn(after)
    b=summary(before,s0,l0);a=summary(after,s1,l1)
    require(b['test_event_ids']==a['test_event_ids'],'Examined test membership changed')
    require(b['training_event_ids']==a['training_event_ids'] and b['validation_event_ids']==a['validation_event_ids'],'Historical event population changed')
    require(l1['locked']['test_outcomes_used']==0,'Future outcomes entered model fitting')
    old_markets={p['instrument'] for p in before['observations']}
    requested=[dict(e,targets=[m for m in e['targets'] if m not in old_markets],eligibility_day=publication(e,after).date().isoformat()) for e in after['events']]
    paths=daily_paths(requested,selections)
    return dict(schema_version=1,kind='daily_price_acquisition_and_separate_evaluation_lanes',protocol=PROTOCOL,
      source_acquisition_status='partial_admitted_daily_data' if selections else 'blocked_no_admitted_daily_data',
      original_examined_evaluation=dict(preserved=True,before=b),
      expanded_retrospective_diagnostics=dict(after=a,admission=admission,
        label='EXPLORATORY: same previously examined historical cases; not new validation',
        new_numeric_observations=a['numeric_daily_observations']-b['numeric_daily_observations'],
        new_settled_paths=a['default_simulation']['complete']-b['default_simulation']['complete'],
        distinct_curated_episode_ids=len({e['episode_id'] for e in after['events']}),
        target_pairs_with_daily_series=sum(p['status']=='daily_reference_present' for p in paths),
        new_qualified_cohorts=a['learning']['qualified_candidate_cohorts']-b['learning']['qualified_candidate_cohorts'],
        supported_entries=0,predictive_improvement_demonstrated=False,
        explanation='More historical coverage or changed retrospective P&L cannot establish new predictive performance. No rule or threshold may be selected on examined test returns.'),
      costs_and_baselines=dict(rule_cost_summaries_evaluated=len(s1['rule_summaries']),
        all_scenarios_unchanged=s0['rule_summaries']==s1['rule_summaries'],
        changed_summaries=[dict(before=x,after=y) for x,y in zip(s0['rule_summaries'],s1['rule_summaries']) if x!=y],
        passive_original=s0['passive_baselines'],passive_expanded=s1['passive_baselines'],
        no_trade_original=s0['no_trade'],no_trade_expanded=s1['no_trade'],
        original_complete_results='simulations/report.json; frozen parent remains unchanged'),
      genuinely_new_evaluation=new_evaluation or dict(kind='prospective_reserved_not_yet_observed',from_timestamp=PROTOCOL['prospective_from'],
        events=0,matured_outcomes=0,calibrated_accuracy=None,predictive_edge_established=False,
        note='Only append-only pre-outcome locks after registration can qualify. Re-importing history never creates a new evaluation.'),
      previously_inspected_ipo_reserve=ipo_coverage(selections),
      raw_daily_captures=dict(instruments=len(selections),rows=sum(len(s['rows']) for s in selections.values()),
        real_numeric=sum(r['status']=='numeric' for s in selections.values() if not s['capture']['synthetic_control'] for r in s['rows']),
        explicit_unavailable=sum(r['status']!='numeric' for s in selections.values() for r in s['rows']),
        synthetic_control_rows=sum(len(s['rows']) for s in selections.values() if s['capture']['synthetic_control']),
        source_rights_verified=None if not selections else all(s['capture']['rights']['status']=='verified' for s in selections.values())),
      missingness=dict(scope='Only wider-asset targets lacking a baseline daily series; existing oil/FX coverage remains in the frozen simulation summary.',requested_wider_asset_cases=len(paths),reasons=dict(sorted(Counter(p['status'] for p in paths).items())),
        note='Absent records remain missing. A blank, missing trade, suspension, delisting and holiday are different; no calendar status inferred.'),
      safeguards=dict(original_price_writes=0,parent_report_writes=0,account_mutations=0,orders=0,paid_services=0,cost_GBP='0.00'),
      limitations=['New historical references are current-vintage unless original receipt/version evidence is actually obtained.',
        'Corporate actions, exact identity/FX, delisted/null observations and actual source gaps must be reviewed; an anonymous HTTP 200 is not validation.',
        'Source rights are resource-specific; a free download, public repo, third-party CC label or accessible HTML is not proof of permitted daily-price reuse.',
        'Unique episode IDs and embargoes reduce duplication; they do not prove statistical independence.',
        'No test on the examined 2020–2026 corpus is advertised as genuinely new. Prospective reserve has no outcomes yet.'])
