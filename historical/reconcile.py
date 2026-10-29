"""Read-only review of a completed EIA reconciliation; never applies price changes."""
import argparse
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from . import prices as p

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'historical/reconciliation'


def require(condition, message):
    if not condition:
        raise p.DataError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 5_000_000, 'Review input exceeds size limit')
    value = json.loads(raw)
    require(isinstance(value, dict), 'Expected a JSON object')
    return value, digest(raw)


def days(values, start, end):
    require(isinstance(values, list), 'Missing date list')
    for value in values:
        p.iso_day(value)
        require(start <= value <= end, 'Date outside reviewed seed coverage')
    require(values == sorted(set(values)), 'Date lists must be sorted and unique')
    return set(values)


def validate_report(report):
    require(report.get('schema_version') == 1, 'Unsupported reconciliation report')
    require(report.get('primary_reconciliation_succeeded') is True,
            'Primary reconciliation did not succeed; no corrections may be proposed')
    require(report.get('status') in {'reconciled', 'reconciled_with_differences'}, 'Inconsistent report status')
    require(report.get('primary_endpoint') == p.ENDPOINT, 'Unexpected primary endpoint')
    require(set(report.get('series', {})) == set(p.SERIES), 'Both oil series are required')
    times = report.get('primary_retrieved_at')
    require(isinstance(times, list) and len(times) == 2, 'Missing primary retrieval timestamps')
    for value in times:
        p.timestamp(value)
    seeds = {}
    for series_id, item in report['series'].items():
        # The report's dictionary order does not define its series identity.
        snapshot = p.seed_snapshot(series_id)
        seed = {d: v for d, v, _ in snapshot['rows']}
        seeds[series_id] = seed
        require(item.get('seed_sha256') == digest(snapshot['payload']), 'Report seed hash differs from preserved source')
        require(item.get('numeric_count') == len(seed), 'Seed observation count mismatch')
        require(item.get('eia_series') == p.SERIES[series_id][1], 'Incorrect EIA series')
        start, end = min(seed), max(seed)
        require(item.get('first') == start and item.get('last') == end, 'Seed range mismatch')
        require(re.fullmatch('[0-9a-f]{64}', item.get('primary_sha256', '')) is not None, 'Invalid primary snapshot hash')
        comparison = item.get('primary_comparison')
        require(isinstance(comparison, dict), 'Missing primary comparison')
        absent = days(comparison['missing_from_seed'], start, end)
        omitted = days(comparison['missing_from_primary'], start, end)
        require(not absent & seed.keys() and omitted <= seed.keys(), 'Date-set claims conflict with seed')
        changed = comparison.get('discrepancies')
        require(isinstance(changed, list), 'Missing discrepancy list')
        seen = set()
        for row in changed:
            d = p.iso_day(row['date'])
            require(d in seed and d not in omitted and d not in seen, 'Invalid or duplicated discrepancy date')
            require(p.number(row['seed'])[0] == seed[d], 'Discrepancy old value differs from seed')
            require(p.number(row['primary'])[0] != seed[d], 'Reported discrepancy is not different')
            seen.add(d)
        require(comparison['shared_dates'] == len(seed) - len(omitted), 'Shared-date count mismatch')
        require(comparison['equal_values'] == comparison['shared_dates'] - len(changed), 'Equal-value count mismatch')
    has_differences = any(s['primary_comparison']['discrepancies'] or s['primary_comparison']['missing_from_seed'] or s['primary_comparison']['missing_from_primary'] for s in report['series'].values())
    require(report.get('verified') is (not has_differences), 'Verification flag contradicts differences')
    require(report['status'] == ('reconciled_with_differences' if has_differences else 'reconciled'), 'Report status contradicts differences')
    return seeds


def web_cells(document):
    require(document.get('schema_version') == 1, 'Unsupported web evidence')
    cells = {}
    for row in document['rows']:
        market = row['market']
        require(market in p.SERIES and row['url'] == p.SERIES[market][2], 'Unexpected official table source')
        start = date.fromisoformat(p.iso_day(row['week_start']))
        require(start.weekday() == 0 and len(row['values']) == 5, 'Expected Monday–Friday table row')
        require(row['evidence_kind'] == 'curated_weekly_table_transcription_not_full_page_snapshot', 'Incorrect evidence description')
        for offset, value in enumerate(row['values']):
            key = market, (start + timedelta(days=offset)).isoformat()
            parsed = p.number(value)[0]
            require(key not in cells, 'Duplicate web evidence cell')
            cells[key] = {'value': parsed, 'source_url': row['url'], 'locator': row['locator'],
                          'checked_on': row['checked_on'], 'evidence_kind': row['evidence_kind']}
    return cells


