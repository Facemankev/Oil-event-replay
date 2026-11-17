"""Separate append-only SQLite store; canonical prices and event DBs are read-only inputs."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from world_events.events import digest, canonical
from .library import ROOT, require, validate_library

APPLICATION = 20261117
VERSION = 3801


def safe_path(value):
    path = Path(value).resolve()
    require(path.is_relative_to((ROOT / 'work').resolve()) and path.suffix == '.sqlite',
            'Use a dedicated .sqlite database under work/')
    return path


def connect(value):
    path = safe_path(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    version = db.execute('PRAGMA user_version').fetchone()[0]
    app = db.execute('PRAGMA application_id').fetchone()[0]
    if version == 0 and app == 0:
        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
            db.close()
            require(False, 'Unrelated database refused')
        db.executescript(f'''
          BEGIN IMMEDIATE;
          CREATE TABLE event_versions(id TEXT, revision INTEGER, sha256 TEXT NOT NULL,
            payload TEXT NOT NULL, imported_at TEXT NOT NULL, PRIMARY KEY(id,revision));
          CREATE TABLE evidence(sha256 TEXT PRIMARY KEY, payload TEXT NOT NULL);
          CREATE TABLE observations(instrument TEXT, date TEXT, snapshot_id TEXT,
            payload TEXT NOT NULL, PRIMARY KEY(instrument,date,snapshot_id));
          CREATE TABLE datasets(sha256 TEXT PRIMARY KEY, metadata TEXT NOT NULL);
          CREATE TABLE import_runs(id INTEGER PRIMARY KEY, imported_at TEXT NOT NULL,
            dataset_sha256 TEXT NOT NULL, inserted_events INTEGER, reused_events INTEGER);
          PRAGMA application_id={APPLICATION}; PRAGMA user_version={VERSION};
          COMMIT;
        ''')
    elif version != VERSION or app != APPLICATION:
        db.close()
        require(False, 'This is not a HIST-1 database')
    return db


def import_library(db, data):
    validate_library(data)
    inserted = reused = inserted_prices = 0
    fingerprint = digest(data)
    when = datetime.now(timezone.utc).isoformat()
    metadata = {k: v for k, v in data.items() if k not in ('events', 'observations')}
    metadata['_event_revisions'] = [[e['id'], e['revision']] for e in data['events']]
    metadata['_observation_snapshots'] = sorted({p['snapshot_id'] for p in data['observations']})
    metadata['_instrument_order'] = list(dict.fromkeys(p['instrument'] for p in data['observations']))
    db.execute('BEGIN IMMEDIATE')
    try:
        for event in data['events']:
            previous = db.execute('SELECT sha256 FROM event_versions WHERE id=? AND revision=?',
                                  (event['id'], event['revision'])).fetchone()
            sha = digest(event)
            if previous:
                require(previous[0] == sha, 'Existing event revision is immutable; review and increment a correction')
                reused += 1
            else:
                maximum = db.execute('SELECT max(revision) FROM event_versions WHERE id=?', (event['id'],)).fetchone()[0] or 0
                require(event['revision'] == maximum + 1, 'Event versions must advance sequentially')
                db.execute('INSERT INTO event_versions VALUES(?,?,?,?,?)',
                           (event['id'], event['revision'], sha, canonical(event), when))
                inserted += 1
        for source in data['sources'].values():
            db.execute('INSERT OR IGNORE INTO evidence VALUES(?,?)', (digest(source), canonical(source)))
        for row in data['observations']:
            key = (row['instrument'], row['date'], row['snapshot_id'])
            old = db.execute('SELECT payload FROM observations WHERE instrument=? AND date=? AND snapshot_id=?', key).fetchone()
            payload = canonical(row)
            require(old is None or old[0] == payload, 'A retained observation is immutable')
            if old is None:
                db.execute('INSERT INTO observations VALUES(?,?,?,?)', (*key, payload))
                inserted_prices += 1
        db.execute('INSERT OR IGNORE INTO datasets VALUES(?,?)', (fingerprint, canonical(metadata)))
        db.execute('INSERT INTO import_runs(imported_at,dataset_sha256,inserted_events,reused_events) VALUES(?,?,?,?)',
                   (when, fingerprint, inserted, reused))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return dict(dataset_sha256=fingerprint, inserted_events=inserted, reused_events=reused,
                inserted_observation_rows=inserted_prices, current_events=len(data['events']),
                numeric_observations=sum(p['status'] == 'numeric' for p in data['observations']))


def read_library(value, dataset=None):
    path = safe_path(value)
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        require(db.execute('PRAGMA application_id').fetchone()[0] == APPLICATION and
                db.execute('PRAGMA user_version').fetchone()[0] == VERSION, 'Unsupported database')
        if dataset is None:
            row = db.execute('SELECT dataset_sha256 FROM import_runs ORDER BY id DESC LIMIT 1').fetchone()
            require(row is not None, 'No imported dataset')
            dataset = row[0]
        row = db.execute('SELECT metadata FROM datasets WHERE sha256=?', (dataset,)).fetchone()
        require(row is not None, 'Dataset not imported')
        data = json.loads(row[0])
        # The dataset manifest pins exact event revisions and observation snapshots.
        entries = data.pop('_event_revisions', None)
        require(entries is not None, 'Dataset revision manifest missing')
        data['events'] = []
        for id, revision in entries:
            row = db.execute('SELECT payload FROM event_versions WHERE id=? AND revision=?', (id, revision)).fetchone()
            require(row is not None, 'Retained event missing')
            data['events'].append(json.loads(row[0]))
        snapshots = data.pop('_observation_snapshots')
        data['observations'] = [json.loads(r[0]) for r in db.execute('SELECT payload FROM observations ORDER BY instrument,date,snapshot_id')
                                if json.loads(r[0])['snapshot_id'] in snapshots]
        # Stable import order is fingerprinted; restore it from the manifest.
        order = data.pop('_instrument_order')
        data['observations'].sort(key=lambda p: (order.index(p['instrument']), p['date']))
        require(digest(data) == dataset, 'Stored dataset fingerprint mismatch')
        validate_library(data)
        return data
    finally:
        db.close()
