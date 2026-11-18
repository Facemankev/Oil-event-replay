"""Dedicated append-only SQLite reference store, versioned by exact capture content."""
import json,sqlite3
from decimal import Decimal
from datetime import date
from pathlib import Path
from event_history.library import ROOT,require
from world_events.events import digest
from .library import validate,period_bounds

MARKER='DATA-2 reference evidence v1'
TABLES=('sources','averages','ipo_facts')


def connect(path):
    path=Path(path).resolve();require(path.is_relative_to((ROOT/'work').resolve()),'Use a dedicated database under work/; historical stores are protected')
    if path.exists():
        # Inspect read-only before executing any schema/PRAGMA on another database.
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as old:
            tables={r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            require(tables=={'identity',*TABLES},'Not a DATA-2 database; refusing all changes')
            require(old.execute('SELECT marker FROM identity').fetchall()==[(MARKER,)],'Wrong database identity')
    else:path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS identity(marker TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS sources(version TEXT PRIMARY KEY,id TEXT NOT NULL,document_day TEXT NOT NULL,payload TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS averages(id TEXT PRIMARY KEY,source_version TEXT NOT NULL REFERENCES sources(version),instrument TEXT NOT NULL,frequency TEXT NOT NULL,period TEXT NOT NULL,start_day TEXT NOT NULL,end_day TEXT NOT NULL,value TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(source_version,instrument,frequency,period));
      CREATE TABLE IF NOT EXISTS ipo_facts(version TEXT PRIMARY KEY,episode_id TEXT NOT NULL,event_day TEXT NOT NULL,payload TEXT NOT NULL);
      CREATE INDEX IF NOT EXISTS average_range ON averages(instrument,frequency,start_day,end_day);
    ''')
    db.execute('INSERT OR IGNORE INTO identity VALUES(?)',(MARKER,))
    for table in ('identity',*TABLES):
        for action in ('UPDATE','DELETE'):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS no_{action.lower()}_{table} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Append only; preserve original evidence'); END")
    db.commit();return db


def import_bundle(db,bundle):
    validate(bundle);before=db.total_changes
    with db:
        versions={}
        for sid,s in bundle['sources'].items():
            version=digest(s);versions[sid]=version
            db.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?,?)',(version,sid,max(s['document_day'],s['web_publication_day']),json.dumps(s,sort_keys=True)))
        for r in bundle['averages']:
            version=versions[r['source_id']];start,end=period_bounds(r['period'],r['frequency'])
            rowid=digest([version,r]);prior=db.execute('SELECT id FROM averages WHERE source_version=? AND instrument=? AND frequency=? AND period=?',(version,r['instrument'],r['frequency'],r['period'])).fetchone()
            # A changed transcription must be a reviewed new capture/source version.
            require(prior is None or prior['id']==rowid,'Changed cell under identical source version; retain old and declare new capture metadata')
            db.execute('INSERT OR IGNORE INTO averages VALUES(?,?,?,?,?,?,?,?,?)',(rowid,version,r['instrument'],r['frequency'],r['period'],start,end,r['value'],json.dumps(r,sort_keys=True)))
        for c in bundle['ipos']:
            db.execute('INSERT OR IGNORE INTO ipo_facts VALUES(?,?,?,?)',(digest(c),c['episode_id'],c['event_day'],json.dumps(c,sort_keys=True)))
    return dict(inserted_rows=db.total_changes-before,**counts(db))


def counts(db):
    return dict(source_versions=db.execute('SELECT count(*) FROM sources').fetchone()[0],
      publication_values=db.execute('SELECT count(*) FROM averages').fetchone()[0],
      distinct_asset_periods=db.execute('SELECT count(*) FROM (SELECT DISTINCT instrument,frequency,period FROM averages)').fetchone()[0],
      ipo_versions=db.execute('SELECT count(*) FROM ipo_facts').fetchone()[0],
      distinct_ipo_episodes=db.execute('SELECT count(DISTINCT episode_id) FROM ipo_facts').fetchone()[0])


def query(db,instrument,frequency,start,end,as_of=None,require_original_vintage=False):
    require(frequency in ('annual','quarterly','monthly'),'Explicit period frequency required; never query this as daily prices')
    date.fromisoformat(start);date.fromisoformat(end);require(start<=end,'Reversed date range')
    if as_of:date.fromisoformat(as_of)
    # This capture has NO verified original-vintage availability. Historical
    # document dates can filter references but cannot establish a backtest clock.
    if require_original_vintage:return []
    records=db.execute('''SELECT a.*,s.payload AS source,s.document_day FROM averages a
      JOIN sources s ON s.version=a.source_version WHERE a.instrument=? AND a.frequency=?
      AND a.start_day<=? AND a.end_day>=? ORDER BY a.start_day,s.document_day,a.source_version''',(instrument,frequency,end,start))
    return [dict(observation=json.loads(r['payload']),source=json.loads(r['source']),
                 point_in_time_verified=False) for r in records if as_of is None or r['document_day']<=as_of]


def revisions(db):
    groups={}
    for r in db.execute('SELECT instrument,frequency,period,value FROM averages ORDER BY instrument,frequency,period'):
        groups.setdefault((r['instrument'],r['frequency'],r['period']),[]).append(Decimal(r['value']))
    return [dict(instrument=k[0],frequency=k[1],period=k[2],editions=len(v),different_values=len(set(v)))
            for k,v in groups.items() if len(set(v))>1]


def read_bundle(db):
    # Multiple versions remain queryable; do not silently choose a correction for
    # a reproducible evaluation. Review/version-select first in a later change.
    require(not db.execute('SELECT id FROM sources GROUP BY id HAVING count(*)>1').fetchall(),
            'Multiple source captures require explicit review; no automatic latest overwrite')
    require(not db.execute('SELECT episode_id FROM ipo_facts GROUP BY episode_id HAVING count(*)>1').fetchall(),
            'Multiple IPO versions require explicit review')
    sources=[json.loads(r[0]) for r in db.execute('SELECT payload FROM sources ORDER BY id')]
    return validate(dict(schema_version=1,sources={s['id']:s for s in sources},
      averages=[json.loads(r[0]) for r in db.execute('SELECT payload FROM averages ORDER BY instrument,period,source_version')],
      ipos=[json.loads(r[0]) for r in db.execute('SELECT payload FROM ipo_facts ORDER BY event_day,episode_id')]))
