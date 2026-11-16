# 2026-11-16 · Dad · Fresh-news pilot

**Goal:** Implement Issue #35 on draft #34, without waiting for Brendan. Test fresh-source ingestion and useful-alert latency with honest historical/price evidence.

**What changed:** [Draft PR #36](https://github.com/Facemankev/Oil-event-replay/pull/36) on `dad/evt-2-fresh-news-pilot`, stacked on verified #34 parent `c498d33`. Working bounded collection, append-only receipt/revision journal, conditional HTTP/backoff, classification/history/peer checks and local-card latency. Original software updates are not asserted to be market-moving financial news. No blocked-source proxy.

**Unfinished:** Permitted financial-news and timestamped exchange-price access; actual publication-to-useful-alert timing and an operating-coverage study. Full CI/WebKit status is in PR #36 Checks. No physical-device acceptance is claimed.

**For Brendan:** Review #36 later; it does not block progress. No merge or preview change. Inspect strict receipt/as-of filtering, original publication gaps, non-financial software-feed scope and opposing-peer evidence.

**Plan changes:** Doing/Now only.

Implemented persistent source reservations, real receipt/version journaling,
conditional HTTP, failure/backoff handling and source-bound classification.
Reuse parent corporate history, market calendar and labelled daily peer context.
No inferred original publication from updates and no stale daily quote is a live fill.
Direct permitted Nvidia software feed returned 200 / ten versions; repeat 304 /
zero new versions. All ten lack original publication clocks and remain context /
No Action. Financial Nvidia/Fed feeds and Nasdaq price probe remain policy-blocked
403; verified intraday prices and publication-to-useful-alert latency are unknown.
Measured first HTTP-to-card 5.320 seconds and conditional 304/reanalysis 3.804 seconds;
exact rounded phases in OBSERVATIONS.json. Two samples are not an SLA.
Controlled fixtures use real prior release facts and explicit artificial transport/
clocks, never a claimed historical/live alert.

Local 74 Python / 109 JavaScript and all ten Chromium browser scripts pass.
All four parent report checks reproduce; protected UI, accounts, original oil/
equity data and previews are unchanged. Draft #36 retains all checks and artifacts;
Brendan review is non-blocking, no merge or continuously running alert claim.
