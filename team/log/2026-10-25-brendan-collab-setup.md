# 2026-10-25 · Brendan · Setting up how we work together

**Goal:** give us (and our AIs) a shared way to communicate, review each
other's work and catch up between sessions.

**What changed:** on branch `brendan/collab-setup`:

- Added `CLAUDE.md` (instructions every Claude session reads) and
  `AGENTS.md` (the same, for Codex).
- Added the `team/` folder: `PLAN.md`, `TODO.md`, `DECISIONS.md`, this log.
- Added four commands in `.claude/skills/`: `catch-up`, `wrap-up`,
  `plan-change`, `review-pr`.
- Added a pull request template in `.github/`.
- Made catch-up and logging automatic. Claude briefs you at the start of
  every session and logs, updates the to-do list and saves to your branch as
  work finishes, without being asked. `.claude/settings.json` fetches the
  latest from GitHub when a session opens. "Wrap up" now just means "send it
  for review".
- Added privacy guardrails, since the repo stays public.
  `.claude/hooks/guard.sh` checks every commit, push and GitHub post the AI
  makes. It blocks keys, passwords, emails, phone numbers and personal words,
  as well as committing or pushing to `main`, merging without approval and
  changing repo settings. A new GitHub check (`privacy-check.yml`) repeats
  the scan on every pull request. `.gitignore` now keeps secrets and each
  person's private word list off GitHub. Tested with 22 safe and unsafe
  examples, all behaving as expected.
- `TODO.md` is now the only to-do list (no new GitHub issues).
- After a project audit, closed three gaps in the guard. It now scans only
  the command (not folder names around it), checks `commit -a` and newly
  added files, and refuses rather than waves through when it can't find
  `origin/main` to compare against. Re-tested: 31 cases, all as expected.
- The audit also found bugs in the original oil replay (its window dropdown
  is ignored for built-in data; chart spacing; CSV import) and that its
  prices have no recorded source. Not changed: for Dad and Brendan to
  discuss.
- No website code was changed.

**Unfinished:** the vision and the workstream list in `PLAN.md` need Dad.

**For Dad:**

- Please review this pull request. It's the first run of the new review
  process.
- Decisions 3–6 in `DECISIONS.md` are proposals waiting for your yes.
- We kept the repo public, which keeps the live website. Two GitHub settings
  only you can switch on, as owner: protecting `main`, and secret scanning
  with push protection. Both are on the to-do list.
- Make your own `.claude/private-words.txt` on your computer once you've
  downloaded the repo.
- The vision in `PLAN.md` is yours to write.

**Plan changes:** first draft of `PLAN.md` written from what's in the repo.
