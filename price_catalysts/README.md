# EVT-3 — Private price-first catalyst research

Working first catalogue/replay stage of revised [Issue #54](https://github.com/Facemankev/Oil-event-replay/issues/54), stacked on draft #53. This reads the existing six owner-supplied captures. It never imports new prices, edits historical observations, changes the examined learning holdout or writes practice accounts. The public three-answer app remains unchanged.

## Run locally

Use Python 3.11+ from the repository root. The six private files, existing daily-price SQLite database and explicit capture manifest from #53 must be present under ignored `work/stooq-private/`. They are deliberately absent from GitHub and CI. No API key, network access or paid service is needed for calculations. On Windows, replace `python3` with `py`.

```sh
python3 -m price_catalysts scan --db work/stooq-private/prices.sqlite --manifest work/stooq-private/import-first.json --output work/evt3/scan.json
python3 -m price_catalysts study --scan work/evt3/scan.json --previous-study work/stooq-private/study-exact-sessions.json --output work/evt3/study.json
python3 -m price_catalysts render --study work/evt3/study.json --output work/evt3/ledger.html
```

Open `work/evt3/ledger.html` directly in a browser. It is standalone, uses Brendan's actual Gold × Desk stylesheet, and makes no network requests until a source link is deliberately opened. Font fallback uses the stylesheet's Georgia/system fonts offline. It works without a build/server or sign-in. **Do not upload this HTML, JSON, reports, database or CSV files to a public preview or Actions artifact.** Outputs are private to ignored `work/`, created exclusively with restrictive file permissions, and refuse overwrite. Use a new filename to repeat a run. Windows ACLs, rather than POSIX mode bits, determine Windows file access.

The previous study is optional. Without it the ledger says the overlap audit was not supplied; it never labels a historical case unseen. The manifest is mandatory: there is no implicit latest capture/revision. Raw byte fingerprints are checked in a read-only database connection; a scan from different captures is rejected. There is no database promotion/overwrite command.

To create the full local Markdown report without replacing an earlier result:

```python
import json
from pathlib import Path
from price_catalysts.ledger import markdown
report = json.loads(Path('work/evt3/study.json').read_text())
output = Path('work/evt3/REPORT.md')
with output.open('x', encoding='utf-8') as stream:
    output.chmod(0o600)
    stream.write(markdown(report))
```

## What it measures

The timestamped [protocol](protocol.json) was committed/pushed before the new scan. Daily returns and gaps use instrument-specific sample volatility from strictly prior observations (60-bar window, minimum 20); current bars never enter their own baseline. Volume uses the strictly prior positive-volume median, with missing values preserved. Five-/20-session moves and exact-date SPY active returns supplement both return signs. GLD is a descriptive gold ETF proxy, not gold spot or futures.

The top three rises, falls, absolute gaps, multi-session standardized moves, volume ratios and absolute SPY excess returns per instrument are retained. SPY-versus-itself ranks are empty because they are meaningless. The top one in each family defines a bounded research shortlist, deduplicated by symbol/date. All other ranked candidates remain visible as **uninvestigated**, not silently explained or discarded. The source file retains company/regulator/news publication dates, verified clocks where available, unknown clocks, citations, limitations and actual research dates. Later sources remain later corroboration. Day-only same-day stories cannot prove they preceded an opening gap. This is manual bounded research, not an exhaustive news archive or deployed monitor.

A complete independent control pool contains all four fiscal-quarter earnings releases for fiscal 2024 (NVIDIA fiscal 2025) for each of the four companies, plus the named FDA approvals in the protocol. Membership was recorded before its outcomes were measured. Positive, negative and small reactions are retained. Earnings are not interchangeable with clinical setbacks/approvals. A return within one percent is only a descriptive quiet-outcome count, never a sampling or signal threshold.

The replay considers the entire chronological trigger census, rather than only the ranked winners. It keeps the **first** trigger in a 20-session cooldown, not the later peak. Fixed long-after-positive/negative daily-anomaly hypotheses enter at the next reporting close and exit 1/5/20 intervals after entry. Other triggers are discovery only. The discovery jump is never booked as trade profit. Source-action/bad-print flags block hypothetical execution while retaining the candidate. Date-only detection is explicitly an after-complete-bar assumption; original receipt is unknown.

Each signal gets a deterministic non-trigger control selected by strictly prior volatility/trend in the preceding 126 sessions, at least 22 sessions earlier so the largest control window finishes before the signal. No future-return, future-trigger, price-availability or winner filters choose controls. Missing controls/outcomes are retained; no retries. Paired comparisons require both outcomes and report missing-pair counts. Reused controls and cross-asset macro episodes are not independent trials.

Calculations reuse #53's exact-session return/cost validation and the existing SIM engine, with all four unchanged illustrative fee/spread/slippage assumptions, exact-date GBP/USD, SPY under identical costs and a no-trade reference. Reaction windows start at the detection-day close; costed exposure starts at the *next* close. They are intentionally different. Missing dates never shift horizons or fabricate prices/FX. Reviewed NYSE/Arca sessions cover 2023–2026; earlier supplied-date unions can miss shared gaps, so those calendars are explicitly unverified. Current-vintage price/volume adjustment methods and original data availability remain unverified.

## Interpretation and scope

`AUDIT.json` contains actual audit counts only. Detailed movements, subsequent returns, costs, matched-control differences and per-instrument summaries are **private local output**. The owner run scanned 43,507 original observations; neither import counts nor unchanged parent simulations are relabelled new predictions. The complete 2020–2026 historical scan was exposed to discovery and the original 21-event holdout was already examined. Both chronological slices are exploratory, with a 20-session boundary embargo. New curation is not a genuinely untouched evaluation.

There is no model fitting, threshold optimization, best-rule selection, probability calibration or validated Buy. Mixed fixed-rule results require genuinely independent future evidence. Fees, source uncertainty, selection/survivorship, overlapping episodes and missing windows limit interpretation. No original price is corrected, redistributed, re-adjusted or promoted. Private processing does not establish public/training permission under Stooq's terms.

Issue #54 remains open for its next stage: implement bounded permitted feeds, actual receipt/publication/latency/outage accounting, pre-outcome prediction locking and subsequent settlement. The existing EVT-2 pilot is not a continuous financial-news monitor. This PR does not claim live alerts, push notifications, deployed monitoring, prospective predictions or orders.

## Tests

```sh
python3 -m unittest discover -s tests -p test_price_catalysts.py -v
python3 -m ci.offline_checks
python3 -m ci.run_browser --browser chromium
python3 -m ci.run_browser --browser webkit
```

The browser gate uses its existing CLI; run `python3 -m ci.run_browser --help` for output options. CI uses the pinned official Playwright image and real Chromium/WebKit executables, including deliberate failure-capture proofs. The new suite uses visibly **synthetic** prices and sources only, on desktop/iPhone/iPad viewports, with light/dark styles, source links, unexplained/missing states, fee sensitivities, script-injection checks and no external data requests. Device emulation does not replace physical iPhone/iPad Safari testing.