def primary_rows(db_path, report, market, seed):
    """Read the exact sanitized snapshot already fetched on the owner's PC."""
    db = p.readonly_db(db_path)
    try:
        expected = report['series'][market]['primary_sha256']
        candidates = db.execute('SELECT * FROM price_snapshots WHERE series_id=? AND source_kind=? AND sha256=?',
                                (market, 'eia', expected)).fetchall()
        require(bool(candidates), 'Audit database lacks the exact report-attested primary snapshot')
        snapshot = candidates[0]
        require(snapshot['source_url'].split('?')[0] == p.ENDPOINT, 'Audit snapshot has an unexpected primary source')
        payload = snapshot['payload']
        require(digest(payload) == expected, 'Primary payload hash mismatch')
        require(p.timestamp(snapshot['retrieved_at']) in [p.timestamp(t) for t in report['primary_retrieved_at']],
                'Primary retrieval timestamp does not match report')
        pages = json.loads(payload)
        require(isinstance(pages, list) and bool(pages), 'Missing sanitized EIA response pages')
        records = []
        totals = []
        for page in pages:
            require(page['response'].get('frequency') == 'daily', 'Primary snapshot is not daily data')
            totals.append(int(page['response']['total']))
            for row in page['response']['data']:
                require(row['series'] == p.SERIES[market][1] and row['units'] in {'Dollars per Barrel', '$/BBL', '$/bbl'},
                        'Wrong series or units in primary snapshot')
                records.append((row['period'], row['value']))
        require(all(total == len(records) for total in totals), 'Incomplete or inconsistent primary pagination')
        rows = p.validate_rows(records, start=min(seed), end=max(seed), retrieved_at=snapshot['retrieved_at'])
        require(len(rows) == len(records), 'Duplicate dates in primary payload')
        stored = [tuple(r) for r in db.execute('SELECT observation_date,value,missing_code FROM price_observations WHERE snapshot_id=? ORDER BY observation_date', (snapshot['id'],))]
        require(rows == stored, 'Audit rows disagree with retained EIA payload')
        result = {d: v for d, v, _ in rows}
        comparison = report['series'][market]['primary_comparison']
        require(set(result) - seed.keys() == set(comparison['missing_from_seed']), 'Primary-only date list mismatch')
        require(seed.keys() - result.keys() == set(comparison['missing_from_primary']), 'Seed-only date list mismatch')
        actual = {d: {'seed': seed[d], 'primary': result[d]} for d in seed.keys() & result.keys() if seed[d] != result[d]}
        expected_changes = {r['date']: {'seed': p.number(r['seed'])[0], 'primary': p.number(r['primary'])[0]} for r in comparison['discrepancies']}
        require(actual == expected_changes, 'Primary value differences do not match report')
        return result
    finally:
        db.close()


