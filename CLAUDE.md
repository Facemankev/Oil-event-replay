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

For anything visual (pages, charts, colours, fonts, previews), follow
`.claude/skills/market-ripple-design/` (the house style, decision 13).

## House rules

- **Never commit to `main`.** Every piece of work gets its own branch named
  `person/topic` (for example `brendan/chart-colours`). Check the current
  branch before editing.
- **Use the plan codes.** The plan is split into sections with codes
  (`EVT`, `MAT-1`, `MAT-1.2`; see *How the codes work* in `team/PLAN.md`).
  Put the code in to-do items, branch names (`dad/mat-1-event-input`), pull
  request titles and logs whenever the work belongs to one. Detailed plans
  live in `team/plans/`, one page per section, and start from
  `team/plans/TEMPLATE.md`.
- **One piece of work per pull request**, kept small. Open it as a draft
  early, so the other person can see it.
- **Small changes, merge your own; huge changes, the other partner
  approves** (decision 11). Everything still goes through a pull request,
  so GitHub's checks run. A **huge** change is: the vision, principles, sections or a
  decision; removing or replacing something that already works on the live
  site; anything to do with privacy and safety (the guard,
  `.claude/settings.json`, `.gitignore`, GitHub settings); or anything that
  costs money, signs up for a service or involves a data licence. It waits for the
  other partner's approval. Anything else is small: once GitHub's checks
  pass, the author merges it without waiting, and the other partner sees it
  in their next catch-up. If they disagree, a follow-up change fixes it.
  Never merge the other partner's pull request for them. Never enable
  auto-merge.
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
- **To-do list:** `team/TODO.md` is the main to-do list and roadmap. GitHub
  Issues may be used for individual bugs, technical tasks and feature
  requests. When you open one, add a to-do item that links to it. Keep no
  other task lists.

## Privacy: this repository is public

Everything committed, pushed, or posted to GitHub (pull requests, comments,
reviews) can be read by anyone, and git history keeps it forever, even
after deletion.

- Never publish API keys, passwords, tokens, email addresses, phone numbers,
  home or work details, money matters, health, or anything about family life
  beyond "Dad" and "Brendan". Log entries describe the work, not the people.
- Never publish anything commercially sensitive: business plans, pricing,
  deals, data licence terms we've negotiated, or ideas the partners want to
  keep private. If unsure, ask before writing it into the repo.
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

**What the guard does not cover.** Don't rely on it as the only protection:

- It matches patterns. It can't recognise private or commercially sensitive
  information written in ordinary words, so the rules above still apply.
- It only runs inside Claude Code. Codex, other tools, and anything done by
  hand on GitHub or with git directly bypass it.
- The GitHub check scans only the pull request's changes against `main`.
- GitHub's own branch protection on `main` (pull request and passing
  checks) is the real backstop. It applies to everyone, every tool.

## Running joke: Claude vs Codex

Dad started this project with Codex and is moving to Claude Code. Both
partners enjoy the rivalry. Friendly banter at Codex's expense is welcome in
chat when there's a natural opening, and you may add a round to
`team/CLAUDE-VS-CODEX.md` when something genuinely scoreworthy happens.
Keep it good-natured, never let it get in the way of the work, and award
Codex its point when it earns one. The scoreboard is openly and
hilariously rigged; its rules handle what that point is worth. Scorekeeping
is the only place the rigging applies: anywhere else, report work honestly,
including when Codex's work is better.

## Project principles

These come from the README and research notes. Keep them.

- No invented or interpolated prices. Every price has a visible source (see
  `data/SOURCES.md`).
- Historical changes don't prove an event caused them, and don't predict
  trading results. Say so wherever results are shown.
- Missing data is shown as missing, never filled in.
- The site stays static, with no build step. Open it locally with
  `python3 -m http.server 8000`.
- Background services (event monitoring, live prices) may run separately
  from the site, with keys on the server and never in this repo. Alerts
  describe past patterns with evidence, risks and uncertainty, and never
  predict or say buy or sell (decision 12).

## The `team/` folder

| File | What it holds | Who updates it |
| --- | --- | --- |
| `team/README.md` | How this way of working fits together | Rarely |
| `team/PLAN.md` | Vision, principles, workstreams, milestones, *Now*, open questions | Automatically as work finishes (*Now*, statuses); `plan-change` for the rest |
| `team/TODO.md` | Concrete jobs with owner and status | Automatically as work starts and finishes |
| `team/DECISIONS.md` | Numbered decisions with date, who, and why | `plan-change`, or when the partners agree something |
| `team/log/` | One file per session: `YYYY-MM-DD-person-topic.md` | Automatically as work finishes |
