#!/usr/bin/env python3
"""
AIsa Social Listening — Python CLI Client
=========================================

Monitor public social conversation across Reddit, Instagram, and Pinterest via
the AIsa Scrape Creators relay. Search Reddit for a topic, pull a subreddit's
recent posts and stats, read an Instagram profile, or scan Pinterest pins for
a theme.

Requires the AISA_API_KEY environment variable.

Usage:
    python3 scrapecreators_client.py reddit-search    --query "ai agents"
    python3 scrapecreators_client.py reddit-subreddit --subreddit artificial
    python3 scrapecreators_client.py subreddit-stats  --subreddit artificial
    python3 scrapecreators_client.py instagram        --handle nasa
    python3 scrapecreators_client.py pinterest        --query "healthy recipes"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
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


def aisa_get(api_key: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
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
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"API error {e.code} on {path}: {body_text}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error on {path}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _reddit_url(post: dict[str, Any]) -> str:
    pl = post.get("permalink") or ""
    if pl.startswith("http"):
        return pl
    if pl:
        return f"https://www.reddit.com{pl}"
    return post.get("url") or ""


def _print_reddit_posts(posts: list[dict[str, Any]], limit: int) -> None:
    for i, p in enumerate(posts[:limit], 1):
        print(f"  [{i}] {p.get('title', '(no title)')}")
        print(f"      r/{p.get('subreddit', '?')} · u/{p.get('author', '?')} · "
              f"{p.get('ups', p.get('score', 0))} upvotes · {p.get('num_comments', 0)} comments")
        body = (p.get("selftext") or "").strip().replace("\n", " ")
        if body:
            print(f"      {body[:160]}")
        print(f"      {_reddit_url(p)}")
        print()


def cmd_reddit_search(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_get(api_key, "/reddit/search",
                    {"query": args.query, "sort": args.sort, "timeframe": args.timeframe})
    posts = data.get("posts") or []
    print(f"\n{'='*66}")
    print(f"  Reddit Search — \"{args.query}\"  ({len(posts)} posts)")
    print(f"{'='*66}\n")
    _print_reddit_posts(posts, args.limit)


def cmd_reddit_subreddit(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_get(api_key, "/reddit/subreddit",
                    {"subreddit": args.subreddit, "sort": args.sort, "timeframe": args.timeframe})
    posts = data.get("posts") or []
    print(f"\n{'='*66}")
    print(f"  r/{args.subreddit} — recent posts ({len(posts)})")
    print(f"{'='*66}\n")
    _print_reddit_posts(posts, args.limit)


def cmd_subreddit_stats(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    d = aisa_get(api_key, "/reddit/subreddit/details", {"subreddit": args.subreddit})
    print(f"\n{'='*66}")
    print(f"  r/{d.get('display_name', args.subreddit)} — community stats")
    print(f"{'='*66}\n")
    print(f"  Subscribers:        {d.get('subscribers') or d.get('num_subscribers') or '—'}")
    print(f"  Weekly active:      {d.get('weekly_active_users', '—')}")
    print(f"  Weekly posts:       {d.get('weekly_contributions', '—')}")
    if d.get("public_description"):
        print(f"\n  About: {d['public_description'][:300]}")
    print()


def cmd_instagram(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_get(api_key, "/instagram/profile", {"handle": args.handle})
    u = (data.get("data") or {}).get("user") or {}
    if not u:
        print("No profile data returned.")
        return
    followers = (u.get("edge_followed_by") or {}).get("count")
    following = (u.get("edge_follow") or {}).get("count")
    posts = (u.get("edge_owner_to_timeline_media") or {}).get("count")
    print(f"\n{'='*66}")
    print(f"  Instagram — @{u.get('username', args.handle)}")
    print(f"{'='*66}\n")
    print(f"  Name:       {u.get('full_name', '—')}"
          f"{'  (verified)' if u.get('is_verified') else ''}")
    print(f"  Followers:  {followers if followers is not None else '—'}")
    print(f"  Following:  {following if following is not None else '—'}")
    print(f"  Posts:      {posts if posts is not None else '—'}")
    if u.get("category_name") or u.get("business_category_name"):
        print(f"  Category:   {u.get('category_name') or u.get('business_category_name')}")
    bio = (u.get("biography") or "").strip()
    if bio:
        print(f"\n  Bio: {bio[:300]}")
    ext = u.get("external_url")
    if ext:
        print(f"  Link: {ext}")
    print()


def cmd_pinterest(args: argparse.Namespace) -> None:
    api_key = get_api_key()
    data = aisa_get(api_key, "/pinterest/search", {"query": args.query})
    pins = data.get("pins") or []
    printable = [p for p in pins if isinstance(p.get("title"), str) and p.get("title")]
    print(f"\n{'='*66}")
    print(f"  Pinterest — \"{args.query}\"  ({len(printable)} pins with titles)")
    print(f"{'='*66}\n")
    for i, p in enumerate(printable[: args.limit], 1):
        title = p.get("grid_title") or p.get("title") or "(untitled)"
        print(f"  [{i}] {title}")
        desc = (p.get("description") or "").strip().replace("\n", " ")
        if desc:
            print(f"      {desc[:140]}")
        pinner = p.get("pinner") or {}
        pinner_name = pinner.get("username") if isinstance(pinner, dict) else pinner
        if pinner_name:
            print(f"      by @{pinner_name}")
        if p.get("url"):
            print(f"      {p['url']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIsa Social Listening (Scrape Creators)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_rs = sub.add_parser("reddit-search", help="Search Reddit posts by keyword")
    p_rs.add_argument("--query", "-q", required=True)
    p_rs.add_argument("--sort", default="relevance", choices=["relevance", "hot", "top", "new", "comments"])
    p_rs.add_argument("--timeframe", default="all", choices=["hour", "day", "week", "month", "year", "all"])
    p_rs.add_argument("--limit", "-n", type=int, default=10)
    p_rs.set_defaults(func=cmd_reddit_search)

    p_rr = sub.add_parser("reddit-subreddit", help="Recent posts from a subreddit")
    p_rr.add_argument("--subreddit", "-s", required=True)
    p_rr.add_argument("--sort", default="hot", choices=["hot", "top", "new", "rising"])
    p_rr.add_argument("--timeframe", default="week", choices=["hour", "day", "week", "month", "year", "all"])
    p_rr.add_argument("--limit", "-n", type=int, default=10)
    p_rr.set_defaults(func=cmd_reddit_subreddit)

    p_ss = sub.add_parser("subreddit-stats", help="Community size / activity stats")
    p_ss.add_argument("--subreddit", "-s", required=True)
    p_ss.set_defaults(func=cmd_subreddit_stats)

    p_ig = sub.add_parser("instagram", help="Public Instagram profile snapshot")
    p_ig.add_argument("--handle", "-u", required=True, help="Username without @")
    p_ig.set_defaults(func=cmd_instagram)

    p_pin = sub.add_parser("pinterest", help="Search Pinterest pins by theme")
    p_pin.add_argument("--query", "-q", required=True)
    p_pin.add_argument("--limit", "-n", type=int, default=10)
    p_pin.set_defaults(func=cmd_pinterest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
