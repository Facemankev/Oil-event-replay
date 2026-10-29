# BRD-2: Gold × Desk visual review

This is an isolated review of Brendan's actual design, merged through PR #8.
`example.html` and `design.css` are byte-for-byte copies of
`.claude/skills/market-ripple-design/` at the source commit pinned in `source.json`.
The original chart, market/window controls, source caveats, light/dark themes,
typography, tokens and placeholder branding are preserved.

`index.html`, `review.css` and `review.js` add only review controls around that
unchanged example: responsive/device width, desktop 1440px, iPad portrait 820px
and iPad landscape 1180px. A fixed-width layout scales down when it cannot fit;
use the full-screen link to judge real text sizes on an iPad. This is layout
emulation, not a claim of testing physical iPad hardware or Safari.

Run from the repository root with `python3 -m http.server 8000`, then open
http://localhost:8000/preview/gold-desk/. No build or API key is required.
Google Fonts is used exactly as in the original design example; system fallbacks
remain available if font loading is blocked. Source price data is the original
historical example, with its original provenance and limitations.

Nothing here approves the house style or modifies the live dashboard, trading,
databases, or other feature PRs. Deployment is to a separate Sites project only.

Public review URL: https://market-ripple-gold-desk-review.royaltulip9.chatgpt.site

GitHub Pages provisioning could not be used because the environment blocks
GitHub API access. A separate free Sites project hosts only this preview.
Production Pages configuration and the live dashboard are untouched. The hosted page/design assets match this preview; review documentation and screenshots
are retained in the repository (hosting metadata stays outside it).
