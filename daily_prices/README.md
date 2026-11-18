# DATA-3 — daily prices and separate evaluation lanes

Issue #51, separate draft on #50. **Source acquisition is currently blocked. Zero
new daily observations have been imported; this is not a completed daily-data
expansion.** Direct provider requests receive this environment's transport-policy
403. The requested domain grant is pending. No account, key, subscription, paid
service, proxy, challenge bypass or broker is used. All original prices, reports,
three-answer pages and paper accounts remain unchanged.

This module implements strict daily import/query/versioning, source admission,
retrospective SIM/LEARN reproduction and a separate pre-outcome research journal.
Synthetic bars exist only in explicit automated controls; none is market history
or an ingredient of the published results.

## Sources actually investigated

See [providers.json](providers.json), [runtime-access.json](runtime-access.json)
and [source-audit.json](source-audit.json). Access, usable numeric data and rights
are separate requirements. No advertised free tier or HTTP 200 establishes all three.

| Source | Rights/access finding | Admission |
| --- | --- | --- |
| Nasdaq/Quandl WIKI | Publisher's indexed documentation explicitly says public domain; frozen/deprecated since 2018 and warns against investment/analysis use. Fresh metadata URL returns 404; current API/export documentation requires login. Runtime API request policy-denied. | Parser accepts only original daily WIKI CSV, exact native US ticker, source actions and adjustments. No key/login configured; no successful source capture claimed. |
| Nasdaq historical quotes | Public pages/API do not establish free bulk reuse/redistribution rights. Runtime request policy-denied. | Not admitted. |
| Yahoo | Personal/access conditions do not establish a public daily-series reuse licence. Runtime request policy-denied. | Not admitted; no session/crumb workaround. |
| Stooq | Terms/challenge, adjustment and redistribution questions remain unresolved; runtime request policy-denied. | Not admitted; an unrelated CC0 mirror is not proof of original rights. |
| TWSE open-data index | Government dataset 11755 expressly licenses the linked historical TAIEX resource under OGDL 1.0. Exact-date API and real schema still need direct validation; reader cannot consume CSV. | Resource-specific index parser; no inferred original clock, US benchmark or executable share. |
| TWSE open-data stocks | Dataset 11549 expressly licenses its linked STOCK_DAY_ALL daily resource under OGDL 1.0. Historical website endpoints are not assumed covered. | Strict original export parser; a one-day snapshot does not establish history. Native Taiwan shares/ETFs never substitute for US stocks/ADRs or a gold benchmark. |
| SPDR gold archive | Download link exists, but terms limit personal saving/display and restrict wider reproduction/derivatives; LBMA data has separate restrictions. | No public gold-series import. Downloadable workbook is not a licence. |
| HF/IEX research archive | Compilation CC BY remains subject to IEX terms, academic/educational purpose and required account. It is a single venue, not a consolidated close. | Not admitted under the no-account/no-key controls. |

