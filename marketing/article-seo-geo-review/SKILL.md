---
name: article-seo-geo-review
description: Use this skill when a user wants an article, blog post, landing page draft, or published URL reviewed for SEO and GEO (generative engine optimization, AI search visibility, being cited by AI Overviews, Google AI Mode, ChatGPT, or Perplexity). It runs one pipeline through AIsa APIs — keyword metrics (DataForSEO + SEMrush), live Google SERP and AI Mode, top-ranking competitor pages, content-gap detection, deterministic on-page SEO and GEO checks, AI answer-engine citation checks, LLM rewrite suggestions — and returns a scored Markdown report plus JSON evidence. Trigger phrases include "review this article for SEO", "GEO audit", "will AI cite this", "content gap vs competitors", "SEO scorecard", "/review-article".
license: MIT
compatibility: "Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3.9+ and AISA_API_KEY. Paid API calls; shows a spend estimate first."
metadata:
  short-description: AIsa-powered SEO + GEO article review
  aisa:
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

# Article SEO + GEO Review

Review one article — a local Markdown draft or a published URL — for classic search optimisation (SEO) and generative engine optimisation (GEO: being retrieved, quoted, and cited by AI Overviews, Google AI Mode, ChatGPT, and Perplexity). Every number comes from AIsa APIs; the LLM only interprets. Pipeline:

`Keyword → SERP → Competitor → Content gap → SEO audit → GEO audit → Rewrite suggestions → Scorecard`

Output: a Markdown scorecard (SEO 0-100, GEO 0-100, grade A-F, per-check evidence, prioritised rewrites, spend) and a JSON file with all raw evidence.

## Requirements

Set an AIsa API key:

```bash
export AISA_API_KEY="your-aisa-api-key"
```

The script also reads `AISA_API_KEY=...` from `~/.aisa/credentials`. Never print, log, or commit API keys. If the key is missing, ask the user to set `AISA_API_KEY`.

## Compatibility

Works with any agentskills.io-compatible harness, including Claude Code, Claude, OpenAI Codex, Cursor, Gemini CLI, OpenCode, Goose, OpenClaw, Hermes, and other runtimes that support skill folders.

Requires Python 3.9+ (standard library only) and `AISA_API_KEY`. Get a key at `https://aisa.one`.

## When to Use

Use this skill for requests like:

- "Review this article for SEO before we publish."
- "Will AI Overviews or ChatGPT cite this post? What do I change?"
- "Run a GEO audit on this URL."
- "Compare my draft with the pages ranking for this keyword and list the content gaps."
- "Give me an SEO + GEO scorecard and rewrite suggestions."

Do not use this skill for keyword research from scratch (use `seo-keyword-research`), full technical site audits, backlink audits, or writing the article itself.

## Quick Start

```bash
# 1. Free, offline: deterministic on-page checks + provisional score
python3 {baseDir}/scripts/review_article.py audit draft.md

# 2. Show the paid calls and the spend estimate, no calls made
python3 {baseDir}/scripts/review_article.py review draft.md --dry-run

# 3. After the user approves the estimate: full review
python3 {baseDir}/scripts/review_article.py review draft.md --yes \
  --out review.md --json-out review.json --cache-dir .review-cache

# Published article (adds domain authority and "does any AI engine cite you" checks)
python3 {baseDir}/scripts/review_article.py review https://example.com/blog/post --yes --out review.md
```

The same commands work with `python3 scripts/review_article.py ...` from the skill root.

## Spend approval protocol (required)

AIsa data endpoints are paid. Before any `review`, `keywords`, `serp`, `competitors`, or `geo` run:

1. Run `review <source> --dry-run` and show the user the call table and the **nominal** and **documented maximum** totals.
2. Wait for the user to approve that scope in their own words.
3. Re-run with `--yes`. Without `--yes` the script prints the plan and exits with code 2. `--max-usd` (default 1.00) refuses plans whose documented maximum exceeds it.

Typical spend for a default run is USD 0.10-0.30 (draft) or USD 0.15-0.35 (URL). The report's **Spend** section lists every call with the cost DataForSEO reported. `--cache-dir` stores raw responses so re-runs and re-renders are free.

