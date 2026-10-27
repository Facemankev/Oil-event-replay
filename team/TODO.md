# To-do list

This is our **main** to-do list and roadmap. GitHub Issues can hold the
detail for individual bugs, technical tasks and feature requests; each one
gets an item here that links to it (issue #3, paper trading, is covered by
the PR #2 item below).

Each item: plan code (see *How the codes work* in `PLAN.md`), what, **who**,
and the date added. Move items between sections as they progress. Mark an
item *Doing* before starting it, so we never both pick up the same job. Done
items stay for two weeks, then the oldest can be deleted (the log keeps the
history).

## Doing

_Nothing right now._

## To do

- [ ] OPS: Write the vision in `PLAN.md` — **Dad** — 2026-10-25
- [ ] OPS-4: Check the proposed sections, codes and provisional plans in `PLAN.md` and `plans/`, and rewrite the goals as you see fit — **Dad** — 2026-10-26
- [ ] OPS: Install Claude Code, sign in to GitHub, and download the repo. Push any unsaved Codex work to a branch first — **Dad** — 2026-10-25
- [ ] OPS-2: Protect `main` on GitHub: changes only by pull request with passing checks. Leave "require approvals" off if decision 11 is agreed — **Dad** — 2026-10-25
- [ ] OPS: Once decision 11 is agreed, update the guard (`.claude/hooks/guard.sh`) so it lets a small change be merged without approval once checks pass. A partner decides how, as the guard is privacy and safety — **Brendan** or **Dad** — 2026-10-26
- [ ] OPS-2: Turn on GitHub's secret scanning and push protection (Settings → Code security) — **Dad** — 2026-10-25
- [ ] OPS: Fill in your own `.claude/private-words.txt` (never shared) — **Brendan** and **Dad**, each on your own computer — 2026-10-25
- [ ] OPS: Turn on GitHub email notifications for reviews and comments — **Brendan** and **Dad** — 2026-10-25
- [ ] PRC-1: Review PR #2 (paper trading, issue #3) — **Brendan** — 2026-10-25
- [ ] OPS: Move the project folder out of OneDrive into a plain folder — **Brendan** — 2026-10-25
- [ ] WEB: Python 3.13 is installed, but on Windows only `py` works: `python` and `python3` open the Microsoft Store. Either turn off the Store shortcuts (Settings → Apps → Advanced app settings → App execution aliases) or use `py -m http.server 8000`. For the browser test, also run `py -m pip install playwright` then `py -m playwright install chromium` — **Brendan** — 2026-10-27
- [ ] OPS: Test run: start a fresh session and check that the catch-up and automatic logging work — **Brendan**, then **Dad** — 2026-10-25
- [ ] OPS-3: Review this way of working after two weeks of use — **Both** — 2026-10-25
- [ ] WEB: The oil replay test fails on Windows computers, because Windows changes the line endings in `index.html` when the repo is downloaded. Not a website bug, but it makes local test runs look broken — **unassigned** — 2026-10-26
- [ ] Pick the first section to plan in detail, and who writes it — **Both** — 2026-10-26
- [ ] BRD: Add Dad's branding request, issue #7, to the plan — **unassigned** — 2026-10-27
- [ ] AST-5 / BRK-1: Before trade suggestions or the broker connection reach anyone beyond us, find out what UK financial-advice rules allow — **Both** — 2026-10-27

## Waiting for review

- [ ] PRC-1: Beginner paper trading, PR #2 (issue #3) — **Dad** — waiting on Brendan
- [ ] OPS-4: Trade suggestions and broker connection added to the plan (decisions 13 and 14) — **Brendan** — waiting on Dad to confirm the wording

## Done

- [x] OPS-4: Sections and codes for the plan, with Dad's monitoring and alerts, PR #5 (merged 2026-10-27) — **Brendan** — 2026-10-26
- [x] OPS: Relaxed review rule, decision 11 (PR #6, merged into PR #5 by Dad) — **Brendan** — 2026-10-26
- [x] OPS-1: Shared way of working and privacy guardrails, PR #4 (approved by Dad, merged 2026-10-26) — **Brendan** — 2026-10-25
