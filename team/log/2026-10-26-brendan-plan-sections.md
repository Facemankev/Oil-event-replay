# 2026-10-26 · Brendan · Plan sections and codes

**Goal:** set up the structure for the project plan, so detailed plans can
be written one section at a time later, mostly by Dad.

**What changed:** on branch `brendan/plan-sections` :

- `team/PLAN.md`: the six draft workstreams are replaced by ten coded
  sections: EVT (event library), DAT (market data), BRD (brand), WEB (site
  and testing), OPS (ways of working), MAT (event matching), CMP
  (comparison and charts), LRN (learning), PRC (practice trading) and AST
  (AI assistant). Each has a provisional goal and a rough order (1 =
  foundations, 2 = core, 3 = later).
- A three-level code system: section `MAT`, plan `MAT-1`, task `MAT-1.2`.
  Codes go in to-do items, branch names, pull request titles and logs.
- `team/plans/`: one page per section with 2–4 provisional plans each,
  drawn from what's in the repo and the 2026-10-25 audit, plus
  `TEMPLATE.md` for writing a plan in detail.
- Brendan's one-line take on the vision added under Dad's vision box, for
  Dad to use or ignore: beginner traders comparing current events with
  similar past events. Two new open questions: how a current event gets
  entered (MAT-1), and how "traders" fits with "beginner-friendly, never
  predicts results".
- Decision 10 proposed. `TODO.md` items now carry codes. `CLAUDE.md`,
  `AGENTS.md` and `team/README.md` point to the codes and `plans/`.
- No website code changed.
- Dad approved PR #4 (collaboration setup); Brendan merged it. OPS-1 marked done.

- Dad reviewed PR #5: happy with the sections, but wanted live world-event
  monitoring and opportunity alerts made explicit, inside the existing
  sections. Added as MAT-4, AST-3, AST-4, PRC-3 and WEB-4, with his
  long-term objective under the vision. Two clashes resolved in the
  wording rather than by another round of questions: alerts describe past
  patterns and never predict or say buy/sell (decision 2 stands), and the
  website stays static while background services are allowed. Proposed as
  decision 12.
- Dad merged the relaxed review rule (PR #6) into this branch. Decisions
  10 and 11 marked agreed.

**Unfinished:** every goal and plan is provisional, waiting for Dad.

**For Dad:**

- Please review the sections and codes, and confirm or change decision 10.
- Rewrite any goals or plans in `team/plans/` as you see fit. They're
  starting points only.
- Then choose together which section gets the first detailed plan.

**Plan changes:** workstreams replaced by ten coded sections (decision 10);
small changes merged by their author (decision 11); monitoring and alerts
added, two principles reworded (decision 12, proposed).
