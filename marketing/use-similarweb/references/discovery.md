# Discovering the contract at runtime

This skill never hardcodes routes' parameters. Everything below was verified on 2026-09-13 across all
23 Similarweb routes.

## Sources

| Source | Access | Use it for |
|---|---|---|
| `https://aisa.one/docs/openapi/similarweb.json` | Public, no key | **Primary.** OpenAPI 3 for the Similarweb family only: routes, parameters, schemas, descriptions, server URL |
| `tools/list` on `https://mcp.aisa.one/similarweb/mcp` | Bearer key | The same schemas as MCP tools — use when the agent already works through MCP |
| MCP `get_details` with an `operation_id` | Bearer key | One route's full schema on demand |
| `https://aisa.one/openapi.yaml` | Public, no key | Fallback: the full AIsa contract; keep paths starting with `/similarweb` |

To reach Similarweb tools over MCP, connect to the Similarweb module endpoint above and use its `tools/list`.

## Caching

The contract responds with `ETag`, `Last-Modified` and `Cache-Control: max-age=1800, must-revalidate`.

1. Store the body with its ETag.
2. Within `max-age`, use the cached copy.
3. After it, revalidate with `If-None-Match: <ETag>` → `304 Not Modified` (no body, about a second) means the
   copy is current; `200` delivers a new contract.

`similarweb_client.py discover` does this automatically (cache: `$AISA_SIMILARWEB_CACHE` or `~/.cache/aisa-similarweb`).

## Building a request from an operation

For the route's `get` operation:

- Include every parameter with `required: true`.
- Use `schema.enum` for allowed values, `schema.default` for defaults and `schema.maximum` for limits.
- Parameter descriptions give formats (for example `YYYY-MM`) and examples (`e.g. …`).
- The operation `description` states date-window rules — how many months a request may span, or that it must
  use the latest month.
- Add optional parameters only when the question needs them.

`similarweb_client.py check ROUTE name=value …` compares a request against the contract without calling the API:
missing required parameters, parameters the contract does not declare, enum violations and maximums.

Verified: requests built from the contract alone were accepted on 23/23 routes; removing any one required
parameter was rejected on 78/78; adding every declared optional parameter was accepted on 23/23.

## What the contract does not carry, and where to get it

| Need | How |
|---|---|
| Latest complete data month | Find the route whose description requires the latest month, send it an old month (`2000-01`) with its other required parameters, and read the allowed month from `meta.error_message` in the 400. Free. `similarweb_client.py window` does this |
| Whether a date window is valid | Quotes validate parameters but not date windows. A real call that breaks a window returns a free 400 whose `meta.error_message` states the rule — fix the dates and retry |
| Valid values after a rejected request | Routes that return `error.supported` list the valid values and name the parameter in `error.message` |

## Keeping in step with the contract

- Revalidate the contract at session start.
- If a request built from the contract is rejected at quote time, re-fetch the contract (`discover --refresh`)
  and rebuild — the contract has changed. `quote` and `call` in the client do this re-check automatically.
