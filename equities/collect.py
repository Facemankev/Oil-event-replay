"""Collect the official NVIDIA RSS feed into a new local research snapshot.

No credentials or services. Offline --input works without network. Never reuse
historical publication times as actual receipt times. XML content stays in work/.
"""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FEED = 'https://nvidianews.nvidia.com/releases.xml'
MAX_BYTES = 1024 * 1024


class SafeError(ValueError):
    pass


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}: self.hidden += 1
    def handle_endtag(self, tag):
        if tag in {'script', 'style'}: self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def plain(value, limit):
    parser = Text(); parser.feed(unescape(value or ''))
    return re.sub(r'\s+', ' ', ' '.join(parser.parts)).strip()[:limit]


def timestamp(value):
    try:
        dt = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            raise SafeError('Missing or invalid feed publication timestamp') from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise SafeError('Feed clock must include its timezone')
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def public_url(value):
    u = urlsplit(value)
    if u.scheme != 'https' or u.hostname != 'nvidianews.nvidia.com' or u.username or u.password or u.port or u.query:
        raise SafeError('Feed article URL outside the public issuer allowlist')
    return urlunsplit((u.scheme, u.netloc, u.path, '', ''))


def parse_feed(payload, received_at):
    receipt = timestamp(received_at)
    if b'\x00' in payload or len(payload) > MAX_BYTES or b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise SafeError('Unsupported or oversized XML')
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise SafeError('Invalid feed XML') from None
    atom = '{http://www.w3.org/2005/Atom}'
    items = root.findall('./channel/item') if root.tag == 'rss' else root.findall(atom + 'entry') if root.tag == atom + 'feed' else None
    if items is None or len(items) > 1000:
        raise SafeError('Unsupported feed structure or too many items')
    output, seen = [], set()
    for item in items:
        is_atom = item.tag == atom + 'entry'
        tag = lambda name: item.findtext((atom if is_atom else '') + name)
        title = plain(tag('title'), 500)
        summary = plain(tag('summary') or tag('content') if is_atom else tag('description'), 1000)
        if is_atom:
            links = [e.get('href') for e in item.findall(atom + 'link') if e.get('rel', 'alternate') == 'alternate']
            link = links[0] if links else None
        else:
            link = tag('link')
        url = public_url(link or '')
        published = timestamp(tag('published') or tag('updated') if is_atom else tag('pubDate'))
        updated = timestamp(tag('updated')) if is_atom and tag('updated') else None
        if updated and updated < published:
            raise SafeError('Feed update precedes publication')
        digest = hashlib.sha256((url + '\n' + published + '\n' + (updated or '') + '\n' + title + '\n' + summary).encode()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        output.append(dict(id='rss-' + digest, source_id='rss', url=url, title=title, summary=summary,
                           company=None, published_at=published, published_day=published[:10], precision='second',
                           updated_at=updated, actual_first_seen_at=receipt, original_vintage_verified=False,
                           capture_kind='actual_feed_receipt; first seen by this collector, not first public dissemination'))
    return dict(schema_version=1, articles=output, feed_url=FEED,
                received_at=receipt, payload_sha256=hashlib.sha256(payload).hexdigest(),
                note='A new immutable receipt snapshot. Use all retained snapshots to preserve revisions and earliest observed receipt. No trade or alert delivery is performed.')


def collect(output, input_path=None, now=None):
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / 'work').resolve()) or output.exists():
        raise SafeError('Output must be a new directory inside work/')
    if input_path is not None:
        with Path(input_path).open('rb') as f:
            payload = f.read(MAX_BYTES + 1)
    else:
        request = urllib.request.Request(FEED, headers={'User-Agent': 'MarketRipple-Research/1.0'})
        with urllib.request.urlopen(request, timeout=20) as response:
            if urlsplit(response.url).hostname != 'nvidianews.nvidia.com':
                raise SafeError('Unexpected feed redirect')
            payload = response.read(MAX_BYTES + 1)
    received = now or datetime.now(timezone.utc).isoformat(timespec='seconds')
    data = parse_feed(payload, received)
    output.mkdir(parents=True)
    (output / 'feed.xml').write_bytes(payload)
    (output / 'news.json').write_text(json.dumps(data, indent=2) + '\n')
    return dict(snapshot_created=True, articles=len(data['articles']),
                received_at=data['received_at'], payload_sha256=data['payload_sha256'],
                price_or_account_changes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Optional local original RSS/Atom file')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(collect(args.output, args.input), indent=2))
    except Exception:
        parser.exit(1, 'Company feed collection failed safely; no import or account operation. Input/network details suppressed.\n')


if __name__ == '__main__':
    main()
