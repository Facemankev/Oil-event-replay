# Historical paper practice in the integrated application

Reused from draft PR #2 at commit c2bcb92. The accounting core is unchanged.
The new application adds Gold × Desk presentation, optional research-reference
notes and explicit memory-only fallback when Safari denies browser storage.

Only the independent 2016 Brent/GBP exercise is enabled. It is a fractional,
unleveraged spot-reference learning exercise, not an executable oil instrument
or a simulation of whichever event was selected in research. £50 default cash,
£5 default virtual allocations, £1 minimum; all units/money are virtual.
No real orders, broker, account deposits, shorts or leverage.

Data: existing data/brent-brexit-source.csv and the unchanged PR #2
GBP/USD slice in data/gbp-usd-brexit-source.csv, joined on exact shared dates.
Sources, precision and end-of-day assumptions: ../data/SOURCES.md.
No interpolation; missing price/FX dates cannot be traded. Zero fees, spread,
slippage, dividends and interest are disclosed simplifications.

Browser-local v2 ledger, source-checked backup restore, sourced valuations and
virtual closes are retained. Export a backup before closing a memory-only tab.
Browser storage/backups can be edited and are not a tamper-proof audit.

Current mode is disabled in this integrated UI. No quote worker or provider is
included or deployed. PR #2 retains its separate optional-provider work; this
integration does not modify that PR. Existing core quote/corporate-action guards
are preserved/tested, without adding or enabling any current market connection.

See ../app/README.md for the end-to-end flow, setup and physical-device checklist.
