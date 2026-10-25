# Decisions

What we've agreed, so neither of us (nor an AI) re-argues it. Newest at the
bottom. A decision is **Agreed** once both of us have said yes. Until then
it's **Proposed**. To change one, add a new decision that replaces it. Don't
edit the old one.

| # | Date | Decision | Why | Proposed by | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | before 2026-10-25 | No invented or interpolated prices. Every number has a visible source. | The site is for honest learning. Made-up data would undermine it. | Dad | Agreed |
| 2 | before 2026-10-25 | Results never claim an event caused a price move or predict trading outcomes. | Correlation isn't causation, and beginners could be misled. | Dad | Agreed |
| 3 | 2026-10-25 | Every change goes through a pull request that the other partner approves. Nobody commits to `main`. | We're equal partners working separately. Nothing should go live unseen. | Brendan | Agreed (Dad's review of PR #4) |
| 4 | 2026-10-25 | The `team/` folder in the repo is our shared memory. AI sessions read it at the start and update it at the end. | The AIs forget between sessions, and the repo is the one place both of us and both AIs can see. | Brendan | Agreed (Dad's review of PR #4) |
| 5 | 2026-10-25 | The repository stays public for now. Personal information, credentials and anything commercially sensitive stay out of it. If Market Ripple becomes a commercial product, we reconsider which parts stay public. | Keeps the live website and GitHub's free safety features, without giving away anything private or valuable. | Brendan, revised by Dad | Agreed (revised after Dad's review of PR #4) |
| 6 | 2026-10-25 | Dad writes the vision. | It's Dad's idea, and the rest of the plan follows from it. | Brendan | Agreed (Dad's review of PR #4) |
| 7 | 2026-10-25 | The AI catches us up and logs work automatically, without being asked. It saves to our own branch as it goes. | We shouldn't have to remember. A session that ends suddenly loses nothing. | Brendan | Agreed (Dad's review of PR #4) |
| 8 | 2026-10-25 | `team/TODO.md` is our main to-do list and roadmap. GitHub Issues may be used for individual bugs, technical tasks and feature requests; the to-do item links to the issue. | One place to see everything, with Issues where a discussion or detail belongs on its own. | Brendan, revised by Dad | Agreed (revised after Dad's review of PR #4) |
| 9 | 2026-10-25 | A guard (`.claude/hooks/guard.sh`) checks everything Claude commits, pushes or posts to GitHub, and blocks keys, passwords, emails, phone numbers and our private words, plus committing or pushing to `main`, merging without approval and changing repo settings. A GitHub check repeats the scan on every pull request. Its limits are documented (`CLAUDE.md`, `team/README.md`), and GitHub's own branch protection and required review are the real backstop. | The repo is public and git history is permanent. Automated checks help but can't catch everything, and don't cover Codex or anything done by hand on GitHub. | Brendan, revised by Dad | Agreed (revised after Dad's review of PR #4) |
