---
name: catch-up
description: Start-of-session briefing for Market Ripple. Runs automatically at the start of every session, and whenever someone says "catch me up", "what's new" or "what did Dad/Brendan do". Reports what the other partner changed since this person's last session and where the whole project stands.
---

# Catch me up

Give the person a short, plain-English briefing as the start of your first
reply in every session, without being asked. Change nothing except updating
their local copy if they agree.

## 1. Work out who and where

- Who: `gh api user --jq .login`. `Facemankev` = Dad, `brendans123` =
  Brendan. If it's neither, ask.
- `git fetch --all --prune`, then `git status`. Note the current branch and
  any unsaved changes.

## 2. Find what's new

- **Their last session:** the newest file in `team/log/` with their name in
  it, on `origin/main` or on any of their open branches. Its date is
  "last time". If there's none, use the last 14 days.
- **The other partner's log entries since then**, on `origin/main`
  (`git show origin/main:team/log/<file>`) and on every one of their
  branches, because work is pushed as it goes, often before a pull request
  exists. For each `origin/dad/*` or `origin/brendan/*` branch:
  `git diff --name-only origin/main...origin/<branch> -- team/` finds new
  or changed notes, and `git show origin/<branch>:<file>` reads them.
  `gh pr list --state open --json number,title,headRefName,author,isDraft,reviewDecision`
  shows which branches already have pull requests.
- **Changes to `main` with no log entry:** `git log origin/main --since=<last time> --oneline`.
  Mention any that no log explains.
- **Pull requests:** ones waiting for this person's review; their own that
  are approved (offer to merge them) or have new comments.
- **`team/TODO.md` and `team/PLAN.md`** from `origin/main`, plus any newer
  versions on open branches.

## 3. Report in this shape

Keep it under about 250 words. Use names, not usernames. Link pull requests.

```
Since you were last here (<date>)
- <What the other partner did, in plain words, one line each>
- <Anything they flagged for you>

Waiting for you
- <Reviews to do, decisions to confirm, your open to-do items>

Where the project stands
- <One line per workstream that moved or is blocked, from PLAN.md>
- <Open questions that need you both>

Suggested next step: <one concrete thing>
```

If nothing changed since last time, say so in one line and go straight to
"Waiting for you".

## 4. Offer to get up to date

If their local `main` is behind `origin/main`, or they're on a branch that's
already merged, offer to switch to an up-to-date `main` (or a new branch for
today's work). Never discard unsaved changes. If there are any, say what
they are and ask.
