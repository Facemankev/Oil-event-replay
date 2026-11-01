# Issue #23 validation — 1 November 2026

[Draft PR #24](https://github.com/Facemankev/Oil-event-replay/pull/24), stacked
on #22/#20/#16. [Successful CI](https://github.com/Facemankev/Oil-event-replay/actions/runs/41350485770).
Latest branch checks appear on the PR. [Public preview](https://market-ripple-ripples-review.g86hz2pjsh.chatgpt.site/ripple/),
no ChatGPT sign-in; native publication succeeded and 67 packaged executable,
price-data and style fingerprints match the tested source.

| Scope | Result |
| --- | --- |
| Python unit/integration | 38 passed |
| Node matching/cohort/research/paper/application/ripple | 46 passed |
| Existing dashboard, matching, histories, events, branding, paper | Browser regressions passed |
| Existing integrated app in Chromium + WebKit | Desktop/iPhone profiles passed |
| New two-screen app in Chromium + WebKit | Desktop/iPhone profiles passed in CI |
| Chart vs virtual fill, forward-only replay, source cutoff, backup | Passed |
| Sparse/unstable paths, missing FX, future-price/event isolation | Passed |
| Reload/response deduplication, accepted/dismissed reviews/outcomes | Passed |
| 375px + landscape, light/dark, large controls, storage denied | Passed |
| Canonical prices/events, parent code/design/core, branch heads | Preserved |
| Public deployed Chromium/WebKit flow without sign-in | Added CI check; latest result on PR Checks |
| Physical iPhone Safari and hands-on desktop | Not tested; device unavailable |

Browser engine tests are not physical-device or iOS certification. CI uses
Playwright 1.64.1 / Ubuntu 24.04; local Chromium used installed Playwright 1.62.0.
Screenshots and JSON reports are in the ripple-browser-reports Actions artifact.
No failing tests were skipped. The inherited chart minimum width was overridden
only for this responsive component; original design.css is unchanged.

Data: 34 genuine exact Brent/GBP pairs from unchanged existing Brent and a new
pinned 35-row FX slice (one blank). 4 September is unavailable for GBP practice;
no filling. Primary EIA articles add context, not price verification. The
11 September publication becomes eligible only on 12 September, never its
measurement week. Original clocks and price vintages remain unestablished;
calendar-leakage guards cannot make this a fully point-in-time-safe backtest.

At entry: 2 five-step comparisons, just 1 complete non-overlapping path. No
supported buy/reversal signal. The £5 experiment is manual; Hold reflects no
exit trigger, and the 5 September Review Sell is the chosen five-step rule.
Explicit close yields about £50.14 virtual cash with zero fees/spread/slippage.
That selected historical example is not a forecast or strategy performance claim.

The first publication was owner-private after automatic approval review blocked
public audience. The owner then explicitly approved public access on 1 November
2026, conditional on no private information/credentials or real trading. The
static package passed privacy/file/credential checks and all 67 executable/data/
style hashes match the tested source. Access is now public; CI verifies the new
public URL without credentials. Existing previews and production are unchanged.

Use the [actual-device acceptance steps](README.md#acceptance-demo), including
Safari touch/rotation, large text, native confirmation and Files backup
restore. Nothing was merged; no real trading, broker or live monitoring was added.
