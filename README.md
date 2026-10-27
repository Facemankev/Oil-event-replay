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
It runs from a static export and does not depend on draft PR #12 or change the
existing lab. Build the local event database and export with:

```sh
python3 -m world_events validate
python3 -m world_events --db work/world-events.sqlite import
python3 -m world_events --db work/world-events.sqlite compare --event ike-2008-galveston
python3 -m world_events --db work/world-events.sqlite export
```

See [setup, exact sources and methodology](world_events/README.md). Unknown
first-public times remain unknown; these descriptive comparisons are not causal
estimates, forecasts, executable trading returns or point-in-time-safe backtests.
