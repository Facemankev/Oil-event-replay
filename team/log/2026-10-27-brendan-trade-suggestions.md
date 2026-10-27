# 2026-10-27 · Brendan · Trade suggestions and broker connection

**Goal:** add the two requests Dad made in his last PR #5 comments, which
didn't make it in before PR #5 was merged.

**What changed:** on branch `brendan/plan-trade-suggestions`:

- Decision 13 proposed, replacing decision 2 and the "never says buy or
  sell" part of decision 12. Market Ripple may rank potential trades and
  suggest a direction and timeframe where the evidence supports it, always
  labelled uncertain and educational, never guaranteed, with the evidence,
  confidence, uncertainty and risks. Every suggestion's outcome is recorded
  openly. Still never claims an event caused a move.
- Decision 14 proposed: a future broker connection (new section BRK,
  possibly Trading 212). Every real order needs the user's explicit
  approval; no unattended trading; built in stages (read-only, demo, real)
  only after paper trading is proven; broker keys on a server only.
- `PLAN.md`: vision note, principles, an eleventh section (BRK, order 4),
  milestones, *Now*, two open questions (UK financial-advice rules, and how
  we judge whether suggestions work) and change history.
- New plans AST-5 (ranked suggestions) and AST-6 (track record). PRC-3 now
  covers suggestions too. New page `plans/BRK.md` with BRK-1 to BRK-5.
- `CLAUDE.md` principles, and the MAT and LRN notes, follow the new
  decisions.
- No website code changed.
- Found that Python 3.13 is installed but only the `py` command works on
  this computer; to-do item reworded with the fix. Playwright isn't
  installed yet.

**Unfinished:** the wording waits for Dad to confirm.

**For Dad:**

- Please check the wording of decisions 13 and 14, and the new BRK page.
- The UK financial-advice question needs us both before suggestions reach
  anyone else.

**Plan changes:** decisions 13 and 14 proposed; decision 2 and part of 12
replaced; new section BRK.
