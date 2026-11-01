# 2026-11-01 · Dad · Ripple decisions (MAT-4 / PRC-1 / WEB-2)

**Goal:** Issue #23, two-screen mobile-first historical simulation; separate draft
PR on PR #22, no merges, parent/EIA/prices unchanged.

**What changed:** branch dad/mat-4-ripple-decisions based on PR #22 at 6fe59ff.
Reviewed issue and existing matching/cohort/core accounting modules. First slice
uses the existing Harvey record, mechanism hypotheses explicitly distinct from
observed downstream effects, and new sourced GBP FX for the SAME 2017 period as
the unchanged Brent observations. Price chart and accounting use that exact
GBP-converted reference instrument. No live feed is implied.

Plan: two screens in an additive ripple/ route; existing integrated/research
routes stay intact. Reuse pure matcher/statistics and accounting core. Gate
research prompts by sample/source/path stability; weak history yields No Action.
Manual virtual practice remains possible. Persist entry hypothesis, sources,
known-at snapshot, horizon/exit rules, and chronological suggestion decisions/
outcomes. Evaluate at each available replay observation, never future prices.
No automatic sell-day claim, brokerage or source-price corrections.

**Unfinished:** Brendan review, physical iPhone Safari acceptance and explicit
new-preview public-access approval.

**For Brendan:** inspect temporal guards, same-price chart/fills, honest weak
cohorts, ripple labels and visible complexity.

**Plan changes:** Now/status only. No vision, principles or decision changes.

Implemented the additive ripple/ route: two compact screens, two three-order
hypotheses, 34 exact 2017 Brent/GBP quotes and an observed-only dated chart sharing
its exact price with the unchanged paper core. 4 September FX is missing and is
skipped. No canonical price or event record changed. Two genuine EIA context
cards have conservative publication eligibility; 11 September findings appear
only from 12 September. Source-backed facts and downstream hypotheses are labelled.

Entry and bounded operation ledger retain exact quotes, hypothesis, frozen exit
plan, evidence/source snapshots, user responses and later-known paper outcomes.
The actual sample is Limited (2 five-step comparisons, 1 non-overlapping full path),
so no supported buy or reversal is fabricated. Manual £5 virtual practice gives
Hold until the entry's five-step review on 5 September; it does not auto-sell.

Local checks: 38 Python tests, six Node suites and every original Chromium
browser regression passed. Initial chart min-width overflow was fixed locally;
the new desktop/iPhone Chromium replay test passed. WebKit will run in CI.

A separate Site was created for this preview. Automatic approval review rejected
public access, stating Issue #23 does not explicitly authorise changing the new
site's audience. Owner-private publication is the safer fallback; no access
workaround or change to earlier public preview sites is made. Unauthenticated
new-deployment browser QA remains blocked pending that access decision.

[Draft PR #24](https://github.com/Facemankev/Oil-event-replay/pull/24) is based
on #22; Brendan is requested as reviewer. The [private preview](https://market-ripple-ripples-review.g86hz2pjsh.chatgpt.site/ripple/)
published successfully as Sites version 1, preserving owner-only access.
67 packaged executable/data/style fingerprints match the tested source.
No authenticated deployed-browser visit is claimed; public access was blocked
by automatic approval review, not silently worked around.

[CI run 41350485770](https://github.com/Facemankev/Oil-event-replay/actions/runs/41350485770)
passed 38 Python and 46 Node tests, all existing browser regressions, the original
application in Chromium/WebKit, and the new two-screen flow in Chromium/WebKit
desktop/iPhone profiles. Screenshots/reports are Actions artifacts. No physical
phone or PC was used. Source preservation checks confirm main, #22/#20/#16,
#19 and #2 heads and original prices/engines/tokens are unchanged.

The working example is a manual £5 virtual entry on 28 August at £40.126632
GBP reference, Hold through four steps, and Review Sell on 5 September under
the user's frozen five-step horizon. It does not execute automatically or infer
a supported historical reversal. Optional explicit close gives about £50.14
virtual cash. All production comparison support remains Limited/No Action.
