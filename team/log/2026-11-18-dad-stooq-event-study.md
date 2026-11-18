# 2026-11-18 · Dad · Stooq event study

**Goal:** Validate six owner-supplied daily CSVs and integrate permitted observations with the existing importer and costed simulation engine. Preserve the holdout, prospective registration and three-answer interface; draft/no merge.

**What changed:** Separate branch on #52. Original supplied files copied byte-for-byte to ignored work/stooq-private with restricted local permissions. Initial counts: NVDA 6999, AMD 11003, MRNA 1998, BMY 12573, SPY 5467, GLD 5467, total 43507; all have Date/OHLC/Volume, no duplicate or weekend dates, end 18 November 2026. No raw prices committed. CSVs lack publisher/usage/adjustment/receipt metadata. Official Stooq terms/download pages return a JavaScript verification page; no challenge bypass. The owner then supplied Stooq Terms text, including redistribution restriction section 5.3. Reviewed scope is private, non-commercial quarantine diagnostics only; no open/public/commercial/training licence is inferred. Imported all 43507 rows through the existing append-only store to ignored work/stooq-private/prices.sqlite; repeated import adds zero. Source authentication and adjustment method remain unverified; zero approved prices or supported trades.

**Validation:** Six files pass dates/OHLC; three blank volumes retained. SPY/GLD omit 2011-02-17 while three stocks include it; fixed union windows block missing benchmarks. Split continuity screens do not certify dividend/adjustment method. Sixteen new tests pass, including quarantine-only admission, exact-byte/repeat/immutable imports, fees, missing asset/benchmark/FX and public-report exclusion. Initial complete offline run passed 206 Python / 112 JS / 29 commands; all 14 local Chromium suites pass. Final checks follow in the draft.

**Unfinished:** Verify benchmark-session calendars for directly covered Nvidia windows, finish fixed-report handoff and final regression/two-engine CI; full source/adjustment evidence and public redistribution permission remain unresolved. Four retained direct NVDA event pairs gain provisional price coverage (12 horizons), not new independent or eligible events. Private study only; old learning holdout and reports unchanged.

**For Brendan:** Review later. No main, #19, original prices, parent reports or interface changes.

**Plan changes:** Doing/Now follow-up only.
