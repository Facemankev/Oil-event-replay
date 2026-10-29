# 2026-10-29 · Dad · Cohort evidence (MAT-3 / CMP-2)

**Goal:** extend existing historical matching with useful sample statistics,
1/3/5/10/20 observation-day windows, evidence/risk research ranking and sourced
severity. Separate draft PR, no merge; leave EIA review untouched.

**What changed:** `dad/mat-3-cohort-evidence`, [draft PR #20](https://github.com/Facemankev/Oil-event-replay/pull/20), stacked on PR #16. Reuses the
existing readers, matcher, price-window function, UI and Gold × Desk stylesheet.
Adds a separate 240-window catalogue, deterministic cohort summaries, precise
membership/exclusions, both-benchmark research priority and four reproducible
demonstrations. The original PR #16 catalogue and default horizons are unchanged.

Six contemporaneous NHC advisory wind facts add a limited severity measure.
They are primary-bulletin operational estimates, not damage/best-track data;
times and source hashes are retained. Other severity remains unknown. Supply/
demand channel labels are explicit mechanism hypotheses. All prices remain
provisional pending the separate EIA API/HTML reconciliation review (PR #19).
No reconciliation artifacts/decisions, source CSVs, schemas, original events,
published price export, dashboard, paper trading or other PR branches are changed.

Group summaries exclude weak/location-mismatched events, unavailable/future
outcomes and overlapping windows without using outcomes to choose membership.
Evidence dominates a bounded sign-neutral movement component and explicit risk
penalties. Counts do not become probabilities or guaranteed returns.

Validation: 35 Python tests, the matching/cohort/research Node suites and all
five browser regressions passed locally. New tests cover temporal cutoffs,
self/future leakage, opposite channels, pinned severity, overlap membership,
null/invalid values, denominators, empty states and bounded sign-neutral ranking.
Four demonstrations reproduce from the catalogue. Canonical data, original
matching catalogue, price/event modules and EIA-related files are unchanged.

[GitHub Actions](https://github.com/Facemankev/Oil-event-replay/actions/runs/40953376424)
also passed the combined unit/build/browser checks. Brendan is requested as
reviewer. Nothing merged; main and the other feature branches are unchanged.

[Working preview](https://market-ripple-cohort-review.royaltulip9.chatgpt.site/matching/)
published successfully as a separate private Sites deployment. Sign in with
the same ChatGPT account. Its nine executable/data/style files match the
tested source bytes. Existing matching and branding previews are untouched.

**Unfinished:** review and physical iPad Safari validation. Existing price
vintages/publication clocks still prevent a point-in-time backtest. The calendar
is actual reporting observations, not a verified exchange trading calendar.
PR #19's API/HTML disputes and possible causes remain unresolved by this work.

**For Brendan:** inspect cohort membership, severity timestamps, overlap exclusions,
summary denominators, risk ranking and source controls. A small selected sample
and shared market regimes can limit the usefulness of any median.

**Plan changes:** Now/status only; vision, principles and decisions unchanged.