Only the exact reviewed public-domain/OGDL resources can enter this store. A file
cannot self-certify a different provider as CC0. Licence/identity changes require
review. OGDL attribution: **Taiwan Stock Exchange / government open-data catalogue,
Weighted Stock Price Index Historical Data and Daily Trading Information of Listed
Stocks, 2026; released under the [Open Government Data License 1.0](https://data.gov.tw/license),
with its attribution and reuse conditions.** This attribution does not claim any
Taiwan observations have been imported yet.

## Use the working importer

Python standard library only. On Windows, use `py` instead of `python3`. Run from
repository root. No credentials or secret environment variables are required.

Create an identity JSON file under ignored `work/`, for example:

```json
{"instrument":"NVDA","symbol":"NVDA","venue":"NASDAQ","asset_kind":"equity","calendar_basis":"Provider reporting dates; full exchange calendar unverified"}
```

For an **already lawfully obtained original** WIKI CSV (not Yahoo/Stooq data renamed
as WIKI), or a direct no-key source request after the necessary network grant:

```sh
python3 -m daily_prices --db work/data3-demo/daily.sqlite import-file \
  --source nasdaq_wiki --file work/data3-demo/original.csv \
  --url https://data.nasdaq.com/api/v3/datasets/WIKI/NVDA.csv \
  --identity work/data3-demo/identity.json
python3 -m daily_prices --db work/data3-demo/daily.sqlite fetch \
  --source nasdaq_wiki --identity work/data3-demo/identity.json
# A denied, empty or unsupported response exits unsuccessfully and imports zero.
# This is not a claim that the deprecated anonymous WIKI endpoint works today.
python3 -m daily_prices --db work/data3-demo/daily.sqlite query \
  --capture CAPTURE_ID --from-date 2015-01-01 --through-date 2015-03-31 \
  --basis provider_adjusted
python3 -m daily_prices --db work/data3-demo/daily.sqlite conflicts
python3 -m daily_prices --db work/data3-demo/daily.sqlite evaluate \
  --capture CAPTURE_ID --output work/data3-demo/expanded-diagnostics.json
```

The URL/ticker, currency, native venue, units and exact licensed endpoint must match.
Store exact provider bytes, their fingerprint, retrieval/local-file receipt time,
source-row fields, daily values, raw close, provider-adjusted close, source splits
and cash dividends. Never derive an unavailable adjustment. Original publication/
availability remains null. A local export receipt is not an original HTTP or
historical quote timestamp. WIKI cannot provide post-2018 prices.

Repeated identical payload imports add no observations and preserve first receipt.
Revisions append a new capture and retain originals. No automatic latest value is
chosen. Explicit coherent raw snapshots can accumulate daily history; overlapping
price conflicts and provider/currency/basis mixing are rejected. Adjusted vintages
cannot be spliced. Missing, suspended, delisted, not-yet-listed and unavailable
observations remain distinct from zero. Absent dates are not declared holidays.
Original calendar/price evidence must justify any stronger trading-session claim.

The database is restricted to a dedicated `work/` path. Other databases are
inspected read-only and refused before mutation. SQL triggers prevent updates and
deletes. No historical/canonical price file or EIA reconciliation record is changed.

## Historical results versus genuinely new evaluation

[protocol.json](protocol.json) is pinned and registered before any new price
outcomes. [report.json](report.json) is reproducible from the actual empty source
store and the unchanged parent databases:

- **Original examined evaluation:** retain its report fingerprints, 51 events,
  151 event/asset pairs and 21 later test IDs. Do not overwrite/re-pin parent reports.
- **Expanded historical diagnostics:** attach explicitly admitted daily references,
  rerun SIM-1/LEARN-1 with the same rules, costs, train/validation boundaries,
  negatives and baselines. New pre-2020 training data may be evaluated by the
  original outcome-filtered fitting logic. Changed results on inspected 2020–2026
  cases are labelled **exploratory**, not new validation or evidence of a new edge.
- **Genuinely new lane:** reserve events from **19 November 2026, 00:00 UTC**.
  Record verified publication, actual receipt and immutable signal/model lock
  before observing outcomes. Late/backfilled events and renamed episodes cannot
  become new independent trials. Synthetic/hypothetical controls do not count.

Actual before/after: **0 new quotes / 0 extra settled paths / 0 new qualified
cohorts**. Default SIM remains **69 settled: 34 positive / 35 negative** after
its declared costs; median reference result **-£0.0024**. LEARN retains **4 Watch /
17 research No Action**: one settled positive, one negative, two unknown among
Watch. Zero supported Buy, calibrated accuracy or demonstrated predictive
improvement. The separate new evaluation has **0 real events and 0 outcomes**.
No percentage from those missing outcomes is invented. All 31 wider-asset target
pairs without a baseline daily series remain missing.

IPO coverage reuses the eight already inspected DATA-2 cases, with withdrawn/
suspended/null outcomes intact. Offer prices and reported first-day facts never
become daily quotes or guaranteed allocations. Post-announcement closing-price
windows are exploratory; raw/adjusted basis and currency/venue must match.

```sh
python3 -m daily_prices --db work/data3-check/daily.sqlite evaluate \
  --check --output work/data3-check/report.json
python3 -m unittest discover -s tests -p test_daily_prices.py -v
python3 -m ci.offline_checks
python3 -m ci.run_browser --browser chromium
python3 -m ci.run_browser --browser webkit
```

The prospective API/CLI (`lock`, `settle`) records only research Watch/No Action,
never orders or account changes. Watch requires received, exact-market, non-stale
prior context. Real news needs verified publication evidence. Outcome data must
arrive after the lock; corrections append without changing the signal. Reference
price changes without verified executable product, exact-date FX and costs have
**no net GBP trading result**. The app's decision gates remain in force.

## Exact remaining owner decision / zero-cost alternative

The running cloud environment currently permits package/GitHub hosts, not the
candidate source domains. Its policy applies outside the process sandbox too.
The domain-grant question is pending; no denial is bypassed through CI, mirrors,
credentials or alternate identities. CI source checks measure independent HTTP
access only and never import or relay provider bodies.

To proceed in this cloud: allow the named public-source domains in the running
environment settings, then verify the observed saved policy before direct requests.
That grants network access **not data rights**. A provider still requiring an
account/key or permission remains blocked by Issue #51's controls. The zero-cost
alternative is to run this importer on the owner's PC with an existing legitimate
original export from an explicitly permitted resource, or obtain no-charge written
reuse permission before proposing another source. Do not sign up, pay, substitute
averages or publish restricted quotes. The daily-data acquisition goal remains
unfinished until real permitted observations are actually imported and evaluated.
