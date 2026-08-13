# Social Listening 👂

Monitor public social conversation across **Reddit, Instagram, and Pinterest**
via [AIsa](https://aisa.one) (Scrape Creators). Search Reddit for a topic, size
up a community, read an Instagram profile, or scan Pinterest for a theme.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:
**Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**,
**OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others.

Requires Python 3 and `AISA_API_KEY` (get one at [aisa.one](https://aisa.one)).

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Reddit topic search
python3 scripts/scrapecreators_client.py reddit-search --query "ai agents"

# Subreddit recent posts + community stats
python3 scripts/scrapecreators_client.py reddit-subreddit --subreddit artificial
python3 scripts/scrapecreators_client.py subreddit-stats  --subreddit artificial

# Instagram profile snapshot
python3 scripts/scrapecreators_client.py instagram --handle nasa

# Pinterest theme scan
python3 scripts/scrapecreators_client.py pinterest --query "healthy recipes"
```

## Use Cases

- **Brand / topic monitoring** — what is Reddit saying about a product this week.
- **Audience research** — community size and activity before you invest in a channel.
- **Trend discovery** — surface rising themes on Pinterest and Reddit.
- **Account profiling** — quick public Instagram stats for a creator or competitor.

Only public data is returned; respect each platform's terms and user privacy.

## Requirements

- Python 3
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
