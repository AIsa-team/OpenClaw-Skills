---
name: creator-marketing
description: Plan creator, influencer and ambassador partnerships for a brand or agency client. Find and assess candidates, structure compensation and usage rights, draft outreach and creative briefs, and measure qualified outcomes. Use for creator sourcing, gifting, sponsorships and UGC programs; connected-account diagnosis and campaign execution use their specialist workflows.
compatibility: "Requires Python 3.10+ and the AISA_API_KEY environment variable."
metadata:
  author: aisa.one
  version: "0.0.1"
  aisa:
    homepage: https://aisa.one
    requires:
      bins:
        - python3
      env:
        - AISA_API_KEY
    primaryEnv: AISA_API_KEY
---

# Creator Marketing

Help the user choose creators and design a feasible partnership pilot. Use information from the current conversation and materials the user explicitly provides. Clarify only missing details that affect the plan: product, audience and market, objective, channels, budget, timing, team capacity and constraints. Do not assume a predefined brand file or workspace layout.

## Choose the partnership model

Select the model by the job: a sponsored placement borrows distribution; commissioned UGC buys content and may not include posting; gifting has no guaranteed post; an affiliate deal needs commission/tracking terms; an ambassador program adds recurring responsibilities and relationship management. A small aligned creator is not automatically cheaper per sale than a larger one. Avoid universal tier, engagement-rate or compensation benchmarks. Treat actual quotes and comparable sourced evidence as inputs, not guarantees.

For detailed deal, brief and measurement guidance read [partnership-playbook.md](references/partnership-playbook.md). For a recurring high-volume UGC network also read [ugc-program.md](references/ugc-program.md); do not default every campaign to a creator network.

## Research and shortlist

Proactively use external evidence when it can improve candidate choice, creative fit, deal assumptions or current practices. Do not wait for a specific request to search. Skip external research when explicitly prohibited or supplied evidence already answers the decision. A planning-only request does not require finding named creators.

Before fetching, read [aisa-contract.md](references/aisa-contract.md) and [capabilities.md](references/capabilities.md). Use only the bundled helper through Router schema → quote → use, with fixed tools. Do not use direct vendors, arbitrary browser/MCP research or paid nested workflows. Reuse supplied account findings. Audience-demographic or fraud checks require evidence from an actually available tool; do not assume one is installed. This skill adds partnership design. No Similarweb is needed for this workflow.

For YouTube/TikTok discovery use similar creators by content direction, seed or both. Start with 3–5 matches (helper maximum 10), apply the requested market/language filters in one query and state remaining fit gaps. Do not create broader unfiltered or alternative queries unless the user asks for a comparison. For YouTube content evidence use a focused YouTube search. Instagram profile/posts can assess known handles; similar creators does not support Instagram. General search/extract can verify case studies, public evidence or current official disclosure guidance. Look up a missing business email only for a selected candidate when contact preparation is part of the request; reuse an email already returned. No bulk enrichment by default.

Never label similarityScore as audience overlap, real follower quality, purchase intent or expected ROI. Creator region/language are not audience demographics. Distinguish provider-returned facts, source dates, content-based hypotheses, and media-kit verification needed. Named recommendations need actual source/profile links. Inspect evidence relevant to the brief rather than claiming a full audit from one page; sparse/private/empty results are gaps, not proof of fraud. Do not infer sensitive personal traits of creators or audiences.

For a shortlist, provide candidate/platform/profile, observed category and content fit, relevant returned metrics with time/denominator if known, uncertainties/conflicts, and why to advance or reject. Use unknown for unreturned fields and price TBD for missing quotes. Do not fabricate candidates to fill the requested count. Keep returned contact details scoped to the user's legitimate partnership task; lookup is not permission to send outreach.

## Produce a feasible partnership pilot

