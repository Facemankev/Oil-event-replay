"""Private Move → Evidence → Explanation ledger; no publisher for owner data."""
import json
from collections import Counter
from datetime import date,timedelta
from pathlib import Path
from statistics import median
from decimal import Decimal as D
from event_history.library import require
from world_events.events import digest
from .detector import PROTOCOL,rank
from .evidence import load_evidence,explanation
from .replay import Evaluator,replay,HORIZONS,reaction

ROOT=Path(__file__).resolve().parents[1]


def overlap(record,prior_study):
    if not prior_study:return dict(status='prior_window_audit_not_supplied',previously_examined=True,genuinely_unseen=False)
    windows=[]
    for c in prior_study['cases']:
        if c['instrument']!=record['instrument']:continue
        r=c.get('reaction',{});start=r.get('baseline_date');end=r.get('end_date')
        if start and end and start<=record['date']<=end:windows.append(c['event_id'])
        for v in c.get('costs',{}).values():
            if v.get('entry_date') and v.get('exit_date') and v['entry_date']<=record['date']<=v['exit_date']:windows.append(c['event_id'])
    return dict(status='overlaps_prior_study_window' if windows else 'newly_investigated_outcome_selected_history',
                prior_event_ids=sorted(set(windows)),previously_examined=bool(windows),genuinely_unseen=False,
                reason='Full current-vintage historical scan exposes realised outcomes; new curation is not untouched validation.')


def build(scan,selections,evidence=None,data=None,prior_study=None):
    require(scan['protocol']==PROTOCOL,'Scan used a different protocol')
    require(scan['capture_fingerprints']=={s:r['capture']['payload_sha256'] for s,r in selections.items()},'Scan/database capture mismatch')
    evidence=evidence or load_evidence();evaluator=Evaluator(selections,data)
    original={n:(ROOT/n/'REPORT.sha256').read_text().strip() for n in ('learning','simulations')}
    _,focus=rank(scan['features']);focus_ids={r['id'] for r in focus};unique={}
    for families in scan['rankings'].values():
        for family,rows in families.items():
            for r in rows:
                entry=unique.setdefault(r['id'],dict(r,selected_by=[]))
                entry['selected_by'].append(dict(family=family,rank=r['rank'],score=r['ranking_score']))
    ledger=[]
    for r in sorted(unique.values(),key=lambda r:(r['instrument'],r['date'])):
        e=explanation(r,evidence)
        # Data anomaly review is a limitation, not an invented company event.
        if r['id']=='BMY-1986-12-26':e['data_review']='Unusual historical step; adjustment/corporate-action reconciliation unresolved.'
        gld=next((f for f in scan['features']['GLD'] if f['date']==r['date']),None)
        ledger.append(dict(r,evidence=e,investigation_focus=r['id'] in focus_ids,examination=overlap(r,prior_study),
            subsequent=evaluator.record(r),GLD_same_session_change_percent=gld['close_change_percent'] if gld else None,
            GLD_role='Descriptive gold ETF proxy; not gold spot, not causal proof or a trade target.',validated_action='No Action',
            action_reason='Private quarantine; adjustments, original availability, execution and predictive calibration unverified. Discovery is outcome selected.'))
    controls=[]
    for c in evidence['controls']:
        source=evidence['sources'][c['source']];pub=source['published_day']
        # Reuse conservative day-only publication bound, not an invented 00:00 receipt.
        anchor=(date.fromisoformat(pub)+timedelta(days=2)).isoformat() if not source['published_at'] else source['published_at'][:10]
        controls.append(dict(c,source=source,publication_day=pub,actual_historical_receipt_at=None,
            publication_day_clock_unknown=source['published_at'] is None,eligibility_anchor=anchor,
            selection='Complete protocol issuer/FDA pool, independent of realised return; all members retained.',
            publication_day_followthrough=[reaction(evaluator.rows[c['instrument']],evaluator.rows['SPY'],pub,h,evaluator.calendar)|dict(horizon=h) for h in HORIZONS],
            publication_note='Close on publication day to H later sessions: descriptive only, not a measured intraday first reaction. Day-only news may be pre-open or after-close.',
            subsequent=[evaluator.window(c['instrument'],anchor,h) for h in HORIZONS],validated_action='No Action'))
    diagnostic=[]
    for category in sorted({c['category'] for c in controls}):
        for h in HORIZONS:
            pool=[next(w for w in c['publication_day_followthrough'] if w['horizon']==h) for c in controls if c['category']==category]
            values=[D(w['change_percent']) for w in pool if w['change_percent'] is not None]
            diagnostic.append(dict(category=category,horizon=h,selected=len(pool),complete=len(values),missing=len(pool)-len(values),
                positive=sum(v>0 for v in values),negative=sum(v<0 for v in values),flat=sum(v==0 for v in values),
                within_one_percent_descriptive=sum(abs(v)<=1 for v in values),median_change_percent=str(median(values)) if values else None,
                interpretation='Complete calendar-selected controls. Direction and quietness are measured outcomes; no predicted probability or claim of identical catalysts.'))
    studied=[r for r in ledger if r['investigation_focus']]
    result=dict(schema_version=1,kind='PRIVATE_EVT3_exploratory_ledger',protocol=PROTOCOL,protocol_sha256=digest(PROTOCOL),
        capture_fingerprints=scan['capture_fingerprints'],source_rows=scan['source_rows'],evidence_sha256=digest(evidence),evidence_researched_at=evidence['researched_at'],
        ledger=ledger,investigation_summary=dict(focus=len(studied),categories=dict(Counter(r['evidence']['category'] for r in studied)),
            explained_means='A possible sourced association, never proven causality. Unexplained includes later-only evidence.'),
        independent_catalyst_controls=controls,independent_control_summary=diagnostic,
        replay=replay(scan,evaluator),parent_report_fingerprints=original,holdout_changed=False,prospective_predictions=0,
        validated_buys=0,actual_alerts=0,continuous_monitor_deployed=False,
        limitations=['Current-vintage owner files are private provisional data, with unknown price/volume adjustment method and original receipt.',
          'All scanned historical results are exploratory. Source selection, survivorship, multiple testing, overlap and macro regimes can create apparent patterns.',
          'Bounded news research is incomplete; absence of evidence is not proof of no news. Later citations never become early features.',
          'No learning/training, probabilities, trade recommendations, account mutations or public redistribution.',
          'Continuous feed ingestion and a genuinely new prospective prediction/settlement journal are a subsequent issue stage, not claimed here.'])
    require(original=={n:(ROOT/n/'REPORT.sha256').read_text().strip() for n in original},'Parent report fingerprint changed')
    return result


