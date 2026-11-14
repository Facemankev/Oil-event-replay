# EVT-1: Nvidia company-news detection and replay

Issue #32, stacked on draft PR #33. A working research layer alongside the oil
study, with no change to the three-step interface, accounts, broker permissions,
original prices, corporate-event database or deployed previews.

## Run the detector and reproducible replay

Python standard library and Node (CI: Python 3.12 / Node 22). No key, paid feed,
service, scheduled task or brokerage is needed.

```sh
node equities/detect.mjs --as-of 2026-11-08T20:01:00Z
node equities/detect.mjs --as-of 2026-11-09T14:31:00Z
node equities/detect.mjs --as-of 2026-11-09T21:01:00Z
node equities/evaluate.mjs --check
node equities/evaluate.mjs --output work/equities/new-report.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
```

`detect.mjs` produces the same three-answer **data contract**: what happened,
likely outcome, suggested action; historical event details remain optional.
This is a command-line research prototype, not an additional application screen.
The existing UI files are byte-unchanged; Nvidia is not enabled as an executable
asset. The historical catalog, sources and replay are real data, not invented
transport fixtures or AI-generated events.

`RESULTS.sha256` pins the full report. `INPUTS.json` pins five curated snapshots;
`.gitattributes` preserves these JSON bytes on Windows. Full numerical traces
belong only in a **new** file inside ignored `work/`, or the CI artifact. Neither
existing files nor source data are overwritten.

## Actual news detection, with receipt history

