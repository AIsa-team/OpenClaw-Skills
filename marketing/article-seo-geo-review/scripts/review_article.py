#!/usr/bin/env python3
"""AIsa Article SEO + GEO Review.

Reviews one article (a local Markdown file or a published URL) for classic
search optimisation (SEO) and generative engine optimisation (GEO) using only
AIsa platform APIs: DataForSEO (keywords, SERP, Google AI Mode, on-page
parsing, LLM mentions), SEMrush (keyword and domain metrics), Oxylabs AI Search
(ChatGPT / Perplexity / Google AI Overview answers) and the AIsa LLM gateway.

Pipeline: Keyword -> SERP -> Competitor -> Content gap -> SEO audit -> GEO
audit -> Rewrite suggestions -> Scorecard.

Standard library only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import hashlib
import json
import math
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

API_BASE = "https://api.aisa.one"
DATA_BASE = API_BASE + "/apis/v1"
CHAT_URL = API_BASE + "/v1/chat/completions"
USER_AGENT = "AIsa Article SEO GEO Review Skill/1.0"
DEFAULT_MODEL = os.environ.get("AISA_REVIEW_MODEL", "").strip() or "gpt-5.4-mini"
VERSION = "1.0"

SLOW_TIMEOUT = 120
FAST_TIMEOUT = 60

# Engine ids accepted by --engines. Order here is the order in the report.
ENGINE_LABELS = {
    "dfs_ai_mode": "Google AI Mode (DataForSEO)",
    "oxy_google_search": "Google AI Overview (Oxylabs)",
    "dfs_chatgpt": "ChatGPT with web search (DataForSEO)",
    "dfs_perplexity": "Perplexity sonar (DataForSEO)",
    "dfs_gemini": "Gemini with web search (DataForSEO)",
    "dfs_claude": "Claude with web search (DataForSEO)",
    "oxy_google_ai_mode": "Google AI Mode (Oxylabs)",
    "dfs_llm_mentions": "LLM mentions top domains (DataForSEO)",
}
# Oxylabs realtime only serves google_search / google_ai_mode through AIsa
# ("Realtime integration is not supported for LLM sources"), so ChatGPT,
# Perplexity, Gemini and Claude answers come from DataForSEO llm_responses.
DEFAULT_ENGINES = [
    "dfs_ai_mode",
    "oxy_google_search",
    "dfs_chatgpt",
    "dfs_perplexity",
    "dfs_llm_mentions",
]
FAST_SKIP = {"dfs_chatgpt", "dfs_perplexity", "dfs_gemini", "dfs_claude"}
LLM_RESPONSE_MODELS = {
    "dfs_chatgpt": ("/dataforseo/ai_optimization/chat_gpt/llm_responses/live", "gpt-5.4-mini"),
    "dfs_perplexity": ("/dataforseo/ai_optimization/perplexity/llm_responses/live", "sonar"),
    "dfs_gemini": ("/dataforseo/ai_optimization/gemini/llm_responses/live", "gemini-2.5-flash"),
    "dfs_claude": ("/dataforseo/ai_optimization/claude/llm_responses/live", "claude-sonnet-4-5"),
}

# call_id -> (label, endpoint, nominal USD, documented max USD)
COSTS: Dict[str, Tuple[str, str, float, float]] = {
    "dfs_keyword_overview": ("Keyword overview", "/dataforseo/dataforseo_labs/google/keyword_overview/live", 0.012, 0.062),
    "dfs_related_keywords": ("Related keywords", "/dataforseo/dataforseo_labs/google/related_keywords/live", 0.012, 0.034),
    "dfs_serp_organic": ("Google organic SERP", "/dataforseo/serp/google/organic/live/advanced", 0.012, 0.031),
    "dfs_ai_mode": ("Google AI Mode SERP", "/dataforseo/serp/google/ai_mode/live/advanced", 0.012, 0.012),
    "dfs_content_parsing": ("On-page content parsing", "/dataforseo/on_page/content_parsing/live", 0.012, 0.012),
    "dfs_llm_mentions": ("LLM mentions top domains", "/dataforseo/ai_optimization/llm_mentions/top_domains/live", 0.101, 0.202),
    "dfs_chatgpt": ("ChatGPT LLM response", "/dataforseo/ai_optimization/chat_gpt/llm_responses/live", 0.012, 0.055),
    "dfs_perplexity": ("Perplexity LLM response", "/dataforseo/ai_optimization/perplexity/llm_responses/live", 0.012, 0.036),
    "dfs_gemini": ("Gemini LLM response", "/dataforseo/ai_optimization/gemini/llm_responses/live", 0.012, 0.055),
    "dfs_claude": ("Claude LLM response", "/dataforseo/ai_optimization/claude/llm_responses/live", 0.012, 0.055),
    "dfs_backlinks_summary": ("Backlinks summary", "/dataforseo/backlinks/summary/live", 0.012, 0.048),
    "sem_keyword_overview": ("SEMrush keyword overview", "/semrush/keyword-overview", 0.003, 0.003),
    "sem_domain_overview": ("SEMrush domain overview", "/semrush/domain-overview", 0.003, 0.003),
    "sem_backlinks_overview": ("SEMrush backlinks overview", "/semrush/backlinks-overview", 0.01, 0.01),
    "sem_url_organic_keywords": ("SEMrush URL organic keywords", "/semrush/url-organic-keywords", 0.09, 0.09),
    "sem_question_keywords": ("SEMrush question keywords", "/semrush/question-keywords", 0.36, 0.36),
    "oxy_ai_search": ("Oxylabs AI search", "/oxylabs/ai-search", 0.001, 0.001),
    "chat": ("AIsa LLM gateway", "/v1/chat/completions", 0.01, 0.03),
}

STOPWORDS = set(
    """a an the and or but if then else of for to in on at by with from as is are was were be been
    being it its this that these those there here how what why when where which who whom can could
    should would will shall may might must do does did done have has had not no nor so than too very
    your you we our us they them their i me my he she his her about into over under between after before
    up down out off again further once all any both each few more most other some such only own same
    also just get got make made use used using one two three""".split()
)
GENERIC_HEADINGS = {
    "overview", "introduction", "conclusion", "summary", "background", "details", "more", "notes",
    "faq", "faqs", "resources", "references", "final thoughts", "wrap up", "about", "next steps",
}
QUESTION_STARTERS = ("what", "how", "why", "when", "where", "which", "who", "can", "does", "do", "is", "are", "should", "will")
DEFINITION_VERBS = ("is", "are", "refers to", "means", "describes", "lets", "helps", "allows")


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def _resolve_aisa_api_key() -> str:
    """Resolve AISA_API_KEY from the environment, then from known credential files.

    os.environ is not always populated. The plugin / OpenClaw install form has no
    profile .env to inherit from, and hermes' sandboxed code-execution path
    strips variables whose name contains "KEY". `~/.aisa/credentials` is the
    cross-harness convention AgentSpec already documents for exactly this case
    (plugin-core/inject.ts: "scripts resolve these as: env var ->
    ~/.aisa/credentials").

    Order: env -> ~/.aisa/credentials
           -> $HERMES_HOME/profiles/$HERMES_PROFILE/.env (when HERMES_PROFILE is set)
           -> $HERMES_HOME/.env

    Under `hermes --profile X`, HERMES_HOME *is* the profile directory and
    HERMES_PROFILE is unset, so the last candidate resolves to that profile's own
    .env; the middle one covers harnesses that identify the profile by name
    instead. Only the running profile is ever read, never a sibling's, so a host
    with several profiles cannot hand back the wrong tenant's key.

    Returns "" when nothing is found; never raises on an unreadable or
    undecodable file.

    Kept byte-identical across the AIsa skills that need it —
    financial/marketpulse/scripts/market_client.py is the canonical copy; change
    it there first, then propagate.
    """
    key = os.environ.get("AISA_API_KEY", "").strip()
    if key:
        return key

    home = os.path.expanduser("~")
    hermes_home = os.environ.get("HERMES_HOME") or os.path.join(home, ".hermes")

    candidates = [os.path.join(home, ".aisa", "credentials")]
    profile = os.environ.get("HERMES_PROFILE", "").strip()
    if profile:
        candidates.append(os.path.join(hermes_home, "profiles", profile, ".env"))
    candidates.append(os.path.join(hermes_home, ".env"))

    for path in candidates:
        try:
            # utf-8-sig drops a BOM; errors="replace" keeps a mis-encoded file
            # from raising UnicodeDecodeError (a ValueError, not an OSError).
            with open(path, encoding="utf-8-sig", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            name, sep, value = line.partition("=")
            if not sep or name.strip() != "AISA_API_KEY":
                continue
            value = value.strip()
            if value[:1] in ("'", '"'):
                # A quoted value ends at its closing quote; whatever follows is
                # a trailing comment, not part of the secret. Checking "starts
                # and ends with a quote" instead would miss `KEY="v" # note`
                # and hand back the value with its quotes still attached.
                end = value.find(value[0], 1)
                value = value[1:end] if end != -1 else value[1:]
            else:
                for marker in (" #", "\t#"):
                    if marker in value:
                        value = value.split(marker, 1)[0]
                value = value.strip()
            # U+FFFD only appears where bytes failed to decode, so the value is
            # corrupt and cannot be a real key — keep looking rather than send
            # garbage as a bearer token.
            if value and "�" not in value:
                return value
    return ""


def api_key() -> str:
    key = _resolve_aisa_api_key()
    if not key:
        raise RuntimeError(
            "AISA_API_KEY is required. Set the environment variable or add "
            "AISA_API_KEY=<key> to ~/.aisa/credentials. Get a key at https://aisa.one"
        )
    return key


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def write_text(path: Optional[str], content: str) -> None:
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    else:
        print(content, end="" if content.endswith("\n") else "\n")


def write_json(path: Optional[str], data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def domain_of(url: str) -> str:
    try:
        host = urllib.parse.urlsplit(url).netloc.lower()
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9'-]*", text.lower()) if t not in STOPWORDS and len(t) > 1]


def has_cjk(text: str) -> bool:
    sample = text[:4000]
    cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", sample))
    return cjk > 0 and cjk / max(1, len(sample)) > 0.2


def count_words(text: str) -> int:
    if has_cjk(text):
        cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", text))
        latin = len(re.findall(r"[A-Za-z0-9]+", text))
        return cjk + latin
    return len(re.findall(r"\S+", text))


def contains_phrase(text: str, phrase: str) -> bool:
    return bool(phrase) and phrase.lower() in text.lower()


def phrase_token_coverage(text: str, phrase: str) -> float:
    """Fraction of the phrase's meaningful tokens that occur in text."""
    needed = tokens(phrase)
    if not needed:
        return 1.0 if contains_phrase(text, phrase) else 0.0
    present = set(tokens(text))
    return sum(1 for t in needed if t in present) / len(needed)


def md_escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def truncate(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_json_loose(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty LLM response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("LLM response is not JSON")


def find_all(obj: Any, key: str) -> List[Any]:
    """Depth-first collection of every value stored under `key`."""
    found: List[Any] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                found.append(v)
            found.extend(find_all(v, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_all(item, key))
    return found


def collect_urls(obj: Any) -> List[str]:
    urls: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k in ("url", "link", "source_url", "href") and v.startswith("http"):
                urls.append(v)
            else:
                urls.extend(collect_urls(v))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str) and item.startswith("http"):
                urls.append(item)
            else:
                urls.extend(collect_urls(item))
    return urls


def collect_text(obj: Any, keys: Tuple[str, ...]) -> str:
    parts: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                if isinstance(v, str):
                    parts.append(v)
                else:
                    parts.append(collect_text(v, ("text", "content", "answer_text", "markdown") + keys))
            else:
                parts.append(collect_text(v, keys))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                parts.append(item)
            else:
                parts.append(collect_text(item, keys))
    return " ".join(p for p in parts if p)


def dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ---------------------------------------------------------------------------
# Cache + spend ledger
# ---------------------------------------------------------------------------


class Cache:
    def __init__(self, directory: Optional[str]) -> None:
        self.dir = Path(directory) if directory else None
        if self.dir:
            self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(endpoint: str, payload: Any) -> str:
        raw = endpoint + "\n" + json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def get(self, endpoint: str, payload: Any) -> Optional[Any]:
        if not self.dir:
            return None
        path = self.dir / (self.key(endpoint, payload) + ".json")
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8")).get("response")
        except (OSError, json.JSONDecodeError):
            return None

    def put(self, endpoint: str, payload: Any, response: Any) -> None:
        if not self.dir:
            return
        path = self.dir / (self.key(endpoint, payload) + ".json")
        record = {"endpoint": endpoint, "payload": payload, "cached_at": now_iso(), "response": response}
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


class Ledger:
    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []
        self.chat_tokens = 0

    def record(self, stage: str, call_id: str, status: str, actual: Optional[float] = None,
               cached: bool = False, error: Optional[str] = None, n: int = 1) -> None:
        label, endpoint, nominal, _max = COSTS[call_id]
        self.entries.append({
            "stage": stage,
            "call_id": call_id,
            "label": label,
            "endpoint": endpoint,
            "nominal_usd": 0.0 if cached else round(nominal * n, 4),
            "actual_usd": None if cached else actual,
            "status": status,
            "cached": cached,
            "error": error,
        })

    def summary(self) -> Dict[str, Any]:
        nominal = sum(e["nominal_usd"] for e in self.entries)
        actual_known = [e["actual_usd"] for e in self.entries if e["actual_usd"] is not None]
        estimated = 0.0
        for e in self.entries:
            if e["cached"]:
                continue
            estimated += e["actual_usd"] if e["actual_usd"] is not None else e["nominal_usd"]
        return {
            "nominal_total_usd": round(nominal, 4),
            "actual_dataforseo_usd": round(sum(actual_known), 4) if actual_known else None,
            "estimated_total_usd": round(estimated, 4),
            "semrush_calls": sum(1 for e in self.entries if e["call_id"].startswith("sem_") and not e["cached"]),
            "oxylabs_calls": sum(1 for e in self.entries if e["call_id"] == "oxy_ai_search" and not e["cached"]),
            "dataforseo_calls": sum(1 for e in self.entries if e["call_id"].startswith("dfs_") and not e["cached"]),
            "chat_calls": sum(1 for e in self.entries if e["call_id"] == "chat" and not e["cached"]),
            "chat_tokens": self.chat_tokens,
            "cache_hits": sum(1 for e in self.entries if e["cached"]),
            "entries": self.entries,
        }


# ---------------------------------------------------------------------------
# AIsa client
# ---------------------------------------------------------------------------


class Aisa:
    def __init__(self, ledger: Ledger, cache: Cache, model: str = DEFAULT_MODEL) -> None:
        self.ledger = ledger
        self.cache = cache
        self.model = model
        self._key: Optional[str] = None

    def key(self) -> str:
        if self._key is None:
            self._key = api_key()
        return self._key

    def _request(self, method: str, url: str, body: Optional[bytes] = None,
                 headers: Optional[Dict[str, str]] = None, timeout: int = SLOW_TIMEOUT,
                 retries: int = 2) -> str:
        base_headers = {"Authorization": f"Bearer {self.key()}", "User-Agent": USER_AGENT}
        if body is not None:
            base_headers["Content-Type"] = "application/json"
        base_headers.update(headers or {})
        request = urllib.request.Request(url, data=body, method=method, headers=base_headers)
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=timeout, context=ssl_context()) as response:
                    return response.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if attempt < retries and (exc.code == 429 or exc.code >= 500):
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"HTTP {exc.code} from {url}: {truncate(detail, 300)}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"Request failed for {url}: {exc}") from exc
        raise RuntimeError(f"Request failed for {url}")

    # -- DataForSEO -------------------------------------------------------

    def dfs(self, call_id: str, task: Dict[str, Any], stage: str, timeout: int = SLOW_TIMEOUT) -> List[Any]:
        endpoint = COSTS[call_id][1]
        payload = [task]
        cached = self.cache.get(endpoint, payload)
        if cached is not None:
            self.ledger.record(stage, call_id, "ok", cached=True)
            return self._dfs_unwrap(cached, endpoint)[0]
        try:
            text = self._request("POST", DATA_BASE + endpoint, json.dumps(payload).encode("utf-8"), timeout=timeout)
            response = json.loads(text) if text else {}
            result, cost = self._dfs_unwrap(response, endpoint)
        except Exception as exc:
            self.ledger.record(stage, call_id, "error", error=str(exc))
            raise
        self.cache.put(endpoint, payload, response)
        self.ledger.record(stage, call_id, "ok", actual=cost)
        return result

    @staticmethod
    def _dfs_unwrap(response: Any, endpoint: str) -> Tuple[List[Any], Optional[float]]:
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected DataForSEO response from {endpoint}")
        code = response.get("status_code")
        if code is not None and code != 20000:
            raise RuntimeError(f"DataForSEO {code}: {response.get('status_message')} ({endpoint})")
        tasks = response.get("tasks") or []
        if not tasks:
            raise RuntimeError(f"DataForSEO returned no tasks ({endpoint})")
        task = tasks[0] or {}
        if task.get("status_code") not in (None, 20000):
            raise RuntimeError(f"DataForSEO task {task.get('status_code')}: {task.get('status_message')} ({endpoint})")
        cost: Optional[float] = None
        for candidate in (task.get("cost"), response.get("cost")):
            if isinstance(candidate, (int, float)):
                cost = float(candidate)
                break
        return list(task.get("result") or []), cost

    # -- SEMrush ----------------------------------------------------------

    def semrush(self, call_id: str, params: Dict[str, str], stage: str) -> List[Dict[str, str]]:
        endpoint = COSTS[call_id][1]
        cached = self.cache.get(endpoint, params)
        if cached is not None:
            self.ledger.record(stage, call_id, "ok", cached=True)
            return self._semrush_rows(cached, endpoint)
        url = DATA_BASE + endpoint + "?" + urllib.parse.urlencode(params)
        try:
            try:
                text = self._request("GET", url, timeout=FAST_TIMEOUT)
            except RuntimeError as exc:
                # Some SEMrush routes reject `database` ("request does not match
                # the endpoint contract") while others require it; retry without.
                if "endpoint contract" in str(exc) and "database" in params:
                    slim = {k: v for k, v in params.items() if k != "database"}
                    text = self._request("GET", DATA_BASE + endpoint + "?" + urllib.parse.urlencode(slim), timeout=FAST_TIMEOUT)
                else:
                    raise
            rows = self._semrush_rows(text, endpoint)
        except Exception as exc:
            self.ledger.record(stage, call_id, "error", error=str(exc))
            raise
        self.cache.put(endpoint, params, text)
        self.ledger.record(stage, call_id, "ok")
        return rows

    @staticmethod
    def _semrush_rows(text: str, endpoint: str) -> List[Dict[str, str]]:
        body = (text or "").strip()
        if body.startswith("{") or body.startswith("["):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = None
            if isinstance(data, dict) and ("error" in data or "message" in data):
                raise RuntimeError(f"SEMrush error ({endpoint}): {truncate(json.dumps(data), 200)}")
            raise RuntimeError(f"SEMrush returned unexpected JSON ({endpoint})")
        if body.upper().startswith("ERROR"):
            raise RuntimeError(f"SEMrush {body.splitlines()[0]} ({endpoint})")
        lines = [line for line in body.splitlines() if line.strip()]
        if len(lines) < 2:
            return []
        header = [h.strip() for h in lines[0].split(";")]
        rows = []
        for line in lines[1:]:
            cells = [c.strip() for c in line.split(";")]
            rows.append({header[i]: cells[i] for i in range(min(len(header), len(cells)))})
        return rows

    # -- Oxylabs ----------------------------------------------------------

    def oxylabs(self, body: Dict[str, Any], stage: str, timeout: int = SLOW_TIMEOUT) -> Any:
        call_id = "oxy_ai_search"
        endpoint = COSTS[call_id][1]
        cached = self.cache.get(endpoint, body)
        if cached is not None:
            self.ledger.record(stage, call_id, "ok", cached=True)
            return cached
        try:
            text = self._request("POST", DATA_BASE + endpoint, json.dumps(body).encode("utf-8"), timeout=timeout, retries=1)
            response = json.loads(text) if text else {}
        except Exception as exc:
            self.ledger.record(stage, call_id, "error", error=str(exc))
            raise
        self.cache.put(endpoint, body, response)
        self.ledger.record(stage, call_id, "ok")
        return response

    # -- LLM gateway ------------------------------------------------------

    def chat(self, system: str, user: str, stage: str, json_mode: bool = True) -> str:
        call_id = "chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        cached = self.cache.get(CHAT_URL, payload)
        if cached is not None:
            self.ledger.record(stage, call_id, "ok", cached=True)
            return self._chat_content(cached)
        try:
            text = self._request("POST", CHAT_URL, json.dumps(payload).encode("utf-8"), timeout=SLOW_TIMEOUT, retries=1)
            response = json.loads(text) if text else {}
            content = self._chat_content(response)
        except Exception as exc:
            self.ledger.record(stage, call_id, "error", error=str(exc))
            raise
        usage = response.get("usage") or {}
        self.ledger.chat_tokens += int(usage.get("total_tokens") or 0)
        self.cache.put(CHAT_URL, payload, response)
        self.ledger.record(stage, call_id, "ok")
        return content

    @staticmethod
    def _chat_content(response: Any) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"LLM gateway returned no content: {truncate(json.dumps(response), 300)}")
        if isinstance(content, list):
            content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content)


