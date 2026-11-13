"""Strict primary table parsers. Never infer numeric data from a blank/ND cell."""
import calendar
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
URLS = {
    'brent': 'https://www.eia.gov/dnav/pet/hist/RBRTED.htm',
    'wti': 'https://www.eia.gov/dnav/pet/hist/RWTCD.htm',
    'fx': 'https://www.federalreserve.gov/releases/h10/hist/dat00_uk.htm',
}
COLUMNS = ['date', 'value', 'status', 'locator']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def numeric(text, fx=False):
    require(isinstance(text, str) and re.fullmatch(r'-?\d+\.\d{2,4}', text), 'Invalid source numeric cell')
    value = Decimal(text)
    require(value.is_finite() and (not fx or value > 0), 'Invalid exchange rate')
    return value


def table_rows(kind, cells):
    label = ' '.join(cells[0].split())
    if kind == 'fx':
        match = re.fullmatch(r'(\d{1,2})-([A-Z]{3})-(\d{2})', label)
        if not match:
            return []
        require(len(cells) == 2, 'Expected a date and a Federal Reserve rate')
        day = date(2000 + int(match[3]), MONTHS[match[2].lower()], int(match[1]))
        text = cells[1].strip()
        if text != 'ND':
            numeric(text, fx=True)
        return [dict(date=day.isoformat(), value='' if text == 'ND' else text,
                     status='ND' if text == 'ND' else 'numeric', locator=label)]
    match = re.fullmatch(r'(\d{4})\s+([A-Za-z]{3})-\s*(\d{1,2})\s+to\s+([A-Za-z]{3})-\s*(\d{1,2})', label)
    if not match:
        return []
    require(kind in {'brent', 'wti'} and len(cells) == 6, 'Expected an EIA week and exactly five weekday cells')
    monday = date(int(match[1]), MONTHS[match[2].lower()], int(match[3]))
    friday = monday + timedelta(days=4)
    require(monday.weekday() == 0 and friday.month == MONTHS[match[4].lower()] and friday.day == int(match[5]), 'EIA week/date mismatch')
    result = []
    for offset, text in enumerate(cells[1:]):
        text = text.strip()
        if text:
            numeric(text)
        result.append(dict(date=(monday + timedelta(days=offset)).isoformat(), value=text,
                           status='numeric' if text else 'blank_primary_cell',
                           locator=f'Week of {monday.isoformat()}; {calendar.day_abbr[offset]}'))
    return result


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.cells, self.text, self.in_cell = [], [], [], False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells = []
        if tag in {'td', 'th'}:
            self.text, self.in_cell = [], True

    def handle_data(self, text):
        if self.in_cell:
            self.text.append(text)

    def handle_endtag(self, tag):
        if tag in {'td', 'th'} and self.in_cell:
            self.cells.append(' '.join(''.join(self.text).split()))
            self.in_cell = False
        if tag == 'tr' and self.cells:
            self.rows.append(self.cells)


def parse_html(kind, payload, start, end):
    require(len(payload) <= 10_000_000, 'Primary response exceeds size limit')
    html = payload.decode('utf-8-sig')
    visible = ' '.join(re.sub('<[^>]+>', ' ', html).split())
    if kind == 'fx':
        require('Historical Rates for the Great British Pound' in visible and 'Rates in U.S. dollars per Great British Pound' in visible, 'Unexpected FX unit or instrument')
    else:
        require(('Europe Brent Spot Price FOB' if kind == 'brent' else 'Cushing, OK WTI Spot Price FOB') in visible and 'Dollars per Barrel' in visible, 'Unexpected oil unit or instrument')
    parser = Tables()
    parser.feed(html)
    records = {}
    for cells in parser.rows:
        for row in table_rows(kind, cells):
            if start <= row['date'] <= end:
                require(row['date'] not in records, 'Duplicate primary date')
                records[row['date']] = row
    require(records, 'No primary table observations parsed')
    # A partial capture must fail instead of turning missing sections into gaps.
    expected = date.fromisoformat(start)
    while expected <= date.fromisoformat(end):
        if expected.weekday() < 5:
            require(expected.isoformat() in records, 'Incomplete primary weekday capture')
        expected += timedelta(days=1)
    return [records[d] for d in sorted(records)]


def csv_bytes(rows):
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue().encode()


def load_sources():
    manifest = json.loads((ROOT / 'verification/sources/manifest.json').read_text())
    require(manifest['schema_version'] == 1 and set(manifest['sources']) == set(URLS), 'Unsupported primary snapshot manifest')
    sources = {}
    for kind, item in manifest['sources'].items():
        path = (ROOT / item['file']).resolve()
        require(path.parent == ROOT / 'verification/sources' and item['url'] == URLS[kind], 'Unexpected primary source path/URL')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == item['sha256'], 'Primary CSV fingerprint changed')
        rows = list(csv.DictReader(io.StringIO(raw.decode())))
        require(len(rows) == item['rows'] and len({r['date'] for r in rows}) == len(rows), 'Duplicate or incomplete snapshot')
        require([r['date'] for r in rows] == sorted(r['date'] for r in rows), 'Unordered source observations')
        for row in rows:
            date.fromisoformat(row['date'])
            require(date.fromisoformat(row['date']).weekday() < 5, 'Unexpected source weekday')
            if row['status'] == 'numeric':
                numeric(row['value'], fx=kind == 'fx')
            else:
                require(row['value'] == '' and row['status'] == ('ND' if kind == 'fx' else 'blank_primary_cell'), 'Invalid missing-value classification')
        require(sum(r['status'] == 'numeric' for r in rows) == item['numeric'], 'Numeric coverage mismatch')
        expected = date.fromisoformat(item['first'])
        captured = {r['date'] for r in rows}
        while expected <= date.fromisoformat(item['last']):
            if expected.weekday() < 5:
                require(expected.isoformat() in captured, 'Uncaptured primary weekday')
            expected += timedelta(days=1)
        sources[kind] = rows
    return manifest, sources
