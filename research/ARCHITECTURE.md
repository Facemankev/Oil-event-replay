# Historical research foundation

The existing application is a static, single-page dashboard. All seven original
oil event records, replay controls, oil CSV upload, comparison table and learning
guide remain. The research lab now has a reproducible two-market Brexit example.
There is no server, production database, external AI call or deployment change.

`schema.sql` is an executable SQLite relational design for the next stage, not a
claim that the static site has a populated database. It separates events,
instruments, series definitions, source snapshots, observations and research runs.
The six asset classes and requested event categories are represented. Every event
and price series references a source. Indexes support date-range research. Store
immutable raw responses outside SQL and reference their SHA-256 and licence;
create a new source snapshot and series for revisions. Ingestion must validate
ISO dates, finite values, units, currency, source rights, timezone, duplicates and
provider-specific missing values before transactional insertion. Negative oil or
zero observations can be legitimate: the future database permits them; the
current percentage-comparison CSV importer deliberately accepts only positive
prices and explains this constraint. Do not use it for negative futures prices.

`compare.js` is a pure, browser-independent calculation boundary. It returns the
actual common dates, raw endpoint values, source metadata, methodology and price
changes. The baseline is the last shared observation before the event; the end is
the last shared observation on or after the event inside ±7, ±30 or ±90 days.
Comparison fails explicitly if any selected market lacks both sides or shared
dates. Prices are never interpolated. Partial coverage, sparse observations and
different daily close times limit interpretation. This is not a causal event
study, benchmark-adjusted return, trading simulation or profit calculation.

Next: build source-specific ingestion with licence review and primary-provider
reconciliation, populate broader coverage, then expose read-only event search,
series coverage and comparison endpoints. Paginate long histories and cache by
immutable snapshot IDs and methodology version. Store research run evidence and
parameters for reproducibility. The current static seed is intentionally bounded.

A future conversational assistant should call those same read-only functions or
endpoints, retrieve verified evidence, and cite source IDs and actual dates with
every numerical claim. Return explicit missing-data states. Keep conversation
separate from market data; never let generated prose write observations or turn
correlation into causation. The existing learning guide remains labelled as
scripted, not live AI.
