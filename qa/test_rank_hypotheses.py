from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.rank_hypotheses import determine_mode, load_backlog, rank_hypotheses, task_keywords


ROOT = Path(__file__).resolve().parents[1]


def write_backlog(payload: object) -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "backlog.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_task(task_id: str, *, max_iterations: int = 3) -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "current-task.md"
    path.write_text(
        "\n".join(
            [
                "# Current task",
                "",
                f"- Task ID: {task_id}",
                "- Task name: Improve hypothesis ranking",
                "- Task type: feature",
                "- Desired outcome: Choose the next hypothesis more intelligently.",
                "- Non-goals:",
                "- none",
                "",
                "## Execution plan",
                "- baseline",
                "- implement",
                "",
                "## Constraints",
                "- standard library only",
                "",
                "## Memory refresh",
                "- Working memory: improvement/current-task.md",
                "",
                "## Fast-loop evals",
                "- tests",
                "",
                "## Full gates",
                "- qa",
                "",
                "## Primary metric",
                "- Name: ranking",
                "- Direction: higher_is_better",
                "- Baseline: 0",
                "- Target: 1",
                "",
                "## Secondary metrics",
                "- qa green",
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
                "- Max task time: short",
                "",
                "## Rollback / checkpoint strategy",
                "- revert",
                "",
                "## Stop conditions",
                "- done",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def write_ledger(entries: list[dict]) -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "ledger.jsonl"
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")
    return path


def ledger_entry(*, task_id: str, iteration: int, value: int, kept: bool = True) -> dict:
    return {
        "task_id": task_id,
        "iteration": iteration,
        "eval_tier": "fast+full",
        "hypothesis": f"iteration-{iteration}",
        "changes": [],
        "hard_gates": {"qa_verify": "pass"},
        "primary_metric": {
            "name": "ranking_quality",
            "baseline": 0,
            "value": value,
            "direction": "higher_is_better",
        },
        "secondary_metrics": {"qa_checks": 80 + iteration},
        "evidence": {"ranking_quality": "measured", "qa_checks": "measured"},
        "kept": kept,
        "summary": "entry",
    }


class RankHypothesesTests(unittest.TestCase):
    def test_load_backlog_rejects_invalid_field_range(self) -> None:
        backlog = write_backlog(
            {
                "hypotheses": [
                    {
                        "id": "bad-risk",
                        "summary": "Bad backlog entry",
                        "kind": "exploit",
                        "expected_upside": 5,
                        "implementation_cost": 1,
                        "risk": 8,
                        "confidence": 4,
                        "reversibility": 4,
                        "evidence": "measured",
                        "notes": "",
                        "related_patterns": [],
                        "related_prevention_rules": [],
                        "blocked_by": [],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "between 0 and 5"):
            load_backlog(backlog)

    def test_auto_mode_uses_plateau_escape_when_metric_is_flat(self) -> None:
        task = write_task("demo-flat")
        ledger = write_ledger(
            [
                ledger_entry(task_id="demo-flat", iteration=0, value=0),
                ledger_entry(task_id="demo-flat", iteration=1, value=0),
            ]
        )

        mode, reasons, state = determine_mode("auto", task_path=task, ledger_path=ledger, task_id_override=None)

        self.assertEqual(mode, "plateau_escape")
        self.assertIsNotNone(state)
        self.assertEqual(state["primary_metric_trend"], "flat")
        self.assertTrue(any("plateau" in reason.lower() for reason in reasons))

    def test_rank_hypotheses_changes_order_by_mode(self) -> None:
        backlog = write_backlog(
            {
                "hypotheses": [
                    {
                        "id": "tighten-known-guardrail",
                        "summary": "Tighten a known guardrail around the next hypothesis selection.",
                        "kind": "exploit",
                        "expected_upside": 4,
                        "implementation_cost": 2,
                        "risk": 1,
                        "confidence": 3,
                        "reversibility": 4,
                        "evidence": "measured",
                        "notes": "Grounded in existing workflow behavior.",
                        "related_patterns": [],
                        "related_prevention_rules": [],
                        "blocked_by": [],
                    },
                    {
                        "id": "plateau-escape-probe",
                        "summary": "Probe a more exploratory next hypothesis when the loop goes flat.",
                        "kind": "explore",
                        "expected_upside": 4,
                        "implementation_cost": 1,
                        "risk": 1,
                        "confidence": 3,
                        "reversibility": 4,
                        "evidence": "inferred",
                        "notes": "Useful for plateau escape.",
                        "related_patterns": [],
                        "related_prevention_rules": [],
                        "blocked_by": [],
                    },
                ]
            }
        )
        task = write_task("demo-mode")
        hypotheses = load_backlog(backlog)
        keywords = task_keywords(task)

        exploit_ranked = rank_hypotheses(hypotheses, mode="exploit", task_keyword_set=keywords, limit=5)
        plateau_ranked = rank_hypotheses(hypotheses, mode="plateau_escape", task_keyword_set=keywords, limit=5)

        self.assertEqual(exploit_ranked[0]["hypothesis"]["id"], "tighten-known-guardrail")
        self.assertEqual(plateau_ranked[0]["hypothesis"]["id"], "plateau-escape-probe")

    def test_cli_outputs_selected_mode_and_recommendation(self) -> None:
        backlog = write_backlog(
            {
                "hypotheses": [
                    {
                        "id": "repair-loop",
                        "summary": "Stabilize the loop after repeated failed iterations.",
                        "kind": "stabilize",
                        "expected_upside": 4,
                        "implementation_cost": 1,
                        "risk": 1,
                        "confidence": 4,
                        "reversibility": 5,
                        "evidence": "measured",
                        "notes": "",
                        "related_patterns": [],
                        "related_prevention_rules": [],
                        "blocked_by": [],
                    }
                ]
            }
        )
        task = write_task("demo-recovery")
        ledger = write_ledger(
            [
                ledger_entry(task_id="demo-recovery", iteration=0, value=0),
                ledger_entry(task_id="demo-recovery", iteration=1, value=1, kept=False),
                ledger_entry(task_id="demo-recovery", iteration=2, value=1, kept=False),
            ]
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "rank_hypotheses.py"),
                "--backlog",
                str(backlog),
                "--task",
                str(task),
                "--ledger",
                str(ledger),
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_mode"], "recovery")
        self.assertEqual(payload["recommended_next_hypothesis"], "repair-loop")


if __name__ == "__main__":
    unittest.main()
