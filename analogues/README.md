# INT-2: qualified historical analogues

Issue #31, stacked on draft PR #30. This is a working, bounded research slice,
using its actual primary oil/FX snapshots and frozen INT-1 paper policy. It does
not change the approved three-step application, saved practice accounts, original
24-event database, canonical prices, PR #19 or any deployed preview.

## Run it

Python standard library and Node (CI: Python 3.12 / Node 22); no key, download,
paid service or browser build is needed for the study.

```sh
node analogues/demo.mjs
node analogues/demo.mjs harvey-2017-texas
node analogues/evaluate.mjs --check
node analogues/evaluate.mjs --output work/int2/new-report.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
```

The output filename must be new and inside `work/`. `RESULTS.sha256` pins the
full deterministic report; `INPUTS.json` pins the three curated input files.
Full derived numerical traces stay in local `work/` or the CI artifact instead
of committing a large generated report. Existing parent reports reproduce
unchanged with `node intelligence/evaluate.mjs --check` and
`node verification/evaluate.mjs --check`.

The demo prints actual selected examples, publication/occurrence clocks,
positive/negative counts, median/range, source limitations and No Action reasons.
There is no new page to learn or deployment to replace the existing preview.

## More events, without counting the same storm twice

Eight additional genuine US Gulf landfalls supplement the original 24 only in
this research catalog. Selected by mechanism and geography before inspecting
returns, including weaker cases. This is not an exhaustive storm census or a
representative sample. These are **operational bulletin winds**, not final
best-track intensity, flooding, oil shut-ins or economic severity.