# ---------------------------------------------------------------------------
# Article model
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.startswith(" ") or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value[:1] in ("'", '"') and value[-1:] == value[:1]:
            value = value[1:-1]
        meta[key.strip().lower()] = value
    return meta, text[match.end():]


def strip_code_blocks(text: str) -> Tuple[str, int]:
    count = len(re.findall(r"```", text)) // 2
    without = re.sub(r"```.*?```", "", text, flags=re.S)
    without = re.sub(r"`[^`\n]+`", " ", without)
    return without, count


def markdown_to_plain(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+[.)]\s+", "", text, flags=re.M)
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    text = re.sub(r"^\|.*\|\s*$", " ", text, flags=re.M)
    return text


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def syllables(word: str) -> int:
    word = word.lower()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee")) and count > 1:
        count -= 1
    return max(1, count)


def flesch_reading_ease(text: str) -> Optional[float]:
    if has_cjk(text):
        return None
    words = re.findall(r"[A-Za-z]+", text)
    sentences = split_sentences(text)
    if len(words) < 50 or not sentences:
        return None
    syl = sum(syllables(w) for w in words)
    score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syl / len(words))
    return round(score, 1)


STAT_PATTERN = re.compile(
    r"(\$\s?\d[\d,.]*\s?(?:k|m|bn|million|billion|trillion)?|\d[\d,.]*\s?%|\d[\d,.]*\s?(?:x|×)\b|\d[\d,.]*\s?(?:million|billion|trillion|thousand)\b|\b\d{2,3}\s?(?:percent)\b)",
    re.I,
)


def extract_statistics(plain_text: str, raw_text: str) -> List[Dict[str, Any]]:
    stats: List[Dict[str, Any]] = []
    for sentence in split_sentences(raw_text):
        matches = STAT_PATTERN.findall(sentence)
        if not matches:
            continue
        cited = bool(re.search(r"\]\(https?://|https?://\S+|\[\d+\]|\(source|according to", sentence, re.I))
        stats.append({"sentence": truncate(markdown_to_plain(sentence), 200), "values": dedupe([m.strip() for m in matches])[:5], "cited": cited})
    return stats


