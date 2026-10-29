"""Validated, versioned historical event records. Python standard library only."""
import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT=Path(__file__).resolve().parents[1]
SEED=Path(__file__).with_name('seed.json')
CATEGORIES={'weather','production_policy','sanctions','conflict','strategic_stocks','demand_shock'}
QUALITIES={'primary_release','official_report','official_retrospective','reliable_secondary'}

class ValidationError(ValueError):
    pass

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def require(condition,message):
    if not condition:
        raise ValidationError(message)

def day(value):
    require(isinstance(value,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',value),'Invalid ISO date')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError('Invalid calendar date') from exc

def instant(value):
    require(isinstance(value,str),'Timestamp must be a string')
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValidationError('Invalid timestamp') from exc
    require(result.tzinfo is not None and result.utcoffset() is not None,'Timestamp needs an explicit UTC offset')
    return result

def text(value,label):
    require(isinstance(value,str) and 0<len(value.strip())<=4000,label+' is required')

def https(value):
    parsed=urlparse(value)
    require(parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password,'Evidence needs a public HTTPS URL without credentials')

def timing(t,unknown=False):
    require(isinstance(t,dict),'Invalid temporal record')
    require(t.get('precision') in ({'unknown','day','minute'} if unknown else {'day','minute'}),'Invalid temporal precision')
    zone=t.get('timezone')
    if zone is not None:
        try:
            ZoneInfo(zone)
        except (ZoneInfoNotFoundError,TypeError,ValueError) as exc:
            raise ValidationError('Unknown IANA timezone') from exc
    if t['precision']=='unknown':
        require(t.get('date') is None and t.get('at') is None and zone is None,'Unknown timing must not carry invented dates or times')
        return
    day(t.get('date'))
    if t['precision']=='day':
        require(t.get('at') is None,'Date-only evidence must not invent a clock time')
    else:
        stamp=instant(t.get('at'))
        require(stamp.date().isoformat()==t['date'],'Timestamp and local calendar date disagree')
        require(zone is not None,'Minute precision needs a named timezone')
        local=stamp.astimezone(ZoneInfo(zone))
        require(local.replace(tzinfo=None)==stamp.replace(tzinfo=None) and local.utcoffset()==stamp.utcoffset(),'Timezone and explicit timestamp offset disagree')
        require(stamp.second==0 and stamp.microsecond==0,'Minute precision must not claim seconds')

def validate_record(record):
    require(isinstance(record,dict),'Event must be an object')
    require(isinstance(record.get('id'),str) and re.fullmatch(r'[a-z][a-z0-9-]{2,80}',record['id']),'Invalid stable event ID')
    require(type(record.get('revision')) is int and record['revision']>=1,'Invalid revision')
    for key in ('title','description','geography','relevance','uncertainty'):
        text(record.get(key),key)
    require(isinstance(record.get('category'),str) and record['category'] in CATEGORIES,'Unknown event category')
    require(isinstance(record.get('affected_commodities'),list) and all(isinstance(v,str) for v in record['affected_commodities']) and set(record['affected_commodities'])=={'brent','wti'} and len(record['affected_commodities'])==2,'Seed scope is Brent and WTI')
    timing(record.get('occurred'))
    require(type(record['occurred'].get('approximate')) is bool,'Occurrence approximation must be explicit')
    timing(record.get('first_public'),unknown=True)
    day(record.get('reviewed_on'))
    require(record['occurred']['date']<=record['reviewed_on'],'Historical occurrence cannot follow its review date')
    sources=record.get('evidence')
    require(isinstance(sources,list) and 1<=len(sources)<=10,'Event needs supporting evidence')
    ids=set()
    for source in sources:
        require(isinstance(source,dict),'Invalid evidence record')
        for key in ('id','url','publisher','stable_reference','locator','summary','reuse_note'):
            text(source.get(key),key)
        require(source['id'] not in ids,'Duplicate source ID');ids.add(source['id'])
        https(source['url'])
        if source.get('archive_url') is not None:
            https(source['archive_url'])
        require(isinstance(source.get('quality'),str) and source['quality'] in QUALITIES,'Unclassified evidence quality')
        require(source.get('evidence_kind')=='curated_fact_card_not_full_page','Do not mislabel curated evidence as an original page snapshot')
        timing(source.get('published'),unknown=True)
        day(source.get('checked_on'))
        if source['published']['date'] is not None:
            require(source['published']['date']<=source['checked_on'],'A source cannot be checked before its stated publication date')
        require(source['checked_on']<=record['reviewed_on'],'Source check cannot follow record review')
        expected=digest({k:v for k,v in source.items() if k!='sha256'})
        require(source.get('sha256')==expected,'Evidence card hash mismatch')
    require(record.get('public_evidence') in ids,'Public evidence reference missing')
    public=record['first_public']
    require(isinstance(public.get('status'),str) and public['status'] in {'earliest_located_not_exhaustive','not_established'},'Unknown first-public status')
    if public['status']=='not_established':
        require(public['precision']=='unknown' and public.get('evidence_id') is None,'Unestablished first-public time must remain null')
    else:
        require(public.get('evidence_id') in ids and public['precision']!='unknown','Located first-public evidence missing')
        source=next(s for s in sources if s['id']==public['evidence_id'])
        require(source['quality']=='primary_release','Institutional reports cannot establish originating first-public disclosure')
        for field in ('date','at','timezone','precision'):
            require(public[field]==source['published'][field],'First-public claim and its supporting publication disagree')
    # An announcement can precede implementation/occurrence. Do not impose a
    # false universal occurred <= published ordering. The seed explains the distinction.
    return record

def load_seed(path=SEED):
    raw=Path(path).read_bytes()
    require(len(raw)<=5_000_000,'Dataset exceeds size bound')
    try:
        dataset=json.loads(raw)
    except (ValueError,UnicodeError) as exc:
        raise ValidationError('Malformed event JSON') from exc
    require(isinstance(dataset,dict) and dataset.get('schema_version')==1,'Unsupported event schema')
    records=dataset.get('events')
    require(isinstance(records,list) and 1<=len(records)<=10000,'Invalid event collection')
    seen=set()
    for record in records:
        validate_record(record)
        require(record['id'] not in seen,'Duplicate event ID in one import');seen.add(record['id'])
    return records

def connect(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,isolation_level=None,timeout=30)
    db.row_factory=sqlite3.Row
    version=db.execute('PRAGMA user_version').fetchone()[0]
    if version==0:
        if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
            db.close()
            raise ValidationError('Refusing to migrate an unrelated database')
        db.executescript('BEGIN IMMEDIATE;\n'+Path(__file__).with_name('schema.sql').read_text()+'\nCOMMIT;')
    else:
        if version!=1301:
            db.close()
            raise ValidationError('This is not an EVT-1 event database; keep price/event database files separate')
    return db

def read_db(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    if db.execute('PRAGMA user_version').fetchone()[0]!=1301:
        db.close()
        raise ValidationError('Unsupported event database version')
    return db

def import_records(db,records):
    require(isinstance(records,list) and 1<=len(records)<=10000,'Invalid event collection')
    seen=set()
    for record in records:
        validate_record(record)
        require(record['id'] not in seen,'Duplicate event ID');seen.add(record['id'])
    inserted=reused=0
    db.execute('BEGIN IMMEDIATE')
    try:
        for record in records:
            sha=digest(record)
            previous=db.execute('SELECT content_sha256 FROM world_event_versions WHERE event_id=? AND revision=?',(record['id'],record['revision'])).fetchone()
            if previous:
                require(previous[0]==sha,'Existing revision is immutable; increment revision for a correction')
                reused+=1;continue
            maximum=db.execute('SELECT max(revision) FROM world_event_versions WHERE event_id=?',(record['id'],)).fetchone()[0] or 0
            require(record['revision']==maximum+1,'Revision numbers must advance one at a time')
            db.execute('INSERT INTO world_event_versions VALUES(?,?,?,?,?,?,?,?,?)',
                       (record['id'],record['revision'],sha,datetime.now(timezone.utc).isoformat(),record['category'],record['occurred']['date'],record['first_public']['at'],record['first_public']['date'],canonical(record)))
            inserted+=1
        db.execute('INSERT INTO world_event_import_runs(imported_at_utc,dataset_sha256,inserted,reused) VALUES(?,?,?,?)',
                   (datetime.now(timezone.utc).isoformat(),digest(records),inserted,reused))
        db.execute('COMMIT')
    except Exception:
        db.execute('ROLLBACK');raise
    return {'inserted':inserted,'reused':reused,'current_events':db.execute('SELECT count(*) FROM world_events_current').fetchone()[0]}

def list_events(db,category=None):
    require(category is None or category in CATEGORIES,'Unknown category')
    sql='SELECT payload FROM world_events_current'
    args=()
    if category:
        sql+=' WHERE category=?';args=(category,)
    return [json.loads(r[0]) for r in db.execute(sql+' ORDER BY occurrence_date,event_id',args)]

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',default='work/world-events.sqlite')
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','import'):
        p=commands.add_parser(name);p.add_argument('--seed',default=str(SEED))
    p=commands.add_parser('list');p.add_argument('--category',choices=sorted(CATEGORIES))
    for name in ('compare','export'):
        p=commands.add_parser(name)
        p.add_argument('--before',type=int,default=5);p.add_argument('--after',type=int,default=5)
        p.add_argument('--prices-json');p.add_argument('--prices-dir',default=str(ROOT/'data/historical'))
        if name=='compare':p.add_argument('--event',required=True)
        else:p.add_argument('--output',default=str(ROOT/'data/world-event-research.json'))
    args=parser.parse_args(argv)
    try:
        if args.command=='validate':
            records=load_seed(args.seed)
            result={'events':len(records),'categories':sorted({r['category'] for r in records}),
                    'minute_public_evidence':sum(r['evidence'][0]['published']['precision']=='minute' for r in records),
                    'first_public_not_established':sum(r['first_public']['status']=='not_established' for r in records)}
        elif args.command=='import':
            records=load_seed(args.seed);db=connect(args.db)
            try:result=import_records(db,records)
            finally:db.close()
        else:
            db=read_db(args.db)
            try:
                records=list_events(db,args.category if args.command=='list' else None)
            finally:db.close()
            if args.command=='list':result=records
            else:
                from .research import CSVPrices,JSONPrices,compare,export
                prices=JSONPrices(args.prices_json) if args.prices_json else CSVPrices(args.prices_dir)
                if args.command=='compare':
                    event=next((r for r in records if r['id']==args.event),None)
                    require(event is not None,'Event ID not found')
                    result=compare(event,prices,args.before,args.after)
                else:
                    result=export(records,prices,args.output,args.before,args.after)
        print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
        return 0
    except (ValidationError,OSError,sqlite3.Error,ValueError,KeyError,TypeError) as exc:
        print('Error: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
