from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STANDARD_DIRECTIONS = {"lower_is_better", "higher_is_better", "pass_fail"}
LEGACY_DIRECTIONS = {"clearer_is_better"}
ACCEPTED_DIRECTIONS = STANDARD_DIRECTIONS | LEGACY_DIRECTIONS
ALLOWED_EVIDENCE_LABELS = {"measured", "inferred", "speculative"}


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"location": self.location, "message": self.message}


@dataclass(frozen=True)
class ValidationReport:
    path: Path
    mode: str
    entry_count: int
    task_count: int
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "mode": self.mode,
            "valid": self.valid,
            "entry_count": self.entry_count,
            "task_count": self.task_count,
            "issue_count": len(self.issues),
            "issues": [issue.as_dict() for issue in self.issues],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the contract used by improvement/ledger.jsonl entries.",
    )
    parser.add_argument("--ledger", type=Path, required=True, help="Path to the ledger file to validate.")
    parser.add_argument(
        "--single-json",
        action="store_true",
        help="Treat the input as one JSON object instead of JSONL.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    return parser.parse_args()


def is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_entries(path: Path, *, single_json: bool) -> tuple[list[tuple[str, dict[str, Any]]], list[ValidationIssue]]:
    text = path.read_text(encoding="utf-8")
    if single_json:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            return [], [ValidationIssue("entry 1", f"invalid JSON: {exc.msg}")]
        if not isinstance(payload, dict):
            return [], [ValidationIssue("entry 1", "single-json input must be a JSON object")]
        return [("entry 1", payload)], []

    entries: list[tuple[str, dict[str, Any]]] = []
    issues: list[ValidationIssue] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        location = f"line {line_number}"
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue(location, f"invalid JSON: {exc.msg}"))
            continue
        if not isinstance(payload, dict):
            issues.append(ValidationIssue(location, "each JSONL record must be a JSON object"))
            continue
        entries.append((location, payload))
    return entries, issues


def require_mapping(payload: dict[str, Any], key: str, location: str, issues: list[ValidationIssue]) -> dict[str, Any] | None:
    value = payload.get(key)
    if not isinstance(value, dict):
        issues.append(ValidationIssue(location, f"'{key}' must be an object"))
        return None
    return value


def validate_entry(location: str, payload: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if not is_non_empty_string(payload.get("task_id")):
        issues.append(ValidationIssue(location, "'task_id' must be a non-empty string"))

    if not is_non_negative_int(payload.get("iteration")):
        issues.append(ValidationIssue(location, "'iteration' must be a non-negative integer"))

    if not is_non_empty_string(payload.get("eval_tier")):
        issues.append(ValidationIssue(location, "'eval_tier' must be a non-empty string"))

    if not is_non_empty_string(payload.get("hypothesis")):
        issues.append(ValidationIssue(location, "'hypothesis' must be a non-empty string"))

    changes = payload.get("changes")
    if not isinstance(changes, list):
        issues.append(ValidationIssue(location, "'changes' must be a list"))
    elif any(not is_non_empty_string(item) for item in changes):
        issues.append(ValidationIssue(location, "'changes' entries must be non-empty strings"))

    hard_gates = require_mapping(payload, "hard_gates", location, issues)
    if hard_gates is not None:
        for gate_name, status in hard_gates.items():
            if not is_non_empty_string(gate_name):
                issues.append(ValidationIssue(location, "'hard_gates' keys must be non-empty strings"))
                break
            if not is_non_empty_string(status):
                issues.append(ValidationIssue(location, "'hard_gates' values must be non-empty strings"))
                break

    primary_metric = require_mapping(payload, "primary_metric", location, issues)
    if primary_metric is not None:
        if not is_non_empty_string(primary_metric.get("name")):
            issues.append(ValidationIssue(location, "'primary_metric.name' must be a non-empty string"))
        if primary_metric.get("direction") not in ACCEPTED_DIRECTIONS:
            issues.append(
                ValidationIssue(
                    location,
                    f"'primary_metric.direction' must be one of {sorted(ACCEPTED_DIRECTIONS)}",
                )
            )
        if "baseline" not in primary_metric or not is_scalar(primary_metric.get("baseline")):
            issues.append(ValidationIssue(location, "'primary_metric.baseline' must be a JSON scalar"))
        if "value" not in primary_metric or not is_scalar(primary_metric.get("value")):
            issues.append(ValidationIssue(location, "'primary_metric.value' must be a JSON scalar"))

    secondary_metrics = payload.get("secondary_metrics")
    if not isinstance(secondary_metrics, dict):
        issues.append(ValidationIssue(location, "'secondary_metrics' must be an object"))

    evidence = require_mapping(payload, "evidence", location, issues)
    if evidence is not None:
        if not evidence:
            issues.append(ValidationIssue(location, "'evidence' must contain at least one claim label"))
        for claim, label in evidence.items():
            if not is_non_empty_string(claim):
                issues.append(ValidationIssue(location, "'evidence' keys must be non-empty strings"))
                break
            if label not in ALLOWED_EVIDENCE_LABELS:
                issues.append(
                    ValidationIssue(
                        location,
                        f"'evidence' labels must be one of {sorted(ALLOWED_EVIDENCE_LABELS)}",
                    )
                )
                break

    if not isinstance(payload.get("kept"), bool):
        issues.append(ValidationIssue(location, "'kept' must be a boolean"))

    if not is_non_empty_string(payload.get("summary")):
        issues.append(ValidationIssue(location, "'summary' must be a non-empty string"))

    return issues


def validate_cross_entry_rules(entries: list[tuple[str, dict[str, Any]]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    iterations_by_task: dict[str, set[int]] = {}
    for location, payload in entries:
        task_id = payload.get("task_id")
        iteration = payload.get("iteration")
        if not is_non_empty_string(task_id) or not is_non_negative_int(iteration):
            continue
        seen_iterations = iterations_by_task.setdefault(task_id.strip(), set())
        if iteration in seen_iterations:
            issues.append(
                ValidationIssue(
                    location,
                    f"task '{task_id}' repeats iteration {iteration}",
                )
            )
        seen_iterations.add(iteration)

    for task_id, iterations in sorted(iterations_by_task.items()):
        if 0 not in iterations:
            issues.append(ValidationIssue(task_id, "task is missing baseline iteration 0"))

    return issues


def validate_ledger(path: Path, *, single_json: bool = False) -> ValidationReport:
    entries, issues = load_entries(path, single_json=single_json)
    for location, payload in entries:
        issues.extend(validate_entry(location, payload))
    if not single_json:
        issues.extend(validate_cross_entry_rules(entries))
    task_ids = {
        str(payload.get("task_id")).strip()
        for _, payload in entries
        if is_non_empty_string(payload.get("task_id"))
    }
    return ValidationReport(
        path=path,
        mode="single-json" if single_json else "jsonl",
        entry_count=len(entries),
        task_count=len(task_ids),
        issues=tuple(issues),
    )


def render_summary(report: ValidationReport) -> str:
    lines = [
        "# Ledger Contract Report",
        "",
        f"- Path: `{report.path}`",
        f"- Mode: {report.mode}",
        f"- Entries: {report.entry_count}",
        f"- Tasks: {report.task_count}",
        f"- Status: {'valid' if report.valid else 'invalid'}",
        f"- Issues: {len(report.issues)}",
    ]
    if report.issues:
        lines.extend(["", "## Issues"])
        for issue in report.issues:
            lines.append(f"- {issue.location}: {issue.message}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = validate_ledger(args.ledger, single_json=args.single_json)
    if args.format == "json":
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        print(render_summary(report), end="")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
