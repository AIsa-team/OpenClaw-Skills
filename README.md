# AIsa Agent Skills

Production-ready skills for autonomous agents, compatible with any
[agentskills.io](https://agentskills.io) harness: Claude Code, Claude,
OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes,
and others that implement the [Agent Skills specification](https://agentskills.io/specification).

Skills are grouped by business domain. Each skill directory remains a
self-contained bundle with a `SKILL.md`, optional human-facing `README.md`,
and supporting scripts. One `AISA_API_KEY` covers AIsa-powered skills.
The generic AIsa Skill lives at the repository root (`aisa/`), not in a
domain category.

## General Skill

| Skill | Description |
|---|---|
| [aisa](./aisa/) | Discover and invoke published AIsa tools with the AIsa CLI (search, schema, quote, call) or unified MCP. Use when the user wants AIsa tools or sign-in, or needs current web, company, or social data AIsa tools can fetch—even if they do not name AIsa. |

The default installer entry is this Skill:

```sh
npx skills add AIsa-team/agent-skills --skill aisa --agent codex
```

Vercel `skills@1.5.25` stops after the root `aisa` Skill (`Found 1 skill`). Domain Skills in this aggregate repo need `--full-depth`, for example:

```sh
npx skills add AIsa-team/agent-skills --full-depth --skill market --agent codex
```

Or install from an existing category export. Do not flatten or duplicate Skills to change shallow discovery.

## Catalog

| Category | Skills | Description |
|---|---:|---|
| [Financial & Markets](./financial/) | 15 | Market data, stock research, portfolio tracking, prediction markets, and financial forecasting. |
| [Search & Research](./search-research/) | 12 | Web, academic, Tavily, Perplexity, and recent multi-source research workflows. |
| [Social Media](./social-media/) | 9 | Twitter/X intelligence and engagement plus YouTube discovery and SERP research. |
| [AI Models](./ai-models/) | 3 | AIsa provider setup and unified model routing for Chinese and global LLMs. |
| [Marketing](./marketing/) | 3 | SEO research, article SEO + GEO review, and creator/KOL discovery workflows. |
| [Creative](./creative/) | 1 | Image and video generation workflows. |

## Skills

### [Financial & Markets](./financial/)

| Skill | Description |
|---|---|
| [market](./financial/market/) | Query real-time and historical financial data across equities and crypto—prices, market moves, metrics, and trends for analysis, alerts, and reporting. Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows. |
| [marketpulse](./financial/marketpulse/) | Query real-time and historical financial data for equities—prices, news, financial statements, metrics, analyst estimates, insider and institutional activity, SEC filings, earnings press releases, segmented revenues, stock screening, and macro interest rates. |
| [crypto-market-data](./financial/crypto-market-data/) | Query real-time and historical cryptocurrency market data via CoinGecko — simple prices, coin details, historical charts, OHLC candles, token prices by contract address, market-cap rankings, exchange data and tickers, categories, trending searches, and crypto news. Use for crypto research, price tracking, on-chain token lookup, portfolio analysis, and market-cap screening. |
| [us-stock-analyst](./financial/us-stock-analyst/) | Professional US stock analysis with financial data, news, social sentiment, and multi-model AI. Comprehensive reports at $0.02-0.10 per analysis. Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows. |
| [stock-analysis](./financial/stock-analysis/) | Analyze stocks and cryptocurrencies with 8-dimension scoring via AIsa API. Provides BUY/HOLD/SELL signals with confidence levels, entry/target/stop prices, and risk flags. Supports single or multi-ticker analysis with optional fast mode and JSON output. Use when the user asks to analyze a stock, check a ticker, or compare investments. |
| [stock-dividend](./financial/stock-dividend/) | Analyze read-only dividend metrics for stocks via AIsa API. Provides yield, payout ratio, growth CAGR, safety score, income rating, and Dividend Aristocrat/King status without placing trades, making purchases, or managing brokerage accounts. Use when: the user needs market data, stock analysis, dividend research, or read-only financial data workflows. |
| [stock-hot](./financial/stock-hot/) | Hot Scanner — find the most trending and high-momentum stocks and crypto right now via AIsa API. Top gainers, losers, most active by volume, crypto highlights, news catalysts, and top 5 watchlist picks. Use when the user asks about trending stocks, what's hot, market movers, or momentum plays. |
| [stock-portfolio](./financial/stock-portfolio/) | Manage investment portfolios with live P&L tracking via AIsa API. Create, add, update, remove positions, rename, and show portfolio summary with real-time profit/loss. Use when the user wants to track investments, manage a portfolio, check P&L, or add/remove holdings. |
| [stock-rumors](./financial/stock-rumors/) | Rumor Scanner — find early signals including M&A rumors, insider activity, analyst upgrades/downgrades, social whispers, and SEC/regulatory activity via AIsa API. Ranked by impact score. Use when the user asks about rumors, insider trading, M&A activity, analyst changes, or early market signals. |
| [stock-watchlist](./financial/stock-watchlist/) | Manage a stock/crypto watchlist with price target and stop-loss alerts via AIsa API. Add, remove, list, and check tickers with live price alerts. Use when the user wants to track stocks, set price alerts, manage a watchlist, or check triggered alerts. |
| [prediction-market-data](./financial/prediction-market-data/) | Prediction markets data - Polymarket, Kalshi markets, prices, positions, and trades |
| [prediction-market-data-zh](./financial/prediction-market-data-zh/) | 通过 AIsa API 查询跨平台预测市场数据。支持 Polymarket 和 Kalshi 的市场行情、价格、订单簿、K线、持仓和交易记录。适用场景：查询预测市场赔率、选举博彩、事件概率、市场情绪、Polymarket 价格、Kalshi 价格、体育博彩赔率、钱包盈亏、跨平台市场对比。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows. |
| [prediction-market-arbitrage](./financial/prediction-market-arbitrage/) | Find and analyze arbitrage opportunities across prediction markets like Polymarket and Kalshi. |
| [prediction-market-arbitrage-zh](./financial/prediction-market-arbitrage-zh/) | 通过 AIsa API 发现 Polymarket 和 Kalshi 预测市场的套利机会。扫描体育市场跨平台价差、比较实时赔率、验证订单簿流动性。适用场景：预测市场套利、跨平台价差、体育博彩套利、赔率对比、无风险利润、市场低效。 Use when: the user needs market data, stock analysis, watchlists, or portfolio workflows. |
| [trend-forecast](./financial/trend-forecast/) | Multi-signal trend forecasting for autonomous agents. Combines prediction market odds, Twitter/X social sentiment, news velocity, and stock market data into a unified trend analysis with confidence scoring. Powered by AIsa — one API key, five data streams. |

### [Search & Research](./search-research/)

| Skill | Description |
|---|---|
| [multi-source-search](./search-research/multi-source-search/) | Multi-source intelligent search for agents. Retrieval across web, scholar, Tavily, and Perplexity Sonar models. |
| [multi-search](./search-research/multi-search/) | Parallel multi-source search combining Web, Scholar, Smart, and Tavily results with confidence scoring and AI synthesis. Best for comprehensive research requiring cross-source validation. Use when: the user needs web search, research, source discovery, or content extraction. |
| [smart-search](./search-research/smart-search/) | Intelligent hybrid search combining web and academic sources via AIsa Smart Search endpoint. Best when you need both web and scholarly results. Use when: the user needs web search, research, source discovery, or content extraction. |
| [web-search](./search-research/web-search/) | Search the web using AIsa Scholar Web endpoint. Returns structured web results with titles, URLs, and snippets. Use when: the user needs web search, research, source discovery, or content extraction. |
| [scholar-search](./search-research/scholar-search/) | Search academic papers and scholarly articles via AIsa Scholar endpoint. Supports year range filtering for targeted research. Use when: the user needs web search, research, source discovery, or content extraction. |
| [aisa-tavily](./search-research/aisa-tavily/) | Search the web and extract public page content through AIsa's Tavily-backed API relay. Use when: the user needs web search, source discovery, current news lookup, or URL content extraction. Supports concise result sets, deeper research, and news-focused queries. |
| [tavily-search](./search-research/tavily-search/) | Advanced web search via Tavily through AIsa API. Supports search depth, topic filtering (general/news/finance), time ranges, domain inclusion/exclusion, and LLM-generated answers. Use when: the user needs web search, research, source discovery, or content extraction. |
| [tavily-extract](./search-research/tavily-extract/) | Extract clean, readable content from one or more URLs using Tavily Extract via AIsa API. Useful for reading full articles without visiting the page. Use when: the user needs web search, research, source discovery, or content extraction. |
| [perplexity-search](./search-research/perplexity-search/) | Perplexity Sonar search and answer generation through AIsa. Use when the task is specifically to call Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, or Sonar Deep Research for citation-backed web answers, analytical reasoning, or long-form research reports. |
| [perplexity-research](./search-research/perplexity-research/) | Deep research using Perplexity Sonar models via AIsa API. Provides synthesized answers with citations. Supports 4 models from fast to exhaustive deep research. Use when: the user needs web search, research, source discovery, or content extraction. |
| [last30days](./search-research/last30days/) | Research the last 30 days across Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and grounded web search. Returns a ranked, clustered brief with citations. Use when the task needs recent social evidence, competitor comparisons, launch reactions, trend scans, or person/company profiles. |
| [last30days-zh](./search-research/last30days-zh/) | 聚合最近 30 天的 Reddit、X/Twitter、YouTube、TikTok、Instagram、Hacker News、Polymarket 和 web search 结果. Use when: the user needs recent multi-source research across the last 30 days. |

### [Social Media](./social-media/)

| Skill | Description |
|---|---|
| [twitter-autopilot](./social-media/twitter-autopilot/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts, likes/unlikes tweets, and follows/unfollows users after the user completes OAuth in the browser. Use when the user asks about Twitter/X data, social listening, posting, or interacting with tweets/users without sharing account passwords. |
| [aisa-twitter-api](./social-media/aisa-twitter-api/) | Twitter/X research, monitoring, watchlists, and OAuth-approved posting through AIsa. Use when: the user needs one flagship Twitter skill for trend tracking, competitor monitoring, timeline analysis, or approved posting without sharing passwords. Supports search, watchlists, relay-based reads, and OAuth-gated text or media posting. |
| [aisa-twitter-command-center](./social-media/aisa-twitter-command-center/) | Search X/Twitter profiles, tweets, trends, lists, communities, and Spaces through the AIsa relay, then support approved posting workflows with OAuth. Use when the user asks for Twitter research, monitoring, or posting without sharing passwords. |
| [aisa-twitter-post-engage](./social-media/aisa-twitter-post-engage/) | Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay. Use when the user asks for Twitter/X research, posting, likes, follows, or related workflows without sharing passwords. |
| [twitter-command-center-search-post](./social-media/twitter-command-center-search-post/) | Searches and reads X (Twitter): profiles, timelines, mentions, followers, tweet search, trends, lists, communities, and Spaces. Publishes posts after the user completes OAuth in the browser. Use when the user asks about Twitter/X data, social listening, or posting without sharing account passwords. |
| [x-intelligence-automation](./social-media/x-intelligence-automation/) | Search X/Twitter profiles, tweets, trends, and approved engagement actions through the AIsa relay. Use when the user asks for Twitter/X research, posting, likes, follows, or related workflows without sharing passwords. |
| [youtube-serp](./social-media/youtube-serp/) | YouTube SERP for agents. Search top-ranking videos, channels, and trends for content research and competitor tracking. |
| [youtube-search](./social-media/youtube-search/) | YouTube Search API via AIsa unified endpoint. Search YouTube videos, channels, and playlists with a single AIsa API key — no Google API key or OAuth required. Use this skill when users want to search YouTube content. For other AIsa capabilities (LLM, financial data, Twitter, web search), see the aisa-core skill. Use when: the user needs YouTube search, trend discovery, channel research, or SERP analysis. |
| [aisa-youtube-search](./social-media/aisa-youtube-search/) | Search YouTube videos, channels, and playlists through the AIsa YouTube relay with one API key. Use when the user asks for YouTube discovery, query expansion, or pagination without managing Google credentials. |

### [AI Models](./ai-models/)

| Skill | Description |
|---|---|
| [aisa-provider](./ai-models/aisa-provider/) | Configure AIsa as a first-class model provider for OpenClaw, enabling production access to major Chinese AI models (Qwen, DeepSeek, Kimi K2.5, Doubao) through official partnerships with Alibaba Cloud, BytePlus, and Moonshot. Use this skill when the user wants to set up Chinese AI models, configure AIsa API access, compare pricing between AIsa and other providers (OpenRouter, Bailian), switch between Qwen/DeepSeek/Kimi models, or troubleshoot AIsa provider configuration in OpenClaw. Also use when the user mentions AISA_API_KEY, asks about Chinese LLM pricing, Kimi K2.5 setup, or needs help with Qwen Key Account setup. |
| [llm-router](./ai-models/llm-router/) | Unified LLM Gateway - One API for 70+ AI models. Route to GPT, Claude, Gemini, Qwen, Deepseek, Grok and more with a single API key. Use when: the user needs model routing, provider setup, or Chinese LLM access guidance. |
| [cn-llm](./ai-models/cn-llm/) | China LLM Gateway - Unified interface for Chinese LLMs including Qwen, DeepSeek, GLM, Baichuan. OpenAI compatible, one API Key for all models. Use when: the user needs model routing, provider setup, or Chinese LLM access guidance. |

### [Marketing](./marketing/)

| Skill | Description |
|---|---|
| [seo-keyword-research](./marketing/seo-keyword-research/) | Use this skill when a user asks for SEO keyword research, keyword discovery, search volume analysis, keyword difficulty, search intent mapping, topic clusters, content opportunities, competitor keyword gaps, or a keyword strategy for a domain, URL, product, market, or seed topic. When a website is provided, crawl and interpret the site first, then use AIsa API access to DataForSEO keyword, SERP, trend, Labs, and OnPage endpoints plus AIsa LLM reasoning to find non-brand keyword opportunities. |
| [article-seo-geo-review](./marketing/article-seo-geo-review/) | Use this skill when a user wants an article, blog post, landing page draft, or published URL reviewed for SEO and GEO (generative engine optimization, AI search visibility, being cited by AI Overviews, Google AI Mode, ChatGPT, or Perplexity). It runs one pipeline through AIsa APIs — keyword metrics (DataForSEO + SEMrush), live Google SERP and AI Mode, top-ranking competitor pages, content-gap detection, deterministic on-page SEO and GEO checks, AI answer-engine citation checks, LLM rewrite suggestions — and returns a scored Markdown report plus JSON evidence. Trigger phrases include "review this article for SEO", "GEO audit", "will AI cite this", "content gap vs competitors", "SEO scorecard", "/review-article". |
| [kol-creator-discovery](./marketing/kol-creator-discovery/) | Use this skill when a user needs KOL or influencer research, creator email lookup, similar-creator discovery, outreach-list building, influencer prospecting, or a contact table from TikTok, Instagram, or YouTube profile URLs. It uses AIsa's WaveInflu APIs to find verified creator emails, match similar YouTube or TikTok creators, enrich each recommended profile with contact emails, and return an outreach-ready Markdown table without inventing missing data. |

### [Creative](./creative/)

| Skill | Description |
|---|---|
| [media-gen](./creative/media-gen/) | Generate images and videos with AIsa. Four image models (Google Gemini 3 Pro Image, Alibaba Wan 2.7 image + image-pro, ByteDance Seedream) and four Wan video variants (wan2.6/2.7 × t2v/i2v). One API key; the client routes each model to the correct endpoint automatically. |

## Review Note

This catalog contains 44 skills: 43 domain skills plus 1 general Skill at [`aisa/`](./aisa/).
Subset skills are intentionally retained as separate discovery and entry points.
The merge analysis is in [SKILL_DEDUP_ANALYSIS.md](./SKILL_DEDUP_ANALYSIS.md).
