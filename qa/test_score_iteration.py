from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.score_iteration import SecondaryRule, build_score_report, find_entry, find_reference_entry, load_ledger_entries


ROOT = Path(__file__).resolve().parents[1]


def entry(
    *,
    iteration: int,
    kept: bool,
    primary_value: int,
    hard_gates: dict[str, str] | None = None,
    secondary_metrics: dict[str, object] | None = None,
    changes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "task_id": "demo-task",
        "iteration": iteration,
        "eval_tier": "fast+full",
        "hypothesis": f"iteration {iteration}",
        "changes": changes if changes is not None else [],
        "hard_gates": hard_gates if hard_gates is not None else {"qa_verify": "pass"},
        "primary_metric": {
            "name": "quality",
            "baseline": 0,
            "value": primary_value,
            "direction": "higher_is_better",
        },
        "secondary_metrics": secondary_metrics if secondary_metrics is not None else {"qa_checks": 80},
        "evidence": {"quality": "measured"},
        "kept": kept,
        "summary": f"iteration {iteration}",
    }


def write_ledger(entries: list[dict[str, object]]) -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "ledger.jsonl"
    path.write_text(
        "\n".join(json.dumps(item, separators=(",", ":")) for item in entries) + "\n",
        encoding="utf-8",
    )
    return path


class ScoreIterationTests(unittest.TestCase):
    def test_primary_improvement_keeps_candidate(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=0, secondary_metrics={"qa_checks": 80}, changes=[]),
                entry(iteration=1, kept=False, primary_value=1, secondary_metrics={"qa_checks": 81}, changes=["README.md", "AGENTS.md"]),
            ]
        )

        entries = load_ledger_entries(ledger)
        report = build_score_report(
            find_entry(entries, task_id="demo-task", iteration=0),
            find_entry(entries, task_id="demo-task", iteration=1),
            task_id="demo-task",
            secondary_rules=[SecondaryRule(name="qa_checks", direction="higher_is_better", allowed_regression=0.0)],
            primary_neutral_threshold=0.0,
            simplicity_proxy="change_count",
        )

        self.assertEqual(report["recommendation"], "keep")

    def test_hard_gate_failure_rejects_candidate(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=0),
                entry(iteration=1, kept=False, primary_value=1, hard_gates={"qa_verify": "fail"}),
            ]
        )

        entries = load_ledger_entries(ledger)
        report = build_score_report(
            find_entry(entries, task_id="demo-task", iteration=0),
            find_entry(entries, task_id="demo-task", iteration=1),
            task_id="demo-task",
            secondary_rules=[],
            primary_neutral_threshold=0.0,
            simplicity_proxy="change_count",
        )

        self.assertEqual(report["recommendation"], "reject")
        self.assertEqual(report["hard_gates"]["status"], "fail")

    def test_secondary_regression_rejects_candidate(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=1, secondary_metrics={"bundle_kb": 100}, changes=["README.md"]),
                entry(iteration=1, kept=False, primary_value=2, secondary_metrics={"bundle_kb": 110}, changes=["README.md", "CLAUDE.md"]),
            ]
        )

        entries = load_ledger_entries(ledger)
        report = build_score_report(
            find_entry(entries, task_id="demo-task", iteration=0),
            find_entry(entries, task_id="demo-task", iteration=1),
            task_id="demo-task",
            secondary_rules=[SecondaryRule(name="bundle_kb", direction="lower_is_better", allowed_regression=5.0)],
            primary_neutral_threshold=0.0,
            simplicity_proxy="change_count",
        )

        self.assertEqual(report["recommendation"], "reject")
        self.assertEqual(report["secondary_metrics"]["overall_status"], "regressed")

    def test_neutral_primary_and_simpler_candidate_keeps(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=1, changes=["README.md", "AGENTS.md"]),
                entry(iteration=1, kept=False, primary_value=1, changes=["README.md"]),
            ]
        )

        entries = load_ledger_entries(ledger)
        report = build_score_report(
            find_entry(entries, task_id="demo-task", iteration=0),
            find_entry(entries, task_id="demo-task", iteration=1),
            task_id="demo-task",
            secondary_rules=[],
            primary_neutral_threshold=0.0,
            simplicity_proxy="change_count",
        )

        self.assertEqual(report["recommendation"], "keep")
        self.assertEqual(report["simplicity"]["status"], "simpler")

    def test_reference_iteration_defaults_to_latest_kept_lower_iteration(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=0),
                entry(iteration=1, kept=False, primary_value=0),
                entry(iteration=2, kept=True, primary_value=1),
                entry(iteration=3, kept=False, primary_value=2),
            ]
        )

        entries = load_ledger_entries(ledger)
        reference = find_reference_entry(entries, task_id="demo-task", candidate_iteration=3, reference_iteration=None)

        self.assertEqual(reference["iteration"], 2)

    def test_cli_outputs_summary(self) -> None:
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, primary_value=0, secondary_metrics={"qa_checks": 80}),
                entry(iteration=1, kept=False, primary_value=1, secondary_metrics={"qa_checks": 82}),
            ]
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "score_iteration.py"),
                "--ledger",
                str(ledger),
                "--task-id",
                "demo-task",
                "--candidate-iteration",
                "1",
                "--reference-iteration",
                "0",
                "--secondary-rule",
                "qa_checks=higher_is_better@0",
                "--format",
                "summary",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Iteration Score Report", result.stdout)
        self.assertIn("Recommendation: keep", result.stdout)


if __name__ == "__main__":
    unittest.main()
