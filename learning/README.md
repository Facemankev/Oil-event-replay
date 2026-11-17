# LEARN-1: chronological candidate research

Issue #44, **built after SIM-1 #43** on draft #45. Free retained source data only;
no provider signup, key, subscription, trial, API fee, broker, order or account
operation. The SIM-1 code, original three-answer application, source prices,
EIA reconciliation #19 and all parent functionality remain unchanged.

```sh
python3 -m learning --check --journal work/learn1/new-audit --output work/learn1/new-full-report.json
python3 -m learning --check --journal work/learn1/new-audit --output work/learn1/repeated-full-report.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
python3 tests/learning_browser_test.py
python3 tests/learning_browser_test.py --browser webkit
python3 -m http.server 8000
# Open http://localhost:8000/learning/ and opt into research.
```

No network or key is required. Outputs must be new paths inside ignored `work/`;
existing sources/reports never overwrite. Full fingerprints/calculation traces and
the append-only SQLite journal stay local. The compact `report.json` retains all
public findings/cases and source links; CI artifacts contain public screenshots,
not raw journal/window traces. `protocol.json` and `REPORT.sha256` pin reproduction.

## What is actually learned

A deterministic search over the **nine predefined SIM-1 rule/horizon combinations**
uses earlier historical reference outcomes, including losses, untriggered signals,
fees, spread and slippage. No AI interpretation, fitted probability or hidden
parameter search. Cohorts require the **same primary instrument and event
category**; a technology return never becomes a pharmaceutical/oil quote.
Location, mechanism and pre-event GBP context remain auditable input facts; sparse
severity/valuation data is not invented. No whole-sample winner is advertised.

The score is the mean net GBP P&L per retained cohort event, including zero for a
rule that does not trigger, minus one quarter of its worst loss. Missing/unsettled
outcomes are **unknown, not zero** and invalidate complete-sample scoring. This is
a declared research criterion, not an estimate of expected future profit.

1. **Training: 2006–2015.** Rank all nine rules on training only. A candidate needs
   a complete sample, at least five settled training trades, at least 80% signal
   completion and a positive score to reach the shortlist (at most three).
2. **Validation: 2016–2019.** Only that training shortlist may be selected. Require
   at least three settled validation trades, adequate coverage, positive score
   and positive stressed-cost mean. Validation cannot change training metrics.
3. **Lock, then later test: 2020–17 November 2026.** Candidate identity and complete
   predictions are sealed before any test response is measured. A rejected
   training leader may be shown as a **diagnostic hypothesis**, never as a
   fallback validation-qualified recommendation. Test outcomes cannot replace it.

One primary exposure per event prevents oil/FX/peer targets inflating sample size.
Earliest-publication episode selection and a **45-day context/response embargo
within each instrument/category cohort** occur before outcomes. Events within 45
days of a fold boundary are purged; fitting receives no observations at/after its
boundary. The test assessor also rejects data after the report cutoff. Different
cohorts can share market regimes, so their counts are not statistically independent.
The held-out one-position cash portfolio separately blocks all overlapping signals
and repeated episodes, including across cohorts. Unknown marks prevent further
funding and a false final balance. It does not sum isolated winning case returns.

Entry, 1/5/20 reporting-observation exits, observed loss review, exact-date GBP
conversion, all-in £5/10% allocation and costs reuse SIM-1 unchanged. Oil spot and
noon FX are reference proxies, not executable exchange products. No IPO allocation,
short, leverage, roll, dividend, tax, missing FX or broker quote is fabricated.

## Actual results and refusal to claim a pattern

Of the **26 later events**, **21** remain after the fixed episode/embargo controls;
all excluded IDs/reasons remain in the report. The training set is very small,
and same-category validation is even sparser. **No cohort passes the configured
training/validation requirements.**

| Later diagnostic result | Count |
| --- | ---: |
| Research Watch | 4 |
| Research No Action | 17 |
| Settled diagnostic hypotheses | 2 |
| Positive after declared costs | 1 |
| Negative after declared costs | 1 |
| Missing/unsettled Watch outcomes | 2 |
| Directional false positives among settled hypotheses | 1 |
| Validated Buy / supported entries / orders | 0 |

The settled rejected hypotheses are OPEC April 2020 (**−£0.2746**) and OPEC July
2021 (**+£0.0669**) under the locked one-observation reversal rule. Laura/Ida storm
hypotheses have incomplete later exact-date GBP marks and remain unsettled, not
wins or losses. These isolated case results are **not** a simultaneously funded
portfolio; the earlier unresolved position blocks later use of its cash.

The fixed five-observation, costed buy-and-hold reference baseline has **10**
settled paths: **6 positive / 4 negative**. No-trade keeps **£50**. Baseline gains do
not prove a missed investable opportunity or an event-caused effect. Stressed
cost outcomes and the held-out portfolio are retained. No fee scenario is tuned
using later outcomes.

The conditional two-case hit fraction is a descriptive count, not a forecast
accuracy claim. **Calibration is undefined**: no probabilistic forecasts were
issued. No invented success probability, p-value, confidence of profit or claim
of repeatability. At least eight later independent settled cases would still be
only one prerequisite; current data also lacks original news/price availability,
investable instruments and prospective replication.

## Immutable predictions and actual clocks

`python3 -m learning --journal ...` completes preparation, commits all prediction
rows, then assesses test outcomes and appends settlements. SQLite triggers reject
updates/deletes. Repeated runs deduplicate without changing first-recorded times;
revised later observations append new settlement versions under the same sealed
prediction. Unknown databases, paths outside `work/`, forged Buy/probability
payloads and missing prior predictions fail closed.

[AUDIT.json](AUDIT.json) records actual successful local runs: first **21**
predictions and **21** settlements, repeat **0 new predictions / 0 new settlements**.
Actual recording times are **17 November 2026**, not invented 2020 clocks. Historical
decision bounds are explicitly simulated. This is not a set of authentic forecasts
made years ago, and not a live monitoring or alert service.

## What the holdout does and does not establish

Tests mutate later prices, future event features and future case membership and
assert training/model selection and complete earlier prediction identities remain
unchanged. Validation mutations cannot change training metrics. Tests also cover
fold maturity, same episodes, sparse/unpriced cohorts, negative/missing outcomes,
realistic cost accounting inherited from SIM-1, cutoff enforcement, commit-before-
assessment ordering and immutable/revised journals. Explicitly synthetic rising
fixtures show the learner can pass its numerical thresholds without ever enabling
execution; those fixture prices are never published as genuine history.

This is **chronologically held out from this fitting procedure**, not a prospective
preregistration or proof that developers never saw these historical outcomes.
The corpus is purposively selected and subject to survivorship, curation, regime
and multiple-testing bias (nine candidates per eligible cohort). Current-vintage
references do not establish original point-in-time availability. A chronological
split cannot cure those source limitations. Repeatedly optimizing on this holdout
would consume it; do not tune these rules on its winners.

Next: expand permitted free histories with original availability and investable
instrument evidence, obtain more independent same-category episodes, predeclare a
new protocol and test against a newly reserved period before any forecast claim.
Keep the simple research view optional and validated execution gates unchanged.
Physical iPhone/iPad Safari acceptance remains outstanding. Separate draft; no merge.
