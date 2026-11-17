# SIM-1: retrospective paper hypotheses

Issue #43, on draft #41. Free retained data only; no API, credential, subscription,
charge, broker or practice-account operation. This optional research page leaves
the original three-answer application and every parent source/module unchanged.
IPO #42 stays separate: no invented offer allocation, opening fill or IPO price.

```sh
python3 -m simulations --check --output work/sim1/new-comparison.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
python3 tests/simulations_browser_test.py
python3 tests/simulations_browser_test.py --browser webkit
python3 -m http.server 8000
# Open http://localhost:8000/simulations/ and opt into research.
```

Outputs must be new paths under ignored `work/`; reproduction never overwrites a
source, canonical price or report. The compact public `report.json`, the full-output `REPORT.sha256` and the pinned
`protocol.json` reproduce all cases and declared sensitivities offline. Visible
GBP values are rounded to four decimals; calculation uses Decimal before rounding.
The raw source price and exact-date FX remain attached. Full calculation traces and per-window fingerprints stay in ignored local output; public pages/artifacts use the compact evidence projection. Source snapshots retain their existing fingerprints.

## Why the validated engine abstains

All **51** events lack verified original news receipts/versions, original price/FX
availability and an executable quote/product. **50** also have fewer than eight
selected historical comparison episodes; none has proven original-as-of qualified
cases. These are separate gates, not 51 measured negative expected returns. The
engine does not assess an edge after these failures. Its policy stays No Action.

## Fixed experiment, not strategy selection

All 51 events and **151 explicitly targeted event/market pairs** are retained,
including unavailable companies/gold/index histories. Oil-linked GBP/USD is
conversion context, so **32** such pairs never become extra currency signals.
The rules and costs were written before this evaluation; this is retrospective
research, not prospective preregistration or a blind market-data study.

Nine predetermined combinations: unconditional event-long, prior-five-observation
GBP-value momentum-up, and prior-five-observation reversal-down, each held for
1/5/20 **subsequent numeric reporting observations**. Every decision is frozen
before future returns. No best-rule ranking or fitting happens in SIM-1.

- Entry is the first numeric reporting observation on a date strictly later than
  the source publication eligibility bound, at most seven calendar days later.
  Day-only publication uses the inherited conservative two-day bound; it is not
  a guessed original clock. No before-release or same-day opening fill is invented.
- Exact-date GBP/USD is required. A missing entry FX rate rejects that entry; it
  does not advance it. A missing later mark preserves the earlier Buy and leaves
  the result unsettled, rather than retrospectively cancelling a losing trade.
- Default cash **£50**, maximum all-in allocation **£5 / 10% of available cash**.
  Both fixed fees are reserved inside that allocation. No leverage or shorting.
- A 10% reference-price loss review exits at the next observed reference that
  triggered it, including worse gaps. It never fills at an imagined stop price.
- Portfolios permit one position and one episode at a time, process publication
  bounds chronologically, use deterministic event/market tie order and exclude
  overlaps before examining rejected future returns. Unsettled positions block
  further entries and make final account value unknown, not falsely profitable.
- Daily liquidation-value drawdown includes costs from the initial £50 peak.
  Intraday losses are unknown. Missing observations are not automatically holidays.

Oil spot is **not an investable exchange product**. These are unleveraged price
reference exercises, with no guessed futures roll, ETF tracking, dividend or tax.
GBP/USD hypotheses explicitly hold USD cash funded from GBP (reciprocal USD/GBP),
not GBP bought with itself or a leveraged long GBP/USD contract. Other supported
reference directions retain their actual units. Original price availability and
exchange calendars remain unverified. Hypothetical Buy/Hold/Sell is never a
validated recommendation or a practice-account transaction.

## Costs and actual results

Each scenario applies half the full spread plus per-leg slippage at entry/exit,
fixed GBP fees both legs, fractional units and exact-date GBP valuation. These are
**declared illustrative friction sensitivities**, not actual broker tariffs or
claims of achievable net returns. The higher fixed-fee case exposes small-budget
friction rather than hiding it. No paid provider was connected.

| Scenario | Fee each leg | Full spread | Slippage each leg | Positive / negative, default 5-observation rule |
| --- | ---: | ---: | ---: | ---: |
| Zero | £0 | 0 bp | 0 bp | 39 / 30 |
| Declared | £0.01 | 10 bp | 5 bp | **34 / 35** |
| Stressed | £0.10 | 30 bp | 15 bp | 12 / 57 |
| Small-account flat fee | £1 | 50 bp | 25 bp | 0 / 69 |

Default coverage: **69 settled / 151 targeted pairs**; 32 conversion-only
exclusions, 31 missing price histories, 18 missing exact-date FX paths and one
nonpositive reference that cannot support fractional exposure. Counts overlap
within events and are not 69 independent experiments. No missing price is filled.
The declared median net result is **−£0.0024** per £5 hypothesis; all 36 rule/cost
summaries retain winners, losers and coverage rather than selecting large moves.

Concrete opposite outcomes from the same early event (Humberto, 2007), selected
only to illustrate both signs, not as a forecast:

- WTI, 14–21 September: gross **+£0.2311**, net **+£0.1998**.
- Brent, the same dates: gross **+£0.0057**, net **−£0.0243** after costs.

The complete default list, including all other losing and missing cases, is in
`report.json` and the page selector. Each has a dated chart/table and hypothetical
Buy/Hold/Sell trail. Same-window costed buy-and-hold disables the loss-review exit;
no-trade leaves £50 unchanged. Broad continuous passive baselines are explicitly
unavailable if any intermediate positive price or exact-date FX is missing.
No selective endpoints repair an incomplete baseline. The three one-observation
portfolios finish below £50; longer portfolios include unsettled paths and do not
receive a fabricated final balance. Event-window wins are not summed into a
fictional simultaneously funded portfolio.

## Limits and next stage

This is a purposively selected, current-vintage event corpus. Survivorship,
selection, regime, episode dependence, original clocks, instrument tradability and
actual execution costs remain unresolved. There is no validated probability,
causality, profitable edge or supported entry. Physical iPhone/iPad Safari testing
remains outstanding even when emulated Chromium/WebKit profiles pass.

LEARN-1 #44 builds only on this completed simulation implementation. It must use
chronological training/validation/later testing, purge overlapping outcomes, lock
candidate selection before test outcomes and retain false positives/missing cases.
No result here relaxes existing execution gates. Keep the PR draft; no merge.
