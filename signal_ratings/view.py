"""Compact private screen, sharing the public empty shell and existing house style."""
import json
from pathlib import Path
from decimal import Decimal as D
from daily_prices.stooq import private_path
from event_history.library import require
from .policy import POLICY

ROOT=Path(__file__).resolve().parents[1]


def screen_view(report):
    require(report['kind']=='PRIVATE_SIGNAL1_EXPLORATORY','Private SIGNAL-1 report required')
    selected=set();cards=[]
    for card in report['cards']:
        ids=card['member_ids'];chosen=[]
        for direction in (-1,0,1):
            matching=[]
            for key in ids:
                w=report['windows'][key];value=w['entry_reaction']['change_percent']
                if value is None:continue
                sign=1 if D(value)>0 else -1 if D(value)<0 else 0
                if sign==direction and w['costs']['declared']['status']=='simulated_reference_path':matching.append(key)
            chosen+=matching[:4]
        sourced=[key for key in ids if report['windows'][key]['evidence']['sources']]
        chosen=list(dict.fromkeys(chosen+sourced[:2]))
        selected.update(chosen)
        cards.append({k:v for k,v in card.items() if k not in ('member_ids','control_ids')}|dict(example_ids=chosen,
                     full_matured_examples=len(ids),example_selection='First chronological positive/negative/flat examples and up to two sourced cases; not largest winners. Full population remains in private analysis JSON.'))
    examples={}
    for key in sorted(selected):
        w=report['windows'][key];e=w['evidence']
        sources=[s for s in e['sources'] if s['published_day']<report['as_of']]
        examples[key]=dict(instrument=w['instrument'],date=w['detection_day'],maturity_day=w['maturity_day'],
              change_percent=w['entry_reaction']['change_percent'],SPY_excess_pp=w['entry_reaction']['SPY_excess_percentage_points'],
              costs={c:{k:o.get(k) for k in ('status','reason','net_pnl_gbp','entry_date','exit_date')} for c,o in w['costs'].items()},
              catalyst=dict(category=e['category'],explanation=e['explanation'],weakness=e['weakness'],
                            sources=[s['id'] for s in sources],retrospective_only=True))
    controls=[]
    for c in report['issuer_controls']:
        # Sources/cases from after an earlier assessment cannot appear as its evidence.
        if c['publication_day']>=report['as_of']:continue
        controls.append(dict(instrument=c['instrument'],category=c['category'],publication_day=c['publication_day'],
                             source=c['source'],selection=c['selection'],publication_note=c['publication_note'],
                             reactions=[r for r in c['publication_day_followthrough'] if r.get('end_date') and r['end_date']<report['as_of']]))
    return dict(schema_version=1,kind='PRIVATE_SIGNAL1_SCREEN',synthetic=False,as_of=report['as_of'],
                source_rows=report['source_rows'],all_history_previously_examined=True,
                source_profile='Private current-vintage owner files; adjustments, original availability and execution unverified.',
                rating_counts=report['rating_counts'],cards=cards,examples=examples,
                sources={k:v for k,v in report['source_facts'].items() if v['published_day']<report['as_of']},
                issuer_controls=controls,catalyst_catalogue=[dict(g,cases=[c for c in g['cases'] if c['date']<report['as_of']]) for g in report.get('catalyst_catalogue',[])],pending_count=len(report['pending']),current_signals=0,
                likely_approved_validation_ids=[],limitations=report['limitations'])


def render_private(path,report):
    view=screen_view(report)
    return render_screen(path,view)


def render_screen(path,view):
    require(view['kind']=='PRIVATE_SIGNAL1_SCREEN','Private screen evidence required')
    template=(ROOT/'signals/index.html').read_text()
    css='\n'.join((ROOT/p).read_text() for p in ('.claude/skills/market-ripple-design/design.css','ripple/style.css','signals/style.css'))
    code=(ROOT/'signals/contract.mjs').read_text().replace('export ','')+'\n'+(ROOT/'signals/view.mjs').read_text().split('\n',1)[1].replace('export ','')
    encoded=json.dumps(view,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=template.replace('<link rel="stylesheet" href="../matching/design.css"><link rel="stylesheet" href="../ripple/style.css"><link rel="stylesheet" href="style.css">','<style>'+css+'</style>')
    template=template.replace('<script type="module" src="view.mjs"></script>',
        '<script type="application/json" id="embedded-policy">'+json.dumps(POLICY)+'</script><script type="application/json" id="embedded-report">'+encoded+'</script><script>'+code+'</script>')
    p=private_path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as stream:p.chmod(0o600);stream.write(template)
    return p
