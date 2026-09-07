# Scoring Model

Two scores out of 100 (SEO, GEO), an overall score (their mean), and a grade. The check registry lives in `run_checks()` inside `scripts/review_article.py`; this file documents the same weights and thresholds.

## Status rules

- `pass` earns the check's full weight, `warn` earns half, `fail` earns nothing.
- `na` removes the check from the denominator (data unavailable or not applicable to a draft).
- Dimension score = earned weight / applicable weight × dimension max.
- A dimension with no applicable checks is dropped and its max is redistributed proportionally; the report names it.
- Overall = mean of SEO and GEO. Grade: A ≥ 85, B ≥ 70, C ≥ 55, D ≥ 40, else F.

## SEO (100)

| Dimension (max) | Check id | Weight | pass / warn / fail |
|---|---|---:|---|
| Keyword targeting (25) | `seo.kw.title` | 4 | exact phrase in title / ≥50% of tokens / less |
| | `seo.kw.h1` | 4 | exact phrase in H1 / ≥50% / less |
| | `seo.kw.intro100` | 4 | exact phrase in first 100 words / ≥50% / less |
| | `seo.kw.h2` | 3 | an H2/H3 contains the phrase / ≥50% / none |
| | `seo.kw.slug` | 3 | slug covers all tokens / ≥50% / less; n/a without slug |
| | `seo.kw.density` | 3 | 0.5–2.5% / 0.2–4% / outside |
| | `seo.kw.secondary_coverage` | 3 | ≥60% of secondary keywords present / ≥30% / less |
| Metadata & structure (15) | `seo.title.length` | 3 | 30–60 chars / 20–70 / outside |
| | `seo.meta.length` | 3 | 70–155 chars / 40–200 / missing or outside |
| | `seo.h1.single` | 3 | exactly one H1 / none but a title / several |
| | `seo.heading.hierarchy` | 2 | no level skips / skips |
| | `seo.paragraph.length` | 2 | longest ≤150 words / ≤220 / longer |
| Content depth vs SERP (25) | `seo.depth.wordcount` | 6 | ≥0.8× competitor median / ≥0.6× / less |
| | `seo.depth.topic_coverage` | 6 | ≤30% of recurring competitor heading terms missing / ≤60% / more |
| | `seo.depth.paa_coverage` | 5 | ≥50% of PAA questions answered / ≥25% / less |
| | `seo.depth.featured_snippet_format` | 3 | list or definition present when SERP has a snippet / warn |
| Links & media (15) | `seo.links.external` | 4 | ≥2 external domains / 1 / 0 |
| | `seo.links.internal` | 3 | ≥1 internal link / warn |
| | `seo.images.alt` | 4 | ≥90% alt coverage / ≥50% / less; n/a without images |
| | `seo.images.present` | 2 | image or video present / warn |
| Readability & E-E-A-T (20) | `seo.read.flesch` | 4 | Flesch ≥50 / ≥30 / less; n/a for CJK |
| | `seo.eeat.author` | 3 | author present / warn (draft) / fail (URL) |
| | `seo.eeat.date` | 3 | date present / warn (draft) / fail (URL) |
| | `seo.eeat.intro_answers_query` | 3 | first paragraph covers keyword tokens fully / ≥50% / less |

## GEO (100)

| Dimension (max) | Check id | Weight | pass / warn / fail |
|---|---|---:|---|
| Answer-first (20) | `geo.answer.first60` | 10 | keyword fully covered in first 60 words / ≥50% / less |
| | `geo.answer.definition_sentence` | 5 | "keyword is / are / refers to / means …" present / absent |
| | `geo.answer.tldr` | 5 | TL;DR, key takeaways, or quick answer block / absent |
| Question alignment (20) | `geo.q.h2_questions` | 7 | ≥2 question-form H2/H3 / 1 / 0 |
| | `geo.q.paa_match` | 8 | ≥40% of PAA + engine questions matched by a heading / ≥15% / less |
| | `geo.q.faq_block` | 5 | FAQ section / none |
| Citability (20) | `geo.cite.stats_with_source` | 8 | ≥3 sourced figures / ≥1 / 0 |
| | `geo.cite.uncited_stats` | 4 | 0 uncited figures / ≤2 / more |
| | `geo.cite.firsthand` | 5 | first-hand or original-data signals, or a table / none |
| | `geo.cite.tables_lists` | 3 | ≥3 list items or tables / ≥1 / 0 |
| Structure & extractability (15) | `geo.struct.section_length` | 5 | longest section ≤300 words / ≤450 / longer |
| | `geo.struct.lists` | 3 | any list / none |
| | `geo.struct.schema` | 4 | Article / FAQPage / HowTo type declared / warn (draft) / fail (URL) |
| | `geo.struct.headings_descriptive` | 3 | ≥70% of H2/H3 descriptive / ≥40% / less |
| Authority & freshness (10) | `geo.auth.author_bio` | 3 | author / warn (draft) / fail (URL) |
| | `geo.auth.date_fresh` | 3 | ≤365 days / older or unparseable / missing (URL) |
| | `geo.auth.snippet_controls` | 2 | no blocking robots directives / blocked; n/a for drafts without `robots` |
| | `geo.auth.domain_strength` | 2 | authority score ≥20 or ≥50 referring domains / weaker; n/a for drafts |
| Current AI visibility (15) | `geo.vis.cited_any_engine` | 8 | article or domain cited by ≥1 engine / not cited; n/a for drafts without `--site-domain` |
| | `geo.vis.topic_overlap` | 4 | ≥50% of top cited-title terms present / ≥30% / less |
| | `geo.vis.ai_overview_present` | 3 | query triggers AI answers / warn |

## Changing the model

Edit the weights or thresholds in `run_checks()` and mirror them here. `render --from review.json --rescore` recomputes scores from saved checks without new API calls.
