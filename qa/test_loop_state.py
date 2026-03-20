from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.loop_state import build_loop_state, load_ledger_entries, load_task_context


ROOT = Path(__file__).resolve().parents[1]


def write_task_file(*, max_iterations: str) -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "current-task.md"
    path.write_text(
        "\n".join(
            [
                "# Current task",
                "",
                "- Task ID: demo-task",
                "- Task name: Demo task",
                "- Task type: feature",
                "- Desired outcome: Demo outcome",
                "- Non-goals: none",
                "",
                "## Execution plan",
                "- Step 1",
                "",
                "## Constraints",
                "- none",
                "",
                "## Fast-loop evals",
                "- tests",
                "",
                "## Full gates",
                "- tests",
                "",
                "## Primary metric",
                "- Name: quality",
                "- Direction: higher_is_better",
                "- Baseline: 0",
                "- Target: 2",
                "",
                "## Secondary metrics",
                "- qa_checks: green",
                "",
                "## Evaluation commands",
                "```bash",
                "python3 qa/verify_skill_system.py",
                "```",
                "",
                "## Measurement notes",
                "- deterministic or noisy: deterministic",
                "",
                "## Iteration budget",
                f"- Max iterations: {max_iterations}",
                "- Max task time: one pass",
                "",
                "## Rollback / checkpoint strategy",
                "- revert",
                "",
                "## Stop conditions",
                "- stop when done",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def entry(*, iteration: int, kept: bool, value: int) -> dict[str, object]:
    return {
        "task_id": "demo-task",
        "iteration": iteration,
        "eval_tier": "fast+full",
        "hypothesis": f"iteration {iteration}",
        "changes": [],
        "hard_gates": {"qa_verify": "pass"},
        "primary_metric": {
            "name": "quality",
            "baseline": 0,
            "value": value,
            "direction": "higher_is_better",
        },
        "secondary_metrics": {"qa_checks": 80},
        "evidence": {"qa_verify": "measured"},
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


class LoopStateTests(unittest.TestCase):
    def test_loop_state_reports_continue_with_budget_remaining(self) -> None:
        task = write_task_file(max_iterations="3")
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, value=0),
                entry(iteration=1, kept=True, value=1),
            ]
        )

        state = build_loop_state(load_task_context(task), load_ledger_entries(ledger), "demo-task")

        self.assertEqual(state["recommendation"], "continue")
        self.assertEqual(state["next_iteration"], 2)
        self.assertEqual(state["remaining_iterations"], 2)
        self.assertEqual(state["primary_metric_trend"], "improving")

    def test_loop_state_reports_budget_exhausted(self) -> None:
        task = write_task_file(max_iterations="1")
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, value=0),
                entry(iteration=1, kept=True, value=1),
            ]
        )

        state = build_loop_state(load_task_context(task), load_ledger_entries(ledger), "demo-task")

        self.assertEqual(state["recommendation"], "stop_budget_exhausted")
        self.assertTrue(state["budget_exhausted"])
        self.assertEqual(state["remaining_iterations"], 0)

    def test_loop_state_recommends_replan_after_recent_failures(self) -> None:
        task = write_task_file(max_iterations="5")
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, value=0),
                entry(iteration=1, kept=False, value=0),
                entry(iteration=2, kept=False, value=0),
            ]
        )

        state = build_loop_state(load_task_context(task), load_ledger_entries(ledger), "demo-task")

        self.assertEqual(state["recommendation"], "replan_before_next_iteration")
        self.assertEqual(state["recent_failed_iterations"], 2)
        self.assertEqual(state["next_iteration"], 3)

    def test_cli_outputs_summary_report(self) -> None:
        task = write_task_file(max_iterations="3")
        ledger = write_ledger(
            [
                entry(iteration=0, kept=True, value=0),
                entry(iteration=1, kept=True, value=1),
            ]
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "loop_state.py"),
                "--task",
                str(task),
                "--ledger",
                str(ledger),
                "--format",
                "summary",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Loop State Report", result.stdout)
        self.assertIn("Recommendation: continue", result.stdout)
        self.assertIn("Next iteration: 2", result.stdout)


if __name__ == "__main__":
    unittest.main()
