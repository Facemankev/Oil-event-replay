# 2026-11-14 · Dad · Nvidia news replay

**Goal:** Implement Issue #32 on draft #33, without waiting for Brendan. Detect company news, measure only source-supported equity reactions and cross-check actual historical corporate events before any paper suggestion.

**What changed:** Claimed `dad/evt-2-nvidia-news` at verified parent `4db1d9b`. Read the issue and primary board statement; allegations remain attributed and disputed, not findings. Keep the existing three-step interface and oil study unchanged.

**Unfinished:** Capture news timestamps and actual equity data, implement bounded replay/dedup/history/ripple checks, run full tests and open separate draft. No inferred intraday prices, causal claims, shorts or brokerage.

**For Brendan:** Later review, not a progress dependency. No merge or preview overwrite.

**Plan changes:** Doing/Now only.

Implemented bounded RSS/Atom collection and actual receipt/version preservation,
deterministic company classification, issuer-copy deduplication, market schedule
and stale-news checks, original-vs-reference price boundaries, four genuine
corporate-history cross-checks and secondary/tertiary market comparisons.
Six source cards describe four developments; 66 daily provider rows cover six
references. Earlier reporting and the company counterpoint remain attributed.
Initial Nvidia close comparison: -4.27%; AMD/AVGO and Nasdaq positive. Opposite
peer moves challenge a blanket sector-decline thesis without proving causality.

All eight replay cutoffs abstain; no supported GBP Nvidia execution or qualified
corporate cohort. Opening sources differ by one cent; exact opening price refused.
No intraday quote or exchange-print verification is fabricated. Day-only release
eligibility is not an initial-reaction clock, and missing sessions are not skipped.
Direct official RSS request received a 403 tunnel denial; offline collector-to-
detector integration passes. Original receipt/vintage evidence is not inferred.
Eight new Python / sixteen JavaScript tests pass; full suite 60 Python / 99 JS.
Local Chromium regressions in progress; full Actions/WebKit follows in the draft.