## Core workflow

### 1. Load the article

- Markdown: frontmatter `title`, `description`, `slug`, `author`, `date`, `robots`, `schema` are read; headings, links, images, lists, statistics, FAQ and TL;DR blocks are extracted. CJK text is word-counted by character and readability is marked n/a.
- URL: `/apis/v1/dataforseo/on_page/content_parsing/live` returns the heading/paragraph structure; a direct fetch adds title, meta description, canonical, robots, JSON-LD types, image alt, author and dates.
- Pass `--site-domain example.com` for drafts so internal links and "is my domain cited" can be evaluated before publishing.

### 2. Keywords

- `--keyword` uses the user's target. Otherwise the AIsa LLM gateway proposes a primary keyword and up to five secondary keywords from the title, headings, and first 300 words (`--no-llm` falls back to a title n-gram heuristic).
- Metrics: DataForSEO `dataforseo_labs/google/keyword_overview/live` (volume, difficulty, intent, CPC) cross-checked with SEMrush `keyword-overview`. `--deep` adds `related_keywords` and SEMrush `question-keywords` (USD 0.36).

### 3. SERP

`serp/google/organic/live/advanced` (depth 10) gives the organic top 10, People-Also-Ask questions, featured snippet, related searches, and whether an AI Overview is shown. `serp/google/ai_mode/live/advanced` returns Google's AI Mode answer with the pages it cites.

### 4. Competitors

The top `--top` (default 5) organic pages are parsed with `on_page/content_parsing/live` (headings, word count) and rated with SEMrush `domain-overview` (rank, organic traffic). The script computes the median word count and the heading terms that recur across competitors but are missing from the article.

### 5. GEO: what AI engines answer and cite

Engines (`--engines`, comma-separated; defaults marked *):

| id | Source | Notes |
|---|---|---|
| `dfs_ai_mode`* | Google AI Mode via DataForSEO | answer + cited URLs |
| `oxy_google_search`* | Google AI Overview via Oxylabs `ai-search` | answer + publisher names |
| `dfs_chatgpt`* | ChatGPT with web search via DataForSEO `llm_responses` | answer + citations |
| `dfs_perplexity`* | Perplexity sonar via DataForSEO `llm_responses` | answer + citations |
| `dfs_llm_mentions`* | DataForSEO `llm_mentions/top_domains` (google + chat_gpt) | which domains AI answers cite most for the topic; ~USD 0.10 per platform |
| `dfs_gemini`, `dfs_claude` | Gemini / Claude with web search | opt-in |
| `oxy_google_ai_mode` | Google AI Mode via Oxylabs | opt-in |

Oxylabs realtime through AIsa only serves Google sources; ChatGPT / Perplexity / Gemini / Claude answers therefore come from DataForSEO. `--fast` skips the LLM-response engines and the executive summary. Engines run in parallel; a failed engine is a data gap, not a crash.

### 6. Deterministic SEO and GEO checks

Every check has an id, a dimension, a weight, pass / warn / fail / n/a, the evidence, and a fix. Thresholds live in `references/scoring.md`; the GEO rubric and its grounding in Google's AI-features guidance live in `references/geo-rubric.md`. Highlights:

- SEO: title 30-60 chars, meta 70-155, one H1, keyword in title / H1 / first 100 words / an H2 / slug, density 0.5-2.5%, word count ≥ 80% of competitor median, PAA coverage ≥ 50%, ≥ 2 external sources, image alt ≥ 90%, Flesch ≥ 50, author, date.
- GEO: direct answer in the first 60 words, a quotable "X is …" definition, TL;DR block, ≥ 2 question-form headings, headings matching PAA, FAQ, ≥ 3 sourced statistics, no uncited figures, first-hand data or experience, sections ≤ 300 words, descriptive headings, schema hint, fresh date, no `nosnippet` / `noindex`, and (URL mode) whether any engine already cites the page.
- `llms.txt` or "AI-specific" markup earns nothing: Google states it does not use them.

