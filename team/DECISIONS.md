# Decisions

What we've agreed, so neither of us (nor an AI) re-argues it. Newest at the
bottom. A decision is **Agreed** once both of us have said yes. Until then
it's **Proposed**. To change one, add a new decision that replaces it. Don't
edit the old one.

| # | Date | Decision | Why | Proposed by | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | before 2026-10-25 | No invented or interpolated prices. Every number has a visible source. | The site is for honest learning. Made-up data would undermine it. | Dad | Agreed |
| 2 | before 2026-10-25 | Results never claim an event caused a price move or predict trading outcomes. | Correlation isn't causation, and beginners could be misled. | Dad | Agreed |
| 3 | 2026-10-25 | Every change goes through a pull request that the other partner approves. Nobody commits to `main`. | We're equal partners working separately. Nothing should go live unseen. | Brendan | Proposed: Dad to confirm |
| 4 | 2026-10-25 | The `team/` folder in the repo is our shared memory. AI sessions read it at the start and update it at the end. | The AIs forget between sessions, and the repo is the one place both of us and both AIs can see. | Brendan | Proposed: Dad to confirm |
| 5 | 2026-10-25 | The repository stays public. Guardrails stop the AI publishing anything private (decision 9). | Keeps the live website and GitHub's free safety features. | Brendan | Proposed: Dad to confirm |
| 6 | 2026-10-25 | Dad writes the vision. | It's Dad's idea, and the rest of the plan follows from it. | Brendan | Proposed: Dad to confirm |
| 7 | 2026-10-25 | The AI catches us up and logs work automatically, without being asked. It saves to our own branch as it goes. | We shouldn't have to remember. A session that ends suddenly loses nothing. | Brendan | Proposed: Dad to confirm |
| 8 | 2026-10-25 | `team/TODO.md` is our only to-do list. No new GitHub issues. | Two lists drift apart, and the AI would have to keep them in sync. | Brendan | Proposed: Dad to confirm |
| 9 | 2026-10-25 | A guard (`.claude/hooks/guard.sh`) checks everything the AI commits, pushes or posts to GitHub, and blocks keys, passwords, emails, phone numbers and our private words. It also blocks committing or pushing to `main`, merging without approval, and changing repo settings. A GitHub check repeats the scan on every pull request. | The repo is public and git history is permanent. Rules in writing aren't enough on their own. | Brendan | Proposed: Dad to confirm |
