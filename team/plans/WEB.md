# WEB · Site and testing

**Status:** Provisional. Everything below is a starting point for Dad to
rewrite. · **Section owner:** not yet chosen

**Goal (provisional):** A website that loads quickly, works on phones, and is checked automatically before every change goes live.

**Exists today:** The static site (`index.html`, `research/`), unit tests that run on every pull request, and a browser test run by hand.

**Depends on:** Nothing.

## Plans

| Code | Plan | Status | Owner | Detail |
| --- | --- | --- | --- | --- |
| WEB-1 | Run the browser test automatically on every pull request | Provisional | — | — |
| WEB-2 | Decide where the live site is hosted and how it updates | Provisional | — | — |
| WEB-3 | Agree how pages are laid out as more sections are added | Provisional | — | — |
| WEB-4 | Background services: where monitoring (MAT-4) and live prices (PRC-2) run, kept apart from the static site | Provisional | — | — |

## Notes

- Principle: the website stays static, with no build step and no API keys needed to use it. Background services may run separately, with keys kept on the server, never in this repo (decision 12).

---

How codes work: see *How the codes work* in [PLAN.md](../PLAN.md). A plan
gets its own file (`WEB-1.md` and so on), copied from
[TEMPLATE.md](TEMPLATE.md), when someone writes it in detail.
