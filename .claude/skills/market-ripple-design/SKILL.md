---
name: market-ripple-design
description: Market Ripple's look and feel ("Gold × Desk"). Use for anything visual in this project, including any page, chart, component, colour, font, icon, layout, dark mode or styling change to the website, mock-ups and previews, and slides or images that represent Market Ripple. Also use when reviewing whether something "looks right" or "on brand".
---

# Market Ripple design: "Gold × Desk"

This is the house style for everything Market Ripple shows people. It
combines Gold's layout (a dot-grid page, very light glass tiles with big
rounded corners, pill buttons, a soft glow around the chart) with Research
desk's colours and fonts (navy ink on off-white with one teal accent,
Newsreader and Public Sans). Brendan chose it on 2026-10-27 from eight
previews. It is decision 13 in `team/DECISIONS.md`. Until Dad approves it,
treat it as the proposed house style.

Two files sit next to this one:

- `design.css`: every token (colours, type, spacing, radii, motion) and the
  components below, ready to use. Copy what you need. Don't invent new values.
- `example.html`: a working page in this style with real Brent prices around
  the Brexit vote. Open it to see the look before building anything.

## Who it's for and what it should feel like

Beginners comparing today's world events with similar events in the past.
The page should feel like a calm, trustworthy research note: professional,
quiet and readable. It should not feel like a trading app, a crypto
dashboard or a generic AI-made site. The chart and the facts are the
point. Everything else stays quiet around them.

## The project's rules come first

These come from `README.md`, `data/SOURCES.md` and decisions 1, 2 and 12.
Design never overrides them:

