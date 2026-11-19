# SIGNAL-1 — Historical signal ratings

[Draft PR #56](https://github.com/Facemankev/Oil-event-replay/pull/56), stacked on #55. A working private historical opportunity dashboard uses the existing EVT-3 features, catalyst research and SIM cost/FX engine. The original app retains its three questions and paper-trading rules; an optional research link opens the empty SIGNAL-1 shell. No price data is bundled with it.

## Run on your PC

Python 3.11+; existing six private captures, explicit #53 import manifest and #55 scan/ledger. No API key, network data call, account or paid service. From the repo root (Windows: replace `python3` with `py`):

```sh
python3 -m signal_ratings analyse --scan work/evt3/scan-v2.json --ledger work/evt3/study-paired.json --as-of 2026-11-19 --output work/signal1/analysis.json
python3 -m signal_ratings render --report work/signal1/analysis.json --output work/signal1/dashboard.html
python3 -m signal_ratings screen --report work/signal1/analysis.json --output work/signal1/screen.json
```

Set the assessment date deliberately and adjust the existing private filenames as needed. `--db` and `--manifest` explicitly select captures; there is no implicit latest/revision. The database opens read-only and original raw-byte fingerprints are verified. Use new output names for repeat runs; every output is restricted to ignored `work/`, created exclusively and never overwritten. POSIX files are owner-readable; Windows ACLs determine actual Windows access.

Open the standalone `dashboard.html`, or serve it only on your own PC:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory work/signal1
```

Then open `http://127.0.0.1:8765/dashboard.html`. The generated file embeds Brendan's actual Gold × Desk CSS, the same three-question layout and a compact report, with no automatic external requests. The public `/signals/` page is an empty shell: it can read your compact `screen.json` locally through its file chooser, without uploading or storing it. Never publicly host the generated HTML/JSON, detailed analysis, original CSVs or database. The larger full analysis is deliberately separate from the phone-sized screen projection.

## Ratings and safeguards

- **NO ACTION:** incomplete, small, conflicting or poor historical evidence. Reasons remain visible, with all missing/losing outcomes counted.
- **POSSIBLE:** a fixed exploratory hypothesis passes the registered historical evidence checks. Displayed direction/timeframe, sample breadth, observed successes/failures, mean/median/range, SPY excess, net GBP, controls and cost sensitivity explain the assessment. This is a watch for confirmation, **not a current forecast or approved trade**.
- **LIKELY:** requires a reviewed, hash-pinned independent validation artifact, with genuinely new pre-outcome predictions after policy registration, audited independent samples and primary point-in-time prices/usage rights. Stress costs, benchmark/control robustness and multiple-testing review are required. High historical success alone never qualifies. The registry is empty: **zero Likely**. Imported files and caller flags cannot self-certify it. This release's browser rejects imported Likely badges; a future reviewed validation release must update both the registry and client trust boundary.

Research ratings never mutate a paper account, execute orders or relax existing source/execution gates. DOWN is a defensive downside-risk hypothesis; returns remain the observed asset movement and the **existing long** simulation. No sign-flipped short P&L, borrow availability, leverage or short orders are fabricated. Cost assumptions are illustrative sensitivities, not a quoted brokerage tariff. The £1-per-leg scenario may make a rise hypothesis unusable while a downside-risk watch remains descriptive; that is not a profitable short trade.

## Fixed method

[policy.json](policy.json) was committed/pushed before the new summaries. Ten fixed pattern families: sharp daily rise/fall, opening gap rise/fall, established prior up/down trend, unusual volume with rising/falling price, and rise/fall plus volume. Both directions explicitly test continuation and reversal. All six assets, 1/5/20 sessions and four unchanged SIM cost assumptions are retained. No threshold optimization, model fitting, best-rule promotion or probability calibration.

Features reuse EVT-3's strictly prior instrument-specific 60-observation volatility and median-volume history. Current volume/returns do not enter their own baseline. Trend uses the prior 20-session endpoint movement scaled by prior volatility. A predicate fires only after a complete daily bar; original historical receipt is unknown. Known bad-print/action/missing-bar flags do not become signals. First qualifying bars receive a 20-session cooldown per asset/pattern, rather than later peaks chosen by their outcomes.

Hypothetical entry is the next reporting close; exit is H later intervals. This differs from discovery-day reaction: **the already-realised jump is not profit**. Exact-date SPY, GBP/USD and every required session are validated by the existing price/SIM code. Missing observations never shift entry or exit. Pending windows are recorded separately; only windows that matured **strictly before** the assessment date enter its statistics. The 20-session chronological boundary embargo remains. Pre-2023 calendars are supplied-date unions, explicitly unverified; reviewed NYSE/Arca calendars cover 2023–2026.

Non-trigger price/volume controls come from similar strictly prior volatility/trend in the preceding 126 sessions, at least 22 sessions earlier so their largest window ends before the signal. Selection does not inspect later returns or choose quiet future outcomes. Missing controls are retained. Non-overlap, reused controls and simultaneous macro periods do not establish independence. All historical slices, including the examined 2020–2026 period, remain exploratory; newly computed statistics are **not new untouched tests**. The original learning holdout and reports are unchanged.

Possible's fixed thresholds require ten complete cases, three years, five later examined cases, 60% coverage and ten complete matched controls. Direction-consistent mean/median returns, after-cost long results, later-slice results and median control/benchmark differences must agree. SPY self-relative excess is mechanically zero, not an alpha claim. Evidence coverage/sample breadth ranks first, adverse movement next, observed median movement last. Success means the later observed USD price direction; it is not net profit or future odds.

The existing 39 dated source facts and complete 18 issuer/FDA controls are reused. Recurring contexts include earnings/guidance, licensing/partnerships, clinical results, acquisitions, litigation and macro shocks, with opposite and unexplained cases. These categories were researched after price discovery and **never become earlier signal inputs**. The price-selected catalogue cannot estimate catalyst recurrence or causal effects. Source publication dates, unknown clocks and later corroboration remain distinct. Data authentication, adjustments and original availability remain unresolved; no canonical/public/learning-source admission changes.

## Results and checks

`AUDIT.json` publishes audit counts only. All actual prices, returns, successful/unsuccessful examples, fees and detailed assessments stay owner-private under `work/signal1/`. The private report can be generated with `signal_ratings.report.markdown(report)`; the full JSON retains all groups, windows, costs, missing cases and source cross-checks. Candidate counts share events and timeframes and must not be presented as independent opportunities.

```sh
python3 -m unittest discover -s tests -p test_signal_ratings.py -v
node --test tests/signals.test.mjs
python3 -m ci.offline_checks
python3 -m ci.run_browser --browser chromium
python3 -m ci.run_browser --browser webkit
```

All original checks remain required. Both engines run the new three-question/rating/cost/example/private-import suite with synthetic fixtures only, including the actual static module entry point, failed policy loading, forged Likely/Possible rejection, XSS, unknown metrics and future evidence. Desktop/iPhone/iPad viewports, light/dark and touch do not replace physical Safari testing. No raw owner files are available in CI artifacts.
