# How we work together

Dad and Brendan are equal partners on Market Ripple. We mostly work
separately, at different times, each with our own AI assistant. This folder
is our shared memory. The AI keeps it up to date by itself, so neither of us
has to remember to.

## What happens automatically

- **At the start of every session,** Claude briefs you: what the other
  person did since you were last here, what's waiting for you, and where the
  whole project stands.
- **As work gets done,** Claude writes it in the session log, updates the
  to-do list and plan, and saves it to your own branch on GitHub. If you
  close the window suddenly, nothing is lost.

## Things you can say

| Say | What happens |
| --- | --- |
| **wrap up** / **send it to Dad** / **send it to Brendan** | Claude opens or updates the pull request so the other person can review it. |
| **I want to change the plan** | Claude drafts the change with the reason and sends it to the other person to agree to. |
| **review Dad's / Brendan's pull request** | Claude explains the change in plain words, shows it running, and helps you approve it or ask for changes. |
| **catch me up** | The start-of-session briefing again, any time. |

## What's in here

- [PLAN.md](PLAN.md): where the project is going (vision, sections and their codes, milestones) and what's happening now.
- [plans/](plans/): one page per section (`EVT.md`, `MAT.md`, …) listing its plans, plus a template for writing a plan in detail.
- [TODO.md](TODO.md): the shared to-do list. Who's doing what.
- [DECISIONS.md](DECISIONS.md): what we've agreed, and why.
- [log/](log/): one short note per working session.

## The rules in one breath

Work on a branch, never on `main`. Every change goes through a pull request
the other person approves. Claim a to-do item before starting it. The vision
and big direction change only when we both agree. `TODO.md` is the main
to-do list; GitHub Issues are fine for single bugs, technical tasks and
feature requests, linked from `TODO.md`.

## Privacy

This repo is public for now, so nothing personal, no passwords or keys, and
nothing commercially sensitive goes in it. If Market Ripple becomes a
commercial product, we reconsider what stays public.

A guard checks everything Claude saves to GitHub or posts there, and blocks
keys, passwords, emails, phone numbers and anything in your personal block
list (`.claude/private-words.txt`, which stays on your computer). GitHub runs
the same check on every pull request. The guard also stops Claude changing
`main` directly, merging without approval, or changing repo settings.

**What it can't do:** it spots patterns, not meaning, so something private
written in ordinary words gets through. It only works inside Claude Code: it
doesn't cover Codex or anything done by hand on GitHub. GitHub's own
protection on `main` (pull request, one approval, passing checks) is the
real backstop, because it applies to everyone.
