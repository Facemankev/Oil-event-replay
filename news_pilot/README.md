# EVT-2: fresh-news receipts and controlled alert latency

Issue #35, stacked on draft PR #34. Working, bounded **paper-only** ingestion and
local-card pilot. No existing UI, public preview, paper account, price database,
equity source snapshot or parent report is modified. No external alert is sent.

## Run

Python standard library and Node (CI uses Python 3.12 / Node 22). No key, signup,
paid feed or broker connection.

```sh
python3 -m news_pilot.run --source nvidia_releases --journal work/news-pilot/session
python3 -m news_pilot.run --source nvidia_news --journal work/news-pilot/session
python3 -m news_pilot.run --source fed_news --journal work/news-pilot/session
python3 -m news_pilot.demo --check --output work/news-pilot/controlled-demo.json
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.cjs tests/*.mjs
```

Each command performs **one** controlled run, writes an immutable run report in
its journal directory and exits. No scheduler or continuous monitoring is installed.
Repeating before the per-source deadline performs no request. Keep the same journal
for a continuing pilot; a new directory is a separate controlled session, not a way
to evade the publisher's limits. Raw responses and full traces remain in ignored
`work/`; reviewed aggregate measurements are in `OBSERVATIONS.json`.

The response contains the existing **what happened / likely outcome / suggested
action** contract. Historical details and source evidence are separate fields;
there is no new application screen or preview to learn.

## Sources and observed access

