"""Fit on past folds, seal research predictions, then assess later reference paths."""
from collections import Counter, defaultdict
from datetime import date,timedelta
from decimal import Decimal
import json
from pathlib import Path
from statistics import mean

from event_history.engine import publication
from event_history.library import require
from free_pilot.data import load_free_library
from simulations.engine import PROTOCOL as SIM, plan, measure, portfolio, q
from world_events.events import digest

HERE=Path(__file__).resolve().parent
PROTOCOL=json.loads((HERE/'protocol.json').read_text())
D=Decimal


def earlier_slice(data,before):
    """Fit cannot access later cases, prices or reported outcomes, even via a helper."""
    return {**data,'events':[e for e in data['events'] if publication(e,data).date().isoformat()<before],
            'observations':[p for p in data['observations'] if p['date']<before],
            'reported_reactions':[]}


def select_events(data,start,end=None):
    selected=[];excluded=[];episodes=set();last=None
    for e in sorted(data['events'],key=lambda e:(publication(e,data),e['id'])):
        day=publication(e,data).date()
        if day.isoformat()<start or end and day.isoformat()>=end:continue
        if end and (date.fromisoformat(end)-day).days<=PROTOCOL['embargo_calendar_days']:
            excluded.append(dict(event_id=e['id'],reason='fold_boundary_maturity_purge'));continue
        key=(e['targets'][0],e['category'])
        prior=next((p for p in reversed(selected) if (p['targets'][0],p['category'])==key),None)
        if e['episode_id'] in episodes or prior and (day-publication(prior,data).date()).days<=PROTOCOL['embargo_calendar_days']:
            excluded.append(dict(event_id=e['id'],reason='same_episode_or_context_response_embargo'));continue
        selected.append(e);episodes.add(e['episode_id']);last=day
    return selected,excluded


def cohort_key(event):
    return event['targets'][0]+'/'+event['category']


def candidates():
    return [(r,h) for r in SIM['rules'] for h in SIM['horizons']]


def performance(events,data,rule,horizon,cost):
    plans=[plan(e,data,e['targets'][0],rule,horizon) for e in events]
    results=[measure(p,data,cost) for p in plans]
    valid=[];settled=[];unavailable=[];no_signal=0
    for p,r in zip(plans,results):
        if p['hypothetical_intent']=='No Action':valid.append(D(0));no_signal+=1
        elif r['status']=='simulated_reference_path':valid.append(D(r['net_pnl_gbp']));settled.append(r)
        else:unavailable.append(dict(event_id=p['event_id'],reason=r['reason']))
    signals=len(plans)-no_signal
    completion=D(len(settled))/signals if signals else D(0)
    complete=bool(events) and len(valid)==len(events)
    average=mean(valid) if complete else None
    worst=min(valid) if valid else None
    score=average-max(D(0),-worst)/4 if average is not None else None
    return dict(rule=rule,horizon=horizon,cost=cost,events=len(events),signals=signals,settled=len(settled),
        no_signal=no_signal,unavailable=unavailable,completion_fraction=q(completion),
        positive=sum(r['net_outcome']=='positive' for r in settled),negative=sum(r['net_outcome']=='negative' for r in settled),
        flat=sum(r['net_outcome']=='flat' for r in settled),mean_net_pnl_gbp=q(average),
        worst_net_pnl_gbp=q(worst),score=q(score),complete_sample=complete,
        event_ids=[e['id'] for e in events],
        outcome_end_dates=[r['exit_date'] for r in settled])


def rank_key(metric):
    return (metric['score'] is not None,D(metric['score']) if metric['score'] is not None else D('-Infinity'),
            metric['settled'],-metric['horizon'],metric['rule'])


