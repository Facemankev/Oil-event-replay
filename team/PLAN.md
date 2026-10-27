# Market Ripple plan

Last updated: 2026-10-27 by Dad (isolated BRD-2 visual preview)

This is the living plan. The top sections change rarely and only when we
both agree (use `plan-change`). *Now* and the milestone statuses are updated
every session.

## 1. Vision

> **To be written by Dad.** One paragraph: what Market Ripple is for, who it
> is for, and what it should become. Everything else in this plan should
> follow from it.

*Dad's long-term objective (from his review of PR #5):* Market Ripple
monitors world events automatically, compares them with historical market
behaviour, spots potentially significant trading opportunities and alerts
users. The AI does the research and explains the evidence, risks and
uncertainty in plain English. Users can then explore an opportunity with
small paper trades before risking real money. This is a core part of the
product, not an optional extra.

*Brendan's one-line take:* Market Ripple helps beginner traders compare
what's happening now with similar events in the past, and see how markets
moved after them.

## 2. Principles

Taken from the README and research notes, which Dad wrote.

- No invented or interpolated prices. Every number has a visible source.
- Historical moves around an event don't prove the event caused them, and
  don't predict trading results.
- An alert or "opportunity" says what a current event resembles and what
  markets did after those past events, with the evidence, risks and
  uncertainty. It never says what will happen, and never says buy or sell.
- Missing data is shown as missing.
- Beginner-friendly: plain explanations alongside the data.
- The website stays static, with no build step and no API keys needed to
  use it. Background services (event monitoring, live prices) may run
  separately when needed, with any keys kept on the server and never in
  this repo.

## 3. Sections

The project is split into ten sections, each with a three-letter code. Each
section has its own page in [`plans/`](plans/), holding its goal and its
list of plans. The goals and plans there are **provisional**: starting
points for Dad to rewrite, not settled decisions.

