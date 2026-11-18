"""Append-only daily captures and revisions, isolated from every parent database."""
import json,sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path
from event_history.library import ROOT,require
from world_events.events import digest
from .model import validate_rows,FIELDS

MARKER='DATA-3 daily source captures v1'
TABLES={'identity','captures','observations','receipts','locks','settlements'}


def connect(path):
    p=Path(path).resolve();require(p.is_relative_to((ROOT/'work').resolve()),'Dedicated work/ database required; original prices are protected')
    if p.exists():
        with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as old:
            tables={r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            require(tables==TABLES and old.execute('SELECT marker FROM identity').fetchall()==[(MARKER,)],'Unrelated database refused before any mutation')
    else:p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(p);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS identity(marker TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS captures(id TEXT PRIMARY KEY,source TEXT NOT NULL,instrument TEXT NOT NULL,retrieved TEXT NOT NULL,payload TEXT NOT NULL,raw BLOB);
      CREATE TABLE IF NOT EXISTS observations(capture_id TEXT NOT NULL REFERENCES captures(id),day TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(capture_id,day));
      CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,source TEXT NOT NULL,observed TEXT NOT NULL,payload TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS locks(id TEXT PRIMARY KEY,recorded TEXT NOT NULL,payload TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS settlements(id TEXT PRIMARY KEY,lock_id TEXT NOT NULL REFERENCES locks(id),recorded TEXT NOT NULL,payload TEXT NOT NULL);
    ''')
    db.execute('INSERT OR IGNORE INTO identity VALUES(?)',(MARKER,))
    for table in TABLES:
        for action in ('UPDATE','DELETE'):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Append only: preserve original evidence'); END")
    db.commit();return db


def import_capture(db,capture,rows,raw=None):
    if not capture['synthetic_control']:
        from .parsers import parse
        require(isinstance(raw,bytes),'Real capture requires exact original payload bytes')
        require(parse(raw,capture)==rows,'Rows differ from original source; no edited history')
    validate_rows(rows,capture);cid=digest({k:v for k,v in capture.items() if k!='retrieved_at'});before=db.total_changes
    old_count=db.execute('SELECT count(*) FROM observations').fetchone()[0]
    with db:
        existing=db.execute('SELECT day,payload FROM observations WHERE capture_id=? ORDER BY day',(cid,)).fetchall()
        if existing:require([json.loads(r['payload']) for r in existing]==rows,'Changed rows under an identical capture; no overwrite')
        db.execute('INSERT OR IGNORE INTO captures VALUES(?,?,?,?,?,?)',(cid,capture['source_id'],capture['instrument'],capture['retrieved_at'],json.dumps(capture,sort_keys=True),raw))
        for r in rows:db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?)',(cid,r['date'],r['status'],json.dumps(r,sort_keys=True)))
    return dict(capture_id=cid,inserted_rows=db.total_changes-before,observations=len(rows),inserted_observations=db.execute('SELECT count(*) FROM observations').fetchone()[0]-old_count)


def record_receipt(db,r):
    rid=digest(r)
    with db:db.execute('INSERT OR IGNORE INTO receipts VALUES(?,?,?,?)',(rid,r['source_id'],r['observed_at'],json.dumps(r,sort_keys=True)))
    return rid


def capture(db,cid):
    r=db.execute('SELECT payload FROM captures WHERE id=?',(cid,)).fetchone();require(r is not None,'Unknown capture')
    return json.loads(r['payload'])


def query(db,cid,start,end,basis='raw'):
    date.fromisoformat(start);date.fromisoformat(end);require(start<=end and basis in ('raw','provider_adjusted'),'Invalid range/price basis')
    c=capture(db,cid)
    rows=[json.loads(r[0]) for r in db.execute('SELECT payload FROM observations WHERE capture_id=? AND day>=? AND day<=? ORDER BY day',(cid,start,end))]
    if basis=='provider_adjusted':require(all(r['status']!='numeric' or r['adjusted_close'] is not None for r in rows),'Adjusted quote absent; never infer factors')
    return dict(capture=c,rows=rows,basis=basis,original_vintage_verified=False,executable=False)


def conflicts(db):
    groups={}
    for r in db.execute('SELECT c.instrument,o.day,o.payload FROM observations o JOIN captures c ON c.id=o.capture_id ORDER BY c.instrument,o.day'):
        p=json.loads(r['payload']);key=(r['instrument'],r['day']);groups.setdefault(key,set()).add(tuple((k,None if p.get(k) is None else Decimal(p[k])) for k in FIELDS)+(('status',p['status']),))
    return [dict(instrument=k[0],date=k[1],different_values=len(v)) for k,v in groups.items() if len(v)>1]


def select_captures(db,ids):
    # Explicit non-overlapping raw snapshots may grow a history. Adjusted
    # histories need one source vintage; no implicit latest/provider splice.
    require(len(ids)==len(set(ids)),'Repeated capture selection')
    groups={}
    for cid in ids:
        c=capture(db,cid);series=query(db,cid,'1900-01-01','2100-12-31')
        groups.setdefault(c['instrument'],[]).append((cid,series))
    out={}
    for market,parts in groups.items():
        first=parts[0][1]['capture'];by_day={}
        if len(parts)>1:
            require(first['price_basis']=='unadjusted_close_actions_unknown','Cannot splice unknown provider adjustment vintages')
        for cid,s in parts:
            c=s['capture']
            require(c['synthetic_control']==first['synthetic_control'],'Real and synthetic captures cannot share an assembled history')
            require(all(c[k]==first[k] for k in ('source_id','symbol','venue','currency','unit','price_basis','asset_kind')),'Mixed identity/provider/currency/price basis')
            for row in s['rows']:
                previous=by_day.get(row['date'])
                if previous:
                    require(previous['status']==row['status'] and all((Decimal(previous[k]) if previous[k] is not None else None)==(Decimal(row[k]) if row[k] is not None else None) for k in FIELDS),'Overlapping source revision needs review; no latest overwrite')
                else:by_day[row['date']]={**row,'component_capture_id':cid}
        out[market]=dict(capture=first,rows=[by_day[d] for d in sorted(by_day)],component_capture_ids=[cid for cid,s in parts],
          assembled_through=max(s['capture']['retrieved_at'] for cid,s in parts))
    return out
