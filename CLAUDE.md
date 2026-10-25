# Market Ripple: instructions for AI assistants

Market Ripple (repo `Oil-event-replay`) is a static website for exploring how
world events have moved markets. Read [README.md](README.md) for what it does.

## Who you are working with

Two equal partners: Dad (GitHub `Facemankev`) and his son Brendan (GitHub
`brendans123`). The project is Dad's idea and he built the first version.
Neither of them is a developer. Explain things in plain words, avoid jargon,
and handle all git and GitHub steps yourself. They work separately, at
different times, each in their own AI session. You have no memory of earlier
sessions, so the `team/` folder is the shared memory. Keep it accurate.

## Every session (automatic, nobody has to ask)

The partners should never have to ask for a catch-up or a log. Do both
without being asked.

1. **Catch up first.** Your first reply in a session starts with the
   `catch-up` briefing, then deals with whatever the person asked. If they
   asked something urgent, keep the briefing to three lines and offer the
   rest.
2. **Log as you go.** As soon as a piece of work is finished (a change made,
   a decision reached, a problem found), and before moving on to the next
   one:
   - Create or update this session's log file in `team/log/` (format in the
     `wrap-up` skill).
   - Update `team/TODO.md` (claim, tick off, add) and the *Now* section of
     `team/PLAN.md`.
   - Commit the work and the notes together to the person's branch, and push
     the branch. This only ever goes to their own `person/topic` branch,
     never to `main`.

   Don't ask permission for these steps or announce each one. A one-line
   mention ("logged and saved") is enough. If the session ends suddenly,
   nothing is lost.
3. **"Wrap up"** is only for sending work to the other partner. It tidies the
   log and opens or updates the pull request. If the person seems to be
   finishing with finished work that hasn't been sent, offer it.

The commands live in `.claude/skills/`: `catch-up`, `wrap-up`, `plan-change`
and `review-pr`. If your tool can't run skills, read the skill file and follow
its steps by hand.

## House rules

- **Never commit to `main`.** Every piece of work gets its own branch named
  `person/topic` (for example `brendan/chart-colours`). Check the current
  branch before editing.
- **One piece of work per pull request**, kept small. Open it as a draft
  early, so the other person can see it.
- **The other partner approves** before anything is merged. Never merge a
  pull request the other partner hasn't approved. Never enable auto-merge.
- **Claim before you start:** mark the to-do item *Doing* with the person's
  name, so the other partner doesn't pick it up too.
- **Bigger than a small change?** Write a short plan in plain words and get
  the person's agreement before building.
- **Vision, principles and workstreams** in `team/PLAN.md` change only
  through `plan-change`, which needs the other partner's approval. The *Now*
  section, milestone statuses and `team/TODO.md` can be updated freely.
- **`team/DECISIONS.md` settles arguments.** Don't reopen a recorded decision
  unless the person asks. If two approaches conflict, ask the partners. Don't
  pick on their behalf.
- **Run the tests** before saying work is finished:
  `node --test tests/research.test.cjs`. The browser test
  (`python3 tests/browser_test.py`) needs Playwright. Run it when the page
  layout changes and it's available.
- **One to-do list:** `team/TODO.md`. Don't open GitHub issues or keep task
  lists anywhere else.

## Privacy: this repository is public

Everything committed, pushed, or posted to GitHub (pull requests, comments,
reviews) can be read by anyone, and git history keeps it forever, even
after deletion.

- Never publish API keys, passwords, tokens, email addresses, phone numbers,
  home or work details, money matters, health, or anything about family life
  beyond "Dad" and "Brendan". Log entries describe the work, not the people.
- If the person mentions something private while working, use it to help
  them, but keep it out of files, commit messages and GitHub posts.
- `.claude/hooks/guard.sh` checks every commit, push and GitHub post before
  it happens. If it blocks you, remove the private item. Don't reword it to
  slip past the check, and never edit the guard, `.claude/settings.json`,
  `.claude/allowed-words.txt` or `.gitignore` to get round it. Only a partner
  decides to allow something. Tell the person what was blocked and why.
- Each partner keeps a personal block list in `.claude/private-words.txt`.
  It stays on their computer and is never committed.
- The guard also blocks committing or pushing to `main`, merging without
  approval, and changing repository settings. Those are done by people.

## Project principles

These come from the README and research notes. Keep them.

- No invented or interpolated prices. Every price has a visible source (see
  `data/SOURCES.md`).
- Historical changes don't prove an event caused them, and don't predict
  trading results. Say so wherever results are shown.
- Missing data is shown as missing, never filled in.
- The site stays static, with no build step. Open it locally with
  `python3 -m http.server 8000`.

## The `team/` folder

| File | What it holds | Who updates it |
| --- | --- | --- |
| `team/README.md` | How this way of working fits together | Rarely |
| `team/PLAN.md` | Vision, principles, workstreams, milestones, *Now*, open questions | Automatically as work finishes (*Now*, statuses); `plan-change` for the rest |
| `team/TODO.md` | Concrete jobs with owner and status | Automatically as work starts and finishes |
| `team/DECISIONS.md` | Numbered decisions with date, who, and why | `plan-change`, or when the partners agree something |
| `team/log/` | One file per session: `YYYY-MM-DD-person-topic.md` | Automatically as work finishes |
