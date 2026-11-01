# Issue #23 validation — 1 November 2026

[Draft PR #24](https://github.com/Facemankev/Oil-event-replay/pull/24), stacked
on #22/#20/#16. [Successful CI](https://github.com/Facemankev/Oil-event-replay/actions/runs/41350485770).
Latest branch checks appear on the PR. [Private preview](https://market-ripple-ripples-review.g86hz2pjsh.chatgpt.site/ripple/),
same ChatGPT account; native publication succeeded and 67 packaged executable,
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
| New private deployed authenticated browser flow | Not verified; native publication/package integrity only |
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

Automatic approval review rejected public audience for this NEW preview, stating
Issue #23 did not explicitly authorise that access change. It was published
owner-private instead. No credentials were sent to CI and no access workaround
was used. Existing public previews and production are unchanged. Public sharing
requires explicit approval before new unauthenticated remote QA can proceed.

Use the [actual-device acceptance steps](README.md#acceptance-demo), including
Safari sign-in, touch/rotation, large text, native confirmation and Files backup
restore. Nothing was merged; no real trading, broker or live monitoring was added.
