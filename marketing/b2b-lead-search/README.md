# B2B Lead Search 🎯

Search and enrich B2B leads from Apollo's 270M+ contact/company database via
[AIsa](https://aisa.one). Find target-account companies, surface
decision-makers by title, and resolve a person's title, company, and email —
the foundation of an automated GTM / cold-outreach flow.

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible harness:
**Claude Code**, **Claude**, **OpenAI Codex**, **Cursor**, **Gemini CLI**,
**OpenCode**, **Goose**, **OpenClaw**, **Hermes**, and others.

Requires Python 3 and `AISA_API_KEY` (get one at [aisa.one](https://aisa.one)).

## Quick Start

```bash
export AISA_API_KEY="your-key"

# Target-account companies
python3 scripts/apollo_client.py companies --keywords "fintech" \
  --locations "United States" --employees "50,200" --per-page 5

# Search your saved Apollo contacts by title
python3 scripts/apollo_client.py contacts --titles "Head of Marketing" --per-page 5

# Person enrichment -> title / company / email
python3 scripts/apollo_client.py enrich-person --first-name Dylan \
  --last-name Field --company Figma

# Company enrichment
python3 scripts/apollo_client.py enrich-org --domain stripe.com
```

## Use Cases

- **Target-account list building** — filter the global company DB by keyword, size, and geography.
- **Decision-maker enrichment** — resolve a person's title, company, LinkedIn, and work email.
- **CRM enrichment** — fill in missing title / company / email / firmographic fields.
- **GTM automation** — feed results into an outreach sequence (e.g. AgentMail).

> `contacts` searches your own saved Apollo contacts, not the global 270M-person
> database. Build lists via `companies` + `enrich-person`.

## Data handling

Contact data is sensitive. Do not publish emails or transmit lists to other
systems without authorization, and never invent an email the API did not return.

## Requirements

- Python 3
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