The official [Nvidia RSS directory](https://nvidianews.nvidia.com/rss) links the
[press-release feed](https://nvidianews.nvidia.com/releases.xml). The collector
supports bounded RSS and Atom, timezone-aware publication/update times, HTML
removal, duplicate entries and public issuer URLs. It rejects XML entities,
unknown timezones, oversized input and credential-bearing URLs.

```sh
python3 -m equities.collect --output work/equities/fresh-feed
# Or import an original locally retained feed without network:
python3 -m equities.collect --input work/original-feed.xml --output work/equities/local-receipt
node equities/detect.mjs --input work/equities/local-receipt/news.json --as-of 2026-11-14T12:00:00Z
```

Each collection creates a new directory with the received XML, its actual byte
hash, receipt time and normalized `news.json`. Keep previous snapshots to retain
versions and the earliest **observed** receipt. No alert message is sent and no
background monitoring is deployed. Direct RSS retrieval failed in this execution
environment; the reader reports an unsupported XML content type. Live collection
is therefore **not certified working here**. The offline collector-to-detector
path is tested end to end; it can be used with a locally saved original feed.

A November 14 receipt cannot appear in a November 9 replay. Bundled historical
cards have no actual first-seen timestamp: a one-minute publication-to-detection
latency is explicitly **simulated**. Test sensitivities are 0, 60, 3,600 and
64,800 seconds. Actual receipt, when provided, is an additional lower boundary.
No historical alert delivery or original first-public dissemination is claimed.

Company detection requires Nvidia/NVDA text and deterministic leadership,
governance, security or regulatory terms. This catches the test case; it is not a
validated universal news interpreter. Detection precision/recall is not established,
and an issuer-only feed can miss earlier independent reporting. Unknown severity
stays unknown. Published
corrections/updates are unavailable before their own timestamps. Same-URL items
and three registered copies of the same issuer statement share one development;
additional copies do not count as independent corroboration or refresh old news.
The latest eligible version and all eligible copies are retained for inspection.

## Sourced chronology and allegations

Six publication cards describe four underlying developments:

| Development | Supporting source | Recorded timing |
| --- | --- | --- |
| Earlier allegations and company response | [ABC report](https://abcnews.com/US/nvidia-responds-report-ceo-allegedly-targeted-chinese-spy/story?id=137704250) | Printed October 31, 2026; clock timezone unestablished, retained as day-only |
| Board initiates independent investigation | [Nvidia](https://nvidianews.nvidia.com/news/statement-from-nvidia-board-of-directors), [issuer syndication](https://www.nasdaq.com/press-release/statement-nvidia-board-directors-2026-11-08), [IR copy](https://investor.nvidia.com/news/press-release-details/2026/Statement-from-NVIDIA-Board-of-Directors/default.aspx) | Syndication printed November 8 at 15:00 EST = 20:00 UTC; the other two copies are day-only |
| Outside counsel retained | [Nvidia November 10 statement](https://nvidianews.nvidia.com/news/statement-from-the-independent-members-of-the-nvidia-board) | Day-only; not available in November 8/9 decisions |
| CEO transition announced | [Nvidia November 12 statement](https://nvidianews.nvidia.com/news/nvidia-announces-ceo-transition) | Day-only; never inserted into earlier inquiry alerts |

The board's announcement confirms an **investigation**, not the allegations.
It also says there was no reason at that point to believe company secrets or
national security had been compromised, and expresses confidence in leadership.
That counterpoint stays attached. Subsequent leadership changes are separate
facts, not proof of the underlying allegation. Personal details are unnecessary
for this market prototype and are not imported.

Day-only clocks cannot produce a claimed initial reaction; their eligibility boundary
is not relabelled as a news timestamp. Missing expected exchange sessions are not
skipped to a later available quote.

Day-only clocks use printed date plus two UTC days as a **conservative eligibility
boundary**, not a claimed release time. Current source pages/fact cards are not
immutable historical article versions; original-vintage verification remains false.
Only relevant article body facts are curated: later-news navigation links are not
part of an earlier article. Prior reporting is acknowledged, so November 8 is not
claimed to be the first public mention.

## First-session reaction: measured daily marks, not verified intraday trades

[Official Nasdaq schedule](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule)
verifies regular 09:30–16:00 New York hours, 2026 holidays and early closes.
Sunday's statement precedes Monday November 9's scheduled 14:30 UTC open and
21:00 UTC close. DST, weekends, Thanksgiving and early closes are tested. Unknown
years fail closed; unscheduled halts, extended-hours products and unexpected
closures are not modelled.

The **price source limitation is material**: Nasdaq's public history page exposed
unavailable data, its API could not be retrieved, and the issuer's lookup exposed
no static prices. A dated Nasdaq Dorsey Wright URL rendered a November 13 heading
and was rejected as a November 9 source. A URL's date is not sufficient evidence.
We do **not** claim to have obtained a verified exchange tape.

The bounded snapshot retains 66 provider rows for six explicitly captured sessions
(November 6 and 9–13), including both open and close: [Stock Analysis](https://stockanalysis.com/stocks/nvda/history/)
and [ChartExchange](https://chartexchange.com/symbol/nasdaq-nvda/historical/) for five
securities, plus the [Nasdaq Composite table](https://finance.yahoo.com/quote/%5EIXIC/history/?p=%5EIXIC).
The two providers may share upstream data; agreement is not independent provenance.
These are **current-vintage daily table marks**, with nominal scheduled boundaries,
not proven original quote availability or individual transaction timestamps.
Source URLs, table locators and limitations are in `sources.json`.

Nvidia closes agree across both tables (also [reported by ABC](https://abcnews.com/Business/nvidia-stock-falls-after-company-opens-probe-ceo/story?id=137970524)):
November 6 **$186.64**, November 9 **$178.67**, a **−4.27%** close-to-close comparison.
The first table displays November 9 open **$173.07**, the second **$173.06**.
The detector retains both and refuses an exact reconciled opening quote. The
implied gap range is about **−7.28% to −7.27%**; it is a retrospective table range,
not a verified opening transaction or fill. There is no fabricated 09:31 quote.

At Sunday/pre-open cutoffs no future open/close is exposed. At 09:31 only nominal
opening evidence can be discussed; that large opening move is already reflected
in those marks. At 16:01 the first closing comparison becomes visible. Intraday
news requires an actual post-news quote/baseline: a day's open or high/low cannot
be substituted. Daily reference context is explicitly separate from a valid
post-news reaction. **Verified intraday reactions: zero.**

## Secondary/tertiary ripples and baseline cross-check

The same November 6 close → November 9 close window gives:

| Reference | Observed daily change | Versus Nasdaq Composite, percentage points |
| --- | ---: | ---: |
| Nvidia | −4.27% | −7.01 |
| AMD | +13.26% | +10.52 |
| Broadcom | +8.78% | +6.04 |
| Microsoft | +2.75% | +0.00 |
| QQQ, Nasdaq-100 ETF | +3.54% | +0.80 |
| Nasdaq Composite | +2.74% | baseline |

AMD/Broadcom competitor substitution and later AI procurement/spending effects
are **hypotheses**, not proved transmission paths or trading opportunities.
Microsoft is a bounded tertiary AI-spending reference. QQQ and Nasdaq both include
Nvidia: neither is an independent control or a fitted risk-adjusted counterfactual.
Other earnings, macro news, oil moves, market recovery and company-specific news
can explain co-moves. The observed positive peer moves oppose a blanket assumption
that every chipmaker must fall with Nvidia. Differences in percentage returns do
not establish causation, abnormal-return significance or a forecast.

## Genuine historical comparisons before a paper decision

Four historical corporate episodes were selected by mechanism before examining
returns, not by selecting the largest declines:

| Case | Why inspect it | Where comparison is weak | Reference closing change |
| --- | --- | --- | ---: |
| [Intel 2018 CEO departure](https://www.intc.com/news-events/press-releases/detail/146/intel-ceo-brian-krzanich-resigns-board-appoints-bob-swan) | Semiconductor leadership/governance | Confirmed departure; contemporaneous guidance increase; no intelligence finding | −2.38% |
| [Equifax 2017 security disclosure](https://investor.equifax.com/news-events/press-releases/detail/240/equifax-announces-cybersecurity-incident-involving-consumer) | Security/governance exposure | Confirmed consumer-data breach, different industry, imprecise original release clock | −13.66% |
| [Tesla 2018 civil disclosure charges](https://www.sec.gov/newsroom/press-releases/2018-219) | CEO/governance/regulatory scrutiny | Different legal mechanism and industry; [later settlement](https://www.sec.gov/newsroom/press-releases/2018-226) changes the story | Missing sourced prices in this slice |
| [Nvidia 2025 H20 restriction](https://www.sec.gov/Archives/edgar/data/1045810/000104581025000082/nvda-20250409.htm) | Same company, China/security-related regulatory exposure | Confirmed product restriction; not an unresolved leadership inquiry; tariff/macro confounders | −6.87% |

Nvidia's private notice on April 9 is distinct from the April 15
[public filing/acceptance](https://www.sec.gov/Archives/edgar/data/1045810/0001045810-25-000082-index.html).
Intel's [filing](https://www.intc.com/filings-reports/all-sec-filings/content/0001193125-18-199045/d598882d8k.htm)
separately records the June 20 occurrence and June 21 public announcement.
Price references are sourced in `history.json`: a [UBS filing](https://www.sec.gov/Archives/edgar/data/1114446/000111444618007465/tc4570597f_1fwp.htm),
a [later SEC document citing Equifax closes](https://www.sec.gov/litigation/complaints/2018/comp-pr2018-40.pdf),
and two bank filings citing Nvidia's [April 15](https://www.sec.gov/Archives/edgar/data/200245/000191870425006605/form424b2.htm)
and [April 16](https://www.sec.gov/Archives/edgar/data/831001/000095010325005095/dp227960_424b8-us2559653.htm)
closing values. SEC hosting is **not SEC verification of bank-supplied market data**.
Missing Tesla prices are not invented or replaced with rounded split-adjusted values.

These are reference closing-day comparisons, not a pooled causal return estimate.
Ranking uses shared category, same company/sector and procedural stage; it never
reads returns. One historical episode counts once, and later settlement evidence
is invisible before its publication boundary. All four are weak at the initial
Nvidia inquiry cutoff; none has sourced comparable severity and original quote
vintage/print evidence. **Qualified cases: zero**, below the inherited conservative
minimum of eight. That threshold is not validated as a profitable equity policy.
A small hand-selected group of negative examples is not the probability of a fall.

## Replay findings and controls

Eight chronological cutoffs cover before the board release, Sunday receipt,
pre-open, first minute, one regular-market hour, first close, later counsel and
later transition. **Buy 0 / Short 0 / No Action 8 / paper trades 0.** The detector
may produce a research Monitor item; it does not send an alert or suggest chasing
a decline. Staleness uses regular-session minutes (60-minute limit) and a seven-day
wall-age cap, so a weekend alone does not age a Sunday release by a trading day.
Reposts do not reset its original clock. Latency does not make an earlier move
available to a later entrant.

Nvidia remains unsupported by the existing dated GBP paper-execution model. No
FX, instrument, liquidity, borrow availability, fees, stop fills, probabilities,
portfolio performance or executable price is invented. The original paper account
and its manual practice/exit reviews remain untouched. Findings are descriptive
research, not a recommendation or guarantee.

Local validation: **60 Python / 99 JavaScript tests pass**, all ten Chromium
browser scripts pass, the original database imports repeat safely and all three
parent reports reproduce. [Draft PR #34 Checks](https://github.com/Facemankev/Oil-event-replay/pull/34/checks)
runs the complete WebKit/browser suite and retains the report, demos and screenshots.

Tests cover bounded RSS/Atom parsing and collector-to-detector integration,
source identity, receipt/version timing, syndication, disputed counterpoints,
DST/holidays/unknown calendar, stale news, intraday missing data, conflicting opens,
corporate-action basis, opposite peer moves, future price/headline mutation,
outcome-blind historical ranks and deterministic reports. Full Actions also runs
all parent unit/database/report/browser regressions and proves oil/UI preservation.
Physical iPhone/iPad Safari acceptance remains a human check; automated profiles
are not physical-device tests.

Next bounded stage: make a verified timestamped public-equity feed/replay available,
retain original news receipt/version history, and expand procedurally comparable
corporate episodes with market-relative outcomes. Then review a separate GBP equity
paper-execution policy. Continue to default Monitor / No Action until supported.
