"""Descriptive event/price joins. No causal inference or executable trade returns."""
import csv
from datetime import timedelta,timezone
from decimal import Decimal,InvalidOperation
import hashlib
import json
from pathlib import Path
from .events import ROOT,ValidationError,canonical,day,digest,instant,require,validate_record

METHODOLOGY='shared-observation-windows-v1'
MARKETS=('brent','wti')

class PriceStore:
    """Adapter boundary: range(market,start,end) -> sorted (date,Decimal|None).

    Metadata must describe the actual vintage/source, not invent known-at times.
    No dependency on historical.prices or any other unmerged PR #12 module.
    """
    def range(self,market,start,end):
        return [(d,v) for d,v in self.rows[market] if start<=d<=end]


def value(raw):
    if raw is None or str(raw).strip() in {'','NA','N/A','.','-','--','W'}:
        return None
    text=str(raw).strip()
    import re
    require(bool(re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',text)),'Invalid price')
    try:n=Decimal(text)
    except InvalidOperation as exc:raise ValidationError('Invalid price') from exc
    require(n.is_finite() and abs(n)<=Decimal('1000000000') and n.as_tuple().exponent>=-12,'Invalid/nonfinite price')
    return n


def normalize(rows):
    parsed={}
    for d,v in rows:
        day(d)
        require(d not in parsed,'Duplicate date in price input')
        parsed[d]=value(v)
    require(bool(parsed),'Empty price series')
    return sorted(parsed.items())

class CSVPrices(PriceStore):
    """Exact committed main-branch snapshots, checked against a reviewed manifest."""
    def __init__(self,directory=ROOT/'data/historical'):
        manifest=json.loads(Path(__file__).with_name('prices-manifest.json').read_text())
        self.rows={};self.metadata={}
        for market in MARKETS:
            m=manifest[market];raw=(Path(directory)/m['filename']).read_bytes()
            require(hashlib.sha256(raw).hexdigest()==m['sha256'],'Price snapshot hash mismatch; review its manifest rather than using an unrecorded revision')
            require(len(raw)<=20_000_000,'Price CSV exceeds size bound')
            reader=csv.reader(raw.decode('utf-8-sig').splitlines(),strict=True)
            require(next(reader,None)==['Date','Price'],'Price CSV needs exactly Date,Price')
            rows=list(reader)
            require(all(len(r)==2 for r in rows),'Malformed price CSV row')
            self.rows[market]=normalize(rows)
            self.metadata[market]={**m,'source_kind':'secondary_EIA_derived_seed','unit':'USD/barrel','count':sum(v is not None for _,v in self.rows[market]),'known_at_utc':None,'point_in_time_safe':False}

class JSONPrices(PriceStore):
    """Consumes the documented DAT-3 range/static-export JSON shape, when supplied.

    This adapter can be used after #12 lands, but imports no code from that PR.
    Query dictionaries can be wrapped in {schemaVersion:1,series:[...]}.
    """
    def __init__(self,path):
        raw=Path(path).read_bytes();require(len(raw)<=20_000_000,'Price JSON is too large')
        data=json.loads(raw)
        require(isinstance(data,dict) and data.get('schemaVersion')==1 and isinstance(data.get('series'),list),'Unsupported price JSON version')
        self.rows={};self.metadata={}
        for s in data['series']:
            market=s.get('series')
            require(market in MARKETS and market not in self.rows,'Unsupported or duplicate market')
            require(s.get('unit')=='USD/barrel','Unsupported quote currency/unit')
            require(isinstance(s.get('sources'),dict) and bool(s['sources']),'Price JSON needs provenance')
            observations=s.get('observations')
            require(isinstance(observations,list),'Missing observations')
            require(all(isinstance(r,dict) and r.get('snapshot_id') in s['sources'] for r in observations),'Unresolved price snapshot reference')
            self.rows[market]=normalize([(r['date'],r['value']) for r in observations])
            self.metadata[market]={'source_kind':'supplied_DAT3_JSON','unit':'USD/barrel','input_sha256':hashlib.sha256(raw).hexdigest(),'sources':s['sources'],'count':sum(v is not None for _,v in self.rows[market]),'known_at_note':s.get('known_at_note','Original publication/vintage times not established'),'point_in_time_safe':False}
        require(set(self.rows)==set(MARKETS),'Both Brent and WTI are required')


def comparison_anchor(event):
    source=next(s for s in event['evidence'] if s['id']==event['public_evidence'])
    published=source['published']
    if published['precision']=='unknown':
        return None,source,'Publication timing unknown; occurrence date is not a substitute'
    if published['at']:
        return instant(published['at']).astimezone(timezone.utc).date(),source,'UTC date of the printed publication stamp; exact market daily-observation time is unknown'
    return day(published['date']),source,'Publisher-labelled publication date; timezone/clock unknown, so alignment is approximate descriptive research only'


def pct(first,last):
    if first<=0:
        return None
    return format(((last/first-1)*100).quantize(Decimal('0.0001')),'f')


def compare(event,prices,before=5,after=5,lookaround_days=60):
    validate_record(event)
    require(type(before) is int and type(after) is int and 1<=before<=20 and 1<=after<=20,'Observation windows must be 1–20 each')
    require(type(lookaround_days) is int and 1<=lookaround_days<=366,'Invalid calendar search bound')
    anchor,source,note=comparison_anchor(event)
    result={'event_id':event['id'],'event_revision':event['revision'],'event_sha256':digest(event),'methodology':METHODOLOGY,'before_observations':before,'after_observations':after,'point_in_time_safe':False,'backtest_eligible':False,'caveat':'Descriptive association only. No causal, predictive or executable trading/P&L claim. Price vintages and original known-at times are not established.','source_evidence_id':source['id'],'first_public_status':event['first_public']['status'],'alignment_note':note,'price_sources':prices.metadata}
    if anchor is None:
        return {**result,'status':'publication_time_unknown','series':[]}
    start=(anchor-timedelta(days=lookaround_days)).isoformat()
    end=(anchor+timedelta(days=lookaround_days)).isoformat()
    maps={m:dict(prices.range(m,start,end)) for m in MARKETS}
    numeric={m:{d for d,v in maps[m].items() if v is not None} for m in MARKETS}
    shared=sorted(numeric['brent'] & numeric['wti'])
    pre=[d for d in shared if d<anchor.isoformat()][-before:]
    post=[d for d in shared if d>anchor.isoformat()][:after]
    result.update(publication_anchor_date=anchor.isoformat(),occurrence_date=event['occurred']['date'],evidence_lag_calendar_days=(anchor-day(event['occurred']['date'])).days,search_range=[start,end],pre_dates=pre,post_dates=post,calendar={'policy':'Use shared actual numeric observation dates; exclude the entire publication anchor date; no weekend/holiday assumption or filling','brent_only_dates':sorted(numeric['brent']-numeric['wti']),'wti_only_dates':sorted(numeric['wti']-numeric['brent']),'explicit_missing':{m:[d for d,v in maps[m].items() if v is None] for m in MARKETS}})
    if len(pre)!=before or len(post)!=after:
        return {**result,'status':'insufficient_shared_observations','series':[]}
    series=[]
    for market in MARKETS:
        baseline=maps[market][pre[-1]];last=maps[market][post[-1]]
        series.append({'series':market,'unit':'USD/barrel','baseline_date':pre[-1],'baseline':str(baseline),'end_date':post[-1],'end':str(last),'absolute_change':str(last-baseline),'change_percent':pct(baseline,last),'pre_window_change_percent':pct(maps[market][pre[0]],baseline),'post_window_change_percent':pct(maps[market][post[0]],last),'percent_note':'Undefined for a zero or negative starting price; absolute changes remain available.','pre_rows':[[d,str(maps[market][d])] for d in pre],'post_rows':[[d,str(maps[market][d])] for d in post]})
    return {**result,'status':'ok','series':series}


def export(records,prices,output,before=5,after=5):
    ordered=sorted(records,key=lambda r:(r['occurred']['date'],r['id']))
    comparisons=[compare(r,prices,before,after) for r in ordered]
    data={'schemaVersion':1,'methodology':METHODOLOGY,'event_set_sha256':digest(ordered),'events':ordered,'comparisons':comparisons,'summary':{'events':len(records),'successful_comparisons':sum(c['status']=='ok' for c in comparisons),'first_public_not_established':sum(r['first_public']['status']=='not_established' for r in records),'minute_public_evidence':sum(s['published']['precision']=='minute' for r in records for s in r['evidence']),'backtest_eligible':0}}
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(canonical(data)+'\n');temporary.replace(path)
    return data['summary']
