#!/usr/bin/env python3
"""
AIsa Brand 360 — Company Digital X-Ray (Composite CLI Client)
=============================================================

One command runs FOUR AIsa APIs concurrently and returns a single, combined,
human-readable "digital X-ray" of any company from just a name + domain:

  1. Firmographics    — Apollo  /apollo/organizations/enrich (by domain)
  2. Search dominance — DataForSEO /dataforseo/serp/google/organic/live/advanced
  3. Social sentiment — Scrape Creators /reddit/search
  4. AI visibility    — Oxylabs AI Search /oxylabs/ai-search (GEO brand-check)

Each section degrades gracefully: if one call fails or times out, that section
prints as "unavailable" and the rest of the report still renders.

Requires the AISA_API_KEY environment variable.

Usage:
    python3 brand360_client.py --company "Midea" --domain midea.com --category "air conditioner"
    python3 brand360_client.py --company "Haier" --domain haier.com --category "refrigerator" --engine chatgpt
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any

AISA_BASE = "https://api.aisa.one/apis/v1"

# Per-section timeouts (seconds). GEO (chatgpt) is slow by design.
TIMEOUT_APOLLO = 60
TIMEOUT_SERP = 90
TIMEOUT_REDDIT = 60
TIMEOUT_GEO = 150

# AI engines that take `prompt`; the rest take `query`.
PROMPT_SOURCES = {"chatgpt", "gemini", "perplexity"}


def get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY", "")
    if not key:
        print("Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


# --------------------------------------------------------------------------- #
# HTTP helpers (reused logic from the four sibling clients). These raise on
# error so the per-section runner can catch and degrade gracefully.
# --------------------------------------------------------------------------- #
def aisa_post(api_key: str, path: str, body: Any, timeout: int) -> dict[str, Any]:
    url = f"{AISA_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def aisa_get(api_key: str, path: str, params: dict[str, Any], timeout: int) -> dict[str, Any]:
    qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{AISA_BASE}{path}?{qs}" if qs else f"{AISA_BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _short_err(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode()[:200] if exc.fp else ""
        except Exception:
            pass
        return f"HTTP {exc.code}{(': ' + body) if body else ''}"
    if isinstance(exc, urllib.error.URLError):
        return f"network error: {exc.reason}"
    return f"{type(exc).__name__}: {exc}"


# --------------------------------------------------------------------------- #
# Section 1 — Firmographics (Apollo organizations/enrich by domain)
# --------------------------------------------------------------------------- #
def fetch_firmographics(api_key: str, domain: str, company: str) -> dict[str, Any]:
    body: dict[str, Any] = {"domain": domain}
    if company:
        body["organization_name"] = company
    data = aisa_post(api_key, "/apollo/organizations/enrich", body, TIMEOUT_APOLLO)
    return data.get("organization") or {}


# --------------------------------------------------------------------------- #
# Section 2 — Search dominance (DataForSEO live organic SERP)
# --------------------------------------------------------------------------- #
def _task_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = data.get("tasks") or []
    if not tasks:
        return []
    results = (tasks[0].get("result")) or []
    if not results:
        return []
    return results[0].get("items") or []


def fetch_serp(api_key: str, query: str, depth: int) -> list[dict[str, Any]]:
    body = [{
        "keyword": query,
        "location_name": "United States",
        "language_name": "English",
        "depth": depth,
    }]
    data = aisa_post(api_key, "/dataforseo/serp/google/organic/live/advanced", body, TIMEOUT_SERP)
    items = _task_result(data)
    return [i for i in items if i.get("type") == "organic"][:depth]


# --------------------------------------------------------------------------- #
# Section 3 — Social sentiment (Scrape Creators reddit/search)
# --------------------------------------------------------------------------- #
def fetch_reddit(api_key: str, company: str) -> list[dict[str, Any]]:
    data = aisa_get(api_key, "/reddit/search",
                    {"query": company, "sort": "relevance", "timeframe": "all"},
                    TIMEOUT_REDDIT)
    return data.get("posts") or []


def _reddit_url(post: dict[str, Any]) -> str:
    pl = post.get("permalink") or ""
    if pl.startswith("http"):
        return pl
    if pl:
        return f"https://www.reddit.com{pl}"
    return post.get("url") or ""


# --------------------------------------------------------------------------- #
# Section 4 — AI visibility (Oxylabs AI Search GEO brand-check)
# --------------------------------------------------------------------------- #
def fetch_geo(api_key: str, query: str, engine: str) -> dict[str, Any]:
    body: dict[str, Any] = {"source": engine, "parse": True, "geo_location": "United States"}
    if engine in PROMPT_SOURCES:
        body["prompt"] = query
        if engine == "chatgpt":
            body["search"] = True
    else:
        body["query"] = query
        body["render"] = "html"
    return aisa_post(api_key, "/oxylabs/ai-search", body, TIMEOUT_GEO)


def _first_result_content(data: dict[str, Any]) -> dict[str, Any]:
    results = data.get("results")
    if isinstance(results, list) and results:
        content = results[0].get("content")
        if isinstance(content, dict):
            return content
    return {}


def parse_geo_answer(engine: str, data: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    """Return (answer_text, [{source, url}, ...]) normalized across engines."""
    answer_parts: list[str] = []
    citations: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_cite(name: str, url: str) -> None:
        url = (url or "").strip()
        if url and url not in seen:
            seen.add(url)
            citations.append({"source": (name or "").strip(), "url": url})

    content = _first_result_content(data)

    if engine in ("chatgpt", "gemini"):
        txt = content.get("response_text") or content.get("text") or ""
        if isinstance(txt, list):
            txt = "\n".join(str(t) for t in txt)
        if txt:
            answer_parts.append(str(txt))
        for c in content.get("citations", []) or []:
            if isinstance(c, dict):
                add_cite(c.get("title") or c.get("source") or "", c.get("url") or c.get("link") or "")
            elif isinstance(c, str):
                add_cite("", c)

    elif engine == "perplexity":
        txt = content.get("response_text") or content.get("answer") or content.get("text") or ""
        if txt:
            answer_parts.append(str(txt))
        for key in ("top_sources", "sources_results", "sources", "citations"):
            for c in content.get(key, []) or []:
                if isinstance(c, dict):
                    add_cite(c.get("title") or c.get("source") or "", c.get("url") or c.get("link") or "")
                elif isinstance(c, str):
                    add_cite("", c)

    else:  # google_search / google_ai_mode
        res = content.get("results")
        res = res if isinstance(res, dict) else content
        for ov in (res.get("ai_overviews") or []):
            for block in ov.get("answer_text", []) or []:
                for frag in block.get("fragments", []) or []:
                    if frag.get("text"):
                        answer_parts.append(frag["text"])
                    for ref in frag.get("references", []) or []:
                        add_cite(ref.get("source", ""), ref.get("url", ""))
            for ref in ov.get("references", []) or []:
                add_cite(ref.get("source", ""), ref.get("url", ""))
        for c in (content.get("citations") or res.get("citations") or []):
            if isinstance(c, dict):
                if c.get("text"):
                    answer_parts.append(str(c["text"]))
                for u in c.get("urls", []) or []:
                    add_cite("", u)

    return "\n".join(p for p in answer_parts if p).strip(), citations


def _root_domain(url_or_domain: str) -> str:
    """Extract a bare registrable-ish domain for comparison."""
    s = (url_or_domain or "").strip().lower()
    if "://" in s:
        s = urllib.parse.urlparse(s).netloc
    else:
        s = s.split("/")[0]
    if s.startswith("www."):
        s = s[4:]
    return s


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #
BAR = "=" * 72
SEP = "-" * 72


def _section_header(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(f"{SEP}")


def render_firmographics(res: dict[str, Any]) -> dict[str, Any]:
    _section_header("1. FIRMOGRAPHICS — company profile (Apollo)")
    summary: dict[str, Any] = {"ok": False, "line": "unavailable"}
    if not res.get("ok"):
        print(f"  (unavailable — {res.get('error', 'no data')})")
        return summary
    o = res["data"]
    if not o:
        print("  (unavailable — no organization match for this domain)")
        return summary
    name = o.get("name") or "?"
    industry = o.get("industry") or "—"
    employees = o.get("estimated_num_employees")
    founded = o.get("founded_year") or "—"
    hq = ", ".join(x for x in [o.get("city"), o.get("state"), o.get("country")] if x) or "—"
    print(f"  Name:        {name}")
    print(f"  Domain:      {o.get('primary_domain') or o.get('website_url') or '—'}")
    print(f"  Industry:    {industry}")
    print(f"  Employees:   {employees if employees is not None else '—'}")
    print(f"  Founded:     {founded}")
    print(f"  HQ:          {hq}")
    print(f"  LinkedIn:    {o.get('linkedin_url') or '—'}")
    about = (o.get("short_description") or "").strip()
    if about:
        print(f"\n  About: {about[:300]}")
    summary["ok"] = True
    emp_s = f"{employees:,} employees" if isinstance(employees, int) else "size n/a"
    summary["line"] = f"{name} — {industry}, {emp_s}, founded {founded}, HQ {hq}"
    return summary


def render_serp(res: dict[str, Any], own_domain: str, query: str) -> dict[str, Any]:
    _section_header(f"2. SEARCH DOMINANCE — Google SERP for \"{query}\" (DataForSEO)")
    summary: dict[str, Any] = {"ok": False, "line": "unavailable", "own_ranks": []}
    if not res.get("ok"):
        print(f"  (unavailable — {res.get('error', 'no data')})")
        return summary
    organic = res["data"]
    if not organic:
        print("  (unavailable — no organic results returned)")
        return summary
    own_root = _root_domain(own_domain)
    own_ranks: list[int] = []
    for it in organic:
        rank = it.get("rank_absolute") or it.get("rank_group") or "?"
        dom = _root_domain(it.get("domain") or "")
        is_own = own_root and (dom == own_root or dom.endswith("." + own_root))
        tag = "  <-- OWN SITE" if is_own else ""
        if is_own and isinstance(rank, int):
            own_ranks.append(rank)
        title = (it.get("title") or "")[:70]
        print(f"  #{str(rank):<3} {title}{tag}")
        print(f"        {dom or it.get('url', '')}")
    summary["ok"] = True
    summary["own_ranks"] = own_ranks
    if own_ranks:
        summary["line"] = (f"owns top-10 slots at rank(s) {', '.join(map(str, own_ranks))} "
                           f"of {len(organic)} organic results")
    else:
        summary["line"] = (f"NOT in the top {len(organic)} organic results for its own category "
                           f"— page is dominated by competitors/marketplaces")
    return summary


def render_reddit(res: dict[str, Any], company: str, limit: int) -> dict[str, Any]:
    _section_header(f"3. SOCIAL SENTIMENT — top Reddit posts for \"{company}\" (Scrape Creators)")
    summary: dict[str, Any] = {"ok": False, "line": "unavailable"}
    if not res.get("ok"):
        print(f"  (unavailable — {res.get('error', 'no data')})")
        return summary
    posts = res["data"]
    if not posts:
        print("  (no Reddit posts found for this company)")
        summary["ok"] = True
        summary["line"] = "no notable Reddit discussion found"
        return summary
    for i, p in enumerate(posts[:limit], 1):
        print(f"  [{i}] {p.get('title', '(no title)')}")
        print(f"      r/{p.get('subreddit', '?')} · {p.get('ups', p.get('score', 0))} upvotes · "
              f"{p.get('num_comments', 0)} comments")
        body = (p.get("selftext") or "").strip().replace("\n", " ")
        if body:
            print(f"      {body[:140]}")
        print(f"      {_reddit_url(p)}")
    summary["ok"] = True
    top = posts[0]
    summary["line"] = (f"{len(posts)} posts; top: \"{(top.get('title') or '')[:80]}\" "
                       f"(r/{top.get('subreddit', '?')}, {top.get('ups', top.get('score', 0))} upvotes)")
    return summary


def render_geo(res: dict[str, Any], company: str, category: str, engine: str) -> dict[str, Any]:
    query = f"best {category} brands 2026"
    _section_header(f"4. AI VISIBILITY (GEO) — \"{query}\" on {engine} (Oxylabs AI Search)")
    summary: dict[str, Any] = {
        "ok": False, "line": "unavailable", "mentioned": None,
        "cited": None, "competitors": [], "query": query,
    }
    if not res.get("ok"):
        print(f"  (unavailable — {res.get('error', 'no data')})")
        return summary
    answer, citations = parse_geo_answer(engine, res["data"])
    if not answer and not citations:
        print("  (unavailable — the engine returned no AI answer for this query)")
        return summary

    company_l = company.lower()
    own_root = _root_domain(res.get("own_domain", ""))
    mentioned = company_l in answer.lower()
    cited_rows = [
        c for c in citations
        if company_l in c["url"].lower()
        or (own_root and own_root in _root_domain(c["url"]))
        or company_l in (c.get("source", "").lower())
    ]
    cited = bool(cited_rows)
    competitor_domains: list[str] = []
    for c in citations:
        d = _root_domain(c["url"])
        if d and d not in competitor_domains and not (own_root and own_root in d):
            competitor_domains.append(d)

    print(f"  Mentioned in AI answer:   {'YES' if mentioned else 'NO'}")
    print(f"  Cited as a source:        {'YES' if cited else 'NO'} ({len(cited_rows)} link(s))")
    print(f"  Total sources cited:      {len(citations)}")
    if competitor_domains:
        print("\n  Competitor / other domains cited by the AI:")
        for i, d in enumerate(competitor_domains[:12], 1):
            print(f"    [{i}] {d}")
    if answer:
        print(f"\n  AI answer (excerpt):\n  {answer[:500].strip()}")

    summary.update({
        "ok": True, "mentioned": mentioned, "cited": cited,
        "competitors": competitor_domains[:12],
    })
    if mentioned or cited:
        summary["line"] = (f"{company} IS {'cited' if cited else 'mentioned'} in {engine}'s answer "
                           f"for \"{query}\" ({len(citations)} sources cited)")
    else:
        summary["line"] = (f"{company} is NOT mentioned or cited in {engine}'s answer "
                           f"for \"{query}\" — {len(citations)} competitor sources are")
    return summary


def render_key_insight(company: str, category: str, engine: str,
                       fg: dict[str, Any], serp: dict[str, Any],
                       reddit: dict[str, Any], geo: dict[str, Any]) -> None:
    print(f"\n{BAR}")
    print("  KEY INSIGHT")
    print(f"{BAR}")
    insights: list[str] = []

    # Flagship: AI-visibility gap.
    if geo.get("ok"):
        if not geo.get("mentioned") and not geo.get("cited"):
            comps = geo.get("competitors") or []
            comp_str = ", ".join(comps[:2]) if comps else "other brands"
            insights.append(
                f"  ⚠️  {company} is NOT cited in {engine}'s answer for "
                f"\"{geo.get('query')}\" — competitors ({comp_str}) ARE. "
                f"High-value GEO opportunity: AI buyers never see {company}."
            )
        elif geo.get("cited"):
            insights.append(
                f"  ✅  {company} IS cited by {engine} for \"{geo.get('query')}\" — "
                f"AI-search visibility is a defensible moat; protect it."
            )
        else:
            insights.append(
                f"  ➖  {company} is mentioned but NOT cited as a source by {engine} for "
                f"\"{geo.get('query')}\" — a citation-quality GEO opportunity."
            )

    # Supporting: classic SERP.
    if serp.get("ok"):
        if serp.get("own_ranks"):
            insights.append(
                f"  🔎  Classic SEO is healthy — {company} owns organic rank(s) "
                f"{', '.join(map(str, serp['own_ranks']))} for \"{category}\", but classic "
                f"rankings no longer guarantee AI-answer visibility (see above)."
            )
        else:
            insights.append(
                f"  🔎  {company} is absent from Google's top organic results for "
                f"\"{category}\" too — both classic and AI search favor competitors."
            )

    if not insights:
        insights.append("  (Insufficient data returned to compute a headline insight — "
                        "one or more sections were unavailable.)")

    for line in insights:
        print(line)
    print()


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _run_section(fn, *fnargs) -> dict[str, Any]:
    try:
        return {"ok": True, "data": fn(*fnargs)}
    except Exception as exc:  # noqa: BLE001 — every section must degrade gracefully
        return {"ok": False, "error": _short_err(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa Brand 360 — one-command company digital X-ray (4 AIsa APIs)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--company", "-c", required=True, help="Company / brand name")
    parser.add_argument("--domain", "-d", required=True, help="Company primary domain (e.g. midea.com)")
    parser.add_argument("--category", required=True,
                        help="Product category for SERP + GEO queries (e.g. 'air conditioner')")
    parser.add_argument("--engine", "-e", default="chatgpt",
                        choices=["chatgpt", "gemini", "perplexity", "google_search", "google_ai_mode"],
                        help="AI engine for the GEO brand-check (default: chatgpt)")
    parser.add_argument("--serp-depth", type=int, default=10, help="Organic SERP depth (default 10)")
    parser.add_argument("--reddit-limit", type=int, default=5, help="Reddit posts to show (default 5)")
    args = parser.parse_args()

    api_key = get_api_key()
    serp_query = f"{args.company} {args.category}"
    geo_query = f"best {args.category} brands 2026"

    print(f"\n{BAR}")
    print(f"  AIsa BRAND 360 — DIGITAL X-RAY")
    print(f"  Company:  {args.company}   ({args.domain})")
    print(f"  Category: {args.category}")
    print(f"  Sources:  Apollo · DataForSEO · Reddit · {args.engine} AI Search")
    print(f"{BAR}")
    print("  Running 4 AIsa calls concurrently (GEO/chatgpt is the slow one, ~40-60s)...")

    # Fire all four concurrently.
    with ThreadPoolExecutor(max_workers=4) as pool:
        f_fg = pool.submit(_run_section, fetch_firmographics, api_key, args.domain, args.company)
        f_serp = pool.submit(_run_section, fetch_serp, api_key, serp_query, args.serp_depth)
        f_reddit = pool.submit(_run_section, fetch_reddit, api_key, args.company)
        f_geo = pool.submit(_run_section, fetch_geo, api_key, geo_query, args.engine)
        r_fg, r_serp, r_reddit, r_geo = (
            f_fg.result(), f_serp.result(), f_reddit.result(), f_geo.result(),
        )
    r_geo["own_domain"] = args.domain  # for citation matching

    fg = render_firmographics(r_fg)
    serp = render_serp(r_serp, args.domain, serp_query)
    reddit = render_reddit(r_reddit, args.company, args.reddit_limit)
    geo = render_geo(r_geo, args.company, args.category, args.engine)
    render_key_insight(args.company, args.category, args.engine, fg, serp, reddit, geo)


if __name__ == "__main__":
    main()
