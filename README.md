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

## Sourced historical world events (EVT-1)

The separate [event research view](event-research.html) contains 24 sourced events,
with occurrence/publication precision, evidence and reproducible Brent/WTI windows.
It runs from a static export and preserves the existing lab. Build the local event database and export with:

```sh
python3 -m world_events validate
python3 -m world_events --db work/world-events.sqlite import
python3 -m world_events --db work/world-events.sqlite compare --event ike-2008-galveston
python3 -m world_events --db work/world-events.sqlite export
```

See [setup, exact sources and methodology](world_events/README.md). Unknown
first-public times remain unknown; these descriptive comparisons are not causal
estimates, forecasts, executable trading returns or point-in-time-safe backtests.

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

## Use the two databases together

Keep the SQLite files separate (they have deliberately different schema versions).
Pass the historical database's export to the event comparison adapter:

```sh
python3 -m historical --db work/prices.sqlite backfill
python3 -m historical --db work/prices.sqlite export --output work/prices.json
python3 -m world_events --db work/world-events.sqlite import
python3 -m world_events --db work/world-events.sqlite compare --event ike-2008-galveston --prices-json work/prices.json
python3 -m world_events --db work/world-events.sqlite export --prices-json work/prices.json --output work/combined-events.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The integration regression imports the actual 10,368 prices and 24 events,
checks safe repeats and database integrity, and verifies all 48 benchmark
results against the original CSV method. Source metadata travels with the export.
These are daily spot-price associations, not executable trading returns.
Primary EIA reconciliation still requires a free key and network access to
`api.eia.gov`; original price publication/vintage times remain unavailable.

## Gold × Desk visual preview

[Open the public desktop/iPad branding preview](https://market-ripple-gold-desk-review.royaltulip9.chatgpt.site)
([original full-screen example](https://market-ripple-gold-desk-review.royaltulip9.chatgpt.site/example.html)).
This separate static preview preserves Brendan's original example and stylesheet
byte-for-byte; it does not restyle the existing dashboard. Local copy:
[preview/gold-desk/](preview/gold-desk/). See its README for provenance.

Browser regressions (Python Playwright plus Chromium at `/usr/bin/chromium`):

```sh
python3 tests/browser_test.py
python3 tests/historical_browser_test.py
python3 tests/world_events_browser_test.py
python3 tests/branding_preview_browser_test.py
```

## Historical event matching (MAT-2 / MAT-3)

Open [the matching prototype](matching/) to describe an oil-relevant event or
select a historical example, inspect ranked analogues and compare 1/3/7/14/30
reported-observation-day reactions. No AI or price outcomes influence ranking.
Price verification is currently **blocked**; seed-based reactions are labelled
provisional and can be hidden with the primary-only option. Unknown severity,
first-public times and missing prices remain unknown. This is historical
research, not a trading recommendation or an estimate of potential earnings.
See [setup, deterministic rules, EIA configuration and tests](matching/README.md)
and the [validation report](matching/validation-report.json).
