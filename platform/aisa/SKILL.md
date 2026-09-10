---
name: aisa
description: "Discover and invoke published AIsa tools with the AIsa CLI (search, schema, quote, call) or unified MCP. Use when the user wants AIsa tools or sign-in, or needs current web, company, or social data AIsa tools can fetch—even if they do not name AIsa. Do not use for OpenClaw Chinese model provider setup (aisa-provider), installing other catalog skills, or work that does not need live AIsa data."
license: MIT
---

# AIsa

If you are already reading this skill, continue the current task. Do not reinstall it, reread setup docs, or relogin a working connection.

If the user named another tool, or a dedicated local tool already covers the job, do not force AIsa.

First-time install and connect: https://aisa.one/docs/agent-quickstart.md

## Reuse

Reuse a working official `aisa` skill, `@aisa-one/cli` **0.5.0 or later**, stored CLI credentials, or a unified MCP session. Prefer the CLI in any working terminal (PowerShell counts; Bash is not required). `AISA_API_KEY` overrides the stored key; if they conflict, explain the sources and leave custom setup alone. Never print credentials. `aisa whoami` is local only. Search and schema may be anonymous — they are not auth proof. Prove CLI auth with `aisa balance`. When authentication is needed, read `aisa login --help` and follow it: relay the actual URL or input the CLI asks for through this current process until login finishes. No credit → top up, not “missing key”.

## Workflow

`search` → `schema` when `has_full_schema` is false → `quote` → `call` inside authorized scope and spend. `quote` and `call` share the saved credentials and the same `calls` JSON shape. Take tool IDs and arguments from search/schema. Do not invent IDs or prices. Runtime help, schema, and quote are authoritative. `--input` is inline JSON:

```sh
aisa search --input '{"query":"<user goal>"}' --json
aisa quote --input '{"calls":[{"call_id":"c1","tool":"<name from search>","arguments":{}}]}' --json
```

Quote does not execute and is not approval to execute. A missing, failed, or partial quote is not free and is not a full-batch total or cap. Estimated cost is not a cap. Setup is not paid execution permission. Reuse a still-valid explicit authorization; do not invent confirmation loops for search, schema, or install. Re-quote if tools, arguments, or scope change. Do not silently retry or expand the batch.

## MCP fallback

If you cannot run commands, or the user explicitly prefers MCP, use native remote Streamable HTTP MCP with OAuth at `https://tools.aisa.one/mcp`. The client owns browser sign-in and tokens. Do not require `npx`. Do not treat domain MCP or `aisa connect`’s default web-search server as this router. Discovery or a 401 is not a protected call.

| MCP tool | CLI command |
| --- | --- |
| `AISA_SEARCH_TOOL` | `aisa search` |
| `AISA_BATCH_GET_SCHEMA` | `aisa schema` |
| `AISA_BATCH_QUOTE` | `aisa quote` |
| `AISA_BATCH_USE` | `aisa call` |

## License

MIT — see [LICENSE](LICENSE).