def fit(data):
    """No test event/price is supplied to either training or validation scoring."""
    require((HERE/'PROTOCOL.sha256').read_text().strip()==digest(PROTOCOL),'Learning protocol changed')
    train=earlier_slice(data,PROTOCOL['validation_from']);val=earlier_slice(data,PROTOCOL['test_from'])
    training,train_ex=select_events(train,PROTOCOL['train_from'],PROTOCOL['validation_from'])
    validating,val_ex=select_events(val,PROTOCOL['validation_from'],PROTOCOL['test_from'])
    train_groups=defaultdict(list);val_groups=defaultdict(list)
    for e in training:train_groups[cohort_key(e)].append(e)
    for e in validating:val_groups[cohort_key(e)].append(e)
    models={}
    for key,events in sorted(train_groups.items()):
        metrics=[performance(events,train,r,h,PROTOCOL['selection_cost']) for r,h in candidates()]
        ordered=sorted(metrics,key=rank_key,reverse=True)
        eligible=[m for m in ordered if m['complete_sample'] and m['settled']>=PROTOCOL['minimum_training_trades']
                  and D(m['completion_fraction'])>=D(PROTOCOL['minimum_signal_completion_fraction'])
                  and m['score'] is not None and D(m['score'])>0]
        shortlist=eligible[:PROTOCOL['training_shortlist']]
        validations=[]
        for m in shortlist:
            evs=val_groups.get(key,[])
            tested=performance(evs,val,m['rule'],m['horizon'],PROTOCOL['selection_cost'])
            stress=performance(evs,val,m['rule'],m['horizon'],PROTOCOL['robustness_cost'])
            qualified=(tested['complete_sample'] and tested['settled']>=PROTOCOL['minimum_validation_trades']
                and D(tested['completion_fraction'])>=D(PROTOCOL['minimum_signal_completion_fraction'])
                and tested['score'] is not None and D(tested['score'])>0
                and stress['mean_net_pnl_gbp'] is not None and D(stress['mean_net_pnl_gbp'])>0)
            validations.append(dict(candidate=m,validation=tested,stress=stress,qualified=qualified))
        winners=sorted([v for v in validations if v['qualified']],key=lambda v:rank_key(v['validation']),reverse=True)
        # Rejected leader is diagnostic; no fallback masquerades as validation.
        leader=next((m for m in ordered if m['settled']>0),None)
        chosen=winners[0]['candidate'] if winners else None
        diagnostic=chosen or leader
        extra_validation=None
        if diagnostic and not any(v['candidate']['rule']==diagnostic['rule'] and v['candidate']['horizon']==diagnostic['horizon'] for v in validations):
            extra_validation=performance(val_groups.get(key,[]),val,diagnostic['rule'],diagnostic['horizon'],PROTOCOL['selection_cost'])
        model=dict(cohort=key,training_candidates=metrics,validation_candidates=validations,
            selected=chosen,diagnostic_leader=diagnostic,diagnostic_validation=extra_validation,
            status='candidate_passed_validation_not_a_validated_forecast' if chosen else 'insufficient_or_nonrobust_training_validation',
            historical_lock_boundary=PROTOCOL['test_from'],
            protocol_sha256=digest(PROTOCOL),sim_protocol_sha256=digest(SIM))
        models[key]=model | {'model_sha256':digest(model)}
    return dict(models=models,training_event_ids=[e['id'] for e in training],validation_event_ids=[e['id'] for e in validating],
                excluded_training=train_ex,excluded_validation=val_ex,
                multiple_testing=dict(candidates_per_cohort=9,training_cohorts=len(models),
                    attempted_training_candidates=len(models)*9,selection_only_on_training_validation=True,
                    significance_established=False),
                test_outcomes_used=0,protocol_sha256=digest(PROTOCOL))


def prediction(event,data,locked):
    model=locked['models'].get(cohort_key(event));candidate=model['diagnostic_leader'] if model else None
    # No model is evaluated using a later quote or test-label information.
    p=plan(event,data,event['targets'][0],candidate['rule'] if candidate else 'event_long',candidate['horizon'] if candidate else 5)
    prior_features=dict(category=p['category'],market=p['market'],location=p['location'],mechanism=p['mechanism'],
        trend=p['context']['trend'],context_change_percent=p['context'].get('change_percent'),
        context=[{k:v for k,v in point.items() if k not in ('snapshot_id','fx_snapshot_id')}
                 for point in p['context']['points']])
    active=bool(candidate) and p['hypothetical_intent']=='Conditional hypothetical Buy'
    payload=dict(event_id=event['id'],title=event['title'],market=p['market'],cohort=cohort_key(event),
        source_id=event['publication_source'],simulated_decision_bound=p['decision_bound'],
        research_action='Watch' if active else 'No Action',
        hypothetical_intent='Conditional hypothetical Buy' if active else 'No Action',
        validated_action='No Action',rule=candidate['rule'] if candidate else None,
        horizon=candidate['horizon'] if candidate else None,features=prior_features,
        model_sha256=model['model_sha256'] if model else None,
        candidate_passed_validation=bool(model and model['selected']),
        probability=None,probability_reason='Sparse selected current-vintage samples do not support a calibrated forecast.',
        original_availability_verified=False,execution_supported=False,
        reason=model['status'] if model else 'no_prior_same_market_category_model',
        protocol_sha256=digest(PROTOCOL))
    return payload | {'prediction_id':digest(payload)}


def prepare(data=None):
    data=data or load_free_library();locked=fit(data)
    test_data=earlier_slice(data,(date.fromisoformat(PROTOCOL['test_through'])+timedelta(days=1)).isoformat())
    events,excluded=select_events(test_data,PROTOCOL['test_from'])
    predictions=[prediction(e,test_data,locked) for e in events]
    plans=[]
    for e,p in zip(events,predictions):
        frozen=plan(e,test_data,e['targets'][0],p['rule'] or 'event_long',p['horizon'] or 5)
        if p['hypothetical_intent']=='No Action':
            frozen=frozen | dict(hypothetical_intent='No Action',status='locked_rule_does_not_trigger_or_no_model')
        plans.append(frozen)
    return dict(locked=locked,events=events,predictions=predictions,plans=plans,excluded_test=excluded,
        source_links=[dict(id=s['id'],url=s['url'],publisher=s['publisher']) for s in data['sources'].values()])


