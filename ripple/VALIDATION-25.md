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

Local: 38 Python tests passed. All seven Node files passed (five new history
unit cases in addition to the existing suite). Chromium desktop/iPhone paper
flow and desktop/iPhone/iPad list/detail tests passed, with light/dark screenshots.
Portrait 375px, landscape, 44px targets, no page overflow; memory-only storage,
failed-load retry, backup tamper, no-match, unavailable prices and unsafe text checked.

WebKit cannot be downloaded in this environment: the network policy returned
403 Domain forbidden for the official Playwright CDN. The new PR workflow runs
Chromium and WebKit, all earlier browser regressions and the exact public package.
CI/deployed results will be recorded after the run; no local WebKit pass claimed.

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
