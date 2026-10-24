# Sourced beginner practice

Issue #3 extends draft PR #2 on `feature/beginner-paper-trading`. Open
`paper.html` from any static server; GitHub Pages needs no backend for historical
practice. The research dashboard and its original oil replays remain intact.

## What works without setup

Start a £50 **Historical practice** account, choose Brent, enter £5, buy virtually,
then move to the next available day and close. A £1 minimum and fractional units
are supported. Values are GBP: units = GBP stake / (USD price × GBP per USD).
Sells and valuations use that replay day's sourced price and FX, never an arbitrary
last entered value. Price/date/source inputs are gone.

Brent is a daily spot benchmark, **not** shares, a fund, futures, a derivative or
a broker-executable asset. The demo allocates virtual money to a fractional
reference unit (barrel equivalent), with no ownership or delivery. It teaches
price/FX arithmetic, not how to purchase oil. Apple history remains in the
research lab but is deliberately unavailable for practice until reuse rights are
resolved. UK shares, ETFs and gold have no built-in licensed histories.

The demo joins existing Brent observations with actual Federal Reserve FX
observations on the **same date**. Holidays, weekends and missing prices/FX are
skipped, never interpolated or carried forward. Source observations have dates,
not independently verified intraday/publication times. The internal `timestamp`
field in historical snapshots is explicitly an **assumed replay availability**
at 23:59:59 UTC, not a claimed observation timestamp. This is displayed in the UI.
No future observation is shown or used to fill an order; replay cannot rewind.
Known historical outcomes and unknown publication lags mean this cannot establish
unbiased backtest results or attainable execution prices.

Source snapshots, upstream blob hashes, conversion direction and rights:
[data/SOURCES.md](../data/SOURCES.md). Zero fees, spread, slippage, dividends and
interest are explicit simplifications recorded on every order. Full float precision
is retained for accounting/units; money is rounded only for display.

## Provider investigation (checked 24 October 2026)

