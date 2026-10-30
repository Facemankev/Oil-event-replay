# 2026-10-30 · Dad · Integrated application (WEB-2 / MAT-3 / PRC-1)

**Goal:** implement Issue #21 as a separate draft PR; no merges or historical price changes.

**What changed:** new branch `dad/web-2-integrated-app`, based on current PR #20
commit 46ef646. That PR is stacked on #16. PR #19 stays separate.

Inventory: root index.html is the original replay/research dashboard; event-research.html
uses world_events/view.mjs and the 24-event export; matching/index.html uses
matching/engine.mjs and analysis.mjs with the cohort catalogue. Paper practice lives
only on PR #2: paper.html and trading/core.mjs/app.mjs, with independent sourced
2016 Brent/FX observations and a £50 virtual account. No backend is required.

Thin slice: a Gold × Desk application home with explicit historical event selection,
shared navigation/deep links into existing evidence and matching views, then an
explicit contextual handoff to the existing historical paper exercise. The exercise
must not be represented as trading the selected event or WTI. No automatic orders.

Working implementation: app/ home, native shared navigation/deep links, optional
reference-only handoff and Gold × Desk paper UI. Reused PR #2 core unchanged;
current-price mode disabled. Explicit loading/empty/invalid-ID/retry/missing-FX
and stale historical coverage states. Memory-only paper practice/export works
when browser storage is denied. Original calculations/price bytes stay unchanged.

Local verification so far: 35 Python tests, all five Node suites, original
matching browser suite and Chromium end-to-end desktop/iPhone profiles passed.
One existing dashboard CSV-import assertion ran before async File.text() completed;
it now waits for the explicit successful-import state and still asserts all rows.
The event-view XSS fixture now targets the selected/bookmarked record on reload,
rather than assuming reload always resets to the first record.
Local WebKit download was denied by network policy; GitHub Actions will test it.

The owner explicitly requested a PUBLIC preview without ChatGPT sign-in. A new
isolated Sites project was registered; existing preview access is unchanged.

**Unfinished:** final regression, CI WebKit, publication and draft PR review.
Reported iPhone failure has no device/error details yet; diagnosis remains open.

**For Brendan:** check the dependency stack, truthful data limits and mobile flow.

**Plan changes:** Now/status only; vision, decisions and principles unchanged.

CI run 41085877222 passed all unit/build/foundation and local Chromium/WebKit
flows, including iPhone profiles. Deployed fingerprint fetch returned HTTP 403;
that remote check remains failing while diagnosed. Native publication succeeded
and access policy confirms public. No original iPhone cause is assumed.
Visual review found inherited link colour hiding the filled action's text;
the new app stylesheet now sets its contrasting paper colour explicitly and a
WCAG 4.5:1 light/dark browser assertion covers that control. Screenshots added.
