---
name: brand-360
description: 'One-command "digital X-ray" of any company from just a name + domain. Chains four AIsa APIs concurrently into a single structured report: Apollo firmographics (industry, size, founded, HQ, LinkedIn), DataForSEO Google SERP dominance for the company''s category (who ranks, and whether the company owns its own results), Scrape Creators Reddit sentiment (real praise/complaints), and — the flagship — an Oxylabs AI Search GEO brand-check that reports whether the company is mentioned and cited in ChatGPT''s answer for "best <category> brands 2026" and which competitor domains ARE cited. Ends with a mechanical KEY INSIGHT that surfaces the AI-visibility gap. Use for competitive intelligence, sales-pitch prep, brand digital audits, and AI-search (GEO/AEO) visibility checks.'
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3 (stdlib only) and AISA_API_KEY. The four calls run concurrently; total runtime is bounded by the GEO/AI-search call (chatgpt/gemini/perplexity ~40-60s). Each section degrades gracefully if its call fails.
metadata:
  aisa:
    emoji: 🩺
    homepage: https://aisa.one
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---

# AIsa Brand 360 🩺

**Profile any company from just a name + domain — firmographics, search dominance, social sentiment, and AI-search visibility in one report. Powered by AIsa.**

Brand 360 is a *composite* skill: a single command fires **four** AIsa APIs concurrently and merges them into one demo-worthy "company digital X-ray". It is built for the moment an agent needs to profile a prospect or competitor fast — and its flagship output is the **AI-visibility gap**: whether the company shows up in ChatGPT's answer for its own category, or whether competitors own that answer instead.

## Setup

This skill requires the `AISA_API_KEY` environment variable (get one at [aisa.one](https://aisa.one)):

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit the key. Python 3 standard library only — no `pip install`.

## Usage

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/brand-360/scripts/brand360_client.py \
  --company "Midea" --domain midea.com --category "air conditioner"
```

This runs, concurrently:

1. **Firmographics** — Apollo `organizations/enrich` by domain → name, industry, employees, founded, HQ, LinkedIn, short about.
2. **Search dominance** — DataForSEO `serp/google/organic/live/advanced` for `"<company> <category>"` → top ~10 (rank, title, domain) with the company's own results flagged vs competitors/marketplaces.
3. **Social sentiment** — Scrape Creators `reddit/search` for the company name → top ~5 posts (title, subreddit, upvotes, comments, snippet) — real praise/complaints.
4. **AI visibility (GEO)** — Oxylabs AI Search brand-check: query `"best <category> brands 2026"` on the chosen engine → whether the company is **mentioned** and **cited**, plus the competitor domains that ARE cited. *This is the flagship insight.*

The report ends with a **KEY INSIGHT** block that mechanically highlights the most sellable finding, especially the AI-visibility gap.

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--company` / `-c` | Yes | — | Company / brand name (used for SERP, Reddit, and mention/citation matching) |
| `--domain` / `-d` | Yes | — | Company primary domain, e.g. `midea.com` (used for Apollo enrichment and own-result detection) |
| `--category` | Yes | — | Product category — drives the SERP query `"<company> <category>"` and the GEO query `"best <category> brands 2026"` |
| `--engine` / `-e` | No | `chatgpt` | AI engine for the GEO check: `chatgpt`, `gemini`, `perplexity`, `google_search`, `google_ai_mode` |
| `--serp-depth` | No | `10` | Number of organic SERP results to inspect |
| `--reddit-limit` | No | `5` | Number of Reddit posts to show |

### Example

```bash
# Full X-ray of a traditional manufacturer, GEO check on ChatGPT
python3 ${CLAUDE_PLUGIN_ROOT}/skills/brand-360/scripts/brand360_client.py \
  --company "Haier" --domain haier.com --category "refrigerator" --engine chatgpt

# Faster GEO check using Google AI Overviews instead of ChatGPT
python3 ${CLAUDE_PLUGIN_ROOT}/skills/brand-360/scripts/brand360_client.py \
  -c "Midea" -d midea.com --category "air conditioner" -e google_search
```

## Output

A clean sectioned, plain-text report: a header identifying the company/category/sources, then the four numbered sections (Firmographics, Search Dominance, Social Sentiment, AI Visibility), then a **KEY INSIGHT** block. The AI-visibility section reports `Mentioned`, `Cited`, total sources cited, and the competitor domains the AI cited; the KEY INSIGHT calls out the gap, e.g.:

> ⚠️  Midea is NOT cited in chatgpt's answer for "best air conditioner brands 2026" — competitors (X, Y) ARE. High-value GEO opportunity.

**Graceful degradation:** if any single call fails or times out, that section prints as `(unavailable — <reason>)` and the rest of the report still renders — one failure never kills the report.

## When to Use

Use Brand 360 for:

- **Competitive intelligence** — a fast, structured profile of any competitor from just name + domain.
- **Sales-pitch prep** — walk into a prospect meeting with their firmographics, SEO position, social chatter, and AI-search gap already surfaced.
- **Brand digital audit** — a one-shot health check across four surfaces (firmographics, classic search, social, AI answers).
- **AI-visibility (GEO/AEO) check** — the flagship: is the brand present in AI answers for its own category, or do competitors own that answer?

For a single surface only, use the underlying skills directly: `b2b-lead-search` (Apollo), `competitive-seo` (DataForSEO), `social-listening` (Scrape Creators), or `geo-visibility` (Oxylabs AI Search).

## API Reference

This skill composes these AIsa endpoints (all `POST`/`GET` under `https://api.aisa.one/apis/v1`):

- `POST /apollo/organizations/enrich` — firmographics by domain
- `POST /dataforseo/serp/google/organic/live/advanced` — live Google organic SERP
- `GET  /reddit/search` — Reddit post search (Scrape Creators)
- `POST /oxylabs/ai-search` — AI answer engines + citations (GEO brand-check)

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
