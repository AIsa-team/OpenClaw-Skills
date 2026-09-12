---
name: agentservices
description: >-
  Access 50+ paid data APIs for AI agents — crypto prices, technical indicators,
  DeFi yields, on-chain analytics (whale tracking, exchange flows, stablecoin flows),
  market intelligence (sentiment, trends, competitor analysis, content gaps, ad copy),
  portfolio intelligence, DeFi strategy optimization, market pulse signals, web search
  and extraction, URL metadata, IP geolocation, AI inference (GPT models), fear-greed
  index, and MCP integration. Use when the agent needs real-time financial data, crypto
  market data, on-chain analysis, marketing intelligence, deep research, or AI inference.
  Payments via x402 protocol (USDC on Base). Free endpoints available for prices,
  trending, news, and social data.
license: MIT
compatibility: >-
  Works with any agentskills-compatible harness — Claude Code, Claude, OpenCode, Cursor,
  Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires curl and optionally
  an x402-compatible wallet (awal CLI or CDP wallet) for paid endpoints. Free endpoints
  work with no wallet or API key.
metadata:
  homepage: https://agentservices.to
  emoji: "⚡"
  requires:
    bins: [curl]
    env: []
  primaryEnv: ""
  harnesses: [claude-code, claude, opencode, cursor, codex, gemini-cli, openclaw, hermes, goose]
  x402:
    network: base
    asset: USDC
    payTo: "0x9863aB6242663FCc84c33632741711dB78f8Fd15"
    endpoint: "https://agentservices.to"
---

# AgentServices ⚡

**Paid APIs for AI agents. Data, search, market intelligence, and services agents pay for via x402.**

50+ endpoints covering crypto market data, on-chain analytics, marketing intelligence,
deep research, and AI inference. Free tier for basic data. Paid endpoints use the x402
protocol (USDC on Base) — no API key, no account, just pay-per-request.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness, including:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**
- and any other harness that implements the [Agent Skills specification](https://agentskills.io/specification)

Requires `curl`. Paid endpoints require an x402-compatible wallet (e.g., awal CLI or
any CDP wallet). Free endpoints work with no setup.

## Quick Start

### Free Endpoints (No Payment Required)

```bash
# Crypto prices
curl -s "https://agentservices.to/v1/prices?symbols=btc,eth,sol"

# Fear & Greed Index
curl -s "https://agentservices.to/v1/fear-greed"

# Trending tokens
curl -s "https://agentservices.to/v1/trending"

# Global market data
curl -s "https://agentservices.to/v1/global"

# Gas prices
curl -s "https://agentservices.to/v1/gas"

# News
curl -s "https://agentservices.to/v1/news"

# Social trending
curl -s "https://agentservices.to/v1/social-trending"
```

### Paid Endpoints (x402 Payment Required)

```bash
# Technical indicators ($0.02)
curl -s "https://agentservices.to/v1/indicators/BTC"

# DeFi yields ($0.02)
curl -s "https://agentservices.to/v1/defi-yields"

# On-chain whale tracking ($0.02)
curl -s "https://agentservices.to/v1/whales?symbol=BTC"

# Deep research: search + extract + synthesize ($0.05)
curl -s -X POST "https://agentservices.to/v1/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Bitcoin ETF flows July 2026"}'

# Portfolio intelligence: price + signal + risk + sentiment ($0.10)
curl -s "https://agentservices.to/v1/portfolio?symbol=BTC"

# DeFi strategy report ($0.25)
curl -s "https://agentservices.to/v1/defi-strategy"

# Market pulse: fear-greed + trending + news + whales ($0.05)
curl -s "https://agentservices.to/v1/market-pulse"

# On-chain overview: whales + flows + TVL + correlation ($0.15)
curl -s "https://agentservices.to/v1/onchain-overview"

# AI inference — GPT-5.4 ($0.03)
curl -s -X POST "https://agentservices.to/v1/inference" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-5.4", "messages": [{"role": "user", "content": "Analyze BTC trend"}]}'
```

## Endpoint Categories

| Category | Endpoints | Price Range |
|----------|-----------|-------------|
| **Crypto Prices** | `/v1/prices`, `/v1/trending`, `/v1/global`, `/v1/gas`, `/v1/fear-greed` | Free |
| **News & Social** | `/v1/news`, `/v1/social-trending` | Free |
| **Technical Analysis** | `/v1/indicators/{symbol}` | $0.02 |
| **DeFi Data** | `/v1/defi-yields`, `/v1/defi-tvl`, `/v1/yield-comparison` | $0.02-$0.03 |
| **On-Chain Analytics** | `/v1/whales`, `/v1/exchange-flows`, `/v1/stablecoin-flows`, `/v1/correlation` | $0.02 |
| **Market Intelligence** | `/v1/token-risk`, `/v1/crypto-signals` | $0.03-$0.04 |
| **Bundled Intelligence** | `/v1/research`, `/v1/portfolio`, `/v1/market-pulse`, `/v1/defi-strategy`, `/v1/onchain-overview` | $0.05-$0.25 |
| **Web Search & Extract** | `/v1/search`, `/v1/web-extract`, `/v1/metadata` | $0.01 |
| **AI Inference** | `/v1/inference`, `/v1/complete` | $0.03 |
| **Marketing Intelligence** | `/v1/sentiment`, `/v1/trends`, `/v1/competitors` | $0.03-$0.05 |

Full API documentation: https://agentservices.to/docs

## MCP Integration

AgentServices also provides a Model Context Protocol (MCP) endpoint with 36 tools:

```
MCP URL: https://agentservices.to/mcp
```

Connect from any MCP-compatible client (Claude Desktop, Cursor, Cline, etc.).

## Example Agent Prompts

```text
"What's the current Fear & Greed Index and top trending crypto?"
→ Use /v1/fear-greed (free) + /v1/trending (free)

"Analyze BTC technical indicators and whale activity"
→ Use /v1/indicators/BTC ($0.02) + /v1/whales?symbol=BTC ($0.02)

"Give me a complete BTC portfolio intelligence report"
→ Use /v1/portfolio?symbol=BTC ($0.10)

"Research the latest Bitcoin ETF flow trends"
→ Use /v1/research with query ($0.05)

"What's the best DeFi yield strategy right now?"
→ Use /v1/defi-strategy ($0.25)
```

## Payment Setup

AgentServices uses the x402 protocol for micropayments. To enable paid endpoints:

1. Install awal CLI: `npx awal@latest`
2. Fund with USDC on Base
3. Paid endpoints return HTTP 402 with payment instructions
4. awal handles payment automatically

Or use any x402-compatible wallet/client. No API key required.

## Links

- **Website**: https://agentservices.to
- **API Docs**: https://agentservices.to/docs
- **MCP Endpoint**: https://agentservices.to/mcp
- **x402 Manifest**: https://agentservices.to/.well-known/x402.json
- **OpenAPI Spec**: https://agentservices.to/openapi.json
- **GitHub**: https://github.com/vbkotecha/aiservices-api
