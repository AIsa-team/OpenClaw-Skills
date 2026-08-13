---
name: competitive-seo
description: 'Live Google SERP rankings, keyword ideas, and search-volume/CPC/competition data via AIsa DataForSEO. See who ranks for a term (organic results + SERP features), expand a seed keyword into ranked ideas with volume, and pull ad economics for a keyword list. Use for SEO audits, competitor rank tracking, keyword research, content-gap analysis, and PPC planning.'
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3 and AISA_API_KEY.
metadata:
  aisa:
    emoji: 📈
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

# Competitive SEO 📈

**Live Google rankings, keyword ideas, and search economics. Powered by AIsa (DataForSEO).**

See exactly who ranks for a term today, discover the keywords worth targeting with real search volume, and pull CPC + competition so you know what a keyword is worth.

## Setup

This skill requires the `AISA_API_KEY` environment variable (get one at [aisa.one](https://aisa.one)):

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit the key.

## Usage

```bash
# Live Google SERP for a keyword (organic results + SERP features)
python3 ${CLAUDE_PLUGIN_ROOT}/skills/competitive-seo/scripts/dataforseo_client.py serp \
  --keyword "ai agents" --depth 10

# Expand a seed into ranked keyword ideas with volume/CPC
python3 ${CLAUDE_PLUGIN_ROOT}/skills/competitive-seo/scripts/dataforseo_client.py keywords \
  --seed "ai agents" --limit 15

# Search volume / CPC / competition for a specific keyword list
python3 ${CLAUDE_PLUGIN_ROOT}/skills/competitive-seo/scripts/dataforseo_client.py volume \
  --keywords "ai agents,llm,rag pipeline"
```

### Subcommands

| Subcommand | Purpose |
|------------|---------|
| `serp` | Live Google organic SERP (rank, title, URL, domain, snippet) + SERP features |
| `keywords` | Keyword ideas expanded from a seed, with volume / CPC / competition |
| `volume` | Search volume / CPC / competition for an explicit keyword list |

### Arguments

| Argument | Subcommand | Default | Description |
|----------|-----------|---------|-------------|
| `--keyword` / `-k` | `serp` | — | The query to fetch the SERP for |
| `--depth` / `-d` | `serp` | 10 | Number of organic results |
| `--seed` / `-s` | `keywords` | — | Seed keyword to expand |
| `--limit` / `-n` | `keywords` | 15 | Number of keyword ideas |
| `--keywords` / `-k` | `volume` | — | Comma-separated keyword list |
| `--location` | all | `United States` | DataForSEO location name |
| `--language` | all | `English` | DataForSEO language name |

### Examples

```bash
# Who ranks for a competitor term in the UK?
python3 ${CLAUDE_PLUGIN_ROOT}/skills/competitive-seo/scripts/dataforseo_client.py serp \
  -k "project management software" --location "United Kingdom" -d 20

# Build a keyword map around a topic
python3 ${CLAUDE_PLUGIN_ROOT}/skills/competitive-seo/scripts/dataforseo_client.py keywords \
  -s "email marketing" -n 25
```

## Output

- **serp** — numbered organic results (absolute rank, title, URL, domain, snippet) followed by the SERP features present (knowledge graph, videos, related searches, etc.).
- **keywords** / **volume** — an aligned table of keyword, monthly search volume, CPC (USD), and competition index (0-1).

## When to Use

Use for **classic search-engine SEO**: rank tracking, keyword research, content-gap analysis, and PPC/CPC planning. For **AI-answer-engine** visibility (ChatGPT / Gemini / Perplexity / Google AI Overviews) use the `geo-visibility` skill instead.

## API Reference

This skill calls these AIsa DataForSEO endpoints:

- `POST /apis/v1/dataforseo/serp/google/organic/live/advanced` — live Google organic SERP
- `POST /apis/v1/dataforseo/dataforseo_labs/google/keyword_ideas/live` — keyword ideas from a seed
- `POST /apis/v1/dataforseo/keywords_data/google_ads/search_volume/live` — search volume / CPC / competition

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
