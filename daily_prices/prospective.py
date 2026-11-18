"""Seal future research signals before outcome observations; never backfill validation."""
import json
from datetime import date,timedelta
from event_history.library import require
from news_pilot.ingest import utc,at
from world_events.events import digest
from .evaluate import PROTOCOL
from .database import capture,query,select_captures
from .model import public_url


def lock(db,event,features,model,capture_ids,clock=utc):
    now=clock();start=at(PROTOCOL['prospective_from']);received=at(event['first_received_at']);published=at(event['published_at'])
    require(at(now)>=start and start<=published<=received<=at(now),'Event/receipt/lock must actually follow prospective registration')
    require((at(now)-published).total_seconds()<=PROTOCOL['maximum_event_to_lock_seconds'],'Late retrospective event cannot become a prospective forecast')
    date.fromisoformat(model['training_through'])
    require(model['training_through']<'2020-01-01' and model['test_outcomes_used']==0,'Examined test results cannot fit/select the prospective model')
    require(received<=at(features['as_of'])<=at(now) and features['outcomes_used']==0,'Features must be computed after event receipt and before actual lock')
    require(not any(p['date']>=features['as_of'][:10] for p in features.get('context',[])),'Only earlier daily observations can form signal context')
    require(event['instrument'] in model['instruments'],'No later asset/winner substitution')
    require(model['rule'] in PROTOCOL['rules'] and model['horizon'] in PROTOCOL['horizons'],'Locked predefined rule required')
    require(features['research_action'] in ('Watch','No Action'),'Research lock cannot authorize a trade')
    require(isinstance(event['synthetic_control'],bool),'Explicit real/control event classification required')
    if not event['synthetic_control']:
        require(event.get('publication_verified') is True,'Unverified/hypothetical news is not genuine new evaluation')
        public_url(event['source_url'])
    if features['research_action']=='Watch':
        require(capture_ids,'No Watch without received daily evidence')
        series=select_captures(db,capture_ids);require(set(series)=={event['instrument']},'Exact market context needed')
        expected=[r for r in series[event['instrument']]['rows'] if r['status']=='numeric' and r['date']<features['as_of'][:10]][-PROTOCOL['minimum_context_observations']:]
        require(len(expected)==PROTOCOL['minimum_context_observations'] and (at(now).date()-at(expected[-1]['date']+'T00:00:00Z').date()).days<=7,'Missing/stale context cannot become Watch')
        require(features.get('context')==[dict(date=r['date'],close=r['close']) for r in expected],'Features must match received earlier quotes')
    for cid in capture_ids:
        c=capture(db,cid)
        require(c.get('usage_scope')!='private_research','Review-only private history cannot enter the prospective journal')
        require(not c['synthetic_control'] and at(c['retrieved_at'])<=at(features['as_of']),'Only real prices actually received before feature computation')
        require(c['instrument']==event['instrument'],'No peer/index/ETF substitution in a price lock')
    payload=dict(protocol=PROTOCOL,event=event,features=features,model=model,capture_ids=sorted(capture_ids),recorded_at=now,
       research_action=features['research_action'],validated_action='No Action',probability=None,orders=0)
    lid=digest(payload)
    with db:
        # SQL write lock serializes deduplication with the insert; renamed cases in
        # the same episode cannot multiply an independent sample count.
        db.execute('BEGIN IMMEDIATE')
        old=[json.loads(r[0]) for r in db.execute('SELECT payload FROM locks')]
        require(not any(r['event']['episode_id']==event['episode_id'] for r in old),'Episode already locked; no retrospective replacement')
        db.execute('INSERT INTO locks VALUES(?,?,?)',(lid,now,json.dumps(payload,sort_keys=True)))
    return dict(lock_id=lid,recorded_at=now,validated_action='No Action')


