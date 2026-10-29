# 2026-10-29 · Dad · Approved integration (DAT-3 / EVT-1 / BRD-2)

**Goal:** integrate approved PRs #12, #14 and #15 through normal GitHub merges.

**What changed:** Brendan's GitHub approvals and successful Actions confirmed
on all three original heads. PR #12 merged as 8173be7. PR #14 documentation
conflicts resolved by retaining both README sections and source limitations.
Added a real SQLite-to-JSON-to-event regression and reproducible README commands;
CI now runs the combined Python tests. Separate database files are intentional.

Combined trial checkout: 23 Python tests and the research suite passed;
dashboard, history, events and original branding browser suites passed.
Actual imports: 5,231 Brent, 5,137 WTI, 24 events, 48 matching benchmark results;
safe repeats and both SQLite integrity checks passed. Paper-trading unit and
browser suites also passed in a separate local compatibility checkout; PR #2
and its remote branch were not changed. Original dashboard script and Brendan's
design source files are preserved. No broker or live trading was connected.

PR #14 merged as e1e6baa after all four updated Actions passed. PR #15 now
includes both database foundations and preserves their README/PLAN/TODO entries.
GitHub dismisses stale reviews on push, so its old approvals were dismissed on
integration updates. The active ruleset has zero required new approving reviews,
no bypass actors and current_user_can_bypass=never. No settings were changed,
no forced push or administrative override was used; the owner explicitly
requested sequential integration. PR #15 is prepared for normal merge after
fresh checks. The original dashboard has only PR #12's history link added;
its existing scripts, prices and replay behavior are unchanged.

**Unfinished:** primary EIA reconciliation and physical iPad Safari review.
Primary EIA verification needs a free key and permitted API access. Seeds remain
secondary EIA-derived, not authenticated EIA reconciliation. Original price
publication/vintages are unknown; 18 event publications are day-only and four
first-public dates unestablished. No comparison is backtest-eligible.

**For Brendan:** Gold × Desk preview remains public at
https://market-ripple-gold-desk-review.royaltulip9.chatgpt.site
The hosting service confirms publication; local Chromium checks passed,
not physical iPad Safari or a remote HTTP inspection.

**Plan changes:** Now/status only. Next milestone: primary EIA reconciliation,
then stronger event disclosure evidence before historical analogue matching.
