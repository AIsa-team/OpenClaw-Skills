# Review Report Template

`review_article.py review` renders this structure automatically. Use it when you narrate results yourself (for example after `--no-llm`, or when combining several reviews).

## Header

- Article title, source (file or URL), mode
- Primary keyword, market (location, language, SEMrush database)
- Grade and overall score

## Scorecard

| Area | Dimension | Score | Max |
|---|---|---:|---:|

One row per dimension for SEO and GEO, totals in bold. Name any dimension that was not applicable and redistributed.

## Executive summary

≤120 words: the single biggest problem, the quickest win, and whether AI engines currently cite the page.

## Keywords

Primary and secondary keywords with volume, difficulty, intent, CPC, and the SEMrush cross-check. State where the keyword came from (user, LLM, heuristic).

## SERP snapshot

Top-10 table, AI Overview present (and whom it cites), featured snippet owner, People-Also-Ask questions, related searches.

## Competitor comparison

Article length vs competitor median, per-competitor words / headings / domain rank / traffic, and the recurring heading terms missing from the article.

## SEO on-page audit / GEO audit

Check tables: id, status, evidence, fix. Quote check ids when discussing scores.

## AI answer engine visibility

Per engine: status, whether it cites the article or domain, the domains it cites most, overlap with the organic top 10. Include short excerpts of what each engine answered. Add the LLM-mentions top domains as the citation baseline for the topic.

## Prioritised rewrite suggestions

Numbered, each with area (SEO / GEO), the issue, the concrete change, an example rewrite when available, and the check ids it addresses. Then the missing topics list.

## Spend

Estimated total, DataForSEO-reported cost, call counts, cache hits, and the per-call table.

## Data gaps & assumptions

Every failed stage or engine, draft-mode limitations, and assumptions such as market defaults.
