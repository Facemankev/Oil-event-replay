# 2026-10-29 · Dad · Historical matching (DAT-3 / MAT-2 / MAT-3)

**Goal:** working deterministic analogues and a beginner-friendly results page,
starting with an honest primary EIA validation attempt; no merge or live trading.

**What changed:** `dad/mat-2-historical-matching` adds the separate `matching/`
page, pure matching module, SQLite catalogue builder and reconciliation/audit CLI.
The original dashboard, database modules/exports, event research, branding
preview and paper-trading work are unchanged. README/Now/TODO record the work.

- Real imports: 5,231 Brent + 5,137 WTI observations and 24 events.
- 240 windows: 1/3/7/14/30 reported observation days for each event/benchmark.
- Rank by category, market, mechanism and location wording; no price-size ranking,
  made-up severity or probabilities. Opposite known production actions excluded.
- Self/future disclosures excluded; historical query dates hide later results.
- Separate occurrence/publication evidence; unavailable first-public clocks stay
  unavailable. All current windows are provisional; primary-only mode hides them.
- Gold × Desk stylesheet copied unchanged, responsive light/dark page and safe text.
- Exact source observations, hashes and evidence retained; report lists absent
  weekdays without inventing holiday classifications or price corrections.

**Unfinished:** EIA reconciliation is blocked: no free key is configured; actual
API/download requests returned proxy CONNECT 403. Official documentation/table
browsing is not full verification. Setup explains hidden local key configuration.
18 event publications are date-only and four first-public dates unestablished;
severity lacks a comparable scale. Observation days are not a verified exchange
calendar. No comparisons are point-in-time-safe backtests or predictions.

**For Brendan:** review rankings, evidence labels, example/date behavior and the
Gold × Desk page. Physical iPad Safari testing remains a manual review step.

**Plan changes:** Now/status only; existing vision, principles and decisions stay.
