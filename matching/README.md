# Historical matching and cohort summaries (MAT-3 / CMP-2)

This next stage is a **separate PR stacked on draft PR #16**. It reuses its
SQLite readers, 24-event library, reaction calculation, pure similarity module,
source gating and Gold × Desk page. It does not modify PR #19, its reconciliation
evidence/decisions, canonical oil prices or either historical database schema.
Nothing here resolves or applies the outstanding EIA API/HTML differences.

## Run and reproduce

Python standard library and Node are sufficient; no API key or paid service:

```sh
python3 -m historical --db work/matching-prices.sqlite backfill
python3 -m world_events --db work/matching-events.sqlite import
python3 -m matching.build --horizons 1,3,5,10,20 --traits matching/traits.json --output matching/cohort-catalog.json
node matching/demo.mjs
python3 -m http.server 8000
# Open http://localhost:8000/matching/
```

The new page reads `cohort-catalog.json`: 24 original events × 2 benchmarks ×
5 windows = **240 provisional windows**, using the existing 5,231 Brent and
5,137 WTI observations. Builder defaults and the original `catalog.json` still
retain PR #16's 1/3/7/14/30-day interface and behavior. New horizons are parameters
of that same calculation, not a second implementation. The original validation
report also remains unchanged as a record of the earlier blocked attempt; the
page now identifies the outstanding reconciliation review accurately.

Rebuilding from identical SQLite inputs is byte-identical. Fresh seed imports
have new retrieval timestamps/source IDs; numeric results reproduce, while those
provenance bytes legitimately differ. No import changes or fills canonical data.

`node matching/demo.mjs --check` verifies the committed **DEMONSTRATIONS.json**
against the catalogue hash and current analysis code. Its four cases are:

| Demonstration | Brent 5-day usable windows | Median | Positive / negative |
| --- | ---: | ---: | --- |
| Hypothetical Gulf storm, 110 mph advisory wind | 3 | −0.9643% | 1 / 2 |
| Hypothetical announced production reduction | 3 | −6.0000% | 0 / 3 |
| Harvey query at 2017-08-26, self/later data excluded | 2 | −5.9496% | 0 / 2 |
| Cutoff before any library event | 0 | Unavailable | 0 / 0 |

These are selected-sample demonstrations, not predictions or fabricated events.
For example, the first sample ranges from −10.9349% to +2.4677%. Two of its
storms occurred in the 2008 financial-crisis regime; shared circumstances still
matter even where the price windows do not overlap.

## Matching evidence and unknowns

Input text is a label, not AI extraction. Structured fields drive matching:
category, market, mechanism, location, likely supply/demand channel and optional
advisory wind speed. Base weights from PR #16 remain category 3, commodity 2,
matching mechanism 4 and up to 2 for overlapping location words. More specific
region words take precedence over generic country words. Known opposite
production actions are excluded. General low/moderate/high severity labels do
not become historical facts.

Supply/demand tags are explicit mechanism hypotheses: production reductions →
possible supply constraints; increases/stock releases → possible supply expansion;
weather → mixed supply/demand exposure; sanctions or conflict → possible supply
constraints; pandemic declaration → possible demand contraction. Targets without
established direction remain unknown. These are not measured output changes or
predictions of price direction. Matching channels add 3 points; known opposite
supply channels are excluded. Other mismatches/unknowns add no points.

`traits.json` adds six numerical severity facts from **indexed primary NHC
bulletin text**, with exact URL, printed offset timestamp, event hash, fact-card
hash and check date. Direct archive opening returned 403; the primary bulletin
text was available through web search. These cards are not full-page snapshots.
The source facts are advisory maximum sustained winds (mph): Gustav 110, Ike 110,
Sandy 80, Harvey 125, Laura 150 and Ida 150. They are operational estimates at the
printed time, not later best-track intensities or damage measurements. Harvey's
125 mph is from its 16:00 advisory six hours before the event bulletin; Laura's
is three hours before and Ida's under two hours before. Other severity stays null.

The builder rejects changed event hashes, altered fact cards, unsupported units
and measurements after the supporting event bulletin or over six hours before it.
A query may use a measurement only if its publication UTC date precedes its
cutoff. Within 15 mph adds 3 severity points; within 30 mph adds 1; larger gaps
are weak and excluded from summaries. These tolerances are transparent research
rules, not calibrated economic-risk probabilities. Wind does not measure rainfall,
refinery exposure, outages or economic severity; these gaps stay visible.

