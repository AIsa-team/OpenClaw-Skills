#!/usr/bin/env python3
"""
AIsa GEO Visibility — Python CLI Client
=======================================

Query real AI answer engines (ChatGPT, Gemini, Perplexity, Google AI
Overviews, Google AI Mode) via the AIsa Oxylabs AI Search endpoint and
inspect the generated answer text plus the source URLs each engine cites.

This powers "GEO / AEO" (Generative Engine Optimization) workflows: check
whether a brand, product, or topic shows up in AI answers and who gets cited.

Requires the AISA_API_KEY environment variable.

Usage:
    python3 geo_client.py ask   --source google_search --query "best CRM for startups"
    python3 geo_client.py ask   --source chatgpt --query "What is Anthropic known for?"
    python3 geo_client.py brand --brand "Anthropic" --query "leading AI safety companies"
    python3 geo_client.py brand --brand "Notion" --query "best note taking apps" --source gemini
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

AISA_BASE = "https://api.aisa.one/apis/v1"
AI_SEARCH_PATH = "/oxylabs/ai-search"

SOURCES = ["google_search", "google_ai_mode", "chatgpt", "gemini", "perplexity"]
# Sources that take `prompt`; the rest take `query`.
PROMPT_SOURCES = {"chatgpt", "gemini", "perplexity"}


def get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY", "")
    if not key:
        print("Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


def aisa_post(api_key: str, path: str, body: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"API error {e.code} on {path}: {body_text}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error on {path}: {e.reason}", file=sys.stderr)
        print("AI sources (chatgpt/gemini/perplexity) can take 40-60s; try again.", file=sys.stderr)
        sys.exit(1)


def build_body(source: str, query: str, geo: str) -> dict[str, Any]:
    body: dict[str, Any] = {"source": source, "parse": True}
    if geo:
        body["geo_location"] = geo
    if source in PROMPT_SOURCES:
        body["prompt"] = query
        if source == "chatgpt":
            body["search"] = True
    else:
        body["query"] = query
        body["render"] = "html"
    return body


def _first_result_content(data: dict[str, Any]) -> dict[str, Any]:
    results = data.get("results")
    if isinstance(results, list) and results:
        content = results[0].get("content")
        if isinstance(content, dict):
            return content
    return {}


def parse_answer(source: str, data: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
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

    # chatgpt / gemini -> response_text + citations[]
    if source in ("chatgpt", "gemini"):
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

    # perplexity -> answer + top_sources/sources_results
    elif source == "perplexity":
        txt = content.get("response_text") or content.get("answer") or content.get("text") or ""
        if txt:
            answer_parts.append(str(txt))
        for key in ("top_sources", "sources_results", "sources", "citations"):
            for c in content.get(key, []) or []:
                if isinstance(c, dict):
                    add_cite(c.get("title") or c.get("source") or "", c.get("url") or c.get("link") or "")
                elif isinstance(c, str):
                    add_cite("", c)

    # google_search / google_ai_mode -> nested content.results
    else:
        res = content.get("results")
        res = res if isinstance(res, dict) else content
        # Google AI Overviews
        for ov in (res.get("ai_overviews") or []):
            for block in ov.get("answer_text", []) or []:
                for frag in block.get("fragments", []) or []:
                    if frag.get("text"):
                        answer_parts.append(frag["text"])
                    for ref in frag.get("references", []) or []:
                        add_cite(ref.get("source", ""), ref.get("url", ""))
            for bl in ov.get("bullet_list", []) or []:
                for pt in bl.get("points", []) or []:
                    if pt.get("text"):
                        answer_parts.append("- " + pt["text"])
                    for ref in pt.get("references", []) or []:
                        add_cite(ref.get("source", ""), ref.get("url", ""))
            for ref in ov.get("references", []) or []:
                add_cite(ref.get("source", ""), ref.get("url", ""))
        # Google AI Mode -> content.citations[]{text, urls[]}
        for c in (content.get("citations") or res.get("citations") or []):
            if isinstance(c, dict):
                if c.get("text"):
                    answer_parts.append(str(c["text"]))
                for u in c.get("urls", []) or []:
                    add_cite("", u)

    return "\n".join(p for p in answer_parts if p).strip(), citations


def print_answer(source: str, query: str, answer: str, citations: list[dict[str, str]]) -> None:
    print(f"\n{'='*66}")
    print(f"  AI Engine: {source}")
    print(f"  Query:     {query}")
    print(f"{'='*66}\n")
    if answer:
        print("Answer:\n")
        print(answer[:4000])
    else:
        print("(No AI answer returned for this query/engine — the engine may not")
        print(" have shown an AI answer for this term.)")
    print(f"\nCited sources ({len(citations)}):")
    if citations:
        for i, c in enumerate(citations, 1):
            label = f" — {c['source']}" if c.get("source") else ""
            print(f"  [{i}] {c['url']}{label}")
    else:
        print("  (none)")
    print()


def cmd_ask(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body = build_body(args.source, args.query, args.geo)
    data = aisa_post(api_key, AI_SEARCH_PATH, body)
    answer, citations = parse_answer(args.source, data)
    print_answer(args.source, args.query, answer, citations)


def cmd_brand(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body = build_body(args.source, args.query, args.geo)
    data = aisa_post(api_key, AI_SEARCH_PATH, body)
    answer, citations = parse_answer(args.source, data)

    brand = args.brand
    brand_l = brand.lower()
    mentioned = brand_l in answer.lower()
    cited_rows = [c for c in citations if brand_l in c["url"].lower() or brand_l in (c.get("source", "").lower())]

    print(f"\n{'='*66}")
    print(f"  GEO Visibility Check")
    print(f"{'='*66}")
    print(f"  Brand:   {brand}")
    print(f"  Query:   {args.query}")
    print(f"  Engine:  {args.source}")
    print(f"{'='*66}\n")
    print(f"  Mentioned in AI answer:   {'YES' if mentioned else 'NO'}")
    print(f"  Cited as a source:        {'YES' if cited_rows else 'NO'} ({len(cited_rows)} link(s))")
    print(f"  Total sources cited:      {len(citations)}")
    if cited_rows:
        print("\n  Your citations:")
        for c in cited_rows:
            print(f"    - {c['url']}")
    print("\n  All cited sources (competitor visibility):")
    for i, c in enumerate(citations[:20], 1):
        label = f" — {c['source']}" if c.get("source") else ""
        print(f"    [{i}] {c['url']}{label}")
    print_answer(args.source, args.query, answer, citations)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa GEO Visibility — query AI answer engines and inspect citations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask", help="Query one AI engine and show its answer + citations")
    p_ask.add_argument("--query", "-q", required=True, help="Question / search term")
    p_ask.add_argument("--source", "-s", default="google_search", choices=SOURCES)
    p_ask.add_argument("--geo", default="United States", help="Country-level geo (e.g. 'United States')")
    p_ask.set_defaults(func=cmd_ask)

    p_brand = sub.add_parser("brand", help="Check if a brand appears/is cited in an AI answer")
    p_brand.add_argument("--brand", "-b", required=True, help="Brand or product name to look for")
    p_brand.add_argument("--query", "-q", required=True, help="Question a user might ask an AI engine")
    p_brand.add_argument("--source", "-s", default="google_search", choices=SOURCES)
    p_brand.add_argument("--geo", default="United States", help="Country-level geo")
    p_brand.set_defaults(func=cmd_brand)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
