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

**Unfinished:** implement and test, public preview, draft PR; physical iPhone
Safari unavailable here and must be explicitly recorded as outstanding.

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
