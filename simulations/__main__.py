"""Reproduce all retrospective hypotheses offline; never overwrite reports."""
import argparse,json
from event_history.__main__ import new_output
from world_events.events import digest
from .engine import build_report,HERE


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--output')
    a=p.parse_args();r=build_report()
    if a.check and (HERE/'REPORT.sha256').read_text().strip()!=digest(r):
        p.exit(1,'Simulation report changed; review before repinning.\n')
    if a.output:new_output(a.output,r)
    print(json.dumps(dict(events=r['universe_events'],event_market_cases=r['event_market_cases'],
        diagnosis=r['diagnosis']['blocker_counts'],default=next(s for s in r['rule_summaries'] if s['rule']=='event_long' and s['horizon']==5 and s['cost']=='declared'),
        supported_entries=0,digest=digest(r)),indent=2))

if __name__=='__main__':main()
