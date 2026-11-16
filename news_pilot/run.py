"""One controlled fetch-to-local-card run. No scheduler, messages or trading."""
import argparse
import json
from pathlib import Path
import subprocess
import time
from .ingest import poll, visible, utc, open_journal
from .sources import SOURCES
from equities.collect import ROOT, SafeError


def run(directory, source, client=None, clock=utc, timer=time.perf_counter):
    start=timer(); started=clock()
    kwargs=dict(clock=clock,timer=timer)
    if client is not None:kwargs['client']=client
    receipt=poll(directory,source,**kwargs)
    before_analysis=timer();cutoff=clock()
    records=visible(directory,cutoff)
    result=subprocess.run(['node',str(ROOT/'news_pilot/analyze.mjs')],
        input=json.dumps(dict(articles=records,as_of=cutoff)),capture_output=True,text=True,timeout=30,cwd=ROOT)
    if result.returncode:raise SafeError('Local analysis failed; receipt journal retained')
    analysis=json.loads(result.stdout);ready=clock();finished=timer()
    # Ready-time ages include actual analysis work, without admitting later data.
    for card in analysis['cards']:
        from .ingest import at
        card['receipt_to_card_seconds']=(at(ready)-at(card['latest_version_first_seen_at'])).total_seconds()
        if card['published_at']:card['publication_to_card_seconds']=(at(ready)-at(card['published_at'])).total_seconds()
    report=dict(new_receipt_cards=sum(c['latest_version_first_seen_at']==receipt.get('received_at') for c in analysis['cards']),schema_version=1,transport_mode='controlled_fixture' if client is not None else 'direct_public_http',clock_mode='controlled' if clock is not utc else 'system_UTC',started_at=started,card_ready_at=ready,analysis_as_of=cutoff,
        ingestion=receipt,analysis=analysis,timings_ms=dict(analysis_ms=round((finished-before_analysis)*1000,3),
        fetch_to_card_ms=round((finished-start)*1000,3)),
        polling_note='Manual single bounded run; configured 60-second minimum interval is not a continuously achieved alert guarantee.')
    path,_db=open_journal(directory);_db.close()
    # Immutable per-run output, including blocked/cooldown attempts.
    import uuid
    out=path/('run-'+uuid.uuid4().hex+'.json');out.write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',choices=SOURCES,required=True);p.add_argument('--journal',required=True,type=Path)
    args=p.parse_args()
    try:
        r=run(args.journal,args.source)
        print(json.dumps(dict(ingestion=r['ingestion'],timings_ms=r['timings_ms'],
            cards=len(r['analysis']['cards']),fresh=sum(c['freshness'].startswith('fresh_') for c in r['analysis']['cards']),
            actions={'Buy':0,'No_Action':len(r['analysis']['cards'])},continuous=False),indent=2))
    except Exception:p.exit(1,'Controlled pilot failed safely; no external alert or order; details suppressed.\n')


if __name__=='__main__':main()
