# Issue #21 validation — 30 October 2026

[Draft PR #22](https://github.com/Facemankev/Oil-event-replay/pull/22), stacked
on #20/#16. [Public preview](https://market-ripple-app-review.g86hz2pjsh.chatgpt.site/app/),
no sign-in; Sites version 3. [Successful full CI run](https://github.com/Facemankev/Oil-event-replay/actions/runs/41087389133).
Final commit status is available on the PR's Checks tab.

| Check | Result |
| --- | --- |
| Python unit/integration | 35 passed |
| Node matching/cohort/research/application/paper accounting | 34 passed |
| Original matching/dashboard/history/events/branding/paper regressions | Passed |
| Chromium desktop + iPhone profiles, local and deployed | Passed |
| WebKit desktop + iPhone profiles, local and deployed | Passed in GitHub Actions |
| Deployed executable/data/style fingerprints | 58 match the PR source |
| Empty/error/retry/invalid IDs, missing FX, storage denied | Passed |
| Virtual buy/revalue/close, persistence/export, optional note | Passed |
| Native back/forward; no duplicate virtual orders | Added regression; local Chromium passed |
| Light/dark 375px-class + desktop, primary action contrast | Passed; screenshots in Actions artifacts |
| Physical iPhone Safari, rotation/large text/Files restore | **Not tested — device unavailable** |
| Physical PC hands-on acceptance | **Not tested — automated desktop only** |

Local WebKit installation was blocked by download policy; CI installed and tested
WebKit 26.5 using Playwright 1.64.1. Device profiles are emulation, not proof of
physical iOS/Safari behavior. No specific iOS version is certified. The earlier
iPhone failure's cause remains unconfirmed without its error/version details.

The first two CI runs passed source/browser checks but failed a Python urllib
fetch of the public deployment: Cloudflare browser-integrity error 1010. The
verification harness now uses the actual browsers, without credentials or a
challenge bypass; the complete remote flow then passed in both engines.
Visual review found/fixed inherited primary-link colour; contrast is now tested.
An existing CSV test now awaits async import; event XSS testing targets the
bookmarked record. Assertions were retained, with no failing tests skipped.

No historical prices were corrected or filled. Brent 5,231 + WTI 5,137 = 10,368
provisional observations, both through 2026-10-20. PR #19/source disagreements
remain separate. Original publication/vintage limits and observation-day proxy
remain. Historical patterns do not establish cause or predict trades.

Paper practice is the original independent 2016 Brent/GBP exercise (PR #2 core),
not event-specific or WTI trading. No live provider, brokerage or real orders.
Use [the acceptance checklist](README.md#iphonepc-acceptance-test) on an actual
phone/PC before accepting Issue #21 as physically verified. Nothing merged.
