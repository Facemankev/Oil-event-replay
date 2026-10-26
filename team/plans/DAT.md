# DAT · Market data

**Status:** Provisional. Everything below is a starting point for Dad to
rewrite. · **Section owner:** not yet chosen

**Goal (provisional):** Price histories for the markets we compare, each with a recorded source and a licence that lets us show it.

**Exists today:** Brent and Apple prices around Brexit (`data/`, sources in `data/SOURCES.md`). The seven oil replays' prices have no recorded source yet. A database design in `research/schema.sql`.

**Depends on:** Licences and data providers (PRC-2 needs the same answer).

## Plans

| Code | Plan | Status | Owner | Detail |
| --- | --- | --- | --- | --- |
| DAT-1 | Find and record sources for the oil replay prices, or mark them unsourced | Provisional | — | — |
| DAT-2 | Agree which data providers and licences we can use | Provisional | — | — |
| DAT-3 | Bring in new price histories with checks (see `research/ARCHITECTURE.md`) | Provisional | — | — |
| DAT-4 | Decide when the database in `research/schema.sql` is needed | Provisional | — | — |

## Notes

- Decision 1: no invented or interpolated prices. Every number has a visible source.
- Licence terms we negotiate are commercially sensitive and stay out of this public repo.

---

How codes work: see *How the codes work* in [PLAN.md](../PLAN.md). A plan
gets its own file (`DAT-1.md` and so on), copied from
[TEMPLATE.md](TEMPLATE.md), when someone writes it in detail.
