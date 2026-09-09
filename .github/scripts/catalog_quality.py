#!/usr/bin/env python3
"""Run objective repository checks and validate only the files changed by a PR."""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit

from skills_ref import validate as validate_skill


CATEGORY_NAMES = (
    "ai-models",
    "creative",
    "financial",
    "marketing",
    "search-research",
    "social-media",
)
ROOT_SKILL_NAME = "aisa"
IGNORED_DIRECTORIES = {".git", ".github", ".hermes", ".venv", "__pycache__"}
CREDENTIAL_IGNORED_DIRECTORIES = {".git", ".hermes", ".venv", "__pycache__"}
MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+[^)]*)?\)"
)
MARKDOWN_REFERENCE_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)", re.MULTILINE)
SCRIPT_REFERENCE_RE = re.compile(
    r"(?<![\w/{])(?:python3?|bash|sh|node)\s+[\"']?"
    r"((?:\./)?scripts/[^\s`\"'<>),]+)"
)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _repository_files(
    root: Path,
    ignored_directories: set[str] = IGNORED_DIRECTORIES,
) -> Iterable[Path]:
    """Yield regular repository files without following symlinked directories."""
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in ignored_directories and not (directory_path / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = directory_path / filename
            if not path.is_symlink():
                yield path


def _skill_files(root: Path) -> list[Path]:
    return sorted(path for path in _repository_files(root) if path.name.lower() == "skill.md")


def _current_counts(root: Path) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORY_NAMES}
    for skill_file in _skill_files(root):
        relative = skill_file.relative_to(root)
        if len(relative.parts) == 3 and relative.parts[0] in counts:
            counts[relative.parts[0]] += 1
    return counts


def _is_root_aisa_skill(relative: Path) -> bool:
    return (
        len(relative.parts) == 2
        and relative.parts[0] == ROOT_SKILL_NAME
        and relative.name == "SKILL.md"
    )


def _root_skill_count(root: Path) -> int:
    return 1 if (root / ROOT_SKILL_NAME / "SKILL.md").is_file() else 0


def repository_symlinks(root: Path) -> set[str]:
    symlinks: set[str] = set()
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = sorted(
            name for name in dirnames if name not in CREDENTIAL_IGNORED_DIRECTORIES
        )
        for name in sorted((*dirnames, *filenames)):
            path = directory_path / name
            if path.is_symlink():
                symlinks.add(_relative(path, root))
        dirnames[:] = [name for name in dirnames if not (directory_path / name).is_symlink()]
    return symlinks


def check_symlinks(root: Path) -> set[str]:
    return {f"structure:symlink:{path}" for path in repository_symlinks(root)}


def check_skill_contracts(root: Path) -> set[str]:
    """Check repository layout only; schema belongs to skills-ref."""
    issues: set[str] = set()
    for category in CATEGORY_NAMES:
        category_dir = root / category
        if not category_dir.is_dir():
            issues.add(f"structure:missing-category:{category}")
            continue
        for child in sorted(category_dir.iterdir()):
            if (
                not child.is_dir()
                or child.is_symlink()
                or child.name.startswith(".")
                or child.name in IGNORED_DIRECTORIES
            ):
                continue
            if not any(
                entry.is_file() and entry.name.lower() == "skill.md"
                for entry in child.iterdir()
            ):
                issues.add(
                    f"structure:missing-skill-file:{category}/{child.name}"
                )

    for skill_file in _skill_files(root):
        relative = skill_file.relative_to(root)
        if skill_file.name != "SKILL.md":
            issues.add(f"structure:noncanonical-skill-file:{relative.as_posix()}")
        if _is_root_aisa_skill(relative):
            continue
        if len(relative.parts) == 2:
            issues.add(f"structure:root-skill:{skill_file.parent.name}")
        elif len(relative.parts) != 3 or relative.parts[0] not in CATEGORY_NAMES:
            issues.add(f"structure:invalid-skill-path:{relative.as_posix()}")

    for child in root.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in CATEGORY_NAMES or child.name in IGNORED_DIRECTORIES:
            continue
        if child.name == ROOT_SKILL_NAME:
            if not (child / "SKILL.md").is_file():
                issues.add(f"structure:missing-skill-file:{ROOT_SKILL_NAME}")
            continue
        if (child / "SKILL.md").exists():
            issues.add(f"structure:root-skill:{child.name}")
    return issues