| Registered original source | Purpose | Observed result |
| --- | --- | --- |
| [Nvidia TensorRT-LLM release Atom feed](https://github.com/NVIDIA/TensorRT-LLM/releases.atom) | Company software/product updates | HTTP 200; ten entries; conditional repeat HTTP 304 |
| [Nvidia newsroom RSS](https://nvidianews.nvidia.com/releases.xml), [publisher directory](https://nvidianews.nvidia.com/rss) | Company announcements | Environment tunnel/policy 403 |
| [Federal Reserve press feed](https://www.federalreserve.gov/feeds/press_all.xml) | Wider-market news | Environment tunnel/policy 403 |
| Nasdaq public NVDA information endpoint | Timestamped price probe | Environment tunnel/policy 403; no verified price obtained |

The GitHub feed is an **original Nvidia-published software feed on a permitted
host**, not a proxy or mirror for blocked financial news. Software release notes
are **not established market-moving announcements**. The observed feed provided
update timestamps but no original publication timestamps. None of its ten entries
qualifies as fresh original financial news. We do not invent a publication time
from update, fetch or receipt time.

Public-source URLs are fixed in `registry.json`, with specific article prefixes.
No arbitrary URL, login, paid service, alternate proxy or credential is accepted.
[GitHub usage policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies)
apply. The pilot uses a conservative locally chosen **60-second minimum** per
source, ETag / Last-Modified conditionals, bounded responses (4 MiB / 100 entries)
and single requests without automatic retry loops. The interval is not claimed to
be a publisher-guaranteed freshness level. Preserve inherited TLS/proxy settings.

Nvidia financial news, Fed news and exchange-price access need appropriate grants
in this execution environment before they can be tested directly. Their denials
remain failures, not empty successful feeds. No broad-market or live-price source
coverage is claimed from the successful software-feed fetch.

## What was measured

`OBSERVATIONS.json` retains actual source URLs, response-body fingerprints,
receipt clocks, HTTP outcomes, counts and rounded phase timings from controlled
runs on **16 November 2026**. It does not contain full articles, author/contact
information, cookies or credentials. The raw successful body is retained locally
under its SHA-256 filename for review; it is not committed.

Three distinct clocks are kept:

- **Publisher publication/update:** original source declarations, separately null
  when absent. A declared update does not prove first disclosure.
- **Actual receipt:** recorded after the HTTP response body has arrived. It is
  first seen by this journal, not proof of when another service could have seen it.
- **Local card ready:** analysis completes after parsing, persistence, classification,
  historical cross-check and price-evidence checks. This is not notification delivery.

Monotonic timings separately measure fetch, normalization, ingestion and analysis,
including Node startup. UTC wall clocks identify receipt/analysis cutoffs. A wall
clock regression blocks importing the response; durations are not inferred by
subtracting publisher timestamps.

**Publication-to-useful-financial-alert latency remains unknown.** The successful
feed lacks original publication clocks and qualified financial materiality. The
measured fetch-to-local-card path is functioning; it does not prove that an alert
would beat a market move. Two controlled HTTP samples are not an SLA or a percentile.

Under an *ideal* regular 60-second polling schedule, a newly available feed item
could wait between zero and 60 seconds for the next poll, plus fetch/processing.
Publisher delay, scheduling jitter, outages, backoff and missing evidence remain
additional unknowns. No such continuous schedule is operated here.

## Receipt journal, revisions and failure handling

The dedicated SQLite journal has its own application identifier and refuses an
unrelated database. Writes are restricted to a subdirectory inside `work/`.

- Polls record request/receipt times, HTTP status, body hash and timings.
- Versions are append-only, keyed by source, canonical article URL and full normalized
  content fingerprint. Changes beyond the short displayed summary are still detected.
- Every observation retains declared publication/update metadata. Repeating identical
  content with a newer timestamp records a metadata change without refreshing first
  receipt or creating a new news event.
- HTTP 304 records a poll and reuses evidence; it does not create or freshen news.
- Concurrent workers reserve the next request atomically before fetching. Conditional
  headers are reused only for the same registered source.
- HTTP 401/403 and malformed feeds back off for an hour; failures are explicit.
  HTTP 429 honors `Retry-After` seconds or HTTP dates. Unrepresentable deadlines
  fail closed. Transport/server failures back off for at least five minutes.
- Redirects are not followed; cookies, authorization and error bodies are not logged.
  Unknown sources, URL credentials, unsafe headers, XML entities/unsupported encodings,
  invalid timezones and oversized input fail closed.

Actual first receipt and later revisions are filtered before their contents enter
an earlier decision. Full original source versions are not reconstructed from a
current page. An originally unknown publication clock cannot be upgraded into
fresh original news by a later timestamp. All eligible versions/counterpoints are
retained together. Three specifically known copies of the Nvidia board statement
are one issuer family even with different wording; unseen syndication relationships
are not guessed. Multiple versions/copies are not independent historical cases.

## Historical, market and decision checks

The existing deterministic company classifier, four real corporate cases, equity
calendar and daily reaction functions are reused. A separate wider-market classifier
covers monetary-policy, trade-restriction and oil-supply language. A product release
stays a product update even if technical text contains financial-looking words.

New source text is untrusted evidence, not instructions. Reported allegations and
denials/company counterpoints are retained; no investigation is treated as a finding.
Coarse oil-supply wording does not invent a storm, supply direction, location or
severity. Such world-event cross-checks remain Weak and never an eligible cohort.
Historical matches are ranked before returns; minimum support and evidence gaps
remain visible. No supported paper entry is possible without qualified evidence.

Live timestamped own/peer quotes are explicitly **unavailable**. The existing
Nvidia/AMD/Broadcom/Microsoft/QQQ/Nasdaq daily snapshot can supply a labelled
historical context check only when its dates are already observed under the parent
method. Opposing daily peer moves are retained instead of assuming sector contagion.
They are not live ticks, original-as-of verified prices, causal transmission or
executable GBP quotes. Missing quotes never become yesterday's fill, an inferred
09:31 price or a short after a decline.

All actual retrieved product entries produce **No Action/context only**, not new
supported trading opportunities. Materiality is unestablished, historical support
is unqualified, equity print/availability evidence is missing and the Nvidia GBP
paper instrument remains disabled. No order, account mutation, portfolio profit,
probability or guaranteed movement is created.

## Controlled replay and tests

`demo.py` reconstructs **test transport from the real, already sourced November 8
board-statement facts** in PR #34. It clearly labels the transport and clock as
controlled; this is not an original historical feed or actual old receipt. Four
cases cover a fresh pre-open item, one minute after open, after first close and an
old story newly received on November 16. All return No Action. Freshness alone
cannot overcome weak historical matches, price gaps or execution safeguards.

`DEMO.sha256` pins deterministic policy outcomes, not machine-dependent timing.
The generated demo also measures local processing, separately from actual HTTP
runs. No artificial fixture timing is presented as an observed live alert.

Automated checks cover bounded parsing, missing original clocks, deep-content
revisions, first-receipt preservation, conditional 304, concurrent polls, cooldown,
403/429/503 failures, clock/as-of boundaries, spoofed publishers, metadata reposts,
syndicated issuer copies, contradictory claims, broader shock categories, historical
cross-checks, opposing daily-market context and the unchanged three-answer contract.
Full CI runs all existing tests, database import/repeat/report checks and Chromium /
WebKit desktop/iPhone/iPad regressions, preserving all parent files. Physical Safari
acceptance remains a human check; no physical-device pass is claimed.

Next: enable a permitted financial-news source and verified timestamped price
source, retain genuine publication/receipt history, then measure a small period of
actual operating coverage. Do not lower evidence gates to manufacture a signal.
