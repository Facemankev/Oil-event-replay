# EVT-1: sourced world-event database

A working first milestone for [issue #13](https://github.com/Facemankev/Oil-event-replay/issues/13):
24 curated events, an immutable-version SQLite importer, strict temporal/evidence
validation, deterministic oil-price comparisons and a separate static research page.
No paid infrastructure, API key, live trading, AI recommendation or network request
is needed to reproduce it. Existing dashboard files and draft PRs #12/#2 are not
changed by this implementation.

## Run it

From the repository root, with Python 3.10+ and the standard IANA timezone database
(install the Python `tzdata` package only if your OS lacks it):

```sh
python3 -m world_events validate
python3 -m world_events --db work/world-events.sqlite import
python3 -m world_events --db work/world-events.sqlite import
python3 -m world_events --db work/world-events.sqlite list --category weather
python3 -m world_events --db work/world-events.sqlite compare --event ike-2008-galveston
python3 -m world_events --db work/world-events.sqlite export
python3 -m http.server 8000
```

Open `http://localhost:8000/event-research.html`. The committed JSON export works
on GitHub Pages with no database server or build step. This PR deploys nothing.
The original dashboard remains at `index.html` and is unchanged. SQLite files
and temporary reports stay in the ignored `work/` folder.

The actual import inserts **24 events**; repeating it reuses **24** with **0 new
versions**. The default export completes **24 two-benchmark comparisons** (48
benchmark results). It includes six categories: weather (6), production policy
(8), sanctions (5), conflict (3), strategic stocks (1) and demand shock (1).
Occurrence dates span 2008-09-01 through 2023-10-07. The price inputs are the
5,231 Brent and 5,137 WTI rows already on main (2006-01-03–2026-10-20).

## Source evidence and what “first public” means

[`seed.json`](seed.json) contains all 24 records and their exact source URLs,
publishers, stable references, checked dates, evidence grades and short paraphrases.
The six NHC sources are archived, contemporaneous landfall bulletins. Eight OPEC
sources are dated policy releases. The remaining records use dated Treasury,
Council of the EU, archived White House, United Nations, EIA, DOE and WHO records.
There are **20 primary releases, 3 institutional reports and 1 retrospective EIA
report**. No inference of a price reaction was used as evidence that an event
happened. Selection is curated and non-exhaustive, not a statistically representative
sample of oil news or all major shocks.

The source facts were inspected via official publisher text returned by web
search/open on 27 October 2026. Some OPEC pages return access errors on direct
opening; their indexed publisher text was inspected instead. No scraping pipeline,
full-article republication or complete source-page snapshot is claimed. Dated
bulletin identifiers, press release references and the official White House archive
are retained. Other web pages may change or disappear. The bibliographic facts and
short original paraphrases are retained as **curated evidence cards**, hashed with
SHA-256; these hashes do **not** authenticate the full external pages. Publisher
rights in linked source text remain with its publisher.

A clock reading is not the same as proof of the globally first news report:

- Six NHC bulletins provide **minute-level printed publication/issuance stamps**.
  They are the earliest supporting landfall confirmations located in this curation,
  not proof that earlier news, forecasts or observations did not exist.
- Fourteen other originating releases have **date-only** timing. Clock and
  publication timezone remain null. Meeting start times, speech start times and
  effective implementation dates are not substituted for disclosure time.
- Four events have **unestablished first-public timing**: the 2012 EU Iran measures
  (evidenced by a same-day US response), the Saudi oil-facility attacks (retrospective
  EIA report), and the Ukraine/Israel escalations (institutional corroboration).
  Their `first_public` timestamps and dates remain null. A separately dated
  supporting publication still supplies an explicit descriptive research anchor.

The dataset claims **zero verified global-first disclosures**. For the 20
originating-release records, `first_public.status=earliest_located_not_exhaustive`
explicitly scopes the field to the supporting publication found here. All exact
unknowns are null, not midnight. For future backtests, first-public evidence needs
further archival review and original price-publication/vintage times must also be
established. All current comparisons are `backtest_eligible=false` and
`point_in_time_safe=false`.

Examples of timing care:

- Ike's bulletin is printed 02:30 CDT; its contemporaneous estimated landfall is
  about 02:10 CDT. These are distinct. NHC estimates can differ from later best tracks.
- Harvey's 22:00 CDT on 25 August is 03:00 UTC on **26 August**; date conversion
  must not silently leave it on the earlier UTC day.
- Ida's archive filename contains 1653, while its printed bulletin says 1155 CDT
  (1655 UTC). The record uses the printed header and retains the discrepancy note.
- The White House transcript's 14:13 speech start is not the exact time of the
  withdrawal sentence or web publication. It remains date-only here.
- The EU sixth-package page prints 09:50, but the inspected evidence does not
  establish that clock's timezone; it remains date-only. Formal adoption is not
  the earlier political agreement or later implementation.
- The Saudi attack occurred on 14 September 2019; its selected EIA report is dated
  **23 September**. The default comparison uses the latter, with a visible nine-day
  evidence lag. It does not pretend this report existed before the initial reaction.

## Record schema and validation

The executable validator is `events.validate_record`; `schema.sql` is the runnable
SQLite migration. Seed JSON has `schema_version=1` and an `events` array.

| Field | Meaning / rules |
| --- | --- |
| `id`, `revision` | Stable ASCII slug; positive integer revision |
| `title`, `description`, `category` | Neutral factual event, not an asserted causal price explanation; category is validated |
| `geography`, `affected_commodities`, `relevance` | Occurrence/affected region, Brent/WTI scope and inclusion rationale |
| `occurred` | Local date, optional offset timestamp, IANA timezone or null, precision and explicit approximation flag |
| `first_public` | Earliest located publication or null, precision, scoped status and supporting evidence ID; never a guaranteed global-first claim |
| `public_evidence` | Explicit supporting-publication reference used for descriptive comparisons |
| `evidence[]` | Publisher, HTTPS URL, optional archive URL, stable reference/locator, quality, publication timing, checked-on date, paraphrase, reuse note and card hash |
| `uncertainty`, `reviewed_on` | Required limitations and curation date |

Timestamps must carry an explicit UTC offset and match the named IANA timezone,
including daylight-saving offsets. Naive/ambiguous local clock strings fail; an
explicit valid DST-fold offset is allowed. Day precision must have no clock.
Unknown first-public timing must have no date/time/zone. A source's stated
publication cannot be after its checked date. Institutional/retrospective sources
cannot masquerade as the originating first-public release. Missing references,
invalid categories/quality, duplicate IDs and altered evidence hashes fail.
An announcement may legitimately precede implementation/occurrence; the validator
does not impose a false universal occurrence-before-publication rule.

SQLite `user_version=1301` identifies this **separate event database**. Existing
unrelated databases and the DAT-3 price database are refused. `world_event_versions`
stores the full canonical JSON, hash, occurrence/public fields and actual importer
UTC time for each event revision; indexes support date/category lookup.
`world_events_current` selects the highest revision. `world_event_import_runs`
records no-op and successful imports. Each import is atomic. Reusing the same
revision/hash is a no-op; changing an existing revision fails. Corrections require
the next integer revision, retaining prior payload/evidence rather than overwriting
history. An older identical version cannot replace the current revision.
Importer timestamps are our knowledge time, not the source's original disclosure.
These are local reproducibility records, not a tamper-proof third-party audit.

## Reproducible event-to-price method

`research.PriceStore.range(market,start,end)` is the boundary returning ordered
actual `(date, Decimal-or-null)` observations plus provenance. No DAT-3 module or
other unmerged code is imported.

1. Choose the explicitly referenced supporting publication, not the occurrence
   date. If its timestamp is precise, use its **UTC calendar date**. With only a
   publisher date, retain that labelled date and flag unknown clock/timezone.
   If even its date is unknown, return `publication_time_unknown` with no result.
2. Search at most 60 calendar days on either side. Intersect **actual numeric
   Brent and WTI dates**. Retain/report one-series-only dates and explicit missing
   codes as missing; never invent weekends, holiday sessions or prices.
3. Exclude the entire publication-anchor date. Select the last N shared observations
   before it and first M after it (defaults N=M=5, configurable 1–20 via `--before`
   and `--after`). Both markets use identical dates. Insufficient windows return
   an explicit status with no percentage or substitute price.
4. Baseline is the last pre-window price, end is the last post-window price.
   Absolute change is end minus baseline. Percentage change is
   `(end / baseline - 1) * 100`, rounded to four decimal places. Also report
   pre-window and post-window percentage changes and every actual observation.
   Percentage changes from a zero/negative baseline are undefined, never fabricated;
   signed/zero observations and absolute changes remain available.
5. Record methodology version `shared-observation-windows-v1`, event revision/hash,
   source evidence, all chosen dates, actual price-file hashes and all caveats.

Daily observation times, publisher-timezone uncertainty, forecast anticipation,
information leakage before official releases, price-vintage revisions and concurrent
events all limit interpretation. Excluding the labelled publication date is an
explicit reproducible **research assumption**, not proof of precise market-close
alignment or a leakage-free backtest. The before-to-after number spans both
windows and the omitted day; it is not the isolated effect of the event.
There is no causal model, statistical significance claim or trading recommendation.

Actual example, Ike landfall bulletin:

| Benchmark | Baseline 2008-09-12 | End 2008-09-19 | Change |
| --- | ---: | ---: | ---: |
| Brent | 94.37 | 93.46 | -0.9643% |
| WTI | 101.19 | 104.05 | +2.8264% |

Both series use shared pre dates 8–12 September and post dates 15–19 September,
from the existing seed observations. This week also contains major financial-crisis
news, so the numbers must not be attributed to Ike. The source-publication anchor
is Saturday 13 September. See `RUN_REPORT.json` and the full static export for
other actual calculations and the event-specific uncertainties.

## Coordination with draft PR #12

Default `CSVPrices` reads only the already-merged `data/historical` files, using
this PR's independently pinned `prices-manifest.json`. If those files change,
review/update the manifest explicitly; do not silently change historical results.
Their EIA-derived secondary-source limitation remains visible. Negative WTI prices
are allowed. This PR does not copy, cherry-pick, modify or merge PR #12's code.

An optional `JSONPrices` adapter accepts the documented external range/static-export
shape (`schemaVersion:1`, two `series` objects with `series`, `unit:"USD/barrel"`,
`sources` and `observations` containing `date`, `value`, `snapshot_id`). It supports
full IDs or per-series short IDs resolved through `sources`. Query results can be
wrapped in the same aggregate object. Supply a file only when available:

```sh
python3 -m world_events --db work/world-events.sqlite compare --event ike-2008-galveston --prices-json /path/to/supplied-price-export.json
```

The supplied file's SHA-256 and source metadata are retained in the result.
Missing markets, wrong units, unresolved source references, duplicate dates and
invalid prices fail. This interface is contract-tested against real seed values
wrapped in that shape, without fetching or depending on unmerged code. All current
price adapters conservatively keep backtest eligibility false.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_world_events.py' -v
node --test tests/research.test.cjs
python3 tests/browser_test.py
python3 tests/world_events_browser_test.py
```

Unit/CLI checks need no network or secrets. Browser tests need Python Playwright
and `/usr/bin/chromium`; they cover actual results, late/unknown disclosures,
category selection, source display, safe text/links, light/dark and mobile/iPad
viewports. Physical iPad/Safari validation is not claimed. CI runs validation,
actual import/repeat/compare/export and deterministic committed-export equality
without external services. `RUN_REPORT.json` records the actual data counts/results.

Next work should strengthen archival first-disclosure evidence and price vintages,
then add point-in-time event-linked research. It must not silently promote this
curated descriptive seed into an unbiased trading backtest. PR #12 and PR #2
remain separate and unmerged.
