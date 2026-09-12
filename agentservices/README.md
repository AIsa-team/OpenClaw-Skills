# AgentServices ⚡

**Paid APIs for AI agents. Data, search, market intelligence, and services agents pay for via x402.**

[![Website](https://img.shields.io/badge/website-agentservices.to-blue)](https://agentservices.to)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![x402](https://img.shields.io/badge/payments-x402%20%2B%20USDC-orange)](https://x402.org)

## What It Does

AgentServices provides 50+ REST API endpoints that AI agents can call for:

- **Crypto Market Data** — prices, technical indicators, DeFi yields, fear-greed index
- **On-Chain Analytics** — whale tracking, exchange flows, stablecoin flows, correlations
- **Market Intelligence** — token risk scores, crypto signals, sentiment analysis
- **Bundled Intelligence** — portfolio reports, DeFi strategy, market pulse, on-chain overview
- **Web Search & Research** — search, extract, and synthesize in one call
- **AI Inference** — GPT-5.4/5.5 models via proxy
- **Marketing Intelligence** — trends, competitors, content gaps, ad copy

Free tier: prices, trending, news, social, global market, gas. Paid endpoints: $0.01–$0.25 per call.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:

- **Claude Code** and **Claude** (Anthropic)
- **OpenAI Codex**
- **Cursor**
- **Gemini CLI** (Google)
- **OpenCode**, **Goose**, **OpenClaw**, **Hermes**

Requires `curl`. Paid endpoints require an x402-compatible wallet.

## Quick Example

```bash
# Free: Get BTC price
curl -s "https://agentservices.to/v1/prices?symbols=btc"

# Paid ($0.02): Technical indicators
curl -s "https://agentservices.to/v1/indicators/BTC"

# Paid ($0.10): Full portfolio intelligence report
curl -s "https://agentservices.to/v1/portfolio?symbol=BTC"
```

## Payments

AgentServices uses the [x402 protocol](https://x402.org) — HTTP 402 Payment Required.
Payments settle in USDC on Base (Layer 2). No API key, no account, no subscription.

- Free endpoints: just curl
- Paid endpoints: server returns 402 with payment instructions
- Use any x402-compatible wallet (awal CLI, CDP wallet, etc.)

## Links

- **Website**: https://agentservices.to
- **API Docs**: https://agentservices.to/docs
- **MCP Server**: https://agentservices.to/mcp (36 tools)
- **OpenAPI Spec**: https://agentservices.to/openapi.json
- **GitHub**: https://github.com/vbkotecha/aiservices-api
