#!/usr/bin/env python3
"""
Twitter relay client for local OAuth authorization and tweet publishing.

Commands:
    python twitter_oauth_client.py authorize [--callback-url <url>] [--open-browser]
    python twitter_oauth_client.py post --text "Hello" [--media-id <id> ...] [--in-reply-to-tweet-id <id>]
    python twitter_oauth_client.py status
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
from typing import Any, Dict, Optional


DEFAULT_TIMEOUT = 30
DEFAULT_BASE_URL = "https://api.aisa.one/apis/v1"


class RelayConfigError(ValueError):
    """Configuration is incomplete or invalid."""


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def normalize_base_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise RelayConfigError("TWITTER_RELAY_BASE_URL is required.")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RelayConfigError("TWITTER_RELAY_BASE_URL must be a valid http(s) URL.")
    return value


def load_config(args: argparse.Namespace) -> Dict[str, Any]:
    base_url = normalize_base_url(
        getattr(args, "base_url", None) or get_env("TWITTER_RELAY_BASE_URL", DEFAULT_BASE_URL)
    )
    aisa_api_key = getattr(args, "aisa_api_key", None) or get_env("AISA_API_KEY")
    callback_url = getattr(args, "callback_url", None) or get_env("AISA_CALLBACK_URL")
    timeout = getattr(args, "timeout", None) or int(get_env("TWITTER_RELAY_TIMEOUT", str(DEFAULT_TIMEOUT)))

    if not aisa_api_key:
        raise RelayConfigError("AISA_API_KEY is required.")

    return {
        "base_url": base_url,
        "aisa_api_key": aisa_api_key,
        "callback_url": callback_url,
        "timeout": timeout,
    }


def send_json_request(url: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {"code": response.status, "msg": "ok", "data": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"code": exc.code, "msg": body or exc.reason, "data": None}
        return {"ok": False, "status": exc.code, "payload": payload}
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "NETWORK_ERROR",
            "payload": {"code": 503, "msg": str(exc.reason), "data": None},
        }


TWITTER_MAX_WEIGHT = 280
TWITTER_URL_WEIGHT = 23
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


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


def split_by_twitter_weight(text: str, max_len: int) -> list[str]:
    parts: list[str] = []
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


def split_text_for_twitter(text: str, max_len: int = TWITTER_MAX_WEIGHT) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []
    if twitter_weight_len(normalized) <= max_len:
        return [normalized]

    words = normalized.split()
    chunks: list[str] = []
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


def post_single_tweet(
    config: Dict[str, Any],
    *,
    content: str,
    media_ids: Optional[list[str]] = None,
    in_reply_to_tweet_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "aisa_api_key": config["aisa_api_key"],
        "content": content,
    }
    if media_ids:
        payload["media_ids"] = media_ids
    if in_reply_to_tweet_id:
        payload["in_reply_to_tweet_id"] = in_reply_to_tweet_id

    return send_json_request(
        f"{config['base_url']}/twitter/post_twitter",
        payload,
        timeout=config["timeout"],
    )


def command_authorize(args: argparse.Namespace) -> None:
    config = load_config(args)
    payload = {"aisa_api_key": config["aisa_api_key"], "callback_url": config["callback_url"]}
    result = send_json_request(
        f"{config['base_url']}/twitter/auth_twitter",
        payload,
        timeout=config["timeout"],
    )

    if result.get("ok") is False:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    auth_url = (result.get("data") or {}).get("auth_url")
    output = {
        "ok": result.get("code") == 200 and bool(auth_url),
        "relay_base_url": config["base_url"],
        "aisa_api_key": config["aisa_api_key"],
        "callback_url": config["callback_url"],
        "authorization_url": auth_url,
        "raw_response": result,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if output["ok"] and args.open_browser:
        webbrowser.open(auth_url)

    if not output["ok"]:
        sys.exit(1)


def command_post(args: argparse.Namespace) -> None:
    config = load_config(args)
    chunks = split_text_for_twitter(args.text)
    if not chunks:
        print(json.dumps({"ok": False, "error": "Post content must not be empty."}, indent=2, ensure_ascii=False))
        sys.exit(1)

    should_thread = len(chunks) > 1
    previous_tweet_id = args.in_reply_to_tweet_id
    publish_results = []

    for index, chunk in enumerate(chunks):
        media_ids = args.media_id if index == 0 else None
        result = post_single_tweet(
            config,
            content=chunk,
            media_ids=media_ids,
            in_reply_to_tweet_id=previous_tweet_id,
        )
        publish_results.append(
            {
                "index": index + 1,
                "content": chunk,
                "in_reply_to_tweet_id": previous_tweet_id,
                "result": result,
            }
        )
        if result.get("ok") is False or result.get("code") != 200:
            output = {
                "ok": False,
                "relay_base_url": config["base_url"],
                "aisa_api_key": config["aisa_api_key"],
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "results": publish_results,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            sys.exit(1)

        latest_tweet_id = extract_tweet_id(result)
        if not latest_tweet_id:
            output = {
                "ok": False,
                "relay_base_url": config["base_url"],
                "aisa_api_key": config["aisa_api_key"],
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "error": "Missing tweet_id in relay response.",
                "results": publish_results,
            }
            print(json.dumps(output, indent=2, ensure_ascii=False))
            sys.exit(1)
        previous_tweet_id = latest_tweet_id

    output = {
        "ok": True,
        "relay_base_url": config["base_url"],
        "aisa_api_key": config["aisa_api_key"],
        "is_thread": should_thread,
        "total_chunks": len(chunks),
        "results": publish_results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def command_status(args: argparse.Namespace) -> None:
    config = load_config(args)
    response = {
        "ok": True,
        "relay_base_url": config["base_url"],
        "aisa_api_key": config["aisa_api_key"],
        "callback_url": config["callback_url"],
        "timeout": config["timeout"],
        "supported_commands": ["authorize", "post", "status"],
        "supported_endpoints": ["/twitter/auth_twitter", "/twitter/post_twitter"],
    }
    print(json.dumps(response, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Twitter relay client for local OAuth and posting",
    )
    parser.add_argument("--base-url", help="Override TWITTER_RELAY_BASE_URL")
    parser.add_argument("--aisa-api-key", help="Override AISA_API_KEY")
    parser.add_argument("--callback-url", help="Override AISA_CALLBACK_URL")
    parser.add_argument("--timeout", type=int, help="Override TWITTER_RELAY_TIMEOUT")

    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize = subparsers.add_parser("authorize", help="Request an authorization URL from the relay service")
    authorize.add_argument("--open-browser", action="store_true", help="Open the authorization URL in the default browser")
    authorize.set_defaults(func=command_authorize)

    post = subparsers.add_parser("post", help="Publish a post through the relay service")
    post.add_argument("--text", required=True, help="Post content")
    post.add_argument(
        "--media-id",
        action="append",
        help="Media ID to attach. Repeat the flag to send multiple media IDs.",
    )
    post.add_argument(
        "--in-reply-to-tweet-id",
        help="Optional parent tweet ID. Useful when replying or continuing an existing thread.",
    )
    post.set_defaults(func=command_post)

    status = subparsers.add_parser("status", help="Show current relay client configuration")
    status.set_defaults(func=command_status)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except RelayConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
