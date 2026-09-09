---
name: aisa
description: "Discover and invoke published AIsa tools with the AIsa CLI (search, schema, quote, call) or unified MCP. Use when the user wants AIsa tools or sign-in, or needs current web, company, or social data AIsa tools can fetch—even if they do not name AIsa. Do not use for OpenClaw Chinese model provider setup (aisa-provider), installing other catalog skills, or work that does not need live AIsa data."
license: MIT
---

# AIsa

Discover published AIsa tools and invoke them. Prefer the CLI in any working terminal (PowerShell counts; Bash is not required). If you are already reading this skill, continue the current task — do not reinstall it or reread setup docs.

Canonical install, only when this skill is not already available:

```sh
npx skills add AIsa-team/agent-skills --skill aisa --agent <current-harness>
```

Optional `--global`. Never `--all`, `--agent '*'`, or `--skill '*'`. Not `aisa skills install`. If the client cannot persist skills, say so and keep going; do not claim a lasting install.

## CLI

If `aisa` is missing, install `@aisa-one/cli` once (`npm install -g @aisa-one/cli`). Do not reinstall or upgrade every task. Verified floor: **0.5.0**. Repair only when setup is actually broken: https://aisa.one/docs/agent-quickstart.md

**Auth.** Reuse existing credentials. If unsigned-in, run `aisa login` — browser OAuth mints and stores a CLI key. Use `aisa login --no-browser` only when this machine cannot finish a local browser redirect; paste the one-time redirect/code back. Do not send the user to copy a key. `AISA_API_KEY` overrides the stored key; if they conflict, explain the source and leave custom setup alone. `aisa whoami` is local only. Search and schema may be anonymous — they are not proof of authentication. Prove CLI auth with `aisa balance`. Never print credentials. Failed login → retry `aisa login`. No credit → top up, not “missing key”.

**Invoke.** `search` → `schema` when `has_full_schema` is false → `quote` → `call` inside authorized scope and spend. Take tool IDs and arguments from returned search/schema. Do not invent IDs, substitute `aisa api list`, or compute prices yourself.

`quote` and `call` share credentials and this JSON shape. `--input` is inline JSON (no file required):

```sh
aisa search "company facts" --json
aisa schema get_financial_company_facts --json
aisa quote --input '{"calls":[{"call_id":"c1","tool":"get_financial_company_facts","arguments":{"ticker":"AAPL"}}]}' --json
aisa call --input '{"calls":[{"call_id":"c1","tool":"get_financial_company_facts","arguments":{"ticker":"AAPL"}}]}' --json
```

`get_financial_company_facts` / `ticker` is the CLI-documented published example, not a default tool. Replace IDs and arguments with what search/schema actually returned.

Quote does not execute and is not approval to execute. A missing, failed, or partial quote is not free and is not a full-batch total. Estimated cost is not a cap; `may_exceed_estimate` and missing amounts are not zero. Search `price` is catalog metadata, not the charge. The CLI does not enforce quote-before-call — you must. Do not execute unquoted, unapproved, or out-of-scope calls; do not silently retry or expand the batch. Re-quote if tools, arguments, or scope change. Reuse a still-valid authorization; do not invent confirmation loops for search, schema, or install. Credentials or a data request are not spending approval. Flags: `aisa <cmd> --help` or `aisa manifest <cmd>`. Prefer `--json` when reading schemas, quotes, or results.

## No command execution

If you cannot run commands (not merely “no Bash”), connect native remote **Streamable HTTP** MCP with **OAuth** at `https://tools.aisa.one/mcp`. Map `search` → `AISA_SEARCH_TOOL`, `schema` → `AISA_BATCH_GET_SCHEMA`, `quote` → `AISA_BATCH_QUOTE`, `call` → `AISA_BATCH_USE`. The client owns browser sign-in and tokens — no manual key. Search/schema success is not proof of OAuth. If you are already reading this skill, continue over MCP; do not require a shell or `npx`. Reuse an existing unified MCP. Do not install both transports or overwrite default models. Do not treat domain MCP or `aisa connect`’s default web-search server as this Router. Setup details: https://aisa.one/docs/agent-quickstart.md

## License

MIT — see [LICENSE](../LICENSE).
