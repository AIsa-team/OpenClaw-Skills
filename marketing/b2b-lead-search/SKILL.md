---
name: b2b-lead-search
description: 'Search and enrich B2B leads with Apollo via AIsa — find target-account companies by keyword, industry, size, and location; enrich a person to resolve their title, company, and work email; enrich a company by domain; and search your saved Apollo contacts. Use for GTM prospecting, building target-account lists, finding decision-makers, and CRM data enrichment.'
license: MIT
compatibility: Works with any agentskills.io-compatible harness — Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI, OpenClaw, Hermes, Goose, and others. Requires Python 3 and AISA_API_KEY.
metadata:
  aisa:
    emoji: 🎯
    homepage: https://aisa.one
    requires:
      bins:
      - python3
      env:
      - AISA_API_KEY
    primaryEnv: AISA_API_KEY
    harnesses:
    - claude-code
    - claude
    - opencode
    - cursor
    - codex
    - gemini-cli
    - openclaw
    - hermes
    - goose
---

# B2B Lead Search 🎯

**Prospect and enrich B2B leads from Apollo's 270M+ contact/company database. Powered by AIsa.**

Find the right companies, surface the right decision-makers, and resolve a person's title, company, and work email — the foundation of an automated GTM / cold-outreach workflow.

## Setup

This skill requires the `AISA_API_KEY` environment variable (get one at [aisa.one](https://aisa.one)):

```bash
export AISA_API_KEY="your-aisa-api-key"
```

Never print, log, or commit the key. Treat returned contact data (names, emails) as sensitive — do not publish or transmit it elsewhere without authorization.

## Usage

```bash
# Find target-account companies
python3 ${CLAUDE_PLUGIN_ROOT}/skills/b2b-lead-search/scripts/apollo_client.py companies \
  --keywords "artificial intelligence" --per-page 5

# Enrich a person -> title, company, email
python3 ${CLAUDE_PLUGIN_ROOT}/skills/b2b-lead-search/scripts/apollo_client.py enrich-person \
  --first-name Dylan --last-name Field --company Figma
```

### Subcommands

| Subcommand | Purpose |
|------------|---------|
| `companies` | Search Apollo's global company database by keyword, location, employee range |
| `enrich-person` | Resolve one person's title, company, LinkedIn, and work email |
| `enrich-org` | Enrich a company by domain or name (industry, size, founded, description) |
| `contacts` | Search **your own saved Apollo contacts** by title/location/company (not the global people database) |

### Arguments

| Argument | Subcommand | Description |
|----------|-----------|-------------|
| `--keywords` / `-k` | `companies`, `contacts` | Comma-separated company keywords |
| `--locations` / `-l` | `companies`, `contacts` | Comma-separated locations |
| `--employees` | `companies` | Employee-count range as `min,max` (e.g. `50,200`) |
| `--titles` / `-t` | `contacts` | Comma-separated job titles |
| `--per-page` | `companies`, `contacts` | Results per page (default 10) |
| `--page` | `companies`, `contacts` | Page number (default 1) |
| `--first-name`, `--last-name`, `--company`, `--domain`, `--email` | `enrich-person` | Any subset that identifies the person |
| `--domain`, `--name` | `enrich-org` | Company domain or name |

### Examples

```bash
# US AI companies with 50-200 employees
python3 ${CLAUDE_PLUGIN_ROOT}/skills/b2b-lead-search/scripts/apollo_client.py companies \
  -k "artificial intelligence" -l "United States" --employees "50,200" --per-page 10

# Marketing decision-makers
python3 ${CLAUDE_PLUGIN_ROOT}/skills/b2b-lead-search/scripts/apollo_client.py contacts \
  -t "Head of Marketing,VP Marketing" --per-page 10

# Enrich a company by domain
python3 ${CLAUDE_PLUGIN_ROOT}/skills/b2b-lead-search/scripts/apollo_client.py enrich-org \
  --domain stripe.com
```

> **Note on `contacts`:** Apollo's `contacts/search` operates on the API
> account's *own saved contacts*, not the global 270M-person database. To build
> a decision-maker list from scratch, use `companies` to find target accounts,
> then `enrich-person` (with a name + company/domain) to resolve each person's
> title and work email.

## Output

Human-readable lists: companies (name, domain, industry, employees, location, LinkedIn), contacts (name, title, company, email, LinkedIn), and enrichment cards (full resolved profile / company facts). `companies`/`contacts` also print the total match count and page info.

## When to Use

Use for **B2B prospecting, GTM lead lists, finding decision-makers, and CRM enrichment**. Pair with the `kol-creator-discovery` skill for influencer outreach, or `competitive-seo` / `geo-visibility` for the marketing-intelligence half of a GTM workflow. Do not fabricate emails — only report what the API returns.

## API Reference

This skill calls these AIsa Apollo endpoints:

- `POST /apis/v1/apollo/mixed_companies/search` — company / account search
- `POST /apis/v1/apollo/contacts/search` — contact search
- `POST /apis/v1/apollo/people/match` — person enrichment
- `POST /apis/v1/apollo/organizations/enrich` — organization enrichment

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the repo root.
