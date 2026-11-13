# DAT-4 — primary oil and GBP/USD audit (Issue #29)

Based on draft PR #28 at `d45f3ff`. PR #19 is reviewed and left separate.
This working, read-only research pipeline adds verified primary-table observations
and reruns the frozen paper policy. The simple interface, original prices,
account snapshots/policies, research records and previews are unchanged.
No merge, brokerage or real-money trading. Brendan can review later; his review
is not an implementation gate.

## Actual findings

All **10,368** existing numeric prices match the captured current EIA publication:
**5,231 Brent / 5,137 WTI**, zero price differences, zero missing numeric seed
observations and zero numeric gaps within the seed range. The current primary
capture also has 13 newer observations per benchmark after 20 October 2026;
these are retained only in the separate source snapshot, not imported into the
canonical database.

| Brent date | Canonical/current EIA | Older reported API | Immediately preceding numeric EIA date |
| --- | ---: | ---: | --- |
| 2016-12-28 | 54.95 | 53.93 | 2016-12-23 |
| 2016-12-29 | 54.97 | 54.95 | 2016-12-28 |
| 2018-04-16 | 72.05 | 73.18 | 2018-04-13 |

USD/barrel. The reported API value equals the preceding numeric observation in
all three cases. That is consistent with a possible alignment problem; it does
**not** establish its cause or prove a revision. Current primary evidence supports
retaining all three original prices. The original API response/SQLite payload
was not supplied here, so its specific conflict and revision history remain
unresolved. No key is requested or used, and no correction is silently applied.

The pinned PR #19 claims are individually rechecked: **137 API-only dates are
explicitly blank in current EIA HTML**, not established missing numeric prices;
**17 API omissions retain matching numeric EIA/seed prices**. API values for those
137 dates remain unknown from the summary. A blank/ND cell does not prove a
holiday, market closure or its cause. Original revision/publication times are unknown.

## Verified FX coverage and rate direction

The Federal Reserve H.10 snapshot retains **5,440 weekday rows, 5,224 numeric
USD-per-GBP observations and 216 explicit ND entries**, 2 January 2006 through
6 November 2026. The page identifies its current release as 9 November 2026.

**GBP oil reference = oil USD ÷ observed USD per GBP.** The raw four-decimal
Fed quote is retained; conversion is computed without rounding its reciprocal
first. No rate is carried forward or interpolated. All 34 old paper FX observations
match the current Fed reciprocal at their existing four-decimal precision;
those original account quotes are nevertheless preserved byte-for-byte.

Source/date/locator, capture timestamp, units, missing marker, snapshot hashes
and the absence of original historical vintage clocks are retained in
`sources/manifest.json` and the CSVs. A current publication is distinct from
information demonstrably available at a historical decision time.

## All 24 events rerun

Each benchmark uses its own actual numeric EIA reporting observations. These
are **not** an asserted exchange trading calendar. The decision date is the
first numeric EIA observation strictly after the existing supporting-publication
anchor. Every decision is frozen before reading following returns.

Complete **current-vintage** data means entry plus every one of the next N oil
reporting observations has an exact same-date numeric Fed rate. No missing
intermediate valuation is hidden. Original as-of release/vintage completeness
remains **zero**; it must not be inferred from observation or capture dates.

| Horizon after entry | Brent complete / 24 | WTI complete / 24 |
| --- | ---: | ---: |
| 1 observation | 23 | 24 |
| 3 observations | 22 | 23 |
| 5 observations | **18** | **22** |
| 10 observations | 15 | 20 |
| 20 observations | 11 | 17 |

For the default five-observation window, **18 events have complete data for both
benchmarks and six have at least one incomplete window**. Brent is 18 complete /
6 incomplete; WTI 22 / 2. All incomplete windows point to explicit Fed ND cells:
Harvey (4 Sep 2017), Iranian sanctions reimposition (12 Nov 2018), Laura
(7 Sep 2020), Ida (6 Sep 2021), OPEC October (10 Oct 2022), and Israel October
(9 Oct 2023). The two WTI incomplete windows are sanctions reimposition and
OPEC October. Calendar causes are not inferred.

**Flat-account policy decisions: Buy 0, Hold 0, Review Sell 0, No Action 24.**
All 48 benchmark cases abstain. Hold/Review Sell require an existing position;
no artificial entry is made just to obtain one. Reasons include:

