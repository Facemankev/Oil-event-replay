"""Rights/identity/price-basis gates for daily observations, not period averages."""
import json
from pathlib import Path
from datetime import date
from decimal import Decimal,InvalidOperation
from urllib.parse import urlsplit,parse_qsl
import re
from event_history.library import require
from news_pilot.ingest import at

FIELDS=('open','high','low','close','adjusted_close','volume','cash_dividend','split_factor')
ALLOWED_RIGHTS={'public_domain','OGDL-1.0','CC0-1.0','CC-BY-4.0'}


def public_url(value):
    p=urlsplit(value)
    require(p.scheme=='https' and p.hostname and p.port in (None,443) and not p.username and not p.password and not p.fragment,'Public HTTPS source URL required')
    require(not any(k.lower() in ('key','api_key','apikey','token','secret','password','signature','auth','access_token','crumb') for k,v in parse_qsl(p.query,keep_blank_values=True)), 'Credential/signed URL refused')


def number(value,positive=False):
    require(isinstance(value,str) and value.strip()==value and value!='','Exact source decimal text required')
    try:d=Decimal(value)
    except InvalidOperation:raise ValueError('Invalid decimal') from None
    require(d.is_finite() and (d>0 if positive else d>=0),'Invalid numeric observation')
    return d


def validate_capture(c):
    catalog=json.loads((Path(__file__).with_name('providers.json')).read_text())['sources']
    require(c['source_id'] in catalog,'Unknown source: self-asserted licence cannot admit prices')
    spec=catalog[c['source_id']];url=urlsplit(c['url'])
    require(url.hostname==spec['host'] and (url.path.startswith(spec['path_prefix']) if c['source_id']=='nasdaq_wiki' else url.path==spec['path_prefix']),'Outside verified source/resource scope')
    require(c['rights']==spec['rights'] and c['rights_url']==spec['rights_url'],'Rights metadata differs from reviewed source')
    require((c['currency'],c['unit'],c['price_basis'])==(spec['currency'],spec['unit'],spec['basis']) and c['asset_kind'] in spec['asset_kinds'],'Wrong currency, units, adjustment or proxy type')
    require(isinstance(c['synthetic_control'],bool),'Explicit synthetic/real capture classification required')
    if c['source_id']=='nasdaq_wiki':
        require(re.fullmatch(r'/api/v3/datasets/WIKI/[A-Z0-9_]+\.csv',url.path) and url.path.rsplit('/',1)[-1]==c['symbol']+'.csv','Source URL/ticker mismatch')
        require(c['instrument']==c['symbol'],'Native US ticker identity required; no proxy alias')
    elif c['source_id']=='twse_open_index':
        require(c['instrument']=='TWSE:TAIEX' and c['symbol']=='TAIEX' and c['venue']=='TWSE','Not the licensed Taiwan index')
    elif c['source_id']=='twse_open_equities':
        require(c['instrument']=='TWSE:'+c['symbol'] and c['venue']=='TWSE','Native Taiwan security cannot become a US stock/ADR')
    require(c['schema_version']==1 and c['frequency']=='daily','Daily source required; never expand monthly averages')
    require(c['rights']['status']=='verified' and c['rights']['license'] in ALLOWED_RIGHTS,'Unverified/limited usage rights; no import')
    require(c['rights']['redistribution'] is True and bool(c['rights']['evidence']),'Explicit rights evidence needed, not an advertised free tier')
    for key in ('url','rights_url'):public_url(c[key])
    at(c['retrieved_at']);date.fromisoformat(c['rights']['checked_on'])
    require(c['original_available_at'] is None and c['original_vintage_verified'] is False,'Present capture cannot invent an old availability clock')
    require(c['price_basis'] in ('unadjusted_close_with_reported_actions','unadjusted_close_actions_unknown','provider_adjusted_reference'),'Unknown price basis')
    require(c['currency'] in ('USD','GBP','GBp','TWD') and c['unit'] in ('per_share','index_points','per_troy_ounce'),'Explicit source currency/unit needed')
    require(c['asset_kind'] in ('equity','index','gold_benchmark','gold_etf_proxy','equity_index_etf_proxy'),'Unknown instrument role')
    require(bool(c['instrument']) and bool(c['symbol']) and bool(c['venue']) and bool(c['calendar_basis']),'Missing identity/calendar scope')
    require(c['executable'] is False and c['snapshot_kind']=='current_capture','A daily reference is not an execution quote')
    require(len(c['payload_sha256'])==64 and all(x in '0123456789abcdef' for x in c['payload_sha256']),'Original payload fingerprint required')
    return c


def validate_rows(rows,capture):
    validate_capture(capture);require(rows,'Empty/challenge data is not a successful import');seen=set();last=None
    for r in rows:
        d=date.fromisoformat(r['date']);require(r['date']<=capture['retrieved_at'][:10],'Source contains a future daily date')
        if capture['source_id']=='nasdaq_wiki':require(r['date']<='2018-04-11','Frozen WIKI archive cannot provide new prices')
        require(r['date'] not in seen,'Duplicate daily date');seen.add(r['date'])
        require(last is None or last<r['date'],'Daily observations must be chronological');last=r['date']
        require(r['status'] in ('numeric','not_reported','suspended','not_yet_listed','delisted','source_unavailable'),'Unknown availability state')
        require(r['original_available_at'] is None,'Date is not a fabricated close/receipt time')
        require(isinstance(r['source_row'],int) and r['source_row']>=2,'Original row locator required')
        if r['status']!='numeric':
            require(all(r.get(k) is None for k in FIELDS),'Unavailable is null, never zero or a carried price');continue
        close=number(r['close'],True)
        for k in ('open','high','low','adjusted_close'):
            if r.get(k) is not None:number(r[k],True)
        for k in ('volume','cash_dividend'):
            if r.get(k) is not None:number(r[k])
        if r.get('split_factor') is not None:number(r['split_factor'],True)
        if all(r.get(k) is not None for k in ('open','high','low')):
            hi=number(r['high'],True);lo=number(r['low'],True);op=number(r['open'],True)
            require(lo<=min(op,close)<=max(op,close)<=hi,'OHLC violation; no silently repaired prices')
        if capture['price_basis']=='provider_adjusted_reference':require(r.get('adjusted_close') is not None,'Provider adjustment missing; do not calculate it')
        if capture['price_basis']=='unadjusted_close_with_reported_actions':
            require(r.get('cash_dividend') is not None and r.get('split_factor') is not None,'Corporate-action metadata missing')
    return rows
