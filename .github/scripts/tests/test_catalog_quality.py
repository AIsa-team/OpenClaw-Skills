from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "catalog_quality.py"
spec = importlib.util.spec_from_file_location("catalog_quality", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
catalog_quality = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = catalog_quality
spec.loader.exec_module(catalog_quality)


def write_skill(root: Path, category: str, name: str, description: str = "test skill") -> Path:
    skill = root / category / name
    skill.mkdir(parents=True, exist_ok=True)
    skill_file = skill / "SKILL.md"
    skill_file.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n# {name}\n",
        encoding="utf-8",
    )
    return skill_file


def write_copy_exporter(root: Path) -> None:
    exporter = root / ".github" / "scripts" / "prepare-category-repo.sh"
    exporter.parent.mkdir(parents=True, exist_ok=True)
    exporter.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "category=$1\n"
        "output=$3\n"
        "mkdir -p \"$output\"\n"
        "cp -a \"$category/.\" \"$output/\"\n",
        encoding="utf-8",
    )


class ChangedScopeTests(unittest.TestCase):
    def test_untouched_legacy_problems_do_not_block_an_unrelated_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_skill = write_skill(root, "financial", "legacy", description="")
            old_script = old_skill.parent / "scripts" / "broken.py"
            old_script.parent.mkdir()
            old_script.write_text("def broken(:\n", encoding="utf-8")
            changed = root / "README.md"
            changed.write_text("# Catalog\n", encoding="utf-8")

            issues = catalog_quality.collect_changed_issues(root, {changed})

        self.assertEqual(issues, set())

    def test_changed_skill_file_runs_official_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = write_skill(root, "financial", "example", description="")

            issues = catalog_quality.collect_changed_issues(root, {skill_file})

        self.assertEqual(issues, {"validator:failed:financial/example"})

    def test_changed_markdown_file_checks_local_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            doc = root / "README.md"
            doc.write_text("[missing](missing.md)\n", encoding="utf-8")

            issues = catalog_quality.collect_changed_issues(root, {doc})

        self.assertEqual(issues, {"links:broken:README.md:missing.md"})

    def test_changing_any_file_in_a_skill_runs_that_skill_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = write_skill(root, "financial", "example", description="")
            changed = skill_file.parent / "README.md"
            changed.write_text("# Example\n", encoding="utf-8")

            issues = catalog_quality.collect_changed_issues(root, {changed})

        self.assertEqual(issues, {"validator:failed:financial/example"})

    def test_changed_script_checks_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "financial" / "example" / "scripts" / "broken.mjs"
            script.parent.mkdir(parents=True)
            script.write_text("const = ;\n", encoding="utf-8")

            issues = catalog_quality.collect_changed_issues(root, {script})

        self.assertEqual(
            issues,
            {"scripts:javascript-syntax:financial/example/scripts/broken.mjs"},
        )

    def test_changed_skill_file_checks_referenced_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = write_skill(root, "financial", "example")
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8")
                + "Run `node scripts/missing.mjs`.\n",
                encoding="utf-8",
            )

            issues = catalog_quality.collect_changed_issues(root, {skill_file})

        self.assertEqual(
            issues,
            {
                "paths:broken-relative-script:financial/example/SKILL.md:"
                "scripts/missing.mjs"
            },
        )

    def test_touching_a_skill_checks_links_in_its_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_file = write_skill(root, "financial", "example")
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8")
                + "See [missing reference](references/missing.md).\n",
                encoding="utf-8",
            )
            changed = skill_file.parent / "scripts" / "client.py"
            changed.parent.mkdir()
            changed.write_text("pass\n", encoding="utf-8")

            issues = catalog_quality.collect_changed_issues(root, {changed})

        self.assertEqual(
            issues,
            {
                "links:broken:financial/example/SKILL.md:references/missing.md"
            },
        )

    def test_git_changed_files_returns_only_committed_pr_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
            )
            kept = root / "kept.md"
            changed = root / "changed.md"
            kept.write_text("same\n", encoding="utf-8")
            changed.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            reference = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            changed.write_text("after\n", encoding="utf-8")
            added = root / "added.md"
            added.write_text("new\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "change"], cwd=root, check=True)

            files = catalog_quality.git_changed_files(root, reference)

        self.assertEqual(
            {path.relative_to(root).as_posix() for path in files},
            {"added.md", "changed.md"},
        )


class GlobalChecksTests(unittest.TestCase):
    def test_category_child_directory_requires_skill_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for category in catalog_quality.CATEGORY_NAMES:
                (root / category).mkdir()
            incomplete = root / "financial" / "incomplete-skill"
            incomplete.mkdir()
            (incomplete / "README.md").write_text("# Incomplete\n", encoding="utf-8")

            issues = catalog_quality.check_skill_contracts(root)

        self.assertEqual(
            issues,
            {"structure:missing-skill-file:financial/incomplete-skill"},
        )

    def test_structure_uses_official_validator_without_optional_field_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for category in catalog_quality.CATEGORY_NAMES:
                (root / category).mkdir()
            skill_file = write_skill(root, "financial", "example")
            skill_file.write_text(
                "---\nname: example\ndescription: test\nlicense: ''\ncompatibility: ''\n---\n",
                encoding="utf-8",
            )

            structure = catalog_quality.check_skill_contracts(root)
            validator = catalog_quality.check_validator(root, {skill_file.parent})

        self.assertEqual(structure, set())
        self.assertEqual(validator, set())

    def test_repository_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            outside = Path(temp_dir) / "outside"
            outside.write_text("x", encoding="utf-8")
            os.symlink(outside, root / "linked")

            issues = catalog_quality.check_symlinks(root)

        self.assertEqual(issues, {"structure:symlink:linked"})

    def test_obvious_credentials_are_rejected_but_local_venv_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = "github_" + "pat_" + "F" * 82
            (root / "credential.txt").write_text(sample, encoding="utf-8")
            ignored = root / ".venv" / "credential.txt"
            ignored.parent.mkdir()
            ignored.write_text(sample, encoding="utf-8")

            issues = catalog_quality.check_credentials(root)

        self.assertEqual(issues, {"secrets:github-token:credential.txt"})

    def test_exporter_must_preserve_file_paths_and_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for category in catalog_quality.CATEGORY_NAMES:
                write_skill(root, category, "example")
            exporter = root / ".github" / "scripts" / "prepare-category-repo.sh"
            exporter.parent.mkdir(parents=True)
            exporter.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "category=$1\n"
                "output=$3\n"
                "mkdir -p \"$output\"\n"
                "cp -a \"$category/.\" \"$output/\"\n"
                "if [[ \"$category\" == financial ]]; then\n"
                "  printf 'changed\\n' >> \"$output/example/SKILL.md\"\n"
                "fi\n",
                encoding="utf-8",
            )

            issues = catalog_quality.check_exports(
                root, {category: 1 for category in catalog_quality.CATEGORY_NAMES}
            )

        self.assertEqual(
            issues,
            {"exports:content-mismatch:financial:example/SKILL.md"},
        )

    def test_global_checks_pass_for_a_small_valid_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for category in catalog_quality.CATEGORY_NAMES:
                write_skill(root, category, "example")
            write_copy_exporter(root)

            issues = catalog_quality.collect_global_issues(root)

        self.assertEqual(issues, set())


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_uses_changed_scope_without_a_baseline(self) -> None:
        repository_root = MODULE_PATH.parents[2]
        workflow = (
            repository_root / ".github" / "workflows" / "validate-skill-catalog.yaml"
        ).read_text(encoding="utf-8")

        self.assertIn("--changed-from", workflow)
        self.assertNotIn("skill-quality-baseline", workflow)
        self.assertNotIn("REFERENCE_ARGS", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("--require-hashes", workflow)


if __name__ == "__main__":
    unittest.main()
