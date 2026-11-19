"""Private owner results and a public count-only audit projection."""
from collections import Counter
from .policy import POLICY


def audit(report):
    return dict(schema_version=1,scope='Examined historical hypotheses, not independent opportunities or current signals',
        original_observations=report['source_rows'],original_writes=0,hypotheses=len(report['cards']),
        pattern_families=len(POLICY['patterns']),rating_counts=report['rating_counts'],
        default_possible_directions=dict(Counter(c['direction'] for c in report['cards'] if c['ratings']['declared']['rating']=='POSSIBLE')),
        approved_current_signals=0,independently_validated_patterns=0,prospective_predictions=0,
        holdout_changed=False,model_fitted=False,public_price_return_or_PNL_values=0,
        detail_location='Ignored owner-only work/signal1; never publish detailed reports, CSVs or database.',
        conclusion='Possible means exploratory historical evidence. No Likely evidence exists; no source or paper-execution check is relaxed.')


def markdown(report):
    lines=['# Private SIGNAL-1 historical opportunity review','',
      'Do not publish this report. Current-vintage private Stooq observations, all already examined; no new untouched evaluation or prospective forecasts. Possible is exploratory, not trade permission. DOWN means downside risk watch, never short-sale profit.',
      '',f"Assessment {report['as_of']}; {report['source_rows']:,} observations; {len(report['cards'])} overlapping pattern/direction/horizon hypotheses. {len(report['pending'])} incomplete future windows pending, never filled.",
      '', '## Rating counts by illustrative cost assumption','',
      '| Cost | Possible | No Action | Likely |','| --- | ---: | ---: | ---: |']
    for cost,counts in report['rating_counts'].items():
        lines.append(f"| {cost} | {counts.get('POSSIBLE',0)} | {counts.get('NO ACTION',0)} | {counts.get('LIKELY',0)} |")
    lines+=['','## Default-cost exploratory patterns','',
      '| Hypothesis | Complete / attempts | Direction successes / failures | Mean / median USD % | Median SPY excess pp | Median long net GBP | Median matched-control difference GBP |',
      '| --- | --- | --- | --- | --- | --- | --- |']
    for c in report['cards']:
        if c['ratings']['declared']['rating']!='POSSIBLE':continue
        s=c['costs']['declared'];lines.append(f"| {c['id']} | {s['complete']} / {s['attempts']} | {s['successful']} / {s['unsuccessful']} | {s['mean_return_percent']} / {s['median_return_percent']} | {s['median_SPY_excess_pp']} | {s['median_net_gbp']} | {s['median_paired_difference_gbp']} |")
    lines+=['','These rows share events, periods, controls and horizons. They are not independent opportunities. Historical direction hit rates are not forecast probabilities. USD price direction and GBP long profit differ; negative long profit is never converted into a fictional short profit. The client rechecks Possible gates and rejects imported self-certified Likely ratings.',
      '', '## Recurring contemporary contexts','']
    for g in report.get('catalyst_catalogue',[]):
        lines += [f"### {g['context']}",'',g['interpretation'],'']
        for c in g['cases']:
            lines += [f"- {c['instrument']} {c['date']}: {c['explanation']} {c['weakness']}"]
            for sid in c['sources']:
                s=report['source_facts'][sid];lines += [f"  [{s['title']}]({s['url']}) — {s['publisher']}, {s['published_day']}; {s['published_at'] or 'intraday clock unknown'}."]
        lines+=['']
    lines+=['## Limits and next stage','',*report['limitations'],'',
      'Genuinely independent future validation remains necessary before Likely. No current signal, paper entry, source promotion, original price write or model training is authorised. Physical iPhone/iPad Safari testing remains separate.']
    return '\n'.join(lines)+'\n'
