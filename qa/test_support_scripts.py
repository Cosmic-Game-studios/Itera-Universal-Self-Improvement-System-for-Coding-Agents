from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.validate_ledger import validate_ledger


ROOT = Path(__file__).resolve().parents[1]


class SupportScriptTests(unittest.TestCase):
    def test_bootstrap_task_cli_writes_contract(self) -> None:
        root = Path(tempfile.mkdtemp())
        output = root / "current-task.md"

        subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "bootstrap_task.py"),
                "--task-id",
                "2026-03-20-demo-task",
                "--task-name",
                "Demo task",
                "--task-type",
                "feature",
                "--desired-outcome",
                "Scaffold a task contract",
                "--plan-step",
                "Draft the contract",
                "--fast-eval",
                "python3 qa/verify_skill_system.py",
                "--full-gate",
                "python3 qa/verify_skill_system.py",
                "--primary-metric-name",
                "quality",
                "--primary-metric-direction",
                "higher_is_better",
                "--primary-metric-baseline",
                "not started",
                "--primary-metric-target",
                "scaffolded",
                "--output",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        text = output.read_text(encoding="utf-8")
        self.assertIn("- Task ID: 2026-03-20-demo-task", text)
        self.assertIn("## Execution plan", text)
        self.assertIn("## Memory refresh", text)
        self.assertIn("## Full gates", text)
        self.assertIn("## Evaluation commands", text)
        self.assertIn("python3 qa/verify_skill_system.py", text)

    def test_bootstrap_task_refuses_overwrite_without_flag(self) -> None:
        root = Path(tempfile.mkdtemp())
        output = root / "current-task.md"
        output.write_text("existing\n", encoding="utf-8")

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "bootstrap_task.py"),
                "--task-id",
                "2026-03-20-demo-task",
                "--task-name",
                "Demo task",
                "--task-type",
                "feature",
                "--desired-outcome",
                "Scaffold a task contract",
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--overwrite", result.stderr)

    def test_log_iteration_cli_appends_valid_entry(self) -> None:
        root = Path(tempfile.mkdtemp())
        ledger = root / "ledger.jsonl"

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "log_iteration.py"),
                "--ledger",
                str(ledger),
                "--task-id",
                "demo-task",
                "--iteration",
                "0",
                "--eval-tier",
                "fast+full",
                "--hypothesis",
                "Baseline",
                "--hard-gate",
                "qa_verify=pass",
                "--primary-metric-name",
                "quality",
                "--primary-metric-baseline",
                "0",
                "--primary-metric-value",
                "0",
                "--primary-metric-direction",
                "higher_is_better",
                "--secondary-metric",
                "qa_checks=80",
                "--evidence",
                "qa_verify=measured",
                "--mistake",
                "Forgot to refresh the ledger contract before appending.",
                "--fix",
                "Used the logging helper so the entry stayed valid.",
                "--prevention-rule",
                "Log iterations with the helper instead of hand-editing JSONL.",
                "--kept",
                "true",
                "--summary",
                "Baseline entry.",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["ledger_report"]["entry_count"], 1)
        self.assertEqual(
            payload["appended"]["memory"]["mistakes"],
            ["Forgot to refresh the ledger contract before appending."],
        )
        self.assertTrue(ledger.exists())
        self.assertTrue(validate_ledger(ledger).valid)

    def test_log_iteration_rejects_duplicate_iteration(self) -> None:
        root = Path(tempfile.mkdtemp())
        ledger = root / "ledger.jsonl"
        base_command = [
            "python3",
            str(ROOT / "tools" / "log_iteration.py"),
            "--ledger",
            str(ledger),
            "--task-id",
            "demo-task",
            "--iteration",
            "0",
            "--eval-tier",
            "fast+full",
            "--hypothesis",
            "Baseline",
            "--hard-gate",
            "qa_verify=pass",
            "--primary-metric-name",
            "quality",
            "--primary-metric-baseline",
            "0",
            "--primary-metric-value",
            "0",
            "--primary-metric-direction",
            "higher_is_better",
            "--secondary-metric",
            "qa_checks=80",
            "--evidence",
            "qa_verify=measured",
            "--kept",
            "true",
            "--summary",
            "Baseline entry.",
        ]

        subprocess.run(base_command, check=True, capture_output=True, text=True)
        duplicate = subprocess.run(base_command, capture_output=True, text=True)

        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("repeats iteration 0", duplicate.stderr or duplicate.stdout)


if __name__ == "__main__":
    unittest.main()
