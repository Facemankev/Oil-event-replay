---
name: wrap-up
description: Send finished Market Ripple work to the other partner. Use when someone says "wrap up", "send it to Dad/Brendan", "I'm done", or "finish for today". Also defines the session log format used automatically during every session.
---

# Wrap up

Logging already happens automatically as work finishes (see `CLAUDE.md`).
Wrap-up tidies that and sends the work for review. Saying "wrap up" is
permission to commit and push to this person's own branch and open or update
a pull request, and, for a small change, to merge it once GitHub's checks
pass (decision 11). Never merge a huge change without the other partner's
approval.

## 1. Make sure the work is on a branch and saved

- `git status` and the current branch. If anything is on `main`, move it to
  a `person/topic` branch (for example `brendan/chart-colours`).
- If website or test files changed, run `node --test tests/research.test.cjs`.
  Report failures in plain words. Don't hide them.

## 2. Tidy the session log

This session's file is `team/log/YYYY-MM-DD-person-topic.md` (person =
`dad` or `brendan`, topic = 2–4 words). It should already exist. If it
doesn't, create it now. Make sure it reads as one clear handover:

```
# YYYY-MM-DD · <Dad|Brendan> · <Topic>

**Goal:** <what this session set out to do>

**What changed:** <plain words, one line each; branch and pull request link>

**Unfinished:** <what's left and where it is; "nothing" is fine>

**For <the other partner>:** <things to look at, decide or watch out for; "nothing" is fine>

**Plan changes:** <what moved in PLAN.md and why; "none" is fine>
```

## 3. Check the shared notes

- `team/TODO.md`: finished items in *Done*, items with a ready pull request
  in *Waiting for review*, and new jobs added with owner and date.
- `team/PLAN.md`: *Now*, milestone statuses and "Last updated" are current.
  Don't touch the vision, principles or workstreams. Those go through
  `plan-change`.

## 4. Send it

- Commit anything outstanding with a plain-English message and push.
- If there's no pull request yet, open one using
  `.github/pull_request_template.md` and request the other partner as
  reviewer: `Facemankev` or `brendans123`. Open it as a draft unless the
  person says the work is finished.
- If there is one, update its description and mark it ready for review if
  the person says it's finished.
- **Small or huge?** Huge is: the vision, principles, sections or a
  decision; removing or replacing something that works on the live site;
  privacy and safety (the guard, `.claude/settings.json`, `.gitignore`,
  GitHub settings); money, sign-ups or data licences. Anything else is
  small.
  - **Small and finished:** once GitHub's checks pass, merge it
    (`gh pr merge <n> --merge --delete-branch`), then switch to an
    up-to-date `main`. If a check fails, fix it first.
  - **Huge:** request the other partner as reviewer and wait for their
    approval.

## 5. Tell them

Three or four lines: the pull request link, whether it was merged or is
waiting on the other partner, and what's next for them.
