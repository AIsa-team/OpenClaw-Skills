#!/usr/bin/env python3
"""
OpenClaw Twitter - AIsa API Client
Twitter/X data and automation for autonomous agents.

Usage:
    python twitter_client.py user-info --username <username>
    python twitter_client.py user-about --username <username>
    python twitter_client.py tweets --username <username>
    python twitter_client.py mentions --username <username>
    python twitter_client.py followers --username <username>
    python twitter_client.py followings --username <username>
    python twitter_client.py verified-followers --user-id <id>
    python twitter_client.py check-follow --source <user> --target <user>
    python twitter_client.py search --query <query> [--type Latest|Top]
    python twitter_client.py user-search --query <query>
    python twitter_client.py trends [--woeid <woeid>]
    python twitter_client.py detail --tweet-ids <ids>
    python twitter_client.py replies --tweet-id <id>
    python twitter_client.py quotes --tweet-id <id>
    python twitter_client.py retweeters --tweet-id <id>
    python twitter_client.py thread --tweet-id <id>
    python twitter_client.py list-members --list-id <id>
    python twitter_client.py list-followers --list-id <id>
    python twitter_client.py community-info --community-id <id>
    python twitter_client.py community-members --community-id <id>
    python twitter_client.py community-tweets --community-id <id>
    python twitter_client.py community-search --query <query>
    python twitter_client.py login --username <u> --email <e> --password <p> --proxy <proxy>
    python twitter_client.py post --cookies <c> --text <text> --proxy <proxy>
    python twitter_client.py like --cookies <c> --tweet-id <id> --proxy <proxy>
    python twitter_client.py unlike --cookies <c> --tweet-id <id> --proxy <proxy>
    python twitter_client.py retweet --cookies <c> --tweet-id <id> --proxy <proxy>
    python twitter_client.py delete-tweet --cookies <c> --tweet-id <id> --proxy <proxy>
    python twitter_client.py follow --cookies <c> --user-id <id> --proxy <proxy>
    python twitter_client.py unfollow --cookies <c> --user-id <id> --proxy <proxy>
    python twitter_client.py send-dm --cookies <c> --user-id <id> --text <text> --proxy <proxy>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, Optional


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
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-Twitter/1.0"
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
        return self._request("GET", "/twitter/user/check_follow_relationship", params={
            "source_user_name": source,
            "target_user_name": target
        })

    def user_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search for Twitter users by keyword."""
        return self._request("GET", "/twitter/user/search", params={"query": query, "cursor": cursor})

    # ==================== Tweet Read APIs ====================

    def search(self, query: str, query_type: str = "Latest", cursor: str = None) -> Dict[str, Any]:
        """Search for tweets matching a query."""
        return self._request("GET", "/twitter/tweet/advanced_search", params={
            "query": query,
            "queryType": query_type,
            "cursor": cursor
        })

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
        return self._request("GET", "/twitter/community/members", params={"community_id": community_id, "cursor": cursor})

    def community_moderators(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community moderators."""
        return self._request("GET", "/twitter/community/moderators", params={"community_id": community_id, "cursor": cursor})

    def community_tweets(self, community_id: str, cursor: str = None) -> Dict[str, Any]:
        """Get community tweets."""
        return self._request("GET", "/twitter/community/tweets", params={"community_id": community_id, "cursor": cursor})

    def community_search(self, query: str, cursor: str = None) -> Dict[str, Any]:
        """Search tweets from all communities."""
        return self._request("GET", "/twitter/community/get_tweets_from_all_community", params={"query": query, "cursor": cursor})

    def space_detail(self, space_id: str) -> Dict[str, Any]:
        """Get Space detail by ID."""
        return self._request("GET", "/twitter/spaces/detail", params={"space_id": space_id})

    # ==================== Write APIs (requires login_cookies) ====================

    def login(self, username: str, email: str, password: str, proxy: str, totp_secret: str = None) -> Dict[str, Any]:
        """Login to Twitter account. Returns login_cookies for write operations."""
        data = {
            "user_name": username,
            "email": email,
            "password": password,
            "proxy": proxy
        }
        if totp_secret:
            data["totp_secret"] = totp_secret
        return self._request("POST", "/twitter/user_login_v2", data=data)

    def create_tweet(self, login_cookies: str, text: str, proxy: str,
                     reply_to_tweet_id: str = None, media_ids: list = None) -> Dict[str, Any]:
        """Create a tweet."""
        data = {
            "login_cookies": login_cookies,
            "tweet_text": text,
            "proxy": proxy
        }
        if reply_to_tweet_id:
            data["reply_to_tweet_id"] = reply_to_tweet_id
        if media_ids:
            data["media_ids"] = media_ids
        return self._request("POST", "/twitter/create_tweet_v2", data=data)

    def like(self, login_cookies: str, tweet_id: str, proxy: str) -> Dict[str, Any]:
        """Like a tweet."""
        return self._request("POST", "/twitter/like_tweet_v2", data={
            "login_cookies": login_cookies,
            "tweet_id": tweet_id,
            "proxy": proxy
        })

    def unlike(self, login_cookies: str, tweet_id: str, proxy: str) -> Dict[str, Any]:
        """Unlike a tweet."""
        return self._request("POST", "/twitter/unlike_tweet_v2", data={
            "login_cookies": login_cookies,
            "tweet_id": tweet_id,
            "proxy": proxy
        })

    def retweet(self, login_cookies: str, tweet_id: str, proxy: str) -> Dict[str, Any]:
        """Retweet a tweet."""
        return self._request("POST", "/twitter/retweet_tweet_v2", data={
            "login_cookies": login_cookies,
            "tweet_id": tweet_id,
            "proxy": proxy
        })

    def delete_tweet(self, login_cookies: str, tweet_id: str, proxy: str) -> Dict[str, Any]:
        """Delete a tweet."""
        return self._request("POST", "/twitter/delete_tweet_v2", data={
            "login_cookies": login_cookies,
            "tweet_id": tweet_id,
            "proxy": proxy
        })

    def follow_user(self, login_cookies: str, user_id: str, proxy: str) -> Dict[str, Any]:
        """Follow a user."""
        return self._request("POST", "/twitter/follow_user_v2", data={
            "login_cookies": login_cookies,
            "user_id": user_id,
            "proxy": proxy
        })

    def unfollow_user(self, login_cookies: str, user_id: str, proxy: str) -> Dict[str, Any]:
        """Unfollow a user."""
        return self._request("POST", "/twitter/unfollow_user_v2", data={
            "login_cookies": login_cookies,
            "user_id": user_id,
            "proxy": proxy
        })

    def send_dm(self, login_cookies: str, user_id: str, text: str, proxy: str) -> Dict[str, Any]:
        """Send a direct message to a user."""
        return self._request("POST", "/twitter/send_dm_to_user", data={
            "login_cookies": login_cookies,
            "user_id": user_id,
            "text": text,
            "proxy": proxy
        })


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Twitter - Twitter/X data and automation",
        formatter_class=argparse.RawDescriptionHelpFormatter
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

    # ---- Write Commands (require login_cookies) ----

    p = subparsers.add_parser("login", help="Login to Twitter account")
    p.add_argument("--username", "-u", required=True)
    p.add_argument("--email", "-e", required=True)
    p.add_argument("--password", "-p", required=True)
    p.add_argument("--proxy", required=True)
    p.add_argument("--totp-secret", help="2FA TOTP secret key")

    p = subparsers.add_parser("post", help="Create a tweet")
    p.add_argument("--cookies", required=True, help="login_cookies from login")
    p.add_argument("--text", "-t", required=True)
    p.add_argument("--proxy", required=True)
    p.add_argument("--reply-to", help="Tweet ID to reply to")

    p = subparsers.add_parser("like", help="Like a tweet")
    p.add_argument("--cookies", required=True)
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("unlike", help="Unlike a tweet")
    p.add_argument("--cookies", required=True)
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("retweet", help="Retweet a tweet")
    p.add_argument("--cookies", required=True)
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("delete-tweet", help="Delete a tweet")
    p.add_argument("--cookies", required=True)
    p.add_argument("--tweet-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("follow", help="Follow a user")
    p.add_argument("--cookies", required=True)
    p.add_argument("--user-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("unfollow", help="Unfollow a user")
    p.add_argument("--cookies", required=True)
    p.add_argument("--user-id", required=True)
    p.add_argument("--proxy", required=True)

    p = subparsers.add_parser("send-dm", help="Send a direct message")
    p.add_argument("--cookies", required=True)
    p.add_argument("--user-id", required=True)
    p.add_argument("--text", "-t", required=True)
    p.add_argument("--proxy", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = TwitterClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)

    result = None
    cmd = args.command

    # User read commands
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
    # Search & Discovery
    elif cmd == "search":
        result = client.search(args.query, args.type, getattr(args, "cursor", None))
    elif cmd == "user-search":
        result = client.user_search(args.query, getattr(args, "cursor", None))
    elif cmd == "trends":
        result = client.trends(args.woeid)
    # Tweet detail commands
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
    # List commands
    elif cmd == "list-members":
        result = client.list_members(args.list_id, getattr(args, "cursor", None))
    elif cmd == "list-followers":
        result = client.list_followers(args.list_id, getattr(args, "cursor", None))
    # Community commands
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
    # Spaces
    elif cmd == "space-detail":
        result = client.space_detail(args.space_id)
    # Write commands
    elif cmd == "login":
        result = client.login(args.username, args.email, args.password, args.proxy, args.totp_secret)
    elif cmd == "post":
        result = client.create_tweet(args.cookies, args.text, args.proxy, args.reply_to)
    elif cmd == "like":
        result = client.like(args.cookies, args.tweet_id, args.proxy)
    elif cmd == "unlike":
        result = client.unlike(args.cookies, args.tweet_id, args.proxy)
    elif cmd == "retweet":
        result = client.retweet(args.cookies, args.tweet_id, args.proxy)
    elif cmd == "delete-tweet":
        result = client.delete_tweet(args.cookies, args.tweet_id, args.proxy)
    elif cmd == "follow":
        result = client.follow_user(args.cookies, args.user_id, args.proxy)
    elif cmd == "unfollow":
        result = client.unfollow_user(args.cookies, args.user_id, args.proxy)
    elif cmd == "send-dm":
        result = client.send_dm(args.cookies, args.user_id, args.text, args.proxy)

    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
