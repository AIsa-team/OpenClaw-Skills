---
name: social-listening
description: 'Monitor public social conversation across Reddit, Instagram, and Pinterest via AIsa Scrape Creators. Search Reddit for a topic, pull a subreddit''s recent posts and community stats, read a public Instagram profile snapshot, and scan Pinterest pins for a theme. Use for social listening, brand/topic monitoring, audience research, and trend discovery.'
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3 and AISA_API_KEY.
metadata:
  aisa:
    emoji: 👂
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

# Social Listening 👂

**Track what people are saying on Reddit, Instagram, and Pinterest. Powered by AIsa (Scrape Creators).**

Search Reddit for a topic, size up a community, read an Instagram profile, or scan Pinterest for a theme — the raw signal for brand monitoring, audience research, and trend discovery.

## Setup

This skill requires the `AISA_API_KEY` environment variable (get one at [aisa.one](https://aisa.one)):

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit the key.

## Usage

```bash
# Search Reddit posts for a topic
python3 ${CLAUDE_PLUGIN_ROOT}/skills/social-listening/scripts/scrapecreators_client.py reddit-search \
  --query "ai agents"

# Public Instagram profile snapshot
python3 ${CLAUDE_PLUGIN_ROOT}/skills/social-listening/scripts/scrapecreators_client.py instagram \
  --handle nasa
```

### Subcommands

| Subcommand | Purpose |
|------------|---------|
| `reddit-search` | Search Reddit posts by keyword |
| `reddit-subreddit` | Recent posts from a specific subreddit |
| `subreddit-stats` | Community size / activity stats for a subreddit |
| `instagram` | Public Instagram profile snapshot (followers, posts, bio) |
| `pinterest` | Search Pinterest pins by theme |

### Arguments

| Argument | Subcommand | Default | Description |
|----------|-----------|---------|-------------|
| `--query` / `-q` | `reddit-search`, `pinterest` | — | Search term |
| `--subreddit` / `-s` | `reddit-subreddit`, `subreddit-stats` | — | Subreddit name (no `r/`) |
| `--handle` / `-u` | `instagram` | — | Instagram username (no `@`) |
| `--sort` | `reddit-search`, `reddit-subreddit` | varies | Sort order |
| `--timeframe` | `reddit-search`, `reddit-subreddit` | varies | Time window |
| `--limit` / `-n` | most | 10 | Max items to print |

### Examples

```bash
# Top posts about a brand this week
python3 ${CLAUDE_PLUGIN_ROOT}/skills/social-listening/scripts/scrapecreators_client.py reddit-search \
  -q "notion ai" --sort top --timeframe week -n 15

# How active is a community?
python3 ${CLAUDE_PLUGIN_ROOT}/skills/social-listening/scripts/scrapecreators_client.py subreddit-stats \
  -s artificial

# Pinterest theme scan
python3 ${CLAUDE_PLUGIN_ROOT}/skills/social-listening/scripts/scrapecreators_client.py pinterest \
  -q "healthy meal prep" -n 15
```

## Output

- **reddit-search / reddit-subreddit** — post title, subreddit, author, upvotes, comment count, a snippet, and the permalink.
- **subreddit-stats** — subscribers, weekly active users, weekly posts, and description.
- **instagram** — name, verified flag, followers, following, post count, category, bio, and link.
- **pinterest** — pin title, description, pinner, and URL.

## When to Use

Use for **social listening / brand monitoring** on Reddit, Instagram, and Pinterest — tracking topics, sizing communities, and profiling accounts. For X/Twitter use the `twitter-*` skills; for YouTube use `youtube-serp`; for influencer email discovery use `kol-creator-discovery`. Only public data is returned; respect platform terms and privacy.

## API Reference

This skill calls these AIsa Scrape Creators endpoints:

- `GET /apis/v1/reddit/search` — Reddit post search
- `GET /apis/v1/reddit/subreddit` — subreddit recent posts
- `GET /apis/v1/reddit/subreddit/details` — subreddit community stats
- `GET /apis/v1/instagram/profile` — public Instagram profile
- `GET /apis/v1/pinterest/search` — Pinterest pin search

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
