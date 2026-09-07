# AIsa API Map for Article SEO + GEO Review

Every endpoint the skill calls, with the request shape the AIsa proxy accepts and the price observed while building the skill. Base URL `https://api.aisa.one`, header `Authorization: Bearer $AISA_API_KEY`.

## DataForSEO (`/apis/v1/dataforseo/...`)

Request body is always a **JSON array with one task object**. The response is HTTP 200 even on failure; success is `status_code == 20000` at the top level and in `tasks[0]`. Cost is in `tasks[0].cost`. Data is in `tasks[0].result`.

| Purpose | Path | Task fields | Result path | Price (observed) |
|---|---|---|---|---|
| Keyword volume / difficulty / intent | `dataforseo_labs/google/keyword_overview/live` | `keywords[]`, `location_code`, `language_code` | `result[0].items[].keyword_info.search_volume`, `.keyword_properties.keyword_difficulty`, `.search_intent_info.main_intent` | $0.012–0.03 |
| Related keywords (`--deep`) | `dataforseo_labs/google/related_keywords/live` | `keyword`, `location_code`, `language_code`, `limit` | `result[0].items[].keyword_data` | $0.012–0.034 |
| Organic SERP + PAA + AI Overview flag | `serp/google/organic/live/advanced` | `keyword`, `location_code`, `language_code`, `depth` | `result[0].items[]` with `type` in `organic`, `people_also_ask`, `featured_snippet`, `ai_overview`, `related_searches`; `result[0].item_types` | $0.012–0.03 |
| Google AI Mode answer | `serp/google/ai_mode/live/advanced` | `keyword`, `location_code`, `language_code` | `result[0].items[0]` (`type: ai_overview`) with `markdown` and `references[]{url, domain, title}` | $0.012 |
| Parse a page's structure | `on_page/content_parsing/live` | `url` | `result[0].items[0].page_content{header, main_topic[], secondary_topic[]}`; each topic has `h_title`, `level`, `primary_content[].text` | $0.012 |
| Domains AI answers cite for a topic | `ai_optimization/llm_mentions/top_domains/live` | `target:[{keyword, match_type}]`, `platform` (`google` or `chat_gpt`), `items_list_limit`, `location_code`, `language_code` (google only) | `result[0].total.sources_domain[]{key, mentions, ai_search_volume}` | **$0.101 per call** (documented max $0.20) |
| ChatGPT answer with citations | `ai_optimization/chat_gpt/llm_responses/live` | `user_prompt` (≤500 chars), `model_name` (e.g. `gpt-5.4-mini`), `web_search: true` | `result[0].items[]`: skip `type: reasoning`; `type: message` → `sections[].text` and `sections[].annotations[]{title, url}` | $0.012–0.055 |
| Perplexity answer with citations | `ai_optimization/perplexity/llm_responses/live` | `user_prompt`, `model_name` (`sonar`, `sonar-pro`, `sonar-reasoning-pro`), `web_search: true`, `web_search_country_iso_code` | same as above | $0.012–0.036 |
| Gemini / Claude (opt-in) | `ai_optimization/{gemini,claude}/llm_responses/live` | `user_prompt`, `model_name`, `web_search: true` | same as above | $0.012–0.055 |
| Backlinks (`--deep`, URL mode) | `backlinks/summary/live` | `target`, `include_subdomains` | `result[0].{rank, backlinks, referring_domains}` | $0.012–0.048 |

Model names for `llm_responses` come from the sibling `.../llm_responses/models` endpoints (free).

## SEMrush (`/apis/v1/semrush/...`)

`GET` with query parameters; responses are **semicolon-delimited text**, first row is the header. Errors are text rows such as `ERROR 50 :: NOTHING FOUND`.

| Purpose | Path | Params | Header row | Price |
|---|---|---|---|---|
| Keyword volume cross-check | `keyword-overview` | `phrase` | `Keyword;Search Volume;CPC;Competition;Number of Results` | $0.003 |
| Competitor domain strength | `domain-overview` | `domain` (no `www.`) | `Database;Domain;Rank;Organic Keywords;Organic Traffic;Organic Cost;Adwords Keywords` | $0.003 |
| Domain authority (URL mode) | `backlinks-overview` | `target` | `ascore;total;domains_num;urls_num;ips_num` | $0.01 |
| Keywords a URL ranks for (`--deep`, URL mode) | `url-organic-keywords` | `url`, `database` | `Keyword;Position;Search Volume;CPC` | $0.09 |
| Question keywords (`--deep`) | `question-keywords` | `phrase`, `database` | `Keyword;Search Volume;CPC` | $0.36 |

Gotcha: `keyword-overview` and `domain-overview` reject a `database` parameter with `{"error":"request does not match the endpoint contract"}`, while `url-organic-keywords` requires it. The client sends `database` and retries without it on that error. Avoid `keyword-difficulty` (billed per row, up to $0.90).

## Oxylabs AI Search (`POST /apis/v1/oxylabs/ai-search`)

Body `{"source": "google_search", "query": "...", "parse": true, "render": "html", "geo_location": "United States"}`. $0.001 per successful result, 4–8 s.

Response: `results[0].content.results.ai_overviews[]` with `answer_text[].fragments[].text` and `references[]{source, url}`. Reference URLs are Google `/goto?url=` redirects, so the skill records the `source` name (a domain or a publisher name) instead.

Through AIsa the realtime endpoint only serves `google_search` and `google_ai_mode`; `chatgpt`, `perplexity` and `gemini` return HTTP 422 "Realtime integration is not supported for LLM sources". Use the DataForSEO `llm_responses` endpoints above for those engines.

## AIsa LLM gateway (`POST /v1/chat/completions`)

OpenAI-compatible. The skill sends `response_format: {"type": "json_object"}` and no `temperature`. Default model `gpt-5.4-mini` (override with `--model` or `AISA_REVIEW_MODEL`); list models with `GET /v1/models`. Used for keyword extraction, content gap + rewrite suggestions, and the executive summary. Guardrail: the system prompt forbids inventing metrics; every suggestion must cite check ids from the evidence.

## Spend accounting

- `--dry-run` prints nominal and documented-maximum totals from the table in `COSTS` inside `scripts/review_article.py`.
- The report's Spend section sums `tasks[0].cost` for DataForSEO calls and counts SEMrush / Oxylabs / LLM calls at nominal price.
- `--cache-dir` stores raw responses keyed by endpoint + payload; cached calls cost $0 and are marked as cache hits.
