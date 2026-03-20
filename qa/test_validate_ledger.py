from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.validate_ledger import validate_ledger


ROOT = Path(__file__).resolve().parents[1]


def write_file(contents: str, *, suffix: str = ".jsonl") -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / f"ledger{suffix}"
    path.write_text(contents, encoding="utf-8")
    return path


class ValidateLedgerTests(unittest.TestCase):
    def test_live_template_single_json_is_valid(self) -> None:
        report = validate_ledger(
            ROOT / "improvement" / "templates" / "ledger-entry.json",
            single_json=True,
        )

        self.assertTrue(report.valid)
        self.assertEqual(report.entry_count, 1)

    def test_duplicate_iteration_and_missing_baseline_fail(self) -> None:
        path = write_file(
            "\n".join(
                [
                    json.dumps(
                        {
                            "task_id": "demo-task",
                            "iteration": 1,
                            "eval_tier": "fast+full",
                            "hypothesis": "first try",
                            "changes": ["README.md"],
                            "hard_gates": {"tests": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 1,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 1},
                            "evidence": {"quality": "measured"},
                            "kept": True,
                            "summary": "ok",
                        }
                    ),
                    json.dumps(
                        {
                            "task_id": "demo-task",
                            "iteration": 1,
                            "eval_tier": "fast+full",
                            "hypothesis": "second try",
                            "changes": ["AGENTS.md"],
                            "hard_gates": {"tests": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 2,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 2},
                            "evidence": {"quality": "measured"},
                            "kept": True,
                            "summary": "still ok",
                        }
                    ),
                ]
            )
            + "\n"
        )

        report = validate_ledger(path)

        self.assertFalse(report.valid)
        messages = [issue.message for issue in report.issues]
        self.assertTrue(any("repeats iteration 1" in message for message in messages))
        self.assertTrue(any("missing baseline iteration 0" in message for message in messages))

    def test_invalid_evidence_label_fails(self) -> None:
        path = write_file(
            json.dumps(
                {
                    "task_id": "demo-task",
                    "iteration": 0,
                    "eval_tier": "fast+full",
                    "hypothesis": "baseline",
                    "changes": [],
                    "hard_gates": {"tests": "pass"},
                    "primary_metric": {
                        "name": "quality",
                        "baseline": 0,
                        "value": 0,
                        "direction": "higher_is_better",
                    },
                    "secondary_metrics": {"qa_checks": 1},
                    "evidence": {"quality": "guessed"},
                    "kept": True,
                    "summary": "baseline",
                }
            )
            + "\n"
        )

        report = validate_ledger(path)

        self.assertFalse(report.valid)
        self.assertTrue(any("labels must be one of" in issue.message for issue in report.issues))

    def test_legacy_clearer_is_better_direction_is_accepted(self) -> None:
        path = write_file(
            json.dumps(
                {
                    "task_id": "demo-task",
                    "iteration": 0,
                    "eval_tier": "fast+full",
                    "hypothesis": "baseline",
                    "changes": [],
                    "hard_gates": {"qa_verify": "pass"},
                    "primary_metric": {
                        "name": "clarity",
                        "baseline": "partial",
                        "value": "clear",
                        "direction": "clearer_is_better",
                    },
                    "secondary_metrics": {"qa_failures": 0},
                    "evidence": {"clarity": "inferred"},
                    "kept": True,
                    "summary": "baseline",
                }
            )
            + "\n"
        )

        report = validate_ledger(path)

        self.assertTrue(report.valid)

    def test_cli_summary_reports_valid_template(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "validate_ledger.py"),
                "--ledger",
                str(ROOT / "improvement" / "templates" / "ledger-entry.json"),
                "--single-json",
                "--format",
                "summary",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Ledger Contract Report", result.stdout)
        self.assertIn("Status: valid", result.stdout)


if __name__ == "__main__":
    unittest.main()
