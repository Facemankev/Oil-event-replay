"""Chronological research reproduction and optional immutable local audit."""
import argparse,json
from event_history.__main__ import new_output
from free_pilot.data import load_free_library
from world_events.events import digest
from .engine import prepare,assess,assemble,HERE
from .journal import record_predictions,record_settlements


def run(data,directory=None,clock=None,assessor=assess):
    p=prepare(data)
    journal={}
    if directory:
        journal['predictions']=record_predictions(directory,p,**({'clock':clock} if clock else {}))
    # The committed prediction transaction finishes before this first test-outcome read.
    assessed=assessor(p,data)
    if directory:
        journal['settlements']=record_settlements(directory,assessed,**({'clock':clock} if clock else {}))
    return assemble(p,assessed),journal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--output');p.add_argument('--journal')
    a=p.parse_args();r,journal=run(load_free_library(),a.journal)
    if a.check and (HERE/'REPORT.sha256').read_text().strip()!=digest(r):
        p.exit(1,'Learning report changed; review before repinning.\n')
    if a.output:new_output(a.output,r)
    print(json.dumps(dict(summary=r['summary'],journal=journal,digest=digest(r)),indent=2))

if __name__=='__main__':main()
