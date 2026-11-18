"""Reproduce typed references, query ranges and audit unchanged frozen evaluations."""
import argparse,json
from event_history.__main__ import new_output
from .library import HERE,load_bundle
from .database import connect,import_bundle,query,revisions,read_bundle
from .evaluate import build_report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',default='work/data2-published/references.sqlite')
    sub=p.add_subparsers(dest='command',required=True);sub.add_parser('import')
    q=sub.add_parser('query');q.add_argument('--instrument',required=True);q.add_argument('--frequency',required=True,choices=['annual','quarterly','monthly'])
    q.add_argument('--from-date',required=True);q.add_argument('--through-date',required=True);q.add_argument('--as-of');q.add_argument('--original-vintage-only',action='store_true')
    sub.add_parser('revisions')
    e=sub.add_parser('evaluate');e.add_argument('--check',action='store_true');e.add_argument('--output')
    a=p.parse_args()
    if a.command=='evaluate':
        db=connect(a.db)
        try:r=build_report(read_bundle(db))
        finally:db.close()
        if a.check and r!=json.loads((HERE/'report.json').read_text()):p.exit(1,'DATA-2 results changed; review before updating the report.\n')
        if a.output:new_output(a.output,r)
        print(json.dumps(dict(imported=r['imported'],comparison=r['comparison'],after=r['after']),indent=2));return
    db=connect(a.db)
    try:
        if a.command=='import':r=import_bundle(db,load_bundle())
        elif a.command=='revisions':r=revisions(db)
        else:r=query(db,a.instrument,a.frequency,a.from_date,a.through_date,a.as_of,a.original_vintage_only)
        print(json.dumps(r,indent=2))
    finally:db.close()

if __name__=='__main__':main()
