# 2026-11-16 · Dad · Fresh-news pilot

**Goal:** Implement Issue #35 on draft #34, without waiting for Brendan. Test fresh-source ingestion and useful-alert latency with honest historical/price evidence.

**What changed:** Claimed `dad/evt-2-fresh-news-pilot` at verified parent `c498d33`. Current environment restricts outbound sources. Use an original permitted company-release feed as a bounded ingestion test; do not present technical product releases as proven market-moving news or route blocked sources through proxies.

**Unfinished:** Receipt/revision journal, conditional HTTP/backoff, broader shock classification, measured local-card latency, tests and separate draft. Timestamped exchange prices may remain unavailable.

**For Brendan:** Later review, not a progress dependency. No merge or preview change.

**Plan changes:** Doing/Now only.

Implemented persistent source reservations, real receipt/version journaling,
conditional HTTP, failure/backoff handling and source-bound classification.
Reuse parent corporate history, market calendar and labelled daily peer context.
No inferred original publication from updates and no stale daily quote is a live fill.
Direct permitted Nvidia software feed returned 200 / ten versions; repeat 304 /
zero new versions. All ten lack original publication clocks and remain context /
No Action. Financial Nvidia/Fed feeds and Nasdaq price probe remain policy-blocked
403; verified intraday prices and publication-to-useful-alert latency are unknown.
Measured cold HTTP-to-card around 5.3 seconds; exact phases in OBSERVATIONS.json.
Controlled fixtures use real prior release facts and explicit artificial transport/
clocks, never a claimed historical/live alert.

Local 74 Python / 109 JavaScript and all ten Chromium browser scripts pass.
All four parent report checks reproduce; protected UI, accounts, original oil/
equity data and previews are unchanged. Next full CI/WebKit and separate draft.
