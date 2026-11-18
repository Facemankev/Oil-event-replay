# Owner-supplied Stooq files — private event review

Separate draft on #52. **43,507 rows inspected and imported into a private quarantine; repeat import adds zero.**
The owner supplied Stooq terms: redistribution requires publisher consent.
Processing is restricted to private, non-commercial diagnostics; no open, public,
commercial or model-training licence is inferred. Source identity and adjustment
treatment remain unresolved, so zero rows are approved for production or trading.
There is no force/accept-risk switch. Raw files, database and
actual detailed study stay under ignored `work/`, never in this public repository,
browser fixtures, Actions artifacts or the dashboard. No network download,
account, credentials, subscription or payment is required.

## Actual supplied files

| Symbol | Rows | Coverage | Role |
| --- | ---: | --- | --- |
| NVDA | 6,999 | 1999-01-22 to 2026-11-18 | Nvidia common stock |
| AMD | 11,003 | 1983-03-21 to 2026-11-18 | AMD common stock |
| MRNA | 1,998 | 2018-12-07 to 2026-11-18 | Moderna common stock |
| BMY | 12,573 | 1977-01-03 to 2026-11-18 | Bristol Myers Squibb common stock |
| SPY | 5,467 | 2005-02-25 to 2026-11-18 | US equity ETF benchmark; not Nasdaq Composite |
| GLD | 5,467 | 2005-02-25 to 2026-11-18 | Gold ETF proxy; not spot gold or futures |

All six have `Date,Open,High,Low,Close,Volume`, ascending unique weekday dates
and valid positive OHLC relationships. NVDA/AMD/BMY each have one blank volume,
retained as null. Price files have no embedded ticker, currency, original receipt,
licence, dividend or adjustment fields. Names/identity are owner-declared;
expected Stooq URLs are not claimed as observed HTTP provenance. Hashes, source
row locators and exact bytes remain in the private inspection report.

SPY/GLD omit 2011-02-17 while three other supplied securities include it. This is
an observed benchmark gap, not a declared holiday. The alignment grid is the
**union** of supplied dates within benchmark coverage, so this gap blocks affected
windows. Shared omissions still cannot be distinguished from exchange closures.
The [reviewed NYSE/NYSE Arca calendar](stooq-calendar.json) supplies benchmark
sessions for 2023–2026, including the special Carter closure on 9 January 2025.
Early closes remain sessions. These years use an independent expected grid, so
even a date missing in all six files is detected. Outside that scope the union
remains explicitly unverified. Individual security halts and quote clocks remain
unresolved. All four direct Nvidia cases have reviewed benchmark-session grids.

Nvidia confirms [four-for-one trading from 20 July 2021](https://investor.nvidia.com/files/doc_downloads/doc_faq/08/Investor-NVIDIA-2021-Stock-Split-FAQ-08.9.2021.pdf)
and [ten-for-one trading from 10 June 2024](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf).
The supplied series has no corresponding four/tenfold discontinuity. That is a
continuity check, not a verified vendor methodology or dividend-return claim.
Never apply those splits a second time or manufacture an adjusted-close field.

## Reproduce locally

Python standard library only. Place the original six files in ignored
`work/stooq-private/` using their supplied `*_us_d.csv` names. Run each command on
one line (Windows: replace `python3` with `py`). Output paths must be new, under
`work/`; existing reports are never overwritten.

```sh
python3 -m daily_prices.stooq inspect --folder work/stooq-private --output work/stooq-private/inspection-new.json
python3 -m daily_prices.stooq review-study --folder work/stooq-private --output work/stooq-private/study-new.json
python3 -m daily_prices.stooq import --folder work/stooq-private --db work/stooq-private/prices.sqlite --output work/stooq-private/import-new.json
```

`inspect` parses and validates owner bytes without admitting prices. `review-study`
performs explicitly provisional in-memory diagnostics on those owner-supplied
materials; it makes no licensed-use or database-admission claim. `import` stores only private quarantine captures under the reviewed owner scope.
It cannot approve prices or unlock training/trading. It reuses the existing append-only daily-price store, exact-byte parser, range queries
and revision protections, with independently restricted private scope.
Use `review-study --from-db` (with the same folder/output options) to query and
analyse the exact imported captures through the existing range-query API. Private
captures cannot enter public daily reports or the prospective journal.

[stooq-policy.json](stooq-policy.json) records actual verification status.
The official [terms](https://stooq.com/t/), [download page](https://stooq.com/db/h/)
and Polish terms returned JavaScript browser-verification pages on review. No
challenge was bypassed. The owner subsequently supplied the terms transcription,
including section 5.3. A private excerpt fingerprint records that receipt without
claiming an independently fetched licence. This supports a limited private
quarantine review, not redistribution or commercial/product use. Unknown source
authentication and adjustments stay explicit, not certified. Redistribution and
model training remain unapproved. Do not paste private negotiated licence terms into this public repo.

## Interpretation and before/after

The fixed panel uses all 51 retained sourced events and all six requested assets:
306 descriptive event/asset pairs, with 1/5/20-session windows and all four existing
SIM-1 cost assumptions. Hypothetical exposure to another company is labelled
`descriptive_panel_no_sourced_company_exposure`, not a newly discovered event.
The existing library directly targets NVDA four times; no AMD/MRNA/BMY events are
invented from CSVs. New direct price coverage is four existing event pairs / twelve
horizon windows. New eligible historical examples, independent events, supported
Buy decisions and genuinely new predictions: **zero**. Private quarantine storage
is not approval of the adjustment methodology or original price availability.

The private report separates publication-day descriptive reactions, conservative
eligibility-window reactions and costed post-eligibility hypotheses. Day-only
sources retain the original two-day conservative decision bound. Exact dated
windows are shown; no claim of isolating the first intraday reaction is made.
SPY returns use the same dates as each asset; percentage-point excess differs from
compounded relative wealth, and both are labelled. GLD keeps ETF expense/tracking
and currency risks; it cannot replace a gold spot/futures series.

Costed results call the existing SIM `plan`/`measure` with fixed horizons and
`risk_exit=False`. Entry follows the existing publication eligibility rule; exact
intermediate GBP/USD evidence is required. Missing asset, benchmark or FX prices
block the path; entry/exit never shift to obtain a nicer result. Original declared,
zero, stressed and flat-fee assumptions are illustrative sensitivities, not a
broker tariff. Winning and losing cases and missing reasons all remain in the
private report; overlapping horizons/assets are not independent trades and their
P&Ls must not be summed as a portfolio.

The original 69-settled SIM result and 21-event LEARN holdout remain unchanged.
There is no training, threshold tuning, test-member change or rewriting of parent
reports. Increased descriptive coverage does not establish predictive improvement.
These are inspected historical outcomes, not fresh forecasts; prospective
registration and its zero new events/outcomes remain separate.

Public [review metadata](stooq-review-summary.json) intentionally includes counts,
coverage, missingness and blockers only. The detailed actual-file results stay
private under the restricted private-use review scope. Automated checks use fabricated,
clearly labelled controls; real uploaded prices are never repackaged as fixtures.
