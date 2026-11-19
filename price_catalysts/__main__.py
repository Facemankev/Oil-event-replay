"""Private price-first discovery. No raw data or report body echoed to public logs."""
import argparse
import json
from .data import load
from .detector import detect
from daily_prices.stooq import save_private


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['scan','study','render'])
    p.add_argument('--db',default='work/stooq-private/prices.sqlite')
    p.add_argument('--manifest',default='work/stooq-private/import-first.json')
    p.add_argument('--output',required=True)
    p.add_argument('--scan')
    p.add_argument('--study')
    p.add_argument('--previous-study')
    args=p.parse_args()
    from daily_prices.stooq import private_path
    if args.command=='render':
        from .view import render_private
        if not args.study:p.error('--study is required for render')
        report=json.loads(private_path(args.study).read_text())
        render_private(args.output,report)
        print(json.dumps(dict(status='private_HTML_only',predictions=0)));return
    selections=load(args.db,args.manifest)
    if args.command=='study':
        from .ledger import build
        if not args.scan:p.error('--scan is required for study')
        scan=json.loads(private_path(args.scan).read_text())
        previous=json.loads(private_path(args.previous_study).read_text()) if args.previous_study else None
        report=build(scan,selections,prior_study=previous)
    else:report=detect(selections)
    save_private(args.output,report)
    print(json.dumps(dict(status='private_exploratory_only',rows=report['source_rows'],predictions=0)))


if __name__=='__main__':main()
