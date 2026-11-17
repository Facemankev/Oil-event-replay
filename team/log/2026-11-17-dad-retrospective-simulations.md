# 2026-11-17 · Dad · Retrospective simulations

**Goal:** Implement SIM-1 #43 before LEARN-1 #44, on verified #41 head `13cefcd`. Free data, separate drafts, no merge or review wait.

**What changed:** [Draft PR #45](https://github.com/Facemankev/Oil-event-replay/pull/45), `dad/sim-1-retrospective-paper`. Reuse the primary library and existing friction assumptions; preserve every parent source/module/UI/account. Explicitly opt-in, retrospective hypotheses must not weaken validated execution gates.

**Method:** Freeze event/context decisions before future prices. Use the next strictly later numeric reference observation, exact-date GBP conversion, positive-price checks, fixed 1/5/20 observation exits, cost sensitivities, cash/size/overlap controls and marked daily drawdown. Oil spot and noon FX are reference proxies, not executable exchange products; no opening fill, holiday or original availability is invented. Include all missing/losing cases and baselines. Follow with chronological training/validation/later holdout, purge outcome overlap, record immutable research predictions and refuse validated forecast claims on sparse/current-vintage data.

**Results:** All 51 validated cases fail original news/price availability and executable-product gates; 50 also have fewer than eight selected analogue episodes. Nine fixed rules/horizons and four cost cases cover 151 targeted pairs; default settled 69, positive 34 / negative 35 after declared costs. Context-only GBP links (32), absent price histories (31), missing exact FX paths (18) and one nonpositive reference remain explicit. WTI Humberto gains while Brent loses after costs on the same dates. Longer sequential portfolios preserve unsettled marks and have no invented final cash. No supported entry or account mutation.

**Validation:** Local 126 Python / 112 JavaScript tests pass; focused 16 SIM tests and desktop/iPhone/iPad Chromium light/dark flow pass. Full CI/WebKit reproduction in the separate draft checks. Full per-window traces stay local; compact public evidence retains all cases/results/raw references/sources. The privacy guard flagged a generated per-window fingerprint resembling a phone number; that redundant fingerprint is absent from the public projection and no guard rule changed.

**Unfinished:** Final full CI in #45 Checks, then LEARN-1 #44. Physical Safari acceptance remains. #42 stays separate: no IPO allocations or unsourced prices.

**For Brendan:** Review later; user authorized continued work and no merge.

**Plan changes:** Doing/Now and linked #42/#44 tasks only.
