# DAT-3: historical Brent and WTI database

This is the working first ingestion milestone for [issue #10](https://github.com/Facemankev/Oil-event-replay/issues/10).
It uses Python's standard library and a local SQLite file. No service signup,
paid infrastructure, JavaScript build, broker connection or live trading is
introduced. The older `research/schema.sql` remains a design document: this
working database has its own versioned migration in `historical/schema.sql`.

## Run it

Use Python 3.10+ with SQLite 3.25+ (window functions). From the repository root:

```sh
python3 -m historical --db work/prices.sqlite backfill
python3 -m historical --db work/prices.sqlite update
python3 -m historical --db work/prices.sqlite query --series wti --start 2020-04-17 --end 2020-04-24
python3 -m historical --db work/prices.sqlite export --output data/historical/prices.json
python3 -m http.server 8000
```

Open `http://localhost:8000/history.html`, or follow the new historical-export
link in the research lab. The default `seed` source imports the exact CSV files
already merged into main, checked against `seeds.json`. It does **not** fetch new
primary prices or relabel the mirror as verified EIA data. A changed seed hash
fails until a reviewer explicitly updates the manifest and source evidence.
SQLite files stay in the ignored `work/` directory; no generated binary database
is committed. The committed static JSON is an actual export from the demonstrated
SQLite database, not a hand-written substitute.

To demonstrate incremental additions entirely offline with actual seed rows:

```sh
python3 -m historical --db work/incremental.sqlite backfill --end 2026-09-30
python3 -m historical --db work/incremental.sqlite update --overlap-days 30
```

Both sources honor inclusive `--start`/`--end` bounds. Updates begin at each series'
last reported date minus the overlap (default 30 calendar days), bounded by
`--start` (default 2006-01-01). A large prior explicit-missing date also participates
in the watermark; the overlap is intended to pick up recent corrections. Run a
full backfill periodically to discover revisions older than that overlap.
Only explicit missing observations retract earlier values; dates absent from a
partial response do not delete existing records. There is no fill, extrapolation
or assumed holiday calendar.

## Actual import results

See [`IMPORT_REPORT.json`](IMPORT_REPORT.json) for the actual command summaries,
snapshot identities, hashes, query example and database integrity result.

| Series | Numeric prices | First | Last | Source |
| --- | ---: | --- | --- | --- |
| Brent | 5,231 | 2006-01-03 | 2026-10-20 | Existing EIA-derived secondary seed |
| WTI Cushing | 5,137 | 2006-01-03 | 2026-10-20 | Existing EIA-derived secondary seed |
| Total | **10,368** | | | |

The full import contains two source snapshots and 10,368 observation versions.
Repeat backfills/updates of the same covered source rows add no duplicate versions.
In the separate incremental demonstration, coverage through September contains
5,217 Brent and 5,123 WTI prices. Update adds **14 per series**, rechecks **22 per
series** in the overlap and reaches the counts above; there are zero revisions in
that real-data example. These results do not imply a successful primary-source
fetch. No EIA key is configured in this execution environment, and its network
policy does not currently allow `api.eia.gov`. Primary reconciliation remains
an explicit follow-up, not an invented verification claim.

## Verified EIA routes, access and cadence

Official documentation checked 27 October 2026:

| Benchmark | API v2 series facet | Legacy daily series | Official table |
| --- | --- | --- | --- |
| Europe Brent spot FOB | `RBRTE` | `PET.RBRTE.D` | https://www.eia.gov/dnav/pet/hist/RBRTED.htm |
| Cushing WTI spot FOB | `RWTC` | `PET.RWTC.D` | https://www.eia.gov/dnav/pet/hist/RWTCD.htm |

The [EIA browser](https://www.eia.gov/opendata/browser/petroleum/pri/spt)
identifies the `petroleum/pri/spt` spot-price route. Requests use
`https://api.eia.gov/v2/petroleum/pri/spt/data/`, `frequency=daily`, `data[0]=value`,
`facets[series][0]=RBRTE` or `RWTC`, ascending `period`, `offset` and `length=5000`.
Units are USD per barrel; other units, series or frequencies are rejected.
[Technical documentation](https://www.eia.gov/opendata/documentation.php) requires
a free API key and documents the 5,000-row JSON limit and pagination. Large
backfills paginate explicitly; totals changing mid-fetch, duplicate dates,
truncated pages, unrecognized warnings or malformed data abort the whole import.
The documented 5,000-row pagination warning is allowed only with the other
completeness checks. Requests have a timeout and size bounds, do not follow
redirects, and do not retry or fall back silently.

The observations are **daily**, but publication is delayed. The official daily
tables checked here show a release of 21 October 2026 and next release of
28 October 2026: weekly publication at this check, not a promise of daily/live
availability. Check EIA's posted schedule when operating updates. Neither a
calendar observation date nor our retrieval time establishes when a historical
value was first published. Revisions may occur.

### Primary-source backfill / incremental update

Register for a free key at https://www.eia.gov/opendata/register.php. Set
`EIA_API_KEY` privately in your shell, permit HTTPS to `api.eia.gov`, then run:

```sh
python3 -m historical --db work/prices.sqlite backfill --source eia --start 2006-01-01 --end 2026-10-27
python3 -m historical --db work/prices.sqlite update --source eia --overlap-days 30
python3 -m historical --db work/prices.sqlite export
```

Both series are fully fetched and validated **before either is written**.
Primary EIA snapshots take precedence over seed values, even if a seed is
imported later. Comparison/revision counts make disagreement visible. The API
adapter has automated contract fixtures, not a claim of an authenticated production
integration check. The missing-key attempt was actually run and failed closed.
No GitHub Actions secret is needed for the seed tests. If you later run the EIA
commands in a manual Actions job, add a repository secret named `EIA_API_KEY` and
pass it only to that job's environment; this PR adds no scheduled fetch/deployment.
EIA echoes keys in response request metadata: stored pages are recursively
credential-redacted before hashing and saving; errors suppress upstream URLs and
response details. No key is embedded in public browser code, logs or snapshots.

## Schema, safety and queries

`PRAGMA user_version=1` identifies the migration. An unrelated nonempty database
or unsupported migration version is refused. Foreign keys, indexed date lookup,
parameterized queries and a single `BEGIN IMMEDIATE` transaction protect imports.
Any cross-series write error rolls the import back. SQLite serializes writers
(with a 30-second lock timeout); no separate process or server is required.

- `price_series`: names, exact EIA facet, USD/barrel, official URL and reuse notes.
- `price_snapshots`: immutable source kind/URL, our UTC retrieval time, reported
  source retrieval date where known, revision description, SHA-256 and audit bytes.
  Seeds retain exact CSV bytes; EIA responses retain credential-redacted JSON pages.
- `price_observations`: snapshot, ISO date, exact normalized decimal text, and
  either a numeric value or explicit missing code. Zero and negative prices are
  valid; nonfinite, malformed, excessive-precision or absurd-magnitude values fail.
  Same-value duplicate CSV dates collapse; conflicting duplicates abort. EIA
  pagination duplicates abort because they can indicate a shifting response.
- `price_current`: latest-per-date view, primary EIA preferred over secondary seed.
  Out-of-order snapshots cannot downgrade a newer source of the same priority.
- `price_import_runs`: auditable summaries, including no-op runs. Repeated current
  snapshots reuse their price versions. A genuine A → B → A source reversion is a
  new version, rather than accidentally ignored because A existed before.

`historical.prices.query(db, market, start, end, as_of=None)` is the local read
boundary. The CLI opens SQLite read-only for queries/exports. It returns inclusive,
ordered observations (including explicit source missing codes), coverage count and
bounds, source/revision/hash/retrieval metadata, units and limitations. There are
no synthetic weekend rows. An empty interval returns zero observations. For SQL:

```sql
SELECT observation_date, value, source_kind, source_url, retrieved_at, sha256
FROM price_current
WHERE series_id = 'wti' AND observation_date BETWEEN '2020-04-17' AND '2020-04-24'
ORDER BY observation_date;
```

`query --as-of <UTC timestamp>` reconstructs only **our ingestion knowledge** from
retained versions. A date before the first recorded retrieval has no known prices.
Every result is marked `point_in_time_safe=false`: current historical vintages and
missing original publication timestamps must not be presented as leakage-free
backtests. Decimal strings preserve price precision; displays may format them but
never replace negative prices with fabricated positives. Spot returns are not
executable P&L on futures, ETFs or CFDs.

`export` writes a temporary file and atomically replaces the destination. The
static schema has `schemaVersion=1`; each series has the same coverage/provenance
as the query result. Short per-series snapshot references (`s0`, etc.) in rows
resolve to full immutable hashes/IDs in `sources`. This keeps the 20-year export
small enough for a static page. The explorer limits the displayed table to 500
rows while reporting all selected counts; full JSON remains downloadable.
The original lab and seven oil replays are unchanged apart from a navigation link.
No backend is required for GitHub Pages, and this PR deploys nothing.

## Data rights and provenance limits

Source: U.S. Energy Information Administration, via the pre-existing
[datasets/oil-prices mirrors](../data/historical/README.md), imported into the
repository on 27 October 2026. Original mirror revision/retrieval time is unknown;
the manifest pins the exact repository Git blobs and SHA-256 of the seed slices.
The database records the source-import date at date precision without pretending
to know an exact upstream time. Importer UTC timestamps are distinct.

[EIA reuse policy](https://www.eia.gov/about/copyrights_reuse.php) permits use and
distribution of its public-domain data with source/publication-date acknowledgement;
protected third-party content and EIA marks are exceptions. The mirror's
[preparation licence](https://github.com/datasets/oil-prices#license) is PDDL.
This implementation neither negotiates a licence nor certifies every mirror
value against the primary source. It preserves that verification limitation in
the database, static export and UI.

## Tests and next phase

```sh
python3 -m unittest discover -s tests -p 'test_historical.py' -v
node --test tests/research.test.cjs
python3 tests/browser_test.py
python3 tests/historical_browser_test.py
```

Python tests need no third-party packages. Browser tests require Playwright and
Chromium at `/usr/bin/chromium`; they test light/dark and mobile/iPad viewport
layouts, not a claim of physical Safari testing. New CI runs the seed/import tests
without external API requests or secrets. Actual counts are tested against every
committed export observation as well as the seed hashes.

Next is a **dated, sourced event dataset**, not AI suggestions or live trading.
Start with a small reviewed set of world events, each with stable ID, category,
geography, occurrence timestamp/precision, first-publication timestamp/precision,
source URL/publisher, retrieved-at UTC, evidence hash, revision/version and
`known_at` time. Unknown publication times stay null and block inclusion in a
point-in-time backtest. Store corrections as new versions and query by `known_at`
and source vintage, never by occurrence date alone. Link events to price evidence
without claiming causation; only then consider event-linked research and
point-in-time backtesting, ahead of portfolio paper-trade evaluation. PR #2 remains
separate and untouched.

## Review of the completed primary EIA reconciliation

The supplied successful API reconciliation and independent official-table checks
are preserved in [reconciliation/](reconciliation/README.md). Three Brent API
values conflict with the official HTML history, which corroborates the seeds.
Date-set differences do not imply numeric gaps or permission to delete prices.
The new `python3 -m historical.reconcile` command is read-only; it can also
inspect the retained sanitized audit database locally without a key. Current
seeds, imports and static exports remain unchanged pending source resolution
and explicit review of any later versioned corrections.
