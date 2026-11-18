"""Owner-file inspection and fail-closed private admission; no network downloader."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import date
from pathlib import Path

from event_history.library import ROOT, require
from news_pilot.ingest import utc, at
from .model import FIELDS, validate_content, public_url

HERE = Path(__file__).resolve().parent
ASSETS = {
    'NVDA': ('nvda_us_d.csv', 'NASDAQ', 'equity'),
    'AMD': ('amd_us_d.csv', 'NASDAQ', 'equity'),
    'MRNA': ('mrna_us_d.csv', 'NASDAQ', 'equity'),
    'BMY': ('bmy_us_d.csv', 'NYSE', 'equity'),
    'SPY': ('spy_us_d.csv', 'NYSE Arca', 'equity_index_etf_proxy'),
    'GLD': ('gld_us_d.csv', 'NYSE Arca', 'gold_etf_proxy'),
}
COLUMNS = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']


def policy():
    return json.loads((HERE / 'stooq-policy.json').read_text())


def private_path(value):
    p = Path(value).resolve()
    require(p.is_relative_to((ROOT / 'work').resolve()), 'Private output must stay under ignored work/')
    return p


def save_private(path, value):
    p = private_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        p.chmod(0o600)
        json.dump(value, f, indent=2)
        f.write('\n')


def capture_for(symbol, raw, received):
    require(symbol in ASSETS, 'Only the six requested exact securities are supported')
    _, venue, kind = ASSETS[symbol]
    return dict(schema_version=1, source_id='stooq_owner_csv', instrument=symbol,
                symbol=symbol, venue=venue, asset_kind=kind, currency='USD', unit='per_share',
                url=f'https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d',
                url_status='expected_origin_not_observed_HTTP_receipt', publisher='Stooq (owner-declared)',
                frequency='daily', retrieved_at=received, original_downloaded_at=None,
                original_available_at=None, original_vintage_verified=False,
                capture_method='owner_supplied_export_not_origin_HTTP_receipt',
                payload_sha256=hashlib.sha256(raw).hexdigest(), synthetic_control=False,
                snapshot_kind='current_capture', executable=False, usage_scope='private_research',
                admission_status='private_quarantine',canonical_prices_approved=False,
                rights=policy(), price_basis='provider_reported_close_do_not_readjust',
                adjustment_basis=policy()['adjustment_basis'],
                calendar_basis='Supplied reporting-date union; independent exchange calendar unverified')


def validate_private_capture(c):
    p = policy()
    require(p['status']=='reviewed_private_quarantine_only' and p['private_research_permitted'] is True,
            'Stooq private-use rights unverified: inspect only; database import refused')
    require(p['reviewed_source_document_sha256'] and len(p['reviewed_source_document_sha256'])==64,
            'Reviewed primary rights document fingerprint required')
    require(p['private_quarantine_only'] is True and c['admission_status']=='private_quarantine' and c['canonical_prices_approved'] is False,
            'Unknown provenance/adjustments must stay quarantined, never approved')
    require(c['symbol'] in p['allowed_symbols'] and p['provenance_evidence'],'Exact reviewed owner-file scope required')
    require(c['rights']==p and c['usage_scope']=='private_research' and c['adjustment_basis']==p['adjustment_basis'], 'Reviewed private-use policy required')
    symbol = c['symbol']
    require(symbol in ASSETS and c['instrument']==symbol, 'No ticker, spot, index or peer aliases')
    _, venue, kind = ASSETS[symbol]
    require((c['venue'],c['asset_kind'],c['currency'],c['unit'])==(venue,kind,'USD','per_share'),
            'Wrong security, currency, units or proxy identity')
    require(c['url']==f'https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d', 'Wrong declared source resource')
    require(c['price_basis']=='provider_reported_close_do_not_readjust' and c['frequency']=='daily',
            'No invented adjusted close or daily conversion')
    require(c['original_available_at'] is None and c['original_vintage_verified'] is False,
            'No invented historical receipt time')
    require(c['capture_method']=='owner_supplied_export_not_origin_HTTP_receipt'
            and c['url_status']=='expected_origin_not_observed_HTTP_receipt', 'No invented HTTP provenance')
    require(c['schema_version']==1 and c['snapshot_kind']=='current_capture'
            and c['executable'] is False and isinstance(c['synthetic_control'],bool), 'Invalid capture flags')
    require(len(c['payload_sha256'])==64 and all(x in '0123456789abcdef' for x in c['payload_sha256']),
            'Original bytes fingerprint required')
    at(c['retrieved_at']); public_url(c['url']); public_url(p['evidence_url'])
    return c


def parse_supplied(raw, c):
    require(isinstance(raw,bytes) and len(raw)<=32*1024*1024, 'Bounded original bytes required')
    require(hashlib.sha256(raw).hexdigest()==c['payload_sha256'], 'Changed original bytes')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    require(reader.fieldnames==COLUMNS, 'Unknown schema/challenge; inspect the original export')
    rows=[]
    for line, original in enumerate(reader,2):
        require(None not in original and all(v is not None for v in original.values()), 'Malformed row')
        d=date.fromisoformat(original['Date'])
        require(d.isoformat()==original['Date'] and d.weekday()<5, 'Invalid/weekend US daily date')
        r=dict.fromkeys(FIELDS)
        for key, label in (('open','Open'),('high','High'),('low','Low'),('close','Close'),('volume','Volume')):
            r[key]=original[label] or None
        # A missing close is explicit unknown; partial OHLC is never repaired.
        r.update(date=d.isoformat(), status='numeric' if r['close'] is not None else 'not_reported',
                 source_row=line, original_available_at=None, source_fields=original)
        if r['close'] is None:
            require(all(r[k] is None for k in ('open','high','low')), 'Inconsistent absent close')
            r['volume']=None
        rows.append(r)
    return validate_content(rows,c)


def inspect_folder(folder, received=None):
    received=received or utc(); at(received)
    selections={}; records=[]
    for symbol,(name,venue,kind) in ASSETS.items():
        raw=(Path(folder)/name).read_bytes(); c=capture_for(symbol,raw,received)
        rows=parse_supplied(raw,c)
        selections[symbol]=dict(capture=c,rows=rows,raw=raw)
        records.append(dict(symbol=symbol,file=name,rows=len(rows),bytes=len(raw),
            payload_sha256=c['payload_sha256'],first_date=rows[0]['date'],last_date=rows[-1]['date'],
            missing_volume=sum(r['volume'] is None for r in rows),
            unavailable_closes=sum(r['status']!='numeric' for r in rows),
            currency='USD (declared security identity; not embedded in CSV)',
            source='owner_declared_Stooq; original server/receipt unverified',
            adjustments='unknown; no separate adjusted close, splits or dividends',
            original_downloaded_at=None))
    spy={r['date'] for r in selections['SPY']['rows']}
    for r in records:
        points=selections[r['symbol']]['rows']; start=max(points[0]['date'],min(spy));end=min(points[-1]['date'],max(spy))
        actual={p['date'] for p in points if start<=p['date']<=end}
        r['missing_dates_relative_to_supplied_SPY']=sorted(d for d in spy if start<=d<=end and d not in actual)
        r['extra_dates_relative_to_supplied_SPY']=sorted(d for d in actual if d not in spy)
    split_checks=[]
    for before,after,factor,url in [('2021-07-19','2021-07-20',4,'https://investor.nvidia.com/files/doc_downloads/doc_faq/08/Investor-NVIDIA-2021-Stock-Split-FAQ-08.9.2021.pdf'),('2024-06-07','2024-06-10',10,'https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf')]:
        points={r['date']:r for r in selections['NVDA']['rows']}
        from decimal import Decimal
        ratio=Decimal(points[after]['close'])/Decimal(points[before]['close']) if before in points and after in points else None
        split_checks.append(dict(symbol='NVDA',before=before,after=after,issuer_confirmed_split=factor,issuer_source=url,
            supplied_close_ratio=None if ratio is None else str(ratio),
            interpretation='Continuity screen only; near-one ratio is consistent with normalisation, not proof of adjustment method. Do not apply the split again.',
            vendor_adjustment_verified=False,dividend_adjustment_verified=False))
    report=dict(kind='owner_supplied_file_validation_not_import',received_at=received,
        files=records,split_continuity_checks=split_checks,rows_inspected=sum(r['rows'] for r in records),rows_imported=0,
        policy=policy(),source_identity_verified=False,adjustment_basis_verified=False,
        exchange_calendar_verified=False,raw_redistribution_permitted=False,
        limitations=['A supplied filename and matching schema do not prove original server identity.',
                     'SPY dates are an empirical alignment grid, not independent calendar verification.',
                     'Missing dates are not classified as holidays, halts or delistings.',
                     'No historical download/publication time or adjustment factor is fabricated.'])
    return report,selections


def public_summary(study):
    """Allowlisted audit metadata only: never public prices, ratios or P&L."""
    inspection=study['inspection']
    return dict(schema_version=1,kind='Stooq_owner_file_admission_audit',
        files=[{k:f[k] for k in ('symbol','rows','first_date','last_date','missing_volume',
               'unavailable_closes','missing_dates_relative_to_supplied_SPY','extra_dates_relative_to_supplied_SPY')}
               for f in inspection['files']],
        rows_inspected=inspection['rows_inspected'],rows_imported=study.get('rows_imported',0),
        approved_price_rows=0,
        private_use_scope='reviewed_owner_private_quarantine_only_not_open_licence',adjustment_basis_verified=False,
        source_identity_verified=False,exchange_calendar_verified=False,
        new_direct_event_pairs_with_price_coverage=study['newly_covered_direct_event_pairs'],
        direct_horizon_windows_with_price_coverage=study['newly_covered_direct_horizon_windows'],
        new_eligible_historical_examples=0,new_independent_events=0,new_supported_buys=0,
        learning_holdout_changed=False,prospective_predictions=0,
        actual_price_or_return_values_published=0,
        status='Private quarantine and diagnostics only. Public redistribution, training and approved-price promotion remain blocked.',
        source_terms='https://stooq.com/t/',
        terms_result='Owner supplied terms text after direct pages returned browser verification. Section 5.3 requires consent for redistribution. No open/public/commercial/training permission claimed.',
        results_location='Private work/ output only; not a GitHub artifact or dashboard dataset.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','review-study','import'])
    parser.add_argument('--folder',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--db',default='work/stooq-private/prices.sqlite')
    parser.add_argument('--from-db',action='store_true',help='Study the exact imported private captures rather than raw in-memory rows')
    args=parser.parse_args()
    report,selections=inspect_folder(args.folder)
    if args.command=='import':
        # Check every capture before creating a database or admitting any row.
        for s in selections.values(): validate_private_capture(s['capture'])
        from .database import connect,import_capture
        db=connect(args.db)
        try:
            report['imports']=[import_capture(db,s['capture'],s['rows'],s['raw']) for s in selections.values()]
            report['rows_imported']=sum(r['inserted_observations'] for r in report['imports'])
        finally: db.close()
    elif args.command=='review-study':
        from .stooq_study import build_study
        if args.from_db:
            from .database import connect,query
            from world_events.events import digest
            require(private_path(args.db).is_file(),'Import private captures before using --from-db')
            db=connect(args.db)
            try:
                for s in selections.values():
                    cid=digest({k:v for k,v in s['capture'].items() if k!='retrieved_at'})
                    stored=query(db,cid,'1900-01-01','2100-12-31')
                    require(stored['rows']==s['rows'],'Stored bytes/rows differ from inspected owner file')
                    s.update(capture=stored['capture'],rows=stored['rows'])
            finally:db.close()
        report=build_study(selections,report)
        if args.from_db:
            report['rows_imported']=sum(len(s['rows']) for s in selections.values())
            report['database_admission']=dict(kind='private_quarantine',approved_price_rows=0,
                observations=report['rows_imported'],source='existing daily-price SQLite captures and range queries')
    save_private(args.output,report)
    # Never echo source rows, report bodies or user paths to public logs.
    print(json.dumps(dict(status='private_review_only' if args.command!='import' else 'private_import',
                         rows_imported=report.get('rows_imported',0),raw_prices_published=0)))


if __name__=='__main__': main()