def review(report_path=DIRECTORY/'eia-verification-new.json', web_path=DIRECTORY/'web-evidence.json', primary_db=None):
    report, report_hash = load_json(report_path)
    seeds = validate_report(report)
    web, web_hash = load_json(web_path)
    cells = web_cells(web)
    result = {'schema_version': 1, 'status': 'review_required', 'report_sha256': report_hash,
              'web_evidence_sha256': web_hash, 'primary_reconciliation_succeeded_in_supplied_report': True,
              'raw_primary_snapshot_checked_here': primary_db is not None,
              'canonical_data_changed': False, 'automatic_apply_supported': False,
              'confirmed_revision_times': None, 'series': {}, 'summary': {}}
    for market, item in report['series'].items():
        seed = seeds[market]
        primary = primary_rows(primary_db, report, market, seed) if primary_db else None
        c = item['primary_comparison']
        changed, missing = [], []
        for row in c['discrepancies']:
            evidence = cells.get((market, row['date']))
            require(evidence is not None, 'Discrepancy lacks independent table evidence')
            old, api = p.number(row['seed'])[0], p.number(row['primary'])[0]
            conflict = evidence['value'] != api
            changed.append({'date': row['date'], 'seed_value': old, 'reported_API_value': api,
                'HTML_value': evidence['value'], 'reported_delta': str(Decimal(api)-Decimal(old)) if api is not None and old is not None else None,
                'classification': 'primary_source_conflict' if conflict else 'corroborated_value_difference',
                'recommended_action': 'retain_seed_pending_source_resolution' if conflict else 'propose_versioned_correction_for_approval',
                'applied': False, 'evidence': evidence,
                'revision_cause': 'Not established; cross-source disagreement is not proof of an historical revision.'})
        for origin, dates in [('API_only', c['missing_from_seed']), ('seed_only', c['missing_from_primary'])]:
            for d in dates:
                evidence = cells.get((market, d))
                require(evidence is not None, 'Missing-date claim lacks independent table evidence')
                html = evidence['value']
                if origin == 'seed_only':
                    category = 'API_omission_seed_supported_by_HTML' if html == seed[d] else 'unresolved_seed_only_date'
                    action = 'retain_seed_no_deletion'
                elif html is None:
                    category = 'HTML_unavailable_API_value_unknown' if primary is None else 'explicit_API_missing_and_HTML_blank' if primary[d] is None else 'primary_source_conflict'
                    action = 'leave_missing_no_filling'
                else:
                    category = 'numeric_HTML_observation_missing_from_seed'
                    action = 'propose_addition_for_review_no_automatic_import'
                holiday = {'12-25': 'Christmas Day', '01-01': "New Year's Day"}.get(d[5:])
                missing.append({'date': d, 'origin': origin, 'classification': category,
                    'seed_value': seed.get(d), 'API_value_state': 'not_returned' if origin == 'seed_only' else 'unknown_from_summary' if primary is None else 'explicit_missing' if primary[d] is None else 'numeric',
                    'API_value': None if primary is None or origin == 'seed_only' else primary[d],
                    'HTML_value': html, 'calendar_label': holiday,
                    'holiday_closure_confirmed': False,
                    'cause': 'No EIA closure reason established; a calendar label or blank cell does not prove why no price was published.',
                    'recommended_action': action, 'evidence': evidence})
        result['series'][market] = {'reported_shared_dates': c['shared_dates'], 'reported_matching_values': c['equal_values'],
            'primary_snapshot_sha256_in_report': item['primary_sha256'], 'primary_retrieved_at_in_report': report['primary_retrieved_at'],
            'value_differences': changed, 'date_review': missing,
            'classification_counts': dict(sorted(Counter(r['classification'] for r in changed+missing).items()))}
    all_changes = [r for s in result['series'].values() for r in s['value_differences']]
    all_dates = [r for s in result['series'].values() for r in s['date_review']]
    result['summary'] = {'seed_numeric_observations': sum(len(s) for s in seeds.values()),
        'reported_matching_values': sum(s['reported_matching_values'] for s in result['series'].values()),
        'reported_value_differences': len(all_changes), 'primary_value_conflicts': sum(r['classification']=='primary_source_conflict' for r in all_changes),
        'API_only_rows': sum(r['origin']=='API_only' for r in all_dates),
        'API_only_rows_blank_on_HTML': sum(r['origin']=='API_only' and r['HTML_value'] is None for r in all_dates),
        'seed_only_rows_supported_by_HTML': sum(r['classification']=='API_omission_seed_supported_by_HTML' for r in all_dates),
        'confirmed_numeric_seed_gaps_from_HTML': sum(r['classification']=='numeric_HTML_observation_missing_from_seed' for r in all_dates),
        'prices_changed': 0, 'prices_added': 0, 'prices_deleted': 0}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', default=str(DIRECTORY/'eia-verification-new.json'))
    parser.add_argument('--web-evidence', default=str(DIRECTORY/'web-evidence.json'))
    parser.add_argument('--primary-db', help='Optional read-only sanitized audit database; no key needed')
    parser.add_argument('--output', help='New JSON file only; refuses existing files')
    args = parser.parse_args()
    try:
        result = review(args.report, args.web_evidence, args.primary_db)
        if args.output:
            path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
        print(json.dumps(result['summary'], indent=2))
        return 0
    except (p.DataError, OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        # Untrusted files/SQL errors may contain private paths or response text.
        print('Review failed: invalid report/evidence, mismatched audit snapshot or existing destination. No prices changed.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
