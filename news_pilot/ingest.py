"""One bounded poll with persistent receipt history, conditional HTTP and backoff."""
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from equities.collect import plain, timestamp, SafeError, ROOT
from .sources import SOURCES, MAX_BYTES


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def at(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.utcoffset() is None:
        raise SafeError('Explicit timezone required')
    return d.astimezone(timezone.utc)


def later(value, seconds):
    return (at(value) + timedelta(seconds=seconds)).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def location(value, source):
    u = urlsplit(value)
    if u.scheme != 'https' or u.username or u.password or u.port or u.query or u.fragment or not any(value.startswith(prefix) for prefix in [source['link_prefix'],*source.get('alternate_article_prefixes',[])]):
        raise SafeError('Unapproved public article location')
    return value


def parse(payload, source_id, receipt):
    source = SOURCES[source_id]
    if len(payload) > MAX_BYTES or b'\x00' in payload or b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise SafeError('Unsupported feed input')
    try:
        tree = ET.fromstring(payload)
    except ET.ParseError:
        raise SafeError('Malformed feed') from None
    ns = '{http://www.w3.org/2005/Atom}'
    atom = tree.tag == ns + 'feed'
    items = tree.findall(ns + 'entry') if atom else tree.findall('./channel/item') if tree.tag == 'rss' else None
    if items is None or len(items) > 100:
        raise SafeError('Feed structure or item count unsupported')
    result = []
    for item in items:
        value = lambda k: item.findtext((ns if atom else '') + k)
        if atom:
            links = [x.get('href') for x in item.findall(ns + 'link') if x.get('rel', 'alternate') == 'alternate']
            link = links[0] if links else ''
        else:
            link = value('link')
        url = location(link or '', source)
        # Missing original publication is NOT replaced by updated/receipt time.
        published = value('published') if atom else value('pubDate')
        updated = value('updated') if atom else None
        published = timestamp(published) if published else None
        updated = timestamp(updated) if updated else None
        if published and updated and at(updated) < at(published):
            raise SafeError('Update precedes publication')
        title = plain(value('title'), 500)
        full_body = plain((value('summary') or value('content')) if atom else value('description'), MAX_BYTES)
        body = full_body[:1200]
        if not title:
            raise SafeError('Missing feed title')
        digest = hashlib.sha256((title + '\n' + full_body).encode()).hexdigest()
        result.append(dict(url=url, title=title, summary=body, body_text=full_body, published_at=published,
                           updated_at=updated, first_seen_at=receipt, content_sha256=digest,
                           source_id=source_id, source_family=source['family'], company=source['company'],
                           source_kind=source['kind'], original_publication_verified=False))
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, headers):
    request = urllib.request.Request(url, headers={'User-Agent': 'MarketRipple-Research/1.0', **headers})
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            return response.status, response.read(MAX_BYTES + 1), dict(response.headers)
    except urllib.error.HTTPError as exc:
        # Discard error bodies and cookies; headers are whitelisted downstream.
        return exc.code, b'', dict(exc.headers)
    except urllib.error.URLError as exc:
        if '403' in str(exc.reason):
            return 403, b'', {'X-Pilot-Transport-Denial': 'true'}
        return 0, b'', {}


def open_journal(directory):
    path = Path(directory).resolve()
    if not path.is_relative_to((ROOT / 'work').resolve()) or path == (ROOT / 'work').resolve():
        raise SafeError('Pilot journal must be inside its own work/ directory')
    path.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path / 'receipts.sqlite', timeout=10)
    db.row_factory = sqlite3.Row
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version == 0:
        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
            db.close(); raise SafeError('Unrelated database refused')
        db.executescript('''CREATE TABLE state(source TEXT PRIMARY KEY,next_at TEXT NOT NULL,etag TEXT,modified TEXT);
        CREATE TABLE polls(id INTEGER PRIMARY KEY,source TEXT NOT NULL,started TEXT NOT NULL,received TEXT,
         status TEXT NOT NULL,http_status INTEGER,payload_sha256 TEXT,metrics_json TEXT);
        CREATE TABLE versions(id INTEGER PRIMARY KEY,source TEXT NOT NULL,url TEXT NOT NULL,content_sha256 TEXT NOT NULL,
         first_seen TEXT NOT NULL,article_json TEXT NOT NULL,UNIQUE(source,url,content_sha256));
        CREATE TABLE observations(poll_id INTEGER,version_id INTEGER,declared_publication TEXT,declared_update TEXT,
         UNIQUE(poll_id,version_id)); PRAGMA application_id=20261116; PRAGMA user_version=1;''')
    elif version != 1 or db.execute('PRAGMA application_id').fetchone()[0] != 20261116:
        db.close(); raise SafeError('Unsupported pilot journal')
    return path, db


def retry_seconds(value, receipt):
    if not value:
        return 60
    try:
        seconds = int(value) if value.isdigit() else (parsedate_to_datetime(value) - at(receipt)).total_seconds()
        return max(60, seconds)
    except (ValueError, TypeError, OverflowError):
        return 3600


def safe_header(headers, name):
    v = next((v for k,v in headers.items() if k.lower() == name.lower()), None)
    return v if isinstance(v, str) and len(v) <= 1000 and '\r' not in v and '\n' not in v else None


