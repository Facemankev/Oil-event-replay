# Historical oil price seed (2006–2026)

These are **daily spot benchmark observations**, not tradeable instrument prices. Imported on 2026-10-27 from the public GitHub datasets/oil-prices repository:
- Brent: https://github.com/datasets/oil-prices/blob/main/data/brent-daily.csv (dataset describes EIA Europe Brent spot price)
- WTI: https://github.com/datasets/oil-prices/blob/main/data/wti-daily.csv (dataset describes EIA Cushing WTI spot price)

The upstream repository identifies the US Energy Information Administration (EIA) as its original source; this import **did not independently reconcile every observation against the primary EIA API**. Verify against primary EIA data as part of issue #10 before treating it as production-quality. Upstream mirror and original-source timestamps may differ.

Fields: `Date` (ISO calendar date), `Price` (USD/barrel spot). The date range selected is 2006-01-01 through 2026-10-27 inclusive. Available observations:
- Brent: **5,231**; first **2006-01-03**, latest **2026-10-20**
- WTI: **5,137**; first **2006-01-03**, latest **2026-10-20**

Different counts and missing dates are retained as provided. **Do not forward-fill or invent missing prices.** These files are static seed snapshots and do not automatically refresh. Prices reflect the source mirror's values as retrieved, not independently verified exchange quotes. Historical spot-price changes cannot be equated with paper-trade profits on futures, ETFs, or CFDs. Preserve source metadata, revision snapshots, and source rights when importing into the planned database.

Related: issue #10 (automated primary-source ingestion and persistent storage).
