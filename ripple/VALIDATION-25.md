# Issue #25 validation — 10 November 2026

Base: draft PR #24, `9a94749`. Branch: `dad/web-2-three-step-events`.
Separate static [public preview](https://market-ripple-three-step-review.g86hz2pjsh.chatgpt.site/ripple/).
No merge, main update, PR #19 reconciliation or original price edit.

## Implemented and checked

- Three concise answers; Limited evidence gives **Brent oil: uncertain / No action**.
- One-tap historical list, one-tap individual detail; own sourced Brent/WTI dated
  USD chart, event/publication distinction, back/forward, match reasons and gaps.
- Existing matcher and evidence query reused; self/future/weak matches excluded.
  Missing/unbacked/conflicting values never become a zero or invented observation.
- Full cohort and ripple mechanisms are optional disclosures. No odds/prediction.
- Same GBP chart/accounting, entry marker, explicit buy/sell confirmations, frozen
  exit plan, saved evidence, outcomes and backup validation remain working.

## Reproduce

```
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
python3 -m ripple.build --check
python3 -m app.data_status --check
node matching/demo.mjs --check
python3 tests/ripple_browser_test.py
python3 tests/ripple_history_browser_test.py
# Repeat both with --browser webkit; add --base-url <preview origin> for deployment.
```

Local: 38 Python and 51 JavaScript tests passed across seven Node files (five new
history unit cases in addition to the existing suite). Chromium desktop/iPhone paper
flow and desktop/iPhone/iPad list/detail tests passed, with light/dark screenshots.
Portrait 375px, landscape, 44px targets, no page overflow; memory-only storage,
failed-load retry, backup tamper, no-match, unavailable prices and unsafe text checked.

WebKit cannot be downloaded in this environment: the network policy returned
403 Domain forbidden for the official Playwright CDN. The new PR workflow runs
Chromium and WebKit, all earlier browser regressions and the exact public package.
[Draft PR #26 checks](https://github.com/Facemankev/Oil-event-replay/pull/26/checks)
contain the full CI and deployed results. No local WebKit pass is claimed.
The [first CI run](https://github.com/Facemankev/Oil-event-replay/actions/runs/42784024225)
passed 38 Python / 51 JavaScript tests, repeatable database imports, preservation
checks and **all earlier browser regressions plus the paper flow in both engines**.
It exposed a test race on return from event detail: a synchronous measurement
ran before the hash view became visible. Explicit visible-view waits fix the
harness without weakening assertions. The full workflow is repeated on the fix.

Screenshots: workflow artifact `three-step-browser-reports`, or local
`work/three-step/<engine>/<local|deployed>/` and `work/ripple/`.

## Source and physical-device limits

Original data, model/core, engine/analysis, original dashboard, earlier app/research,
branding tokens and previews match #24. Only the shared query extraction changes
`paths.mjs`; existing ledger reconstruction tests pass. The two visible matches are
Gustav and Ike (2008), not independent trials. One full non-overlapping path and
two five-day comparisons do not support a directional prompt.

Prices remain labelled provisional pending the separate PR #19 correction review.
No credentials used or published, no primary-source verification invented, no
missing calendar date labelled a holiday without evidence. Publication vintages
and daily observation clocks are incomplete, so this is not a fully point-in-time
backtest. Only Brent has GBP virtual fills; WTI is historical research only.

No physical iPhone, iPad or desktop device testing claimed. Remaining human checks:
actual Safari touch/rotation, large text/VoiceOver, native confirmations and Files
backup export/restore. This is a historical replay, not live monitoring or trading.


## Public package and review

Native Sites publication succeeded on the separate public project. The static
package contains 88 public files with 73 executable/data/style fingerprints;
CI compares those fingerprints with its checkout before testing the public flow.
No configured price provider, credentials, private workspace files or account
backups are shipped. Browser-local accounts are separate from the older app.
The Site's own source Git/archive provenance is retained by the hosting service;
the separate draft targets PR #24 and does not change its branch or preview.

At handoff, Brendan is requested on [draft PR #26](https://github.com/Facemankev/Oil-event-replay/pull/26).
Original source hashes and remote main/#24/#22/#19 heads were checked unchanged.
For final CI status and downloadable screenshots use the PR Checks link above.
