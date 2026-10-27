# Market Ripple / Oil-event-replay

Beginner-friendly historical market research, served as a static website.

Run locally: `python3 -m http.server 8000`, then open http://localhost:8000.
No build step or API keys. Existing seven oil replays remain available below the
multi-market lab. The lab includes Apple and Brent prices around the Brexit
referendum result, with matching dates, visible sources and optional CSV imports.
Other event types are catalogued but need imported histories to compare.

- Sources and verification limits: [data/SOURCES.md](data/SOURCES.md)
- Database and future assistant design: [research/ARCHITECTURE.md](research/ARCHITECTURE.md)
- Tests: `node --test tests/research.test.cjs`
- Browser regression: `python3 tests/browser_test.py` (requires Python Playwright and Chromium)

No prices are invented. Historical changes do not establish causation or predict
trading outcomes. Imports remain in memory until reload or clearing.

## Local historical price database (DAT-3)

Import the existing 20-year Brent/WTI CSVs into SQLite with Python only:

```sh
python3 -m historical --db work/prices.sqlite backfill
python3 -m historical --db work/prices.sqlite update
python3 -m historical --db work/prices.sqlite query --series wti --start 2020-04-17 --end 2020-04-24
```

Actual seed counts: **5,231 Brent + 5,137 WTI = 10,368 prices**, spanning
2006-01-03–2026-10-20. These remain secondary EIA-derived snapshots until primary
reconciliation. Browse the SQLite-generated static export at [history.html](history.html).
See [setup, provenance, queries, tests and EIA update instructions](historical/README.md)
and the [actual import report](historical/IMPORT_REPORT.json).
No paid service or live trading is introduced; the existing dashboard stays static.
