# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working
with code in this repository.

## What this repo is

A catalog of **agent skills** for the AIsa platform (https://aisa.one).
Top-level directories are categories, and every immediate child is a
self-contained skill:

- `platform/` — generic AIsa CLI/MCP Skill
- `financial/` — market data, stock research, portfolios, prediction markets
- `search-research/` — web, academic, Tavily, Perplexity, recent research
- `social-media/` — Twitter/X and YouTube workflows
- `ai-models/` — provider setup and LLM routing
- `marketing/` — SEO and creator discovery
- `creative/` — image and video generation

Skills are consumed by any [agentskills.io](https://agentskills.io)-
compatible harness (Claude Code, Claude, OpenCode, Cursor, Codex,
Gemini CLI, OpenClaw, Hermes, Goose, and others). This repo is *not*
an application, but it has a catalog quality gate under `.github/scripts/`
that validates every source and exported Skill package.

## Authoring reference

`SKILL_AUTHORING.md` at the repo root is the **authoritative SOP** for
composing and maintaining skills. When making any change to a skill's
`SKILL.md`, `README.md`, or frontmatter, read that first. This file
(CLAUDE.md) only covers the runtime and editing invariants Claude Code
needs to know; `SKILL_AUTHORING.md` covers the format, validation, and
conventions.

## Skill anatomy

Every skill directory contains:

- **`SKILL.md`** — the required agent-facing contract. Frontmatter requires
  `name` and `description`; `license`, `compatibility`, `metadata`, and
  `allowed-tools` are optional specification fields. The Markdown body has no
  mandatory heading template.
- **`README.md`** — optional human-facing overview for GitHub visitors. Keep it
  concise and avoid duplicating instructions that can drift from `SKILL.md`.
- **`scripts/*.py`, `scripts/*.sh`** — optional executable helpers. Prefer
  self-contained scripts, but third-party dependencies are allowed when the
  Skill clearly documents how to install or invoke them.
- **`references/`** — extra prose files linked from `SKILL.md` when a
  workflow is too large to inline (e.g. `social-media/twitter-autopilot/references/`
  for OAuth-gated post/engage flows).

Use Skill-root-relative resource references such as `scripts/client.py` and
`references/REFERENCE.md`, as recommended by the Agent Skills specification.
A Harness-specific placeholder such as `{baseDir}` may be included for a
verified integration, but do not assume every client substitutes it.

## API surface

All clients hit `https://api.aisa.one` and authenticate with
`Authorization: Bearer $AISA_API_KEY`. Two base paths coexist:

- `/apis/v1/...` — the main AIsa REST surface (financial, twitter,
  polymarket, kalshi, youtube, search, perplexity, etc.)
- `/v1/...` — OpenAI-compatible surface (chat completions, models) used
  by `last30days` for planner/reranker/fun-scorer LLM calls, and
  `/v1/models/{model}:generateContent` for the Gemini passthrough used
  by `media-gen`.

## Documentation

All doc links use **`aisa.one/docs/...`** (never `docs.aisa.one` or
`aisa.mintlify.app`, which are legacy hosts). Canonical targets:

- `https://aisa.one/docs` — landing
- `https://aisa.one/docs/api-reference` — endpoint catalog
- `https://aisa.one/docs/api-reference/<category>/<slug>` — specific endpoint
- `https://aisa.one/docs/guides/models` — model catalog (read by
  `last30days`' interactive setup)
- `https://aisa.one/docs/llms.txt` — docs index for LLMs

## Conventions to preserve when editing

- Keep `SKILL.md` frontmatter spec-compliant. Required fields are `name`
  (matches directory, lowercase+hyphens) and `description`. Other fields are
  optional and should be added only when useful.
- Preserve vendor metadata that existing consumers use, but do not require a
  single metadata shape for every Skill.
- Keep CLI subcommand surfaces stable (e.g.
  `market_client.py stock prices ...`); `SKILL.md` examples are the
  spec and must stay in sync with `scripts/*.py`.
- When an endpoint has narrower coverage than siblings (e.g.
  `/financial/earnings/press-releases`), document the gotcha inline
  in `SKILL.md` and, if there's a supported-tickers list, keep it in a
  sibling `.md` file (see `financial/marketpulse/earnings-press-releases-tickers.md`).
- Async task endpoints (video generation, OAuth) poll via a task-id GET —
  follow the pattern in `creative/media-gen/scripts/media_gen_client.py` rather
  than reinventing.
- When a Harness integration is actually verified, update only the Skills whose
  compatibility claims or vendor metadata are affected. Do not add a universal
  roster or a fixed body section to unrelated Skills.

## Running a skill locally

```bash
export AISA_API_KEY="..."
python3 <category>/<skill>/scripts/<client>.py <subcommand> [--flags]
```

`last30days` is the exception — it's a bash-wrapped Python skill:

```bash
export AISA_API_KEY="..."
bash search-research/last30days/scripts/run-last30days.sh setup      # first-run
bash search-research/last30days/scripts/run-last30days.sh "<topic>"
```

Run the catalog quality gate before committing any Skill change:

```bash
uv --no-config venv --python python3.11 .venv
uv --no-config pip sync --python .venv/bin/python --require-hashes \
  --only-binary :all: .github/quality-gate-requirements.txt
.venv/bin/python .github/scripts/catalog_quality.py --changed-from origin/main
```

This validates repository-wide structure, credentials, symlinks, and category
exports, then applies schema, link, reference, and syntax checks only to files
changed from `origin/main`. Use `--all` when intentionally cleaning historical
catalog issues. For behavior changes, also run the affected client against the
live API with a real key. Skill removals remain normal Git changes and require
explicit reviewer approval; there is no separate retirement database.