def markdown(report):
    lines=['# Private Market Ripple price-led review','',
      'Owner research only. Do not publish this report or its detailed HTML. All historical outcomes are exploratory, not validated predictions.',
      '',f"Scanned {report['source_rows']:,} original observations; no price writes. Ranked {len(report['ledger'])} distinct bars; investigated {report['investigation_summary']['focus']}. Categories: {json.dumps(report['investigation_summary']['categories'],sort_keys=True)}.",
      '', '## Ranked movement ledger','', '| Instrument/date | Discovery return % | SPY excess pp | Evidence | 1 / 5 / 20 later sessions % |','| --- | ---: | ---: | --- | --- |']
    for r in report['ledger']:
        if not r['investigation_focus']:continue
        values=' / '.join(w['reaction']['change_percent'] or 'missing' for w in r['subsequent'])
        lines.append(f"| {r['id']} | {r['close_change_percent']} | {r['SPY_excess_percentage_points'] or 'missing'} | {r['evidence']['category']} ({r['evidence']['confidence']}) | {values} |")
    lines += ['', 'Discovery returns were already realised at detection. They are never booked as paper-trade profit. Hypothetical entry is a later close; costs/FX and SPY require exact windows. See ledger JSON/HTML for every ranked bar, source clock, control, missing window and cost scenario.',
      '', '## Fixed-rule replay','',f"Trigger bars: {report['replay']['trigger_bars']}; first chronological episodes: {report['replay']['first_trigger_episodes']}; daily-return rule cases: {report['replay']['daily_anomaly_rule_cases']}. Reused context controls: {report['replay']['reused_context_controls']}. They are not independent trials.",
      '', '| Slice / rule | H | Cost | Lane | Complete / attempts | Positive / negative | Median net GBP | Median net excess vs SPY GBP |','| --- | ---: | --- | --- | --- | --- | ---: | ---: |']
    for r in report['replay']['summaries']:
        lines.append(f"| {r['period']} / {r['rule']} | {r['horizon']} | {r['cost']} | {r['lane']} | {r['complete']} / {r['attempts']} | {r['positive']} / {r['negative']} | {r['median_net_pnl_gbp'] or 'missing'} | {r['median_net_excess_vs_SPY_gbp'] or 'missing'} |")
    lines += ['', '## Matched control comparison','',
      'Only pairs with both windows measured enter the paired difference. Missing pairs stay in the attempt count. Cross-asset/macro dependence and reused controls prevent treating these as independent trials.',
      '', '| Slice / rule | H | Cost | Complete / attempts | Better / worse | Median signal minus control GBP |',
      '| --- | ---: | --- | --- | --- | ---: |']
    for r in report['replay']['paired_context_comparisons']:
        lines.append(f"| {r['period']} / {r['rule']} | {r['horizon']} | {r['cost']} | {r['complete_pairs']} / {r['attempts']} | {r['signal_better']} / {r['signal_worse']} | {r['median_paired_net_difference_gbp'] or 'missing'} |")
    lines += ['', 'Instrument-specific summaries are retained in JSON; pooled SPY-versus-itself excess is mechanically zero and is not evidence of alpha.',
      '', '## Independent source-selected controls','',json.dumps(report['independent_control_summary'],indent=2),
      '', '## Limits and next stage','',*report['limitations'],
      '', 'No demonstrated prospective predictive value. No supported Buy, no actual alerts or new settled predictions. The original examined holdout/report fingerprints are unchanged. Bounded feed integration and genuine pre-outcome prediction locking remain to implement and operate.']
    lines += ['', '## Dated catalyst investigations','']
    for row in report['ledger']:
        if not row['investigation_focus']:continue
        e=row['evidence']
        lines += [f"### {row['id']} — {e['category']} ({e['confidence']} confidence)", '', e['explanation'], '', e['weakness'], '']
        for s in e['sources']:
            lines += [f"- [{s['title']}]({s['url']}) — {s['publisher']}; publication {s['published_day']}; {s['published_at'] or 'intraday time unknown'}; {s['timing']}. {s['fact']}"]
        if not e['sources']:lines+=['- No reliable source established in this bounded search.']
        lines += ['', 'Actual historical receipt unknown. No proven causal effect or early warning.', '']
    return '\n'.join(lines)+'\n'


def audit(report):
    """Public audit COUNTS only. No prices, returns, P&L, row traces or hashes."""
    return dict(schema_version=1,kind='EVT3_public_audit_metadata_only',
        source_observations=report['source_rows'],original_price_writes=0,
        ranked_distinct_bars=len(report['ledger']),investigation=report['investigation_summary'],
        independent_source_selected_controls=len(report['independent_catalyst_controls']),
        trigger_bars=report['replay']['trigger_bars'],first_trigger_episodes=report['replay']['first_trigger_episodes'],
        fixed_daily_rule_cases=report['replay']['daily_anomaly_rule_cases'],
        published_price_return_or_PNL_values=0,holdout_changed=False,genuinely_unseen_historical_tests=0,
        actual_prospective_predictions=0,qualified_buys=0,continuous_monitor_deployed=False,
        results_location='Owner-only ignored work/evt3; private detailed results must not be hosted or uploaded as CI artifacts.',
        conclusion='Exploratory associations and mixed diagnostic outcomes do not establish prospective predictive value. Source adjustment/authentication, original receipt and execution remain unverified.',
        next_stage='Bounded permitted feeds and an actual-clock pre-outcome prediction/settlement journal; not claimed deployed by this catalogue stage.')
