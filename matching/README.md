# Historical matching prototype (MAT-2 / MAT-3)

Open **matching/index.html through an HTTP server**, or the separate preview URL
[open the isolated preview](https://market-ripple-event-matching.royaltulip9.chatgpt.site/matching/) (sign in with the same ChatGPT account). This is functioning deterministic research software, not
monitoring, a forecast or a trading system. The existing dashboard content/replay logic, research views, paper-trading branch
and original branding preview are preserved. One CSS width constraint fixes an
inherited dashboard mobile grid overflow found by the combined CI browser suite.

## Reproduce the data and run

Python standard library and Node only; no paid infrastructure or keys for the
provisional prototype:

```sh
python3 -m historical --db work/matching-prices.sqlite backfill
python3 -m world_events --db work/matching-events.sqlite import
python3 -m matching.validate_prices --db work/matching-prices.sqlite
python3 -m matching.build
python3 -m http.server 8000
# Open http://localhost:8000/matching/
```

The builder **reads** the DAT-3 and EVT-1 databases separately. It never changes
those schemas or the existing static exports. The committed catalogue contains
24 events and 240 reaction windows (24 × 2 benchmarks × 5 horizons), all currently
provisional, using 5,231 Brent and 5,137 WTI observations. No invented observations
or probability estimates are included. Rebuilding against the same database
reproduces the catalogue byte-for-byte. A fresh import has fresh retrieval times
and snapshot IDs, so its provenance bytes legitimately differ; numeric results
and classifications reproduce.

## Primary-price verification: blocked, not complete

[validation-report.json](validation-report.json) audits exact pinned seed hashes,
counts, coverage, explicit missing markers, cross-market differences and absent
weekdays. [ACCESS_ATTEMPT.json](ACCESS_ATTEMPT.json) records the actual failed
primary-source access attempts on 29 October 2026. No `EIA_API_KEY` is configured;
the environment proxy also blocks the API and EIA download host. Official EIA
HTML and documentation readable through a browser are not full database
reconciliation. Missing weekday causes and possible value revisions are unknown.

- Numeric observations: Brent **5,231**, WTI **5,137**, 2006-01-03–2026-10-20.
- **5,068** common numeric dates; Brent-only **163**, WTI-only **69**.
- Absent weekdays within each coverage: Brent **195**, WTI **289**. These lists
  include possible holidays/publication closures; they are not confirmed errors.
- No explicit missing-value markers in the seeds. No full primary discrepancy
  count is known. Existing local seed DB: 2 snapshots / 10,368 versions, integrity
  `ok`, zero additional versions. This does not prove the seeds were never revised.

EIA's [API documentation](https://www.eia.gov/opendata/documentation.php) explains
registration and pagination. Register for a free key at
https://www.eia.gov/opendata/register.php . Configure it **only in your local shell**
on a machine with permitted HTTPS access to `api.eia.gov`:

```sh
# Bash: hidden prompt; the key is not included in command history or arguments.
read -r -s -p 'EIA key: ' EIA_API_KEY
export EIA_API_KEY
python3 -m matching.validate_prices --attempt-primary --db work/matching-prices.sqlite --output work/eia-validation.json
unset EIA_API_KEY
```

Never paste the key into HTML, JavaScript, JSON, a URL in a report, GitHub comments
or a committed file. If automation is added later, use an encrypted Actions secret,
not a repository variable or checked-in environment file. This PR adds no scheduled
requests or credentials to CI.

The authenticated command uses the existing strict paginated EIA adapter for
`RBRTE` and `RWTC`, requests each seed's full inclusive coverage, compares Decimal
values/date sets, and lists every discrepancy and date missing from either source.
It reports `primary_reconciliation_succeeded` separately from `verified` (all seed
values/date sets agree). Disagreements may be revisions or mirror errors; their
cause and revision time stay unknown. Both sources are retained in a **separate**
`work/eia-reconciliation.sqlite`, with sanitized response snapshots/hashes. A failed
fetch never imports substitute prices or claims success. Exit 2 means verification
is blocked or incomplete. Do not publish reports before checking for credentials.

After a successful live reconciliation, inspect discrepancies and rebuild using
actual primary-source observations:

```sh
python3 -m matching.build --prices-db work/eia-reconciliation.sqlite --events-db work/matching-events.sqlite --output work/primary-catalog.json
```

Primary wins per date, but any remaining seed-only date makes its entire reaction
window provisional. Do not overwrite the reviewed catalogue until reviewing the
report and new outputs. Current EIA values still do not establish the original
publication timestamps or vintages needed for a point-in-time backtest.

## Matching rules, without using hindsight to rank

The same pure JavaScript module runs in Node tests and the browser. Input text
is a label, not AI extraction. Explicit fields drive matching; unknowns remain
unknown. Users can supply category, Brent/WTI, location, event detail, occurrence
date, public-information date and their own severity label.

- Require the same category and affected commodity. Exclude the query record,
  events occurring on/after the query public date, and supporting publications
  on/after that date. Same-day ordering is conservatively unavailable.
- Category: 3 points. Commodity: 2. Matching event detail: 4. Location: up to 2,
  proportional to normalized input words shared with the recorded geography.
  Matching words are disclosed; this is not a geographic distance model.
- Known production cuts, increases and unchanged targets cannot match an opposite
  policy action. Other different mechanisms are weak, explicitly labelled
  broad-category resemblances. Unknown details add no points. Algiers and Vienna 2016 retain neutral production-target labels because their retained cards state targets rather than a comparable direction.
- Severity earns **zero** points: the 24 records lack a sourced comparable scale.
  User severity is never fabricated onto a historical event.
- Closer means same detail and location overlap; Partial means same detail;
  Weak means category/commodity only. Sort score descending, then stable ID.
  No price move, direction, significance threshold or future reaction enters rank.

This is a small curated sample, not a representative or exhaustive event set.
OPEC announcements from one episode can be correlated. Shared categories and
countries do not establish equivalent supply exposure. There is no statistical
probability, win rate or claim that the largest move will recur.

## Reaction method and evidence

Use the **supporting-publication** date, converting a printed offset timestamp to
UTC where available. Never substitute occurrence for unknown publication timing.
The four unestablished first-public dates stay unestablished. Saudi's 2019 attacks
therefore anchor to the EIA article on 23 September, not the occurrence on the 14th.

For each benchmark independently, baseline is its last reported observation
strictly before the anchor day. Endpoints are observation 1, 3, 7, 14 and 30
strictly after that day. The entire anchor day is excluded because the price
fixing/publication clock is unknown. These are **reported observation days**,
not a verified exchange trading calendar; weekend/holiday rows are not invented.
Different Brent/WTI dates can give different endpoints. Unlike the existing EVT-1
shared-calendar method, MAT uses each benchmark's own reporting calendar, clearly
labelled in the page and catalogue. Existing EVT-1 results are unchanged.

Absolute move is end minus baseline in USD/barrel. Percentage is
`(end / baseline - 1) × 100`, rounded to four decimal places in the export, two
on the page. Zero/negative baselines retain absolute differences, with percentage
undefined. Missing baseline, an explicit missing report, insufficient tail,
a baseline older than 14 calendar days or an excessive endpoint gap blocks that
window. Undetected absent reporting dates cannot be ruled out until primary
reconciliation. No filling/interpolation occurs. Results on/after a historical
query's public date are withheld. The downloadable library contains present-day
historical vintages and must never be treated as an as-of backtest archive.

Each window retains the exact baseline, all included observations, endpoint,
source IDs, URL, retrieval time, revision and hash. All included rows must be
primary EIA for a primary badge. A primary-only view hides provisional numbers.
Evidence is Limited today. Moderate requires closer match details/location,
five primary windows and minute-level event evidence; Strong is unavailable
without comparable severity and original price publication times. Strength is
an evidence rubric, not predictive confidence. Source cards are curated
bibliographic evidence, not full archived source pages.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
python3 tests/matching_browser_test.py
python3 tests/browser_test.py
python3 tests/historical_browser_test.py
python3 tests/world_events_browser_test.py
python3 tests/branding_preview_browser_test.py
```

Browser tests require Python Playwright and Chromium at `/usr/bin/chromium`.
They check inputs, rankings, self/future exclusion, source gates, no-match states,
XSS-safe rendering, missing files and desktop/iPad/mobile light/dark layouts.
Physical iPad Safari is not claimed. The stylesheet is copied byte-for-byte from
Brendan's Gold × Desk skill; only page-specific layout uses the existing tokens.
