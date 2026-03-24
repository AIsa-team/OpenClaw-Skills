#!/usr/bin/env python3
"""
OpenClaw Twitter - AIsa API Client
Twitter/X data and OAuth-based posting for autonomous agents.

Read operations use GET with Authorization: Bearer AISA_API_KEY.
Posting uses OAuth relay: POST /twitter/auth_twitter and /twitter/post_twitter
OAuth relay POSTs include aisa_api_key in the JSON body (no Bearer on those POSTs).

Usage (read):
    python twitter_client.py user-info --username <username>
    python twitter_client.py search --query <query> [--type Latest|Top]
    ...

Usage (OAuth post):
    python twitter_client.py authorize [--open-browser]
    python twitter_client.py post --text "Hello" [--media-id <id> ...] [--type <quote|reply>]
    python twitter_client.py status
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
import webbrowser
from typing import Any, Dict, List, Optional


DEFAULT_RELAY_TIMEOUT = 30
TWITTER_MAX_WEIGHT = 280
TWITTER_URL_WEIGHT = 23
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


class TwitterClient:
    """OpenClaw Twitter - Twitter/X API Client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key."""
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set it via environment variable or pass to constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API (read + legacy POST patterns)."""
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-Twitter/1.0",
        }

        request_data = None
        if method == "POST":
            body = data.copy() if data else {}
            body.setdefault("aisa_api_key", self.api_key)
            request_data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"success": False, "error": {"code": str(e.code), "message": error_body}}
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    def _relay_post_json(
        self, path: str, payload: Dict[str, Any], timeout: int
    ) -> Dict[str, Any]:
        """POST JSON to OAuth relay endpoints; aisa_api_key must be in payload."""
        url = f"{self.BASE_URL}{path}"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "OpenClaw-Twitter/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {"code": response.status, "msg": "ok", "data": None}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"code": exc.code, "msg": body or exc.reason, "data": None}
            return {"ok": False, "status": exc.code, "payload": parsed}
        except urllib.error.URLError as exc:
            return {
                "ok": False,
                "status": "NETWORK_ERROR",
                "payload": {"code": 503, "msg": str(exc.reason), "data": None},
            }

    def relay_authorize(
        self, timeout: int
    ) -> Dict[str, Any]:
        """Request OAuth authorization URL from AIsa relay."""
        payload: Dict[str, Any] = {"aisa_api_key": self.api_key}
        return self._relay_post_json("/twitter/auth_twitter", payload, timeout)

    def relay_post(
        self,
        text: str,
        media_ids: Optional[List[str]],
        timeout: int,
        quote_tweet_id: Optional[str] = None,
        post_type: str = "quote",
    ) -> Dict[str, Any]:
        """Publish a post via OAuth-backed relay."""
        payload: Dict[str, Any] = {
            "aisa_api_key": self.api_key,
            "content": text,
            "type": post_type,
        }
        if media_ids:
            payload["media_ids"] = media_ids
        if quote_tweet_id:
            payload["quote_tweet_id"] = quote_tweet_id
        return self._relay_post_json("/twitter/post_twitter", payload, timeout)

    # ==================== User Read APIs ====================

    def user_info(self, username: str) -> Dict[str, Any]:
        """Get Twitter user information by username."""
        return self._request("GET", "/twitter/user/info", params={"userName": username})

    def user_about(self, username: str) -> Dict[str, Any]:
        """Get user profile about page (account country, verification, etc.)."""
        return self._request("GET", "/twitter/user_about", params={"userName": username})

    def batch_user_info(self, user_ids: str) -> Dict[str, Any]:
        """Batch get user info by comma-separated user IDs."""
        return self._request("GET", "/twitter/user/batch_info_by_ids", params={"userIds": user_ids})

    def user_tweets(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get latest tweets from a specific user."""
        return self._request("GET", "/twitter/user/last_tweets", params={"userName": username, "cursor": cursor})

    def user_mentions(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get mentions of a user."""
        return self._request("GET", "/twitter/user/mentions", params={"userName": username, "cursor": cursor})

    def followers(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get user followers."""
        return self._request("GET", "/twitter/user/followers", params={"userName": username, "cursor": cursor})

    def followings(self, username: str, cursor: str = None) -> Dict[str, Any]:
        """Get user followings."""
        return self._request("GET", "/twitter/user/followings", params={"userName": username, "cursor": cursor})

    def verified_followers(self, user_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get verified followers of a user (requires user_id, not username)."""
        return self._request("GET", "/twitter/user/verifiedFollowers", params={"user_id": user_id, "cursor": cursor})

    def check_follow_relationship(self, source: str, target: str) -> Dict[str, Any]:
        """Check follow relationship between two users."""
        return self._request(
            "GET",
            "/twitter/user/check_follow_relationship",
            params={"source_user_name": source, "target_user_name": target},
        )

    def user_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search for Twitter users by keyword."""
        return self._request("GET", "/twitter/user/search", params={"query": query, "cursor": cursor})

    # ==================== Tweet Read APIs ====================

    def search(self, query: str, query_type: str = "Latest", cursor: str = None) -> Dict[str, Any]:
        """Search for tweets matching a query."""
        return self._request(
            "GET",
            "/twitter/tweet/advanced_search",
            params={"query": query, "queryType": query_type, "cursor": cursor},
        )

    def tweet_detail(self, tweet_ids: str) -> Dict[str, Any]:
        """Get detailed information about tweets by IDs (comma-separated)."""
        return self._request("GET", "/twitter/tweets", params={"tweet_ids": tweet_ids})

    def tweet_replies(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get replies to a tweet."""
        return self._request("GET", "/twitter/tweet/replies", params={"tweetId": tweet_id, "cursor": cursor})

    def tweet_quotes(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get quotes of a tweet."""
        return self._request("GET", "/twitter/tweet/quotes", params={"tweetId": tweet_id, "cursor": cursor})

    def tweet_retweeters(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get retweeters of a tweet."""
        return self._request("GET", "/twitter/tweet/retweeters", params={"tweetId": tweet_id, "cursor": cursor})

    def tweet_thread(self, tweet_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get the full thread context of a tweet."""
        return self._request("GET", "/twitter/tweet/thread_context", params={"tweetId": tweet_id, "cursor": cursor})

    def article(self, tweet_id: str) -> Dict[str, Any]:
        """Get article content by tweet ID."""
        return self._request("GET", "/twitter/article", params={"tweet_id": tweet_id})

    # ==================== Trends, Lists, Communities, Spaces ====================

    def trends(self, woeid: int = 1) -> Dict[str, Any]:
        """Get current Twitter trending topics by WOEID (1 = worldwide)."""
        return self._request("GET", "/twitter/trends", params={"woeid": woeid})

    def list_members(self, list_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get members of a Twitter list."""
        return self._request("GET", "/twitter/list/members", params={"list_id": list_id, "cursor": cursor})

    def list_followers(self, list_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get followers of a Twitter list."""
        return self._request("GET", "/twitter/list/followers", params={"list_id": list_id, "cursor": cursor})

    def community_info(self, community_id: str) -> Dict[str, Any]:
        """Get community info by ID."""
        return self._request("GET", "/twitter/community/info", params={"community_id": community_id})

    def community_members(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community members."""
        return self._request(
            "GET", "/twitter/community/members", params={"community_id": community_id, "cursor": cursor}
        )

    def community_moderators(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community moderators."""
        return self._request(
            "GET", "/twitter/community/moderators", params={"community_id": community_id, "cursor": cursor}
        )

    def community_tweets(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community tweets."""
        return self._request(
            "GET", "/twitter/community/tweets", params={"community_id": community_id, "cursor": cursor}
        )

    def community_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search tweets from all communities."""
        return self._request(
            "GET",
            "/twitter/community/get_tweets_from_all_community",
            params={"query": query, "cursor": cursor},
        )

    def space_detail(self, space_id: str) -> Dict[str, Any]:
        """Get Space detail by ID."""
        return self._request("GET", "/twitter/spaces/detail", params={"space_id": space_id})


def _relay_timeout() -> int:
    return int(os.environ.get("TWITTER_RELAY_TIMEOUT", str(DEFAULT_RELAY_TIMEOUT)))


def twitter_char_weight(ch: str) -> int:
    if unicodedata.east_asian_width(ch) in {"W", "F"}:
        return 2
    if unicodedata.category(ch).startswith("M"):
        return 0
    return 1


def twitter_weight_len(text: str) -> int:
    total = 0
    idx = 0
    for matched in URL_PATTERN.finditer(text):
        start, end = matched.span()
        while idx < start:
            total += twitter_char_weight(text[idx])
            idx += 1
        total += TWITTER_URL_WEIGHT
        idx = end

    while idx < len(text):
        total += twitter_char_weight(text[idx])
        idx += 1
    return total


def split_by_twitter_weight(text: str, max_len: int) -> List[str]:
    parts: List[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        if twitter_weight_len(candidate) <= max_len:
            current = candidate
            continue
        if current:
            parts.append(current)
        current = ch
    if current:
        parts.append(current)
    return parts


def split_text_for_twitter(text: str, max_len: int = TWITTER_MAX_WEIGHT) -> List[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if twitter_weight_len(normalized) <= max_len:
        return [normalized]

    words = normalized.split()
    chunks: List[str] = []
    current = ""
    for word in words:
        if twitter_weight_len(word) > max_len:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(split_by_twitter_weight(word, max_len))
            continue

        candidate = word if not current else f"{current} {word}"
        if twitter_weight_len(candidate) <= max_len:
            current = candidate
        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)
    return chunks


def extract_tweet_id(result: Dict[str, Any]) -> Optional[str]:
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, dict):
        return None
    tweet_id = data.get("tweet_id")
    return str(tweet_id) if tweet_id else None


def publish_chunks(
    client: TwitterClient,
    chunks: List[str],
    timeout: int,
    media_ids: Optional[List[str]] = None,
    initial_quote_tweet_id: Optional[str] = None,
    post_type: str = "quote",
) -> Dict[str, Any]:
    should_thread = len(chunks) > 1
    previous_tweet_id = initial_quote_tweet_id
    publish_results = []

    for index, chunk in enumerate(chunks):
        current_media_ids = media_ids if index == 0 and media_ids else None
        result = client.relay_post(
            chunk,
            current_media_ids,
            timeout,
            quote_tweet_id=previous_tweet_id,
            post_type=post_type,
        )
        publish_results.append(
            {
                "index": index + 1,
                "content": chunk,
                "quote_tweet_id": previous_tweet_id,
                "result": result,
            }
        )

        if result.get("ok") is False or result.get("code") != 200:
            return {
                "ok": False,
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "results": publish_results,
            }

        latest_tweet_id = extract_tweet_id(result)
        if not latest_tweet_id:
            return {
                "ok": False,
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "error": "Missing tweet_id in relay response.",
                "results": publish_results,
            }
        previous_tweet_id = latest_tweet_id

    return {
        "ok": True,
        "is_thread": should_thread,
        "total_chunks": len(chunks),
        "results": publish_results,
    }


def command_authorize(client: TwitterClient, args: argparse.Namespace) -> None:
    timeout = _relay_timeout()
    result = client.relay_authorize(timeout)

    if result.get("ok") is False:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    auth_url = (result.get("data") or {}).get("auth_url")
    output = {
        "ok": result.get("code") == 200 and bool(auth_url),
        "authorization_url": auth_url,
        "raw_response": result,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if output["ok"] and args.open_browser and auth_url:
        webbrowser.open(auth_url)

    if not output["ok"]:
        sys.exit(1)


def command_post(client: TwitterClient, args: argparse.Namespace) -> None:
    """Split oversized content locally, then publish chunks through the relay."""
    timeout = _relay_timeout()
    chunks = split_text_for_twitter(args.text)
    if not chunks:
        print(json.dumps({"ok": False, "error": "Post content must not be empty."}, indent=2, ensure_ascii=False))
        sys.exit(1)
    output = publish_chunks(
        client,
        chunks,
        timeout,
        media_ids=getattr(args, "media_id", None),
        post_type=args.post_type,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if not output["ok"]:
        sys.exit(1)


def command_status(client: TwitterClient, args: argparse.Namespace) -> None:
    del args
    response = {
        "ok": True,
        "base_url": TwitterClient.BASE_URL,
        "relay_timeout_seconds": _relay_timeout(),
        "oauth_endpoints": ["/twitter/auth_twitter", "/twitter/post_twitter"],
        "note": "OAuth relay POSTs send aisa_api_key in JSON body (no Authorization header).",
    }
    print(json.dumps(response, indent=2, ensure_ascii=False))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Twitter - Twitter/X data and OAuth posting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # ---- User Read Commands ----

    p = subparsers.add_parser("user-info", help="Get user information")
    p.add_argument("--username", "-u", required=True)

    p = subparsers.add_parser("user-about", help="Get user profile about")
    p.add_argument("--username", "-u", required=True)

    p = subparsers.add_parser("batch-users", help="Batch get users by IDs")
    p.add_argument("--user-ids", required=True, help="Comma-separated user IDs")

    p = subparsers.add_parser("tweets", help="Get user's latest tweets")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("mentions", help="Get user mentions")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("followers", help="Get user followers")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("followings", help="Get user followings")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("verified-followers", help="Get verified followers")
    p.add_argument("--user-id", required=True, help="User ID (not username)")
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("check-follow", help="Check follow relationship")
    p.add_argument("--source", required=True, help="Source username")
    p.add_argument("--target", required=True, help="Target username")

    # ---- Search & Discovery ----

    p = subparsers.add_parser("search", help="Search tweets")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--type", "-t", choices=["Latest", "Top"], default="Latest")
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("user-search", help="Search users")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("trends", help="Get trending topics")
    p.add_argument("--woeid", "-w", type=int, default=1)

    # ---- Tweet Detail Commands ----

    p = subparsers.add_parser("detail", help="Get tweets by IDs")
    p.add_argument("--tweet-ids", required=True, help="Comma-separated tweet IDs")

    p = subparsers.add_parser("replies", help="Get tweet replies")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("quotes", help="Get tweet quotes")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("retweeters", help="Get tweet retweeters")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("thread", help="Get tweet thread context")
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("article", help="Get article by tweet ID")
    p.add_argument("--tweet-id", required=True)

    # ---- List Commands ----

    p = subparsers.add_parser("list-members", help="Get list members")
    p.add_argument("--list-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("list-followers", help="Get list followers")
    p.add_argument("--list-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    # ---- Community Commands ----

    p = subparsers.add_parser("community-info", help="Get community info")
    p.add_argument("--community-id", required=True)

    p = subparsers.add_parser("community-members", help="Get community members")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-moderators", help="Get community moderators")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-tweets", help="Get community tweets")
    p.add_argument("--community-id", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    p = subparsers.add_parser("community-search", help="Search all community tweets")
    p.add_argument("--query", "-q", required=True)
    p.add_argument("--cursor", help="Pagination cursor")

    # ---- Spaces ----

    p = subparsers.add_parser("space-detail", help="Get Space detail")
    p.add_argument("--space-id", required=True)

    # ---- OAuth posting (relay) ----

    p = subparsers.add_parser("authorize", help="Request OAuth authorization URL from AIsa")
    p.add_argument("--open-browser", action="store_true", help="Open the authorization URL")
    p.set_defaults(_handler="authorize")

    p = subparsers.add_parser("post", help="Publish a post via OAuth-backed relay")
    p.add_argument("--text", "-t", required=True, help="Post content")
    p.add_argument(
        "--media-id",
        action="append",
        help="Media ID to attach (repeat for multiple)",
    )
    p.add_argument(
        "--type",
        dest="post_type",
        choices=["quote", "reply"],
        default="quote",
        help="Post type. Defaults to quote. Only use reply when the user explicitly asks for a reply.",
    )
    p.set_defaults(_handler="post")

    p = subparsers.add_parser("status", help="Show OAuth relay client configuration")
    p.set_defaults(_handler="status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = getattr(args, "_handler", None)

    if handler in ("authorize", "post", "status"):
        try:
            client = TwitterClient()
        except ValueError as e:
            print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
            sys.exit(1)
        if handler == "authorize":
            command_authorize(client, args)
        elif handler == "post":
            command_post(client, args)
        else:
            command_status(client, args)
        return

    try:
        client = TwitterClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)

    result = None
    cmd = args.command

    if cmd == "user-info":
        result = client.user_info(args.username)
    elif cmd == "user-about":
        result = client.user_about(args.username)
    elif cmd == "batch-users":
        result = client.batch_user_info(args.user_ids)
    elif cmd == "tweets":
        result = client.user_tweets(args.username, getattr(args, "cursor", None))
    elif cmd == "mentions":
        result = client.user_mentions(args.username, getattr(args, "cursor", None))
    elif cmd == "followers":
        result = client.followers(args.username, getattr(args, "cursor", None))
    elif cmd == "followings":
        result = client.followings(args.username, getattr(args, "cursor", None))
    elif cmd == "verified-followers":
        result = client.verified_followers(args.user_id, getattr(args, "cursor", None))
    elif cmd == "check-follow":
        result = client.check_follow_relationship(args.source, args.target)
    elif cmd == "search":
        result = client.search(args.query, args.type, getattr(args, "cursor", None))
    elif cmd == "user-search":
        result = client.user_search(args.query, getattr(args, "cursor", None))
    elif cmd == "trends":
        result = client.trends(args.woeid)
    elif cmd == "detail":
        result = client.tweet_detail(args.tweet_ids)
    elif cmd == "replies":
        result = client.tweet_replies(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "quotes":
        result = client.tweet_quotes(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "retweeters":
        result = client.tweet_retweeters(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "thread":
        result = client.tweet_thread(args.tweet_id, getattr(args, "cursor", None))
    elif cmd == "article":
        result = client.article(args.tweet_id)
    elif cmd == "list-members":
        result = client.list_members(args.list_id, getattr(args, "cursor", None))
    elif cmd == "list-followers":
        result = client.list_followers(args.list_id, getattr(args, "cursor", None))
    elif cmd == "community-info":
        result = client.community_info(args.community_id)
    elif cmd == "community-members":
        result = client.community_members(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-moderators":
        result = client.community_moderators(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-tweets":
        result = client.community_tweets(args.community_id, getattr(args, "cursor", None))
    elif cmd == "community-search":
        result = client.community_search(args.query, getattr(args, "cursor", None))
    elif cmd == "space-detail":
        result = client.space_detail(args.space_id)

    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
