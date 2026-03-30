#!/usr/bin/env python3
"""
Twitter relay client for local OAuth authorization and tweet publishing.

Commands:
    python twitter_oauth_client.py authorize [--callback-url <url>] [--open-browser]
    python twitter_oauth_client.py post [--text "Hello"] [--media-id <id> ...] [--media-file <path> ...] [--type <quote|reply>] [--quote-tweet-url <url>] [--in-reply-to-tweet-id <id>]
    python twitter_oauth_client.py status
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
import uuid
import webbrowser
from typing import Any, Dict, Optional


DEFAULT_TIMEOUT = 30
MEDIA_UPLOAD_TIMEOUT = 120
DEFAULT_BASE_URL = "https://api.aisa.one/apis/v1"
DEFAULT_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)



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
        get_env("TWITTER_RELAY_BASE_URL", DEFAULT_BASE_URL)
    )
    aisa_api_key = getattr(args, "aisa_api_key", None) or get_env("AISA_API_KEY")
    timeout = getattr(args, "timeout", None) or int(get_env("TWITTER_RELAY_TIMEOUT", str(DEFAULT_TIMEOUT)))

    if not aisa_api_key:
        raise RelayConfigError("AISA_API_KEY is required.")

    return {
        "base_url": base_url,
        "aisa_api_key": aisa_api_key,
        "timeout": timeout,
    }


def parse_response_body(raw: str, status: Any, default_message: str) -> Dict[str, Any]:
    try:
        return json.loads(raw) if raw else {"code": status, "msg": default_message, "data": None}
    except json.JSONDecodeError:
        return {"code": status, "msg": raw or default_message, "data": None}


def build_auth_headers(aisa_api_key: str, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {aisa_api_key}",
        "User-Agent": DEFAULT_CHROME_USER_AGENT,
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def send_json_request(
    url: str,
    payload: Dict[str, Any],
    timeout: int,
    aisa_api_key: str,
) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=build_auth_headers(
            aisa_api_key,
            {"Content-Type": "application/json", "Accept": "application/json"},
        ),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return parse_response_body(raw, response.status, "ok")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        payload = parse_response_body(body, exc.code, exc.reason)
        return {"ok": False, "status": exc.code, "payload": payload}
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "NETWORK_ERROR",
            "payload": {"code": 503, "msg": str(exc.reason), "data": None},
        }


def encode_multipart_form_data(
    fields: Dict[str, Any],
    files: list[Dict[str, Any]],
) -> tuple[bytes, str]:
    boundary = f"----OpenClawTwitterBoundary{uuid.uuid4().hex}"
    body = bytearray()

    def append_text_part(name: str, value: Any) -> None:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for field_name, field_value in fields.items():
        if field_value is None:
            continue
        if isinstance(field_value, list):
            for item in field_value:
                append_text_part(field_name, item)
            continue
        append_text_part(field_name, field_value)

    for file_payload in files:
        field_name = file_payload["field_name"]
        filename = file_payload["filename"]
        ascii_filename = "".join(ch if ord(ch) < 128 and ch not in {'"', "\\"} else "_" for ch in filename) or "upload.bin"
        quoted_filename = urllib.parse.quote(filename, safe="")
        content_type = file_payload["content_type"]

        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{ascii_filename}"; filename*=UTF-8\'\'{quoted_filename}\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_payload["content"])
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), boundary


def send_multipart_request(
    url: str,
    fields: Dict[str, Any],
    files: list[Dict[str, Any]],
    timeout: int,
    aisa_api_key: str,
) -> Dict[str, Any]:
    body, boundary = encode_multipart_form_data(fields, files)
    request = urllib.request.Request(
        url,
        data=body,
        headers=build_auth_headers(
            aisa_api_key,
            {
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Accept": "application/json",
            },
        ),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return parse_response_body(raw, response.status, "ok")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        payload = parse_response_body(body, exc.code, exc.reason)
        return {"ok": False, "status": exc.code, "payload": payload}
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "status": "NETWORK_ERROR",
            "payload": {"code": 503, "msg": str(exc.reason), "data": None},
        }


# ---------------------------------------------------------------------------
# Media upload
# ---------------------------------------------------------------------------

def upload_single_media(
    config: Dict[str, Any],
    media_file: Dict[str, Any],
) -> Dict[str, Any]:
    """Upload a single media file to the relay and return the parsed response.

    The relay endpoint ``/twitter/upload_media`` accepts a multipart request
    with the ``aisa_api_key`` text field and a single ``media_file`` binary
    part.  On success the response contains a ``media_id`` that can later be
    passed to ``/twitter/post_twitter``.
    """
    endpoint = f"{config['base_url']}/twitter/upload_media"
    fields: Dict[str, Any] = {
        "aisa_api_key": config["aisa_api_key"],
    }
    # The relay expects the file part under the field name "media_file".
    file_entry = {
        "field_name": "media_file",
        "filename": media_file["filename"],
        "content_type": media_file["content_type"],
        "content": media_file["content"],
    }
    timeout = max(config["timeout"], MEDIA_UPLOAD_TIMEOUT)
    return send_multipart_request(endpoint, fields, [file_entry], timeout=timeout, aisa_api_key=config["aisa_api_key"])


def extract_media_id(result: Dict[str, Any]) -> Optional[str]:
    """Extract the media_id from an upload_media response."""
    if isinstance(result, dict):
        # Try common response shapes:
        #   {"code": 200, "data": {"media_id": "..."}}
        #   {"media_id": "..."}
        #   {"data": {"media_id_string": "..."}}
        data = result.get("data") if isinstance(result.get("data"), dict) else result
        for key in ("media_id", "media_id_string"):
            value = data.get(key)
            if value:
                return str(value)
    return None


def upload_media_files(
    config: Dict[str, Any],
    media_files: list[Dict[str, Any]],
) -> list[str]:
    """Upload all media files and return a list of media IDs.

    Raises ``RelayConfigError`` if any upload fails or does not return a
    ``media_id``.
    """
    media_ids: list[str] = []
    for media_file in media_files:
        result = upload_single_media(config, media_file)

        if result.get("ok") is False:
            raise RelayConfigError(
                f"Media upload failed for {media_file['filename']}: "
                f"{json.dumps(result, ensure_ascii=False)}"
            )

        media_id = extract_media_id(result)
        if not media_id:
            raise RelayConfigError(
                f"Media upload for {media_file['filename']} did not return a media_id. "
                f"Response: {json.dumps(result, ensure_ascii=False)}"
            )
        media_ids.append(media_id)

    return media_ids


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


def extract_tweet_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise RelayConfigError("Quote tweet URL must be a valid http(s) URL.")
    if parsed.netloc.lower() not in {"twitter.com", "www.twitter.com", "x.com", "www.x.com"}:
        raise RelayConfigError("Quote tweet URL must point to twitter.com or x.com.")

    match = re.search(r"/status/(\d+)", parsed.path)
    if not match:
        raise RelayConfigError("Quote tweet URL must contain a valid /status/<tweet_id> path.")
    return match.group(1)


def append_quote_url_to_content(content: str, quote_url: str) -> str:
    normalized_content = content.strip()
    normalized_quote_url = quote_url.strip()
    if not normalized_quote_url:
        return normalized_content
    if normalized_quote_url in normalized_content:
        return normalized_content
    if not normalized_content:
        return normalized_quote_url
    return f"{normalized_content}\n\n{normalized_quote_url}"


def extract_tweet_id(result: Dict[str, Any]) -> Optional[str]:
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, dict):
        return None
    tweet_id = data.get("tweet_id")
    return str(tweet_id) if tweet_id else None


def publish_chunks(
    config: Dict[str, Any],
    chunks: list[str],
    media_ids: Optional[list[str]] = None,
    initial_parent_tweet_id: Optional[str] = None,
    post_type: str = "quote",
) -> Dict[str, Any]:
    should_thread = len(chunks) > 1
    previous_tweet_id = initial_parent_tweet_id
    publish_results = []

    for index, chunk in enumerate(chunks):
        current_media_ids = media_ids if index == 0 and media_ids else None
        result = post_single_tweet(
            config,
            content=chunk,
            media_ids=current_media_ids,
            parent_tweet_id=previous_tweet_id,
            post_type=post_type,
        )
        publish_results.append(
            {
                "index": index + 1,
                "content": chunk,
                "parent_tweet_id": previous_tweet_id,
                "result": result,
            }
        )
        if result.get("ok") is False or result.get("code") != 200:
            return {
                "ok": False,
                "aisa_api_key": config["aisa_api_key"],
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "results": publish_results,
            }

        latest_tweet_id = extract_tweet_id(result)
        if not latest_tweet_id:
            return {
                "ok": False,
                "aisa_api_key": config["aisa_api_key"],
                "is_thread": should_thread,
                "total_chunks": len(chunks),
                "failed_at_chunk": index + 1,
                "error": "Missing tweet_id in relay response.",
                "results": publish_results,
            }
        previous_tweet_id = latest_tweet_id

    return {
        "ok": True,
        "aisa_api_key": config["aisa_api_key"],
        "is_thread": should_thread,
        "total_chunks": len(chunks),
        "results": publish_results,
    }


def post_single_tweet(
    config: Dict[str, Any],
    *,
    content: Optional[str] = None,
    media_ids: Optional[list[str]] = None,
    parent_tweet_id: Optional[str] = None,
    post_type: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "aisa_api_key": config["aisa_api_key"],
    }
    if content:
        payload["content"] = content
    if post_type:
        payload["type"] = post_type
    if media_ids:
        payload["media_ids"] = media_ids
    if parent_tweet_id:
        parent_key = "in_reply_to_tweet_id" if post_type == "reply" else "quote_tweet_id"
        payload[parent_key] = parent_tweet_id

    endpoint = f"{config['base_url']}/twitter/post_twitter"
    return send_json_request(
        endpoint,
        payload,
        timeout=config["timeout"],
        aisa_api_key=config["aisa_api_key"],
    )


def load_media_files(paths: Optional[list[str]]) -> list[Dict[str, Any]]:
    if not paths:
        return []

    media_files: list[Dict[str, Any]] = []
    media_kinds: set[str] = set()
    seen_paths: set[str] = set()

    for raw_path in paths:
        resolved_path = os.path.abspath(os.path.expanduser(raw_path))
        normalized_path = os.path.normcase(resolved_path)
        if normalized_path in seen_paths:
            continue
        seen_paths.add(normalized_path)

        if not os.path.exists(resolved_path):
            raise RelayConfigError(f"Media file does not exist: {raw_path}")
        if not os.path.isfile(resolved_path):
            raise RelayConfigError(f"Media path is not a file: {raw_path}")

        mime_type = mimetypes.guess_type(resolved_path)[0] or "application/octet-stream"
        media_kind = mime_type.split("/", 1)[0]
        if media_kind not in {"image", "video"}:
            raise RelayConfigError(
                f"Unsupported media type for {raw_path}: {mime_type}. Only image and video files are supported."
            )
        media_kinds.add(media_kind)

        with open(resolved_path, "rb") as file_handle:
            content = file_handle.read()

        media_files.append(
            {
                "field_name": "media_file",
                "filename": os.path.basename(resolved_path),
                "content_type": mime_type,
                "content": content,
            }
        )

    if len(media_kinds) > 1:
        raise RelayConfigError("Do not mix image and video files in a single post request.")

    return media_files


def command_authorize(args: argparse.Namespace) -> None:
    config = load_config(args)
    payload = {"aisa_api_key": config["aisa_api_key"]}
    result = send_json_request(
        f"{config['base_url']}/twitter/auth_twitter",
        payload,
        timeout=config["timeout"],
        aisa_api_key=config["aisa_api_key"],
    )

    if result.get("ok") is False:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    auth_url = (result.get("data") or {}).get("auth_url")
    output = {
        "ok": result.get("code") == 200 and bool(auth_url),
        "aisa_api_key": config["aisa_api_key"],
        "authorization_url": auth_url,
        "raw_response": result,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if output["ok"] and args.open_browser:
        webbrowser.open(auth_url)

    if not output["ok"]:
        sys.exit(1)


def command_post(args: argparse.Namespace) -> None:
    """Split oversized content locally, then publish chunks through the relay."""
    config = load_config(args)
    media_ids = getattr(args, "media_id", None) or []
    media_files = load_media_files(getattr(args, "media_file", None))
    normalized_text = (args.text or "").strip()
    quote_tweet_url = (getattr(args, "quote_tweet_url", None) or "").strip()
    initial_parent_tweet_id = None

    if not normalized_text and not media_ids and not media_files:
        print(
            json.dumps(
                {"ok": False, "error": "Post content must not be empty unless media files or media IDs are provided."},
                indent=2,
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    # ---- Upload local media files first to obtain media IDs ----
    if media_files:
        uploaded_ids = upload_media_files(config, media_files)
        media_ids = list(media_ids) + uploaded_ids

    if args.type == "quote":
        if args.in_reply_to_tweet_id:
            raise RelayConfigError(
                "Quote posts that reference another tweet must use --quote-tweet-url. "
                "The published post will include that link in its content."
            )
        if quote_tweet_url:
            initial_parent_tweet_id = extract_tweet_id_from_url(quote_tweet_url)
            normalized_text = append_quote_url_to_content(normalized_text, quote_tweet_url)
    else:
        if quote_tweet_url:
            raise RelayConfigError("--quote-tweet-url can only be used together with --type quote.")
        initial_parent_tweet_id = args.in_reply_to_tweet_id

    chunks = split_text_for_twitter(normalized_text) if normalized_text else [""]
    should_use_post_type = len(chunks) > 1 or bool(initial_parent_tweet_id)
    effective_post_type = None
    if should_use_post_type:
        effective_post_type = args.type
    output = publish_chunks(
        config,
        chunks,
        media_ids=media_ids if media_ids else None,
        post_type=effective_post_type,
        initial_parent_tweet_id=initial_parent_tweet_id,
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if not output["ok"]:
        sys.exit(1)


def command_status(args: argparse.Namespace) -> None:
    config = load_config(args)
    response = {
        "ok": True,
        "relay_base_url": config["base_url"],
        "aisa_api_key": config["aisa_api_key"],
        "timeout": config["timeout"],
        "supported_commands": ["authorize", "post", "status"],
        "supported_endpoints": [
            "/twitter/auth_twitter",
            "/twitter/upload_media",
            "/twitter/post_twitter",
        ],
        "media_upload": {
            "upload_endpoint": "/twitter/upload_media",
            "field_name": "media_file",
            "transport": "multipart/form-data",
            "supported_media_types": ["image/*", "video/*"],
            "flow": "Upload file to /twitter/upload_media -> receive media_id -> pass media_ids to /twitter/post_twitter",
        },
    }
    print(json.dumps(response, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Twitter relay client for local OAuth and posting",
    )
    parser.add_argument("--aisa-api-key", help="Override AISA_API_KEY")
    parser.add_argument("--timeout", type=int, help="Override TWITTER_RELAY_TIMEOUT")

    subparsers = parser.add_subparsers(dest="command", required=True)

    authorize = subparsers.add_parser("authorize", help="Request an authorization URL from the relay service")
    authorize.add_argument("--open-browser", action="store_true", help="Open the authorization URL in the default browser")
    authorize.set_defaults(func=command_authorize)

    post = subparsers.add_parser("post", help="Publish a post through the relay service")
    post.add_argument("--text", default="", help="Post content. Optional when media is provided.")
    post.add_argument(
        "--media-id",
        action="append",
        help="Media ID to attach. Repeat the flag to send multiple media IDs.",
    )
    post.add_argument(
        "--media-file",
        action="append",
        help="Local image or video path to upload. Repeat the flag to attach multiple files of the same media kind.",
    )
    post.add_argument(
        "--type",
        choices=["quote", "reply"],
        default="quote",
        help="Relationship used to continue multi-chunk posts. Use quote to publish quote-style chains or reply for reply-style threading.",
    )
    post.add_argument(
        "--quote-tweet-url",
        help="Quoted tweet URL for quote-style posting. When provided, the URL is appended to the published content and used as the first quoted tweet.",
    )

    post.add_argument(
        "--in-reply-to-tweet-id",
        help="Optional external parent tweet ID for reply-style posting. When provided with --type reply, the first chunk starts from that tweet before continuing the thread.",
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
