---
name: Prediction Market Data
description: "Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades"
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"📈","requires":{"bins":["curl","python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# Cross-Platform Prediction Market Data 📈

**Prediction markets data access for autonomous agents. Powered by AIsa.**

One API key. Full Polymarket and Kalshi intelligence.

## What Can You Do?

### Probability Checks
```text
"What are the odds of [event] happening?"
```

### Market Sentiment
```text
"Research the current market sentiment on the upcoming election."
```

### Trading Analysis
```text
"Analyze historical prices and orderbooks for this market."
```

### Portfolio Tracking
```text
"Track portfolio positions and P&L for wallet address X."
```

### Arbitrage Detection
```text
"Find arbitrage opportunities across Polymarket and Kalshi."
```

## Quick Start

```bash
export AISA_API_KEY="your-key"
```

## Core Capabilities

### Polymarket

#### Markets

```bash
# Find markets on Polymarket
curl -X GET "https://api.aisa.one/apis/v1/polymarket/markets?search=election&status=open" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Fetch the current market price for a market by token_id
curl -X GET "https://api.aisa.one/apis/v1/polymarket/market-price/{token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Activity

```bash
# Fetch activity data for a specific user
curl -X GET "https://api.aisa.one/apis/v1/polymarket/activity?user={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orders?market={market_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific asset
curl -X GET "https://api.aisa.one/apis/v1/polymarket/orderbooks?token_id={token_id}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Candlesticks

```bash
# Fetch historical candlestick data for a market
curl -X GET "https://api.aisa.one/apis/v1/polymarket/candlesticks/{condition_id}?interval=60" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Positions

```bash
# Fetch all Polymarket positions for a proxy wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/positions/wallet/{wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet

```bash
# Fetch wallet information
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet?eoa={wallet_address}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Wallet Profit-and-Loss

```bash
# Fetch realized profit and loss (PnL) for a specific wallet address
curl -X GET "https://api.aisa.one/apis/v1/polymarket/wallet/pnl/{wallet_address}?granularity=day" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Kalshi

#### Markets

```bash
# Find markets on Kalshi
curl -X GET "https://api.aisa.one/apis/v1/kalshi/markets?search=fed%20rate" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Market Price

```bash
# Fetch the current market price for a Kalshi market
curl -X GET "https://api.aisa.one/apis/v1/kalshi/market-price/{market_ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Trade History

```bash
# Fetch historical trade data for Kalshi markets
curl -X GET "https://api.aisa.one/apis/v1/kalshi/trades?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Orderbook History

```bash
# Fetch historical orderbook snapshots for a specific Kalshi market
curl -X GET "https://api.aisa.one/apis/v1/kalshi/orderbooks?ticker={ticker}" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

### Cross-Platform

#### Sports Markets

```bash
# Find equivalent markets across platforms for sports events
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

#### Sports Markets by Date

```bash
# Find equivalent markets across platforms for sports events by date
curl -X GET "https://api.aisa.one/apis/v1/matching-markets/sports/nba?date=2024-03-01" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

## API Endpoints Reference

### Polymarket Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/polymarket/markets` | Find markets | `search`, `status`, `market_slug`, `limit` |
| `/polymarket/market-price/{token_id}` | Get market price | `token_id`, `at_time` |
| `/polymarket/activity` | Get user activity | `user`, `start_time`, `end_time` |
| `/polymarket/orders` | Get trade history | `market_slug`, `token_id`, `user` |
| `/polymarket/orderbooks` | Get orderbook history | `token_id`, `start_time`, `end_time` |
| `/polymarket/candlesticks/{condition_id}` | Get candlestick data | `condition_id`, `start_time`, `end_time`, `interval` |
| `/polymarket/positions/wallet/{wallet_address}` | Get wallet positions | `wallet_address`, `limit` |
| `/polymarket/wallet` | Get wallet info | `eoa` or `proxy`, `with_metrics` |
| `/polymarket/wallet/pnl/{wallet_address}` | Get wallet PnL | `wallet_address`, `granularity` |

### Kalshi Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/kalshi/markets` | Find markets | `search`, `status`, `market_ticker` |
| `/kalshi/market-price/{market_ticker}` | Get market price | `market_ticker`, `at_time` |
| `/kalshi/trades` | Get trade history | `ticker`, `start_time`, `end_time` |
| `/kalshi/orderbooks` | Get orderbook history | `ticker`, `start_time`, `end_time` |

### Cross-Platform Endpoints (GET)

| Endpoint | Description | Key Params |
|----------|-------------|------------|
| `/matching-markets/sports` | Find matching sports markets | `polymarket_market_slug` or `kalshi_event_ticker` |
| `/matching-markets/sports/{sport}` | Find sports markets by date | `sport`, `date` |

## Response Schemas

### Markets Response
Returns markets array:
- `title` (string) - Market question (e.g., "Will Trump nationalize elections?")
- `market_slug` (string) - URL-friendly identifier
- `condition_id` (string) - Blockchain condition ID
- `start_time` / `end_time` (integer) - Unix timestamps
- `completed_time` (integer|null) - Null if still open
- `tags` (array) - Category tags (e.g., ["politics", "us election"])
- `volume_1_week` / `volume_1_month` / `volume_1_year` / `volume_total` (number) - Trading volume in USD
- `side_a` / `side_b` (object) - id and label (typically "Yes"/"No")
- `winning_side` (object|null) - Null if unresolved
- `image` (string) - Market thumbnail URL

### Activity Response
Returns activities array:
- `title` (string) - Market title
- `market_slug` (string) - Market identifier
- `side` (string) - Trade side: BUY, SELL, or MERGE
- `shares` (integer) - Raw share amount
- `shares_normalized` (number) - Human-readable share amount
- `price` (number) - Trade price (0-1, represents probability)
- `timestamp` (integer) - Unix timestamp of the trade
- `user` (string) - Wallet address of the trader
- `tx_hash` (string) - Blockchain transaction hash

## Understanding Odds
- Prices are shown as decimals (0.65 = 65% probability)
- "Yes" price = probability market thinks event will happen
- Higher volume = more confidence/liquidity
- Prices change based on trading activity

## Pricing

| API | Cost |
|-----|------|
| Prediction market read query | $0.01 |

Every response includes `usage.cost` and `usage.credits_remaining`.

## Get Started

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key
3. Add credits (pay-as-you-go)
4. Set environment variable: `export AISA_API_KEY="your-key"`

## Full API Reference

See [API Reference](https://docs.aisa.one/reference/) for complete endpoint documentation.