| Code | Section | Goal (provisional) | Exists today | Order |
| --- | --- | --- | --- | --- |
| [EVT](plans/EVT.md) | Event library | A list of past events, each with its date, type, description and source | 7 oil events and Brexit | 1 |
| [DAT](plans/DAT.md) | Market data | Sourced price histories we're allowed to use, and later a database | Brent and Apple around Brexit; oil replay prices (no recorded source) | 1 |
| [BRD](plans/BRD.md) | Brand | Name, logo, colours, fonts and tone of voice, used the same everywhere | The name only | 1 |
| [WEB](plans/WEB.md) | Site and testing | The website itself: layout, hosting, tests, speed | Yes | 1 |
| [OPS](plans/OPS.md) | Ways of working | The `team/` folder, GitHub settings, the privacy guard | Yes (PR #4) | 1 |
| [MAT](plans/MAT.md) | Event matching | Spot today's events (by hand at first, automatically later) and find the past events most like them | No | 2 |
| [CMP](plans/CMP.md) | Comparison and charts | Show how markets moved around the matched events | Oil replays and the Brexit lab | 2 |
| [LRN](plans/LRN.md) | Learning | Plain explanations and honest warnings for beginners | The learning guide | 2 |
| [PRC](plans/PRC.md) | Practice trading | Pretend-money trading on historical prices, and trying an alert with a small paper trade | Draft (PR #2) | 3 |
| [AST](plans/AST.md) | AI assistant and alerts | Research matches, explain the evidence, risks and uncertainty in plain English, and alert users | Design notes only | 3 |

**Order** is a rough guide. 1 = foundations everything else needs. 2 = the
heart of the product. 3 = later. Later doesn't mean optional: monitoring
and alerts (MAT-4, AST-3, AST-4) are core to the vision, they just need
matching to work first. Work already under way (like PR #2) carries on
regardless.

### How the codes work

Three levels:

| Level | Looks like | Example | Where it lives |
| --- | --- | --- | --- |
| Section | `XXX` | `MAT` (event matching) | A row above, and `plans/MAT.md` |
| Plan | `XXX-n` | `MAT-1` (decide how a current event is entered) | A line in `plans/MAT.md`; its own file `plans/MAT-1.md` once it's written in detail |
| Task | `XXX-n.n` | `MAT-1.2` | Inside the plan's file, and in `TODO.md` when someone picks it up |

- Numbers are never reused. A dropped plan keeps its number, marked
  *Dropped*.
- Use the code wherever the work shows up: to-do items
  (`MAT-1.2: … — **Dad**`), branch names (`dad/mat-1-event-input`), pull
  request titles (`MAT-1: …`) and session logs.
- Work that doesn't belong to a plan yet can still be done. Give it the
  section code alone (`WEB: fix typo`).
- A detailed plan starts from [`plans/TEMPLATE.md`](plans/TEMPLATE.md).
  Writing or changing one is a normal pull request for the other partner
  to approve. Adding, removing or renaming a **section** goes through
  `plan-change`.

Plan statuses: Provisional · Agreed · In progress · Done · Dropped

## 4. Milestones

Status: Done · In progress · Waiting for review · Planned · Blocked

| Milestone | Code | Status | Owner | Depends on |
| --- | --- | --- | --- | --- |
| Seven oil replays live | CMP | Done | Dad | — |
| Brexit multi-market comparison live (PR #1) | CMP | Done | Dad | — |
| Beginner paper trading (PR #2, issue #3) | PRC-1 | Waiting for review | Dad | Brendan's review |
| Live prices for paper trading | PRC-2 | Blocked | Dad | A price provider licence and a deployed proxy (see PR #2) |
| Shared way of working and privacy guardrails set up (PR #4) | OPS-1 | Done | Brendan | Dad's review |
| Sections and codes for the plan agreed (PR #5) | OPS-4 | Done | Brendan | Dad's review |
| House style chosen and written down as a skill | BRD-2 | Waiting for review | Brendan | Dad's approval (decision 13) |
| Vision written | OPS | Planned | Dad | — |
| Source-specific data ingestion | DAT-3 | Planned | — | Vision, see `research/ARCHITECTURE.md` |

## 5. Now

What each of us is on this week. Keep it short. Details live in `TODO.md`.

- **Dad:** preparing a separate BRD-2 visual preview of Brendan’s original design; no live-site restyle or approval. Also, paper trading (PR #2) waiting for Brendan's review. Next: approve
  the sections with his monitoring and alerts added (PR #5), write the
  vision, then turn on the GitHub protections.
- **Brendan:** chose the house style, "Gold × Desk", from eight previews, and
  wrote it down as the `market-ripple-design` skill (BRD-2, decision 13), sent
  to Dad (`brendan/brd-2-design-system`). Next: review PR #2.

## 6. Open questions

- How do we settle a disagreement, given we have equal say?
- If Market Ripple becomes a commercial product, which parts stay public?
  (Decision 5)
- Does the repo stay on Dad's account, or move to a free GitHub organisation
  where both of us are owners?
- Who is Market Ripple for: personal learning, family, or the public?
  Brendan suggests beginner traders.
- How does someone tell Market Ripple what today's event is at first:
  pick from a list or type a description? Long term, the site spots it
  itself (MAT-1, MAT-4).
- Where do world-event news come from for monitoring, and what does that
  cost or license? (MAT-4; a paid feed is a huge change under decision 11)
- How do alerts reach people: on the site, by email, or something else?
  (AST-4)

## Change history

Big changes to sections 1–3, newest first. Small updates are in `log/`.

- 2026-10-26: Dad's monitoring and opportunity alerts added inside the
  existing sections (MAT-4, AST-3, AST-4, PRC-3, WEB-4), with two
  principles reworded so they fit: alerts describe past patterns and never
  predict or say buy/sell; the website stays static but background
  services are allowed (decision 12).
- 2026-10-26: workstreams replaced by ten coded sections (EVT, DAT, BRD,
  WEB, OPS, MAT, CMP, LRN, PRC, AST), with a three-level code system and a
  page per section of provisional plans (Brendan, decision 10, for Dad to
  confirm). Brand and event matching are new; the rest regroup the old
  workstreams.
- 2026-10-25: first draft of this plan (Brendan). Vision left for Dad.
