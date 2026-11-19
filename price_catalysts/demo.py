"""Deliberately fabricated browser/regression controls; never actual market data."""
from datetime import date,timedelta
from decimal import Decimal as D
from daily_prices.stooq_calendar import is_session
from .detector import detect
from .ledger import build


def synthetic_report():
    rows=[];d=date(2024,1,2);price=D(100)
    while len(rows)<110:
        day=d.isoformat();d+=timedelta(days=1)
        if not is_session(day):continue
        price*=1+D([1,-2,3,-1,2,-3][len(rows)%6])/1000
        rows.append(dict(date=day,status='numeric',open=str(price),high=str(price*D('1.01')),low=str(price*D('.99')),close=str(price),volume='100'))
    rows[70]=dict(rows[70],close=str(D(rows[69]['close'])*D('1.2')),volume='700')
    selections={s:dict(rows=rows,capture={'payload_sha256':'SYNTHETIC-'+s}) for s in ['NVDA','AMD','MRNA','BMY','SPY','GLD']}
    scan=detect(selections);focus=scan['focus'][0];day=focus['date'];prior=rows[10]['date']
    source=dict(id='synthetic',publisher='SYNTHETIC fixture',title='SYNTHETIC contemporary announcement',published_day=prior,
        published_at=None,precision='day_only',url='https://example.org/synthetic-evidence',fact='Fabricated source used to test rendering only.',kind='primary')
    evidence=dict(researched_at='2026-11-19T08:00:00Z',sources={'synthetic':source},investigations={focus['id']:dict(sources=['synthetic'],category='plausible',
        explanation='SYNTHETIC association for browser tests; not actual market research.',weakness='Unknown clock; no causal proof.',search='SYNTHETIC',causal_proof=False)},
        controls=[dict(id='synthetic-control',instrument='NVDA',source='synthetic',category='earnings',occurred_day=prior)])
    fx=[dict(instrument='gbpusd',date=r['date'],value='1.25',status='numeric',source_id='synthetic',snapshot_id='synthetic') for r in rows]
    report=build(scan,selections,evidence=evidence,data=dict(observations=fx))
    report['limitations'].insert(0,'SYNTHETIC TEST FIXTURE — no actual market prices or performance.')
    return report
