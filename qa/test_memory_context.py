from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.memory_context import build_memory_brief, load_ledger_entries, load_task_contract, parse_patterns


ROOT = Path(__file__).resolve().parents[1]


def write_task() -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "current-task.md"
    path.write_text(
        "\n".join(
            [
                "# Current task",
                "",
                "- Task ID: current-task",
                "- Task name: Improve frontend drawer workflow",
                "- Task type: frontend",
                "- Desired outcome: Reduce regressions in drawer behavior and accessibility.",
                "- Non-goals:",
                "- Rewrite the whole page shell.",
                "",
                "## Execution plan",
                "- Review prior drawer regressions.",
                "- Tighten keyboard and focus behavior.",
                "",
                "## Constraints",
                "- Keep the change small.",
                "",
                "## Memory refresh",
                "- Working memory: improvement/current-task.md",
                "- Episodic memory: improvement/ledger.jsonl",
                "- Learned memory: improvement/patterns.md",
                "- Procedural memory: AGENTS.md / CLAUDE.md / SKILL.md",
                "- Refresh command: python3 tools/memory_context.py --format summary",
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
                "- Target: 1",
                "",
                "## Secondary metrics",
                "- a11y: no regression",
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
                "- Max iterations: 2",
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


def write_ledger() -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "ledger.jsonl"
    entries = [
        {
            "task_id": "current-task",
            "iteration": 0,
            "eval_tier": "fast+full",
            "hypothesis": "baseline",
            "changes": [],
            "hard_gates": {"qa_verify": "pass"},
            "primary_metric": {"name": "quality", "baseline": 0, "value": 0, "direction": "higher_is_better"},
            "secondary_metrics": {"qa_checks": 1},
            "evidence": {"quality": "measured"},
            "kept": True,
            "summary": "Baseline entry.",
        },
        {
            "task_id": "drawer-focus-fix",
            "iteration": 0,
            "eval_tier": "fast+full",
            "hypothesis": "baseline",
            "changes": [],
            "hard_gates": {"qa_verify": "pass"},
            "primary_metric": {"name": "quality", "baseline": 0, "value": 0, "direction": "higher_is_better"},
            "secondary_metrics": {"qa_checks": 1},
            "evidence": {"quality": "measured"},
            "kept": True,
            "summary": "Baseline entry.",
        },
        {
            "task_id": "drawer-focus-fix",
            "iteration": 1,
            "eval_tier": "fast+full",
            "hypothesis": "Add a focus trap to the drawer",
            "changes": ["src/drawer.ts"],
            "hard_gates": {"qa_verify": "pass"},
            "primary_metric": {"name": "quality", "baseline": 0, "value": 1, "direction": "higher_is_better"},
            "secondary_metrics": {"qa_checks": 2},
            "evidence": {"quality": "measured"},
            "memory": {
                "mistakes": ["Skipped keyboard navigation coverage in an earlier draft."],
                "fixes": ["Added focus-trap coverage before keeping the drawer change."],
                "prevention_rules": ["Test focus and escape-key behavior before keeping drawer changes."],
            },
            "kept": True,
            "summary": "Improved the drawer without breaking accessibility.",
        },
    ]
    path.write_text(
        "\n".join(json.dumps(item, separators=(",", ":")) for item in entries) + "\n",
        encoding="utf-8",
    )
    return path


def write_patterns() -> Path:
    root = Path(tempfile.mkdtemp())
    path = root / "patterns.md"
    path.write_text(
        "\n".join(
            [
                "# Durable repository patterns",
                "",
                "## Pattern: test focus behavior early for drawer work",
                "- Context: drawer and modal work tends to regress keyboard focus handling.",
                "- Signal: past kept fixes were safer when focus and escape-key behavior were tested before broader polish.",
                "- Caveat: only relevant when the UI change actually manipulates focus or overlay state.",
                "",
                "## Pattern: keep qa_verify as a universal gate",
                "- Context: the repository uses a structural QA check on every kept task.",
                "- Signal: the QA check stayed green across successful tasks.",
                "- Caveat: it does not replace task-specific tests.",
            ]
        ),
        encoding="utf-8",
    )
    return path


class MemoryContextTests(unittest.TestCase):
    def test_memory_brief_surfaces_related_mistakes_and_patterns(self) -> None:
        task = write_task()
        ledger = write_ledger()
        patterns = write_patterns()

        brief = build_memory_brief(
            load_task_contract(task),
            load_ledger_entries(ledger),
            parse_patterns(patterns),
            task_id="current-task",
            related_limit=3,
            pattern_limit=3,
            root=ROOT,
        )

        episodic = brief["episodic_memory"]
        self.assertIn(
            "Skipped keyboard navigation coverage in an earlier draft.",
            episodic["mistakes_to_avoid"],
        )
        self.assertIn(
            "Test focus and escape-key behavior before keeping drawer changes.",
            episodic["prevention_rules"],
        )
        titles = [pattern["title"] for pattern in brief["learned_memory"]["patterns"]]
        self.assertIn("test focus behavior early for drawer work", titles)

    def test_cli_summary_renders_memory_brief(self) -> None:
        task = write_task()
        ledger = write_ledger()
        patterns = write_patterns()

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "memory_context.py"),
                "--task",
                str(task),
                "--ledger",
                str(ledger),
                "--patterns",
                str(patterns),
                "--format",
                "summary",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Memory Brief", result.stdout)
        self.assertIn("Mistake to avoid: Skipped keyboard navigation coverage in an earlier draft.", result.stdout)
        self.assertIn("Pattern: test focus behavior early for drawer work", result.stdout)


if __name__ == "__main__":
    unittest.main()
