# AST · AI assistant and alerts

**Status:** Provisional. Everything below is a starting point for Dad to
rewrite. · **Section owner:** not yet chosen

**Goal (provisional):** The AI researches matched events, ranks the strongest potential trades, suggests a direction and timeframe where the evidence supports it, explains the evidence, risks and uncertainty in plain English (citing sources and real dates), alerts users, and keeps an honest record of how its suggestions turned out.

**Exists today:** Design notes in `research/ARCHITECTURE.md`. The learning guide is scripted, not AI.

**Depends on:** DAT, CMP, and MAT-4 for alerts.

## Plans

| Code | Plan | Status | Owner | Detail |
| --- | --- | --- | --- | --- |
| AST-1 | Decide what the AI does first, and which AI service | Provisional | — | — |
| AST-2 | The read-only research functions it would use | Provisional | — | — |
| AST-3 | Opportunity write-ups: what the event resembles, what markets did then, evidence, risks, uncertainty | Provisional (core) | Dad | — |
| AST-4 | Alerts: how and when users are told about a new opportunity | Provisional (core) | Dad | — |
| AST-5 | Ranked trade suggestions: direction (buy/long or sell/short), estimated timeframe, strength of evidence, confidence and risks, showing only the strongest few | Provisional (core) | Dad | — |
| AST-6 | Track record: record every suggestion and how it turned out, shown openly, including the wrong ones | Provisional (core) | Dad | — |

## Notes

- Dad: alerts are a core part of the vision, not an optional extra.
- Decision 13 (replaces decision 2 and part of 12): suggestions may give a direction and timeframe where the evidence supports it, always labelled uncertain and educational, never guaranteed, with evidence, confidence, uncertainty and downside risks. The user decides.
- See the open question in `PLAN.md` about UK financial-advice rules before suggestions reach anyone beyond the two of us.
- The assistant may never write prices, or turn a pattern into a claim of cause.

---

How codes work: see *How the codes work* in [PLAN.md](../PLAN.md). A plan
gets its own file (`AST-1.md` and so on), copied from
[TEMPLATE.md](TEMPLATE.md), when someone writes it in detail.