**Twelve Data is the implemented optional adapter**, not a deployed service.
Its official [pricing](https://twelvedata.com/pricing) lists Basic at 8 API
credits/minute and 800/day, with internal non-display use. Those free credits
**do not authorize public/commercial display**. Paid individual plans are for
personal/internal non-commercial use. [Business pricing](https://twelvedata.com/pricing-business)
includes external display on paid business plans, subject to exchange rights.
[Usage terms](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage)
require a separate redistribution agreement and additional approval outside the US.
The owner must obtain explicit rights for public quotes, simulated portfolios,
**browser-local storage and exported raw quote snapshots**, not merely an API key.
Commercial use is possible under the appropriate business/exchange agreements;
it is not granted by the free tier or by this repository's code.

| Market | Candidate feed / implementation | Availability and rights limits |
| --- | --- | --- |
| US equities | Twelve Data AAPL, MIC XNAS | Adapter implemented; requires display entitlement and fresh intraday data |
| UK equities | Twelve Data ULVR, MIC XLON | Adapter implemented; UK entitlement/approval required; GBP and GBp/GBX normalized explicitly (pence ÷ 100) |
| ETFs | Twelve Data SPY and GLD, MIC ARCX | ETF entitlement required; SPY is an equity fund, GLD a gold exposure fund, neither is an index/spot gold price |
| Oil benchmarks | EIA historical Brent; Twelve Data commodity catalogue is a future candidate | EIA demo only; no current oil symbol guessed; futures/derivatives excluded |
| Gold | GLD ETF adapter; Twelve Data XAU/USD commodity catalogue as reference candidate | ETF and spot are distinct; no speculative spot/derivative trading enabled |
| FX | Twelve Data USD/GBP `/quote`, 1min | Used solely for conversion, requires its own fresh timestamp; no leveraged currency orders |

Twelve Data [API documentation](https://twelvedata.com/docs) describes `/quote`,
`interval`, currency, timestamp and `is_market_open`; the
[official response model](https://github.com/twelvedata/twelvedata-node/blob/master/docs/GetQuote200Response.md)
corroborates those fields. `/quote` defaults to daily bars; we explicitly request
`interval=1min`, `prepost=false`. Quote timestamps represent the opening time of
the selected bar, not a guaranteed tick execution time. Missing fields, unsupported
MIC/currency, provider errors and quota errors all fail closed. The
[commodity catalogue](https://twelvedata.com/exchanges/commodity?group=reference)
confirms commodity coverage; coverage listings alone do not establish entitlement.
Each USD asset refresh makes two quote requests (asset + FX); GBP uses one.
No streaming, automatic retries or polling of the provider is used. Shared quotas
can be exhausted by multiple visitors; the adapter returns unavailable.

**Alpha Vantage was considered, not implemented.** Its
[support page](https://www.alphavantage.co/support/) lists a standard free limit
of 25 requests/day (higher allowances may be approved for verified projects).
[Quote documentation](https://www.alphavantage.co/documentation/) says the default
quote is end-of-day, with real-time/15-minute US data requiring entitlements.
[Commercial market-data policy](https://www.alphavantage.co/realtime_data_policy/)
requires business onboarding; free API access is not public redistribution rights.
It offers equities/FX/commodities but its free default does not meet this app's
current intraday trading policy. Scraped finance sites, anonymous CORS relays,
browser API keys and fabricated prices were excluded.

## Optional deployment — owner action required

Nothing is deployed by this change. Historical practice works immediately;
current mode remains unavailable because `trading/config.js` has an empty URL.

1. Obtain a Twelve Data plan and **written display, storage/export and simulation
   rights**, exchange entitlements (including UK approval if needed), approved
   instrument MICs and actual delay. Confirm the APIs return the documented
   fields for those assets and USD/GBP. Do not enable unlicensed symbols.
2. Use a Cloudflare account and Wrangler (e.g. `npx wrangler`, installed from its
   official npm package). From `proxy/`, set `FRONTEND_ORIGIN` to the exact static
   site origin (scheme + hostname, no path), `CURRENT_ASSETS` to a comma-separated
   subset of `AAPL,SPY,GLD,ULVR`, `QUOTE_DELAY_SECONDS` to the entitled delay
   (0–900), and `DISPLAY_LICENSE_CONFIRMED="yes"` only after rights are confirmed.
   Use one uniform quote delay across enabled assets; otherwise deploy separate
   adapters or extend to per-asset delay settings before enabling them.
3. Set the secret server-side: `npx wrangler secret put TWELVE_DATA_API_KEY`.
   Never put the key in Git, HTML, localStorage, backups or frontend config.
4. Configure the `RATE_LIMITER` binding shown in `wrangler.toml` (Cloudflare Workers
   rate limiting, 6 requests/minute/IP). Review account-wide quota and abuse
   protection before public launch; origin checks are not authentication and can
   be forged by non-browser clients. Use an account budget/usage cap and tighten
   Cloudflare controls to match the contracted quota. No limiter means fail closed.
5. Deploy using `npx wrangler deploy` from `proxy/`. Check the deployed response
   during market hours using the configured Origin header. Set the public HTTPS
   `/quote` URL in `trading/config.js` only after that check. Pages stays static.
   This repository has no workflow that deploys the worker or configures secrets.

The worker accepts only GET `/quote?asset=<allowlisted ID>` from the configured
origin. It cannot proxy arbitrary URLs or accept an upstream API key from a
visitor. No credentials are returned. Upstream failures have sanitized errors;
no provider URLs/keys are logged by the code. CORS is exact-origin, responses are
`no-store`, upstream fetches have timeouts and redirects are refused. Closed,
holiday, unknown-status and unavailable markets disable buys **and closes**.
There are no queued orders that could execute later unnoticed.

Current mode requires asset quote age ≤ entitled delay + 120 seconds, with at
most 900 seconds declared delay, and non-GBP FX age ≤ 120 seconds. Future timestamps
beyond 30 seconds are rejected. Browser clocks therefore need to be correct.
Validation happens on every trade, as well as after retrieval. The UI rechecks
expiry every 10 seconds; old marks are not used when sources fail.

Current practice is intentionally **intraday only**. Without a full corporate
action ledger, a holding whose quote date differs from entry date cannot close;
it needs reconciliation outside this prototype. No split/dividend adjustment is
invented. Reset/export is available. This conservative limit may block around a
UTC date change as well as across market sessions. Multi-day current portfolios,
corporate-action processing and additional currency pairs are future work.

## Persistence and verification

Version 2 accounts store a bounded ledger with full quote snapshot, source
evidence, FX direction/rate/timestamps, units, GBP amounts, replay date, actual
order timestamp, reason and fee/spread/slippage assumptions. Restore recomputes
balances from the ledger, validates transactions, and compares historical
snapshots with committed source observations. Browser-local storage is user
editable, not an immutable audit. Current backups cannot independently certify
old provider responses. Restore is bounded to 5 MB/5,000 transactions and uses
text nodes, never renders user-provided HTML. Old version 1 manual-price data
is retained under its old key and can be exported, but cannot become sourced
trades silently. Storage failures are reported without applying an in-memory trade.

Run:

```sh
node --test --test-isolation=none tests/research.test.cjs tests/trading.test.mjs
python3 tests/browser_test.py
python3 tests/paper_browser_test.py
```

Browser checks require Python Playwright + Chromium at `/usr/bin/chromium`.
They exercise iPad/mobile layouts in Chromium, not actual Safari/WebKit. A physical
iPad/Safari check and an entitled provider integration check are still needed;
provider tests use clearly isolated fixtures, never production demo prices.
