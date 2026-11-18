"""Import reviewed daily files, query exact captures and compare separate evaluation lanes."""
import argparse,json
from pathlib import Path
from event_history.library import require
from event_history.__main__ import new_output
from news_pilot.ingest import utc
from .database import connect,import_capture,query,conflicts,select_captures
from .ingest import make_capture,poll,providers
from .parsers import parse
from .evaluate import build_report,HERE


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',default='work/data3/daily.sqlite')
    sub=p.add_subparsers(dest='command',required=True)
    i=sub.add_parser('import-file');i.add_argument('--source',required=True,choices=list(providers()));i.add_argument('--file',required=True);i.add_argument('--url',required=True);i.add_argument('--identity',required=True)
    f=sub.add_parser('fetch');f.add_argument('--source',required=True,choices=list(providers()));f.add_argument('--url');f.add_argument('--identity',required=True)
    q=sub.add_parser('query');q.add_argument('--capture',required=True);q.add_argument('--from-date',required=True);q.add_argument('--through-date',required=True);q.add_argument('--basis',choices=['raw','provider_adjusted'],default='raw')
    sub.add_parser('conflicts')
    a=sub.add_parser('access');a.add_argument('--environment',default='runtime',choices=['runtime','github_actions']);a.add_argument('--output',required=True)
    e=sub.add_parser('evaluate');e.add_argument('--capture',action='append',default=[]);e.add_argument('--check',action='store_true');e.add_argument('--output')
    l=sub.add_parser('lock');l.add_argument('--event',required=True);l.add_argument('--features',required=True);l.add_argument('--model',required=True);l.add_argument('--capture',action='append',default=[])
    t=sub.add_parser('settle');t.add_argument('--lock',required=True);t.add_argument('--capture',action='append',required=True)
    args=p.parse_args();db=connect(args.db)
    try:
        if args.command=='import-file':
            identity=json.loads(Path(args.identity).read_text());raw=Path(args.file).read_bytes()
            # Actual local receipt time, not a guessed historical publication time.
            c=make_capture(args.source,args.url,raw,identity,utc());c['capture_method']='owner_supplied_source_export_not_origin_HTTP_receipt'
            r=import_capture(db,c,parse(raw,c),raw)
        elif args.command=='fetch':r=poll(db,args.source,json.loads(Path(args.identity).read_text()),import_data=True,request_url=args.url)
        elif args.command=='query':r=query(db,args.capture,args.from_date,args.through_date,args.basis)
        elif args.command=='conflicts':r=conflicts(db)
        elif args.command=='lock':
            from .prospective import lock
            load=lambda path:json.loads(Path(path).read_text())
            r=lock(db,load(args.event),load(args.features),load(args.model),args.capture)
        elif args.command=='settle':
            from .prospective import settle
            r=settle(db,args.lock,args.capture)
        elif args.command=='access':
            r=dict(environment=args.environment,receipts=[poll(db,sid) for sid in providers()],imported_rows=0,
              note='Direct fixed anonymous source requests; no data import, bodies saved, proxy, credentials or retry. HTTP access is not permission or a working numeric series.')
            new_output(args.output,r)
        else:
            from .prospective import summary
            r=build_report(select_captures(db,args.capture),summary(db))
            if args.check:require(r==json.loads((HERE/'report.json').read_text()),'DATA-3 results changed; review without repinning old tests')
            if args.output:new_output(args.output,r)
        print(json.dumps(r,indent=2,ensure_ascii=False))
        if args.command=='fetch' and r['status']!='validated_daily_reference':p.exit(1,'No usable daily series imported; inspect the recorded source/access/format status.\n')
    finally:db.close()

if __name__=='__main__':main()
