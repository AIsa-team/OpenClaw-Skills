# Competitive SEO 📈

Live Google SERP rankings, keyword ideas, and search-volume / CPC / competition
data via [AIsa](https://aisa.one) (DataForSEO). See who ranks for a term today,
expand a seed keyword into ranked ideas, and pull the ad economics of any
keyword list.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:
**Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**,
**OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others.

Requires Python 3 and `AISA_API_KEY` (get one at [aisa.one](https://aisa.one)).

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Live Google SERP
python3 scripts/dataforseo_client.py serp --keyword "ai agents" --depth 10

# Keyword ideas with volume/CPC
python3 scripts/dataforseo_client.py keywords --seed "ai agents" --limit 15

# Volume / CPC / competition for a keyword list
python3 scripts/dataforseo_client.py volume --keywords "ai agents,llm,rag pipeline"
```

## Use Cases

- **Rank tracking** — see the live top-N organic results for any keyword/market.
- **Keyword research** — expand a seed topic into a ranked idea list with volume.
- **Content-gap analysis** — the SERP shows which domains own a term.
- **PPC planning** — CPC + competition tell you what a keyword costs to buy.

For AI-answer-engine visibility (ChatGPT / Gemini / Perplexity / Google AI
Overviews), use the sibling **geo-visibility** skill.

## Requirements

- Python 3
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
