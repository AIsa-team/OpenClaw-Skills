# OpenClaw Prediction Market Toolkit 📈⚖️

**A comprehensive toolkit for accessing prediction market data and finding cross-platform arbitrage opportunities for autonomous agents. Powered by AIsa.**

This repository contains skills and Python clients that allow AI agents and developers to interact with prediction markets like **Polymarket** and **Kalshi** using a single, unified API.

## 📁 Included Files

This toolkit provides two main capabilities: **General Market Data** and **Arbitrage Detection**. Each capability comes with an agent-readable `SKILL.md` and a ready-to-use Python client.

### 1. General Market Data
Access markets, prices, orderbooks, trade history, and wallet portfolios across platforms.
- `SKILL.md` — The core OpenClaw skill definition for general prediction market data access.
- `prediction_market_client.py` — A full-featured CLI and Python wrapper for all Polymarket and Kalshi endpoints.

### 2. Arbitrage Detection
Automatically match equivalent events across platforms to detect risk-free price discrepancies.
- `SKILL_ARBITRAGE.md` — A specialized OpenClaw skill focused purely on finding and verifying arbitrage opportunities.
- `arbitrage_finder.py` — An automated Python script that scans for matching markets, compares prices, calculates spreads, and verifies orderbook liquidity.

---

## 🚀 Setup & Authentication

Both the skills and the Python scripts require an AIsa API key.

1. Sign up at [aisa.one](https://aisa.one)
2. Get your API key and add credits (pay-as-you-go).
3. Set the environment variable:

```bash
export AISA_API_KEY="your-key-here"
```

---

## 💻 Using the Python Clients

### General Prediction Market Client (`prediction_market_client.py`)

This script provides comprehensive access to both Polymarket and Kalshi data.

**Polymarket Examples:**
```bash
# Search for open election markets
python prediction_market_client.py polymarket markets --search "election" --status open

# Get current price for a specific token
python prediction_market_client.py polymarket price <token_id>

# Get wallet portfolio and PnL
python prediction_market_client.py polymarket positions <wallet_address>
python prediction_market_client.py polymarket pnl <wallet_address> --granularity day
```

**Kalshi Examples:**
```bash
# Search for Fed rate markets
python prediction_market_client.py kalshi markets --search "fed rate" --status open

# Get orderbook for a market
python prediction_market_client.py kalshi orderbooks --ticker <ticker>
```

### Arbitrage Finder (`arbitrage_finder.py`)

This script automates the 3-step arbitrage workflow: finding matching markets, comparing prices, and verifying liquidity.

**Scan an entire sport for a specific date:**
```bash
# Scan all NBA games on March 30, 2025, showing only spreads > 2% and liquidity > $500
python arbitrage_finder.py scan nba --date 2025-03-30 --min-spread 2.0 --min-liquidity 500
```

**Analyze a specific matched market:**
```bash
# Check a specific event using its Polymarket slug
python arbitrage_finder.py match --polymarket-slug nba-lakers-vs-celtics

# Or using its Kalshi ticker
python arbitrage_finder.py match --kalshi-ticker KXNBA-25-LAL-BOS
```

---

## 🤖 Using the OpenClaw Skills

For autonomous agents, simply load `SKILL.md` into the agent's context. The skills provide exact `curl` commands, ID resolution workflows, and response schemas.

**General ID Lookup Workflow:**
Most endpoints require an ID that must first be fetched from the `/markets` endpoint:
1. **Polymarket `token_id`** — Query `/polymarket/markets` → find `side_a.id` or `side_b.id`
2. **Polymarket `condition_id`** — Query `/polymarket/markets` → find `condition_id`
3. **Kalshi `market_ticker`** — Query `/kalshi/markets` → find `market_ticker`

---

## 💰 Pricing

| API Operation | Cost |
|---------------|------|
| Prediction market read query | $0.01 |

*Note: Every API response includes `usage.cost` and `usage.credits_remaining`.*

## 📚 Documentation

For complete endpoint documentation, visit the [AIsa API Reference](https://docs.aisa.one/reference/).
