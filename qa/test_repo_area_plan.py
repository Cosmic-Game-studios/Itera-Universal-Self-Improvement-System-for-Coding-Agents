from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repo_area_plan import build_area_plans, render_json


ROOT = Path(__file__).resolve().parents[1]


def create_repo(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel_path, content in files.items():
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


class RepoAreaPlanTests(unittest.TestCase):
    def test_build_area_plans_allocates_entire_budget_and_ignores_cache(self) -> None:
        root = create_repo(
            {
                "README.md": "# Demo\n",
                "AGENTS.md": "demo\n",
                ".agents/skills/demo/SKILL.md": "demo\n",
                ".claude/skills/demo/SKILL.md": "demo\n",
                "qa/check.py": "print('ok')\n",
                "tools/helper.py": "print('ok')\n",
                "improvement/current-task.md": "# task\n",
                "global-templates/codex-home-AGENTS.md": "demo\n",
                "qa/__pycache__/ignored.pyc": "x",
            }
        )

        plans = build_area_plans(root, 600)

        self.assertEqual(sum(plan.suggested_runs for plan in plans), 600)
        self.assertTrue(all("__pycache__" not in path for plan in plans for path in plan.notable_files))
        self.assertIn("[root]", {plan.area for plan in plans})
        self.assertIn(".agents/", {plan.area for plan in plans})

    def test_render_json_reports_budget_and_area_details(self) -> None:
        root = create_repo(
            {
                "README.md": "# Demo\n",
                "tools/helper.py": "print('ok')\n",
            }
        )

        payload = json.loads(render_json(root, 42, build_area_plans(root, 42)))

        self.assertEqual(payload["budget"], 42)
        self.assertEqual(sum(area["suggested_runs"] for area in payload["areas"]), 42)
        self.assertTrue(any(area["area"] == "tools/" for area in payload["areas"]))

    def test_cli_outputs_markdown_report(self) -> None:
        root = create_repo(
            {
                "README.md": "# Demo\n",
                "tools/helper.py": "print('ok')\n",
                "qa/check.py": "print('ok')\n",
            }
        )

        result = subprocess.run(
            [
                "python3",
                str(ROOT / "tools" / "repo_area_plan.py"),
                "--root",
                str(root),
                "--budget",
                "120",
                "--format",
                "markdown",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Repo Area Plan", result.stdout)
        self.assertIn("Suggested runs", result.stdout)
        self.assertIn("Area:", result.stdout)


if __name__ == "__main__":
    unittest.main()
