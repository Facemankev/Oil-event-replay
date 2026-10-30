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



## To do

- [ ] DAT-3: Reconcile Brent/WTI against authenticated primary EIA data; retain discrepancy/revision evidence before extending matching — **Dad** — 2026-10-29

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
- [ ] WEB: Install Python, which is needed to preview the site locally (`python3 -m http.server`) and for the browser test — **Brendan** — 2026-10-25
- [ ] OPS: Test run: start a fresh session and check that the catch-up and automatic logging work — **Brendan**, then **Dad** — 2026-10-25
- [ ] OPS-3: Review this way of working after two weeks of use — **Both** — 2026-10-25
- [ ] WEB: The oil replay test fails on Windows computers, because Windows changes the line endings in `index.html` when the repo is downloaded. Not a website bug, but it makes local test runs look broken — **unassigned** — 2026-10-26
- [ ] Pick the first section to plan in detail, and who writes it — **Both** — 2026-10-26
- [ ] BRD-4: Restyle the live site (`index.html`) in the house style, once decision 13 is agreed. Removing the current look counts as a huge change, so it goes to the other partner — **unassigned** — 2026-10-27
- [ ] BRD-1: Design the real logo (the ripple mark in the skill is a placeholder) — **unassigned** — 2026-10-27

## Waiting for review

- [ ] WEB-2 / MAT-3 / PRC-1: Connected application ([draft PR #22](https://github.com/Facemankev/Oil-event-replay/pull/22), stacked on #20/#16; [Issue #21](https://github.com/Facemankev/Oil-event-replay/issues/21)); [public preview](https://market-ripple-app-review.g86hz2pjsh.chatgpt.site/app/), Chromium/WebKit local and deployed flows passed; physical iPhone acceptance outstanding — **Dad** — 2026-10-30

- [ ] MAT-3 / CMP-2: Cohort summaries, 1/3/5/10/20 observation days, evidence/risk ranking and sourced severity ([draft PR #20](https://github.com/Facemankev/Oil-event-replay/pull/20), stacked on #16); [private working preview](https://market-ripple-cohort-review.royaltulip9.chatgpt.site/matching/), automated checks passed — **Dad** — 2026-10-29
- [ ] MAT-2 / MAT-3: Working historical matching, Gold × Desk page and provisional-source gates ([PR #16](https://github.com/Facemankev/Oil-event-replay/pull/16)); EIA differences await the separate PR #19 review — **Dad** — 2026-10-29



- [ ] PRC-1: Beginner paper trading, PR #2 (issue #3) — **Dad** — waiting on Brendan
- [ ] BRD-2: House style "Gold × Desk" and the `market-ripple-design` skill (decision 13) — **Brendan** — waiting on Dad

## Done

- [x] DAT-3 / EVT-1 / BRD-2: Combined database and original-preview validation; README/PLAN/TODO conflicts resolved, dashboard and PR #2 preserved — **Dad** — 2026-10-29
- [x] EVT-1: Approved PR #14 merged; 24 events, 48 descriptive results, real DAT-3 export integration test in CI — **Dad** — 2026-10-29
- [x] BRD-2: Approved isolated Gold × Desk preview, PR #15; public URL in README, original design unchanged — **Dad** — 2026-10-29

- [x] DAT-3: Historical price database, approved PR #12 merged; 10,368 secondary-source prices — **Dad** — 2026-10-29

- [x] OPS-4: Sections and codes for the plan, with Dad's monitoring and alerts added, PR #5 (merged by Dad) — **Brendan** — 2026-10-26

- [x] OPS: Relaxed review rule, decision 11 (PR #6, merged into PR #5 by Dad) — **Brendan** — 2026-10-26
- [x] OPS-1: Shared way of working and privacy guardrails, PR #4 (approved by Dad, merged 2026-10-26) — **Brendan** — 2026-10-25