| Additional event | Occurrence, CDT (approximate) | Supporting issuance, CDT | Wind mph |
| --- | --- | --- | ---: |
| [Humberto](https://www.nhc.noaa.gov/archive/2007/al09/al092007.update.09130713.shtml) | 2007-09-13 02:00 | 02:10 | 85 |
| [Dolly](https://www.nhc.noaa.gov/archive/2008/al04/al042008.posest.07231753.shtml) | 2008-07-23 13:00 | 13:00 | 100* |
| [Isaac](https://www.nhc.noaa.gov/archive/2012/al09/al092012.posest.08282356.shtml) | 2012-08-28 18:45 | 19:00 | 80 |
| [Nate](https://www.nhc.noaa.gov/archive/2017/al16/al162017.public_a.014.shtml) | 2017-10-07 19:00 | 19:00 | 85 |
| [Delta](https://www.nhc.noaa.gov/archive/2020/al26/al262020.update.10092259.shtml) | 2020-10-09 18:00 | 18:00 | 100 |
| [Zeta](https://www.nhc.noaa.gov/archive/2020/al28/al282020.public.017.shtml) | 2020-10-28 16:00 | 16:00 | 110 |
| [Nicholas](https://www.nhc.noaa.gov/archive/2021/al14/al142021.public_a.008.shtml) | 2021-09-14 00:30 | 01:00 | 75 |
| [Francine](https://www.nhc.noaa.gov/archive/2024/al06/al062024.update.09112157.shtml) | 2024-09-11 17:00 | 17:00 | 100 |

*Dolly's wind is from [advisory 13A at noon](https://www.nhc.noaa.gov/archive/2008/al04/al042008.public_a.013.shtml),
not inferred from the later position estimate. Printed headers govern; archive
filenames can precede a nominal issuance time. The supporting bulletin is the
earliest located here, not a proven earliest public disclosure: forecasts and
precautionary shutdowns preceded landfall. Some local dates cross UTC midnight;
full offset timestamps are retained. Existing publication-day anchor semantics
remain unchanged, rather than silently changing the parent study.

Source facts were checked through indexed **primary NHC products**. Direct archive
opens returned 403. `capture_kind` records that limitation; no original HTTP byte
hash is claimed. The source cards are concise fact transcriptions, not page copies.

## Auditable qualification

`engine.mjs` delegates similarity scoring to the existing matcher. It adds an
explicit US Gulf exposure-region gate and storm episode identity from NHC IDs.
Only the bounded Gulf-landfall slice receives these additional candidates; other
categories are retained for coverage/abstention auditing, without pretending they
have acquired new analogues.

1. Same category, affected benchmark and landfall mechanism; sourced US Gulf region.
2. Operational wind known before cutoff, within the existing **30 mph** tolerance.
   Unknown magnitude or different exposure is a recorded exclusion. Wind does not
   establish comparable refinery exposure, flood damage, season or recovery.
3. Self, future/unknown public clocks, duplicate event IDs and repeated bulletins
   from the same NHC episode are excluded. The earliest located supporting bulletin
   represents each episode; an attractive later bulletin cannot replace a failed one.
4. Select chronological, non-overlapping **21-observation precondition + five-observation
   reaction** intervals before reading returns. Reserve dates even if a later data
   or condition gate fails; do not replace failed cases with profitable neighbours.
5. Reuse the unchanged parent precondition, complete positive price-path, original
   source/availability and vintage tests. Reuse minimum **8** qualified cases,
   prior-five-return adjustment, volatility-ratio, split-half/leave-one-out,
   75% sign consistency and dispersion gates. No threshold fitted to these results.

Non-overlap is a duplication control, **not proof of independence**. Market regimes,
other news, anticipatory pricing and shared Gulf infrastructure remain confounders.
The crude supply constraint and lost refinery demand can oppose each other.

At Harvey, the expansion gives **two** usable current-data, condition-compatible
cases (Dolly and Gustav), previously one with these stricter episode/context rules.
Both descriptive GBP reactions are negative: median **−5.36%**, range **−7.65% to
−3.07%**. Ike overlaps Gustav's context and is excluded. Humberto/Isaac are too weak
on this operational wind comparison, Sandy has different exposure. This supports
caution, not a short position or a guarantee of falling prices.

Francine has eight structural episode candidates, but only six usable current-data
reaction paths (three positive/three negative); condition and original-as-of tests
still fail. Zeta is excluded because its context overlaps Delta's reaction.
Adding names does not produce eight fully qualified cases.

## Evidence at each decision point

Four dated Federal Reserve H.10 releases, **20 observations: 19 numeric / 1 ND**,
all agree with the current primary table at original precision:

- [2017-09-05](https://www.federalreserve.gov/releases/h10/20170905/): August 28–September 1.
- [2017-09-11](https://www.federalreserve.gov/releases/h10/20170911/): September 4–8; September 4 is explicitly ND.
- [2020-10-13](https://www.federalreserve.gov/releases/h10/20201013/): October 5–9.
- [2020-11-02](https://www.federalreserve.gov/releases/h10/20201102/): October 26–30.

`fxEvidenceAt` requires the dated release to be eligible **strictly before** the
cutoff. Day-only publication with unknown clock/timezone uses printed date plus
two UTC days as a conservative study boundary. This covers an unspecified local
release day; it is **not a claimed actual publication clock**. Rates are USD per
GBP; GBP oil is USD oil divided by that exact rate. No ND filling or new rate import.

A dated official page is stronger evidence than an observation date alone, but it
is not immutable historical bytes or proof of an original vintage. Those fields
remain null. In particular, August 28 FX in the September 5 release cannot justify
an August 28 execution. Oil original-vintage evidence remains unavailable; **zero
complete historical price/FX paths are certified original-as-of**.

Harvey's existing EIA infrastructure and later refinery articles are reused under
the same conservative day-publication rule. First/second/third-order paths remain
explicit hypotheses with counterarguments. The September refinery finding cannot
appear in August. Harvey-specific observations are not copied onto other storms.
For other storms, missing sourced exposure/outage magnitude stays missing.

## Reproducible results

Decisions use the first numeric oil observation strictly after the supporting
publication anchor, with an explicit end-of-decision-day cutoff assumption. Freeze
paper decisions before attaching future returns. Price calendars are each
benchmark's **numeric reporting observations**, not a verified exchange calendar.

The analogue reaction starts at the last observation **before** the publication
anchor; it describes the surrounding event. The costed counterfactual execution
baseline starts **after** the anchor and exits five oil observations later. They
are different windows; event-reaction statistics are not claimed executable returns.

| Scope | Complete fixed-five Brent | Complete fixed-five WTI | Buy / Hold / Review Sell / No Action, Brent |
| --- | ---: | ---: | --- |
| Original 24 | 18/24 | 22/24 | 0 / 0 / 0 / 24 |
| Expanded 32 | 24/32 | 28/32 | 0 / 0 / 0 / 32 |

WTI also abstains in all cases and stays **research-only**. No supported opportunity
emerges. All events lack eight original-as-of qualified analogues and original
price/FX vintages; 17 expanded Brent events also have incomplete preconditions,
and three lack an exact entry price/FX pair. Gaps are not assigned a holiday cause
without evidence. No trade is invented to create Hold or Review Sell.

Complete current-data entry + horizon coverage, **1 / 3 / 5 / 10 / 20**:

| Scope/market | Counts |
| --- | --- |
| Original Brent | 23 / 22 / 18 / 15 / 11 |
| Original WTI | 24 / 23 / 22 / 20 / 17 |
| Expanded Brent | 29 / 28 / 24 / 20 / 15 |
| Expanded WTI | 30 / 29 / 28 / 25 / 21 |

Costed £5 Brent counterfactuals, including negative cases, reuse DAT-4 definitions:
zero costs, declared (one penny per leg, 10 bps spread, 5 bps slippage per leg),
stressed (ten pence per leg, 30 bps spread, 15 bps slippage per leg).

| Scope | Zero positive/negative | Declared positive/negative | Stressed positive/negative |
| --- | --- | --- | --- |
| Original 18 complete baselines | 9/9 | 9/9 | 5/13 |
| Expanded 24 complete baselines | 14/10 | 13/11 | 6/18 |

These are independent counterfactual examples, not executed policy entries or an
overlapping portfolio. Policy remains cash-only (£50), with zero trades and
undefined predictive accuracy. Largest movement never overrides evidence/risk.

## Original EIA conflict remains separate

`api-evidence.json` records recovery scope, expected sanitized snapshot fingerprints
from immutable PR #19 review and the unresolved result. No original response or
SQLite snapshot was located in task data. The earlier attachment could not be
resolved by the file service in this session; its retained review is not the payload.
The older three numbers matching previous numeric observation dates is insufficient
to prove an alignment bug or revision. No original price or reconciliation artifact
is changed, and no API key is needed or requested.

If the original historical SQLite database is retained locally, this optional
inspector opens it read-only, verifies the exact expected sanitized payload hash,
replays dates/values/units/pagination and compares parsed vs stored rows:

```sh
python3 -m analogues.inspect_eia --db work/original-prices.sqlite
```

It refuses a missing file, suppresses input/error details, never prints request
metadata/payloads, does not migrate/import/write, and makes no network request.
Synthetic recovery tests are transport fixtures, never historical evidence. A new
API fetch cannot recover the old response. Expected hash recovery still does not
establish a historical revision timestamp.

## Validation and next stage

New tests cover source facts, conservative release boundaries, missing FX, weaker
comparisons, duplicate IDs/episodes, full-context overlap, future price mutation,
late counterevidence, original/expanded counts, cost sensitivity and safe read-only
recovery. The INT-2 Actions workflow runs all parent tests, repeatable real database
imports, both pinned parent reports, new report/demo, source/UI preservation and
Chromium/WebKit desktop/iPhone/iPad browser regressions. Physical-device Safari
acceptance remains a human check; automated profiles do not establish a device pass.

Next bounded step: recover original sanitized EIA evidence; retain authentic dated
price releases and more weekly FX vintages around a **single** storm cohort, with
sourced outages/recovery/forecast timing. Then re-evaluate the unchanged gates.
Do not add live trading or lower thresholds to force a positive signal.
