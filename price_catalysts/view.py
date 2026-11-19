"""Generate a standalone private Gold × Desk review; never deploy owner data."""
import json
from pathlib import Path
from daily_prices.stooq import private_path
from event_history.library import require

ROOT=Path(__file__).resolve().parents[1]


def screen_view(report):
    """Keep full replay traces in JSON; the PRIVATE mobile page needs less data."""
    def outcome(o):
        return {k:o.get(k) for k in ('entry_date','exit_date','net_pnl_gbp','reason')}
    ledger=[]
    for row in report['ledger']:
        r={k:row[k] for k in ('id','instrument','date','close_change_percent','overnight_gap_percent',
           'SPY_excess_percentage_points','GLD_same_session_change_percent','volume_ratio','basis',
           'data_flags','detection_assumption','evidence','examination','action_reason','selected_by')}
        r['subsequent']=[dict(horizon=w['horizon'],reaction=w['reaction'],
            costs={c:outcome(o) for c,o in w['costs'].items()},SPY_costs={c:outcome(o) for c,o in w['SPY_costs'].items()}) for w in row['subsequent']]
        ledger.append(r)
    return dict(source_rows=report['source_rows'],ledger=ledger,investigation_summary=report['investigation_summary'],
        replay={k:report['replay'][k] for k in ('trigger_bars','first_trigger_episodes','daily_anomaly_rule_cases')},
        independent_catalyst_controls=[{k:c[k] for k in ('source','instrument','publication_day','category')} for c in report['independent_catalyst_controls']],
        limitations=report['limitations'])


def render_private(path,report):
    require(report['kind']=='PRIVATE_EVT3_exploratory_ledger' and report['validated_buys']==0,'Private exploratory ledger required')
    p=private_path(path);p.parent.mkdir(parents=True,exist_ok=True)
    css=(ROOT/'.claude/skills/market-ripple-design/design.css').read_text()
    template=(Path(__file__).parent/'template.html').read_text()
    # No data strings are HTML, even inside the inert JSON script element.
    encoded=json.dumps(screen_view(report),ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    text=template.replace('/* HOUSE_STYLE */',css).replace('/* PRIVATE_DATA */',encoded)
    with p.open('x',encoding='utf-8') as f:
        p.chmod(0o600);f.write(text)
    return p
