from __future__ import annotations

import argparse
from pathlib import Path


TASK_TYPES = (
    "bugfix",
    "feature",
    "frontend",
    "backend",
    "perf",
    "refactor",
    "ml",
    "infra",
    "data",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold improvement/current-task.md for the swe-self-improve workflow.",
    )
    parser.add_argument("--task-id", required=True, help="Unique task id such as 2026-03-20-demo-task.")
    parser.add_argument("--task-name", required=True, help="Human-readable task name.")
    parser.add_argument("--task-type", choices=TASK_TYPES, required=True, help="Task category.")
    parser.add_argument("--desired-outcome", required=True, help="Main intended result.")
    parser.add_argument("--non-goal", action="append", default=[], help="Non-goal bullet. Repeat as needed.")
    parser.add_argument("--plan-step", action="append", default=[], help="Execution-plan step. Repeat as needed.")
    parser.add_argument("--constraint", action="append", default=[], help="Constraint bullet. Repeat as needed.")
    parser.add_argument("--fast-eval", action="append", default=[], help="Fast-loop eval bullet. Repeat as needed.")
    parser.add_argument("--full-gate", action="append", default=[], help="Full-gate bullet. Repeat as needed.")
    parser.add_argument("--primary-metric-name", default="<metric name>", help="Primary metric name.")
    parser.add_argument(
        "--primary-metric-direction",
        default="higher_is_better",
        choices=("lower_is_better", "higher_is_better", "pass_fail"),
        help="Primary metric direction.",
    )
    parser.add_argument("--primary-metric-baseline", default="<measure baseline>", help="Primary metric baseline.")
    parser.add_argument("--primary-metric-target", default="<set target>", help="Primary metric target.")
    parser.add_argument("--secondary-metric", action="append", default=[], help="Secondary metric bullet.")
    parser.add_argument(
        "--evaluation-command",
        action="append",
        default=[],
        help="Evaluation command to include in the bash block. Repeat as needed.",
    )
    parser.add_argument("--measurement-note", action="append", default=[], help="Measurement-note bullet.")
    parser.add_argument("--max-iterations", default="<set max iterations>", help="Iteration budget.")
    parser.add_argument("--max-task-time", default="<set max task time>", help="Task time budget.")
    parser.add_argument("--rollback-step", action="append", default=[], help="Rollback strategy bullet.")
    parser.add_argument("--stop-condition", action="append", default=[], help="Stop-condition bullet.")
    parser.add_argument("--area", action="append", default=[], help="Optional area-coverage bullet.")
    parser.add_argument("--run-budget", action="append", default=[], help="Optional run-budget bullet.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("improvement/current-task.md"),
        help="Path to write. Defaults to improvement/current-task.md.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing output file.")
    return parser.parse_args()


def bullet_lines(items: list[str], placeholder: str) -> list[str]:
    cleaned = [item.strip() for item in items if item.strip()]
    if cleaned:
        return [f"- {item}" for item in cleaned]
    return [f"- {placeholder}"]


def command_lines(commands: list[str], fast_evals: list[str], full_gates: list[str]) -> list[str]:
    cleaned = [command.strip() for command in commands if command.strip()]
    if not cleaned:
        merged: list[str] = []
        for command in [*fast_evals, *full_gates]:
            stripped = command.strip()
            if stripped and stripped not in merged:
                merged.append(stripped)
        cleaned = merged
    if not cleaned:
        return ["# add evaluation commands here"]
    return cleaned


def render_task_contract(args: argparse.Namespace) -> str:
    lines = [
        "# Current task",
        "",
        f"- Task ID: {args.task_id}",
        f"- Task name: {args.task_name}",
        f"- Task type: {args.task_type}",
        f"- Desired outcome: {args.desired_outcome}",
        "- Non-goals:",
    ]
    lines.extend(bullet_lines(args.non_goal, "<non-goal>"))
    lines.extend(
        [
            "",
            "## Execution plan",
        ]
    )
    lines.extend(bullet_lines(args.plan_step, "<3-7 short ordered steps>"))
    lines.extend(
        [
            "",
            "## Optional: Area coverage plan",
        ]
    )
    lines.extend(bullet_lines(args.area, "<root docs / skills / tools / qa / improvement / templates / other areas>"))
    lines.extend(
        [
            "",
            "## Optional: Run budget allocation",
        ]
    )
    lines.extend(bullet_lines(args.run_budget, "<area>: <planned runs>"))
    lines.extend(
        [
            "",
            "## Constraints",
        ]
    )
    lines.extend(bullet_lines(args.constraint, "<constraint>"))
    lines.extend(
        [
            "",
            "## Memory refresh",
            "- Working memory: improvement/current-task.md",
            "- Episodic memory: improvement/ledger.jsonl",
            "- Learned memory: improvement/patterns.md",
            "- Procedural memory: AGENTS.md / CLAUDE.md / SKILL.md",
            "- Refresh command: <tools/memory_context.py command if the repo ships one>",
            "- Mistakes to avoid: <fill after reviewing prior runs>",
            "- Reusable fixes: <fill after reviewing prior runs>",
        ]
    )
    lines.extend(
        [
            "",
            "## Fast-loop evals",
        ]
    )
    lines.extend(bullet_lines(args.fast_eval, "<cheap checks run each iteration>"))
    lines.extend(
        [
            "",
            "## Full gates",
        ]
    )
    lines.extend(bullet_lines(args.full_gate, "<broader checks required before final keep>"))
    lines.extend(
        [
            "",
            "## Primary metric",
            f"- Name: {args.primary_metric_name}",
            f"- Direction: {args.primary_metric_direction}",
            f"- Baseline: {args.primary_metric_baseline}",
            f"- Target: {args.primary_metric_target}",
            "",
            "## Secondary metrics",
        ]
    )
    lines.extend(bullet_lines(args.secondary_metric, "<metric>: <guardrail>"))
    lines.extend(
        [
            "",
            "## Evaluation commands",
            "```bash",
        ]
    )
    lines.extend(command_lines(args.evaluation_command, args.fast_eval, args.full_gate))
    lines.extend(
        [
            "```",
            "",
            "## Measurement notes",
        ]
    )
    lines.extend(
        bullet_lines(
            args.measurement_note,
            "deterministic or noisy: <note>",
        )
    )
    lines.extend(
        [
            "",
            "## Iteration budget",
            f"- Max iterations: {args.max_iterations}",
            f"- Max task time: {args.max_task_time}",
            "",
            "## Rollback / checkpoint strategy",
        ]
    )
    lines.extend(bullet_lines(args.rollback_step, "<rollback step>"))
    lines.extend(
        [
            "",
            "## Stop conditions",
        ]
    )
    lines.extend(bullet_lines(args.stop_condition, "<stop condition>"))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    output = args.output
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Refusing to overwrite existing file without --overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_task_contract(args), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
