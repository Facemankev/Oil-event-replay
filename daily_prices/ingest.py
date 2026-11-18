"""Bounded anonymous source checks; explicit rights and observed data precede import."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
from event_history.library import require
from event_history.__main__ import new_output
from news_pilot.ingest import fetch,utc,at,retry_seconds,later,safe_header
from .model import public_url
from .parsers import parse
from .database import record_receipt,import_capture

HERE=Path(__file__).resolve().parent


def providers():return json.loads((HERE/'providers.json').read_text())['sources']


def make_capture(sid,url,payload,identity,received_at):
    spec=providers()[sid];public_url(url);u=urlsplit(url)
    require(u.hostname==spec['host'] and (u.path.startswith(spec['path_prefix']) if sid=='nasdaq_wiki' else u.path==spec['path_prefix']),'Unapproved source location')
    require(not any(k in identity for k in ('source_id','url','rights','payload_sha256','retrieved_at','original_available_at')),'Identity cannot override source provenance')
    return dict(schema_version=1,source_id=sid,url=url,rights_url=spec['rights_url'],rights=spec['rights'],
      publisher=spec['publisher'],payload_sha256=hashlib.sha256(payload).hexdigest(),retrieved_at=received_at,
      frequency='daily',capture_method='direct_HTTP_body',price_basis=spec['basis'],currency=spec['currency'],unit=spec['unit'],
      original_available_at=None,original_vintage_verified=False,snapshot_kind='current_capture',executable=False,
      synthetic_control=False,**identity)


def poll(db,sid,identity=None,client=fetch,clock=utc,import_data=False,request_url=None):
    spec=providers()[sid];started=clock();url=request_url or spec['probe_url']
    public_url(url);parsed=urlsplit(url)
    require(parsed.hostname==spec['host'] and (parsed.path.startswith(spec['path_prefix']) if sid=='nasdaq_wiki' else parsed.path==spec['path_prefix']),'Unapproved request source/resource')
    if sid=='nasdaq_wiki':require(re.fullmatch(r'/api/v3/datasets/WIKI/[A-Z0-9_]+\.csv',parsed.path),'Only the reviewed original daily ticker resource is requested')
    with db:
        db.execute('BEGIN IMMEDIATE')
        prior=db.execute('SELECT payload FROM receipts WHERE source=? ORDER BY observed DESC,rowid DESC LIMIT 1',(sid,)).fetchone()
        if prior:
            previous=json.loads(prior['payload'])
            if at(started)<at(previous['next_attempt_at']):return dict(source_id=sid,status='cooldown_no_request',imported_rows=0,next_attempt_at=previous['next_attempt_at'])
        reservation=dict(source_id=sid,url=url,observed_at=started,status='request_reserved',next_attempt_at=later(started,60),imported_rows=0)
        record_receipt(db,reservation)
    try:status,body,headers=client(url,{})
    except Exception:status,body,headers=0,b'',{}
    received=clock();valid_clock=at(received)>=at(started)
    delay=retry_seconds(safe_header(headers,'Retry-After'),received) if status==429 else 3600 if status in (401,403) else 300 if status==0 or status>=500 else 60
    receipt=dict(source_id=sid,url=url,observed_at=received,started_at=started,http_status=status,
      body_bytes_observed=len(body),transport_denial=safe_header(headers,'X-Pilot-Transport-Denial')=='true',
      status='http_access_only_not_a_working_series' if status==200 else 'unavailable_no_import',
      next_attempt_at=later(max(started,received,key=at),delay),imported_rows=0,
      rows_validated=0,payload_sha256=None,cost_GBP='0.00',original_vintage_verified=False)
    if status==200 and valid_clock and len(body)<=32*1024*1024 and identity:
        cap=make_capture(sid,url,body,identity,received)
        try:
            rows=parse(body,cap)
            receipt.update(status='validated_daily_reference',rows_validated=len(rows),payload_sha256=cap['payload_sha256'])
            if import_data:receipt.update(import_capture(db,cap,rows,body));receipt['inserted_database_rows']=receipt.pop('inserted_rows');receipt['imported_rows']=receipt.pop('inserted_observations')
        except (ValueError,KeyError,TypeError,UnicodeError,ArithmeticError):receipt['status']='invalid_unknown_or_challenge_series';receipt['next_attempt_at']=later(received,3600)
    elif not valid_clock:receipt['status']='clock_regressed_no_import'
    record_receipt(db,receipt);return receipt
