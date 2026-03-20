from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from tools.validate_ledger import validate_ledger
except ImportError:
    from validate_ledger import validate_ledger  # type: ignore[no-redef]


TASK_ID_RE = re.compile(r"^- Task ID:\s*(.+?)\s*$", re.M)
TASK_NAME_RE = re.compile(r"^- Task name:\s*(.+?)\s*$", re.M)
TASK_TYPE_RE = re.compile(r"^- Task type:\s*(.+?)\s*$", re.M)
MAX_ITERATIONS_RE = re.compile(r"^- Max iterations:\s*(.+?)\s*$", re.M)


@dataclass(frozen=True)
class TaskContext:
    task_id: str | None
    task_name: str | None
    task_type: str | None
    max_iterations: int | None
    path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the current self-improvement loop state from current-task.md and ledger history.",
    )
    parser.add_argument(
        "--task",
        type=Path,
        default=Path("improvement/current-task.md"),
        help="Path to current-task.md.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("improvement/ledger.jsonl"),
        help="Path to the ledger JSONL file.",
    )
    parser.add_argument(
        "--task-id",
        help="Override the task id instead of reading it from current-task.md.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    return parser.parse_args()


def extract_line(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def parse_max_iterations(raw: str | None) -> int | None:
    if raw is None:
        return None
    stripped = raw.strip()
    if stripped.isdigit():
        return int(stripped)
    return None


def load_task_context(path: Path) -> TaskContext:
    text = path.read_text(encoding="utf-8")
    return TaskContext(
        task_id=extract_line(TASK_ID_RE, text),
        task_name=extract_line(TASK_NAME_RE, text),
        task_type=extract_line(TASK_TYPE_RE, text),
        max_iterations=parse_max_iterations(extract_line(MAX_ITERATIONS_RE, text)),
        path=path,
    )


def load_ledger_entries(path: Path) -> list[dict[str, Any]]:
    report = validate_ledger(path)
    if not report.valid:
        raise ValueError("Ledger must be valid before loop state can be summarized.")
    entries: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def safe_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def scalar_metric_value(value: Any) -> float | str | bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return value
    return None


def metric_trend(entries: list[dict[str, Any]]) -> tuple[str, list[str], dict[str, Any]]:
    kept_entries = [entry for entry in entries if entry.get("kept") is True]
    if len(kept_entries) < 2:
        return "insufficient_history", ["Not enough kept history to compare metrics yet."], {}

    previous = kept_entries[-2].get("primary_metric", {})
    current = kept_entries[-1].get("primary_metric", {})
    if not isinstance(previous, dict) or not isinstance(current, dict):
        return "unknown", ["Primary metric payload is missing or malformed."], {}

    prev_name = previous.get("name")
    curr_name = current.get("name")
    if prev_name != curr_name:
        return "metric_changed", ["Primary metric name changed between kept iterations."], {}

    direction = current.get("direction")
    prev_value = scalar_metric_value(previous.get("value"))
    curr_value = scalar_metric_value(current.get("value"))
    details = {
        "name": curr_name,
        "direction": direction,
        "previous_value": prev_value,
        "current_value": curr_value,
    }

    if direction in {"higher_is_better", "lower_is_better"} and isinstance(prev_value, float) and isinstance(curr_value, float):
        if curr_value == prev_value:
            return "flat", ["Primary metric stayed flat across the two most recent kept iterations."], details
        if direction == "higher_is_better":
            if curr_value > prev_value:
                return "improving", ["Primary metric improved in the latest kept iteration."], details
            return "worse", ["Primary metric is worse than in the previous kept iteration."], details
        if curr_value < prev_value:
            return "improving", ["Primary metric improved in the latest kept iteration."], details
        return "worse", ["Primary metric is worse than in the previous kept iteration."], details

    if curr_value == prev_value:
        return "flat", ["Primary metric value did not change across the two most recent kept iterations."], details
    return "changed_non_numeric", ["Primary metric changed, but not in a numeric form that can be ordered automatically."], details


def recommendation_for_state(
    *,
    baseline_present: bool,
    budget_exhausted: bool,
    recent_failed_iterations: int,
    trend: str,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not baseline_present:
        reasons.append("Baseline iteration 0 is missing for this task.")
        return "needs_baseline", reasons

    if budget_exhausted:
        reasons.append("The configured iteration budget is exhausted.")
        return "stop_budget_exhausted", reasons

    if recent_failed_iterations >= 2:
        reasons.append("Two or more recent non-baseline iterations were discarded or failed to keep.")
        return "replan_before_next_iteration", reasons

    if trend == "flat":
        reasons.append("Recent kept iterations look flat on the primary metric.")
        return "consider_stop_if_no_new_hypothesis", reasons

    if trend == "worse":
        reasons.append("The most recent kept metric looks worse than the previous kept state.")
        return "review_before_continue", reasons

    reasons.append("Baseline exists, budget remains, and no immediate stop signal is present.")
    return "continue", reasons


def build_loop_state(task: TaskContext, ledger_entries: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    entries = sorted(
        [entry for entry in ledger_entries if entry.get("task_id") == task_id],
        key=lambda entry: safe_int(entry.get("iteration")) or -1,
    )
    baseline_present = any(entry.get("iteration") == 0 for entry in entries)
    non_baseline_entries = [entry for entry in entries if safe_int(entry.get("iteration")) not in (None, 0)]
    last_entry = entries[-1] if entries else None
    last_iteration = safe_int(last_entry.get("iteration")) if isinstance(last_entry, dict) else None
    next_iteration = 0 if last_iteration is None else last_iteration + 1
    used_iterations = len(non_baseline_entries)
    remaining_iterations = None
    budget_exhausted = False
    if task.max_iterations is not None:
        remaining_iterations = max(task.max_iterations - used_iterations, 0)
        budget_exhausted = remaining_iterations == 0

    recent_failed_iterations = 0
    for entry in reversed(non_baseline_entries):
        if entry.get("kept") is False:
            recent_failed_iterations += 1
            continue
        break

    trend, trend_reasons, metric_details = metric_trend(entries)
    recommendation, reasons = recommendation_for_state(
        baseline_present=baseline_present,
        budget_exhausted=budget_exhausted,
        recent_failed_iterations=recent_failed_iterations,
        trend=trend,
    )
    reasons = [*reasons, *trend_reasons]

    return {
        "task_id": task_id,
        "task_name": task.task_name,
        "task_type": task.task_type,
        "task_path": str(task.path),
        "entry_count": len(entries),
        "baseline_present": baseline_present,
        "next_iteration": next_iteration,
        "max_iterations": task.max_iterations,
        "used_iterations": used_iterations,
        "remaining_iterations": remaining_iterations,
        "budget_exhausted": budget_exhausted,
        "recent_failed_iterations": recent_failed_iterations,
        "last_entry": {
            "iteration": last_iteration,
            "kept": last_entry.get("kept") if isinstance(last_entry, dict) else None,
            "summary": last_entry.get("summary") if isinstance(last_entry, dict) else None,
        },
        "primary_metric_trend": trend,
        "primary_metric_details": metric_details,
        "recommendation": recommendation,
        "reasons": reasons,
    }


def render_summary(state: dict[str, Any]) -> str:
    lines = [
        "# Loop State Report",
        "",
        f"- Task ID: {state['task_id']}",
        f"- Task name: {state.get('task_name') or 'unknown'}",
        f"- Task type: {state.get('task_type') or 'unknown'}",
        f"- Recommendation: {state['recommendation']}",
        f"- Baseline present: {'yes' if state['baseline_present'] else 'no'}",
        f"- Entries for task: {state['entry_count']}",
        f"- Next iteration: {state['next_iteration']}",
        f"- Max iterations: {state['max_iterations'] if state['max_iterations'] is not None else 'unknown'}",
        f"- Remaining iterations: {state['remaining_iterations'] if state['remaining_iterations'] is not None else 'unknown'}",
        f"- Recent failed iterations: {state['recent_failed_iterations']}",
        f"- Primary metric trend: {state['primary_metric_trend']}",
        "",
        "## Reasons",
    ]
    for reason in state["reasons"]:
        lines.append(f"- {reason}")
    last_entry = state.get("last_entry", {})
    if isinstance(last_entry, dict) and last_entry.get("iteration") is not None:
        lines.extend(
            [
                "",
                "## Last entry",
                f"- Iteration: {last_entry.get('iteration')}",
                f"- Kept: {last_entry.get('kept')}",
                f"- Summary: {last_entry.get('summary') or ''}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        task = load_task_context(args.task)
        task_id = args.task_id or task.task_id
        if not task_id:
            raise ValueError("Could not determine task id. Provide --task-id or add '- Task ID:' to the task file.")
        entries = load_ledger_entries(args.ledger)
        state = build_loop_state(task, entries, task_id)
    except ValueError as exc:
        raise SystemExit(str(exc))
    if args.format == "json":
        print(json.dumps(state, indent=2, sort_keys=True))
    else:
        print(render_summary(state), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
