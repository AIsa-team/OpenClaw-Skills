# AIsa Similarweb

**Similarweb website intelligence for autonomous agents — discovered at runtime, spent deliberately. Powered by AIsa.**

This skill holds no endpoint parameters and no prices. The agent reads parameters from the live contract
(`https://aisa.one/docs/openapi/similarweb.json`) and gets the cost of every request from the API — a free quote
before the call, the cost header after it — so the skill stays correct when routes or prices change.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness: Claude Code, Claude, OpenCode,
Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others.

Requires Python 3 and `AISA_API_KEY` on an account with the Hive GTM subscription (get one at
[aisa.one](https://aisa.one)).

## What Can You Do?

### Traffic for a domain
```text
"How many visits did cnn.com get last month? Quote it first."
```

### Competitors and search footprint
```text
"Who are nike.com's keyword competitors and which landing pages win?"
```

### Audience and sources, within a budget
```text
"Show me cnn.com's referral sources and its audience overlap with bbc.com — ask me before spending."
```

## Quick Start

```bash
export AISA_API_KEY="sk-aisa-..."
python3 scripts/similarweb_client.py discover
python3 scripts/similarweb_client.py describe ROUTE
python3 scripts/similarweb_client.py quote ROUTE name=value …
python3 scripts/similarweb_client.py call  ROUTE name=value … --max-usd "$APPROVED_USD"
```

## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) and the Similarweb contract at
`https://aisa.one/docs/openapi/similarweb.json`.

## License

MIT — see [LICENSE](../LICENSE) at the category root.
