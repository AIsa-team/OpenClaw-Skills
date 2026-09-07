# GEO Rubric

Generative engine optimisation (GEO) means being retrieved, quoted, and cited by AI answer surfaces: Google AI Overviews and AI Mode, ChatGPT with browsing, Perplexity, Gemini, Claude. The rubric below drives the `geo.*` checks in `scripts/review_article.py`. It is grounded in Google's guidance for succeeding in AI search features (developers.google.com/search/docs/fundamentals/ai-optimization-guide) and in what the queried engines actually cite.

## What Google says works

| Guidance | Check ids |
|---|---|
| Unique, non-commodity content with expert or first-hand perspective | `geo.cite.firsthand`, `geo.cite.stats_with_source` |
| Helpful, people-first content organised in clear sections with descriptive headings | `geo.struct.section_length`, `geo.struct.headings_descriptive`, `geo.struct.lists` |
| Pages must be indexed and eligible to show a snippet | `geo.auth.snippet_controls` (no `nosnippet`, `max-snippet:0`, `noindex`) |
| Include relevant images and video; AI features are multimodal | `seo.images.present`, `seo.images.alt` |
| Structured data helps rich results but is **not** required for AI features | `geo.struct.schema` is a low-weight warn, never a fail for drafts |
| Show authorship and freshness | `geo.auth.author_bio`, `geo.auth.date_fresh` |
| Measure with Search Console's generative AI performance report | reported as a next step, not scored |

## What Google says does not help (never scored positively)

- `llms.txt` or other "special" AI markup — Google Search does not use them.
- Chunking content into tiny fragments — systems understand multi-topic pages.
- Rewriting content in an "AI voice" or repeating exact keyword strings — synonyms and meaning are understood.
- Pursuing inauthentic brand mentions.
- Over-investing in structured data as a ranking lever.

## What answer engines reward (observed from citations)

| Behaviour | Why it matters | Check ids |
|---|---|---|
| A direct answer within the first 60 words | Engines lift the first passage that answers the query | `geo.answer.first60` |
| A quotable definition: "X is …" | Definitions are the most common lifted fragment in AI Overviews and AI Mode | `geo.answer.definition_sentence` |
| A TL;DR or key-takeaways block | Gives engines a self-contained summary to cite | `geo.answer.tldr` |
| Question-form headings that mirror People-Also-Ask and engine fan-out queries | Retrieval matches passages to sub-questions | `geo.q.h2_questions`, `geo.q.paa_match` |
| An FAQ with concise answers | Each Q/A pair is an independently citable passage | `geo.q.faq_block` |
| Specific figures with an in-sentence source | Engines prefer sourced claims and often quote the number and the source together | `geo.cite.stats_with_source`, `geo.cite.uncited_stats` |
| Tables and lists | Structured comparisons are extracted verbatim | `geo.cite.tables_lists` |
| Sections ≤ 300 words | Long sections dilute the passage embedding | `geo.struct.section_length` |
| Being on the domains engines already cite | Citation share is sticky; new pages on cited domains are picked up faster | `geo.vis.cited_any_engine`, `geo.vis.topic_overlap`, `dfs_llm_mentions` engine |

## How the visibility dimension works

- `dfs_ai_mode`, `oxy_google_search`, `dfs_chatgpt`, `dfs_perplexity` return the answer text and the cited URLs or publisher names for the primary keyword (or the article's question-form title).
- `dfs_llm_mentions` returns the domains cited most across Google AI and ChatGPT answers about the topic, with mention counts and AI search volume.
- In URL mode the skill checks whether the article URL or its domain appears among the citations of any engine (`geo.vis.cited_any_engine`). For drafts this check is n/a unless `--site-domain` is given; its weight is redistributed across the other GEO dimensions.
- `geo.vis.topic_overlap` compares the article's vocabulary with the titles of cited and ranking pages; low overlap usually means the article answers a different question than the one engines are answering.
- `geo.vis.ai_overview_present` records whether the query triggers AI answers at all; if not, classic SEO should take priority.

## Interpreting the GEO score

- ≥ 70: the article is structured for citation; focus on distribution and freshness.
- 50–69: fix answer-first, definition, FAQ, and sourcing gaps first — they are cheap and high impact.
- < 50: the article is a narrative, not a reference; restructure around the questions in the SERP and the engine answers.
