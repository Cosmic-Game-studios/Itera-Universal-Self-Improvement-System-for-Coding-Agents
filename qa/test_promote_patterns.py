from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.promote_patterns import build_memory_candidates, build_recognition_candidates, dedupe_candidates, existing_fingerprints


ROOT = Path(__file__).resolve().parents[1]


def write_ledger(entries: list[dict]) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    ledger_path = temp_dir / "ledger.jsonl"
    ledger_path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
    return ledger_path


def write_patterns(text: str) -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    patterns_path = temp_dir / "patterns.md"
    patterns_path.write_text(text, encoding="utf-8")
    return patterns_path


def make_entry(
    *,
    task_id: str,
    iteration: int,
    summary: str,
    changes: list[str],
    hard_gates: dict[str, str],
    memory: dict[str, list[str]] | None = None,
) -> dict:
    payload = {
        "task_id": task_id,
        "iteration": iteration,
        "eval_tier": "fast+full",
        "hypothesis": "Improve the workflow",
        "changes": changes,
        "hard_gates": hard_gates,
        "primary_metric": {
            "name": "quality",
            "baseline": 0,
            "value": 1 if iteration else 0,
            "direction": "higher_is_better",
        },
        "secondary_metrics": {"qa_checks": 80 + iteration},
        "evidence": {"qa_checks": "measured", "quality": "measured"},
        "kept": True,
        "summary": summary,
    }
    if memory is not None:
        payload["memory"] = memory
    return payload


def make_baseline(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "iteration": 0,
        "eval_tier": "fast+full",
        "hypothesis": "Baseline",
        "changes": [],
        "hard_gates": {"qa_verify": "pass"},
        "primary_metric": {
            "name": "quality",
            "baseline": 0,
            "value": 0,
            "direction": "higher_is_better",
        },
        "secondary_metrics": {"qa_checks": 80},
        "evidence": {"qa_checks": "measured", "quality": "measured"},
        "kept": True,
        "summary": "baseline",
    }


class PromotePatternsTests(unittest.TestCase):
    def test_build_memory_candidates_uses_prevention_rules(self) -> None:
        entries = [
            make_entry(
                task_id="memory-one",
                iteration=1,
                summary="Captured a reusable workflow lesson",
                changes=["tools/log_iteration.py"],
                hard_gates={"qa_verify": "pass"},
                memory={
                    "mistakes": ["Forgot to validate the ledger after appending entries."],
                    "fixes": ["Ran the ledger validator as part of the normal keep flow."],
                    "prevention_rules": ["Always validate the ledger after appending iteration logs."],
                },
            ),
            make_entry(
                task_id="memory-two",
                iteration=1,
                summary="Repeated the same durable rule in another task",
                changes=["tools/validate_ledger.py"],
                hard_gates={"qa_verify": "pass"},
                memory={
                    "mistakes": ["Forgot to validate the ledger after appending entries."],
                    "fixes": ["Kept validation attached to the logging flow."],
                    "prevention_rules": ["Always validate the ledger after appending iteration logs."],
                },
            ),
        ]

        candidates = build_memory_candidates(entries, min_support=2)

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.source, "ledger_memory")
        self.assertEqual(candidate.source_kind, "prevention_rule")
        self.assertEqual(candidate.support, 2)
        self.assertIn("always validate the ledger after appending iteration logs", candidate.title)
        self.assertIn("Associated fixes:", candidate.signal)
        self.assertIn("Mistakes it helps prevent:", candidate.signal)

    def test_dedupe_candidates_skips_existing_pattern_by_key(self) -> None:
        ledger_path = write_ledger(
            [
                make_baseline("gate-one"),
                make_entry(
                    task_id="gate-one",
                    iteration=1,
                    summary="qa_verify stayed green",
                    changes=["README.md"],
                    hard_gates={"qa_verify": "pass"},
                ),
                make_baseline("gate-two"),
                make_entry(
                    task_id="gate-two",
                    iteration=1,
                    summary="qa_verify stayed green again",
                    changes=["README.md"],
                    hard_gates={"qa_verify": "pass"},
                ),
            ]
        )
        patterns_path = write_patterns(
            "\n".join(
                [
                    "# Durable repository patterns",
                    "",
                    "## Pattern: keep `qa_verify` as the universal hard gate",
                    "- Context: every kept task ends with qa_verify.",
                    "- Signal: `qa_verify` remains the universal hard gate.",
                    "- Caveat: pair it with task-specific checks.",
                    "",
                    "## Pattern: verify README changes on GitHub when Mermaid or positioning changes are involved",
                    "- Context: README work often includes GitHub rendering changes.",
                    "- Signal: kept README iterations paired local QA with a live GitHub README check.",
                    "- Caveat: most important for README and diagram edits.",
                    "",
                ]
            )
        )

        promotable, skipped = dedupe_candidates(
            build_recognition_candidates(ledger_path, min_support=2),
            existing=existing_fingerprints(patterns_path),
            limit=10,
        )

        self.assertEqual(promotable, [])
        self.assertTrue(any("qa_verify" in candidate.reason for candidate in skipped))

    def test_cli_apply_appends_only_new_patterns(self) -> None:
        ledger_path = write_ledger(
            [
                make_baseline("demo-gate-one"),
                make_entry(
                    task_id="demo-gate-one",
                    iteration=1,
                    summary="qa_verify stayed green",
                    changes=["README.md"],
                    hard_gates={"qa_verify": "pass"},
                    memory={
                        "mistakes": ["Forgot to validate the ledger after appending entries."],
                        "fixes": ["Ran the validator immediately after logging the iteration."],
                        "prevention_rules": ["Always validate the ledger after appending iteration logs."],
                    },
                ),
                make_baseline("demo-gate-two"),
                make_entry(
                    task_id="demo-gate-two",
                    iteration=1,
                    summary="qa_verify stayed green again",
                    changes=["README.md"],
                    hard_gates={"qa_verify": "pass"},
                    memory={
                        "mistakes": ["Forgot to validate the ledger after appending entries."],
                        "fixes": ["Kept validation attached to the logging flow."],
                        "prevention_rules": ["Always validate the ledger after appending iteration logs."],
                    },
                ),
            ]
        )
        patterns_path = write_patterns(
            "\n".join(
                [
                    "# Durable repository patterns",
                    "",
                    "## Pattern: keep `qa_verify` as the universal hard gate",
                    "- Context: every kept task ends with qa_verify.",
                    "- Signal: `qa_verify` remains the universal hard gate.",
                    "- Caveat: pair it with task-specific checks.",
                    "",
                    "## Pattern: verify README changes on GitHub when Mermaid or positioning changes are involved",
                    "- Context: README work often includes GitHub rendering changes.",
                    "- Signal: kept README iterations paired local QA with a live GitHub README check.",
                    "- Caveat: most important for README and diagram edits.",
                    "",
                ]
            )
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "promote_patterns.py"),
                "--ledger",
                str(ledger_path),
                "--patterns",
                str(patterns_path),
                "--apply",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["applied_patterns"], ["always validate the ledger after appending iteration logs"])
        updated_patterns = patterns_path.read_text(encoding="utf-8")
        self.assertEqual(updated_patterns.count("## Pattern: keep `qa_verify` as the universal hard gate"), 1)
        self.assertIn("## Pattern: always validate the ledger after appending iteration logs", updated_patterns)


if __name__ == "__main__":
    unittest.main()