def poll(directory, source_id, client=fetch, clock=utc, timer=time.perf_counter):
    if source_id not in SOURCES:
        raise SafeError('Source not registered')
    source = SOURCES[source_id]; total_start = timer(); started = at(clock()).isoformat(timespec='microseconds').replace('+00:00','Z')
    path, db = open_journal(directory)
    try:
        db.execute('BEGIN IMMEDIATE')
        previous = db.execute('SELECT * FROM state WHERE source=?', (source_id,)).fetchone()
        if previous and at(started) < at(previous['next_at']):
            db.rollback()
            return dict(source_id=source_id,status='cooldown_no_request',next_attempt_at=previous['next_at'],
                        network_request=False,new_versions=0,continuous=False)
        db.execute('INSERT INTO state(source,next_at) VALUES(?,?) ON CONFLICT(source) DO UPDATE SET next_at=excluded.next_at',
                   (source_id,later(started,source['min_interval'])))
        poll_id = db.execute('INSERT INTO polls(source,started,status) VALUES(?,?,?)', (source_id,started,'request_started')).lastrowid
        db.commit()
        headers = {}
        if previous:
            if previous['etag']: headers['If-None-Match'] = previous['etag']
            if previous['modified']: headers['If-Modified-Since'] = previous['modified']
        request_start = timer()
        try:
            status,payload,response_headers = client(source['url'],headers)
        except Exception:
            status,payload,response_headers = 0,b'',{}
        receipt = at(clock()).isoformat(timespec='microseconds').replace('+00:00','Z'); http_end = timer(); normalized = []; payload_hash = None
        state = 'not_modified' if status == 304 else 'http_'+str(status)
        if at(receipt) < at(started):
            state = 'wall_clock_regressed'
        elif status == 200:
            try:
                normalized = parse(payload,source_id,receipt); state='ok'
                payload_hash=hashlib.sha256(payload).hexdigest()
                folder=path/'payloads'; folder.mkdir(exist_ok=True)
                target=folder/(payload_hash+'.xml')
                if not target.exists(): target.write_bytes(payload)
            except Exception:
                state='invalid_feed'; normalized=[]
        parse_end=timer(); new=0; metadata_changes=0
        db.execute('BEGIN IMMEDIATE')
        for article in normalized:
            old=db.execute('SELECT id,article_json FROM versions WHERE source=? AND url=? AND content_sha256=?',
                           (source_id,article['url'],article['content_sha256'])).fetchone()
            if old:
                vid=old['id']; saved=json.loads(old['article_json'])
                if saved.get('published_at')!=article['published_at'] or saved.get('updated_at')!=article['updated_at']:metadata_changes+=1
            else:
                vid=db.execute('INSERT INTO versions(source,url,content_sha256,first_seen,article_json) VALUES(?,?,?,?,?)',
                               (source_id,article['url'],article['content_sha256'],receipt,json.dumps(article,sort_keys=True))).lastrowid;new+=1
            db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?)', (poll_id,vid,article['published_at'],article['updated_at']))
        cooldown=source['min_interval']
        if status in (401,403) or state in ('invalid_feed','wall_clock_regressed'):cooldown=3600
        if status==429:cooldown=retry_seconds(safe_header(response_headers,'Retry-After'),receipt)
        if status==0 or status>=500:cooldown=max(cooldown,300)
        try:next_at=later(max(started,receipt,key=at),cooldown)
        except (OverflowError,ValueError):next_at='9999-12-31T23:59:59.999999Z'  # fail closed for an unrepresentable Retry-After
        if state=='ok':
            db.execute('UPDATE state SET next_at=?,etag=?,modified=? WHERE source=?',
                       (next_at,safe_header(response_headers,'ETag'),safe_header(response_headers,'Last-Modified'),source_id))
        else:db.execute('UPDATE state SET next_at=? WHERE source=?',(next_at,source_id))
        metrics=dict(fetch_ms=round((http_end-request_start)*1000,3),normalize_ms=round((parse_end-http_end)*1000,3))
        metrics['ingest_total_ms']=round((timer()-total_start)*1000,3)
        db.execute('UPDATE polls SET received=?,status=?,http_status=?,payload_sha256=?,metrics_json=? WHERE id=?',
                   (receipt,state,status,payload_hash,json.dumps(metrics,sort_keys=True),poll_id));db.commit()
        return dict(source_id=source_id,poll_id=poll_id,status=state,http_status=status,started_at=started,
                    received_at=receipt,payload_sha256=payload_hash,items=len(normalized),new_versions=new,
                    metadata_only_changes=metadata_changes,next_attempt_at=next_at,metrics=metrics,
                    network_request=True,continuous=False,
                    source_scope=source['scope'],transport_denial=safe_header(response_headers,'X-Pilot-Transport-Denial')=='true')
    finally:
        db.close()


def visible(directory, cutoff):
    _,db=open_journal(directory)
    try:
        # Filter actual receipt before decoding content; future versions remain hidden.
        rows=db.execute('SELECT article_json FROM versions WHERE first_seen<=? ORDER BY first_seen,id',
                        (at(cutoff).isoformat(timespec='microseconds').replace('+00:00','Z'),)).fetchall()
        return [json.loads(r[0]) for r in rows]
    finally:db.close()
