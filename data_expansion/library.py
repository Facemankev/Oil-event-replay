"""Validate exact primary transcriptions and short, separately typed IPO facts."""
import calendar,csv,hashlib,json,re
from datetime import date
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from event_history.library import ROOT,require
from free_pilot.data import load_free_library

HERE=Path(__file__).resolve().parent
ASSETS={'wb-brent-average':'USD/barrel','wb-wti-average':'USD/barrel','wb-gold-average':'USD/troy_ounce'}


def https_url(value):
    p=urlsplit(value)
    require(p.scheme=='https' and p.hostname and not p.username and not p.password and not p.query,'Expected public source URL without credentials/query')


def period_bounds(period,frequency):
    if frequency=='annual' and re.fullmatch(r'\d{4}',period):
        year=int(period);return date(year,1,1).isoformat(),date(year,12,31).isoformat()
    if frequency=='monthly' and re.fullmatch(r'\d{4}-\d{2}',period):
        y,m=map(int,period.split('-'));start=date(y,m,1);end=date(y,m,calendar.monthrange(y,m)[1])
        return start.isoformat(),end.isoformat()
    if frequency=='quarterly' and re.fullmatch(r'\d{4}-Q[1-4]',period):
        y=int(period[:4]);m=int(period[-1])*3
        return date(y,m-2,1).isoformat(),date(y,m,calendar.monthrange(y,m)[1]).isoformat()
    raise ValueError('Frequency/period mismatch; no daily observations accepted')


def validate(bundle):
    require(bundle['schema_version']==1,'Unknown bundle version')
    sources=bundle['sources'];seen=set()
    require(sources and bundle['averages'] and bundle['ipos'],'Empty evidence is not a successful import')
    for sid,s in sources.items():
        require(sid==s['id'] and s['publisher']=='World Bank','Unknown primary provider')
        require(s['license']=='CC-BY-4.0' and s['license_url']=='https://datacatalog.worldbank.org/public-licenses','Unverified redistribution rights')
        require(s['url'].startswith('https://thedocs.worldbank.org/en/doc/') and s['url'].endswith('.pdf'),'Unknown primary table')
        for k in ('url','license_url','dataset_url'):https_url(s[k])
        for k in ('document_day','web_publication_day','checked_on'):date.fromisoformat(s[k])
        require(s['capture_method']=='visible_official_table_transcription_via_supported_reader','Unexpected capture type')
        require(s['original_http_sha256'] is None and s['original_available_at'] is None and s['original_version_verified'] is False,'Transcription is not an original HTTP vintage')
    for r in bundle['averages']:
        require(r['instrument'] in ASSETS and r['unit']==ASSETS[r['instrument']] and r['currency']=='USD','Instrument/unit mismatch')
        require(r['source_id'] in sources and r['statistic']=='period_average' and r['status']=='numeric','Not a sourced average')
        _,end=period_bounds(r['period'],r['frequency']);s=sources[r['source_id']]
        require(end<max(s['document_day'],s['web_publication_day']),'Average not yet mature at declared publication day')
        require(Decimal(r['value']).is_finite() and Decimal(r['value'])>0,'Invalid reference average')
        key=(r['source_id'],r['instrument'],r['frequency'],r['period'])
        require(key not in seen,'Duplicate period within edition');seen.add(key)
        require(bool(r['locator']),'Missing source cell locator')
    ids=set();offerings=set()
    for c in bundle['ipos']:
        require(c['id'] not in ids and c['episode_id']==c['id'],'Repeated offering episode');ids.add(c['id'])
        offering=(c['issuer'].casefold(),c['first_session'] or c['event_day'])
        require(offering not in offerings,'Repeated issuer/offering even under a different event ID');offerings.add(offering)
        require(c['evaluation_membership']=='separate_research_reserve','New IPO cannot enter old held-out evaluation')
        require(c['public_at'] is None and c['original_available_at'] is None and c['original_version_verified'] is False,'Unknown original timestamps must remain unknown')
        date.fromisoformat(c['event_day']);date.fromisoformat(c['checked_on'])
        if c['document_day']:date.fromisoformat(c['document_day'])
        require(c['status'] in ('priced','traded','withdrawal_requested','suspended_before_listing'),'Unknown offering status')
        require(c['corporate_actions_verified'] is False and c['adjusted_daily_history'] is False and c['retail_allocation_verified'] is False,'Unsupported security-price/fill claim')
        for s in [c['event_source'],c['reaction_source']]:
            if s:
                https_url(s['url']);require(s['rights']=='FACTS_ONLY_NOT_A_PRICE_FEED','No bulk price rights established')
        if c['status'] in ('withdrawal_requested','suspended_before_listing'):
            require(all(c[k] is None for k in ('offer_price','unit','first_session','reported_first_close','reaction_source')),'No invented fill/return for uncompleted listing')
        else:
            require(c['unit'] in ('USD/share','USD/ADS','GBp/share') and Decimal(c['offer_price'])>0,'Unsupported offer units/value')
            if c['first_session']:
                date.fromisoformat(c['first_session']);require(c['first_session']>=c['event_day'],'Session before offering')
        if c['reported_first_close'] is not None:
            require(c['status']=='traded' and c['first_session'] and c['reaction_source'] and Decimal(c['reported_first_close'])>0,'Unsourced first-close fact')
        if c['reaction_source'] and c['reaction_source'].get('document_day'):
            require(c['reaction_source']['document_day']>=c['first_session'],'Outcome reported before session')
    return bundle


def load_bundle():
    manifest=json.loads((HERE/'sources/world-bank.json').read_text())
    require(manifest['schema_version']==1 and manifest['file']=='world-bank-averages.csv','Unknown capture identity')
    raw=(HERE/'sources'/manifest['file']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==manifest['sha256'],'Review changed source transcription before updating its pin')
    averages=list(csv.DictReader(raw.decode().splitlines()))
    require(len(averages)==manifest['rows'],'Source count mismatch')
    ipo=json.loads((HERE/'sources/ipo-facts.json').read_text())
    require(ipo['schema_version']==1 and ipo['kind']=='sourced_factual_research_reserve','Unknown IPO source shape')
    return validate(dict(schema_version=1,sources={s['id']:s for s in manifest['sources']},averages=averages,ipos=ipo['cases']))


def expanded_library(data=None,bundle=None):
    """Attach typed context; no average/offer/reported close enters the daily engine."""
    data=dict(data if data is not None else load_free_library());bundle=bundle or load_bundle()
    validate(bundle)
    data['period_average_references']=bundle['averages']
    data['ipo_research_reserve']=bundle['ipos']
    return data
