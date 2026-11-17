"""Local append-only research timestamps; no backdating and no account operations."""
import json,sqlite3
from pathlib import Path
from event_history.library import ROOT,require
from world_events.events import digest,canonical
from news_pilot.ingest import utc,at


def connect(directory):
    path=Path(directory).resolve()
    require(path.is_relative_to((ROOT/'work').resolve()) and path!=(ROOT/'work').resolve(),'Dedicated work/ learning journal required')
    path.mkdir(parents=True,exist_ok=True)
    target=path/'predictions.sqlite'
    require(not target.is_symlink(),'Symlink journal refused')
    db=sqlite3.connect(target,timeout=15);db.row_factory=sqlite3.Row
    try:
        app=db.execute('PRAGMA application_id').fetchone()[0];version=db.execute('PRAGMA user_version').fetchone()[0]
        if app==0 and version==0:
            require(not db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0],'Unrelated database refused')
            schema="""BEGIN IMMEDIATE;
              CREATE TABLE models(id TEXT PRIMARY KEY,payload TEXT NOT NULL);
              CREATE TABLE predictions(id TEXT PRIMARY KEY,recorded_at TEXT NOT NULL,payload TEXT NOT NULL);
              CREATE TABLE settlements(id TEXT PRIMARY KEY,prediction_id TEXT NOT NULL REFERENCES predictions(id),recorded_at TEXT NOT NULL,payload TEXT NOT NULL);
              PRAGMA application_id=44001; PRAGMA user_version=4401;
            """
            for table in ('models','predictions','settlements'):
                for op in ('UPDATE','DELETE'):
                    schema+=f"CREATE TRIGGER immutable_{table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'Immutable research journal'); END;"
            db.executescript(schema+'COMMIT;')
        else:require(app==44001 and version==4401,'Unsupported or unrelated learning journal')
        require(db.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'immutable_%'").fetchone()[0]==6,
                'Immutable journal guards missing')
        db.execute('PRAGMA foreign_keys=ON')
        return db
    except Exception:
        db.close();raise


def append(db,table,id,payload,when=None,prediction_id=None):
    require(table in ('models','predictions','settlements'),'Unknown journal table')
    encoded=canonical(payload)
    prior=db.execute(f'SELECT payload FROM {table} WHERE id=?',(id,)).fetchone()
    if prior:
        require(prior['payload']==encoded,'Immutable identity/payload mismatch')
        return False
    if table=='models':db.execute('INSERT INTO models VALUES(?,?)',(id,encoded))
    elif table=='predictions':db.execute('INSERT INTO predictions VALUES(?,?,?)',(id,when,encoded))
    else:db.execute('INSERT INTO settlements VALUES(?,?,?,?)',(id,prediction_id,when,encoded))
    return True


def record_predictions(directory,prepared,clock=utc):
    when=clock();at(when);db=connect(directory)
    inserted=0
    try:
        db.execute('BEGIN IMMEDIATE')
        for model in prepared['locked']['models'].values():
            require(model['model_sha256']==digest({k:v for k,v in model.items() if k!='model_sha256'}),'Model fingerprint mismatch')
            append(db,'models',model['model_sha256'],model)
        for p in prepared['predictions']:
            require(p['validated_action']=='No Action' and p['research_action'] in ('Watch','No Action') and p['probability'] is None,'Research-only prediction required')
            require(p['prediction_id']==digest({k:v for k,v in p.items() if k!='prediction_id'}),'Prediction fingerprint mismatch')
            inserted+=append(db,'predictions',p['prediction_id'],p,when)
        db.commit()
        return dict(predictions=len(prepared['predictions']),new_predictions=inserted,actual_recorded_at=when,
            timestamp_scope='Actual current research recording; historical decision bounds are simulated, not original predictions.')
    finally:db.close()


def record_settlements(directory,assessed,clock=utc):
    when=clock();at(when);db=connect(directory);inserted=0
    try:
        db.execute('BEGIN IMMEDIATE')
        for r in assessed['records']:
            pid=r['prediction']['prediction_id']
            require(db.execute('SELECT 1 FROM predictions WHERE id=?',(pid,)).fetchone(),'Prediction must be committed before assessment')
            payload=dict(prediction_id=pid,outcome=r['outcome'],scope='Retrospective current-vintage reference observation; no executed trade')
            inserted+=append(db,'settlements',digest(payload),payload,when,pid)
        db.commit()
        return dict(new_settlements=inserted,actual_recorded_at=when,
                    revisions='Changed later observations append a new settlement version; earlier predictions/outcomes never overwrite.')
    finally:db.close()