- Every price has a visible source near where it's shown.
- Never invent, interpolate or smooth prices. Missing days are left out and
  the page says so ("Weekends and holidays have no price, so they're left
  out.").
- Wherever results appear, say that a past move doesn't prove the event
  caused it and doesn't predict future prices.
- Never show anything that implies a feature we don't have: no "LIVE" pills,
  fake statuses, fake logs, invented testimonials, prices or plans.
- The site stays static with no build step. Fonts come from Google Fonts. No
  other outside scripts unless a partner agrees.

## Colour

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--mr-paper` | `#f7f8f6` | `#26292d` | Page background |
| `--mr-ink` | `#13233a` | `#eceef0` | Headings, numbers, chart line, chosen button |
| `--mr-body` | `#3d4856` | `#c4c9cf` | Reading text |
| `--mr-muted` | `#5b6675` | `#a6adb5` | Captions, dates, axis labels, sources |
| `--mr-hair` | `#dfe3e8` | `#3b4046` | Gridlines and table rules only |
| `--mr-accent` | `#0f6e6e` | `#5cc2b8` | Teal: labels, one highlighted phrase, the event marker, icons |
| `--mr-up` | `#1e6b52` | `#7fd1a1` | Price rose |
| `--mr-down` | `#b3261e` | `#ff8f84` | Price fell |

- Teal is the only accent. Use it sparingly: small labels, one short phrase
  in a headline, the event line and band on a chart, and icon squares.
- Red and green mean price direction and nothing else. Always pair them with
  a sign (−4.0%, +2.1%), so colour is never the only signal.
- No gold, purple, blue gradients, neon or glowing text.
- Every text colour above passes 4.5:1 contrast in both themes, on the page
  and on the glass tiles, which are slightly lighter than the page in dark
  mode (lowest: muted, about 5.1:1 on a dark tile). If you add a colour,
  check it on both surfaces first.

## Type

- **Newsreader** (serif, weights 500 and 600): the brand name, headlines,
  panel headings and big key numbers.
- **Public Sans** (weights 400 to 700): everything else, including body text,
  buttons, labels, captions, chart labels and tables.
- Scale: hero `clamp(2.4rem, 5.6vw, 4.2rem)`, key figures
  `clamp(28px, 3.4vw, 38px)`, panel headings 26px, body 17px (1.55 line
  height), buttons 14px, labels and captions 13px.
- Sentence case everywhere. No labels in all capitals, no tracked-out
  eyebrow text above headings, and no `A · B · C` strings.
- Use tabular figures (`font-variant-numeric: tabular-nums`) wherever
  numbers line up.
- Keep reading lines under about 65 characters (`max-width: 62ch`).

## Surfaces and layout

- **Page:** off-white (or charcoal) with a faint dot grid every 32px
  (`.mr-page`).
- **Glass:** the header bar, panels and tiles all share one very light glass
  finish (`.mr-glass`): a faint sheen, a bright top edge, a soft lift and a
  14px blur, so the dot grid shows through as a haze. Keep it subtle. Don't
  stack glass on glass, and don't add colour glows to tiles.
- **Glow:** only the main chart card gets the soft teal glow
  (`.mr-chart-card`). One per page.
- **Shapes:** header bar is a pill (999px), panels have 32px corners, tiles
  have 24px corners, and buttons are pills.
- **Order on an event page:** header bar, then the event panel (icon square,
  headline, one-paragraph summary, market buttons), then a row of key-figure
  tiles, then the chart card with its caption, price table, caveat and
  source.
- **Phones:** tiles go two across under 640px, panels tighten, and wide
  charts scroll inside their own box. The page itself never scrolls
  sideways.

## Components (all in `design.css`)

| Class | What it is |
| --- | --- |
| `.mr-bar` + `.mr-brand` + `.mr-badge` | Header pill with the ripple mark, the name, and "Historical research, not trading advice" |
| `.mr-panel`, `.mr-panel-title`, `.mr-icon` | A content block with a 48px teal-tinted icon square that grows slightly on hover |
| `.mr-hero` + `.mr-hl` | Lead headline. At most one short phrase in teal |
| `.mr-btn` | Pill button. `aria-pressed="true"` (or `.mr-btn-primary`) fills it with ink |
| `.mr-figures`, `.mr-tile`, `.mr-label`, `.mr-figure`, `.mr-meta` | Key-figure tiles: teal label, big serif number, muted date |
| `.mr-chart-card`, `.mr-chart` | The chart card with the glow, and the SVG chart styles |
| `.mr-caption`, `.mr-disclosure`, `.mr-table` | What a chart point means, and "Show these prices as a table" |
| `.mr-note` | The caveat and the source line |

Icons are simple line drawings in SVG (1.7px stroke, `currentColor`).
Never use emoji as icons. The logo is a placeholder (a dot with three
ripples) until BRD-1 settles it.

## Charts

- A line chart of daily closes: ink line 2.5px, faint gridlines, dollar
  axis labels on the left.
- Count the x-axis in trading days from the event (T−10 … T0 … T+10), with
  the date under each label. T0 is the first trading day on or after the
  event.
- Mark the event with a dashed teal line labelled in plain words ("Result
  announced") and a teal band over the gap between the last price before
  and the first price after.
- Highlight only the two points either side of the event. Label exact values
  in their tooltips.
- Under every chart: a one-line caption saying what a point is, a "Show
  these prices as a table" disclosure with every value, the caveat, and the
  source.
- Give the SVG `role="img"` and an `aria-label` that states the main finding.

## Words

- Write for a beginner, in plain words. Name things the way people would.
- Buttons say what they do ("Show these prices as a table", not "More").
- No hype, no predictions, no "unlock", no "AI-powered".

## Motion

- Hover and state changes ease over 0.3s with `cubic-bezier(.4,0,.2,1)`.
- Panels and tiles may slide up 14px once when they first appear
  (`.mr-enter`). Never fade content in from invisible. The page must be
  readable even if animations don't run.
- Turn all of it off under `prefers-reduced-motion`. Glass becomes solid
  under `prefers-reduced-transparency`. Both are already in `design.css`.

## Light and dark

Light is the default. Dark follows the viewer's device, and
`data-theme="light"` or `data-theme="dark"` on `<html>` overrides it. Design
and check both. Every colour in this file has a dark value. Never use a
colour that only works in one theme.

## Before calling visual work finished

1. Compare it with `example.html`. Does it use only the tokens and
   components above?
2. Check both light and dark at desktop width and at 375px. No sideways
   scrolling, nothing clipped.
3. Check text contrast is at least 4.5:1, every button is at least 44px
   tall, focus outlines show when using the keyboard, and reduced motion
   and reduced transparency work.
4. Make sure every price shown has its source and caveat nearby, and nothing
   suggests a feature we don't have.
5. Run the project's tests (`node --test tests/research.test.cjs`), and the
   browser test when the layout changed.

## Changing the house style

The look is a decision (13), so changing it is a huge change under decision
11: propose it with `plan-change` for the other partner to approve. Small
refinements that keep to these tokens (spacing tweaks, a new component built
from them) are ordinary changes. Update this file and `design.css` together.
