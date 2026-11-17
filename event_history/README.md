# HIST-1: cross-market historical evidence

Issue #38, on draft #36. A working, separate SQLite research library with
versioned events, source evidence, price observations, matching, coverage and
optional historical-detail exports. The three-step application, accounts,
canonical prices, EIA review, parent reports and existing previews are unchanged.
No live feed, order, broker connection or automatic paper entry is added.

## Reproduce

Python standard library; Node is needed for the existing application and JS bridge.
No network or API key is needed to reproduce retained evidence.

```sh
python3 -m event_history import
python3 -m event_history import
python3 -m event_history list --group pharmaceuticals
python3 -m event_history list --from-date 2019-01-01 --through-date 2020-12-31
python3 -m event_history show --event biogen-2019-reanalysis
python3 -m event_history match --event harvey-2017-texas --instrument brent --as-of 2017-08-27T12:00:00Z
python3 -m event_history evaluate --check --output work/hist1/new-evaluation.json
python3 -m event_history export --output work/hist1/new-historical-events.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
```

Default database: `work/hist1/library.sqlite`. Set `--db work/your-study.sqlite`
**before** the command for a separate study. Outputs require a new path under
ignored `work/`; existing evidence files are refused. Raw data/report precision
is retained there; [COVERAGE.json](COVERAGE.json) rounds display statistics only.
`RESULTS.sha256` pins the complete deterministic report at the stated study cutoff.
`INPUTS.json` fingerprints parsed JSON, so Windows line endings do not alter facts;
the inherited primary CSVs retain their original strict byte fingerprints.

## Actual coverage

**51 genuine events:** 32 inherited oil events, four inherited corporate cases,
and 15 new dated announcements. New events cover Nvidia earnings/guidance,
four Fed decisions, two Bank of England decisions, the Bank's referendum
response, an independent Merck trial stop, two Biogen trial/reanalysis stages and Pfizer trial/authorization stages.
The same drug/policy programme is explicitly one episode, not several independent
training examples. Equifax/Tesla are cross-sector corporate comparisons, not
semiconductor companies.

| Market group | Primary events | Linked events | Numeric series observations | Separately reported session reactions |
| --- | ---: | ---: | ---: | ---: |
| Oil / Brent and WTI | 32 | 40 | 10,394 | 0 |
| Technology / corporate equities | 7 | 7 | 0 | 3 |
| Gold | 0 | 6 | 0 | 2 |
| Pharma / biotech | 5 | 5 | 0 | 3 |
| Broad stock indices | 4 | 13 | 0 | 5 |
| Currencies / GBP–USD | 3 | 40 | 5,224 | 0 |

These counts overlap: **not 51 independent examples per market**. Gold coverage
is macro/political/vaccine exposure, not six gold-industry announcements. Thirty-two
currency links are GBP conversion references for oil; they are not claimed FX shocks.
EUR/JPY and other pairs are currently missing. The instrument registry identifies
spot benchmarks, a currency reference, specific common stocks and the Nasdaq
Composite price index. Generic reported gold futures lack a verified contract
identifier; they cannot become an executable gold instrument.

The separate database imports **16,320 primary observation rows: 15,618 numeric
and 702 explicitly blank/ND**. These reuse the pinned current EIA/Fed snapshots:
5,244 Brent, 5,150 WTI and 5,224 GBP/USD numeric observations. They do not overwrite
any of the original 10,368 canonical oil observations. Three inherited corporate
reference price pairs remain separately labelled, not adjusted daily series.

All 51 frozen event decisions are **No Action; Buy 0, supported paper entries 0**.
Original news versions/receipts, price availability and executable quotes remain
unproven. No successful strategy or predictive accuracy is claimed.

## Reactions, opposite outcomes and ripples

For oil/GBP reference series the module calculates **1, 3, 5, 10 and 20 numeric
reporting-observation horizons**. A baseline is the last numeric day before the
publication UTC date; the endpoint is the Nth numeric day strictly after it.
This deliberately excludes ambiguous publication-day prices. It is a descriptive
event window, not a verified exchange trading-day or intraday execution window.
Actual timestamps, holidays and unavailable prices are never manufactured.

GBP oil reference is `USD oil / USD per GBP`. Every intermediate oil observation
requires an exact-date numeric Fed rate for a complete GBP path; ND rates are
not skipped, interpolated or carried forward. Zero/negative oil values survive;
nonpositive endpoints have an absolute change but no percentage metric.

The 13 checked reported reactions remain outside calculated horizons/cohorts:

- Reuters reported gold futures **+3.1%** in the March 2020 emergency-cut session
  and **−5%** in the November vaccine-news session. Generic futures and spot
  intraday marks are different instruments/clocks.
- Biogen's reported **−29.2%** at trial discontinuation and **+26.11%** at its
  later reversal illustrate counterevidence within one programme. The reversal
  cannot enter the earlier decision or be counted as an independent programme.
- The Fed-cut session's Nasdaq **−2.99%** contrasts with **+2.5%** in the June
  2022 hike session. An easing decision does not guarantee a stock-market rise.
