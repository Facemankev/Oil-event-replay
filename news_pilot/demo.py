"""Controlled transport with real previously sourced release facts, not a live alert."""
import argparse
from datetime import datetime
from email.utils import format_datetime
import hashlib
import json
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape
from .run import run
from equities.collect import ROOT


def build_demo():
    originals=json.loads((ROOT/'equities/news.json').read_text())['articles']
    wire=next(a for a in originals if a['id']=='board-wire')
    primary=next(a for a in originals if a['id']=='board-newsroom')
    payload=('<rss><channel><item><title>'+escape(wire['title'])+'</title><link>'+primary['url']+'</link><description>'+escape(wire['summary'])+'</description><pubDate>'+format_datetime(datetime.fromisoformat(wire['published_at']))+'</pubDate></item></channel></rss>').encode()
    policy=[];latencies=[]
    (ROOT/'work').mkdir(exist_ok=True)
    for name,cutoff in [('fresh_before_open','2026-11-08T20:00:30Z'),('one_minute_after_open','2026-11-09T14:31:00Z'),('after_first_close','2026-11-09T21:01:00Z'),('old_news_received_now','2026-11-16T16:00:00Z')]:
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            report=run(Path(tmp)/'journal','nvidia_news',client=lambda u,h:(200,payload,{}),clock=lambda:cutoff)
            card=report['analysis']['cards'][0]
            policy.append(dict(scenario=name,as_of=cutoff,action=card['action'],freshness=card['freshness'],market=report['analysis']['market']['state'],
                historical_cases=len(card['historical_cross_check']['matches']),qualified_cases=card['historical_cross_check']['qualified_count'],
                peer_evidence=card['peer_price_check']['status'],new_receipt_cards=report['new_receipt_cards'],external_alerts_sent=0))
            latencies.append(dict(scenario=name,**report['timings_ms']))
    protocol=dict(kind='controlled_transport_and_clock',source_publication=wire['published_at'],publication_source=wire['url'],story_source=primary['url'],
        payload_is_original_feed=False,scenarios=policy,minimum_poll_interval_seconds=60,
        interpretation='Real sourced release facts in reconstructed test transport. No actual historical receipt, delivery, continuous coverage or verified intraday opportunity claimed.')
    return dict(policy=protocol,measured_local_processing_ms=latencies)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path);args=p.parse_args()
    r=build_demo();serialized=json.dumps(r['policy'],sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(serialized).hexdigest()
    if args.check and Path(__file__).with_name('DEMO.sha256').read_text().strip()!=digest:raise SystemExit('Pilot policy demonstration changed; review before updating digest')
    if args.output:
        output=args.output.resolve()
        if not output.is_relative_to((ROOT/'work').resolve()) or output.exists():raise SystemExit('New work/ output file required')
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))


if __name__=='__main__':main()
