# Ripple decisions — Issue #23

Additive `ripple/` application, based on draft PR #22 (6fe59ff), on #20/#16.
Existing pages, price/event records, matching/cohort engines, trading/core.mjs,
design tokens and PR #19 are unchanged. No merge or live provider.

## Run

```sh
python3 -m ripple.build --check
python3 -m http.server 8000
# http://localhost:8000/ripple/
node --test tests/*.cjs tests/*.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/ripple_browser_test.py
python3 tests/ripple_browser_test.py --browser webkit
```

Python standard library, Node and static HTML/ES modules; no build service/key.
Browser checks need Python Playwright and Chromium/WebKit. CI installs both.
`python3 -m ripple.build` reproducibly writes only ripple/data.json from the
existing immutable Brent export and the new pinned FX slice. No price is filled
or corrected. A fresh build is byte-identical. Previous PR #22 account storage
is separate; this feature uses market-ripple-ripple-practice-v1.

## Two screens

Opportunities shows one genuine Harvey event and two three-stage mechanisms:
production → crude availability → energy buyers; refining → crude demand/fuel
supply → transport/airline costs. NHC establishes the located landfall bulletin;
EIA's dated pre-landfall article establishes infrastructure exposure. Downstream
price/business effects are **hypotheses**, not measured correlations. No fuel,
airline, insurance or transport price data/trading is claimed.

Decision/position uses the SAME GBP-converted Brent reference as the virtual fill
and marks landfall, entry and current replay observation on a dated chart. The
inspector selects known points only; it never rewinds the account or supplies
an old fill price. Historical comparisons and sources are closed disclosures.
The user can explicitly confirm a £5 virtual experiment with £50 virtual cash.
Real trading is disabled. No broker, real orders, monitoring service or live feed.

## Source provenance and timing

34 exact price/FX joins, 14 August–29 September 2017. Brent is from the existing
5,231-row provisional EIA-derived export. WTI remains research scope only.
FX preserves 35 United Kingdom CSV rows including the blank 4 September row;
that date has no tradable GBP quote and is skipped. No previous rate is reused.

