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
