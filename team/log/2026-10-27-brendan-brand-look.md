# 2026-10-27 · Brendan · House style (BRD-2)

**Goal:** start the brand conversation, try different looks for the site, and
settle on one that every future page can follow.

**What changed:** on branch `brendan/brd-2-design-system`:

- Tried eight looks side by side on a throwaway preview of the Brexit page
  (real Brent prices from `data/`): today's look, liquid glass (including real
  light-bending glass from the free liquidGL library), Apple clean (light and
  dark), Research desk (light and dark), Terminal, Newsprint, Gold, and
  Gold × Desk. The preview isn't in the repo.
- Chose **Gold × Desk**: Gold's dot grid, very light glass tiles, rounded
  corners, pill buttons and chart glow, with Research desk's navy, off-white
  and teal colours (charcoal grey in dark mode) and its fonts (Newsreader and
  Public Sans).
- Checked it with the UI/UX Pro Max and frontend-design guidance: every text
  colour passes 4.5:1 contrast in both themes, buttons are at least 44px,
  focus is visible, reduced motion and reduced transparency are handled, and
  the chart has a caption, a price table, a caveat and its source.
- New skill `.claude/skills/market-ripple-design/`: `SKILL.md` (the rules),
  `design.css` (tokens and components) and `example.html` (a working page in
  the style). `CLAUDE.md` now points to it for anything visual.
- Decision 13 proposed. BRD-2 waiting for review. New to-do items for BRD-4
  (restyle the live site) and BRD-1 (real logo). Tidied the PR #5 items
  into Done, since Dad merged it.
- Ran UI/UX Pro Max on the example page before sending it, and fixed what it
  found: the dark-mode grey for dates and captions was just under 4.5:1 on
  the glass tiles (now `#a6adb5`, 5.1:1); on phones the headline was squeezed
  beside its icon (icon now sits above it); and on phones the key figures
  didn't line up when a label wrapped (labels now reserve two lines). Its
  generated "design system" suggestions (a green wellness style, then gold
  and purple) didn't fit the brief or decision 13, so they weren't used.
- No website code changed.

**Unfinished:** the live site still has its old look (BRD-4, after Dad agrees).
The logo is a placeholder (BRD-1).

**For Dad:** please open `example.html` (see the skill folder) and approve or
change decision 13. Choosing the look is a decision, so it waits for you.

**Plan changes:** decision 13 proposed; BRD-2 now waiting for review.
