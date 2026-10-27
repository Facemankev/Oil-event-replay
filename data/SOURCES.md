# Initial historical example

Retrieved 24 October 2026 using the connected GitHub file API. Values are copied
from actual source CSVs, not generated. The source slices are committed for audit.
The example covers 25 May–22 July 2016 (a ±30 calendar-day Brexit result window).
No other event has new built-in multi-market price coverage in this change.

| Series | Field used | Source file | Git blob SHA |
| --- | --- | --- | --- |
| Apple | AAPL.Close (not AAPL.Adjusted) | [Plotly finance-charts-apple.csv](https://github.com/plotly/datasets/blob/master/finance-charts-apple.csv) | 7b1bab3953bb5cdf47e84de1048ca04b0c991987 |
| Brent | Price | [datasets brent-daily.csv](https://github.com/datasets/oil-prices/blob/main/data/brent-daily.csv) | 183a6e25c91f33d0db3cc48238354d03fa164723 |

Verification means matching the upstream CSV values, not independently checking
an exchange feed. The Apple file is a secondary historical dataset, with no
exchange certification or explicit price licence established here. Review rights
and reconcile against a licensed provider before broader commercial distribution.
Apple uses the historical snapshot's share basis, before its later stock split;
it excludes dividends. Do not compare its raw dollar price to current Apple prices.

The oil repository identifies EIA as its source. [EIA Brent series](https://www.eia.gov/dnav/pet/hist/RBRTED.htm).
[EIA reuse terms](https://www.eia.gov/about/copyrights_reuse.cfm): public-domain
US government data; acknowledge EIA. DataHub preparation is PDDL licensed.
The primary EIA feed was not independently fetched in this session.

Event references and the date choice are in `events.js`. Event records are
research milestones; no market reaction is claimed for events without prices.
Existing seven oil replay samples are preserved unchanged and have not been
re-certified by this work.

## Historical-practice FX addition (24 October 2026)

`gbp-usd-brexit-source.csv` contains the United Kingdom rows from 25 May–22 July
2016 of [datasets/exchange-rates daily.csv](https://github.com/datasets/exchange-rates/blob/main/data/daily.csv),
retrieved via connected GitHub blob API at SHA
`ed5f4b490edb0ec0585e40d019c73c33fb03948d`. Empty observations are preserved.
The source is Federal Reserve Board H.10 / FRED **DEXUSUK**, inverted by the
[preparation script](https://github.com/datasets/exchange-rates/blob/main/exchange_rates_flow.py)
(SHA `78e23d8eac7081856d425b943b536c01acafb8ea`). Therefore these particular
values are **GBP per USD** (e.g. 0.6805 on 25 May), not USD per GBP, despite the
upstream README's confusing ratio description. We preserve the source's rounded
precision and use USD price × this rate to obtain GBP price.

Dataset preparation is [PDDL](https://github.com/datasets/exchange-rates#license).
The [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm) permits
copying/distribution of Board information in the public domain unless indicated
otherwise, with source attribution. See [FRED terms](https://fred.stlouisfed.org/legal/)
for series-specific rights and attribution. This is Federal Reserve data via
FRED, prepared by datasets/exchange-rates; commercial reuse is permitted for the
public-domain data/PDDL preparation with attribution and no claim of endorsement.
The primary H.10 feed was not independently fetched; this verifies the committed
slice against its secondary source, not a certified FX execution feed.

For paper practice only, Brent and FX are joined on exact shared dates. Both are
historical daily observations with unknown intraday/publication timestamps.
End-of-day replay availability is a disclosed assumption, not a sourced time.
No interpolation, forward fill, contemporary quote claims or synthetic price
observations are introduced. Apple's unresolved rights keep it out of the
practice demo; the existing research example remains unchanged.
