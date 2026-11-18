"""Strict daily-price parsers; no credentials, synthetic fills or adjusted-value guesses."""
import csv,hashlib,io,json
from .model import FIELDS,validate_rows
from event_history.library import require

WIKI_COLUMNS=['Date','Open','High','Low','Close','Volume','Ex-Dividend','Split Ratio','Adj. Open','Adj. High','Adj. Low','Adj. Close','Adj. Volume']
CANONICAL_COLUMNS=['date','status',*FIELDS]


def parse_csv(payload,capture,format='canonical'):
    require(isinstance(payload,bytes) and len(payload)<=32*1024*1024,'Bounded source bytes required')
    require(hashlib.sha256(payload).hexdigest()==capture['payload_sha256'],'Source bytes differ from capture provenance')
    text=payload.decode('utf-8-sig');require('<html' not in text[:2000].lower() and '<!doctype' not in text[:2000].lower(),'HTML/challenge is not prices')
    reader=csv.DictReader(io.StringIO(text,newline=''));rows=[]
    if format=='wiki':require(reader.fieldnames==WIKI_COLUMNS,'Unknown WIKI fields; never assume an adjustment basis')
    else:require(format=='canonical' and reader.fieldnames==CANONICAL_COLUMNS,'Unknown typed daily CSV fields')
    for line,p in enumerate(reader,2):
        require(None not in p and all(v is not None for v in p.values()),'Malformed daily source row')
        if format=='wiki':
            r=dict(date=p['Date'],status='numeric',open=p['Open'],high=p['High'],low=p['Low'],close=p['Close'],volume=p['Volume'],
                   cash_dividend=p['Ex-Dividend'],split_factor=p['Split Ratio'],adjusted_close=p['Adj. Close'])
        else:r={k:(v if v!='' else None) for k,v in p.items()}
        r.update(source_row=line,original_available_at=None,source_fields=p);rows.append(r)
    # A source can return reverse chronological CSV. Preserve original row locator,
    # normalize date order only, never prices or dates themselves.
    rows.sort(key=lambda r:r['date'])
    return validate_rows(rows,capture)


def parse_twse_index(payload,capture):
    require(hashlib.sha256(payload).hexdigest()==capture['payload_sha256'],'Source bytes changed')
    data=json.loads(payload)
    require(data.get('stat')=='OK' and data.get('fields')==['日期','開盤指數','最高指數','最低指數','收盤指數'],'Wrong index/source response or challenge')
    rows=[]
    for i,cells in enumerate(data['data'],2):
        require(len(cells)==5,'Wrong daily index width');parts=cells[0].split('/')
        require(len(parts)==3 and len(parts[0])==3,'ROC calendar required; do not guess date format')
        day=f'{int(parts[0])+1911:04d}-{int(parts[1]):02d}-{int(parts[2]):02d}'
        r=dict.fromkeys(FIELDS);r.update(date=day,status='numeric',open=cells[1].replace(',',''),high=cells[2].replace(',',''),
          low=cells[3].replace(',',''),close=cells[4].replace(',',''),source_row=i,original_available_at=None);rows.append(r)
    rows.sort(key=lambda r:r['date']);return validate_rows(rows,capture)


def parse_twse_current(payload,capture):
    """Documented open-data fields; a one-day export is never called history."""
    require(hashlib.sha256(payload).hexdigest()==capture['payload_sha256'],'Source bytes changed')
    reader=csv.DictReader(io.StringIO(payload.decode('utf-8-sig'),newline=''))
    columns=['Date','Code','Name','TradeVolume','TradeValue','OpeningPrice','HighestPrice','LowestPrice','ClosingPrice','Change','Transaction']
    require(reader.fieldnames==columns,'Unknown TWSE export fields; inspect actual response before changing parser')
    rows=[]
    for i,p in enumerate(reader,2):
        if p['Code']!=capture['symbol']:continue
        day=p['Date'];require(day.isdigit() and len(day) in (7,8),'Unknown source date format')
        year=int(day[:-4]);year=year+1911 if len(day)==7 else year
        day=f'{year:04d}-{day[-4:-2]}-{day[-2:]}'
        r=dict.fromkeys(FIELDS);close=p['ClosingPrice'].replace(',','')
        unavailable=close in ('','--','---')
        if not unavailable:
            r.update(close=close,volume=p['TradeVolume'].replace(',',''))
            for field,original in [('open','OpeningPrice'),('high','HighestPrice'),('low','LowestPrice')]:
                value=p[original].replace(',','');r[field]=None if value in ('','--','---') else value
        r.update(date=day,status='not_reported' if unavailable else 'numeric',source_row=i,original_available_at=None,source_fields=p)
        rows.append(r)
    rows.sort(key=lambda r:r['date']);return validate_rows(rows,capture)


def parse(payload,capture):
    if capture['source_id']=='nasdaq_wiki':return parse_csv(payload,capture,'wiki')
    if capture['source_id']=='twse_open_index':return parse_twse_index(payload,capture)
    if capture['source_id']=='twse_open_equities':return parse_twse_current(payload,capture)
    raise ValueError('Unknown reviewed provider/parser')
