# 2026-10-26 · Brendan · Relaxed review rule

**Goal:** stop small changes waiting for the other partner's approval, while
keeping the automatic checks and an approval step for huge changes.

**What changed:** on branch `brendan/plan-relaxed-reviews` (built on
`brendan/plan-sections`, PR #5, because both change `TODO.md`):

- Decision 11 proposed, replacing decision 3. Every change still goes
  through a pull request. Small changes: the author merges once GitHub's
  checks pass. Huge changes wait for approval. Huge means the plan's
  direction or a decision, removing something that works on the live site,
  privacy and safety settings, or money, sign-ups and data licences.
- `CLAUDE.md`, `AGENTS.md`, `team/README.md` and the `wrap-up` skill follow
  the new rule. Wrap-up now merges small finished changes once checks pass.
- The to-do for protecting `main` now says to leave "require approvals" off.
- No website code changed.

**Unfinished:** the guard (`.claude/hooks/guard.sh`) still blocks Claude
from merging anything unapproved. It's privacy and safety, so Claude didn't
change it. On the to-do list for a partner, once decision 11 is agreed.

**For Dad:**

- Please confirm or change decision 11, especially the list of what counts
  as huge.
- When you protect `main`, require passing checks but not approvals.

**Plan changes:** decision 11 proposed (replaces decision 3).
