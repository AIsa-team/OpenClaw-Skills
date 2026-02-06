#!/usr/bin/env python3
"""
CN-LLM - China LLM Unified Gateway Client
Access Chinese LLMs including Qwen, DeepSeek, GLM, Baichuan, Moonshot via AIsa API.

Usage:
    python cn_llm_client.py chat --model <model> --message <message> [--stream]
    python cn_llm_client.py chat --model <model> --messages <json_array>
    python cn_llm_client.py compare --models <model1,model2,...> --message <message>
    python cn_llm_client.py models
"""

import argparse
import io
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, Generator, List, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class CNLLMClient:
    """China LLM Unified Gateway Client."""

    BASE_URL = "https://api.aisa.one/v1"

    # Supported Chinese LLMs (from marketplace.aisa.one/pricing)
    SUPPORTED_MODELS = {
        "Qwen3 (Alibaba)": [
            "qwen3-max",
            "qwen3-max-2026-01-23",
            "qwen3-coder-plus",
            "qwen3-coder-flash",
            "qwen3-coder-480b-a35b-instruct",
            "qwen3-vl-plus",
            "qwen3-vl-plus-2025-12-19",
            "qwen3-vl-flash",
            "qwen3-vl-flash-2025-10-15",
            "qwen3-omni-flash",
            "qwen3-omni-flash-2025-12-01"
        ],
        "Qwen (Alibaba)": [
            "qwen-vl-max",
            "qwen-plus-2025-12-01",
            "qwen-mt-flash",
            "qwen-mt-lite"
        ],
        "DeepSeek": [
            "deepseek-r1",
            "deepseek-v3",
            "deepseek-v3-0324",
            "deepseek-v3.1"
        ]
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client."""
        self.api_key = api_key or os.environ.get("AISA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY required. Set environment variable or pass to constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """Send HTTP request to AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenClaw-CNLLM/1.0",
            "Accept": "application/json"
        }

        request_data = None
        if data:
            request_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        try:
            response = urllib.request.urlopen(req, timeout=120)

            if stream:
                return self._handle_stream(response)
            else:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"error": {"code": str(e.code), "message": error_body}}
        except urllib.error.URLError as e:
            return {"error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    def _handle_stream(self, response) -> Generator[str, None, None]:
        """Handle streaming response (SSE)."""
        for line in response:
            line = line.decode("utf-8").strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion.

        Args:
            model: Model identifier (e.g., qwen-max, deepseek-v3)
            messages: Message list containing 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stream: Enable streaming output
            **kwargs: Additional parameters

        Returns:
            Chat completion response
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p

        payload.update(kwargs)

        return self._request("POST", "/chat/completions", data=payload, stream=stream)

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Create a streaming chat completion.

        Yields generated content chunk by chunk.
        """
        return self.chat(model=model, messages=messages, stream=True, **kwargs)

    def compare_models(
        self,
        models: List[str],
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Compare responses from multiple models.

        Args:
            models: List of model identifiers
            message: Message to send to each model

        Returns:
            Dictionary with model names as keys and results as values
        """
        import time

        results = {}
        for model in models:
            start = time.time()
            try:
                response = self.chat(
                    model=model,
                    messages=[{"role": "user", "content": message}],
                    **kwargs
                )
                elapsed = time.time() - start

                if "error" in response:
                    results[model] = {
                        "success": False,
                        "error": response["error"],
                        "latency": elapsed
                    }
                else:
                    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = response.get("usage", {})
                    results[model] = {
                        "success": True,
                        "response": content,
                        "latency": elapsed,
                        "tokens": usage.get("total_tokens", 0),
                        "cost": usage.get("cost", 0)
                    }
            except Exception as e:
                results[model] = {
                    "success": False,
                    "error": str(e),
                    "latency": time.time() - start
                }

        return results

    def list_models(self) -> Dict[str, List[str]]:
        """List supported Chinese LLMs."""
        return self.SUPPORTED_MODELS


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CN-LLM - China LLM Unified Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s chat --model qwen-max --message "Hello!"
    %(prog)s chat --model deepseek-coder --message "Write a quicksort"
    %(prog)s chat --model deepseek-r1 --message "Which is larger, 9.9 or 9.11?"
    %(prog)s chat --model qwen-plus --message "Tell a story" --stream
    %(prog)s chat --model glm-4 --system "You are a poet" --message "Write a poem about spring"
    %(prog)s compare --models "qwen-max,deepseek-v3" --message "What is AI?"
    %(prog)s models
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send chat request")
    chat_parser.add_argument("--model", "-m", required=True, help="Model identifier")
    chat_parser.add_argument("--message", help="User message")
    chat_parser.add_argument("--messages", help="Full message array (JSON format)")
    chat_parser.add_argument("--system", "-s", help="System prompt")
    chat_parser.add_argument("--temperature", "-t", type=float, help="Temperature (0-2)")
    chat_parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate")
    chat_parser.add_argument("--stream", action="store_true", help="Streaming output")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple models")
    compare_parser.add_argument("--models", required=True, help="Comma-separated model list")
    compare_parser.add_argument("--message", "-m", required=True, help="Message to send")
    compare_parser.add_argument("--temperature", "-t", type=float, help="Temperature")
    compare_parser.add_argument("--max-tokens", type=int, help="Maximum tokens")

    # Models command
    subparsers.add_parser("models", help="List supported models")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Models command doesn't require API Key
    if args.command == "models":
        print(json.dumps(CNLLMClient.SUPPORTED_MODELS, indent=2, ensure_ascii=False))
        sys.exit(0)

    try:
        client = CNLLMClient()
    except ValueError as e:
        print(json.dumps({"error": {"code": "AUTH_ERROR", "message": str(e)}}, ensure_ascii=False))
        sys.exit(1)

    result = None

    if args.command == "chat":
        # Build messages
        if args.messages:
            messages = json.loads(args.messages)
        elif args.message:
            messages = []
            if args.system:
                messages.append({"role": "system", "content": args.system})
            messages.append({"role": "user", "content": args.message})
        else:
            print(json.dumps({"error": {"code": "INVALID_INPUT", "message": "Requires --message or --messages parameter"}}, ensure_ascii=False))
            sys.exit(1)

        kwargs = {}
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.max_tokens is not None:
            kwargs["max_tokens"] = args.max_tokens

        if args.stream:
            # Streaming mode
            try:
                for chunk in client.chat_stream(model=args.model, messages=messages, **kwargs):
                    print(chunk, end="", flush=True)
                print()  # Final newline
                sys.exit(0)
            except Exception as e:
                print(json.dumps({"error": {"code": "STREAM_ERROR", "message": str(e)}}, ensure_ascii=False))
                sys.exit(1)
        else:
            result = client.chat(model=args.model, messages=messages, **kwargs)

    elif args.command == "compare":
        models = [m.strip() for m in args.models.split(",")]
        kwargs = {}
        if args.temperature is not None:
            kwargs["temperature"] = args.temperature
        if args.max_tokens is not None:
            kwargs["max_tokens"] = args.max_tokens
        result = client.compare_models(models=models, message=args.message, **kwargs)

    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))

        # Return error code if result contains error
        if isinstance(result, dict) and "error" in result:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