def settle(db,lid,outcome_capture_id,clock=utc):
    now=clock();stored=db.execute('SELECT payload FROM locks WHERE id=?',(lid,)).fetchone();require(stored is not None,'Prediction must exist before settlement')
    prediction=json.loads(stored['payload']);ids=[outcome_capture_id] if isinstance(outcome_capture_id,str) else outcome_capture_id
    series=select_captures(db,ids);require(set(series)=={prediction['event']['instrument']},'Exact outcome instrument required')
    for cid in ids:
        c=capture(db,cid)
        require(c.get('usage_scope')!='private_research','Private history cannot settle prospective predictions')
        require(not c['synthetic_control'],'Synthetic prices cannot settle a real evaluation')
        require(at(prediction['recorded_at'])<at(c['retrieved_at'])<=at(now),'Outcome capture must arrive after the immutable prediction')
    rows=series[prediction['event']['instrument']]['rows']
    rows=[r for r in rows if r['date']>prediction['recorded_at'][:10]]
    h=prediction['model']['horizon'];chosen=rows[:h+1]
    complete=len(chosen)==h+1 and all(r['status']=='numeric' for r in chosen) and (date.fromisoformat(chosen[0]['date'])-date.fromisoformat(prediction['recorded_at'][:10])).days<=prediction['protocol']['max_entry_delay_calendar_days'] and not any((date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days>prediction['protocol']['max_reporting_gap_calendar_days'] for a,b in zip(chosen,chosen[1:]))
    # Report reference diagnostics only. Future execution/FX/product provenance is
    # a separate gate; do not turn a completed price window into a supported Buy.
    if complete:
        from decimal import Decimal
        field='adjusted_close' if all(r['adjusted_close'] is not None for r in chosen) else 'close'
        move=(Decimal(chosen[-1][field])/Decimal(chosen[0][field])-1)*100
        result=dict(status='matured_daily_reference_only',price_basis=field,trading_sessions_verified=False,gross_change_percent=str(move.quantize(Decimal('0.0001'))),
                    entry_date=chosen[0]['date'],exit_date=chosen[-1]['date'])
    else:result=dict(status='insufficient_outcome_data',gross_change_percent=None,entry_date=None,exit_date=None)
    payload=dict(lock_id=lid,outcome_capture_ids=sorted(ids),recorded_at=now,**result,
      net_pnl_gbp=None,reason='No verified executable product/exact-date FX/costed fill; gross reference movement is not a validated trade result.',validated_action='No Action')
    sid=digest({k:v for k,v in payload.items() if k!='recorded_at'})
    with db:db.execute('INSERT OR IGNORE INTO settlements VALUES(?,?,?,?)',(sid,lid,now,json.dumps(payload,sort_keys=True)) )
    return payload


def summary(db):
    records=[json.loads(r[0]) for r in db.execute('SELECT payload FROM locks')]
    real=[r for r in records if not r['event']['synthetic_control']]
    lids={r['event']['episode_id'] for r in real}
    ids={digest(r) for r in real};outcomes={}
    for r in db.execute('SELECT lock_id,payload FROM settlements ORDER BY recorded,id'):
        if r['lock_id'] in ids:outcomes.setdefault(r['lock_id'],[]).append(json.loads(r['payload']))
    first=[next((r for r in rows if r['status']=='matured_daily_reference_only'),None) for rows in outcomes.values()]
    return dict(kind='prospective_pre_outcome_journal',from_timestamp=PROTOCOL['prospective_from'],events=len(real),independent_episodes=len(lids),
      research_watch=sum(r['research_action']=='Watch' for r in real),research_no_action=sum(r['research_action']=='No Action' for r in real),
      matured_reference_outcomes=sum(r is not None for r in first),settlement_versions=sum(len(v) for v in outcomes.values()),
      synthetic_control_events=len(records)-len(real),calibrated_accuracy=None,predictive_edge_established=False,
      note='Unique pre-outcome locks only; price revisions do not create independent evaluations. Gross reference movements do not establish costed/executable trade outcomes.')
