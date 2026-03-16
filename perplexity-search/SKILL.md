---
name: perplexity-search
description: "Perplexity Sonar search and answer generation through AIsa. Use when the task is specifically to call Perplexity Sonar, Sonar Pro, Sonar Reasoning Pro, or Sonar Deep Research for citation-backed web answers, analytical reasoning, or long-form research reports."
homepage: https://openclaw.ai
metadata: {"openclaw":{"emoji":"🔎","requires":{"bins":["curl","python3"],"env":["AISA_API_KEY"]},"primaryEnv":"AISA_API_KEY"}}
---

# Perplexity-Search

Use this skill when the user specifically wants Perplexity-powered search answers instead of structured scholar/web retrieval.

This skill covers four AIsa endpoints:
- `/perplexity/sonar`
- `/perplexity/sonar-pro`
- `/perplexity/sonar-reasoning-pro`
- `/perplexity/sonar-deep-research`

## Requirements

- Set `AISA_API_KEY`
- Use the bundled client at `{baseDir}/scripts/perplexity_search_client.py`

## Model Selection

- Use `sonar` for fast, lightweight answers with citations
- Use `sonar-pro` for stronger synthesis and comparison tasks
- Use `sonar-reasoning-pro` for analytical or multi-step reasoning questions
- Use `sonar-deep-research` for exhaustive reports; expect slower responses and occasional timeouts

## Python Client

```bash
python3 {baseDir}/scripts/perplexity_search_client.py sonar --query "What changed in AI this week?"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-pro --query "Compare coding agents with citations"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-reasoning-pro --query "Analyze whether vertical AI agents can defend against general copilots"
python3 {baseDir}/scripts/perplexity_search_client.py sonar-deep-research --query "Create a deep research report on AI coding agents in 2026"
```

Add a system message when you want a more specific output format:

```bash
python3 {baseDir}/scripts/perplexity_search_client.py sonar-pro \
  --query "Map the top coding agent products" \
  --system "Respond in markdown with an executive summary first."
```

## Curl Examples

### Sonar

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [
      {"role": "user", "content": "What changed in the AI agent ecosystem this week?"}
    ]
  }'
```

### Sonar Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-pro",
    "messages": [
      {"role": "user", "content": "Compare the top coding agents and cite the key differences."}
    ]
  }'
```

### Sonar Reasoning Pro

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-reasoning-pro" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-reasoning-pro",
    "messages": [
      {"role": "user", "content": "Analyze whether vertical AI agents can defend against general copilots."}
    ]
  }'
```

### Sonar Deep Research

```bash
curl -X POST "https://api.aisa.one/apis/v1/perplexity/sonar-deep-research" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar-deep-research",
    "messages": [
      {"role": "user", "content": "Create a deep research report on AI coding agents in 2026."}
    ]
  }'
```

## Timeout Behavior

- `sonar-deep-research` uses a longer timeout and automatic retries in the bundled client
- If it still times out, narrow the query or retry later
- If the user wants a faster answer, fall back to `sonar-pro` or `sonar-reasoning-pro`

## References

- [Sonar](https://docs.aisa.one/reference/post_perplexity-sonar)
- [Sonar Pro](https://docs.aisa.one/reference/post_perplexity-sonar-pro)
- [Sonar Reasoning Pro](https://docs.aisa.one/reference/post_perplexity-sonar-reasoning-pro)
- [Sonar Deep Research](https://docs.aisa.one/reference/post_perplexity-sonar-deep-research)
