# 2026-11-13 · Dad · Primary prices and FX (DAT-4 / INT-1)

**Goal:** Review #19/#28, reconcile primary oil-price evidence, extend verified
GBP/USD coverage and rerun all 24 events; separate draft, no merge or canonical
price replacement. Preserve the simple interface and existing previews.

**What changed:** Claimed `dad/dat-4-primary-prices-fx` at d45f3ff. Read actual PR
changes and EIA importer/review code. Primary EIA/Fed tables are accessible through
the supported web reader; source/vintage/API-payload limitations remain explicit.

**Unfinished:** Original API cause requires its retained sanitized payload; future as-of evidence and physical Safari acceptance. Final CI linked in PR Checks; Brendan review is non-blocking.

**For Brendan:** Review date alignment, reciprocal FX, missing-value handling,
coverage/abstentions and absence of invented historical availability.

**Plan changes:** Doing and Now only; no new vision or workstream changes.

Issue #29 explicitly authorises continuing without waiting for Brendan. Captured
all 5,440 weekday rows per current primary table (EIA Brent/WTI, Fed H.10), with
source locators, units, capture time and normalized-byte fingerprints. Direct
executor HTTP is denied; supported web-reader transcription is identified honestly,
with no invented original HTTP hash or historical publication/vintage clock.
The source loader validates every weekday, numeric/blank/ND marker and fingerprint.

All 10,368 seed prices match current EIA exactly (5,231/5,137), with zero numeric
gaps/differences in the seed range. All three older API numbers match the preceding
numeric EIA observation, but the original API cause remains unproven. Rechecked
137 explicit blanks and 17 matching omissions separately; no holiday/revision
reason inferred, no canonical record changed. New source snapshots alone retain
13 later observations per benchmark, not a database overwrite.

Fed coverage is 5,224 numeric rates / 216 ND entries. Exact same-day reciprocal
conversion is used; all 34 old rates agree at their original four-decimal precision
and stay immutable. Reused the frozen INT-1 matcher/policy for all 24 events and
48 market cases, with real GBP historical paths and explicit gaps. At fixed five
oil-reporting observations: Brent 18 complete/6 incomplete, WTI 22/2, both 18/6.
Original-as-of completeness is zero. Buy 0 / Hold 0 / No Action 24 from flat accounts;
all events lack qualified as-of analogues. WTI is research only.

Same-entry joint-day coverage gives 23 Brent baselines; 24 only under explicitly
deferred entry. The strict 18-case counterfactual has 9 positive/9 negative under
declared costs, 5/13 under stressed costs, not policy signals. Missing rates remain
missing; future prices cannot affect frozen decisions. Full traces stay local under
work/ and are pinned by RESULTS.sha256; no generated long-number report is committed.

Local 47 Python / 72 JavaScript tests pass. Original dashboard, simple UI, pricing
and account modules, PR #28 report and prior previews are byte-unchanged. No merge,
credential request, paid service, live trading or blocked review dependency.
Next: draft and full CI; handover for Brendan is non-blocking.


[Draft PR #30](https://github.com/Facemankev/Oil-event-replay/pull/30) targets #28.
The implementation and concise handover are complete without waiting for Brendan.
Full Actions reruns the 47 Python/72 JavaScript suite, unchanged parent report,
new pinned primary report, original browsers and paper/list/detail flows in
Chromium/WebKit. Screenshots/reports are in `dat4-browser-reports`; final status is
in PR Checks. No original snapshot/account policy was migrated, no preview deployed,
no key requested and no branch merged. Source/provenance limitations remain explicit.