def _check_markdown_file(root: Path, path: Path) -> set[str]:
    issues: set[str] = set()
    relative = _relative(path, root)
    text = path.read_text(encoding="utf-8", errors="replace")
    without_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    targets = [*MARKDOWN_LINK_RE.findall(without_fences)]
    targets.extend(MARKDOWN_REFERENCE_RE.findall(without_fences))
    resolved_root = root.resolve()

    for target in targets:
        normalized = target.strip("<>")
        parsed = urlsplit(normalized)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        candidate = path.parent / unquote(parsed.path)
        resolved = candidate.resolve()
        try:
            resolved.relative_to(resolved_root)
        except ValueError:
            issues.add(f"links:outside-root:{relative}:{normalized}")
            continue
        if not resolved.exists():
            issues.add(f"links:broken:{relative}:{normalized}")
        elif normalized.endswith("/") and not resolved.is_dir():
            issues.add(f"links:not-directory:{relative}:{normalized}")
        elif not normalized.endswith("/") and not resolved.is_file():
            issues.add(f"links:not-file:{relative}:{normalized}")
    return issues


def check_markdown_links(root: Path, files: Iterable[Path]) -> set[str]:
    issues: set[str] = set()
    for path in sorted(set(files)):
        if path.is_file() and path.suffix.lower() == ".md":
            issues.update(_check_markdown_file(root, path))
    return issues


def _text_chunks(path: Path) -> Iterable[str]:
    overlap = b""
    with path.open("rb") as handle:
        while chunk := handle.read(2 * 1024 * 1024):
            payload = overlap + chunk
            yield payload.decode("utf-8", errors="ignore")
            overlap = payload[-256:]


def check_credentials(root: Path) -> set[str]:
    patterns = {
        "private-key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC |ENCRYPTED )?PRIVATE KEY"),
        "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "github-token": re.compile(
            r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{70,})"
        ),
        "openai-key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        "literal-bearer": re.compile(
            r"Authorization[\"']?\s*[:=]\s*[\"']Bearer\s+"
            r"(?!\$|\{|<|YOUR_|REPLACE_|\[REDACTED\])[A-Za-z0-9._-]{12,}",
            re.IGNORECASE,
        ),
    }
    issues: set[str] = set()
    for path in _repository_files(root, CREDENTIAL_IGNORED_DIRECTORIES):
        matched: set[str] = set()
        for text in _text_chunks(path):
            for name, pattern in patterns.items():
                if name not in matched and pattern.search(text):
                    issues.add(f"secrets:{name}:{_relative(path, root)}")
                    matched.add(name)
    return issues


def check_script_syntax(root: Path, files: Iterable[Path]) -> set[str]:
    issues: set[str] = set()
    candidates = sorted(path for path in set(files) if path.is_file())

    for path in (candidate for candidate in candidates if candidate.suffix == ".py"):
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            issues.add(f"scripts:python-syntax:{_relative(path, root)}")

    for path in (candidate for candidate in candidates if candidate.suffix == ".sh"):
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        shebang = first_line[0] if first_line and first_line[0].startswith("#!") else ""
        shell = "sh" if re.search(r"(?:^|[/ ])sh(?:\s|$)", shebang) else "bash"
        try:
            result = subprocess.run(
                [shell, "-n", str(path)], capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            issues.add(f"scripts:shell-timeout:{_relative(path, root)}")
            continue
        if result.returncode:
            issues.add(f"scripts:shell-syntax:{_relative(path, root)}")

    for path in (
        candidate for candidate in candidates if candidate.suffix in {".js", ".mjs"}
    ):
        try:
            result = subprocess.run(
                ["node", "--check", str(path)], capture_output=True, text=True, timeout=30
            )
        except FileNotFoundError:
            issues.add("tooling:node-unavailable")
            break
        except subprocess.TimeoutExpired:
            issues.add(f"scripts:javascript-timeout:{_relative(path, root)}")
            continue
        if result.returncode:
            issues.add(f"scripts:javascript-syntax:{_relative(path, root)}")
    return issues


def check_skill_references(root: Path, skill_files: Iterable[Path]) -> set[str]:
    issues: set[str] = set()
    for skill_file in sorted(set(skill_files)):
        if not skill_file.is_file():
            continue
        relative = _relative(skill_file, root)
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"\{baseDir\}/([^\s`\"'<>),]+)", text):
            target = match.group(1).rstrip(".:;")
            resolved = (skill_file.parent / target).resolve()
            try:
                resolved.relative_to(skill_file.parent.resolve())
            except ValueError:
                issues.add(f"paths:outside-skill-basedir:{relative}:{target}")
                continue
            if not resolved.exists():
                issues.add(f"paths:broken-basedir:{relative}:{target}")
        for match in SCRIPT_REFERENCE_RE.finditer(text):
            target = match.group(1).rstrip(".:;")
            resolved = (skill_file.parent / target).resolve()
            try:
                resolved.relative_to(skill_file.parent.resolve())
            except ValueError:
                issues.add(f"paths:outside-skill-script:{relative}:{target}")
                continue
            if not resolved.exists():
                issues.add(f"paths:broken-relative-script:{relative}:{target}")
    return issues


def _file_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in _repository_files(root, set()):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        hashes[_relative(path, root)] = digest.hexdigest()
    return hashes


