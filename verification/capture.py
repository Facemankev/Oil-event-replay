"""Optional fresh, no-key primary download. Writes ONLY a new local directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from .sources import URLS, ROOT, csv_bytes, parse_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--start', default='2006-01-02')
    parser.add_argument('--end', default='2026-11-06')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if not output.is_relative_to(ROOT / 'work'):
        raise ValueError('Capture output must be a new directory under work/')
    output.mkdir(parents=True, exist_ok=False)
    receipts = {}
    for kind, url in URLS.items():
        request = Request(url, headers={'User-Agent': 'MarketRipple historical research; no trading'})
        with urlopen(request, timeout=45) as response:
            if response.url != url:
                raise ValueError('Unexpected primary redirect; review before retaining data')
            raw = response.read(10_000_001)
        rows = parse_html(kind, raw, args.start, args.end)
        data = csv_bytes(rows)
        (output / (kind + '.csv')).write_bytes(data)
        # Original pages may contain unrelated site contact details; keep them
        # local, outside the public source snapshot. No credential is requested.
        (output / (kind + '.html')).write_bytes(raw)
        receipts[kind] = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                          'http_sha256': hashlib.sha256(raw).hexdigest(),
                          'csv_sha256': hashlib.sha256(data).hexdigest(), 'rows': len(rows)}
    (output / 'manifest.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    main()
