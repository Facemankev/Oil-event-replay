"""Owner-private SIGNAL-1 reports. No report body or prices printed to CI logs."""
import argparse
import json
from datetime import date
from pathlib import Path
from daily_prices.stooq import private_path, save_private
from price_catalysts.data import load
from .engine import build


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['analyse', 'render'])
    p.add_argument('--scan', default='work/evt3/scan-v2.json')
    p.add_argument('--ledger', default='work/evt3/study-paired.json')
    p.add_argument('--db', default='work/stooq-private/prices.sqlite')
    p.add_argument('--manifest', default='work/stooq-private/import-first.json')
    p.add_argument('--as-of', default=date.today().isoformat())
    p.add_argument('--report')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    if args.command == 'render':
        from .view import render_private
        if not args.report:
            p.error('--report is required for render')
        render_private(args.output, json.loads(private_path(args.report).read_text()))
    else:
        date.fromisoformat(args.as_of)
        report = build(json.loads(private_path(args.scan).read_text()), load(args.db, args.manifest),
                       json.loads(private_path(args.ledger).read_text()), args.as_of)
        save_private(args.output, report)
    print(json.dumps(dict(status='private_historical_research_only',current_signals=0,orders=0)))


if __name__ == '__main__':
    main()
