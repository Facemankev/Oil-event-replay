"""Build/query the HIST-1 SQLite library and reproduce its read-only evidence export."""
import argparse
import json
from pathlib import Path

from world_events.events import digest, ValidationError
from .library import ROOT, HERE, load_library, require
from .database import connect, import_library, read_library
from .engine import evaluate, drilldown, historical_decision, match_history


def new_output(path, value):
    target = Path(path).resolve()
    require(target.is_relative_to((ROOT / 'work').resolve()) and not target.exists(),
            'Use a new output file under work/; existing evidence is never overwritten')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def summary(report):
    return {key: report[key] for key in
            ('schema_version', 'as_of', 'event_count', 'visible_events', 'sampling', 'coverage', 'decisions_summary', 'point_in_time_safe', 'limitations')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='work/hist1/library.sqlite')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('import')
    p = sub.add_parser('list')
    p.add_argument('--group')
    p.add_argument('--from-date')
    p.add_argument('--through-date')
    p = sub.add_parser('show')
    p.add_argument('--event', required=True)
    p.add_argument('--as-of', default='2026-11-17T23:59:59Z')
    p = sub.add_parser('match')
    p.add_argument('--event', required=True)
    p.add_argument('--instrument', required=True)
    p.add_argument('--as-of', required=True)
    p = sub.add_parser('evaluate')
    p.add_argument('--as-of', default='2026-11-17T23:59:59Z')
    p.add_argument('--output')
    p.add_argument('--check', action='store_true')
    p = sub.add_parser('export')
    p.add_argument('--as-of', default='2026-11-17T23:59:59Z')
    p.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'import':
            data = load_library()
            db = connect(args.db)
            try:
                result = import_library(db, data)
            finally:
                db.close()
        else:
            data = read_library(args.db)
            if args.command == 'list':
                from .library import GROUPS
                from .engine import day
                require(not args.group or args.group in GROUPS, 'Unknown market group')
                for date in (args.from_date, args.through_date):
                    if date:
                        day(date)
                require(not args.from_date or not args.through_date or args.from_date <= args.through_date,
                        'Date range reversed')
                result = [{k: e.get(k) for k in ('id', 'title', 'primary_group', 'public_day', 'episode_id')}
                          for e in data['events'] if (not args.group or e['primary_group'] == args.group)
                          and (not args.from_date or e.get('public_day') and e['public_day'] >= args.from_date)
                          and (not args.through_date or e.get('public_day') and e['public_day'] <= args.through_date)]
            elif args.command in ('evaluate', 'export'):
                report = evaluate(data, args.as_of)
                if args.command == 'export':
                    new_output(args.output, report)
                    result = dict(contract=report['contract'], events=report['visible_events'], output=args.output)
                else:
                    if args.check:
                        require((HERE / 'RESULTS.sha256').read_text().strip() == digest(report),
                                'History findings changed; review differences before updating the digest')
                    if args.output:
                        new_output(args.output, report)
                    result = summary(report)
            else:
                event = next((e for e in data['events'] if e['id'] == args.event), None)
                require(event is not None, 'Unknown historical event')
                if args.command == 'show':
                    result = drilldown(event, data, args.as_of)
                else:
                    result = dict(decision=historical_decision(event, data, args.instrument, args.as_of),
                                  comparisons=match_history(event, data, args.instrument, args.as_of))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ValidationError) as exc:
        parser.exit(1, 'Historical research failed validation: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
