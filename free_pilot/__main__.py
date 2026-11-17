"""Zero-charge source checks and a bounded observation-only Market Ripple demo."""
import argparse
import json
from pathlib import Path

from event_history.__main__ import new_output
from event_history.database import connect, import_library
from world_events.events import digest
from .data import HERE, load_free_library, coverage
from .pipeline import CASES, build_demo, run_case
from .providers import SOURCES, poll
from event_history.library import ROOT, require
from verification.sources import csv_bytes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('import'); p.add_argument('--db', default='work/free-pilot/history.sqlite')
    commands.add_parser('coverage')
    p = commands.add_parser('probe'); p.add_argument('--source', choices=SOURCES, required=True)
    p.add_argument('--journal', default='work/free-pilot/probes'); p.add_argument('--output')
    p = commands.add_parser('run'); p.add_argument('--case', choices=CASES, required=True)
    p.add_argument('--fetch-event', action='store_true')
    p.add_argument('--journal', default='work/free-pilot/session'); p.add_argument('--output', required=True)
    p = commands.add_parser('demo'); p.add_argument('--check', action='store_true'); p.add_argument('--output')
    p = commands.add_parser('capture')
    p.add_argument('--source', choices=['fed_eurusd','fed_usdjpy','eia_brent','eia_wti'], required=True)
    p.add_argument('--output-directory', required=True)
    p.add_argument('--journal', default='work/free-pilot/probes')
    args = parser.parse_args(argv)
    try:
        if args.command == 'import':
            data = load_free_library(); db = connect(args.db)
            try:
                result = import_library(db, data)
            finally:
                db.close()
        elif args.command == 'coverage':
            result = coverage(load_free_library())
        elif args.command == 'probe':
            r = poll(args.journal, args.source)
            parsed = r.pop('normalized', None)
            result = dict(r, parsed_metadata={k:v for k,v in parsed.items() if k not in ('data','rows')} if parsed else None)
            if args.output:
                new_output(args.output, result)
        elif args.command == 'capture':
            output = Path(args.output_directory).resolve()
            require(output.is_relative_to((ROOT/'work').resolve()) and not output.exists(), 'New work/ capture directory required')
            r = poll(args.journal, args.source)
            parsed = r.pop('normalized', None)
            require(parsed is not None and parsed.get('public_research_usable') and parsed.get('rows'), 'Primary source unavailable; no capture written')
            output.mkdir(parents=True)
            raw = csv_bytes(parsed.pop('rows'))
            (output/'observations.csv').write_bytes(raw)
            result = dict(r, parsed_metadata=parsed, canonical_records_changed=0,
                          note='New bounded snapshot only; review revisions before any canonical import.')
            (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
        elif args.command == 'run':
            r = run_case(args.case, args.journal, args.fetch_event)
            new_output(args.output, r)
            result = {k:r.get(k) for k in ('status','cost_GBP','orders','account_mutations','local_processing_ms')}
            result['output'] = args.output
            result['action'] = r.get('result', {}).get('action', 'No Action')
        else:
            result = build_demo()
            if args.check and (HERE/'DEMO.sha256').read_text().strip() != digest(result):
                raise ValueError('Demonstration changed; review differences before repinning')
            if args.output:
                new_output(args.output, result)
            result = dict(cases=len(result['cases']), coverage=result['coverage'],
                          supported_entries=0, cost_GBP='0.00', digest=digest(result))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    except Exception:
        parser.exit(1, 'Free pilot failed safely; source/output validation required. No order, charge or credential operation.\n')


if __name__ == '__main__':
    main()
