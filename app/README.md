# Integrated application (Issue #21)

The working entry point is **app/index.html**. It connects the existing pages
using native links, stable public event IDs and validated query parameters.
No SPA router, pop-up login, service worker, backend or API key is required.
Free-text event descriptions and account records are never put in navigation URLs.

Dependency stack: this separate draft PR is based on **PR #20 at 46ef646**,
which is based on **PR #16**. Rebase/retarget only after reviewing those parents.
The paper accounting core and source FX slice are reused from **PR #2 at c2bcb92**;
this does not modify or merge that branch. PR #19 remains completely separate.

## What actually works

1. Original dashboard → Application home → select a genuine library event.
2. Read its occurrence, located public disclosure, uncertainty and primary source.
3. Open the existing event research page at that exact record.
4. Open existing matching at the same record, market and observation-day window.
   The existing matcher excludes the selected event and future evidence/outcomes.
5. Inspect existing cohort counts, medians, signed counts, ranges and transparent
   evidence/risk ranking. Both the original shared-calendar event study and the
   independent benchmark calendars in matching retain their own disclosed methods.
6. Optionally open **separate 2016 Brent/GBP practice**, copy a research reference
   to a note, explicitly create a £50 virtual account and choose a £5 virtual buy.
   Advance to the next sourced date, value/close the position, export/reload/restore.

The handoff is a journal reference, **not a simulation of the selected event**.
WTI practice is unavailable. There is no conversion from an oil spot-price median
into a portfolio return. No order/account is created by navigation or copying a
reference. Fees/spreads/slippage are explicitly assumed zero in the existing
educational exercise. Current mode is disabled in the UI; no provider or quote
worker is included/deployed by this PR. Real orders and brokerage are absent.

## Setup and checks

```sh
python3 -m http.server 8000
# http://localhost:8000/app/
node --test tests/*.cjs tests/*.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m app.data_status --check
node matching/demo.mjs --check
python3 tests/application_browser_test.py
python3 tests/application_browser_test.py --browser webkit
# Public deployed site root, once published:
python3 tests/application_browser_test.py --browser webkit --base-url https://YOUR-PREVIEW
```

Install Python Playwright 1.64.1 and its Chromium/WebKit engines/dependencies for
browser checks. CI uses Ubuntu 24.04 and runs both engines. Local WebKit download
was blocked by this environment's network policy; CI must provide that result.
`work/application/` contains browser JSON reports (ignored, never account data).
`python3 -m app.data_status` rebuilds the small coverage report from the unchanged
price export; it makes no database/price changes.

## iPhone/PC acceptance test

Use the public preview URL in the PR directly in Safari, not inside a social app.
It should open without ChatGPT sign-in. No in-app authentication is implemented
or needed. The previous preview was owner-private; the reported iPhone failure
has no confirmed iOS/error details, so its cause is **unconfirmed**. Publishing a
public preview removes that access gate, without claiming the prior bug reproduced.

1. Open `/app/`, select Harvey; note occurrence versus disclosure/cutoff dates.
2. Choose **Read this event’s evidence**, confirm Harvey and its NHC source link.
3. Choose **Find comparable historical events**. Confirm Harvey remains selected,
   self/later events are excluded, and the five-day Brent cohort has two windows.
4. Choose WTI / 3 days from research priority, inspect the sample and risks.
5. Choose **Open separate 2016 Brent practice**. Confirm the visible mismatch
   disclosure and that no account/trade already exists in a new browser session.
6. Copy the optional research note, start £50 practice, buy £5, advance one day.
   The original demo values that position at £5.07. Close, export and reload.
7. Use native back/forward and navigation links; rotate portrait/landscape and
   test light/dark, enlarged text, source links and backup save/restore in Files.

**Physical iPhone Safari / physical PC interaction is outstanding** unless the
validation report explicitly records a human run. WebKit with iPhone settings is
automated engine testing, not a real device or proof of an iOS version working.
There is no physical device attached to this environment. Browser engine/version,
URL, visible error and whether it happened before/after application load are useful
diagnostics; never send tokens, cookies, account backups or personal information.

## Truthful failure and data states

Loading is explicit; data failure clears results and exposes retry on the home.
An empty library disables selection. Invalid public IDs show an explanatory
fallback, rather than inventing events. Optional coverage metadata failure does
not prevent independent event research. Missing FX/prices block paper-account
startup. Safari storage denial/quota failure shows memory-only status while
retaining export; reloading can lose unsaved in-memory practice. Persistent
storage, if available, stays browser/origin-local; backups are user-managed.

Both oil histories still end on **2026-10-20** (10,368 records total), not today.
No live detection, current feed, automatic monitoring or alerts are implied.
Prices and current evidence remain provisional/Limited pending **PR #19**.
No EIA key, reconciliation evidence or source-correction decisions are needed here.
The original price-publication/vintage limits and observation-day proxy remain.
Shared regimes, anticipation and other news still prevent causal/predictive claims.

Original replay logic, database/event records, price exports, design tokens and
branding preview are preserved. Existing pages gain navigation; matching and
event research gain validated deep links, not new calculation implementations.
Apple/Brent lab CSV imports remain browser-local on the original dashboard.
