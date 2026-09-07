# Article SEO + GEO Review

**AIsa-powered SEO and GEO review for one article, in one command.**

Give the skill a Markdown draft or a published URL. It measures the target keyword with DataForSEO and SEMrush, pulls the live Google SERP and Google AI Mode answer, parses the top-ranking competitor pages, asks ChatGPT, Perplexity and Google AI Overview what they answer and whom they cite, runs deterministic on-page SEO and GEO checks, and returns a scored Markdown report with prioritised rewrite suggestions plus a JSON evidence file.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.

Requires Python 3.9+ and `AISA_API_KEY` (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Review a draft before publishing

```text
"Review draft.md for SEO and tell me whether AI Overviews would cite it."
```

### Audit a published article

```text
"Run an SEO + GEO review on https://example.com/blog/post and show me the scorecard."
```

### Find the content gap

```text
"Compare my article with the pages ranking for 'generative engine optimization' and list what they cover that I don't."
```

### Get rewrite suggestions

```text
"Give me the top rewrite suggestions to make this post citable by ChatGPT and Perplexity."
```

## Quick Start

```bash
export AISA_API_KEY="your-aisa-api-key"

# free offline checks
python3 scripts/review_article.py audit assets/sample-article.md

# see the paid calls first, then run with --yes
python3 scripts/review_article.py review assets/sample-article.md --dry-run
python3 scripts/review_article.py review assets/sample-article.md --yes \
  --out review.md --json-out review.json --cache-dir .review-cache
```

## Inputs and Outputs

- **Input:** one Markdown file or URL, optional primary keyword, market (location / language / SEMrush database), competitor count, AI engines to query.
- **Output:** a Markdown report (scorecard, keywords, SERP snapshot, competitor comparison, SEO and GEO check tables, AI engine visibility, prioritised rewrites, spend, data gaps) and a JSON file with every raw metric and citation.

## When to use / When NOT to use

**Use when:**
- You want to know how an article will perform in Google search and in AI answers before or after publishing.
- You need evidence-backed rewrite suggestions rather than generic SEO tips.

**Do NOT use when:**
- You need keyword research from scratch (see `seo-keyword-research`), a technical site audit, or a backlink audit.
- You want the article written for you; this skill reviews, it does not draft.

## Requirements

- Python 3.9+
- `AISA_API_KEY`

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.

## License

MIT — see [LICENSE](../LICENSE) at the category root.