- Original price/FX publication vintages remain unproven for all 24 events.
- Fewer than eight as-of-qualified, non-overlapping, condition/scale-matched
  analogues qualify for every event. GBP cohorts use genuinely converted
  historical observations and explicitly exclude unavailable FX paths.
- Fourteen Brent pre-event condition windows are incomplete under the strict
  21-observation rule; one Brent event has unavailable entry FX.
- WTI remains research-only: no WTI paper account/instrument has been invented.

Improved numerical coverage is not evidence of predictive accuracy. The policy
and thresholds are unchanged. The existing manual £5 practice flow and its
position-aware Hold/reviews continue to work and are regression-tested.

## Gap and cost sensitivity

PR #28 had one GBP baseline using five **jointly priced** observations. With
this source coverage there are **23** such Brent baselines at the original
entry date, or **24** only if entry is explicitly deferred to the first joint day.
Those are different timing rules, not additional filled rates. For example,
Harvey's strict fifth oil observation is 4 September (Fed ND), while the fifth
joint observation is 5 September. Israel's original 9 October entry is not priced
in GBP; a separately labelled deferred-entry sensitivity begins 10 October.

The main fixed-window counterfactual baseline includes all 18 complete Brent
cases: **9 positive / 9 negative** with zero or declared costs; **5 positive /
13 negative** with stressed costs. These are retrospective £5 practice baselines,
not policy Buy signals or strategy returns. No costed WTI trade is fabricated.

| Scenario | Fee per leg | Full spread | Slippage per leg |
| --- | ---: | ---: | ---: |
| Zero | £0 | 0 bp | 0 bp |
| Declared | £0.01 | 10 bp | 5 bp |
| Stressed | £0.10 | 30 bp | 15 bp |

Entry/exit dates are held fixed across costs. The actual policy stays in £50
cash, like no-trade. False-positive rate is undefined because there are no
supported entries. Selected-event baselines do not establish a causal or
predictive edge; unrecorded events cannot be counted.

## Reproduce

Python standard library plus Node; no key, network or paid service needed for
retained-snapshot validation:

```sh
node verification/evaluate.mjs --check
node verification/evaluate.mjs --output work/dat4-new-report.json
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.mjs tests/*.cjs
python3 -m http.server 8000
# Existing unchanged interface: http://localhost:8000/ripple/
```

`RESULTS.sha256` pins the full deterministic trace, including every event,
all horizons, missing dates, sources, cohort exclusions and sensitivities.
Full-precision derived reports stay under ignored `work/`, not in public source.
Existing report files and canonical output paths are refused. JSON inputs are
fingerprinted by parsed serialization (portable across JSON line endings); source
CSVs retain strict byte fingerprints. Raw captured
prices/rates retain their precision and missingness; display summaries are not
replacements for data. `.gitattributes` preserves source CSV bytes on Windows.

Optional fresh primary download, when ordinary HTTPS access to the sources is
available (writes only a **new** local directory under `work/`):

```sh
python3 -m verification.capture --output work/primary-fresh-2026-11-13
```

The current executor's outbound policy rejects direct official-site HTTP; the
retained snapshot was captured from visible primary tables through the supported
web reader. All 5,440 weekday rows per source are captured and validated. This is
a normalized primary table transcription, **not original HTTP bytes**. Dates/week
columns are precise locators. `original_http_sha256` is null, not invented. The
optional downloader records real HTTP hashes when it succeeds; it never supplies
historical publication/vintage times. Original raw pages remain local.

Primary sources: [EIA Brent](https://www.eia.gov/dnav/pet/hist/RBRTED.htm),
[EIA WTI](https://www.eia.gov/dnav/pet/hist/RWTCD.htm),
[Federal Reserve H.10 GBP](https://www.federalreserve.gov/releases/h10/hist/dat00_uk.htm).
Rates are USD per GBP; the Fed describes these as New York noon buying rates.
Government numerical data are retained with source attribution; no third-party
proprietary price/FX feed or negotiated licence is introduced.

Next: obtain the retained sanitized API payload to explain the old three-value
conflict, preserve actual historical release/vintage evidence, and expand genuine
comparable events before evaluating a frozen policy on a later untouched sample.
Do not loosen the gates to manufacture Buy signals. No deployment, merge or
historical-data replacement occurs in this draft. Physical Safari acceptance
remains a human check; automated profiles are not physical device testing.
