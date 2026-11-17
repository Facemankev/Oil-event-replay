# 2026-11-17 · Dad · Cross-market history

**Goal:** Implement Issue #38 on draft #36; broaden sourced historical comparisons across six market groups and coordinate evidence with LIVE-1 #37.

**What changed:** Claimed `dad/hist-1-cross-market-analogues` at verified #36 head `2285073`. Issue #37 has no implementation PR yet. Keep a separate additive historical module and a stable read-only evidence contract; do not implement the live provider pilot here.

**Unfinished:** Full Chromium/WebKit CI and later physical-device acceptance. Adjusted equity/contract-specific gold/index series and original news/price vintages remain missing; #37 retains the provider/source-access work.

**For Brendan:** Review later; no merge, original source replacement, account or preview changes.

**Plan changes:** Doing and Now only; no principles or workstream changes.

Implemented a dedicated append-only SQLite library and reproducible report: 48
sourced events (36 inherited, 12 added), 81 source cards, 16,320 primary rows /
15,618 numeric values, plus 11 separately reported reactions and three inherited
corporate reference pairs. Gold is macro-linked reported context, not a verified
contract series. Currency coverage is GBP/USD; 32 links are conversion references.
No adjusted equity/index series or original price/news availability is claimed.

Matching uses available category/mechanism/stage/location/scale/regime features,
then chronological episode/overlap controls before reading outcomes. Future-case,
episode, price and outcome mutations preserve earlier decisions. All 48 decisions
are No Action; no supported paper entries or causal downstream claims.

Local 93 Python / 112 JavaScript tests pass; all four parent reports and the pilot
demo reproduce unchanged. Node's child-process integration needed the authorized
execution mode; the initial sandbox EPERM was environmental, not a skipped test.
All ten Chromium scripts and full GitHub/WebKit checks are being run. Three-step
UI, source snapshots, accounts and public previews remain unchanged. No merge.
