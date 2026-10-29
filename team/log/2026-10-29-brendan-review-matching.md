# 2026-10-29 · Brendan · Reviewed Dad's matching work (MAT-2 / MAT-3)

**Goal:** go through the open pull requests, review Dad's event matching
(#16) and evidence ranking (#20), and get them merged.

**What changed:**

- Looked at all five open pull requests. #16, #19 and #20 pass every check
  and follow the principles. #2 (paper trading) now clashes with `main` and
  its live-prices part needs a paid data licence (a huge change). #9 clashes
  with Dad's newer notes.
- Tried #16 and #20 in a local preview. Approved #16.
- Fixed two small things on #20, on Dad's branch with his agreement (as
  Brendan reported): the table said "1 days", and the ranking note now
  says a larger past move can lift a row a little, so a high rank never
  means a bigger expected move.
- Tried to merge #16 with Dad's agreement. The guard blocked it: it only
  allows a merge when GitHub shows "approved", and with no required
  approvals on `main` GitHub never shows that, so every merge is blocked.
  The guard wasn't changed.

**Problem found:** on Windows, 19 of the Python tests error because Windows
won't delete a test's temporary database file while it's still open. The
same errors happen without any change. GitHub's checks (Linux) are
unaffected.

**Unfinished:** #16 and #20 not merged. #19 and #2 not yet reviewed in
GitHub. #9 needs its clash fixed. The trade-suggestions plan change
(`brendan/plan-trade-suggestions`) still needs renumbering (decisions 14
and 15) and a pull request.

**For Dad:**

- #16 is approved. Please merge it, then #20 (which includes Brendan's two
  small fixes).
- The guard blocks all merges while `main` requires no approvals. One of us
  needs to decide how the guard should treat that (it's on the to-do list).

**Plan changes:** none.