def check_exports(root: Path, expected_categories: dict[str, int]) -> set[str]:
    """Run the trusted exporter and compare exported paths and file contents."""
    issues: set[str] = set()
    exporter = root / ".github/scripts/prepare-category-repo.sh"
    if not exporter.exists():
        return {"exports:missing-exporter"}

    source_snapshots = {
        category: _file_hashes(root / category) for category in CATEGORY_NAMES
    }
    for category in CATEGORY_NAMES:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "release"
            try:
                result = subprocess.run(
                    ["bash", str(exporter), category, "--output", str(destination)],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                issues.add(f"exports:timeout:{category}")
                continue
            if result.returncode:
                issues.add(f"exports:failed:{category}")
                continue
            if destination.is_symlink() or any(
                path.is_symlink() for path in destination.rglob("*")
            ):
                issues.add(f"exports:symlink:{category}")
                continue

            count = len(list(destination.glob("*/SKILL.md")))
            expected = expected_categories[category]
            if count != expected:
                issues.add(f"exports:skill-count:{category}:{count}!={expected}")

            source_hashes = source_snapshots[category]
            exported_hashes = _file_hashes(destination)
            source_paths = set(source_hashes)
            exported_paths = set(exported_hashes)
            for path in sorted(source_paths - exported_paths):
                issues.add(f"exports:missing-file:{category}:{path}")
            for path in sorted(exported_paths - source_paths):
                issues.add(f"exports:unexpected-file:{category}:{path}")
            for path in sorted(source_paths & exported_paths):
                if source_hashes[path] != exported_hashes[path]:
                    issues.add(f"exports:content-mismatch:{category}:{path}")
    return issues


def check_validator(root: Path, skill_dirs: Iterable[Path]) -> set[str]:
    issues: set[str] = set()
    for skill_dir in sorted(set(skill_dirs)):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        if validate_skill(skill_dir):
            issues.add(f"validator:failed:{_relative(skill_dir, root)}")
    return issues


def _changed_skill_dirs(root: Path, changed_files: Iterable[Path]) -> set[Path]:
    skill_dirs: set[Path] = set()
    for path in changed_files:
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] == ROOT_SKILL_NAME:
            skill_dir = root / ROOT_SKILL_NAME
            if (skill_dir / "SKILL.md").is_file():
                skill_dirs.add(skill_dir)
            continue
        if len(relative.parts) >= 2 and relative.parts[0] in CATEGORY_NAMES:
            skill_dir = root / relative.parts[0] / relative.parts[1]
            if (skill_dir / "SKILL.md").is_file():
                skill_dirs.add(skill_dir)
    return skill_dirs


def collect_changed_issues(root: Path, changed_files: Iterable[Path]) -> set[str]:
    changed = set(changed_files)
    skill_dirs = _changed_skill_dirs(root, changed)
    skill_files = {skill_dir / "SKILL.md" for skill_dir in skill_dirs}
    issues: set[str] = set()
    issues.update(check_markdown_links(root, changed | skill_files))
    issues.update(check_script_syntax(root, changed))
    issues.update(check_skill_references(root, skill_files))
    issues.update(check_validator(root, skill_dirs))
    return issues


def collect_global_issues(root: Path) -> set[str]:
    issues: set[str] = set()
    issues.update(check_symlinks(root))
    issues.update(check_skill_contracts(root))
    issues.update(check_credentials(root))
    issues.update(check_exports(root, _current_counts(root)))
    return issues


def collect_all_issues(root: Path) -> set[str]:
    files = set(_repository_files(root, CREDENTIAL_IGNORED_DIRECTORIES))
    return collect_global_issues(root) | collect_changed_issues(root, files)


def git_changed_files(root: Path, reference: str) -> set[Path]:
    """Return committed, staged, unstaged, and untracked paths changed from reference."""
    relative_paths: set[str] = set()
    commands = (
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", f"{reference}...HEAD", "--"],
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", "--"],
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRD", "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or f"failed to run {' '.join(command)}")
        relative_paths.update(line for line in result.stdout.splitlines() if line)
    return {root / relative for relative in relative_paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--changed-from", help="Validate files changed from this Git ref")
    mode.add_argument("--all", action="store_true", help="Validate the entire catalog")
    args = parser.parse_args()

    root = args.root.resolve()
    if args.all:
        issues = collect_all_issues(root)
        print("scope=all")
    else:
        changed_files = git_changed_files(root, args.changed_from)
        issues = collect_global_issues(root) | collect_changed_issues(root, changed_files)
        print(f"scope=changed files={len(changed_files)}")

    counts = _current_counts(root)
    print(f"skills={sum(counts.values()) + _root_skill_count(root)}")
    if not issues:
        print("Catalog quality checks passed")
        return 0

    print(f"issues={len(issues)}")
    for issue in sorted(issues):
        print(f"  - {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
