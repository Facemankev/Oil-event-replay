# 2026-11-12 · Dad · Decision evidence (INT-1)

**Goal:** Issue #27, separate draft stacked on #26, unchanged three-step UI,
paper-only. No merges, price correction or preview overwrite.

**What changed:** Reviewed #19, #24, #26 and existing matching/model tests.
Claimed `dad/int-1-evidence-decisions` at 20f54bb. PR #19 holds three API/HTML
conflicts; it does not establish a corrected point-in-time price series. Current
Harvey sample is 2 five-day cases / 1 full non-overlapping path, so Buy must abstain.
Build an auditable vertical slice around existing modules, not a new dashboard.

**Unfinished:** Brendan review and physical Safari acceptance; final automated results linked in PR Checks.

**For Brendan:** Inspect data/time guards, paper risk policy, abstentions and baselines.

**Plan changes:** Doing and Now only, no vision or decision changes.

Implemented `intelligence/engine.mjs`: source/time/instrument/FX/duplicate audit,
sourced three-order hypotheses with counterarguments, existing matcher plus
pre-condition/reaction non-overlap, 21-observation pre-context, prior-window
baseline and source-qualified cautious policy. New version-two paper runs retain
full decision traces, thesis/invalidation criteria and a 10% full-allocation risk
cap. Actual PR #26 version-one fixture restores exactly without silent migration.
The HTML, CSS, UI controller, matching/accounting cores and canonical data are
byte-unchanged. Existing previews have not been deployed over.

`evaluate.mjs --check` reproduces a source-hashed report over all 24 genuine events:
24 abstentions, zero entries; 16 negative later Brent USD outcomes, seven above
+1%; one exact GBP baseline and 23 unpriced cases. False positives undefined.
Costed fixed £5 Harvey baseline net about £0.1051; strategy stays cash, not proof
of accuracy. PR #19 findings are attributed to the pinned review, not a new API
fetch or a confirmed correction. No credentials or historical overwrites.

Local 38 Python / 63 JavaScript cases passed. Chromium desktop/iPhone paper flow
and new risk-cap/trace/legacy-restore integration passed. Local WebKit installation
is unavailable; CI will install/test both engines and all original regressions.
Next: full Actions results, Brendan review and physical Safari acceptance.


The privacy guard flagged derived floating-point substrings as possible phone
numbers in the generated full report. The initial shell sequence incorrectly
continued after the guard failure and pushed the first feature commit. Corrected
the unreviewed feature commit: removed the generated numeric report from source,
retained a deterministic checksum and local report generation. No personal data
or credentials were present; guard/settings/allowlist are unchanged. Future save
commands stop on any failure. No parent branch, preview or canonical data changed.


[Draft PR #28](https://github.com/Facemankev/Oil-event-replay/pull/28) targets #26;
Brendan requested. Local full suite is 38 Python / 63 JavaScript, with Chromium
original and INT-1 paper flows passed. CI repeats all database/import/source checks,
original browser regressions, the three-answer historical drilldown and INT-1
risk-cap/trace/legacy-restore flows in Chromium/WebKit. Results/screenshots are
in PR Checks (`intelligence-browser-reports`). The approved previews remain intact;
run the branch with the documented static server for the new backend policy.