Recommend a first pilot or rank alternatives. Specify creators or selection criteria, deliverables, posting vs content-only scope, schedule, cash fees, product cost/shipping, commissions, usage rights, revisions, production and coordination workload. Sum combined-plan costs and peak-week hours; include capped incentive liability rather than excluding it from budget. Preserve the user's cost categories exactly: a product-plus-shipping amount already includes both, so do not relabel it as shipping or assume free inventory. Mark unquoted creator fees as proposed allocations, not agreed rates. If capacity, quotes or margins are unknown, show dependencies and provisional allocations rather than predicted sales.

Draft personalized outreach only when useful, grounded in observed content; do not send it without authorization. A creator brief includes audience/problem, 2–3 substantiated messages, format, CTA, creative freedom, claims to avoid, disclosure requirements to verify, delivery/review dates and agreed usage boundaries. Never imply paid reuse, account access, exclusivity or AI likeness rights are automatically included. Content usage rights alone do not fund or launch paid distribution. When media spend is unallocated, keep the current pilot organic/content-only and describe paid amplification as a separately budgeted, authorized next step. Do not say the pilot tests paid performance merely because the quote includes ad rights.

Explain compensation alternatives and tradeoffs. Ask for a quote with separately priced deliverables, rights and exclusivity; do not prescribe one negotiation anchor universally. Draft a commercial checklist, not a purported legally approved contract. Before stating jurisdiction-specific legal or platform requirements, verify current official sources through the research tools, or identify the specific rule as pending verification. Distinguish source requirements from recommended best practices; do not turn wording such as “likely to notice” into a mandatory legal rule. Match the disclosure to the actual compensation: free-product wording alone is incomplete when cash is also paid. Transparently disclose material brand relationships and avoid fabricated personal experience or claims.

Measure the agreed objective: use creator/placement links and codes, qualified lead definitions and an attribution window, plus surveys when appropriate. Deduplicate code/link conversions, separate attributed revenue from incremental lift, and include total costs and margin when calculating profitability. Paid reuse metrics do not by themselves prove the creator's organic audience converts. If sample size is small, use learning criteria; no unsupported industry averages or sales forecasts.

Deliver a concise shortlist/pilot/brief matching the actual request, with the next action, owner, evidence and unresolved dependencies. Explain how research changed or supplemented the plan; no useful sources is an acceptable finding.

## Runtime and handoff


This skill researches and drafts plans; it does not send messages, sign agreements, transfer money, publish posts or change ad accounts. If the user requests execution, confirm that an appropriate tool is available and that their authorization covers the action. Otherwise, provide the prepared material and next steps.


On `budget_approval_required`, explain the quote and remaining allowance for the requested single scope, then wait for actual authorization before increasing the allowance. Do not recommend arbitrary multiples of the estimate as a new budget. Use always obtains a fresh quote; saved quotes are observations, not execution tokens. Do not switch providers to evade this decision.

## Stateless cost control

Read references/aisa-contract.md before research. Default task data budget is $2 unless the user specifies otherwise. Before Use, fetch a fresh quote and compare it with the remaining budget; exceeding that budget requires user authorization. Each attempted Use consumes its quoted amount from the task budget, even when it fails. Pass the returned remaining_budget_usd_micros on subsequent calls. Actual fees are informational: use a valid header, otherwise the item fee, otherwise null. Missing or differing fees never hide valid results or require billing reconciliation. Estimates may settle higher; quoted budget is not a hard billing cap. No automatic network retries or accounting files. Report concrete request errors; never ask the user to check invoices or billing dashboards.

## Authentication and invocation

Set `AISA_API_KEY` in the process environment; never paste it into a prompt or commit it. If missing, ask the user to configure it. Run commands from this skill directory or resolve `scripts/request.py` against the loaded skill root. The existing direct-API skills use api.aisa.one; this skill intentionally uses the Router at tools.aisa.one for schema, quote and tool execution. It needs Python 3.10+ only.

When the helper returns `budget_approval_required`, end external research for this turn and present that quote. Do not substitute a cheaper capability, provider or reduced input unless the user authorizes a changed scope. A free quote error may be corrected before use. Explain concrete execution failures without creating a billing-reconciliation task.
