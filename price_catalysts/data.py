"""Read only the six explicitly identified private captures; no implicit latest."""
import hashlib
import json
import sqlite3
from pathlib import Path

from daily_prices.database import MARKER,query
from daily_prices.stooq import ASSETS,private_path
from event_history.library import require


def load(db_path,manifest_path):
    p=private_path(db_path);manifest=json.loads(Path(manifest_path).read_text())
    selections={}
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        require(db.execute('SELECT marker FROM identity').fetchall()[0][0]==MARKER,'Wrong private database')
        for entry in manifest['imports']:
            s=query(db,entry['capture_id'],'1900-01-01','2100-12-31');c=s['capture']
            require(c['source_id']=='stooq_owner_csv' and c['usage_scope']=='private_research'
                    and c['canonical_prices_approved'] is False,'Only quarantined owner files, never approved feeds')
            raw=db.execute('SELECT raw FROM captures WHERE id=?',(entry['capture_id'],)).fetchone()[0]
            require(hashlib.sha256(raw).hexdigest()==c['payload_sha256'],'Original byte fingerprint changed')
            require(c['instrument'] not in selections,'Explicit duplicate/revision needs review')
            selections[c['instrument']]=dict(capture=c,rows=s['rows'],capture_id=entry['capture_id'])
    require(set(selections)==set(ASSETS),'Six exact securities required')
    return selections
