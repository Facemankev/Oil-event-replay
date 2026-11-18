# DATA-2 — verified free reference evidence

Issue #47, stacked on CI-1 #49 and LEARN-1 #46. No live trading, charges, accounts,
credentials, merge, canonical price correction or screen change. This is a working
SQLite import/query/evaluation module, not a connected daily equity data service.

## What was actually imported

- **99** selected World Bank publication values from **3** official 2020 Pink Sheet
  editions (July, September, December), **51 distinct asset/frequency/period keys**.
  Each of Brent, WTI and gold has 33 edition values / 17 distinct periods:
  annual 2017–2019, quarters 2019 Q2–2020 Q3, months April–November 2020.
  Overlapping editions and frequencies are **not independent daily prices**.
- **8 separate IPO research episodes**: Etsy, Lyft, Uber, We Company, Ant Group,
  Airbnb, Deliveroo and Arm. Five attributed first-close references (3 above and
  2 below offer), one missing reaction, two uncompleted listings with null returns.
  No quote path, retail allocation, listing success or zero return is invented.
- **0 new daily security quotes**, **0 verified original historical vintages**.
  Existing 26,074 numeric EIA/Fed daily references, 66 secondary candidate quotes,
  13 reporting-only reactions and all old event/price files remain unchanged.

World Bank attribution: **World Bank, Commodity Price Data (Pink Sheet), archived
2020 editions**, [public dataset, CC BY 4.0](https://datacatalog.worldbank.org/search/dataset/0038238/commodity-prices-history-and-projections),
[licence](https://datacatalog.worldbank.org/public-licenses). Selected numerical
Brent, WTI and gold rows were transcribed from the visible official tables through
the supported reader. `sources/world-bank.json` links each original PDF and cell
locator; the CSV byte hash identifies **our transcription**, not downloaded PDF
bytes. Changes: selection, transcription, typed frequency/units/provenance. No
third-party raw daily bullion feed, ETF, futures or adjusted security history is
claimed. Numerical dates do not establish publication receipt or archived version
integrity. Original HTTP hashes and availability timestamps remain null.

An additional April capture was withheld entirely after the repository privacy
guard flagged its numeric public source identifier. Guard and allowed words remain
unchanged. January–March monthly values are consequently absent, not filled in.

IPO facts link issuer announcements, SEC/exchange documents and explicitly
attributed AP/PA/Reuters reporting. Only short factual data and links are extracted;
no article text, bulk security feed or general quote redistribution right is
claimed. Deliveroo uses secondary PA reporting because the issuer PDF was denied;
GBp/share is pence, not GBP. Arm's body/header dates differ; both are documented.
Lyft/Airbnb later annual reports do not prove their first-close facts were available
at the original event time. We Company's 2019 withdrawal request never inherits
quotes from its later SPAC listing. None has verified corporate-action factors,
complete daily exchange calendars, delisting coverage or original receipt times.

## Reproduce, query and inspect differences

Python standard library only; work from repository root. `work/` is ignored.

```sh
python3 -m data_expansion --db work/data2-demo/references.sqlite import
python3 -m data_expansion --db work/data2-demo/references.sqlite import
# First run: 110 inserted rows (3 sources + 99 values + 8 facts); repeat: zero.
python3 -m data_expansion --db work/data2-demo/references.sqlite query \
  --instrument wb-gold-average --frequency monthly \
  --from-date 2020-04-01 --through-date 2020-11-30
python3 -m data_expansion --db work/data2-demo/references.sqlite revisions
python3 -m data_expansion --db work/data2-demo/references.sqlite evaluate \
  --check --output work/data2-demo/evaluation.json
python3 -m unittest discover -s tests -p test_data_expansion.py -v
python3 -m ci.offline_checks
python3 -m ci.run_browser --browser chromium
python3 -m ci.run_browser --browser webkit
```

Query returns all matching edition versions for periods **overlapping** the date
range; frequency is mandatory. `--as-of YYYY-MM-DD` filters declared document days,
not original quote/news availability. `--original-vintage-only` returns no rows
because no original vintage is verified. Missing periods stay missing. Annual and
quarter cells are not recast as daily observations or duplicated signals.

Only a dedicated database under `work/` is allowed. Other existing SQLite stores
are inspected read-only and refused before mutation. Immutable triggers prevent
updates/deletes. Identical reimports insert zero. A changed cell under identical
source metadata is rejected atomically. A reviewed new capture with different
metadata appends a source version and retains every old value; `revisions` lists
conflicting asset/period values. Evaluation refuses ambiguous multiple captures
until explicitly reviewed. Current three editions have **0 conflicting selected
periods**. The oil-average crosscheck is context between different aggregations,
not EIA reconciliation or permission to correct daily prices. PR #19 is separate.

## Honest before/after result

[report.json](report.json) is reproduced from the **imported SQLite data**. Both
SIM-1 and LEARN-1 actually run before and after attaching the typed new references.
All 51 original events, 151 targeted pairs, 7 training / 11 validation / 21 retained
test IDs, rules, costs and boundaries remain fixed. The raw reports and outcomes
are identical; additional averages/facts cannot settle missing daily price paths.

| Metric | Before | After |
| --- | ---: | ---: |
| Settled default SIM references | 69 | 69 |
| Positive / negative, declared costs | 34 / 35 | 34 / 35 |
| Median net result per hypothetical reference case | -£0.0024 | -£0.0024 |
| LEARN test Watch / No Action | 4 / 17 | 4 / 17 |
| Settled Watch: positive / negative / unknown | 1 / 1 / 2 | 1 / 1 / 2 |
| Qualified models / supported entries | 0 / 0 | 0 / 0 |

The two settled Watch hypotheses are OPEC April 2020 **-£0.2746** and July 2021
**+£0.0669**. Laura/Ida remain unsettled. This is not a portfolio total or executable
fill. **No predictive improvement demonstrated**. The 1/2 conditional hit fraction
is not calibrated accuracy or a validated edge; unknown outcomes are not losses.
All 21 validated test decisions remain No Action; none becomes a supported Buy.

IPO cases remain in a separate, manually curated research reserve. Date partitions
are descriptive only, not a newly valid heldout test. Episode IDs deduplicate an
offering, and repeated publication editions never expand old sample membership.
Positive/negative contrasts are coverage research, not a population sample or an
outcome-blind estimate. The already examined holdout is not re-used to tune rules.

## Actual access and remaining gaps

[provider-audit.json](provider-audit.json) records actual coverage, free-tier limits,
rights, symbols/basis, survivorship and blockers. FRED Nasdaq explicitly requires
copyright pre-approval; Stooq terms reader challenges and basis/redistribution are
unverified. No keyed free tier is claimed connected; no account/trial/paid action
is configured. Complete daily adjusted NVDA/AMD/biotech/index/gold/IPO histories
remain missing under verified public-use rights. Do not infer fills from references.

[runtime-access.json](runtime-access.json) contains actual anonymous direct runtime
probes: official World Bank XLS, SEC withdrawal document and Fed table all returned
transport-policy 403. No denial was bypassed. Supported reader transcription access
is recorded separately and never described as a successful raw HTTP download.

```sh
python3 -m data_expansion.probe --environment runtime \
  --output work/data2-access/first-runtime.json
```

The separate **Anonymous official data access receipts** Actions workflow runs the
same fixed bounded endpoints independently in CI, keeps only status/size/type/time,
and uploads its JSON receipt. No body is saved/imported/relayed, no keys, redirects,
retries or provider fallbacks. HTTP 200 proves neither valid prices nor rights.
A completed probe workflow may legitimately contain 403/connection failures; it is
an availability measurement, not an all-sources-working badge. The required browser
and offline gate stays fixture-only and fails actual application/test regressions.

Next useful data milestone: obtain a genuinely free, usable adjusted daily equity
and gold history with actions/calendar/delisted coverage and source availability,
then register fresh chronological examples **before** inspecting outcomes. There
is no basis here to claim that more rows alone improved predictive performance.
