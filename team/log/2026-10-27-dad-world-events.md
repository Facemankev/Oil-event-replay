# 2026-10-27 · Dad · Sourced world events (EVT-1)

**Goal:** implement issue #13 independently of draft PR #12.

**What changed:** on `dad/evt-1-world-events`, [draft PR #14](https://github.com/Facemankev/Oil-event-replay/pull/14), review requested from Brendan:
- Working SQLite event database with 24 genuine sourced records, stable IDs,
  immutable revisions and atomic/idempotent imports. Repeat imports add no versions.
- Validated occurrence time, earliest located supporting publication, timezone,
  evidence quality, references and curated-card hashes. Six publications have
  minute stamps; 18 are date-only; four first-public dates remain unestablished.
  No record claims verified global-first reporting.
- Reproducible shared-calendar price research for all 24 events (48 benchmark
  results), using only the Brent/WTI CSVs already on main. Optional DAT-3 JSON
  adapter uses an external file boundary, not unmerged PR #12 code.
- Separate static explorer with sources, timing caveats, actual observation rows
  and negative/zero price handling. Existing dashboard files are unchanged.
- Actual data/count report, 10 event unit tests, six existing research unit checks
  and both browser suites pass. No paid service, deployment or live trading.

**Unfinished:** stronger archival first-disclosure evidence and original price
publication/vintage times are required before point-in-time backtesting. The
retrospective Saudi source aligns to its later evidence date, not the attack date.

**For Brendan:** review source interpretation, UTC/day-only alignment and the
explicitly descriptive comparisons. All pairings have backtest eligibility false.
PR #12 and PR #2 must remain untouched. No merge is authorized.

**Plan changes:** moved EVT-1 work to Waiting for review/Now; no changes to vision, principles,
section definitions or recorded decisions.
