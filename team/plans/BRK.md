# BRK · Broker connection

**Status:** Provisional, future. Everything below is a starting point for
Dad to rewrite. · **Section owner:** Dad

**Goal (provisional):** Later, connect Market Ripple to a real broker
(possibly Trading 212, if its API and supported instruments suit) so it can
prepare a trade for the user to approve or reject. The AI prepares; the
human decides.

**Exists today:** Nothing.

**Depends on:** PRC (paper trading built and proven first), AST-5 and AST-6
(suggestions and their track record), WEB-4 (a background service to hold
the broker keys).

## Plans

| Code | Plan | Status | Owner | Detail |
| --- | --- | --- | --- | --- |
| BRK-1 | Check whether the broker's API and instruments suit us, and what the rules allow (see *Open questions* in `PLAN.md`) | Provisional | — | — |
| BRK-2 | Read-only connection: show the account's positions and balance, place no orders | Provisional | — | — |
| BRK-3 | Demo orders on the broker's practice account | Provisional | — | — |
| BRK-4 | Real orders, each one approved by the user, with security controls, limits and duplicate-order prevention | Provisional | — | — |
| BRK-5 | Watch an open position and propose a review or exit (any real exit order also needs approval) | Provisional | — | — |

## Notes

- Decision 14: nothing reaches a real broker without the user explicitly
  approving that exact order. No unattended, automatic trading.
- A proposed trade shows the instrument, direction, order type, size, entry
  or limit price, estimated costs, timeframe, historical evidence,
  uncertainty and downside risks.
- After an approved order, show the broker's own result.
- Broker keys live on a server only, never in this repo or the website. The
  repo is public.
- This must not hold up the foundations or paper trading.

---

How codes work: see *How the codes work* in [PLAN.md](../PLAN.md). A plan
gets its own file (`BRK-1.md` and so on), copied from
[TEMPLATE.md](TEMPLATE.md), when someone writes it in detail.
