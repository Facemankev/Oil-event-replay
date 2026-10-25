# Market Ripple plan

Last updated: 2026-10-25 by Brendan (first draft, to be checked by Dad)

This is the living plan. The top sections change rarely and only when we
both agree (use `plan-change`). *Now* and the milestone statuses are updated
every session.

## 1. Vision

> **To be written by Dad.** One paragraph: what Market Ripple is for, who it
> is for, and what it should become. Everything else in this plan should
> follow from it.

## 2. Principles

Taken from the README and research notes, which Dad wrote.

- No invented or interpolated prices. Every number has a visible source.
- Historical moves around an event don't prove the event caused them, and
  don't predict trading results.
- Missing data is shown as missing.
- Beginner-friendly: plain explanations alongside the data.
- A static website with no build step and no API keys needed to use it.

## 3. Workstreams

A draft read from what's in the repo today. Dad to confirm, rename or
reorder.

| Workstream | What it covers | Where it lives |
| --- | --- | --- |
| Oil event replays | The seven original oil-price event replays, with replay controls and the learning guide | `index.html`, `data/events.js` |
| Research lab | Comparing several markets around one event (Brexit: Apple and Brent) | `research/`, `data/research-data.js` |
| Sourced data | Adding verified price histories with recorded sources and licences | `data/`, `data/SOURCES.md` |
| Paper trading | Practice trading with pretend money on historical and (optionally) current prices | PR #2, issue #3 |
| Database and assistant | The future database design and an AI research assistant | `research/schema.sql`, `research/ARCHITECTURE.md` |
| Ways of working | This `team/` system, GitHub settings, onboarding Brendan | `team/`, `CLAUDE.md` |

## 4. Milestones

Status: Done · In progress · Waiting for review · Planned · Blocked

| Milestone | Workstream | Status | Owner | Depends on |
| --- | --- | --- | --- | --- |
| Seven oil replays live | Oil event replays | Done | Dad | — |
| Brexit multi-market comparison live (PR #1) | Research lab | Done | Dad | — |
| Beginner paper trading (PR #2, issue #3) | Paper trading | Waiting for review | Dad | Brendan's review |
| Live prices for paper trading | Paper trading | Blocked | Dad | A price provider licence and a deployed proxy (see PR #2) |
| Shared way of working and privacy guardrails set up | Ways of working | Waiting for review | Brendan | Dad's review |
| Vision written | Ways of working | Planned | Dad | — |
| Source-specific data ingestion | Database and assistant | Planned | — | Vision, see `research/ARCHITECTURE.md` |

## 5. Now

What each of us is on this week. Keep it short. Details live in `TODO.md`.

- **Dad:** paper trading (PR #2) waiting for Brendan's review. Next: write
  the vision and turn on the GitHub protections.
- **Brendan:** setting up the shared way of working and privacy guardrails
  (`brendan/collab-setup`). Next: review PR #2.

## 6. Open questions

- How do we settle a disagreement, given we have equal say?
- Does the repo stay on Dad's account, or move to a free GitHub organisation
  where both of us are owners?
- Who is Market Ripple for: personal learning, family, or the public?

## Change history

Big changes to sections 1–3, newest first. Small updates are in `log/`.

- 2026-10-25: first draft of this plan (Brendan). Vision left for Dad.