Closest event matches never use subsequent price movements. The detailed cards
show up to six matches, including explicitly weak context where useful. Group
statistics exclude weak matches and mismatched requested locations; every sample
member and exclusion is available in the page and demonstration export.

## Price windows and statistics

Each benchmark uses its own actual reporting dates, independently. Anchor to the
supporting-publication date (printed offset times converted to UTC); never replace
unknown publication timing with occurrence. Baseline is the last observation
strictly before the anchor. Endpoint is observation 1, 3, 5, 10 or 20 strictly
after it. The anchor day is excluded because daily price fixing/publication times
are unknown. Saudi's 2019 attack therefore remains anchored to the later EIA
article on 23 September, not backdated to occurrence on the 14th.

These are **reported observation days, a provisional proxy for trading days**;
no authoritative exchange calendar has been established for these spot benchmarks.
Missing holidays/weekends are not filled. An explicit missing observation,
missing/stale baseline, insufficient tail or excessive date gap blocks that
window using PR #16's existing checks. Percentage is `(end / baseline - 1) × 100`,
rounded to four decimals in the catalogue, two in the page. Nonpositive baselines
retain absolute USD/barrel changes with percentage undefined.

For each market/window the page shows eligible/comparable event counts, usable
window count, the percentage denominator, median, min/max range, positive,
negative and flat counts, absolute median and undefined percentage count. Invalid,
unavailable and future data never become zeros. Direction counts use absolute
price signs so a rounded tiny percentage is not mislabelled flat. A primary-only
view hides provisional numbers from both cards and group statistics.

Overlapping baseline-to-end windows are excluded in chronological order (stable
ID tie-breaks), **before looking at outcomes**. This reduces repeated price
episodes but does not establish statistical independence: events may share regimes
or other news. Included IDs, exclusions and reasons are visible. Counts are sample
descriptions, not future probabilities; no win rate or expected return is computed.

## Research priority and evidence

Both benchmarks' five windows are ranked by evidence tier, availability, then a
fixed research-priority score, with stable market/horizon tie-breaks:

- support: `3 × min(non-overlapping windows, 5)`;
- historical movement: `0.4 × min(abs(median percent), 10)` (0–4 points, sign-neutral);
- penalties: fewer than 3 windows = 4; provisional prices = 2; imprecise event
  clocks = 2; missing comparable severity = 1; mixed signs = 2; observed range
  wider than 20 percentage points = 3.

Evidence tier always wins over movement. These design weights are not statistically
fitted signals, predicted profits or an assessment of actual future investment
risk. “Moderate” needs at least three non-overlapping windows, all primary prices,
minute-level event clocks and matched sourced severity. All current summaries are
“Limited”; “Strong” is unavailable without original price-publication/vintage
information. Unknowns and sample/regime risks remain visible alongside results.

The interface describes historical spot-price changes, not earnings on an oil
fund, futures contract or a small paper-trading stake. No fees, spread, leverage,
FX or instrument-specific P&L are inferred. No brokerage/trading code changes.

## Time controls and look-ahead limitations

Self matches and event/supporting-publication dates on or after the query cutoff
are excluded. An outcome enters a statistic or ranking input only when its end
date is strictly before the query date. Altering later outcomes cannot change
historical-query results (tested). Severity also respects its publication cutoff.
No future movement, post-event best-track revision or invented clock is a match
feature. Queries and thresholds do not automatically optimize on the largest gain.

These controls prevent calendar leakage within the present dataset. They **do not
make a point-in-time backtest**: current price vintages and unknown original EIA
publication times still prevent verified historical information sets. All exports
retain `point_in_time_safe=false`. First-public dates remain unestablished for four
events; retrospective supporting evidence is never silently backdated.

## Tests

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
node matching/demo.mjs --check
python3 tests/matching_browser_test.py
python3 tests/browser_test.py
python3 tests/historical_browser_test.py
python3 tests/world_events_browser_test.py
python3 tests/branding_preview_browser_test.py
```

Browser tests use Python Playwright and Chromium at `/usr/bin/chromium`, including
light/dark desktop, iPad portrait/landscape and phone widths, source gates, sample
counts, risk/window selection, safe text, empty states and missing exports. Physical
iPad Safari is not claimed. Dedicated CI runs against this stacked PR's base as
well as main and checks that all underlying data/research foundations remain intact.
