# 2026-10-29 · Dad · EIA reconciliation review (DAT-3)

**Goal:** review the supplied successful EIA report and prepare a draft PR,
without overwriting source data, merging or requiring credentials.

**What changed:** [draft PR #19](https://github.com/Facemankev/Oil-event-replay/pull/19), separate `dad/dat-3-eia-reconciliation` branch from current main,
independent of PR #16. Preserved the original report and created a read-only
review command, 102 curated official EIA table-row transcriptions and a
reproducible per-date review. Report hash and evidence-file hash are retained.

The report records 10,348 equal values, three Brent differences, 137 API-only
rows and 17 seed-only rows. Every one of the 157 disputed series/date pairs was
checked against official EIA HTML. All three differences conflict with HTML,
which corroborates the seeds; all 17 API omissions have published seed-matching
HTML prices. All 137 API-only dates have blank HTML cells. There are no confirmed
numeric seed gaps among them. Calendar labels do not establish holiday closures.
No revision cause or revision timestamp is known. Keep the existing values.

Added optional read-only inspection of the exact retained primary snapshot, bound
to the supplied response hash, metadata, units, dates and values. This needs no
key and distinguishes explicit API nulls from unavailable summary information.
No database-write or apply command exists. Existing output paths are refused.

All 32 Python database/event/reconciliation tests and the existing research
suite passed. Review reproduction is byte-for-byte deterministic. Source hashes
and the read-only audit database remain unchanged under tests; negative/zero/null
prices, corrupted payloads, source conflicts and existing-output refusal are
covered. No browser rerun was needed: no page or layout code changed. The original
Windows report retains its exact CRLF bytes; provenance-bearing CSV/report
paths are protected against Git line-ending conversion, and the existing
shell-script LF rule is preserved.

**Unfinished:** resolve the EIA API/HTML disagreement with the retained response
snapshots or EIA clarification. The raw API snapshot was not attached or fetched
again here; it is not claimed as independently replayed. Any later price edits
require review and immutable source/version preservation. No canonical CSV,
SQLite schema, default importer, static export, dashboard or research result
has been modified. PR #16, PR #2 and both previews are unchanged.

**For Brendan:** review the held corrections and all date classifications. Do not
replace prices solely to make an API-only equality check pass.

**Plan changes:** Now/status only; no vision, principles or decisions changed.