- Biogen's negative session had a reported positive Nasdaq reaction; Pfizer's
  positive session had negative gold/Nasdaq reactions. Different settlement/close
  times are not a synchronized causal experiment.
- Nvidia's three earnings announcements share a results/outlook mechanism, yet
  reported reactions include **+24.37%, +0.1% and +16.4%**. Near-flat +0.1% is
  positive, not a fabricated zero. Missing adjusted histories prevent a price cohort.
- Merck's earlier EPOCH stop provides an independent trial-stage cross-check for
  Biogen. Different biological mechanisms, populations and endpoints remain explicit;
  MRK prices are never substituted for BIIB.
- June 2023's unchanged policy rate is a null **policy change**, not an invented
  zero price return. Actual flat price observations and missing prices remain distinct.

Each figure has a dated source and locator in [additions.json](additions.json).
Primary issuer/regulator/central-bank announcements establish event facts;
secondary market reports establish only what those reports said. None verifies
original exchange prints, adjustment factors or an immutable historical article.
No raw price is reverse-engineered from a rounded reported percentage.

Drilldowns include first/second/third-order channel hypotheses, related episode
stages, sources, risks, context and measured reference paths. Hypothesized channels
are not assertions that the event caused a downstream move. Currency translation
is arithmetic, not a causal market ripple. Coverage distributions mix mechanisms
and instruments and must not be presented as comparable-cohort forecasts.

## Matching and historical time controls

Corpus curation is purposive and retrospective, including famous moves and
counterexamples. It is not a blinded, complete or representative event sample.
**Matching is outcome-blind:** category, mechanism, stage, location, available
operational scale and sourced regime labels determine similarity. Missing severity,
surprise/consensus, regime and economic exposure remain weaknesses. Cut/hike/hold,
unresolved allegation/confirmed incident and trial/authorization stages differ.

The algorithm filters publication clocks before projecting facts, excludes self
and the same episode, and freezes chronological non-overlapping intervals before
reading returns. Twenty-one prior observations form context; response windows
must mature before a historical cutoff. Changes to later events, their episode
labels, future observations or past return magnitudes cannot change earlier
selection. Tests assert equality of the complete earlier decision record.

Day-only publications use a conservative **two-UTC-day eligibility bound**, not
a guessed publication time. Pfizer's timezone-free printed clock stays null;
the FDA's explicitly timed Friday-night bulletin stays after market close.
Occurrence, supporting publication and actual original receipt remain distinct.
No original historical receipts were obtained: receipt-strict mode admits zero cases.

The decision function never reads forward returns or reported reactions. Separate
retrospective cohort statistics show selected/usable counts, median, signs and
range, keeping GBP and USD apart. Current-vintage price descriptions are **not
point-in-time-safe backtests**. Original availability is unknown for every case;
no Strong evidence, odds, calibrated likelihood or paper permission is invented.
Pre-event trends are descriptive current-vintage context, not ranking inputs.

Gross reference changes exclude costs. The inherited declared practice example
is £0.01 per leg, 10 bp full spread and 5 bp slippage per leg; actual provider
costs and equity/FX/gold execution terms are unverified. No costed trade or net
strategy result is fabricated from these assumptions.

## SQLite safety and integration with LIVE-1 #37

The dedicated application/version-marked database rejects unrelated databases and
canonical paths. Imports validate the whole bundle first and use one transaction.
Identical imports reuse rows; changed event revisions are refused unless explicitly
incremented for review. Old event revisions and source/observation snapshots are
retained. Each dataset pins its exact revisions; older imports remain reproducible.

`export` emits **`HIST-1/read-only/1`** with `view_historical_events`, evidence,
coverage and the existing three-answer contract. `adapter.mjs` supplies read-only
lookup/summary functions for #37. Oil records work with the unchanged
`ripple/history.mjs` reader (integration-tested). New assets are data-only and do
not generate unsupported legacy routes. This does not claim new cases are already
visible on the deployed site. No wider-asset UI, preview or account migration occurs.

#37 can add an approved provider beside this module and normalize actual source
clocks and instrument observations into a **new** study/version. It must not
replace missing vintages, treat reported news percentages as prices, reuse old
contracts as live quotes or lower gates to manufacture signals. No competing
live provider adapter is implemented here; #37 remains separate.

## Remaining source requirements

[SOURCE_ACCESS.json](SOURCE_ACCESS.json) records checked source limits and exact
next requirements. FRED removed its LBMA series; S&P reproduction is restricted.
No prohibited series was imported, no licence agreed and no paid account created.
Further work needs permitted contract-specific gold data; adjusted equity histories
with action factors and historical calendars; permitted index history; more exact
FX observations/releases; and original dated source/price vintages. Provider access,
redistribution terms, keys and any cost decision belong to the owner/#37. Never
paste credentials into this repository, a GitHub post or the conversation.

All existing tests plus HIST-1 unit/integration checks and complete Chromium/WebKit
regressions run in the dedicated stacked-PR workflow. Physical iPhone/iPad Safari
acceptance remains a human check; no physical-device pass is claimed.
