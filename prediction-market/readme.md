# Prediction Market

Get current odds, prices, and market data from prediction markets like Polymarket and Kalshi. Access historical orderbook data, candlestick charts, trade history, wallet positions, and more.

## Features

- **Polymarket**: Search markets, live prices, trade history, orderbooks, candlesticks, wallet positions, P&L
- **Kalshi**: Search markets, live prices, trade history, orderbooks
- **Cross-Platform**: Match equivalent sports markets across Polymarket and Kalshi

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Search Polymarket for election markets
python scripts/prediction_market_client.py polymarket markets --search "election" --status open

# Get current price for a Polymarket token
python scripts/prediction_market_client.py polymarket price <token_id>

# Search Kalshi for Fed rate markets
python scripts/prediction_market_client.py kalshi markets --search "fed rate"

# Get current price for a Kalshi market
python scripts/prediction_market_client.py kalshi price <market_ticker>

# Find matching NBA markets across platforms
python scripts/prediction_market_client.py sports by-date nba --date 2025-03-01
