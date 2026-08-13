# AIsa Brand 360 🩺

A composite "company digital X-ray" via [AIsa](https://aisa.one). One command
fires **four** AIsa APIs concurrently and merges them into a single structured
report — profiling any company from just a name + domain:

1. **Firmographics** (Apollo) — industry, employees, founded, HQ, LinkedIn, about.
2. **Search dominance** (DataForSEO) — Google organic SERP for the company's
   category, with the company's own results flagged vs competitors/marketplaces.
3. **Social sentiment** (Scrape Creators) — top Reddit posts, real praise/complaints.
4. **AI visibility / GEO** (Oxylabs AI Search) — the flagship: is the company
   *mentioned* and *cited* in ChatGPT's answer for "best &lt;category&gt; brands
   2026", and which competitor domains ARE cited?

The report ends with a **KEY INSIGHT** block that mechanically surfaces the most
sellable finding — especially the AI-visibility gap.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:
**Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**,
**OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others.

Requires Python 3 (standard library only) and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## Quick Start

```bash
export AISA_API_KEY="your-key"

python3 scripts/brand360_client.py \
  --company "Midea" --domain midea.com --category "air conditioner"
```

The four calls run concurrently, so total runtime is bounded by the slow
GEO/AI-search call (`chatgpt`/`gemini`/`perplexity` ~40-60s). Use
`--engine google_search` for a faster (~5-10s) GEO check via Google AI Overviews.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--company` / `-c` | Yes | — | Company / brand name |
| `--domain` / `-d` | Yes | — | Primary domain (e.g. `midea.com`) |
| `--category` | Yes | — | Product category (drives SERP + GEO queries) |
| `--engine` / `-e` | No | `chatgpt` | GEO engine: `chatgpt`, `gemini`, `perplexity`, `google_search`, `google_ai_mode` |
| `--serp-depth` | No | `10` | Organic SERP results to inspect |
| `--reddit-limit` | No | `5` | Reddit posts to show |

## Use Cases

- **Competitive intelligence** — fast structured competitor profile from name + domain.
- **Sales-pitch prep** — walk in with firmographics, SEO position, social chatter, and the AI-search gap already surfaced.
- **Brand digital audit** — one-shot health check across four surfaces.
- **AI-visibility (GEO/AEO) check** — is the brand present in AI answers for its own category, or do competitors own it?

Each section degrades gracefully: if one call fails, that section prints as
`(unavailable)` and the rest of the report still renders.

## Requirements

- Python 3 (standard library only — no `pip install`)
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
