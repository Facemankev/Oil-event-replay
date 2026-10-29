# 2026-10-29 · Dad · Cohort evidence (MAT-3 / CMP-2)

**Goal:** extend existing historical matching with useful sample statistics,
1/3/5/10/20 observation-day windows, evidence/risk research ranking and sourced
severity. Separate draft PR, no merge; leave EIA review untouched.

**What changed:** `dad/mat-3-cohort-evidence`, stacked on PR #16. Reuses the
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

**Unfinished:** review and physical iPad Safari validation. Existing price
vintages/publication clocks still prevent a point-in-time backtest. The calendar
is actual reporting observations, not a verified exchange trading calendar.
PR #19's API/HTML disputes and possible causes remain unresolved by this work.

**For Brendan:** inspect cohort membership, severity timestamps, overlap exclusions,
summary denominators, risk ranking and source controls. A small selected sample
and shared market regimes can limit the usefulness of any median.

**Plan changes:** Now/status only; vision, principles and decisions unchanged.
