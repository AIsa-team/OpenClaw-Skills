"""Contract tests for the AISA credential/config resolver shared by AIsa skills.

Several skills carry a byte-identical `_resolve_aisa_api_key()` (last30days
generalises it to `_resolve_from_files(name)`), because a skill has to be
self-contained and cannot import across skill directories. That duplication is
the reason these tests live here rather than in any one skill: this file is the
single place asserting that every copy still behaves the same.

Resolution order under test:

    1. the environment variable
    2. ~/.aisa/credentials
    3. $HERMES_HOME/profiles/$HERMES_PROFILE/.env   (when HERMES_PROFILE is set)
    4. $HERMES_HOME/.env

A sibling profile is never read: on a host running several profiles that would
both leak credentials across profiles and hand back the wrong tenant's key.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Callable

REPO = Path(__file__).resolve().parents[3]

# (label, path, exported symbol) — every copy that must satisfy the contract.
TARGETS: list[tuple[str, str, str]] = [
    ("marketpulse", "financial/marketpulse/scripts/market_client.py", "_resolve_aisa_api_key"),
    ("prediction-market-data", "financial/prediction-market-data/scripts/prediction_market_client.py", "_resolve_aisa_api_key"),
    ("multi-source-search", "search-research/multi-source-search/scripts/search_client.py", "_resolve_aisa_api_key"),
    ("aisa-twitter-api", "social-media/aisa-twitter-api/scripts/twitter_client.py", "_resolve_aisa_api_key"),
    ("aisa-twitter-api-oauth", "social-media/aisa-twitter-api/scripts/twitter_oauth_client.py", "_resolve_aisa_api_key"),
    ("article-seo-geo-review", "marketing/article-seo-geo-review/scripts/review_article.py", "_resolve_aisa_api_key"),
    ("last30days", "search-research/last30days/scripts/lib/env.py", "_resolve_aisa_api_key"),
]

# Neutralised for every case so a real value on the machine running the tests
# can never make one pass.
SCRUB = ("AISA_API_KEY", "AISA_MODEL", "HERMES_HOME", "HERMES_PROFILE", "HOME",
         "USERPROFILE", "LAST30DAYS_CONFIG_DIR", "XDG_CONFIG_HOME")


def load(path: Path) -> ModuleType:
    """Import a target file, honouring package layout when there is one."""
    pkg_parts: list[str] = []
    anchor = path.parent
    while (anchor / "__init__.py").exists():
        pkg_parts.insert(0, anchor.name)
        anchor = anchor.parent

    added = str(anchor) not in sys.path
    if added:
        sys.path.insert(0, str(anchor))
    try:
        if pkg_parts:
            dotted = ".".join(pkg_parts + [path.stem])
            for stale in [m for m in sys.modules if m.split(".")[0] == pkg_parts[0]]:
                del sys.modules[stale]
            return importlib.import_module(dotted)
        name = f"_t_{path.stem}_{abs(hash(str(path))) % 100000}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            sys.path.remove(str(anchor))


class Sandbox:
    """Fake HOME + HERMES_HOME with a fully scrubbed environment."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.hermes = self.home / ".hermes"
        (self.home / ".aisa").mkdir(parents=True)
        (self.hermes / "profiles").mkdir(parents=True)
        self._saved: dict[str, str | None] = {}

    def __enter__(self) -> "Sandbox":
        for key in SCRUB:
            self._saved[key] = os.environ.pop(key, None)
        os.environ["HOME"] = str(self.home)
        os.environ["USERPROFILE"] = str(self.home)
        return self

    def __exit__(self, *exc: object) -> bool:
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        self._tmp.cleanup()
        return False

    def credentials(self, text: str) -> None:
        (self.home / ".aisa" / "credentials").write_text(text, encoding="utf-8")

    def credentials_bytes(self, data: bytes) -> None:
        (self.home / ".aisa" / "credentials").write_bytes(data)

    def profile_env(self, name: str, text: str) -> None:
        directory = self.hermes / "profiles" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".env").write_text(text, encoding="utf-8")
        os.environ["HERMES_HOME"] = str(self.hermes)

    def hermes_env(self, text: str) -> None:
        (self.hermes / ".env").write_text(text, encoding="utf-8")
        os.environ["HERMES_HOME"] = str(self.hermes)


Setup = Callable[[Sandbox], None]


def _env_wins(sb: Sandbox) -> None:
    os.environ["AISA_API_KEY"] = "from-env"
    sb.credentials("AISA_API_KEY=from-credentials\n")
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")