FX: datasets/exchange-rates commit c28e171e36a46bd2941cf66156acd8efaf9906f5,
[raw snapshot](https://raw.githubusercontent.com/datasets/exchange-rates/c28e171e36a46bd2941cf66156acd8efaf9906f5/data/daily.csv).
Full retrieval SHA-256 5f82c543467ae6398e766fb110fe57abe446b95c4ad13b2eaca8954911c6259d.
The 35-row slice is fx-harvey-source.csv; source/input hashes are in data.json.
[Preparation code](https://github.com/datasets/exchange-rates/blob/c28e171e36a46bd2941cf66156acd8efaf9906f5/exchange_rates_flow.py)
identifies DEXUSUK and inverts it: these particular rounded values are GBP per
USD. GBP reference = unchanged USD Brent × that same-date rate. This is Federal
Reserve data via FRED/datasets; secondary, not independently H.10 reconciled.
Preparation is PDDL; Board public-domain attribution terms and the existing
source-family documentation in data/SOURCES.md apply. No data licence changes.

New curated EIA context/update cards, reviewed 1 November 2026:
- [25 August exposure article](https://www.eia.gov/TodayinEnergy/detail.php?id=32652).
- [11 September refinery findings](https://www.eia.gov/todayinEnergy/detail.php?id=32852).

The article clocks are unknown: expose each only from the NEXT UTC date.
The September findings are not backdated to their measured week ending 1
September. These are short curated cards, not full archived pages or proof of
historical webpage versions. The original event record stays unchanged.

Daily price and FX values are treated as available at replay day-end, an explicit
educational assumption. Original publication clocks/vintages are unknown;
retrospectively retrieved records cannot establish a fully point-in-time-safe
backtest. Future observations exist in the source file but are excluded from
rendered charts, entry evidence, review decisions and observed-outcome logs.

## Prompts and conditional path method

Reuse PR #16 similarity and PR #20 non-overlapping cohort selection. Historical
full 20-step rows supply actual day-by-day Brent observations; only rows completely
available before the replay cutoff qualify. Self, future and weak/location/severity
mismatches are excluded using the existing rules. Full-window chronological
non-overlap selection happens before looking at movements. It does not prove
independence. At Harvey entry there are 2 five-step comparisons but just 1 usable
non-overlapping full path; the evidence is Limited.

Align historical paths by Brent report-day index after the publication anchor.
At current phase k, compute prior two-step change and the next three-step
conditional historical return from actual past observations, not endpoint medians.
Report counts, signed outcomes, median, range, IQR and rising-then-falling counts.
FX is not in these historical comparison returns. The GBP paper horizon counts
available JOINT price/FX steps; the two calendars are explicitly different.

Exploratory support gates (not fitted forecasts/probabilities): at least 8 complete
non-overlapping paths, all primary prices, precise clocks, comparable severity and
original as-of evidence; IQR ≤5pp and range ≤15pp; same-signed chronological-half
and leave-one-out medians; at least 75% relevant signed examples. A reversal also
requires prior rises followed by falls and median conditional return below −1%.
A positive research prompt requires analogous positive support. Those numerical
rules are transparent design choices, not validated investment signals.

All production data fails those support/as-of gates. **No Action** is correct
before entry; no supported Consider Buy or reversal is fabricated. Unit fixtures
exercise those supported branches and are never production data. Manual paper
experimentation remains an explicit user choice.

After entry, **Hold** means no chosen review criterion triggered, not expected
price appreciation. **Review Sell** can follow the user's frozen loss/gain/time
rules, genuine newly available adverse context, materially weaker evidence or a
supported conditional path. Nothing sells automatically or assumes day 3 is a sell.
Default plan: 5 joint priced steps, 3% loss-review, 5% gain-review. Daily gaps can
exceed thresholds; they are not stop orders or guaranteed loss limits.

Entry persists hypothesis, market/instrument, exact USD price/FX/GBP reference,
date, source references, evidence snapshot and exit criteria. Each new replay
observation evaluates again. Suggestion IDs prevent reload/response duplicates.
Browser time and simulated information date are separate. Accept/cancel/dismiss
responses are chronological; later close outcomes are stamped when observed,
not backdated. Backups replay a bounded operation ledger against canonical quotes
and reject altered balances/snapshots/ordering/revisions; browser records are not
tamper-proof. Storage denial uses an explicitly labelled exportable memory session.

## Acceptance demo

1. Open the new preview. See one Harvey card and two hypothetical ripple paths.
   Default is No sufficiently supported opportunities; optional evidence is closed.
2. Open Decision / position. Replay starts 28 August 2017, GBP reference £40.13.
   Move the inspector to 14 August: the trade confirmation must STILL use 28 August.
3. Confirm a manual £5 virtual buy. Entry reference is exactly 51.87 × 0.7736 =
   £40.126632; virtual cash is £45. The entry marker appears; Hold is shown.
4. Advance four priced steps: still Hold. The next available step is 5 September,
   skipping the missing FX date. Review Sell cites the chosen five-step horizon,
   not a learned reversal. Position is still open until explicit close confirmation.
5. Dismiss, then explicitly close if desired. Observed proceeds are about £5.14;
   total virtual cash about £50.14. Export/reload/restore; later outcomes retain
   their actual simulated observation dates. Earlier paper accounts stay unchanged.
6. An optional long-horizon experiment (20 steps, 50%/100% review thresholds)
   stays Hold through 11 September. The EIA update first becomes eligible on
   12 September and prompts a new-source risk review, never before publication.

Physical iPhone Safari remains untested here: check actual touch/rotation, enlarged
text, focus, native confirmations, sign-in (for a private preview) and Files
backup save/restore before physical-device acceptance. Automated WebKit/iPhone
profiles are engine tests, not physical iOS certification.

The new preview was registered separately. Automatic approval review rejected
public audience because the current issue did not explicitly authorise that change.
Until approved, private publication is the safe fallback; old public previews
and their audiences are untouched. New deployed browser QA may require that
access decision; source/loopback browser tests still run in both engines.
