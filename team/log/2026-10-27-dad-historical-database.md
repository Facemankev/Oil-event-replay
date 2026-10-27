# 2026-10-27 · Dad · Historical database (DAT-3)

**Goal:** implement issue #10 using the Brent/WTI CSVs merged into main.

**What changed:** on `dad/dat-3-historical-sqlite`, [draft PR #12](https://github.com/Facemankev/Oil-event-replay/pull/12):
- Python standard-library SQLite importer, immutable snapshots, revision history,
  primary-source preference, repeatable backfill and overlapping incremental updates.
- EIA API v2 adapter with pagination, strict validation and credential redaction.
  Seed provenance stays secondary until independently reconciled.
- Inclusive date queries, retrieval-time history and a static export explorer linked
  from the existing lab. Original dashboard scripts and PR #2 are unchanged.
- Actual seed import: 5,231 Brent and 5,137 WTI prices, 2006-01-03–2026-10-20.
- 12 parser/import/query/update tests, 6 research unit tests and both browser suites pass. Source missing values,
  zero and negative prices are preserved; missing dates are never filled in.

**Unfinished:** provide a free EIA key and permitted API network access for a real
primary-source backfill/reconciliation. The API path has fixture tests, not a
claim of a successful authenticated fetch. See `historical/README.md` and import report.

**For Brendan:** review the data source distinction, safe reruns/revisions and the
static export. No merge is authorized. Event publication/known-at data is the next
phase, documented with point-in-time limits before any backtesting work.

**Plan changes:** DAT-3 milestone and Now section moved to waiting for review; no vision, section,
principle, negotiated licence or decision changes.
