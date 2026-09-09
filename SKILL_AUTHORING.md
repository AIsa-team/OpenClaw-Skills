# Skill Authoring SOP — AIsa-team/agent-skills

Standard operating procedure for composing and maintaining skills in this
repo. Based on the [agentskills.io specification](https://agentskills.io/specification)
with a few house-level requirements on top.

## TL;DR

1. Skills live in `<category>/<skill-name>/`, where `<category>` is one of
   `financial`, `search-research`, `social-media`, `ai-models`, `marketing`,
   `creative`, or `platform`. The generic AIsa Skill is `platform/aisa/`
   (slug `aisa`). Do not add extra root-level Skills.
2. `SKILL.md` frontmatter must be **spec-compliant** (validate with
   [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref)
   before merging).
3. Use the optional `compatibility:` field when a Skill has environment or
   product constraints that users need to know before activation.
4. A `README.md` and consistent body sections are recommended for humans
   browsing the repository, but they are not required by the Agent Skills
   specification and are not validity gates.

## Directory layout

```
<category>/
├── README.md         # category index
├── LICENSE           # category-local copy for skill-relative license links
└── <skill-name>/
    ├── SKILL.md      # required — metadata + agent-facing instructions
    ├── README.md     # optional — human-facing overview
    ├── scripts/      # optional — runnable code
    ├── references/   # optional — long-form docs the agent loads on demand
    ├── assets/       # optional — static resources (templates, data, images)
    └── ...
```

Use the narrowest matching category. Adding a new top-level category requires
updating the root README, `CATEGORY_NAMES`, and the exporter allowlist. Add a
sync workflow only when a separate category distribution is intended;
`platform` currently has none. Do not create placeholder publisher workflows.

Directory name rules (enforced by the spec):

- Lowercase ASCII letters, digits, and hyphens only — `a-z 0-9 -`
- 1–64 characters
- No leading or trailing hyphen
- No consecutive hyphens
- **Must match the `name:` field in `SKILL.md` exactly.**

## `SKILL.md` frontmatter

| Field           | Required | Notes |
|-----------------|----------|-------|
| `name`          | **Yes**  | Matches directory name. See rules above. |
| `description`   | **Yes**  | 1–1024 chars. Describe **what the skill does and when to use it**. Include specific keywords that help an agent pick it. |
| `license`       | No | Recommended when a Skill has a distinct distribution license. The field is optional in the specification. |
| `compatibility` | No | Recommended for environment requirements or known product constraints. Maximum 500 chars. |
| `metadata`      | Recommended | Vendor metadata — `homepage`, `emoji`, `requires`, `primaryEnv`, etc. Use reasonably unique keys. |
| `allowed-tools` | Optional | Space-separated list. Experimental, support varies. |

### Example frontmatter

Only `name` and `description` are required. Include optional fields only when
their values are accurate and useful:

```yaml
---
name: <directory-name>
description: "<one paragraph: what + when. 1-1024 chars. Specific keywords for agent discovery.>"
license: MIT
compatibility: "Requires <verified binaries, environment variables, operating systems, or client features>."
metadata:
  homepage: https://aisa.one
  emoji: "<single emoji>"
  requires:
    bins: [<binary1>, <binary2>]
    env: [<ENV_VAR_1>]
  primaryEnv: <PRIMARY_ENV_VAR>
  harnesses: [<verified-harness-id>]
---
```

### Dual-license arrangement

This repo has two licenses, serving two different purposes:

| What | License | Where |
|---|---|---|
| **Contribution / source-repo license** | Apache-2.0 | [`LICENSE`](./LICENSE) at the repo root. Covers the umbrella contributor bargain — explicit patent grant, attribution, notice preservation. This is what governs pull requests and source-tree redistribution. |
| **Per-skill distribution license** | MIT | Declared in each `SKILL.md`'s `license:` frontmatter. This is what packaged skills ship under when they're pulled from this repo and redistributed via [clawhub.ai](https://clawhub.ai) — simpler, fewer obligations for redistribution consumers. |

The two are mutually compatible: Apache-2.0 is strictly more permissive-with-obligations than MIT, so the umbrella can host MIT-licensed distribution artifacts without friction. New skills should keep `license: MIT` in their frontmatter unless there's a deliberate reason to differ.

### Compatibility metadata

- **`compatibility:`** is the agentskills.io-spec field. Human-readable
  sentence. Harnesses that read the spec surface this to the user.
- **`metadata.harnesses:`** is a machine-readable list some harnesses
  (OpenClaw, Hermes) use for install-time checks.

Use only claims that have actually been verified. Do not require every Skill
to repeat a fixed harness roster: support can depend on how a client discovers
and resolves packaged resources.

## `SKILL.md` body

The specification imposes no fixed headings on the Markdown body. The
following is an optional template for larger API-backed Skills; omit or rename
sections that do not help the agent perform the task:

```markdown
# <Skill Name> <emoji>

**<One-sentence tagline describing the value.> Powered by AIsa.**

<One paragraph expanding the tagline. What sources / models / workflows
it touches. Any unique capability.>

## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness, including:

- **Claude Code** — via `claude skill add`
- **OpenClaw** — drops into the skill directory
- **OpenAI Codex** — via the `skills/` folder
- **Cursor** — agent skills support
- **Gemini CLI**, **Goose**, **OpenCode**, **Hermes**, and others

Requires `python3`, `bash`, and `AISA_API_KEY`.

## What Can You Do?

### <Use case 1>
```text
"<example query>"
```

### <Use case 2>
```text
"<example query>"
```

## Quick Start

```bash
export AISA_API_KEY=sk-...
python3 {baseDir}/scripts/<client>.py <subcommand> [--flags]
```

The portable Agent Skills convention is to reference resources relative to
the Skill root, for example `scripts/client.py` or
`references/REFERENCE.md`. A Harness-specific placeholder such as `{baseDir}`
may be shown as an additional example only when that Harness is explicitly
supported; do not assume all clients substitute it.

## Inputs and Outputs

- Input: <what the user passes>
- Output: <what the skill returns — formats, fields>

## When to use / When NOT to use

- Use when: …
- Do NOT use when: …

## Requirements

- <bin> / <version>
- `AISA_API_KEY` — required, get one at [aisa.one](https://aisa.one)
- <optional creds>

## API Reference

<One-sentence description of the endpoint family this skill calls, then
a bulleted list of each specific endpoint with a link to its reference
page. Example:>

This skill calls the following AIsa endpoints directly:

- [<Endpoint name>](https://aisa.one/docs/api-reference/<category>/<slug>) — <what it's used for>
- [<Endpoint name>](https://aisa.one/docs/api-reference/<category>/<slug>) — <what it's used for>

See the [full AIsa API Reference](https://aisa.one/docs/api-reference) for the complete catalog.

## License

MIT — see [LICENSE](../LICENSE) at the category root.
```

Keep `SKILL.md` under 500 lines. Move long reference material into
`references/*.md` and link to it — agents load those on demand, saving
context.

## Where API Reference information goes

For API-backed Skills, put the endpoint information where it helps the agent
use the Skill correctly. A dedicated `## API Reference` heading is optional;
the information may be integrated into usage instructions or a referenced
file.

**README.md gets only a one-paragraph pointer to the catalog.** Humans
landing on the folder on GitHub want orientation, not an endpoint table.
Duplicating the list creates drift — when AIsa adds a new endpoint we'd
have to update two places per skill.

If a README is present, a short link to the API catalog is usually sufficient:

```markdown
## API Reference

See the [AIsa API Reference](https://aisa.one/docs/api-reference) for the
complete catalog of endpoints this skill can call.
```

## `README.md` body

The README is optional and intended for humans landing on the Skill folder on
GitHub. Avoid duplicating large instruction blocks that can drift from
`SKILL.md`.

```markdown
## Compatibility

Works with any [agentskills.io](https://agentskills.io)-compatible
harness: Claude Code, Claude, OpenCode, Cursor, Codex, Gemini CLI,
OpenClaw, Hermes, Goose, and others.
```

## Documentation links

Always link to the canonical docs host: **`https://aisa.one/docs/...`**

Do **not** use:

- `https://docs.aisa.one/...` (legacy subdomain; redirects today, may not later)
- `https://aisa.mintlify.app/...` (preview/staging host; not a stable URL)

Common targets:

| You want to link to | Use |
|---|---|
| Docs landing | `https://aisa.one/docs` |
| API reference index | `https://aisa.one/docs/api-reference` |
| A specific endpoint | `https://aisa.one/docs/api-reference/<category>/<slug>` |
| Model catalog | `https://aisa.one/docs/guides/models` |
| Docs index for LLMs | `https://aisa.one/docs/llms.txt` |

## Validation before submitting a PR

Blocking checks are limited to objective, reproducible conditions:

1. `name` matches the Skill directory and satisfies the specification.
2. `description` is non-empty and no longer than 1024 characters.
3. Frontmatter passes the pinned `skills-ref==0.1.1` validator.
4. Local Markdown references resolve inside the repository.
5. Referenced scripts and `{baseDir}` targets exist.
6. Python, shell, and JavaScript entry points parse successfully.
7. No plaintext credentials or repository symlinks are introduced.
8. Every category export is byte-for-byte identical to its source directory.
9. Run the repository quality gate with its locked dependencies:
   ```bash
   uv --no-config venv --python python3.11 .venv
   uv --no-config pip sync --python .venv/bin/python --require-hashes \
     --only-binary :all: .github/quality-gate-requirements.txt
   .venv/bin/python .github/scripts/catalog_quality.py --changed-from origin/main
   ```
   This validates repository-wide structure, credentials, symlinks, and
   category exports, while schema, link, reference, and syntax checks apply to
   files changed from `origin/main`. Run with `--all` when deliberately cleaning
   historical catalog issues.
   If `.github/quality-gate-requirements.in` changes, regenerate and commit the
   hashed lock using the exact command recorded at the top of
   `.github/quality-gate-requirements.txt`.

README files, fixed body headings, `license`, `compatibility`, canonical Docs
URLs, and a consistent presentation style remain useful review guidance, but
are not Agent Skills validity requirements and are not blocking checks.

The gate has no historical issue baseline. Untouched legacy issues do not block
unrelated contributions, while any changed Skill must pass the current checks.
Skill removals are ordinary Git changes and must be called out in the PR for
review; Git history remains the retirement record.

## Updating this SOP

When a new Harness integration is verified, update this guide and only the
Skills whose actual compatibility claims, requirements, or vendor metadata
change. Do not add a universal compatibility roster or fixed Markdown section
to every Skill. Keep claims evidence-based and scoped to the affected package.
