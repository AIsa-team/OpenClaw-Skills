---
name: aisa-similarweb
description: "Use this skill whenever a user or agent needs Similarweb website intelligence through AIsa — monthly visits and engagement for a domain, traffic trend, country/category rank, PPC spend, marketing channels, referrals, ad networks, similar sites, demographics, deduplicated audience, audience interest and overlap, technologies, popular pages, subdomains, keyword competitors, website keywords, SERP players, landing pages, top geographies. It holds no parameters and no prices: it reads the live API contract to build and validate every request, finds the latest data month, quotes each request for free, compares scope variants, gets approval against the user's budget, caps spend with a header, and reports the actual cost. Keywords - similarweb, website traffic, domain traffic, competitor traffic, traffic sources, audience overlap, keyword competitors, aisa, openapi contract, quote, budget."
license: MIT
compatibility: "Works with any agentskills.io-compatible harness (Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose). Requires Python 3 and AISA_API_KEY on an account with the Hive GTM subscription."
metadata:
  short-description: Similarweb through AIsa — contract discovered at runtime, cost quoted before every call
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# AIsa Similarweb 📡

**Similarweb website intelligence for agents — discovered at runtime, spent deliberately. Powered by AIsa.**

This skill holds **no endpoint parameters and no prices**, because both change over time. The agent reads
them from the API instead: parameters from the live contract at `https://aisa.one/docs/openapi/similarweb.json`,
cost from a free quote before each call and the cost header after it. A 20-line version of this protocol for
pasting into any agent is `references/agent-rules.txt`.

## Requirements

```bash
export AISA_API_KEY="sk-aisa-..."
```

- Base URL `https://api.aisa.one/apis/v1/similarweb`; header `Authorization: Bearer $AISA_API_KEY`.
- The key's account needs the **Go-to-Market Plan subscription**. `https://aisa.one/solutions/go-to-market`
- Never print or commit the key. If it is missing, ask the user to set `AISA_API_KEY`.

## Quick Start

```bash
python3 scripts/similarweb_client.py discover                     # route index from the live contract
python3 scripts/similarweb_client.py describe ROUTE               # one route: parameters, enums, limits, date rules
python3 scripts/similarweb_client.py window                       # latest complete data month
python3 scripts/similarweb_client.py check ROUTE name=value …     # validate against the contract, no API call
python3 scripts/similarweb_client.py quote ROUTE name=value …     # free price estimate
python3 scripts/similarweb_client.py call  ROUTE name=value … --max-usd "$APPROVED_USD"
python3 scripts/similarweb_client.py usage --days 1               # charged USD for reconciliation
```

`ROUTE` is a path from `discover` (without the `/similarweb` prefix). Every `name=value` comes from `describe`.
`{baseDir}/scripts/similarweb_client.py` is the same path in harnesses that substitute `{baseDir}`.

## Two rules

- **Cost rule** — never state or assume a price. Prices come only from a quote (before a call) or the
  `x-aisa-customer-cost-micros-usd` response header (after it).
- **Contract rule** — never assume a parameter. Build every request from the live contract.

## The protocol

### Discover — at session start, and again whenever a contract-built request is rejected

1. **Fetch the contract** — `discover`. It downloads the contract once, caches it with its ETag and revalidates
   with `If-None-Match` (a 304 means unchanged). `discover --refresh` forces a new copy.
2. **Read each route you need** — `describe ROUTE` shows required and optional parameters, enums, defaults,
   maximums and the route description. Date-window rules are written in the description.
3. **Find the latest data month** — `window`. It finds the route whose description requires the latest month,
   sends it an old month, and reads the allowed month from the free 400 message.

### Call — every request, in order

4. **Build the smallest request** that answers the question — the fewest months, metrics and rows the
   contract allows — and `check` it.
5. **Quote it** — `quote` (free). A 400 on a contract-built request means the contract changed: the client
   re-fetches the contract and reports what now differs.
6. **Compare before widening** — to add months, metrics, rows or domains, quote the wider variant too and pick
   the one that answers the question at the lowest quote.
7. **Get approval** — show the user the quote. Ask for a budget if none is set; above it, wait for approval.
8. **Call with a cap** — `call … --max-usd <approved USD>` sets `X-AISA-Max-Price-USD` and an
   `Idempotency-Key`. `call` without `--max-usd` only quotes.
9. **Report and reconcile** — report `cost_usd` (from the cost header) and `data_month`; reconcile with `usage`.

## How discovery works

| You need | Where it comes from |
|---|---|
| Routes and parameters | The contract JSON — `discover`, `describe` |
| Whether a request is valid | `check` against the contract, then a free quote |
| Date-window rules | The route description, and the message of the free 400 a real call returns if a rule is broken |
| Latest data month | `window` |
| Valid values after a 400 | `error.supported` in the response |
| Price before a call | `quote` (`X-AISA-Cost-Mode: quote`) |
| Actual cost | `cost_usd` (`x-aisa-customer-cost-micros-usd`) |
| Data month | `data_month` (`meta.last_updated` or `meta.end_date`) |
| Spend to date | `usage` (`GET /v1/usage`) |

Verified on 2026-09-13 across all 23 routes: every request built from the contract alone was accepted, every
required parameter was enforced exactly as declared, and every declared optional parameter was accepted.
Details, including the MCP alternative: `references/discovery.md`.

## Reading responses

- **400 with `meta.error_message`** on a real call — a date-window rule quotes do not check. The message states
  the rule or the allowed range; use it to fix the dates and retry. Not billed.
- **400 with `error.supported`** — `error.message` names the parameter, `supported` lists valid values. Not billed.
- **402** — the estimate is above your cap. Not billed.
- **409** — the `Idempotency-Key` was already used. Not billed.
- **503 with `retryable: true`** — retry once with a new key. Not billed.
- **Never retry a 200.** Make paid calls over REST, where the cost header is returned.

Cost-control detail: `references/cost-control.md`.

## When to use / when not to

- Use when the question is about a **website's** traffic, audience, sources, technology or search footprint.
- For keyword volumes and difficulty use the DataForSEO or Semrush skills; for backlinks, Ahrefs.

## Output

`call` prints JSON: `status`, `quoted_usd`, `cost_usd`, `request_id`, `latency_s`, `data_month`, `note`
(the API's own explanation when a rule or value was rejected) and `data` (the Similarweb response).
Report the data month with every number.

## API Reference

- Contract: [`https://aisa.one/docs/openapi/similarweb.json`](https://aisa.one/docs/openapi/similarweb.json) — the source of truth for routes and parameters
- Human reference: [Similarweb API docs](https://aisa.one/docs/api-reference/similarweb/get_similarweb-website-traffic-engagement) (each page embeds the same contract)
- MCP: `https://mcp.aisa.one/similarweb/mcp` (`tools/list` returns the same schemas)
- Cost control: quote header `X-AISA-Cost-Mode: quote` · cap header `X-AISA-Max-Price-USD` · cost header `x-aisa-customer-cost-micros-usd` · usage `GET https://api.aisa.one/v1/usage?start_time=<unix>`

See the [full AIsa API Reference](https://aisa.one/docs/api-reference).

## License

MIT — see [LICENSE](../LICENSE) at the category root.
