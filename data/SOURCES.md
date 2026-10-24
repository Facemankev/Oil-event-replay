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
