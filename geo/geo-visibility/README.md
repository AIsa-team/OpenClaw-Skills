# GEO Visibility 🛰️

Check how a brand, product, or topic appears across real AI answer engines —
**ChatGPT, Gemini, Perplexity, Google AI Overviews, and Google AI Mode** — and
see exactly which source URLs each engine cites. This is the "AI-era SEO"
(GEO / AEO) capability: as users move from blue links to AI answers, you need
to know whether *you* are in the answer and who is being cited.

Powered by [AIsa](https://aisa.one) via the Oxylabs AI Search endpoint.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:
**Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**,
**OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others.

Requires Python 3 and `AISA_API_KEY` (get one at [aisa.one](https://aisa.one)).

## Quick Start

```bash
export AISA_API_KEY="your-key"

# What does Google's AI Overview say, and who does it cite? (fast, ~4-8s)
python3 scripts/geo_client.py ask --source google_search \
  --query "leading AI safety research companies"

# Is my brand mentioned / cited in the answer?
python3 scripts/geo_client.py brand --brand "Anthropic" \
  --query "leading AI safety research companies"
```

## Sources

| `--source`        | Engine                          | Typical latency |
|-------------------|---------------------------------|-----------------|
| `google_search`   | Google AI Overviews             | 4-8s            |
| `google_ai_mode`  | Google AI Mode                  | 4-8s            |
| `chatgpt`         | ChatGPT (web-connected)         | 40-60s          |
| `gemini`          | Gemini                          | 40-60s          |
| `perplexity`      | Perplexity                      | 40-60s          |

## Use Cases

- **GEO / AEO audit** — track your AI-answer share of voice over time.
- **Competitor citation tracking** — see which competitor domains AI engines trust.
- **Content gap analysis** — the cited URLs show what content is winning the answer.
- **Market variation** — pass `--geo "United Kingdom"` etc. to compare regions.

## Requirements

- Python 3
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