def assess(prepared,data):
    observed=earlier_slice(data,(date.fromisoformat(PROTOCOL['test_through'])+timedelta(days=1)).isoformat())
    records=[]
    # Only after prepare has completed/sealed ALL predictions do outcomes enter.
    for event,p,planned in zip(prepared['events'],prepared['predictions'],prepared['plans']):
        if p['rule'] is None:
            outcome=dict(status='no_candidate_forecast',reason=p['reason'],net_pnl_gbp=None,path=[],actions=[])
        else:
            require(planned['decision_bound']==p['simulated_decision_bound'],'Historical bound changed')
            outcome=measure(planned,observed,PROTOCOL['selection_cost'])
        baseline=measure(plan(event,observed,event['targets'][0],'event_long',5),observed,PROTOCOL['selection_cost'],risk_exit=False)
        stressed=None if p['rule'] is None else measure(planned,observed,PROTOCOL['robustness_cost'])
        records.append(dict(prediction=p,outcome=outcome,fixed_buy_and_hold_baseline=baseline,stressed_cost_outcome=stressed))
    active=[r for r in records if r['prediction']['hypothetical_intent']=='Conditional hypothetical Buy']
    settled=[r for r in active if r['outcome']['status']=='simulated_reference_path']
    positive=sum(r['outcome']['net_outcome']=='positive' for r in settled)
    negative=sum(r['outcome']['net_outcome']=='negative' for r in settled)
    baselines=[r['fixed_buy_and_hold_baseline'] for r in records]
    return dict(records=records,heldout_reference_portfolio=portfolio(prepared['plans'],observed),summary=dict(retained_test_events=len(records),
        research_watch=len(active),research_no_action=len(records)-len(active),settled_diagnostic_hypotheses=len(settled),
        positive=positive,negative=negative,flat=len(settled)-positive-negative,
        directional_false_positives=negative+sum(r['outcome']['net_outcome']=='flat' for r in settled),
        missing_or_unsettled_signals=len(active)-len(settled),
        conditional_hit_fraction=q(D(positive)/len(settled)) if settled else None,
        fixed_baseline_settled=sum(b['status']=='simulated_reference_path' for b in baselines),
        fixed_baseline_positive=sum(b.get('net_outcome')=='positive' for b in baselines),
        fixed_baseline_negative=sum(b.get('net_outcome')=='negative' for b in baselines),
        calibration=None,calibration_reason='No probabilistic forecasts issued; a conditional historical hit fraction is not calibrated predictive accuracy.',
        qualified_candidate_cohorts=sum(m['selected'] is not None for m in prepared['locked']['models'].values()),
        supported_entries=0,validated_buy=0,validated_no_action=len(records),
        repeatable_pattern_established=False,point_in_time_safe=False),
        no_trade=dict(initial_cash_gbp='50',final_cash_gbp='50',net_pnl_gbp='0'))


def assemble(prepared,assessed):
    return dict(schema_version=1,kind='chronological_candidate_research_only',protocol=PROTOCOL,
        locked=prepared['locked'],excluded_test=prepared['excluded_test'],source_links=prepared['source_links'],**assessed,
        cost_GBP='0.00',orders=0,account_mutations=0,
        limitations=['Training 2006–2015, validation 2016–2019, held-out 2020–2026; no test outcomes in fitting or validation selection.',
            'One primary market per event, same-market/category cohorts, episode/45-day embargo and boundary maturity purge reduce leakage, not establish independence.',
            'Rejected training leaders are diagnostic hypotheses, not qualified forecasts. No later winner can replace a locked rule.',
            'Nine candidates per cohort create multiple-testing risk; this is not a prospective preregistration or proof the developers never saw historical outcomes.',
            'Selected corpus has survivorship/selection/regime bias. Current-vintage source data lacks original news/price availability and executable products.',
            'No calibrated probability, repeatable pattern, supported Buy, prospective paper fill or live order is established.'])


def build_report(data=None):
    data=data or load_free_library();prepared=prepare(data)
    return assemble(prepared,assess(prepared,data))


def public_view(report):
    """All public findings without local journal/window identity internals."""
    def clean(x):
        if isinstance(x,dict):
            return {k:clean(v) for k,v in x.items() if k not in
                    ('model_sha256','prediction_id','protocol_sha256','sim_protocol_sha256','snapshot_id','fx_snapshot_id','features')}
        if isinstance(x,list):return [clean(v) for v in x]
        return x
    return clean(report)
