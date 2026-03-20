from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.pattern_recognition import load_ledger, normalize_token, suggest_patterns


ROOT = Path(__file__).resolve().parents[1]


def write_ledger(entries: list[dict]) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    ledger_path = temp_dir / "ledger.jsonl"
    content = "\n".join(json.dumps(entry) for entry in entries) + "\n"
    ledger_path.write_text(content, encoding="utf-8")
    return ledger_path


class PatternRecognitionTests(unittest.TestCase):
    def test_load_ledger_skips_blank_lines_and_parses_entries(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-one",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Improve README clarity",
                    "summary": "README verified on GitHub",
                    "changes": ["README.md"],
                    "hard_gates": {"qa_verify": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "clarity"},
                }
            ]
        )
        ledger_path.write_text(ledger_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

        entries = load_ledger(ledger_path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].task_id, "demo-one")
        self.assertTrue(entries[0].kept)
        self.assertEqual(entries[0].changes, ("README.md",))

    def test_load_ledger_rejects_non_boolean_kept_values(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-bad-kept",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Invalid kept value",
                    "summary": "This should fail parsing",
                    "changes": ["README.md"],
                    "hard_gates": {"qa_verify": "pass"},
                    "kept": "false",
                    "primary_metric": {"name": "clarity"},
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "boolean 'kept'"):
            load_ledger(ledger_path)

    def test_suggest_patterns_detects_area_and_gate_patterns(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-readme-one",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Refine README diagram",
                    "summary": "Verified GitHub render for README diagram",
                    "changes": ["README.md", "improvement/current-task.md"],
                    "hard_gates": {"qa_verify": "pass", "github_readme_check": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "readme_quality"},
                },
                {
                    "task_id": "demo-readme-two",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Strengthen README comparison",
                    "summary": "GitHub render remained clean after README update",
                    "changes": ["README.md", "improvement/ledger.jsonl"],
                    "hard_gates": {"qa_verify": "pass", "github_readme_check": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "readme_quality"},
                },
                {
                    "task_id": "demo-mixed-areas",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Touch README and tooling together",
                    "summary": "GitHub check passed while a tooling file also changed",
                    "changes": ["README.md", "tools/pattern_recognition.py"],
                    "hard_gates": {"qa_verify": "pass", "github_readme_check": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "readme_quality"},
                },
                {
                    "task_id": "demo-tooling",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Build pattern recognition tool",
                    "summary": "Added tested CLI for ledger patterns",
                    "changes": ["tools/pattern_recognition.py", "qa/test_pattern_recognition.py"],
                    "hard_gates": {"qa_verify": "pass", "tests": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "tool_exists"},
                },
                {
                    "task_id": "demo-discarded",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Discarded README experiment",
                    "summary": "Did not keep the experiment",
                    "changes": ["README.md"],
                    "hard_gates": {"qa_verify": "fail"},
                    "kept": False,
                    "primary_metric": {"name": "readme_quality"},
                },
            ]
        )

        candidates = suggest_patterns(load_ledger(ledger_path), min_support=2, limit=10)
        by_key = {(candidate.kind, candidate.key): candidate for candidate in candidates}

        readme_candidate = by_key[("area", "README.md")]
        self.assertEqual(readme_candidate.support, 3)
        self.assertIn(("qa_verify", 2), readme_candidate.top_gates)
        self.assertIn(("github_readme_check", 2), readme_candidate.top_gates)

        gate_candidate = by_key[("gate", "qa_verify")]
        self.assertEqual(gate_candidate.support, 4)

        tools_candidate = by_key[("area", "tools/")]
        self.assertEqual(tools_candidate.support, 2)
        self.assertNotIn(("github_readme_check", 1), tools_candidate.top_gates)
        self.assertNotIn(("github", 1), tools_candidate.top_terms)

    def test_cli_outputs_markdown_report(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-readme-one",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Refine README diagram",
                    "summary": "Verified GitHub render for README diagram",
                    "changes": ["README.md", "improvement/current-task.md"],
                    "hard_gates": {"qa_verify": "pass", "github_readme_check": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "readme_quality"},
                },
                {
                    "task_id": "demo-readme-two",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Strengthen README comparison",
                    "summary": "GitHub render remained clean after README update",
                    "changes": ["README.md", "improvement/ledger.jsonl"],
                    "hard_gates": {"qa_verify": "pass", "github_readme_check": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "readme_quality"},
                },
            ]
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "pattern_recognition.py"),
                "--ledger",
                str(ledger_path),
                "--format",
                "markdown",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Pattern Recognition Report", result.stdout)
        self.assertIn("## Pattern:", result.stdout)
        self.assertIn("README.md", result.stdout)

    def test_cli_json_output_is_stable_across_hash_seeds(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-alpha",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Compare apples and oranges",
                    "summary": "alpha beta",
                    "changes": ["docs/guide.md"],
                    "hard_gates": {"tests": "pass", "lint": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "stability"},
                },
                {
                    "task_id": "demo-beta",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Compare oranges and apples",
                    "summary": "beta alpha",
                    "changes": ["docs/guide.md"],
                    "hard_gates": {"lint": "pass", "tests": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "stability"},
                },
            ]
        )

        env = {**os.environ, "PYTHONHASHSEED": "random"}
        command = [
            "python3",
            str(ROOT / "tools" / "pattern_recognition.py"),
            "--ledger",
            str(ledger_path),
            "--format",
            "json",
        ]

        first = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
        second = subprocess.run(command, check=True, capture_output=True, text=True, env=env)

        self.assertEqual(first.stdout, second.stdout)

    def test_normalize_token_keeps_non_plural_words_intact(self) -> None:
        self.assertEqual(normalize_token("analysis"), "analysis")
        self.assertEqual(normalize_token("status"), "status")
        self.assertEqual(normalize_token("stories"), "story")

    def test_meta_area_without_focused_signal_is_not_suggested(self) -> None:
        ledger_path = write_ledger(
            [
                {
                    "task_id": "demo-tool-one",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Build tooling and tests together",
                    "summary": "Added tool implementation with tests",
                    "changes": ["tools/pattern_recognition.py", "qa/test_pattern_recognition.py"],
                    "hard_gates": {"tests": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "tool_exists"},
                },
                {
                    "task_id": "demo-tool-two",
                    "iteration": 1,
                    "eval_tier": "fast+full",
                    "hypothesis": "Refine tooling and tests together",
                    "summary": "Improved tool coverage with tests",
                    "changes": ["tools/helper.py", "qa/test_helper.py"],
                    "hard_gates": {"tests": "pass"},
                    "kept": True,
                    "primary_metric": {"name": "tool_exists"},
                },
            ]
        )

        candidates = suggest_patterns(load_ledger(ledger_path), min_support=2, limit=10)
        keys = {(candidate.kind, candidate.key) for candidate in candidates}

        self.assertIn(("area", "tools/"), keys)
        self.assertNotIn(("area", "qa/"), keys)


if __name__ == "__main__":
    unittest.main()
