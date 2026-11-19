"""Private price-first discovery. No raw data or report body echoed to public logs."""
import argparse
import json
from .data import load
from .detector import detect
from daily_prices.stooq import save_private


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['scan'])
    p.add_argument('--db',default='work/stooq-private/prices.sqlite')
    p.add_argument('--manifest',default='work/stooq-private/import-first.json')
    p.add_argument('--output',required=True)
    args=p.parse_args()
    report=detect(load(args.db,args.manifest));save_private(args.output,report)
    print(json.dumps(dict(status='private_discovery_only',rows=report['source_rows'],focus=len(report['focus']),predictions=0)))


if __name__=='__main__':main()