def is_question_heading(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered.endswith("?") or lowered.split(" ")[0].rstrip(":") in QUESTION_STARTERS


def parse_markdown(text: str, source: str, site_domain: Optional[str]) -> Dict[str, Any]:
    meta, body = parse_frontmatter(text)
    body_no_code, code_blocks = strip_code_blocks(body)
    lines = body_no_code.splitlines()

    headings: List[Dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if match:
            headings.append({"level": len(match.group(1)), "text": match.group(2).strip(), "line": index})

    # Section word counts (text between headings)
    sections: List[Dict[str, Any]] = []
    for pos, heading in enumerate(headings):
        start = heading["line"] + 1
        end = headings[pos + 1]["line"] if pos + 1 < len(headings) else len(lines)
        section_text = markdown_to_plain("\n".join(lines[start:end]))
        sections.append({"heading": heading["text"], "level": heading["level"], "word_count": count_words(section_text)})

    body_no_h1 = re.sub(r"^\s{0,3}#\s+.*$", "", body_no_code, flags=re.M)
    plain = markdown_to_plain(body_no_h1)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", plain) if p.strip()]
    paragraph_word_counts = [count_words(p) for p in paragraphs]

    links = []
    for label, url in re.findall(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", body_no_code):
        links.append({"text": label, "url": url})
    for url in re.findall(r"(?<![\(\"'])\bhttps?://[^\s)\]>]+", body_no_code):
        if not any(link["url"] == url for link in links):
            links.append({"text": "", "url": url})
    internal, external = [], []
    for link in links:
        url = link["url"]
        if url.startswith("#"):
            continue
        host = domain_of(url) if url.startswith("http") else ""
        if not url.startswith("http") or (site_domain and host.endswith(site_domain)):
            internal.append(link)
        else:
            external.append(link)

    images = [{"alt": alt.strip(), "url": url} for alt, url in re.findall(r"!\[([^\]]*)\]\(([^)\s]+)", body_no_code)]
    video = bool(re.search(r"youtube\.com|youtu\.be|vimeo\.com|<video|\.mp4", body, re.I))

    h1s = [h for h in headings if h["level"] == 1]
    title = meta.get("title") or (h1s[0]["text"] if h1s else "")
    slug = meta.get("slug") or Path(source).stem if not source.startswith("http") else ""
    first_paragraph = ""
    for paragraph in paragraphs:
        if paragraph.strip() and paragraph.strip() != title.strip():
            first_paragraph = paragraph
            break

    faq = any(re.search(r"\bfaq|frequently asked", h["text"], re.I) for h in headings)
    if not faq:
        run = 0
        for heading in headings:
            run = run + 1 if is_question_heading(heading["text"]) else 0
            if run >= 3:
                faq = True
                break

    lists = len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s+", body_no_code, re.M))
    tables = len(re.findall(r"^\s*\|.*\|\s*$", body_no_code, re.M))
    blockquotes = len(re.findall(r"^\s{0,3}>", body_no_code, re.M))
    tldr = bool(re.search(r"tl;?dr|key takeaways|quick answer|in short|summary:", body_no_code[:3000], re.I))

    date = meta.get("date") or meta.get("published") or meta.get("updated") or meta.get("last_updated") or ""
    author = meta.get("author") or meta.get("authors") or ""
    schema_types = []
    for key in ("schema", "schema_type", "schematype", "type"):
        if meta.get(key):
            schema_types.append(meta[key])

    return {
        "mode": "file",
        "source": source,
        "domain": site_domain or "",
        "url": meta.get("canonical") or "",
        "slug": slug,
        "title": title,
        "meta_description": meta.get("description") or meta.get("meta_description") or "",
        "h1": h1s[0]["text"] if h1s else "",
        "h1_count": len(h1s),
        "headings": headings,
        "sections": sections,
        "word_count": count_words(plain),
        "first_paragraph": first_paragraph,
        "paragraph_word_counts": paragraph_word_counts,
        "links": {"internal": internal, "external": external},
        "images": images,
        "has_video": video,
        "stats": extract_statistics(plain, body_no_code),
        "has_faq": faq,
        "has_tldr": tldr,
        "lists": lists,
        "tables": tables,
        "blockquotes": blockquotes,
        "code_blocks": code_blocks,
        "author": author,
        "date": date,
        "schema_types": schema_types,
        "robots": meta.get("robots") or "",
        "language_cjk": has_cjk(plain),
        "text": plain,
    }


class _HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: Dict[str, str] = {}
        self.canonical = ""
        self.jsonld: List[str] = []
        self.images: List[Dict[str, str]] = []
        self.links: List[str] = []
        self.headings: List[Dict[str, Any]] = []
        self.paragraphs: List[str] = []
        self.has_video = False
        self._stack: List[str] = []
        self._buffer: List[str] = []
        self._in_jsonld = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attributes = {k: (v or "") for k, v in attrs}
        if tag in ("script", "style", "noscript"):
            if tag == "script" and "ld+json" in attributes.get("type", ""):
                self._in_jsonld = True
            else:
                self._skip += 1
            return
        if tag == "meta":
            name = (attributes.get("name") or attributes.get("property") or "").lower()
            if name:
                self.meta[name] = attributes.get("content", "")
        elif tag == "link" and attributes.get("rel", "").lower() == "canonical":
            self.canonical = attributes.get("href", "")
        elif tag == "img":
            self.images.append({"alt": attributes.get("alt", ""), "url": attributes.get("src", "")})
        elif tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        elif tag in ("video", "iframe"):
            self.has_video = True
        if tag in ("title", "h1", "h2", "h3", "h4", "h5", "h6", "p", "li"):
            self._stack.append(tag)
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            if self._in_jsonld:
                self._in_jsonld = False
            elif self._skip:
                self._skip -= 1
            return
        if self._stack and self._stack[-1] == tag:
            text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
            self._stack.pop()
            if tag == "title" and not self.title:
                self.title = text
            elif tag.startswith("h") and text:
                self.headings.append({"level": int(tag[1]), "text": text, "line": len(self.headings)})
            elif text:
                self.paragraphs.append(text)

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self.jsonld.append(data)
        elif self._skip == 0 and self._stack:
            self._buffer.append(data)


def fetch_head_signals(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AIsaReview/1.0)"})
    with urllib.request.urlopen(request, timeout=30, context=ssl_context()) as response:
        html_text = response.read(2_000_000).decode("utf-8", errors="replace")
    parser = _HeadParser()
    parser.feed(html_text)
    schema_types: List[str] = []
    for blob in parser.jsonld:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        for value in find_all(data, "@type"):
            if isinstance(value, str):
                schema_types.append(value)
            elif isinstance(value, list):
                schema_types.extend(str(v) for v in value)
    return {
        "title": parser.title,
        "meta": parser.meta,
        "canonical": parser.canonical,
        "schema_types": dedupe(schema_types),
        "images": parser.images,
        "links": parser.links,
        "headings": parser.headings,
        "paragraphs": parser.paragraphs,
        "has_video": parser.has_video,
    }


def flatten_page_content(page_content: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    headings: List[Dict[str, Any]] = []
    paragraphs: List[str] = []
    header = page_content.get("header") or {}
    for block in (header.get("primary_content") or []):
        if isinstance(block, dict) and block.get("text"):
            paragraphs.append(block["text"])
    for topic in (page_content.get("main_topic") or []) + (page_content.get("secondary_topic") or []):
        if not isinstance(topic, dict):
            continue
        title = topic.get("h_title") or topic.get("main_title") or ""
        level = topic.get("level") or 2
        if title:
            headings.append({"level": int(level) if str(level).isdigit() else 2, "text": str(title).strip(), "line": len(headings)})
        for block in (topic.get("primary_content") or []) + (topic.get("secondary_content") or []):
            if isinstance(block, dict) and block.get("text"):
                paragraphs.append(str(block["text"]))
    return headings, paragraphs


def parse_url(url: str, client: Optional[Aisa], site_domain: Optional[str]) -> Dict[str, Any]:
    domain = site_domain or domain_of(url)
    warnings: List[str] = []
    head: Dict[str, Any] = {}
    try:
        head = fetch_head_signals(url)
    except Exception as exc:  # non-fatal
        warnings.append(f"Direct fetch of {url} failed: {exc}")

    headings: List[Dict[str, Any]] = []
    paragraphs: List[str] = []
    if client is not None:
        try:
            result = client.dfs("dfs_content_parsing", {"url": url}, "parse")
            items = (result[0] or {}).get("items") if result else None
            page_content = (items[0] or {}).get("page_content") if items else None
            if page_content:
                headings, paragraphs = flatten_page_content(page_content)
            else:
                warnings.append("DataForSEO content_parsing returned no page_content")
        except Exception as exc:
            warnings.append(f"DataForSEO content_parsing failed: {exc}")
    if not headings and head.get("headings"):
        headings = head["headings"]
    if not paragraphs and head.get("paragraphs"):
        paragraphs = head["paragraphs"]

    plain = "\n\n".join(paragraphs)
    meta = head.get("meta", {})
    h1s = [h for h in headings if h["level"] == 1]
    title = (h1s[0]["text"] if h1s else "") or head.get("title", "")
    path = urllib.parse.urlsplit(url).path.rstrip("/")
    slug = path.split("/")[-1] if path else ""
    internal, external = [], []
    for href in head.get("links", []):
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        host = domain_of(href) if href.startswith("http") else ""
        if not href.startswith("http") or host.endswith(domain):
            internal.append({"text": "", "url": href})
        else:
            external.append({"text": "", "url": href})
    sections = []
    for pos, heading in enumerate(headings):
        sections.append({"heading": heading["text"], "level": heading["level"], "word_count": None})
    first_paragraph = paragraphs[0] if paragraphs else ""
    date = meta.get("article:published_time") or meta.get("article:modified_time") or meta.get("date") or ""
    author = meta.get("author") or meta.get("article:author") or ""
    faq = any(re.search(r"\bfaq|frequently asked", h["text"], re.I) for h in headings) or "FAQPage" in head.get("schema_types", [])
    return {
        "mode": "url",
        "source": url,
        "domain": domain,
        "url": url,
        "slug": slug,
        "title": title,
        "meta_description": meta.get("description", ""),
        "h1": h1s[0]["text"] if h1s else "",
        "h1_count": len(h1s),
        "headings": headings,
        "sections": sections,
        "word_count": count_words(plain),
        "first_paragraph": first_paragraph,
        "paragraph_word_counts": [count_words(p) for p in paragraphs],
        "links": {"internal": internal, "external": external},
        "images": head.get("images", []),
        "has_video": head.get("has_video", False),
        "stats": extract_statistics(plain, plain),
        "has_faq": faq,
        "has_tldr": bool(re.search(r"tl;?dr|key takeaways|quick answer|in short", plain[:3000], re.I)),
        "lists": sum(1 for p in paragraphs if len(p) < 200),
        "tables": 0,
        "blockquotes": 0,
        "code_blocks": 0,
        "author": author,
        "date": date,
        "schema_types": head.get("schema_types", []),
        "robots": meta.get("robots", ""),
        "language_cjk": has_cjk(plain),
        "text": plain,
        "warnings": warnings,
    }


def load_article(source: str, client: Optional[Aisa], site_domain: Optional[str]) -> Dict[str, Any]:
    if source.startswith("http://") or source.startswith("https://"):
        return parse_url(source, client, site_domain)
    path = Path(source)
    if not path.exists():
        raise ValueError(f"Article not found: {source}")
    return parse_markdown(path.read_text(encoding="utf-8"), str(path), site_domain)


def article_public(article: Dict[str, Any]) -> Dict[str, Any]:
    public = {k: v for k, v in article.items() if k != "text"}
    public["text_preview"] = truncate(article.get("text", ""), 400)
    return public


# ---------------------------------------------------------------------------
# Keyword helpers
# ---------------------------------------------------------------------------


def heuristic_keyword(article: Dict[str, Any]) -> str:
    title = article.get("title") or article.get("h1") or ""
    body = article.get("text", "").lower()
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9'-]*", title.lower())]
    best, best_score = "", 0.0
    for n in (4, 3, 2, 1):
        for i in range(0, max(0, len(words) - n + 1)):
            gram = words[i : i + n]
            if gram[0] in STOPWORDS or gram[-1] in STOPWORDS:
                continue
            phrase = " ".join(gram)
            freq = body.count(phrase)
            if freq == 0:
                continue
            score = freq * (n ** 2)
            if score > best_score:
                best, best_score = phrase, score
    if not best:
        toks = tokens(title)
        best = " ".join(toks[:3]) if toks else "article"
    return best


# ---------------------------------------------------------------------------
# Stage functions
# ---------------------------------------------------------------------------

KEYWORD_SYSTEM = (
    "You are an SEO/GEO editor. Use only the facts provided. Never invent metrics, volumes, "
    "rankings, or citations. Output strictly the requested JSON object and nothing else."
)


def stage_keywords(article: Dict[str, Any], args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    out: Dict[str, Any] = {"primary": {}, "secondary": [], "entities": [], "source": "", "metrics_source": []}
    if args.keyword:
        out["primary"] = {"keyword": args.keyword.strip(), "rationale": "provided by user"}
        out["source"] = "user"
    elif not args.no_llm:
        headings = "\n".join(f"{'#' * h['level']} {h['text']}" for h in article["headings"][:40])
        freq: Dict[str, int] = {}
        for tok in tokens(article["text"]):
            freq[tok] = freq.get(tok, 0) + 1
        top_terms = ", ".join(t for t, _ in sorted(freq.items(), key=lambda kv: -kv[1])[:20])
        prompt = (
            "Identify the primary search keyword this article targets and up to 5 secondary keywords.\n"
            "Rules: 1-5 words each; must appear in or be strongly implied by the text; primary keyword should "
            "match how a searcher would phrase the topic; do not include brand names unless the article is about them.\n"
            f"Title: {article.get('title')}\nMeta description: {article.get('meta_description')}\n"
            f"H1: {article.get('h1')}\nHeadings:\n{headings}\n\nFirst 300 words:\n{truncate(article['text'], 1800)}\n\n"
            f"Frequent terms: {top_terms}\n\n"
            'Return JSON: {"primary": {"keyword": "...", "rationale": "..."}, '
            '"secondary": [{"keyword": "...", "rationale": "..."}], "entities": ["..."]}'
        )
        try:
            data = parse_json_loose(client.chat(KEYWORD_SYSTEM, prompt, "keywords"))
            primary = data.get("primary") or {}
            if isinstance(primary, str):
                primary = {"keyword": primary, "rationale": ""}
            out["primary"] = {"keyword": str(primary.get("keyword", "")).strip(), "rationale": str(primary.get("rationale", ""))}
            secondary = []
            for item in (data.get("secondary") or [])[:5]:
                if isinstance(item, str):
                    secondary.append({"keyword": item.strip(), "rationale": ""})
                elif isinstance(item, dict) and item.get("keyword"):
                    secondary.append({"keyword": str(item["keyword"]).strip(), "rationale": str(item.get("rationale", ""))})
            out["secondary"] = secondary
            out["entities"] = [str(e) for e in (data.get("entities") or [])[:15]]
            out["source"] = "llm"
        except Exception as exc:
            out["warning"] = f"LLM keyword extraction failed, fell back to heuristic: {exc}"
    if not out["primary"].get("keyword"):
        out["primary"] = {"keyword": heuristic_keyword(article), "rationale": "heuristic: most frequent title n-gram in body"}
        out["source"] = out["source"] or "heuristic"

    keywords = [out["primary"]["keyword"]] + [s["keyword"] for s in out["secondary"]]
    keywords = dedupe([k for k in keywords if k])
    metrics: Dict[str, Dict[str, Any]] = {k: {} for k in keywords}
    try:
        result = client.dfs(
            "dfs_keyword_overview",
            {"keywords": keywords[:20], "location_code": args.location_code, "language_code": args.language_code},
            "keywords",
        )
        items = (result[0] or {}).get("items") if result else []
        for item in items or []:
            kw = item.get("keyword")
            if not kw:
                continue
            info = item.get("keyword_info") or {}
            props = item.get("keyword_properties") or {}
            intent = item.get("search_intent_info") or {}
            metrics.setdefault(kw, {}).update({
                "search_volume": info.get("search_volume"),
                "cpc": info.get("cpc"),
                "competition": info.get("competition_level") or info.get("competition"),
                "keyword_difficulty": props.get("keyword_difficulty"),
                "intent": intent.get("main_intent"),
            })
        out["metrics_source"].append("dataforseo_keyword_overview")
    except Exception as exc:
        out["dataforseo_error"] = str(exc)

    try:
        rows = client.semrush("sem_keyword_overview", {"phrase": keywords[0], "database": args.database}, "keywords")
        if rows:
            row = rows[0]
            metrics.setdefault(keywords[0], {}).update({
                "semrush_search_volume": _to_number(row.get("SearchVolume") or row.get("Search Volume")),
                "semrush_cpc": _to_number(row.get("CPC")),
                "semrush_competition": _to_number(row.get("Competition")),
                "semrush_results": _to_number(row.get("NumberOfResults") or row.get("Number of Results")),
            })
            out["metrics_source"].append("semrush_keyword_overview")
    except Exception as exc:
        out["semrush_error"] = str(exc)

    if args.deep:
        try:
            result = client.dfs(
                "dfs_related_keywords",
                {"keyword": keywords[0], "location_code": args.location_code, "language_code": args.language_code, "limit": 20},
                "keywords",
            )
            related = []
            for item in ((result[0] or {}).get("items") or []) if result else []:
                kd = item.get("keyword_data") or {}
                related.append({
                    "keyword": kd.get("keyword"),
                    "search_volume": (kd.get("keyword_info") or {}).get("search_volume"),
                    "keyword_difficulty": (kd.get("keyword_properties") or {}).get("keyword_difficulty"),
                })
            out["related"] = [r for r in related if r.get("keyword")]
        except Exception as exc:
            out["related_error"] = str(exc)
        try:
            rows = client.semrush("sem_question_keywords", {"phrase": keywords[0], "database": args.database}, "keywords")
            out["questions"] = [{"keyword": r.get("Keyword"), "search_volume": _to_number(r.get("Search Volume"))} for r in rows][:20]
        except Exception as exc:
            out["questions_error"] = str(exc)

    out["metrics"] = metrics
    for key in ("primary",):
        out[key].update(metrics.get(out[key]["keyword"], {}))
    for item in out["secondary"]:
        item.update(metrics.get(item["keyword"], {}))
    return out


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in ("n/a", "na", "-"):
            return None
        number = float(text)
        return int(number) if number.is_integer() else number
    except ValueError:
        return None


def stage_serp(keyword: str, args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "keyword": keyword,
        "organic_top10": [],
        "paa": [],
        "featured_snippet": None,
        "ai_overview": {"present": False, "references": []},
        "related_searches": [],
        "item_types": [],
    }
    result = client.dfs(
        "dfs_serp_organic",
        {"keyword": keyword, "location_code": args.location_code, "language_code": args.language_code, "depth": 10},
        "serp",
    )
    page = result[0] if result else {}
    out["item_types"] = page.get("item_types") or []
    out["check_url"] = page.get("check_url")
    for item in page.get("items") or []:
        kind = item.get("type")
        if kind == "organic" and len(out["organic_top10"]) < 10:
            out["organic_top10"].append({
                "rank": item.get("rank_group"),
                "url": item.get("url"),
                "domain": item.get("domain"),
                "title": item.get("title"),
                "description": truncate(item.get("description") or "", 200),
            })
        elif kind == "people_also_ask":
            for sub in item.get("items") or []:
                if isinstance(sub, dict) and sub.get("title"):
                    out["paa"].append(sub["title"])
        elif kind == "featured_snippet":
            out["featured_snippet"] = {
                "url": item.get("url"),
                "domain": item.get("domain"),
                "title": item.get("title"),
                "description": truncate(item.get("description") or "", 300),
            }
        elif kind == "ai_overview":
            refs = []
            for ref in find_all(item, "references"):
                if isinstance(ref, list):
                    for r in ref:
                        if isinstance(r, dict) and r.get("url"):
                            refs.append({"url": r.get("url"), "domain": r.get("domain") or domain_of(r.get("url", "")), "title": r.get("title")})
            out["ai_overview"] = {
                "present": True,
                "asynchronous": bool(item.get("asynchronous_ai_overview")),
                "references": refs[:20],
                "text": truncate(collect_text(item, ("text", "markdown")), 600),
            }
        elif kind == "related_searches":
            out["related_searches"] = [s for s in (item.get("items") or []) if isinstance(s, str)][:10]
    out["paa"] = dedupe(out["paa"])[:12]
    return out


def parse_competitor_page(url: str, args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    result = client.dfs("dfs_content_parsing", {"url": url}, "competitors")
    items = (result[0] or {}).get("items") if result else None
    page_content = (items[0] or {}).get("page_content") if items else None
    if not page_content:
        raise RuntimeError("no page_content")
    headings, paragraphs = flatten_page_content(page_content)
    text = "\n".join(paragraphs)
    return {"headings": [h["text"] for h in headings][:40], "word_count": count_words(text), "text_preview": truncate(text, 300)}


def stage_competitors(serp: Dict[str, Any], article: Dict[str, Any], args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    top = [o for o in serp.get("organic_top10", []) if o.get("url")]
    own_domain = article.get("domain")
    competitors = [o for o in top if not (own_domain and o.get("domain", "").endswith(own_domain))][: args.top]
    out: Dict[str, Any] = {"items": [], "median_word_count": None, "missing_heading_terms": [], "shared_heading_terms": []}

    def work(entry: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(entry)
        try:
            record.update(parse_competitor_page(entry["url"], args, client))
        except Exception as exc:
            record["parse_error"] = str(exc)
        try:
            bare = entry["domain"][4:] if entry["domain"].startswith("www.") else entry["domain"]
            rows = client.semrush("sem_domain_overview", {"domain": bare, "database": args.database}, "competitors")
            if rows:
                row = rows[0]
                record["domain_rank"] = _to_number(row.get("Rank"))
                record["organic_keywords"] = _to_number(row.get("OrganicKeywords") or row.get("Organic Keywords"))
                record["organic_traffic"] = _to_number(row.get("OrganicTraffic") or row.get("Organic Traffic"))
        except Exception as exc:
            record["semrush_error"] = str(exc)
        return record

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        out["items"] = list(pool.map(work, competitors))

    counts = sorted(c["word_count"] for c in out["items"] if c.get("word_count"))
    if counts:
        mid = len(counts) // 2
        out["median_word_count"] = counts[mid] if len(counts) % 2 else (counts[mid - 1] + counts[mid]) // 2

    term_sets = []
    for comp in out["items"]:
        terms = set()
        for heading in comp.get("headings") or []:
            terms.update(t for t in tokens(heading) if len(t) >= 4)
        if terms:
            term_sets.append(terms)
    counter: Dict[str, int] = {}
    for terms in term_sets:
        for term in terms:
            counter[term] = counter.get(term, 0) + 1
    shared = sorted((t for t, c in counter.items() if c >= 2), key=lambda t: -counter[t])
    article_terms = set(tokens(article.get("text", "")) + tokens(" ".join(h["text"] for h in article.get("headings", []))))
    out["shared_heading_terms"] = shared[:40]
    out["missing_heading_terms"] = [t for t in shared if t not in article_terms][:25]
    return out


def stage_authority(article: Dict[str, Any], args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    target = article.get("domain") or ""
    try:
        rows = client.semrush("sem_backlinks_overview", {"target": target}, "authority")
        if rows:
            row = rows[0]
            out["backlinks"] = {
                "authority_score": _to_number(row.get("ascore")),
                "referring_domains": _to_number(row.get("referring_domains") or row.get("domains_num")),
                "total_backlinks": _to_number(row.get("total_backlinks") or row.get("total")),
            }
    except Exception as exc:
        out["backlinks_error"] = str(exc)
    if args.deep:
        try:
            rows = client.semrush("sem_url_organic_keywords", {"url": article["url"], "database": args.database}, "authority")
            out["url_organic_keywords"] = [
                {"keyword": r.get("Keyword"), "position": _to_number(r.get("Position")), "search_volume": _to_number(r.get("Search Volume"))}
                for r in rows
            ][:20]
        except Exception as exc:
            out["url_organic_keywords_error"] = str(exc)
        try:
            result = client.dfs("dfs_backlinks_summary", {"target": target, "include_subdomains": True}, "authority")
            summary = result[0] if result else {}
            out["dataforseo_backlinks"] = {
                "rank": summary.get("rank"),
                "backlinks": summary.get("backlinks"),
                "referring_domains": summary.get("referring_domains"),
            }
        except Exception as exc:
            out["dataforseo_backlinks_error"] = str(exc)
    return out


def _engine_result(engine: str, question: str) -> Dict[str, Any]:
    return {
        "engine": engine,
        "label": ENGINE_LABELS.get(engine, engine),
        "status": "ok",
        "question": question,
        "answer_excerpt": "",
        "cited": [],
        "article_cited": False,
        "domain_cited": False,
        "overlap_with_top10": [],
        "error": None,
    }


def _finish_engine(result: Dict[str, Any], urls: List[str], titles: Dict[str, str], article: Dict[str, Any], top10_domains: List[str]) -> Dict[str, Any]:
    cited = []
    for url in dedupe(urls)[:25]:
        if url.startswith("name:"):
            # Publisher name without a resolvable URL (Google AI Overview redirect links)
            cited.append({"url": "", "domain": url[len("name:"):].lower(), "title": url[len("name:"):]})
            continue
        cited.append({"url": url, "domain": domain_of(url), "title": titles.get(url, "")})
    result["cited"] = cited
    own_url = (article.get("url") or "").rstrip("/")
    own_domain = article.get("domain") or ""
    result["article_cited"] = bool(own_url) and any(c["url"].rstrip("/") == own_url for c in cited)
    result["domain_cited"] = bool(own_domain) and any(c["domain"].endswith(own_domain) for c in cited)
    result["overlap_with_top10"] = sorted({c["domain"] for c in cited if c["domain"] in top10_domains})
    if not cited and not result["answer_excerpt"] and result["status"] == "ok":
        result["status"] = "no_answer"
    return result


def run_engine(engine: str, keyword: str, question: str, article: Dict[str, Any], top10_domains: List[str],
               args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    result = _engine_result(engine, question)
    titles: Dict[str, str] = {}
    urls: List[str] = []
    try:
        if engine == "dfs_ai_mode":
            data = client.dfs(
                "dfs_ai_mode",
                {"keyword": keyword, "location_code": args.location_code, "language_code": args.language_code},
                "geo",
            )
            page = data[0] if data else {}
            for refs in find_all(page, "references"):
                if isinstance(refs, list):
                    for ref in refs:
                        if isinstance(ref, dict) and ref.get("url"):
                            urls.append(ref["url"])
                            if ref.get("title"):
                                titles[ref["url"]] = ref["title"]
            result["answer_excerpt"] = truncate(collect_text(page.get("items") or [], ("markdown", "text")), 700)
        elif engine == "dfs_llm_mentions":
            domains: List[Dict[str, Any]] = []
            for platform in ("google", "chat_gpt"):
                task = {
                    "target": [{"keyword": keyword, "match_type": "partial_match"}],
                    "platform": platform,
                    "items_list_limit": 10,
                }
                if platform == "google":
                    task["location_code"] = args.location_code
                    task["language_code"] = args.language_code
                try:
                    data = client.dfs("dfs_llm_mentions", task, "geo")
                    page = data[0] if data else {}
                    groups = (page.get("total") or {}).get("sources_domain") or page.get("items") or []
                    for item in groups:
                        if not isinstance(item, dict):
                            continue
                        name = item.get("key") or item.get("domain")
                        if name:
                            domains.append({"platform": platform, "domain": domain_of("https://" + str(name)), "mentions": item.get("mentions"), "ai_search_volume": item.get("ai_search_volume")})
                except Exception as exc:
                    result.setdefault("platform_errors", {})[platform] = str(exc)
            result["top_domains"] = domains
            urls = ["https://" + d["domain"] for d in domains]
            if not domains and result.get("platform_errors"):
                raise RuntimeError("; ".join(result["platform_errors"].values()))
        elif engine in LLM_RESPONSE_MODELS:
            endpoint, model_name = LLM_RESPONSE_MODELS[engine]
            task = {"user_prompt": truncate(question, 480), "model_name": model_name, "web_search": True}
            if engine == "dfs_perplexity":
                task["web_search_country_iso_code"] = "US"
            data = client.dfs(engine, task, "geo")
            page = data[0] if data else {}
            texts: List[str] = []
            for item in page.get("items") or []:
                if not isinstance(item, dict) or item.get("type") == "reasoning":
                    continue
                message = item.get("message") if isinstance(item.get("message"), dict) else item
                for section in (message or {}).get("sections") or []:
                    if isinstance(section, dict):
                        if section.get("text"):
                            texts.append(str(section["text"]))
                        for ann in section.get("annotations") or []:
                            if isinstance(ann, dict) and ann.get("url"):
                                urls.append(ann["url"])
                                if ann.get("title"):
                                    titles[ann["url"]] = ann["title"]
            if not urls:
                urls = collect_urls(page.get("items") or [])
            result["answer_excerpt"] = truncate(" ".join(texts) or collect_text(page.get("items") or [], ("text",)), 700)
            result["fan_out_queries"] = [q for q in (page.get("fan_out_queries") or []) if isinstance(q, str)][:10]
        else:
            source = engine[len("oxy_"):]
            body: Dict[str, Any] = {"source": source, "parse": True, "geo_location": args.geo_location}
            if source in ("google_search", "google_ai_mode"):
                body["query"] = keyword
                body["render"] = "html"
            else:
                body["prompt"] = question
                if source == "chatgpt":
                    body["search"] = True
            timeout = SLOW_TIMEOUT if source not in ("google_search", "google_ai_mode") else FAST_TIMEOUT
            response = client.oxylabs(body, "geo", timeout=timeout)
            results = response.get("results") if isinstance(response, dict) else None
            content = (results[0] or {}).get("content") if results else response
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    result["answer_excerpt"] = truncate(content, 700)
                    content = {}
            if source == "google_search":
                overviews = find_all(content, "ai_overviews")
                scope: Any = overviews[0] if overviews and overviews[0] else None
                if not scope:
                    result["status"] = "no_ai_overview"
                else:
                    # Google AI Overview references carry `/goto?url=` redirects; the
                    # `source` field holds the display domain or publisher name.
                    for refs in find_all(scope, "references"):
                        if isinstance(refs, list):
                            for ref in refs:
                                if not isinstance(ref, dict):
                                    continue
                                url = ref.get("url") or ""
                                source_name = str(ref.get("source") or "").strip()
                                if url.startswith("http"):
                                    urls.append(url)
                                elif "." in source_name and " " not in source_name:
                                    urls.append("https://" + source_name.lower())
                                elif source_name:
                                    urls.append("name:" + source_name)
                    result["answer_excerpt"] = truncate(collect_text(scope, ("answer_text", "text")), 700)
            else:
                urls = collect_urls(content)
                text = collect_text(content, ("response_text", "answer", "answer_text", "text", "markdown"))
                result["answer_excerpt"] = result["answer_excerpt"] or truncate(text, 700)
                for entry in find_all(content, "citations") + find_all(content, "top_sources") + find_all(content, "sources_results"):
                    if isinstance(entry, list):
                        for ref in entry:
                            if isinstance(ref, dict) and ref.get("url") and ref.get("title"):
                                titles[ref["url"]] = ref["title"]
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
    return _finish_engine(result, urls, titles, article, top10_domains)


def stage_geo(keyword: str, article: Dict[str, Any], serp: Dict[str, Any], args: argparse.Namespace, client: Aisa) -> Dict[str, Any]:
    question = article.get("title") or keyword
    if not is_question_heading(question):
        question = f"What is {keyword} and how do I get it right?" if len(keyword.split()) <= 4 else keyword
    top10_domains = [o.get("domain", "") for o in serp.get("organic_top10", [])]
    engines = list(args.engines)
    out: Dict[str, Any] = {"question": question, "engines": [], "cited_domain_frequency": {}, "overlap_with_top10": []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(engines))) as pool:
        futures = {pool.submit(run_engine, e, keyword, question, article, top10_domains, args, client): e for e in engines}
        results: Dict[str, Dict[str, Any]] = {}
        for future in concurrent.futures.as_completed(futures, timeout=SLOW_TIMEOUT + 30):
            engine = futures[future]
            try:
                results[engine] = future.result()
            except Exception as exc:  # pragma: no cover - defensive
                record = _engine_result(engine, question)
                record["status"] = "error"
                record["error"] = str(exc)
                results[engine] = record
    for engine in engines:
        if engine not in results:
            record = _engine_result(engine, question)
            record["status"] = "timeout"
            results[engine] = record
        out["engines"].append(results[engine])
    freq: Dict[str, int] = {}
    for engine_result in out["engines"]:
        if engine_result["engine"] == "dfs_llm_mentions":
            continue
        for cited in engine_result["cited"]:
            if cited["domain"]:
                freq[cited["domain"]] = freq.get(cited["domain"], 0) + 1
    out["cited_domain_frequency"] = dict(sorted(freq.items(), key=lambda kv: -kv[1])[:20])
    out["overlap_with_top10"] = sorted({d for d in freq if d in top10_domains})
    out["any_article_cited"] = any(e["article_cited"] for e in out["engines"])
    out["any_domain_cited"] = any(e["domain_cited"] for e in out["engines"])
    out["engines_answered"] = sum(1 for e in out["engines"] if e["status"] == "ok")
    return out


# ---------------------------------------------------------------------------
# Deterministic checks
# ---------------------------------------------------------------------------

SEO_DIMENSIONS = {
    "Keyword targeting": 25,
    "Metadata & structure": 15,
    "Content depth vs SERP": 25,
    "Links & media": 15,
    "Readability & E-E-A-T": 20,
}
GEO_DIMENSIONS = {
    "Answer-first": 20,
    "Question alignment": 20,
    "Citability": 20,
    "Structure & extractability": 15,
    "Authority & freshness": 10,
    "Current AI visibility": 15,
}


def _check(id_: str, area: str, dimension: str, weight: int, status: str, evidence: str, fix: str = "") -> Dict[str, Any]:
    return {"id": id_, "area": area, "dimension": dimension, "weight": weight, "status": status, "evidence": evidence, "fix": fix if status != "pass" else ""}


def _band(value: Optional[float], good: Tuple[float, float], okay: Tuple[float, float]) -> str:
    if value is None:
        return "fail"
    if good[0] <= value <= good[1]:
        return "pass"
    if okay[0] <= value <= okay[1]:
        return "warn"
    return "fail"


def _ratio_status(value: Optional[float], pass_at: float, warn_at: float) -> str:
    if value is None:
        return "na"
    if value >= pass_at:
        return "pass"
    if value >= warn_at:
        return "warn"
    return "fail"


def run_checks(article: Dict[str, Any], keywords: Dict[str, Any], serp: Dict[str, Any], competitors: Dict[str, Any],
               geo: Dict[str, Any], authority: Dict[str, Any], mode: str, site_domain: Optional[str]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    kw = (keywords.get("primary") or {}).get("keyword", "")
    text = article.get("text", "")
    title = article.get("title", "")
    h1 = article.get("h1", "")
    headings = article.get("headings", [])
    sub_headings = [h for h in headings if h["level"] in (2, 3)]
    first_words = " ".join(text.split()[:100])
    first_60 = " ".join(text.split()[:60])
    words = max(1, article.get("word_count") or 1)
    cjk = article.get("language_cjk", False)
    serp_ok = not serp.get("error") and bool(serp.get("organic_top10"))
    comp_ok = not competitors.get("error") and bool(competitors.get("items"))
    geo_ok = not geo.get("error") and bool(geo.get("engines"))

    # --- SEO: Metadata & structure ---
    dim = "Metadata & structure"
    checks.append(_check("seo.title.length", "seo", dim, 3, _band(len(title) if title else None, (30, 60), (20, 70)),
                         f"title is {len(title)} chars: “{truncate(title, 80)}”", "Rewrite the title to 30-60 characters with the primary keyword near the front."))
    meta = article.get("meta_description", "")
    checks.append(_check("seo.meta.length", "seo", dim, 3, _band(len(meta) if meta else None, (70, 155), (40, 200)),
                         f"meta description is {len(meta)} chars" if meta else "no meta description",
                         "Add a 70-155 character meta description that states the answer and includes the primary keyword."))
    h1_count = article.get("h1_count", 0)
    h1_status = "pass" if h1_count == 1 else ("warn" if h1_count == 0 and title else "fail")
    checks.append(_check("seo.h1.single", "seo", dim, 3, h1_status, f"{h1_count} H1 heading(s)", "Use exactly one H1 that carries the primary keyword."))
    skips = 0
    previous = 1
    for heading in headings:
        if heading["level"] > previous + 1:
            skips += 1
        previous = heading["level"]
    checks.append(_check("seo.heading.hierarchy", "seo", dim, 2, "pass" if skips == 0 else "warn",
                         f"{skips} heading level skip(s) across {len(headings)} headings", "Do not skip heading levels (H2 -> H4); keep a clean outline."))
    max_para = max(article.get("paragraph_word_counts") or [0])
    checks.append(_check("seo.paragraph.length", "seo", dim, 2, "pass" if max_para <= 150 else ("warn" if max_para <= 220 else "fail"),
                         f"longest paragraph is {max_para} words", "Split paragraphs longer than 150 words; answer engines lift short passages."))

    # --- SEO: Keyword targeting ---
    dim = "Keyword targeting"
    if not kw:
        checks.append(_check("seo.kw.missing", "seo", dim, 25, "fail", "no primary keyword could be determined", "Pick a primary keyword and use it consistently."))
    else:
        cov_title = phrase_token_coverage(title, kw)
        checks.append(_check("seo.kw.title", "seo", dim, 4, "pass" if contains_phrase(title, kw) else ("warn" if cov_title >= 0.5 else "fail"),
                             f"title coverage of “{kw}”: {int(cov_title * 100)}%", f"Put the exact phrase “{kw}” in the title."))
        cov_h1 = phrase_token_coverage(h1, kw) if h1 else 0.0
        checks.append(_check("seo.kw.h1", "seo", dim, 4, "pass" if h1 and contains_phrase(h1, kw) else ("warn" if cov_h1 >= 0.5 else "fail"),
                             f"H1 coverage: {int(cov_h1 * 100)}%" if h1 else "no H1", f"Use “{kw}” in the H1."))
        cov_intro = phrase_token_coverage(first_words, kw)
        checks.append(_check("seo.kw.intro100", "seo", dim, 4, "pass" if contains_phrase(first_words, kw) else ("warn" if cov_intro >= 0.5 else "fail"),
                             f"first 100 words coverage: {int(cov_intro * 100)}%", f"Mention “{kw}” verbatim in the first 100 words."))
        h2_hits = [h for h in sub_headings if contains_phrase(h["text"], kw) or phrase_token_coverage(h["text"], kw) >= 0.99]
        h2_partial = any(phrase_token_coverage(h["text"], kw) >= 0.5 for h in sub_headings)
        checks.append(_check("seo.kw.h2", "seo", dim, 3, "pass" if h2_hits else ("warn" if h2_partial else "fail"),
                             f"{len(h2_hits)} of {len(sub_headings)} H2/H3 contain the keyword",
                             f"Add at least one H2 that contains “{kw}” or a close variant."))
        slug = article.get("slug", "")
        slug_cov = phrase_token_coverage(slug.replace("-", " "), kw) if slug else None
        checks.append(_check("seo.kw.slug", "seo", dim, 3, "na" if slug_cov is None else _ratio_status(slug_cov, 0.99, 0.5),
                             f"slug “{slug}” coverage {int((slug_cov or 0) * 100)}%" if slug else "no slug available", f"Use a short slug built from “{kw}”."))
        occurrences = len(re.findall(re.escape(kw.lower()), text.lower()))
        density = occurrences * len(kw.split()) / words * 100
        checks.append(_check("seo.kw.density", "seo", dim, 3, _band(density, (0.5, 2.5), (0.2, 4.0)),
                             f"“{kw}” appears {occurrences}× (density {density:.2f}%)", "Aim for 0.5-2.5% density: use the phrase naturally a few more times, or trim if stuffed."))
        secondary = [s["keyword"] for s in keywords.get("secondary") or [] if s.get("keyword")]
        if secondary:
            present = [s for s in secondary if phrase_token_coverage(text, s) >= 0.99]
            ratio = len(present) / len(secondary)
            checks.append(_check("seo.kw.secondary_coverage", "seo", dim, 3, _ratio_status(ratio, 0.6, 0.3),
                                 f"{len(present)}/{len(secondary)} secondary keywords present; missing: {', '.join(s for s in secondary if s not in present) or 'none'}",
                                 "Work the missing secondary keywords into headings or body copy."))
        else:
            checks.append(_check("seo.kw.secondary_coverage", "seo", dim, 3, "na", "no secondary keywords", ""))

    # --- SEO: Content depth vs SERP ---
    dim = "Content depth vs SERP"
    median = competitors.get("median_word_count") if comp_ok else None
    if median:
        ratio = article["word_count"] / median
        checks.append(_check("seo.depth.wordcount", "seo", dim, 6, _ratio_status(ratio, 0.8, 0.6),
                             f"{article['word_count']} words vs competitor median {median} ({ratio:.2f}×)", "Expand the thinnest sections until the article is within 80% of the top-ranking median length."))
        shared = competitors.get("shared_heading_terms") or []
        missing = competitors.get("missing_heading_terms") or []
        miss_ratio = len(missing) / len(shared) if shared else 0.0
        checks.append(_check("seo.depth.topic_coverage", "seo", dim, 6, "na" if not shared else ("pass" if miss_ratio <= 0.3 else ("warn" if miss_ratio <= 0.6 else "fail")),
                             f"{len(missing)}/{len(shared)} recurring competitor heading terms missing: {', '.join(missing[:10]) or 'none'}",
                             "Add sections covering the recurring competitor topics you skip."))
    else:
        checks.append(_check("seo.depth.wordcount", "seo", dim, 6, "na", "competitor data unavailable", ""))
        checks.append(_check("seo.depth.topic_coverage", "seo", dim, 6, "na", "competitor data unavailable", ""))
    paa = serp.get("paa") or [] if serp_ok else []
    if paa:
        covered = [q for q in paa if phrase_token_coverage(text, q) >= 0.6]
        ratio = len(covered) / len(paa)
        checks.append(_check("seo.depth.paa_coverage", "seo", dim, 5, _ratio_status(ratio, 0.5, 0.25),
                             f"{len(covered)}/{len(paa)} People-Also-Ask questions answered; unanswered: {'; '.join(q for q in paa if q not in covered)[:300] or 'none'}",
                             "Answer the unanswered People-Also-Ask questions in dedicated H2/H3 sections or an FAQ."))
    else:
        checks.append(_check("seo.depth.paa_coverage", "seo", dim, 5, "na", "no People-Also-Ask data", ""))
    snippet = serp.get("featured_snippet") if serp_ok else None
    if snippet:
        has_format = article.get("lists", 0) > 0 or bool(re.search(rf"{re.escape(kw)}\s+(?:{'|'.join(DEFINITION_VERBS)})", text, re.I)) if kw else False
        checks.append(_check("seo.depth.featured_snippet_format", "seo", dim, 3, "pass" if has_format else "warn",
                             f"SERP has a featured snippet from {snippet.get('domain')}; article {'has' if has_format else 'lacks'} a list or definition passage",
                             "Add a 40-60 word definition paragraph or a step list that can replace the current featured snippet."))
    else:
        checks.append(_check("seo.depth.featured_snippet_format", "seo", dim, 3, "na", "no featured snippet on the SERP" if serp_ok else "SERP data unavailable", ""))

    # --- SEO: Links & media ---
    dim = "Links & media"
    external_domains = {domain_of(l["url"]) for l in article["links"]["external"]}
    checks.append(_check("seo.links.external", "seo", dim, 4, "pass" if len(external_domains) >= 2 else ("warn" if external_domains else "fail"),
                         f"{len(article['links']['external'])} external links to {len(external_domains)} domain(s)", "Link to at least two authoritative external sources for the claims you make."))
    internal_count = len(article["links"]["internal"])
    checks.append(_check("seo.links.internal", "seo", dim, 3, "pass" if internal_count >= 1 else "warn",
                         f"{internal_count} internal link(s)" + ("" if mode == "url" or site_domain else " (pass --site-domain to classify absolute links)"),
                         "Add internal links to related pages on your site."))
    images = article.get("images") or []
    if images:
        with_alt = sum(1 for i in images if i.get("alt"))
        ratio = with_alt / len(images)
        checks.append(_check("seo.images.alt", "seo", dim, 4, _ratio_status(ratio, 0.9, 0.5), f"{with_alt}/{len(images)} images have alt text", "Write descriptive alt text for every image."))
    else:
        checks.append(_check("seo.images.alt", "seo", dim, 4, "na", "no images", ""))
    checks.append(_check("seo.images.present", "seo", dim, 2, "pass" if images or article.get("has_video") else "warn",
                         f"{len(images)} image(s), video: {'yes' if article.get('has_video') else 'no'}", "Add at least one relevant image or video; AI features can surface multimodal content."))

    # --- SEO: Readability & E-E-A-T ---
    dim = "Readability & E-E-A-T"
    flesch = None if cjk else flesch_reading_ease(text)
    checks.append(_check("seo.read.flesch", "seo", dim, 4, "na" if cjk else _ratio_status(flesch, 50, 30),
                         f"Flesch reading ease {flesch}" if flesch is not None else ("not applicable for CJK text" if cjk else "too short to score"),
                         "Shorten sentences and prefer plain words to lift Flesch reading ease above 50."))
    checks.append(_check("seo.eeat.author", "seo", dim, 3, "pass" if article.get("author") else ("warn" if mode == "file" else "fail"),
                         f"author: {article.get('author') or 'none'}", "Add a named author with credentials (byline + short bio)."))
    checks.append(_check("seo.eeat.date", "seo", dim, 3, "pass" if article.get("date") else ("warn" if mode == "file" else "fail"),
                         f"date: {article.get('date') or 'none'}", "Show a published / updated date."))
    intro_cov = phrase_token_coverage(article.get("first_paragraph", ""), kw) if kw else None
    checks.append(_check("seo.eeat.intro_answers_query", "seo", dim, 3, "na" if intro_cov is None else _ratio_status(intro_cov, 0.99, 0.5),
                         f"first paragraph keyword coverage {int((intro_cov or 0) * 100)}%", "Open with a paragraph that directly addresses the search query."))

    # --- GEO: Answer-first ---
    dim = "Answer-first"
    cov60 = phrase_token_coverage(first_60, kw) if kw else None
    checks.append(_check("geo.answer.first60", "geo", dim, 10, "na" if cov60 is None else _ratio_status(cov60, 0.99, 0.5),
                         f"first 60 words: “{truncate(first_60, 160)}”", "State the direct answer to the query in the first 60 words, before any context or story."))
    definition = bool(kw) and bool(re.search(rf"\b{re.escape(kw)}\b\s+(?:{'|'.join(DEFINITION_VERBS)})\b", text, re.I))
    checks.append(_check("geo.answer.definition_sentence", "geo", dim, 5, "pass" if definition else "fail",
                         "found a definition sentence" if definition else f"no sentence of the form “{kw} is …”", f"Add one crisp sentence: “{kw} is …” that an engine can quote verbatim."))
    checks.append(_check("geo.answer.tldr", "geo", dim, 5, "pass" if article.get("has_tldr") else "fail",
                         "TL;DR / key takeaways block present" if article.get("has_tldr") else "no TL;DR or key-takeaways block", "Add a 3-5 bullet “Key takeaways” block near the top."))

    # --- GEO: Question alignment ---
    dim = "Question alignment"
    question_headings = [h for h in sub_headings if is_question_heading(h["text"])]
    checks.append(_check("geo.q.h2_questions", "geo", dim, 7, "pass" if len(question_headings) >= 2 else ("warn" if question_headings else "fail"),
                         f"{len(question_headings)} question-form H2/H3", "Rewrite at least two section headings as the questions searchers ask."))
    engine_questions = list(paa)
    if geo_ok:
        for engine in geo.get("engines", []):
            if engine.get("question"):
                engine_questions.append(engine["question"])
    engine_questions = dedupe(engine_questions)
    if engine_questions:
        matched = [q for q in engine_questions if any(phrase_token_coverage(h["text"], q) >= 0.5 for h in sub_headings)]
        ratio = len(matched) / len(engine_questions)
        checks.append(_check("geo.q.paa_match", "geo", dim, 8, _ratio_status(ratio, 0.4, 0.15),
                             f"{len(matched)}/{len(engine_questions)} SERP / engine questions have a matching heading",
                             "Mirror the People-Also-Ask phrasing in your headings so passages align with the questions engines answer."))
    else:
        checks.append(_check("geo.q.paa_match", "geo", dim, 8, "na", "no question data", ""))
    checks.append(_check("geo.q.faq_block", "geo", dim, 5, "pass" if article.get("has_faq") else "fail",
                         "FAQ section present" if article.get("has_faq") else "no FAQ section", "Add an FAQ with 3-5 questions taken from People-Also-Ask, each answered in 2-3 sentences."))

    # --- GEO: Citability ---
    dim = "Citability"
    stats = article.get("stats") or []
    cited_stats = [s for s in stats if s.get("cited")]
    uncited = [s for s in stats if not s.get("cited")]
    checks.append(_check("geo.cite.stats_with_source", "geo", dim, 8, "pass" if len(cited_stats) >= 3 else ("warn" if cited_stats else "fail"),
                         f"{len(cited_stats)} statistic(s) with an in-sentence source out of {len(stats)}", "Include at least three specific figures, each with a linked source in the same sentence."))
    checks.append(_check("geo.cite.uncited_stats", "geo", dim, 4, "pass" if not uncited else ("warn" if len(uncited) <= 2 else "fail"),
                         f"{len(uncited)} uncited figure(s): " + "; ".join(truncate(s['sentence'], 90) for s in uncited[:3]) if uncited else "every figure is sourced",
                         "Attach a source link to every number, or remove figures you cannot back."))
    firsthand = bool(re.search(r"\b(we tested|our (?:data|benchmark|research|survey|experiment|analysis|team)|in our experience|we measured|we found|we ran|hands-on|case study)\b", text, re.I))
    checks.append(_check("geo.cite.firsthand", "geo", dim, 5, "pass" if firsthand or article.get("tables") else "fail",
                         "first-hand experience or original data signals found" if firsthand else "no first-hand testing, original data, or case study signals",
                         "Add original data, a benchmark, or a documented first-hand experience; engines prefer non-commodity sources."))
    structured = (article.get("tables") or 0) + (article.get("lists") or 0)
    checks.append(_check("geo.cite.tables_lists", "geo", dim, 3, "pass" if structured >= 3 else ("warn" if structured else "fail"),
                         f"{article.get('tables', 0)} table(s), {article.get('lists', 0)} list item(s)", "Present comparisons and steps as tables or lists."))

    # --- GEO: Structure & extractability ---
    dim = "Structure & extractability"
    section_counts = [s["word_count"] for s in article.get("sections", []) if s.get("word_count")]
    longest = max(section_counts) if section_counts else None
    checks.append(_check("geo.struct.section_length", "geo", dim, 5, "na" if longest is None else ("pass" if longest <= 300 else ("warn" if longest <= 450 else "fail")),
                         f"longest section {longest} words" if longest is not None else "section lengths unavailable", "Break sections longer than 300 words with sub-headings."))
    checks.append(_check("geo.struct.lists", "geo", dim, 3, "pass" if article.get("lists") else "fail", f"{article.get('lists', 0)} list item(s)", "Use bullet or numbered lists for steps and options."))
    schema_types = article.get("schema_types") or []
    schema_ok = any(t.lower() in ("article", "blogposting", "newsarticle", "faqpage", "howto", "techarticle") for t in schema_types)
    checks.append(_check("geo.struct.schema", "geo", dim, 4, "pass" if schema_ok else ("warn" if mode == "file" else "fail"),
                         f"schema types: {', '.join(schema_types) or 'none'}", "Publish with Article (and FAQPage if you add an FAQ) structured data; it is not required for AI features but supports rich results."))
    descriptive = [h for h in sub_headings if len(h["text"].split()) >= 3 and h["text"].strip().lower() not in GENERIC_HEADINGS]
    ratio = len(descriptive) / len(sub_headings) if sub_headings else None
    checks.append(_check("geo.struct.headings_descriptive", "geo", dim, 3, _ratio_status(ratio, 0.7, 0.4),
                         f"{len(descriptive)}/{len(sub_headings)} H2/H3 are descriptive (3+ words, not generic)", "Replace generic headings like “Overview” or “Conclusion” with descriptive ones."))

    # --- GEO: Authority & freshness ---
    dim = "Authority & freshness"
    checks.append(_check("geo.auth.author_bio", "geo", dim, 3, "pass" if article.get("author") else ("warn" if mode == "file" else "fail"),
                         f"author: {article.get('author') or 'none'}", "Add an author byline and bio; people-first, expert content is what Google's AI features favour."))
    fresh_status, fresh_evidence = "warn" if mode == "file" else "fail", "no date"
    if article.get("date"):
        parsed = _parse_date(article["date"])
        if parsed:
            age = (_dt.date.today() - parsed).days
            fresh_status = "pass" if age <= 365 else "warn"
            fresh_evidence = f"dated {parsed.isoformat()} ({age} days ago)"
        else:
            fresh_status, fresh_evidence = "warn", f"unparseable date “{article['date']}”"
    checks.append(_check("geo.auth.date_fresh", "geo", dim, 3, fresh_status, fresh_evidence, "Show a visible published/updated date within the last 12 months."))
    robots = (article.get("robots") or "").lower()
    blocked = any(token in robots for token in ("nosnippet", "max-snippet:0", "noindex"))
    checks.append(_check("geo.auth.snippet_controls", "geo", dim, 2, "na" if (mode == "file" and not robots) else ("fail" if blocked else "pass"),
                         f"robots directives: {robots or 'none'}", "Remove nosnippet / max-snippet:0 / noindex; pages must be indexable and snippet-eligible to appear in AI features."))
    backlinks = (authority or {}).get("backlinks") if authority else None
    if backlinks:
        strong = (backlinks.get("authority_score") or 0) >= 20 or (backlinks.get("referring_domains") or 0) >= 50
        checks.append(_check("geo.auth.domain_strength", "geo", dim, 2, "pass" if strong else "warn",
                             f"authority score {backlinks.get('authority_score')}, {backlinks.get('referring_domains')} referring domains", "Earn links and mentions from sites already cited by AI engines."))
    else:
        checks.append(_check("geo.auth.domain_strength", "geo", dim, 2, "na", "domain authority not measured" if mode == "file" else "backlinks data unavailable", ""))

    # --- GEO: Current AI visibility ---
    dim = "Current AI visibility"
    if geo_ok and (mode == "url" or site_domain):
        cited = geo.get("any_article_cited") or geo.get("any_domain_cited")
        engines_cited = [e["label"] for e in geo["engines"] if e.get("article_cited") or e.get("domain_cited")]
        checks.append(_check("geo.vis.cited_any_engine", "geo", dim, 8, "pass" if cited else "fail",
                             f"cited by: {', '.join(engines_cited) or 'no engine'}", "None of the queried engines cite you yet; target the sources they do cite (see GEO section) and earn mentions there."))
    else:
        checks.append(_check("geo.vis.cited_any_engine", "geo", dim, 8, "na", "unpublished draft; citation check needs a URL or --site-domain" if not geo.get("error") else "engine data unavailable", ""))
    if geo_ok:
        title_terms: Dict[str, int] = {}
        for engine in geo.get("engines", []):
            for cited in engine.get("cited", []):
                for tok in tokens(cited.get("title") or ""):
                    title_terms[tok] = title_terms.get(tok, 0) + 1
        for organic in serp.get("organic_top10", []) if serp_ok else []:
            for tok in tokens(organic.get("title") or ""):
                title_terms[tok] = title_terms.get(tok, 0) + 1
        top_terms = [t for t, _ in sorted(title_terms.items(), key=lambda kv: -kv[1])[:20]]
        article_terms = set(tokens(text))
        overlap = sum(1 for t in top_terms if t in article_terms) / len(top_terms) if top_terms else None
        checks.append(_check("geo.vis.topic_overlap", "geo", dim, 4, _ratio_status(overlap, 0.5, 0.3),
                             f"{int((overlap or 0) * 100)}% of the top terms in cited/ranking titles appear in the article" if overlap is not None else "no cited titles to compare",
                             "Cover the terms that cited pages emphasise so your passages match what engines retrieve."))
        ai_present = bool((serp.get("ai_overview") or {}).get("present")) or any(e["status"] == "ok" and e["engine"] != "dfs_llm_mentions" for e in geo["engines"])
        checks.append(_check("geo.vis.ai_overview_present", "geo", dim, 3, "pass" if ai_present else "warn",
                             f"AI Overview on SERP: {'yes' if (serp.get('ai_overview') or {}).get('present') else 'no'}; engines answering: {geo.get('engines_answered', 0)}/{len(geo['engines'])}",
                             "The query rarely triggers AI answers today; prioritise classic SEO for it."))
    else:
        checks.append(_check("geo.vis.topic_overlap", "geo", dim, 4, "na", "engine data unavailable", ""))
        checks.append(_check("geo.vis.ai_overview_present", "geo", dim, 3, "na", "engine data unavailable", ""))
    return checks


def _parse_date(value: str) -> Optional[_dt.date]:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y/%m/%d", "%d %B %Y", "%B %d, %Y", "%Y-%m"):
        try:
            return _dt.datetime.strptime(value[:len(_dt.datetime.now().strftime(fmt))] if fmt.endswith("%z") else value, fmt).date()
        except ValueError:
            continue
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if match:
        try:
            return _dt.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def compute_scores(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    def area_score(area: str, dimensions: Dict[str, int]) -> Dict[str, Any]:
        detail: Dict[str, Any] = {}
        applicable_max = 0.0
        earned = 0.0
        for dimension, max_points in dimensions.items():
            relevant = [c for c in checks if c["area"] == area and c["dimension"] == dimension and c["status"] != "na"]
            total_weight = sum(c["weight"] for c in relevant)
            if total_weight == 0:
                detail[dimension] = {"score": None, "max": max_points, "applicable": False}
                continue
            got = sum(c["weight"] for c in relevant if c["status"] == "pass") + 0.5 * sum(c["weight"] for c in relevant if c["status"] == "warn")
            ratio = got / total_weight
            detail[dimension] = {"score": round(ratio * max_points, 1), "max": max_points, "applicable": True, "ratio": round(ratio, 3)}
            applicable_max += max_points
            earned += ratio * max_points
        total = round(earned / applicable_max * 100) if applicable_max else None
        return {"dimensions": detail, "total": total, "redistributed": [d for d, v in detail.items() if not v["applicable"]]}

    seo = area_score("seo", SEO_DIMENSIONS)
    geo = area_score("geo", GEO_DIMENSIONS)
    parts = [s for s in (seo["total"], geo["total"]) if s is not None]
    overall = round(sum(parts) / len(parts)) if parts else None
    grade = "n/a"
    if overall is not None:
        grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D" if overall >= 40 else "F"
    return {"seo": seo, "geo": geo, "overall": overall, "grade": grade}


# ---------------------------------------------------------------------------
# LLM stages
# ---------------------------------------------------------------------------


def stage_llm_gap(article: Dict[str, Any], keywords: Dict[str, Any], serp: Dict[str, Any], competitors: Dict[str, Any],
                  geo: Dict[str, Any], checks: List[Dict[str, Any]], client: Aisa) -> Dict[str, Any]:
    outline = "\n".join(f"{'#' * h['level']} {h['text']}" for h in article["headings"][:40])
    comp_lines = []
    for comp in (competitors.get("items") or [])[:5]:
        heads = "; ".join((comp.get("headings") or [])[:25])
        comp_lines.append(f"- {comp.get('domain')} (#{comp.get('rank')}, {comp.get('word_count') or '?'} words): {heads}")
    engine_lines = []
    for engine in (geo.get("engines") or []):
        if engine["status"] not in ("ok", "no_answer") or engine["engine"] == "dfs_llm_mentions":
            continue
        domains = ", ".join(dedupe([c["domain"] for c in engine["cited"]])[:8])
        engine_lines.append(f"- {engine['label']}: cites [{domains}]. Answer excerpt: {truncate(engine['answer_excerpt'], 400)}")
    top_domains = [d for d in (geo.get("cited_domain_frequency") or {})][:10]
    failing = [c for c in checks if c["status"] in ("fail", "warn")]
    fail_lines = "\n".join(f"- {c['id']} [{c['status']}]: {c['evidence']}" for c in failing[:30])
    primary = keywords.get("primary") or {}
    metrics = f"volume {primary.get('search_volume')}, difficulty {primary.get('keyword_difficulty')}, intent {primary.get('intent')}"
    prompt = (
        f"Primary keyword: {primary.get('keyword')} ({metrics}).\n"
        f"Secondary keywords: {', '.join(s['keyword'] for s in keywords.get('secondary') or [])}\n\n"
        f"ARTICLE TITLE: {article.get('title')}\nARTICLE OUTLINE:\n{outline}\n\nFIRST PARAGRAPH: {truncate(article.get('first_paragraph', ''), 600)}\n"
        f"WORD COUNT: {article.get('word_count')} (competitor median: {competitors.get('median_word_count')})\n\n"
        f"TOP-RANKING COMPETITOR OUTLINES:\n{chr(10).join(comp_lines) or '- none available'}\n\n"
        f"PEOPLE ALSO ASK: {'; '.join(serp.get('paa') or []) or 'none'}\n"
        f"RELATED SEARCHES: {'; '.join(serp.get('related_searches') or []) or 'none'}\n\n"
        f"WHAT AI ANSWER ENGINES SAY AND CITE:\n{chr(10).join(engine_lines) or '- none available'}\n"
        f"MOST-CITED DOMAINS ACROSS ENGINES: {', '.join(top_domains) or 'none'}\n\n"
        f"FAILED / WARNING CHECKS:\n{fail_lines or '- none'}\n\n"
        "Task: identify the content gaps versus competitors and AI answers, then produce prioritised rewrite suggestions "
        "for both SEO and GEO (generative engine optimisation: being cited by AI answers). Ground every suggestion in the "
        "evidence above; cite the check ids it addresses. Each example_rewrite must be at most 80 words and reuse only facts "
        "present in the article or evidence (no invented statistics).\n"
        'Return JSON: {"missing_topics": [{"topic": "...", "seen_in": ["domain"], "why": "..."}], '
        '"suggestions": [{"priority": 1, "area": "seo|geo", "issue": "...", "suggestion": "...", "example_rewrite": "...", "source_check_ids": ["..."]}]} '
        "with at most 12 suggestions ordered by expected impact."
    )
    data = parse_json_loose(client.chat(KEYWORD_SYSTEM, prompt, "rewrite"))
    suggestions = []
    for index, item in enumerate((data.get("suggestions") or [])[:12], start=1):
        if not isinstance(item, dict):
            continue
        suggestions.append({
            "priority": int(item.get("priority") or index),
            "area": "geo" if str(item.get("area", "")).lower().startswith("geo") else "seo",
            "issue": str(item.get("issue", "")),
            "suggestion": str(item.get("suggestion", "")),
            "example_rewrite": str(item.get("example_rewrite", "")),
            "source_check_ids": [str(c) for c in (item.get("source_check_ids") or [])],
        })
    suggestions.sort(key=lambda s: s["priority"])
    missing = [m for m in (data.get("missing_topics") or []) if isinstance(m, dict)][:12]
    return {"missing_topics": missing, "suggestions": suggestions}


def stage_summary(scores: Dict[str, Any], suggestions: List[Dict[str, Any]], geo: Dict[str, Any], client: Aisa) -> str:
    top = "\n".join(f"{s['priority']}. [{s['area']}] {s['issue']} -> {s['suggestion']}" for s in suggestions[:5])
    cited = ", ".join(list((geo.get("cited_domain_frequency") or {}).keys())[:6]) or "none"
    prompt = (
        f"Scores: SEO {scores['seo']['total']}/100, GEO {scores['geo']['total']}/100, overall {scores['overall']} (grade {scores['grade']}).\n"
        f"Article cited by AI engines: {'yes' if geo.get('any_article_cited') or geo.get('any_domain_cited') else 'no / unknown'}; domains engines cite most: {cited}.\n"
        f"Top suggestions:\n{top}\n\nWrite an executive summary of at most 120 words for the author. "
        'Return JSON: {"summary": "..."}'
    )
    data = parse_json_loose(client.chat(KEYWORD_SYSTEM, prompt, "summary"))
    return str(data.get("summary", "")).strip()


def deterministic_suggestions(checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked = sorted((c for c in checks if c["status"] in ("fail", "warn") and c["fix"]), key=lambda c: (c["status"] != "fail", -c["weight"]))
    return [
        {"priority": i, "area": c["area"], "issue": c["evidence"], "suggestion": c["fix"], "example_rewrite": "", "source_check_ids": [c["id"]]}
        for i, c in enumerate(ranked[:12], start=1)
    ]


# ---------------------------------------------------------------------------
# Planning / governance
# ---------------------------------------------------------------------------


def plan_calls(args: argparse.Namespace, mode: str) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []

    def add(call_id: str, n: int = 1, note: str = "") -> None:
        label, endpoint, nominal, maximum = COSTS[call_id]
        plan.append({"call_id": call_id, "label": label, "endpoint": endpoint, "n": n, "nominal_usd": round(nominal * n, 4), "max_usd": round(maximum * n, 4), "note": note})

    if mode == "url":
        add("dfs_content_parsing", 1, "parse the published page")
    if not args.keyword and not args.no_llm:
        add("chat", 1, "keyword extraction")
    add("dfs_keyword_overview", 1)
    add("sem_keyword_overview", 1)
    if args.deep:
        add("dfs_related_keywords", 1)
        add("sem_question_keywords", 1)
    add("dfs_serp_organic", 1)
    add("dfs_content_parsing", args.top, f"top {args.top} competitors")
    add("sem_domain_overview", args.top, f"top {args.top} competitors")
    if mode == "url":
        add("sem_backlinks_overview", 1)
        if args.deep:
            add("sem_url_organic_keywords", 1)
            add("dfs_backlinks_summary", 1)
    for engine in args.engines:
        if engine == "dfs_ai_mode":
            add("dfs_ai_mode", 1)
        elif engine == "dfs_llm_mentions":
            add("dfs_llm_mentions", 2, "google + chat_gpt platforms")
        elif engine in LLM_RESPONSE_MODELS:
            add(engine, 1, ENGINE_LABELS.get(engine, engine))
        else:
            add("oxy_ai_search", 1, ENGINE_LABELS.get(engine, engine))
    if not args.no_llm:
        add("chat", 1, "content gap + rewrite suggestions")
        if not args.fast:
            add("chat", 1, "executive summary")
    return plan


def render_plan(plan: List[Dict[str, Any]]) -> str:
    lines = ["Planned AIsa calls (nominal price per call; max is the documented worst case):", ""]
    lines.append(f"{'call':<30}{'n':>3}  {'nominal':>8}  {'max':>8}  {'endpoint':<62} note")
    for entry in plan:
        lines.append(f"{entry['label']:<30}{entry['n']:>3}  ${entry['nominal_usd']:>7.4f}  ${entry['max_usd']:>7.4f}  {entry['endpoint']:<62} {entry['note']}")
    nominal = sum(e["nominal_usd"] for e in plan)
    maximum = sum(e["max_usd"] for e in plan)
    lines.append("")
    lines.append(f"Estimated spend: ${nominal:.4f} nominal, ${maximum:.4f} documented maximum.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

STATUS_ICON = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "na": "n/a"}


def _fmt(value: Any) -> str:
    if value is None or value == "":
        return "–"
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def report_markdown(review: Dict[str, Any]) -> str:
    meta = review["meta"]
    article = review["article"]
    scores = review["scores"]
    keywords = review.get("keywords") or {}
    serp = review.get("serp") or {}
    competitors = review.get("competitors") or {}
    geo = review.get("geo") or {}
    checks = review.get("checks") or []
    lines: List[str] = []
    lines.append(f"# SEO + GEO Review: {article.get('title') or meta['source']}")
    lines.append("")
    lines.append(f"- Source: `{meta['source']}` ({meta['mode']} mode)")
    lines.append(f"- Primary keyword: **{meta.get('keyword') or '–'}**")
    lines.append(f"- Market: location {meta['location_code']}, language {meta['language_code']}, SEMrush db {meta['database']}")
    lines.append(f"- Generated: {meta['generated_at']} by AIsa article-seo-geo-review v{VERSION}")
    lines.append(f"- **Grade: {scores['grade']}** (overall {_fmt(scores['overall'])}/100)")
    lines.append("")

    lines.append("## Scorecard")
    lines.append("")
    lines.append("| Area | Dimension | Score | Max |")
    lines.append("|---|---|---:|---:|")
    for area, label in (("seo", "SEO"), ("geo", "GEO")):
        block = scores[area]
        lines.append(f"| **{label}** | **Total** | **{_fmt(block['total'])}** | **100** |")
        for dimension, detail in block["dimensions"].items():
            score = "n/a" if not detail["applicable"] else _fmt(detail["score"])
            lines.append(f"| {label} | {dimension} | {score} | {detail['max']} |")
    redistributed = scores["geo"].get("redistributed") or []
    if redistributed:
        lines.append("")
        lines.append(f"_Not applicable and redistributed: {', '.join(redistributed)}._")
    lines.append("")

    if review.get("summary"):
        lines.append("## Executive summary")
        lines.append("")
        lines.append(review["summary"])
        lines.append("")

    lines.append("## Keywords")
    lines.append("")
    if keywords.get("error"):
        lines.append(f"Keyword stage failed: {keywords['error']}")
    else:
        lines.append("| Keyword | Role | Volume | KD | Intent | CPC | SEMrush volume |")
        lines.append("|---|---|---:|---:|---|---:|---:|")
        primary = keywords.get("primary") or {}
        rows = [(primary, "primary")] + [(s, "secondary") for s in keywords.get("secondary") or []]
        for item, role in rows:
            lines.append(f"| {md_escape(item.get('keyword'))} | {role} | {_fmt(item.get('search_volume'))} | {_fmt(item.get('keyword_difficulty'))} | {_fmt(item.get('intent'))} | {_fmt(item.get('cpc'))} | {_fmt(item.get('semrush_search_volume'))} |")
        lines.append("")
        lines.append(f"Keyword source: {keywords.get('source')}; metrics: {', '.join(keywords.get('metrics_source') or []) or 'none'}. {primary.get('rationale') or ''}".strip())
        for key in ("dataforseo_error", "semrush_error", "warning"):
            if keywords.get(key):
                lines.append(f"- Note: {keywords[key]}")
        if keywords.get("related"):
            lines.append("")
            lines.append("Related keywords (deep): " + ", ".join(f"{r['keyword']} ({_fmt(r.get('search_volume'))})" for r in keywords["related"][:12]))
        if keywords.get("questions"):
            lines.append("")
            lines.append("Question keywords (deep): " + "; ".join(q["keyword"] for q in keywords["questions"][:10] if q.get("keyword")))
    lines.append("")

    lines.append("## SERP snapshot")
    lines.append("")
    if serp.get("error"):
        lines.append(f"SERP stage failed: {serp['error']}")
    else:
        lines.append("| # | Domain | Title |")
        lines.append("|---:|---|---|")
        for organic in serp.get("organic_top10") or []:
            lines.append(f"| {organic.get('rank')} | {md_escape(organic.get('domain'))} | [{md_escape(truncate(organic.get('title') or '', 90))}]({organic.get('url')}) |")
        lines.append("")
        overview = serp.get("ai_overview") or {}
        lines.append(f"- AI Overview on SERP: {'yes' if overview.get('present') else 'no'}" + (f" (cites {', '.join(dedupe([r['domain'] for r in overview.get('references') or []])[:8])})" if overview.get("references") else ""))
        snippet = serp.get("featured_snippet")
        lines.append(f"- Featured snippet: {snippet.get('domain') if snippet else 'none'}")
        lines.append(f"- SERP item types: {', '.join(serp.get('item_types') or []) or '–'}")
        if serp.get("paa"):
            lines.append("- People also ask:")
            for question in serp["paa"]:
                lines.append(f"  - {question}")
        if serp.get("related_searches"):
            lines.append(f"- Related searches: {', '.join(serp['related_searches'])}")
    lines.append("")

    lines.append("## Competitor comparison")
    lines.append("")
    if competitors.get("error"):
        lines.append(f"Competitor stage failed: {competitors['error']}")
    elif not competitors.get("items"):
        lines.append("No competitor pages analysed.")
    else:
        lines.append(f"Article length: {_fmt(article.get('word_count'))} words vs competitor median {_fmt(competitors.get('median_word_count'))}.")
        lines.append("")
        lines.append("| # | Domain | Words | Headings | Domain rank | Organic traffic |")
        lines.append("|---:|---|---:|---:|---:|---:|")
        for comp in competitors["items"]:
            lines.append(f"| {comp.get('rank')} | {md_escape(comp.get('domain'))} | {_fmt(comp.get('word_count'))} | {len(comp.get('headings') or [])} | {_fmt(comp.get('domain_rank'))} | {_fmt(comp.get('organic_traffic'))} |")
        lines.append("")
        if competitors.get("missing_heading_terms"):
            lines.append(f"Recurring competitor heading terms missing from the article: {', '.join(competitors['missing_heading_terms'])}")
        errors = [f"{c.get('domain')}: {c.get('parse_error') or c.get('semrush_error')}" for c in competitors["items"] if c.get("parse_error") or c.get("semrush_error")]
        if errors:
            lines.append("")
            lines.append("Partial data: " + "; ".join(errors))
    lines.append("")

    for area, heading in (("seo", "SEO on-page audit"), ("geo", "GEO audit")):
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("| Check | Status | Evidence | Fix |")
        lines.append("|---|---|---|---|")
        for check in checks:
            if check["area"] != area:
                continue
            lines.append(f"| `{check['id']}` | {STATUS_ICON[check['status']]} | {md_escape(check['evidence'])} | {md_escape(check['fix'])} |")
        lines.append("")

    lines.append("## AI answer engine visibility")
    lines.append("")
    if geo.get("error"):
        lines.append(f"GEO stage failed: {geo['error']}")
        lines.append("")
    elif not geo.get("engines"):
        lines.append("No AI engines were queried.")
        lines.append("")
    else:
        lines.append(f"Question asked: “{geo.get('question')}”")
        lines.append("")
        lines.append("| Engine | Status | Cites you | Top cited domains | Overlap with organic top 10 |")
        lines.append("|---|---|---|---|---|")
        for engine in geo["engines"]:
            if engine["engine"] == "dfs_llm_mentions":
                domains = ", ".join(f"{d['domain']} ({d['platform']})" for d in (engine.get("top_domains") or [])[:8]) or "–"
                cites = "–"
            else:
                domains = ", ".join(dedupe([c["domain"] for c in engine["cited"]])[:6]) or "–"
                cites = "yes" if engine["article_cited"] or engine["domain_cited"] else "no"
            lines.append(f"| {engine['label']} | {engine['status']}{(' – ' + md_escape(truncate(engine['error'], 80))) if engine.get('error') else ''} | {cites} | {md_escape(domains)} | {md_escape(', '.join(engine['overlap_with_top10']) or '–')} |")
        lines.append("")
        if geo.get("cited_domain_frequency"):
            lines.append("Most-cited domains across engines: " + ", ".join(f"{d} ×{n}" for d, n in geo["cited_domain_frequency"].items()))
            lines.append("")
        for engine in geo["engines"]:
            if engine.get("answer_excerpt"):
                lines.append(f"**{engine['label']} says:** {engine['answer_excerpt']}")
                lines.append("")

    lines.append("## Prioritised rewrite suggestions")
    lines.append("")
    suggestions = review.get("suggestions") or []
    if not suggestions:
        lines.append("No suggestions generated.")
    for item in suggestions:
        lines.append(f"{item['priority']}. **[{item['area'].upper()}] {item['issue']}**")
        lines.append(f"   - {item['suggestion']}")
        if item.get("example_rewrite"):
            lines.append(f"   - Example: _{item['example_rewrite']}_")
        if item.get("source_check_ids"):
            lines.append(f"   - Checks: {', '.join('`' + c + '`' for c in item['source_check_ids'])}")
    if review.get("missing_topics"):
        lines.append("")
        lines.append("Missing topics versus competitors and AI answers:")
        for topic in review["missing_topics"]:
            lines.append(f"- **{topic.get('topic')}** (seen in {', '.join(topic.get('seen_in') or []) or 'AI answers'}): {topic.get('why', '')}")
    lines.append("")

    spend = review.get("spend") or {}
    lines.append("## Spend")
    lines.append("")
    lines.append(f"- Estimated total: ${_fmt(spend.get('estimated_total_usd'))} (nominal ${_fmt(spend.get('nominal_total_usd'))}; DataForSEO reported ${_fmt(spend.get('actual_dataforseo_usd'))})")
    lines.append(f"- Calls: DataForSEO {spend.get('dataforseo_calls', 0)}, SEMrush {spend.get('semrush_calls', 0)}, Oxylabs {spend.get('oxylabs_calls', 0)}, LLM {spend.get('chat_calls', 0)} ({spend.get('chat_tokens', 0)} tokens), cache hits {spend.get('cache_hits', 0)}")
    lines.append("")
    if spend.get("entries"):
        lines.append("| Stage | Call | Nominal | Actual | Status |")
        lines.append("|---|---|---:|---:|---|")
        for entry in spend["entries"]:
            lines.append(f"| {entry['stage']} | {entry['label']} | ${entry['nominal_usd']:.4f} | {('$' + format(entry['actual_usd'], '.4f')) if entry['actual_usd'] is not None else ('cached' if entry['cached'] else '–')} | {entry['status']}{(' – ' + md_escape(truncate(entry['error'], 80))) if entry.get('error') else ''} |")
        lines.append("")

    lines.append("## Data gaps & assumptions")
    lines.append("")
    gaps = review.get("data_gaps") or []
    if not gaps:
        lines.append("- None recorded.")
    for gap in gaps:
        lines.append(f"- {gap}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_stage(name: str, fn: Callable[[], Dict[str, Any]], gaps: List[str]) -> Dict[str, Any]:
    log(f"[{name}] running…")
    started = time.time()
    try:
        result = fn()
        log(f"[{name}] done in {time.time() - started:.1f}s")
        return result
    except Exception as exc:
        gaps.append(f"{name} stage failed: {exc}")
        log(f"[{name}] failed: {exc}")
        return {"error": str(exc)}


def base_meta(args: argparse.Namespace, source: str, mode: str) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "generated_at": now_iso(),
        "source": source,
        "mode": mode,
        "keyword": None,
        "location_code": args.location_code,
        "language_code": args.language_code,
        "database": args.database,
        "model": None if getattr(args, "no_llm", False) else args.model,
        "engines": list(getattr(args, "engines", []) or []),
        "flags": {"fast": bool(getattr(args, "fast", False)), "deep": bool(getattr(args, "deep", False)), "no_llm": bool(getattr(args, "no_llm", False))},
    }


def build_review(args: argparse.Namespace, client: Aisa, ledger: Ledger, stages: Tuple[str, ...]) -> Dict[str, Any]:
    gaps: List[str] = []
    source = args.source
    mode = "url" if source.startswith("http") else "file"
    article = load_article(source, client if "parse" in stages else None, args.site_domain)
    for warning in article.get("warnings") or []:
        gaps.append(warning)
    review: Dict[str, Any] = {"meta": base_meta(args, source, mode), "article": article_public(article)}
    keywords: Dict[str, Any] = {}
    serp: Dict[str, Any] = {}
    competitors: Dict[str, Any] = {}
    authority: Dict[str, Any] = {}
    geo: Dict[str, Any] = {}

    if "keywords" in stages:
        keywords = run_stage("keywords", lambda: stage_keywords(article, args, client), gaps)
    if not keywords.get("primary", {}).get("keyword"):
        keywords = dict(keywords)
        keywords["primary"] = {"keyword": args.keyword or heuristic_keyword(article), "rationale": "fallback"}
        keywords.setdefault("secondary", [])
    keyword = keywords["primary"]["keyword"]
    review["meta"]["keyword"] = keyword
    review["keywords"] = keywords

    if "serp" in stages:
        serp = run_stage("serp", lambda: stage_serp(keyword, args, client), gaps)
    if "competitors" in stages and not serp.get("error"):
        competitors = run_stage("competitors", lambda: stage_competitors(serp, article, args, client), gaps)
    elif "competitors" in stages:
        competitors = {"error": "skipped because the SERP stage failed"}
    if "authority" in stages and mode == "url":
        authority = run_stage("authority", lambda: stage_authority(article, args, client), gaps)
    if "geo" in stages:
        geo = run_stage("geo", lambda: stage_geo(keyword, article, serp, args, client), gaps)
        for engine in geo.get("engines") or []:
            if engine["status"] in ("error", "timeout"):
                gaps.append(f"{engine['label']}: {engine['status']}{(' – ' + engine['error']) if engine.get('error') else ''}")
    review.update({"serp": serp, "competitors": competitors, "authority": authority, "geo": geo})

    checks = run_checks(article, keywords, serp, competitors, geo, authority, mode, args.site_domain)
    review["checks"] = checks
    review["scores"] = compute_scores(checks)

    suggestions: List[Dict[str, Any]] = []
    missing_topics: List[Dict[str, Any]] = []
    summary = None
    if "rewrite" in stages and not args.no_llm:
        gap = run_stage("rewrite", lambda: stage_llm_gap(article, keywords, serp, competitors, geo, checks, client), gaps)
        suggestions = gap.get("suggestions") or []
        missing_topics = gap.get("missing_topics") or []
    if not suggestions:
        suggestions = deterministic_suggestions(checks)
        if "rewrite" in stages and not args.no_llm:
            gaps.append("LLM suggestions unavailable; showing deterministic fixes instead")
    review["suggestions"] = suggestions
    review["missing_topics"] = missing_topics
    if "summary" in stages and not args.no_llm and not args.fast:
        result = run_stage("summary", lambda: {"summary": stage_summary(review["scores"], suggestions, geo, client)}, gaps)
        summary = result.get("summary")
    review["summary"] = summary
    if mode == "file" and not args.site_domain:
        gaps.append("Draft mode: AI citation and domain-authority checks are not applicable until the article is published (or pass --site-domain).")
    review["spend"] = ledger.summary()
    review["data_gaps"] = gaps
    return review


def make_client(args: argparse.Namespace) -> Tuple[Aisa, Ledger]:
    ledger = Ledger()
    cache = Cache(getattr(args, "cache_dir", None))
    return Aisa(ledger, cache, model=getattr(args, "model", DEFAULT_MODEL)), ledger


def emit(args: argparse.Namespace, data: Dict[str, Any], markdown: Optional[str] = None) -> None:
    json_out = getattr(args, "json_out", None)
    out = getattr(args, "out", None)
    if markdown is not None:
        write_text(out, markdown)
        if json_out:
            write_json(json_out, data)
    else:
        write_json(json_out or out, data)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def command_parse(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    mode = "url" if args.source.startswith("http") else "file"
    article = load_article(args.source, client if mode == "url" else None, args.site_domain)
    emit(args, {"meta": base_meta(args, args.source, mode), "article": article_public(article), "spend": ledger.summary()})


def command_audit(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    mode = "url" if args.source.startswith("http") else "file"
    article = load_article(args.source, client if mode == "url" else None, args.site_domain)
    keyword = args.keyword or heuristic_keyword(article)
    keywords = {"primary": {"keyword": keyword, "rationale": "user" if args.keyword else "heuristic"}, "secondary": [], "source": "user" if args.keyword else "heuristic"}
    checks = run_checks(article, keywords, {}, {}, {}, {}, mode, args.site_domain)
    review = {
        "meta": base_meta(args, args.source, mode),
        "article": article_public(article),
        "keywords": keywords,
        "serp": {},
        "competitors": {},
        "authority": {},
        "geo": {},
        "checks": checks,
        "scores": compute_scores(checks),
        "suggestions": deterministic_suggestions(checks),
        "missing_topics": [],
        "summary": None,
        "spend": ledger.summary(),
        "data_gaps": ["audit mode: no SERP, competitor, or AI engine data; depth and visibility dimensions are not applicable"] + list(article.get("warnings") or []),
    }
    review["meta"]["keyword"] = keyword
    emit(args, review, report_markdown(review))


def _gate(args: argparse.Namespace, mode: str, plan: List[Dict[str, Any]]) -> None:
    maximum = sum(e["max_usd"] for e in plan)
    if args.dry_run:
        print(render_plan(plan))
        raise SystemExit(0)
    if maximum > args.max_usd:
        log(render_plan(plan))
        raise SystemExit(f"Documented maximum exposure ${maximum:.4f} exceeds --max-usd {args.max_usd:.2f}. Reduce scope (--fast, --top, --engines) or raise --max-usd.")
    if not args.yes:
        log(render_plan(plan))
        log("")
        log("Paid AIsa calls require explicit approval. Show this estimate to the user, then re-run with --yes.")
        raise SystemExit(2)


def command_review(args: argparse.Namespace) -> None:
    mode = "url" if args.source.startswith("http") else "file"
    plan = plan_calls(args, mode)
    _gate(args, mode, plan)
    client, ledger = make_client(args)
    review = build_review(args, client, ledger, ("parse", "keywords", "serp", "competitors", "authority", "geo", "rewrite", "summary"))
    review["plan"] = plan
    emit(args, review, report_markdown(review))


def command_keywords(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    mode = "url" if args.source.startswith("http") else "file"
    article = load_article(args.source, client if mode == "url" else None, args.site_domain)
    log(render_plan([e for e in plan_calls(args, mode) if e["call_id"] in ("dfs_keyword_overview", "sem_keyword_overview", "dfs_related_keywords", "sem_question_keywords") or (e["call_id"] == "chat" and e["note"] == "keyword extraction")]))
    keywords = stage_keywords(article, args, client)
    emit(args, {"meta": base_meta(args, args.source, mode), "keywords": keywords, "spend": ledger.summary()})


def command_serp(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    serp = stage_serp(args.keyword, args, client)
    engines = [e for e in args.engines if e == "dfs_ai_mode"]
    if engines:
        dummy = {"title": "", "domain": "", "url": ""}
        ai_mode = run_engine("dfs_ai_mode", args.keyword, args.keyword, dummy, [o.get("domain", "") for o in serp["organic_top10"]], args, client)
        serp["ai_mode"] = ai_mode
    emit(args, {"meta": base_meta(args, args.keyword, "keyword"), "serp": serp, "spend": ledger.summary()})


def command_competitors(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    serp = stage_serp(args.keyword, args, client)
    article = {"domain": args.site_domain or "", "text": "", "headings": []}
    competitors = stage_competitors(serp, article, args, client)
    emit(args, {"meta": base_meta(args, args.keyword, "keyword"), "serp": serp, "competitors": competitors, "spend": ledger.summary()})


def command_geo(args: argparse.Namespace) -> None:
    client, ledger = make_client(args)
    article = {"title": "", "domain": args.site_domain or (domain_of(args.url) if args.url else ""), "url": args.url or ""}
    serp: Dict[str, Any] = {"organic_top10": []}
    geo = stage_geo(args.keyword, article, serp, args, client)
    emit(args, {"meta": base_meta(args, args.keyword, "keyword"), "geo": geo, "spend": ledger.summary()})


def command_render(args: argparse.Namespace) -> None:
    review = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    if "checks" in review and args.rescore:
        review["scores"] = compute_scores(review["checks"])
    write_text(args.out, report_markdown(review))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _engines_arg(value: str) -> List[str]:
    engines = [v.strip() for v in value.split(",") if v.strip()]
    unknown = [e for e in engines if e not in ENGINE_LABELS]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown engine(s): {', '.join(unknown)}. Choose from {', '.join(ENGINE_LABELS)}")
    return engines


def add_common(parser: argparse.ArgumentParser, *, source: bool = False, keyword_required: bool = False, network: bool = True) -> None:
    if source:
        parser.add_argument("source", help="Markdown file path or http(s) URL of the article")
    if keyword_required:
        parser.add_argument("--keyword", required=True, help="Primary keyword")
    else:
        parser.add_argument("--keyword", help="Primary keyword (skips LLM extraction)")
    parser.add_argument("--site-domain", help="Your site's domain (classifies internal links and citation hits for drafts)")
    parser.add_argument("--location-code", type=int, default=2840, help="DataForSEO location code (default 2840 = United States)")
    parser.add_argument("--language-code", default="en", help="DataForSEO language code (default en)")
    parser.add_argument("--database", default="us", help="SEMrush regional database (default us)")
    parser.add_argument("--geo-location", default="United States", help="Oxylabs geo_location (default United States)")
    parser.add_argument("--top", type=int, default=5, help="Competitor pages to analyse (default 5)")
    parser.add_argument("--engines", type=_engines_arg, default=list(DEFAULT_ENGINES), help="Comma-separated AI engines: " + ", ".join(ENGINE_LABELS))
    parser.add_argument("--fast", action="store_true", help="Skip the LLM-response engines (ChatGPT, Perplexity, Gemini, Claude) and the executive summary")
    parser.add_argument("--deep", action="store_true", help="Add related keywords, question keywords, and URL-level authority data")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"AIsa LLM model (default {DEFAULT_MODEL}; env AISA_REVIEW_MODEL)")
    parser.add_argument("--no-llm", action="store_true", help="Skip every LLM call (heuristic keyword, deterministic suggestions)")
    parser.add_argument("--cache-dir", help="Directory to store raw API responses (re-runs are free)")
    parser.add_argument("--out", help="Output file (Markdown for review/audit, JSON otherwise); stdout when omitted")
    parser.add_argument("--json-out", help="Also write the full JSON evidence to this file")
    if network:
        parser.add_argument("--dry-run", action="store_true", help="Print the planned paid calls and exit")
        parser.add_argument("--yes", action="store_true", help="Confirm that the user approved the planned spend")
        parser.add_argument("--max-usd", type=float, default=1.00, help="Refuse to run when the documented maximum exposure exceeds this (default 1.00)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review an article for SEO and GEO using AIsa APIs.")
    commands = parser.add_subparsers(dest="command", required=True)

    review = commands.add_parser("review", help="Full pipeline: keywords -> SERP -> competitors -> GEO -> audit -> rewrite -> scorecard")
    add_common(review, source=True)
    review.set_defaults(func=command_review)

    audit = commands.add_parser("audit", help="Deterministic on-page SEO + GEO checks only (free for local files)")
    add_common(audit, source=True, network=False)
    audit.set_defaults(func=command_audit)

    parse = commands.add_parser("parse", help="Dump the normalised article model")
    add_common(parse, source=True, network=False)
    parse.set_defaults(func=command_parse)

    keywords = commands.add_parser("keywords", help="Extract and measure the article's keywords")
    add_common(keywords, source=True, network=False)
    keywords.set_defaults(func=command_keywords)

    serp = commands.add_parser("serp", help="Google organic SERP (+ AI Mode when dfs_ai_mode is in --engines)")
    add_common(serp, keyword_required=True, network=False)
    serp.set_defaults(func=command_serp)

    competitors = commands.add_parser("competitors", help="Parse the top-ranking pages for a keyword")
    add_common(competitors, keyword_required=True, network=False)
    competitors.set_defaults(func=command_competitors)

    geo = commands.add_parser("geo", help="Query AI answer engines for a keyword")
    add_common(geo, keyword_required=True, network=False)
    geo.add_argument("--url", help="Published article URL to test for citations")
    geo.set_defaults(func=command_geo)

    render = commands.add_parser("render", help="Re-render Markdown from a saved review JSON")
    render.add_argument("--from", dest="from_json", required=True, help="review.json produced by `review --json-out`")
    render.add_argument("--out", help="Markdown output path; stdout when omitted")
    render.add_argument("--rescore", action="store_true", help="Recompute scores from the saved checks")
    render.set_defaults(func=command_render)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "fast", False) and hasattr(args, "engines"):
        args.engines = [e for e in args.engines if e not in FAST_SKIP]
    try:
        args.func(args)
    except ValueError as exc:
        parser.error(str(exc))
    except RuntimeError as exc:
        raise SystemExit(f"error: {exc}")
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
