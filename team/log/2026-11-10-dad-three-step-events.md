# 2026-11-10 · Dad · Three-step events (WEB-2 / MAT-4 / PRC-1)

**Goal:** Implement Issue #25 on draft PR #24, a separate draft and public preview.
No merges, price corrections or changes to production/PR #19.

**What changed:** Claimed `dad/web-2-three-step-events` from #24 at 9a94749.
Reviewed the actual issue, existing matching, evidence gates, chart and ledger.
Reuse the same matcher and account model; simplify the three-answer card and
add event list/detail routes with sourced Brent/WTI observations. More detail
stays optional. Preserve the Gold × Desk tokens and existing applications.

**Unfinished:** Implementation, automated mobile/desktop tests and publication.
Physical iPhone Safari acceptance will require a person with the device.

**For Brendan:** Review the three-answer flow, evidence labels and event drilldown.

**Plan changes:** Doing and Now only; no principles or decision changes.

Implemented three-answer card and hash-routed historical list/detail. Reuses the
same query/matcher; two eligible real storms, own sourced Brent/WTI charts,
publication/occurrence distinction, no-match/unavailable states and safe text.
Extra statistics/ripple hypotheses/controls are optional. Account model, quote
snapshot and original dashboard/research/design files are byte-unchanged.

Local 38 Python tests, seven Node files and Chromium desktop/iPhone/iPad checks
passed. The new five unit cases cover matching reuse, temporal/source/null guards
and route parsing. WebKit download is blocked by the environment's domain policy;
GitHub Actions will run both browser engines and every previous regression.

A new Site was registered for this specific preview, with identity persisted in
its separate checkout. Public URL access succeeded under the user's explicit
request. Earlier Site audiences/previews were not changed. Publication pending.
