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

- [ ] DATA-3: Verified free daily equity/ETF-index/gold/IPO histories, rights-aware imports, separate historical/new evaluation ([Issue #51](https://github.com/Facemankev/Oil-event-replay/issues/51)), [draft #52](https://github.com/Facemankev/Oil-event-replay/pull/52), stacked on #50; importer/evaluation path built, zero new prices; acquisition blocked pending source-domain grant. Preserve original tests/UI/prices, no paid source/key/merge — **Dad — Doing; source acquisition blocked** — 2026-11-18

















## To do

- [ ] IPO-1: Separate IPO discovery/investable-outcome work ([Issue #42](https://github.com/Facemankev/Oil-event-replay/issues/42)); no allocation/IPO price assumptions in SIM-1 — **unassigned** — 2026-11-17

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

- [ ] DATA-2: Verified typed reference import / fixed-population audit ([draft PR #50](https://github.com/Facemankev/Oil-event-replay/pull/50), on #49; [Issue #47](https://github.com/Facemankev/Oil-event-replay/issues/47)). 99 World Bank publication values / 51 distinct asset-periods + 8 IPO reserve episodes; 110 then 0 inserted rows. Zero new daily security quotes/original vintages; broader equity/index/gold coverage blocked. Actual SIM/LEARN rerun unchanged: 69 settled (34 positive/35 negative), retained 21-test 4 Watch/17 No Action, no qualified model or supported Buy. New 16 tests pass; full final-head Actions in PR Checks. Separate #19, unchanged interface, £0/no merge — **Dad** — 2026-11-18
- [ ] CI-1: Universal offline/Chromium/WebKit required gate ([draft PR #49](https://github.com/Facemankev/Oil-event-replay/pull/49), on #46; [Issue #48](https://github.com/Facemankev/Oil-event-replay/issues/48)). No branch/path/draft filter; screenshots/traces/logs, failure proof and all-page touch/theme smoke. Existing tests intact. #45/#46 final-head successes verified and stale checklists corrected. Owner activation of protection remains necessary: App read is 403; no settings or merge. Local 14 Chromium suites and capture proof pass; final two-engine CI in PR Checks — **Dad** — 2026-11-18

- [ ] LEARN-1: Chronological candidate fitting and immutable later-event audit ([draft PR #46](https://github.com/Facemankev/Oil-event-replay/pull/46), on #45; [Issue #44](https://github.com/Facemankev/Oil-event-replay/issues/44)). Seven training / eleven validation / 21 later retained primary-event cases, 27 candidate fits; no cohort qualifies. Four diagnostic Watch: one settled gain / one settled loss / two incomplete; seventeen research No Action. Baseline ten settled (six positive/four negative); zero supported entries, no calibration/edge claim. Actual audit 21 predictions then 21 settlements, repeat adds zero. Local 142 Python/112 JS and Chromium profiles pass; final CI/WebKit in PR Checks. [Public learning preview](https://market-ripple-research-lab.g86hz2pjsh.chatgpt.site/learning/) and [SIM-1 preview](https://market-ripple-research-lab.g86hz2pjsh.chatgpt.site/simulations/) are separately published; native hosting confirms deployment, hosted-browser access is restricted in this executor. Full traces local, UI/accounts/prices/gates preserved; £0 data, no merge or review wait — **Dad** — 2026-11-17

- [ ] SIM-1: Retrospective costed hypotheses ([draft PR #45](https://github.com/Facemankev/Oil-event-replay/pull/45), on #41; [Issue #43](https://github.com/Facemankev/Oil-event-replay/issues/43)). 51-event gate diagnosis, 151 target pairs, 69 default settled paths / 34 positive / 35 negative after costs, all 36 rule/cost summaries and optional three-answer charts. Local 126 Python/112 JS and Chromium profiles pass; final full CI/WebKit in PR Checks. Full traces local, compact public evidence; accounts/prices/UI/gates preserved, £0 data, no merge. LEARN-1 follows after checks — **Dad** — 2026-11-17

- [ ] DATA-FREE-1: Free-source cross-market database and complete observation-only process ([draft PR #41](https://github.com/Facemankev/Oil-event-replay/pull/41), on #39; [Issue #40](https://github.com/Facemankev/Oil-event-replay/issues/40)); [public preview](https://market-ripple-free-data-review.g86hz2pjsh.chatgpt.site). 10,456 new Fed FX observations, 26,074 numeric primary observations total; 66 inherited secondary candidates remain separate. Five demonstrations all No Action, zero supported entries/orders/account changes. Local 110 Python/112 JS and new Chromium desktop/iPhone/iPad profiles pass; final full CI/WebKit in PR Checks. Native preview deployment confirmed; hosted browser access is blocked in this executor and physical Safari acceptance remains outstanding. Free only, no signup/key/billing/API charge; source/vintage/adjusted-series gaps documented, #37 coordinated, #19/UI/prices/accounts preserved. No merge — **Dad** — 2026-11-17

- [ ] HIST-1: Cross-market event library ([draft PR #39](https://github.com/Facemankev/Oil-event-replay/pull/39), on #36; [Issue #38](https://github.com/Facemankev/Oil-event-replay/issues/38)). 51 events / 86 source cards, 15,618 numeric oil/GBP observations and 13 separately reported reactions. Outcome-blind matches, as-of tests, immutable SQLite imports and read-only #37 handoff. All 51 No Action, no supported entry; original vintages and adjusted wider-asset series missing. Local 94 Python/112 JS and all ten Chromium scripts pass; full CI/WebKit in PR Checks. UI, data, accounts and previews preserved; no merge — **Dad** — 2026-11-17

- [ ] EVT-2: Fresh-news receipt/revision journal, history/peer checks and local-card latency ([draft PR #36](https://github.com/Facemankev/Oil-event-replay/pull/36), on #34; [Issue #35](https://github.com/Facemankev/Oil-event-replay/issues/35)). Original Nvidia software feed: ten versions, no original publication clocks, all No Action; first HTTP-to-card 5.320 seconds, conditional 304/reanalysis 3.804 seconds. Financial-news/price sources blocked; no verified intraday prices or publication-to-useful-alert claim. Local 74 Python/109 JS and all Chromium pass; full CI/WebKit in PR Checks. UI, accounts, source snapshots and previews preserved. No review wait or merge — **Dad** — 2026-11-16

- [ ] EVT-1 / MAT: Nvidia company-news replay and corporate-history/ripple cross-check ([draft PR #34](https://github.com/Facemankev/Oil-event-replay/pull/34), on #33; [Issue #32](https://github.com/Facemankev/Oil-event-replay/issues/32)). Six publication cards/four developments, four historical cases, 66 daily provider rows; eight cutoffs all No Action. Intraday prints/original availability unverified; direct RSS tunnel denied, offline path tested. Local 60 Python/99 JS and all Chromium pass; full CI/WebKit in PR Checks. No review wait, UI/account/data changes, preview overwrite or merge — **Dad** — 2026-11-14

- [ ] INT-2: Qualified Gulf-storm analogues and dated release evidence ([draft PR #33](https://github.com/Facemankev/Oil-event-replay/pull/33), on #30; [Issue #31](https://github.com/Facemankev/Oil-event-replay/issues/31)). Eight sourced storms added, 32 total; original 24 and expanded 32 all No Action, zero supported Buy. Local 52 Python / 83 JS and all Chromium regressions pass; full WebKit/CI status in PR Checks. Brendan review is non-blocking. Interface, original prices, parent reports and previews unchanged; no merge — **Dad** — 2026-11-14

- [ ] DAT-4 / INT-1: Primary oil/FX validation and 24-event rerun ([draft PR #30](https://github.com/Facemankev/Oil-event-replay/pull/30), on #28; [Issue #29](https://github.com/Facemankev/Oil-event-replay/issues/29)). All 10,368 prices match current EIA; 5,224 numeric Fed rates; five-observation coverage Brent 18/24, WTI 22/24; Buy 0 / Hold 0 / No Action 24. Local 47 Python/72 JS passed; CI in PR Checks. Proceeded without waiting for Brendan; no merge or canonical/UI changes — **Dad** — 2026-11-13

- [ ] INT-1: Evidence/condition gates, reproducible paper traces, risk limits and 24-event walk-forward audit ([draft PR #28](https://github.com/Facemankev/Oil-event-replay/pull/28), stacked on #26; [Issue #27](https://github.com/Facemankev/Oil-event-replay/issues/27)). Local 38 Python/63 JavaScript and Chromium passed; CI and Brendan review in PR Checks. UI, canonical data and previews unchanged — **Dad** — 2026-11-12

- [ ] WEB-2 / MAT-4 / PRC-1: Three-answer opportunity card and historical event list/detail ([draft PR #26](https://github.com/Facemankev/Oil-event-replay/pull/26), based on #24; [Issue #25](https://github.com/Facemankev/Oil-event-replay/issues/25)); [public preview](https://market-ripple-three-step-review.g86hz2pjsh.chatgpt.site/ripple/). Local 38 Python/51 JavaScript and Chromium desktop/iPhone/iPad pass; full CI in PR checks. Brendan review and physical Safari acceptance outstanding — **Dad** — 2026-11-10

- [ ] MAT-4 / PRC-1 / WEB-2: Two-screen ripple/decision replay ([draft PR #24](https://github.com/Facemankev/Oil-event-replay/pull/24), stacked on #22; [Issue #23](https://github.com/Facemankev/Oil-event-replay/issues/23)); [public preview](https://market-ripple-ripples-review.g86hz2pjsh.chatgpt.site/ripple/), 38 Python/46 Node plus Chromium/WebKit passed. Physical Safari acceptance outstanding — **Dad** — 2026-11-01

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
