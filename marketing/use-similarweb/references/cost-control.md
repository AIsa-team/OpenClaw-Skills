# Cost control protocol

**This file contains no prices or pricing formulas, by design.** Prices and the way they are computed can
change at any time, so the only sources of cost are the API's quote (before a call) and its cost header (after).

## 1. Quote (free)

Send the exact request you intend to make — built from the contract (`discovery.md`) — plus one header:

```bash
curl -s "https://api.aisa.one/apis/v1/similarweb<ROUTE>?<parameters from the contract>" \
  -H "Authorization: Bearer $AISA_API_KEY" \
  -H "X-AISA-Cost-Mode: quote"
```

- Response: `200 {"object":"cost_estimate","estimated_cost_micros_usd":<int>,"may_exceed_estimate":<bool>, …}`.
- Units: micro-dollars, 1,000,000 = 1 USD.
- A quote is not executed, not billed and not counted as a request.
- An invalid request is rejected at quote time with the same 400 it would get when executed.

## 2. Compare scope variants before widening

Scope dimensions include months, metrics, rows (`limit`, `offset`) and the number of domains. Do not assume how
any of them affects cost:

1. Build the smallest request that answers the question and quote it.
2. If the question needs more, build the wider variant and quote it.
3. Compare what each variant returns against what it costs, and choose.

Quotes are free, so two to four quotes per decision is normal.

## 3. Budget and approval

Get a budget from the user, per call or per task. Never execute a call whose quote exceeds it without explicit
approval. `similarweb_client.py call` enforces this: without `--max-usd` it only quotes.

## 4. Cap

`X-AISA-Max-Price-USD: <USD>` → if the estimate exceeds it, the call is refused before execution:
`402 {"error":{"code":"estimated_price_exceeds_max_price"}}`, not billed. Set it to the approved amount.

## 5. Idempotency

`Idempotency-Key: <uuid>` → a repeated key returns `409 {"error":"idempotent request already admitted"}`, not
billed. Use one key per logical request and a fresh key for a deliberate retry.

## 6. Actual cost

On a 2xx response, the header `x-aisa-customer-cost-micros-usd` is what was charged. Report this value; it can
differ from the quote.

## 7. Reconcile

`GET https://api.aisa.one/v1/usage?start_time=<unix>&end_time=<unix>` → `totals.charged_micros_usd`.

## Over MCP

MCP `use(max_price_usd=…)` refuses calls whose estimate is above the cap (402, not billed). For each call's actual
cost, make paid calls over REST, which returns the cost header.
