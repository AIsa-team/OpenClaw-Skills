#!/usr/bin/env python3
"""
Perplexity Search client for AIsa Sonar endpoints.

Usage:
    python perplexity_search_client.py sonar --query <query> [--system <instruction>]
    python perplexity_search_client.py sonar-pro --query <query> [--system <instruction>]
    python perplexity_search_client.py sonar-reasoning-pro --query <query> [--system <instruction>]
    python perplexity_search_client.py sonar-deep-research --query <query> [--system <instruction>]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class PerplexitySearchClient:
    """Minimal client for AIsa Perplexity Sonar endpoints."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError("AISA_API_KEY is required.")

    def _request(
        self,
        endpoint: str,
        model: str,
        query: str,
        system: Optional[str] = None,
        timeout: int = 120,
        retries: int = 0,
        retry_delay_seconds: int = 5,
    ) -> Dict[str, Any]:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": query})

        body = {"model": model, "messages": messages}
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Perplexity-Search/1.0",
        }
        req = urllib.request.Request(
            f"{self.BASE_URL}{endpoint}", data=data, headers=headers, method="POST"
        )

        attempts = retries + 1
        for attempt in range(1, attempts + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                if exc.code in {502, 503, 504} and attempt < attempts:
                    time.sleep(retry_delay_seconds)
                    continue
                error_data = self._decode_error(exc.code, error_body)
                if exc.code == 504 and endpoint == "/perplexity/sonar-deep-research":
                    return self._friendly_deep_research_timeout(attempt, timeout, error_data)
                return error_data
            except urllib.error.URLError as exc:
                if attempt < attempts:
                    time.sleep(retry_delay_seconds)
                    continue
                error_data = {
                    "success": False,
                    "error": {"code": "NETWORK_ERROR", "message": str(exc.reason)},
                }
                if endpoint == "/perplexity/sonar-deep-research":
                    return self._friendly_deep_research_timeout(attempt, timeout, error_data)
                return error_data

        return {"success": False, "error": {"code": "UNKNOWN_ERROR", "message": "Request failed unexpectedly."}}

    @staticmethod
    def _decode_error(code: int, error_body: str) -> Dict[str, Any]:
        try:
            return json.loads(error_body)
        except json.JSONDecodeError:
            return {"success": False, "error": {"code": str(code), "message": error_body}}

    @staticmethod
    def _friendly_deep_research_timeout(
        attempts: int, timeout: int, error_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        base_error = error_data.get("error", {})
        return {
            "success": False,
            "error": {
                "code": str(base_error.get("code", "TIMEOUT")),
                "message": (
                    "Sonar Deep Research timed out after "
                    f"{attempts} attempt(s) with a {timeout}s timeout per attempt. "
                    "Try a narrower prompt, retry later, or switch to sonar-pro / "
                    "sonar-reasoning-pro for a faster response."
                ),
                "details": base_error.get("message", "Timed out"),
            },
        }

    def sonar(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._request("/perplexity/sonar", "sonar", query, system)

    def sonar_pro(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._request("/perplexity/sonar-pro", "sonar-pro", query, system)

    def sonar_reasoning_pro(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._request(
            "/perplexity/sonar-reasoning-pro", "sonar-reasoning-pro", query, system
        )

    def sonar_deep_research(self, query: str, system: Optional[str] = None) -> Dict[str, Any]:
        return self._request(
            "/perplexity/sonar-deep-research",
            "sonar-deep-research",
            query,
            system,
            timeout=180,
            retries=2,
            retry_delay_seconds=6,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Perplexity Sonar search client for AIsa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s sonar --query "What changed in AI this week?"
    %(prog)s sonar-pro --query "Compare coding agents with citations"
    %(prog)s sonar-deep-research --query "Create a deep research report on AI coding agents"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Perplexity model")
    for command_name, help_text in [
        ("sonar", "Perplexity Sonar"),
        ("sonar-pro", "Perplexity Sonar Pro"),
        ("sonar-reasoning-pro", "Perplexity Sonar Reasoning Pro"),
        ("sonar-deep-research", "Perplexity Sonar Deep Research"),
    ]:
        subparser = subparsers.add_parser(command_name, help=help_text)
        subparser.add_argument("--query", "-q", required=True, help="User query")
        subparser.add_argument("--system", help="Optional system instruction")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = PerplexitySearchClient()
    except ValueError as exc:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(exc)}}))
        sys.exit(1)

    result: Optional[Dict[str, Any]] = None
    if args.command == "sonar":
        result = client.sonar(args.query, args.system)
    elif args.command == "sonar-pro":
        result = client.sonar_pro(args.query, args.system)
    elif args.command == "sonar-reasoning-pro":
        result = client.sonar_reasoning_pro(args.query, args.system)
    elif args.command == "sonar-deep-research":
        result = client.sonar_deep_research(args.query, args.system)

    if result is None:
        parser.print_help()
        sys.exit(1)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        print(json.dumps(result, indent=2, ensure_ascii=True))

    sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()