### 7. Rewrite suggestions and summary

The LLM receives the article outline, competitor outlines, PAA, engine answers and citations, and the failed checks, and returns up to 12 prioritised suggestions with example rewrites limited to facts already in the evidence. `--no-llm` substitutes the deterministic fixes. Model: `--model` or `AISA_REVIEW_MODEL` (default `gpt-5.4-mini`).

### 8. Scorecard

Dimension score = (pass weight + 0.5 × warn weight) / applicable weight × dimension max. `n/a` checks leave the denominator; a fully n/a dimension (for example *Current AI visibility* for an unpublished draft) is redistributed and noted. Overall = mean of SEO and GEO. Grade: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, else F.

## Commands

| Command | Purpose | Paid calls |
|---|---|---|
| `audit <src>` | On-page SEO + GEO checks and provisional score | none for files; 1 content_parsing for URLs |
| `parse <src>` | Dump the normalised article model | same as audit |
| `review <src>` | Full pipeline and report | yes, gated by `--dry-run` / `--yes` |
| `keywords <src>` | Keyword extraction + metrics | yes |
| `serp --keyword K` | Organic SERP + AI Mode | yes |
| `competitors --keyword K` | Parse and rate top pages | yes |
| `geo --keyword K [--url U]` | Query AI engines; `--url` checks citations | yes |
| `render --from review.json [--rescore]` | Re-render Markdown from saved JSON | none |

Shared flags: `--keyword`, `--site-domain`, `--location-code 2840`, `--language-code en`, `--database us`, `--geo-location "United States"`, `--top 5`, `--engines`, `--fast`, `--deep`, `--model`, `--no-llm`, `--cache-dir`, `--out`, `--json-out`. `review` adds `--dry-run`, `--yes`, `--max-usd`.

## Presenting results

- Lead with the grade and the two totals, then the top three suggestions.
- Quote check ids when explaining a score so the user can map fixes to evidence.
- Separate facts (metrics, citations, SERP) from recommendations (LLM output).
- Repeat the data-gap list; if an engine failed, say so rather than implying the page is not cited.
- For a draft, remind the user that the AI-visibility dimension can only be measured after publishing (or with `--site-domain`).

## Quality rules

- Never invent search volume, difficulty, rankings, or citations; if a stage failed, report the gap.
- Do not run paid stages before the user has seen the dry-run estimate and approved it.
- Do not credit `llms.txt`, keyword stuffing, "AI rewrites", or artificial brand mentions.
- Keep the primary keyword the user gave; propose alternatives separately if the data suggests a better one.
- Keep raw exports private when they contain unpublished drafts or client domains.

## References

- `references/aisa-api-map.md` — every endpoint used, request shape, envelope, price.
- `references/geo-rubric.md` — GEO checks and their rationale.
- `references/scoring.md` — dimensions, weights, thresholds.
- `references/report-template.md` — report sections for agents that narrate `--no-llm` output.
- `assets/sample-article.md` — deliberately imperfect demo draft.

## API Reference

This skill calls the following AIsa endpoints (bearer auth, base `https://api.aisa.one`):

- [Chat completions](https://aisa.one/docs/api-reference/chat/post_chat-completions) — keyword extraction, content gap, rewrite suggestions, summary
- [Oxylabs AI Search](https://aisa.one/docs/api-reference/search/post_oxylabs-ai-search) — Google AI Overview answers and sources
- DataForSEO `/apis/v1/dataforseo/...` — `dataforseo_labs/google/keyword_overview/live`, `related_keywords/live`, `serp/google/organic/live/advanced`, `serp/google/ai_mode/live/advanced`, `on_page/content_parsing/live`, `ai_optimization/llm_mentions/top_domains/live`, `ai_optimization/{chat_gpt,perplexity,gemini,claude}/llm_responses/live`, `backlinks/summary/live`
- SEMrush `/apis/v1/semrush/...` — `keyword-overview`, `domain-overview`, `backlinks-overview`, `url-organic-keywords`, `question-keywords`

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the category root.