def _credentials(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY=from-credentials\n")


def _credentials_beat_profile(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY=from-credentials\n")
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


def _named_profile(sb: Sandbox) -> None:
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


def _sibling_never_read(sb: Sandbox) -> None:
    sb.profile_env("aaa-other", "AISA_API_KEY=wrong-tenant\n")
    sb.profile_env("zzz-mine", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "zzz-mine"


def _no_profile_no_scan(sb: Sandbox) -> None:
    # HERMES_PROFILE unset -> do NOT sweep profiles/*/.env.
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")


def _hermes_env(sb: Sandbox) -> None:
    # Under `hermes --profile X` this is the shape that fires: HERMES_HOME is
    # the profile directory itself and HERMES_PROFILE is not set.
    sb.hermes_env("AISA_API_KEY=from-hermes-env\n")


def _nothing(sb: Sandbox) -> None:
    pass


def _empty_env_falls_through(sb: Sandbox) -> None:
    os.environ["AISA_API_KEY"] = ""
    sb.credentials("AISA_API_KEY=from-credentials\n")


def _empty_value_falls_through(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY=\n")
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


def _double_quoted(sb: Sandbox) -> None:
    sb.credentials('AISA_API_KEY="from-credentials"\n')


def _single_quoted(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY='from-credentials'\n")


def _export_prefix(sb: Sandbox) -> None:
    sb.credentials("export AISA_API_KEY=from-credentials\n")


def _whole_line_comment_ignored(sb: Sandbox) -> None:
    sb.credentials("# AISA_API_KEY=commented-out\nAISA_API_KEY=from-credentials\n")


def _inline_comment_stripped(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY=from-credentials  # my key\n")


def _quoted_then_comment(sb: Sandbox) -> None:
    # Regression: a whole-value quote check fails here (last char is a comment
    # character, not a quote), so a naive parser takes the unquoted branch and
    # returns the value with its quotes still attached — a garbage bearer token.
    sb.credentials('AISA_API_KEY="from-credentials" # my key\n')


def _single_quoted_then_comment(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY='from-credentials' # my key\n")


def _quoted_then_tab_comment(sb: Sandbox) -> None:
    sb.credentials('AISA_API_KEY="from-credentials"\t# my key\n')


def _hash_inside_quotes_kept(sb: Sandbox) -> None:
    sb.credentials('AISA_API_KEY="pa#ss"\n')


def _hash_inside_quotes_plus_comment(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY='pa#ss' # my key\n")


def _unterminated_quote(sb: Sandbox) -> None:
    sb.credentials('AISA_API_KEY="from-credentials\n')


def _spaces_inside_quotes_kept(sb: Sandbox) -> None:
    sb.credentials('AISA_API_KEY="from credentials"\n')


def _spaces_around_equals(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY = from-credentials\n")


def _similar_names_ignored(sb: Sandbox) -> None:
    sb.credentials("OTHER=nope\nAISA_API_KEY_SUFFIX=nope2\nAISA_API_KEY=from-credentials\n")


def _trailing_whitespace_stripped(sb: Sandbox) -> None:
    sb.credentials("AISA_API_KEY=from-credentials   \n")


def _crlf(sb: Sandbox) -> None:
    sb.credentials_bytes(b"AISA_API_KEY=from-credentials\r\n")


def _utf8_bom(sb: Sandbox) -> None:
    sb.credentials_bytes(b"\xef\xbb\xbfAISA_API_KEY=from-credentials\n")


def _non_utf8_does_not_raise(sb: Sandbox) -> None:
    # UnicodeDecodeError is a ValueError, not an OSError: a bare `except OSError`
    # lets it escape and the resolver raises despite documenting that it never
    # does. The corrupt value must also not be returned.
    sb.credentials_bytes(b"AISA_API_KEY=\xff\xfe\x80bad\n")
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


def _utf16_does_not_raise(sb: Sandbox) -> None:
    sb.credentials_bytes("AISA_API_KEY=utf16\n".encode("utf-16"))
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


def _unreadable_file_skipped(sb: Sandbox) -> None:
    # A directory where a file is expected must fall through, not raise.
    (sb.home / ".aisa" / "credentials").mkdir()
    sb.profile_env("aisa-cio", "AISA_API_KEY=from-profile\n")
    os.environ["HERMES_PROFILE"] = "aisa-cio"


CASES: list[tuple[str, Setup, str]] = [
    ("env var wins over every file", _env_wins, "from-env"),
    ("~/.aisa/credentials", _credentials, "from-credentials"),
    ("credentials beat the profile .env", _credentials_beat_profile, "from-credentials"),
    ("named profile .env", _named_profile, "from-profile"),
    ("sibling profile is never read", _sibling_never_read, "from-profile"),
    ("no HERMES_PROFILE means no sweep", _no_profile_no_scan, ""),
    ("$HERMES_HOME/.env as last resort", _hermes_env, "from-hermes-env"),
    ("nothing found returns empty", _nothing, ""),
    ("empty env var falls through", _empty_env_falls_through, "from-credentials"),
    ("empty value falls through", _empty_value_falls_through, "from-profile"),
    ("double-quoted value", _double_quoted, "from-credentials"),
    ("single-quoted value", _single_quoted, "from-credentials"),
    ("export prefix", _export_prefix, "from-credentials"),
    ("whole-line comment ignored", _whole_line_comment_ignored, "from-credentials"),
    ("inline comment stripped", _inline_comment_stripped, "from-credentials"),
    ('"value" then comment', _quoted_then_comment, "from-credentials"),
    ("'value' then comment", _single_quoted_then_comment, "from-credentials"),
    ('"value" then tab comment', _quoted_then_tab_comment, "from-credentials"),
    ("# inside quotes is data", _hash_inside_quotes_kept, "pa#ss"),
    ("# inside quotes, comment after", _hash_inside_quotes_plus_comment, "pa#ss"),
    ("unterminated quote", _unterminated_quote, "from-credentials"),
    ("spaces inside quotes kept", _spaces_inside_quotes_kept, "from credentials"),
    ("spaces around =", _spaces_around_equals, "from-credentials"),
    ("similar key names ignored", _similar_names_ignored, "from-credentials"),
    ("trailing whitespace stripped", _trailing_whitespace_stripped, "from-credentials"),
    ("CRLF line endings", _crlf, "from-credentials"),
    ("UTF-8 BOM tolerated", _utf8_bom, "from-credentials"),
    ("non-UTF-8 file does not raise", _non_utf8_does_not_raise, "from-profile"),
    ("UTF-16 file does not raise", _utf16_does_not_raise, "from-profile"),
    ("unreadable path skipped", _unreadable_file_skipped, "from-profile"),
]


class CredentialResolutionContract(unittest.TestCase):
    def test_every_copy_satisfies_the_contract(self) -> None:
        for label, rel, symbol in TARGETS:
            path = REPO / rel
            self.assertTrue(path.exists(), f"{label}: missing {rel}")
            module = load(path)
            resolve = getattr(module, symbol, None)
            self.assertIsNotNone(resolve, f"{label}: {rel} does not export {symbol}()")
            assert resolve is not None
            for name, setup, expected in CASES:
                with self.subTest(skill=label, case=name):
                    with Sandbox() as sb:
                        setup(sb)
                        self.assertEqual(resolve(), expected)

    def test_last30days_http_layer_uses_the_resolver(self) -> None:
        """The HTTP layer must actually reach the header, not merely import it."""
        http_path = REPO / "search-research/last30days/scripts/lib/http.py"
        for name, setup, expected in [
            ("credentials file", _credentials, "from-credentials"),
            ("profile .env", _named_profile, "from-profile"),
        ]:
            with self.subTest(case=name):
                with Sandbox() as sb:
                    setup(sb)
                    module = load(http_path)
                    headers: dict[str, str] = {}
                    module._inject_aisa_headers("https://api.aisa.one/apis/v1/x", headers, False)
                    self.assertEqual(headers.get("Authorization"), f"Bearer {expected}")

    def test_last30days_clean_mode_reads_nothing_from_disk(self) -> None:
        """LAST30DAYS_CONFIG_DIR="" means hermetic.

        evaluate_search_quality's create_eval_env() builds a deliberately minimal
        environment to compare two revisions; picking the operator's model pin up
        off disk there would silently change what is being measured.
        """
        env_path = REPO / "search-research/last30days/scripts/lib/env.py"
        with Sandbox() as sb:
            sb.credentials("AISA_API_KEY=from-credentials\nAISA_MODEL=from-credentials\n")
            os.environ["LAST30DAYS_CONFIG_DIR"] = ""
            module = load(env_path)
            config = module.get_config()
            self.assertIsNone(config["AISA_API_KEY"])
            self.assertIsNone(config["AISA_MODEL"])

        with Sandbox() as sb:
            sb.credentials("AISA_API_KEY=from-credentials\nAISA_MODEL=from-credentials\n")
            module = load(env_path)
            config = module.get_config()
            self.assertEqual(config["AISA_API_KEY"], "from-credentials")
            self.assertEqual(config["AISA_MODEL"], "from-credentials")

    def test_resolver_bodies_are_identical_across_skills(self) -> None:
        """Byte-identical copies, so a fix in one cannot silently miss the rest."""
        import ast

        bodies: dict[str, str] = {}
        for label, rel, _ in TARGETS:
            source = (REPO / rel).read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in (
                    "_resolve_aisa_api_key", "_resolve_from_files"
                ):
                    if node.name == "_resolve_aisa_api_key" and len(node.body) <= 2:
                        continue  # last30days' thin back-compat alias
                    lines = source.replace("\r\n", "\n").split("\n")
                    assert node.end_lineno is not None
                    # Compare the executable body only: last30days generalises the
                    # signature and docstring, but the parsing must not drift.
                    body_start = node.body[1].lineno - 1 if len(node.body) > 1 else node.lineno
                    bodies[label] = "\n".join(lines[body_start:node.end_lineno])
                    break

        clients = {k: v for k, v in bodies.items() if k != "last30days"}
        self.assertEqual(len(clients), 6, f"expected 6 client copies, got {sorted(clients)}")
        self.assertEqual(len(set(clients.values())), 1,
                         "client copies of the resolver have drifted apart")


if __name__ == "__main__":
    unittest.main()
