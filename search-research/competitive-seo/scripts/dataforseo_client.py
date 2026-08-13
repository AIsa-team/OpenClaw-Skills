#!/usr/bin/env python3
"""
AIsa Competitive SEO — Python CLI Client
========================================

Live Google SERP rankings, keyword ideas, and search-volume/CPC data via the
AIsa DataForSEO relay. Use it to see who ranks for a term, discover related
keywords with volume, and pull ad economics (CPC + competition) for a list of
keywords.

Requires the AISA_API_KEY environment variable.

Usage:
    python3 dataforseo_client.py serp     --keyword "ai agents" --depth 10
    python3 dataforseo_client.py keywords --seed "ai agents" --limit 15
    python3 dataforseo_client.py volume   --keywords "ai agents,llm,rag pipeline"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

AISA_BASE = "https://api.aisa.one/apis/v1"


def get_api_key() -> str:
    key = os.environ.get("AISA_API_KEY", "")
    if not key:
        print("Error: AISA_API_KEY environment variable is not set.", file=sys.stderr)
        print("Get your key at https://aisa.one", file=sys.stderr)
        sys.exit(1)
    return key


def aisa_post(api_key: str, path: str, body: Any) -> dict[str, Any]:
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"API error {e.code} on {path}: {body_text}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error on {path}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _task_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Unwrap DataForSEO's tasks[].result[].items[] envelope; check status."""
    if data.get("status_code") not in (20000, None):
        print(f"DataForSEO error {data.get('status_code')}: {data.get('status_message')}",
              file=sys.stderr)
    tasks = data.get("tasks") or []
    if not tasks:
        return []
    t0 = tasks[0]
    if t0.get("status_code") and t0["status_code"] != 20000:
        print(f"Task error {t0['status_code']}: {t0.get('status_message')}", file=sys.stderr)
    results = t0.get("result") or []
    if not results:
        return []
    return results[0].get("items") or []


def _fmt_num(n: Any) -> str:
    if n is None:
        return "—"
    try:
        return f"{int(n):,}"
    except (ValueError, TypeError):
        return str(n)


def cmd_serp(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body = [{
        "keyword": args.keyword,
        "location_name": args.location,
        "language_name": args.language,
        "depth": args.depth,
    }]
    data = aisa_post(api_key, "/dataforseo/serp/google/organic/live/advanced", body)
    items = _task_result(data)
    organic = [i for i in items if i.get("type") == "organic"]

    print(f"\n{'='*66}")
    print(f"  Google SERP — \"{args.keyword}\" ({args.location})")
    print(f"{'='*66}\n")
    for it in organic[: args.depth]:
        rank = it.get("rank_absolute") or it.get("rank_group")
        print(f"  #{rank:<3} {it.get('title', '')}")
        print(f"        {it.get('url', '')}")
        print(f"        domain: {it.get('domain', '')}")
        if it.get("description"):
            print(f"        {it['description'][:140]}")
        print()

    features = sorted({i.get("type") for i in items if i.get("type") != "organic"})
    if features:
        print(f"  SERP features present: {', '.join(features)}\n")


def cmd_keywords(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    body = [{
        "keywords": [args.seed],
        "location_name": args.location,
        "language_name": args.language,
        "limit": args.limit,
    }]
    data = aisa_post(api_key, "/dataforseo/dataforseo_labs/google/keyword_ideas/live", body)
    items = _task_result(data)

    print(f"\n{'='*66}")
    print(f"  Keyword Ideas — seed \"{args.seed}\" ({args.location})")
    print(f"{'='*66}\n")
    print(f"  {'Keyword':<40} {'Volume':>10} {'CPC':>8} {'Comp':>6}")
    print(f"  {'-'*40} {'-'*10} {'-'*8} {'-'*6}")
    for it in items[: args.limit]:
        ki = it.get("keyword_info") or {}
        kw = (it.get("keyword") or "")[:40]
        vol = _fmt_num(ki.get("search_volume"))
        cpc = ki.get("cpc")
        cpc_s = f"${cpc:.2f}" if isinstance(cpc, (int, float)) else "—"
        comp = ki.get("competition")
        comp_s = f"{comp:.2f}" if isinstance(comp, (int, float)) else "—"
        print(f"  {kw:<40} {vol:>10} {cpc_s:>8} {comp_s:>6}")
    print()


def cmd_volume(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    body = [{
        "keywords": keywords,
        "location_name": args.location,
        "language_name": args.language,
    }]
    data = aisa_post(api_key, "/dataforseo/keywords_data/google_ads/search_volume/live", body)
    items = _task_result(data)

    print(f"\n{'='*66}")
    print(f"  Search Volume & CPC ({args.location})")
    print(f"{'='*66}\n")
    print(f"  {'Keyword':<40} {'Volume':>10} {'CPC':>8} {'Comp':>6}")
    print(f"  {'-'*40} {'-'*10} {'-'*8} {'-'*6}")
    for it in items:
        kw = (it.get("keyword") or "")[:40]
        vol = _fmt_num(it.get("search_volume"))
        cpc = it.get("cpc")
        cpc_s = f"${cpc:.2f}" if isinstance(cpc, (int, float)) else "—"
        comp = it.get("competition")
        comp_s = f"{comp:.2f}" if isinstance(comp, (int, float)) else "—"
        print(f"  {kw:<40} {vol:>10} {cpc_s:>8} {comp_s:>6}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa Competitive SEO (DataForSEO)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_serp = sub.add_parser("serp", help="Live Google organic SERP for a keyword")
    p_serp.add_argument("--keyword", "-k", required=True)
    p_serp.add_argument("--depth", "-d", type=int, default=10, help="Number of results")
    p_serp.add_argument("--location", default="United States")
    p_serp.add_argument("--language", default="English")
    p_serp.set_defaults(func=cmd_serp)

    p_kw = sub.add_parser("keywords", help="Keyword ideas with volume/CPC from a seed")
    p_kw.add_argument("--seed", "-s", required=True)
    p_kw.add_argument("--limit", "-n", type=int, default=15)
    p_kw.add_argument("--location", default="United States")
    p_kw.add_argument("--language", default="English")
    p_kw.set_defaults(func=cmd_keywords)

    p_vol = sub.add_parser("volume", help="Search volume/CPC/competition for keywords")
    p_vol.add_argument("--keywords", "-k", required=True, help="Comma-separated keywords")
    p_vol.add_argument("--location", default="United States")
    p_vol.add_argument("--language", default="English")
    p_vol.set_defaults(func=cmd_volume)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
