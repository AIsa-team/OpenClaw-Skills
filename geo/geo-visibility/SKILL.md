---
name: geo-visibility
description: 'Check how a brand, product, or topic appears in real AI answer engines — ChatGPT, Gemini, Perplexity, Google AI Overviews, and Google AI Mode — via AIsa Oxylabs AI Search. Returns the AI-generated answer text plus the exact source URLs each engine cites, and can report whether your brand is mentioned and who else is cited. Use for GEO / AEO (Generative Engine Optimization), AI-search visibility audits, and competitor citation tracking.'
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3 and AISA_API_KEY. AI sources (chatgpt/gemini/perplexity) can take 40-60s per call; Google sources are 4-8s.
metadata:
  aisa:
    emoji: 🛰️
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

# GEO Visibility 🛰️

**See whether AI answer engines mention and cite your brand — the "AI-era SEO" (GEO) capability. Powered by AIsa.**

Traditional SEO tracks Google's blue links. But users increasingly get answers from ChatGPT, Gemini, Perplexity, and Google's AI Overviews — where only a handful of sources get cited. This skill sends a **real query** to those engines and returns the AI answer plus the URLs it cites, so you can audit whether your brand shows up and who is winning the citation.

## Setup

This skill requires the `AISA_API_KEY` environment variable (get one at [aisa.one](https://aisa.one)):

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit the key.

## Usage

```bash
# Ask one AI engine and see its answer + cited sources
python3 ${CLAUDE_PLUGIN_ROOT}/skills/geo-visibility/scripts/geo_client.py ask \
  --source google_search --query "best CRM for startups"

# Check whether a brand is mentioned / cited in an engine's answer
python3 ${CLAUDE_PLUGIN_ROOT}/skills/geo-visibility/scripts/geo_client.py brand \
  --brand "Anthropic" --query "leading AI safety research companies"
```

### Subcommands

| Subcommand | Purpose |
|------------|---------|
| `ask` | Query one AI engine and print its answer + all cited sources |
| `brand` | Query an engine and report whether the brand is mentioned / cited, plus the full citation list (competitor visibility) |

### Arguments

| Argument | Applies to | Required | Default | Description |
|----------|-----------|----------|---------|-------------|
| `--query` / `-q` | both | Yes | — | The question a user might ask an AI engine |
| `--brand` / `-b` | `brand` | Yes | — | Brand or product name to look for in the answer/citations |
| `--source` / `-s` | both | No | `google_search` | One of `google_search`, `google_ai_mode`, `chatgpt`, `gemini`, `perplexity` |
| `--geo` | both | No | `United States` | Country-level geo location |

**Sources:** `google_search` = Google AI Overviews, `google_ai_mode` = Google AI Mode. `chatgpt`, `gemini`, and `perplexity` query those AI answer engines directly.

> **Latency:** `chatgpt` / `gemini` / `perplexity` take ~40-60s per call; Google sources return in ~4-8s. Prefer Google sources for fast iteration.

### Examples

```bash
# Google AI Overviews (fast): who does Google cite for a topic?
python3 ${CLAUDE_PLUGIN_ROOT}/skills/geo-visibility/scripts/geo_client.py ask \
  -s google_search -q "best project management software 2026"

# ChatGPT: does Notion appear when users ask about note-taking apps?
python3 ${CLAUDE_PLUGIN_ROOT}/skills/geo-visibility/scripts/geo_client.py brand \
  -b "Notion" -q "best note taking apps" -s chatgpt

# Perplexity in a specific market
python3 ${CLAUDE_PLUGIN_ROOT}/skills/geo-visibility/scripts/geo_client.py ask \
  -s perplexity -q "top fintech companies" --geo "United Kingdom"
```

## Output

- **ask** — the AI answer text (up to ~4000 chars) and a numbered list of every cited source URL with its display name.
- **brand** — a visibility scorecard (`Mentioned in AI answer`, `Cited as a source`, count of your links), your own citations, the full competitor citation list, then the full answer.

## When to Use

Use this skill when the user asks about **AI search visibility**, **GEO / AEO**, whether their (or a competitor's) brand shows up in **ChatGPT / Gemini / Perplexity / Google AI Overviews**, or who gets **cited** for a topic. This is the differentiated "AI-era SEO" audit — for classic blue-link rankings use `competitive-seo` instead.

## API Reference

- [Oxylabs AI Search](https://aisa.one/docs/api-reference) — single passthrough endpoint (`POST /apis/v1/oxylabs/ai-search`) covering all five AI answer engines.

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
