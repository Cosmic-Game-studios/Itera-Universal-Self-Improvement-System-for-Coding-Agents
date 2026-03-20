from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from tools.validate_ledger import ACCEPTED_DIRECTIONS, validate_ledger
except ImportError:
    from validate_ledger import ACCEPTED_DIRECTIONS, validate_ledger  # type: ignore[no-redef]


PASS_LIKE_STATUSES = {"pass", "passed", "green", "ok", "success", "true", "yes"}
FAIL_LIKE_STATUSES = {"fail", "failed", "red", "error", "false", "no"}
RULE_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)=(?P<direction>higher_is_better|lower_is_better|pass_fail)(?:@(?P<budget>.+))?$"
)


@dataclass(frozen=True)
class SecondaryRule:
    name: str
    direction: str
    allowed_regression: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction,
            "allowed_regression": self.allowed_regression,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare one ledger iteration against a reference state using hard gates, the primary metric, explicit secondary rules, and a simplicity tie-break.",
    )
    parser.add_argument("--ledger", type=Path, default=Path("improvement/ledger.jsonl"), help="Path to improvement/ledger.jsonl.")
    parser.add_argument("--task-id", required=True, help="Task id whose entries should be compared.")
    parser.add_argument("--candidate-iteration", type=int, required=True, help="Iteration to score as the candidate.")
    parser.add_argument(
        "--reference-iteration",
        type=int,
        help="Explicit iteration to treat as the reference state. Defaults to the most recent kept lower iteration.",
    )
    parser.add_argument(
        "--secondary-rule",
        action="append",
        default=[],
        help="Secondary guardrail rule as name=direction or name=direction@allowed_regression.",
    )
    parser.add_argument(
        "--primary-neutral-threshold",
        type=float,
        default=0.0,
        help="Absolute numeric threshold below which primary-metric changes count as neutral.",
    )
    parser.add_argument(
        "--simplicity-proxy",
        choices=("change_count", "none"),
        default="change_count",
        help="Proxy used for the final simplicity tie-break.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    return parser.parse_args()


def load_ledger_entries(path: Path) -> list[dict[str, Any]]:
    report = validate_ledger(path)
    if not report.valid:
        raise ValueError("Ledger must be valid before iteration scoring can run.")

    entries: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def parse_secondary_rule(raw: str) -> SecondaryRule:
    match = RULE_RE.fullmatch(raw.strip())
    if not match:
        raise ValueError(f"Invalid secondary rule: {raw}")
    budget_text = match.group("budget")
    allowed_regression = 0.0
    if budget_text is not None:
        try:
            allowed_regression = float(json.loads(budget_text))
        except (json.JSONDecodeError, TypeError):
            try:
                allowed_regression = float(budget_text)
            except ValueError as exc:
                raise ValueError(f"Secondary rule budget must be numeric: {raw}") from exc
    if allowed_regression < 0:
        raise ValueError(f"Secondary rule budget must be non-negative: {raw}")
    return SecondaryRule(
        name=match.group("name"),
        direction=match.group("direction"),
        allowed_regression=allowed_regression,
    )


def find_entry(entries: list[dict[str, Any]], *, task_id: str, iteration: int) -> dict[str, Any]:
    for entry in entries:
        if entry.get("task_id") == task_id and entry.get("iteration") == iteration:
            return entry
    raise ValueError(f"Could not find task '{task_id}' iteration {iteration} in the ledger.")


def find_reference_entry(entries: list[dict[str, Any]], *, task_id: str, candidate_iteration: int, reference_iteration: int | None) -> dict[str, Any]:
    if reference_iteration is not None:
        return find_entry(entries, task_id=task_id, iteration=reference_iteration)

    candidates = [
        entry
        for entry in entries
        if entry.get("task_id") == task_id
        and isinstance(entry.get("iteration"), int)
        and entry.get("iteration") < candidate_iteration
        and entry.get("kept") is True
    ]
    if not candidates:
        raise ValueError(
            f"Could not infer a reference entry for task '{task_id}' iteration {candidate_iteration}; no earlier kept iteration exists."
        )
    return sorted(candidates, key=lambda entry: int(entry["iteration"]))[-1]


def gate_passes(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized in PASS_LIKE_STATUSES


def gate_status(value: Any) -> str:
    return str(value).strip() if value is not None else "missing"


def numeric_scalar(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def pass_fail_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in PASS_LIKE_STATUSES:
        return True
    if normalized in FAIL_LIKE_STATUSES:
        return False
    return None


def compare_primary_metric(reference: dict[str, Any], candidate: dict[str, Any], neutral_threshold: float) -> dict[str, Any]:
    reference_metric = reference.get("primary_metric")
    candidate_metric = candidate.get("primary_metric")
    if not isinstance(reference_metric, dict) or not isinstance(candidate_metric, dict):
        return {
            "status": "unresolved",
            "reason": "Reference or candidate primary metric payload is missing or malformed.",
        }

    reference_name = reference_metric.get("name")
    candidate_name = candidate_metric.get("name")
    reference_direction = reference_metric.get("direction")
    candidate_direction = candidate_metric.get("direction")
    payload = {
        "name": candidate_name,
        "direction": candidate_direction,
        "reference_value": reference_metric.get("value"),
        "candidate_value": candidate_metric.get("value"),
    }

    if reference_name != candidate_name:
        return {**payload, "status": "unresolved", "reason": "Primary metric names do not match."}
    if reference_direction != candidate_direction:
        return {**payload, "status": "unresolved", "reason": "Primary metric directions do not match."}
    if candidate_direction not in ACCEPTED_DIRECTIONS:
        return {**payload, "status": "unresolved", "reason": "Primary metric direction is not supported."}

    direction = str(candidate_direction)
    if direction in {"higher_is_better", "lower_is_better"}:
        reference_value = numeric_scalar(reference_metric.get("value"))
        candidate_value = numeric_scalar(candidate_metric.get("value"))
        if reference_value is None or candidate_value is None:
            return {**payload, "status": "unresolved", "reason": "Primary metric values are not both numeric."}
        delta = candidate_value - reference_value
        if abs(delta) <= neutral_threshold:
            return {
                **payload,
                "status": "neutral",
                "delta": delta,
                "reason": "Primary metric change is within the neutral threshold.",
            }
        if direction == "higher_is_better":
            status = "improved" if delta > 0 else "worse"
        else:
            status = "improved" if delta < 0 else "worse"
        return {
            **payload,
            "status": status,
            "delta": delta,
            "reason": "Primary metric comparison completed.",
        }

    if direction == "pass_fail":
        reference_value = pass_fail_value(reference_metric.get("value"))
        candidate_value = pass_fail_value(candidate_metric.get("value"))
        if reference_value is None or candidate_value is None:
            return {**payload, "status": "unresolved", "reason": "Primary pass/fail values could not be interpreted."}
        if reference_value == candidate_value:
            return {**payload, "status": "neutral", "reason": "Primary pass/fail result stayed the same."}
        return {
            **payload,
            "status": "improved" if candidate_value else "worse",
            "reason": "Primary pass/fail result changed.",
        }

    if direction == "clearer_is_better":
        if reference_metric.get("value") == candidate_metric.get("value"):
            return {**payload, "status": "neutral", "reason": "Legacy clarity metric stayed the same."}
        return {
            **payload,
            "status": "unresolved",
            "reason": "Legacy 'clearer_is_better' metrics require manual review when values differ.",
        }

    return {**payload, "status": "unresolved", "reason": "Primary metric direction is not comparable here."}


def compare_secondary_metrics(reference: dict[str, Any], candidate: dict[str, Any], rules: list[SecondaryRule]) -> dict[str, Any]:
    reference_metrics = reference.get("secondary_metrics")
    candidate_metrics = candidate.get("secondary_metrics")
    if not isinstance(reference_metrics, dict) or not isinstance(candidate_metrics, dict):
        return {
            "overall_status": "unresolved",
            "results": [],
            "regressions": [],
            "unresolved": ["Reference or candidate secondary metrics payload is missing or malformed."],
            "unscored_metrics": [],
        }

    results: list[dict[str, Any]] = []
    regressions: list[str] = []
    unresolved: list[str] = []
    scored_names = {rule.name for rule in rules}
    unscored_metrics = sorted(set(candidate_metrics) - scored_names)

    for rule in rules:
        reference_value = reference_metrics.get(rule.name)
        candidate_value = candidate_metrics.get(rule.name)
        result: dict[str, Any] = {
            "name": rule.name,
            "direction": rule.direction,
            "allowed_regression": rule.allowed_regression,
            "reference_value": reference_value,
            "candidate_value": candidate_value,
        }
        if rule.name not in reference_metrics or rule.name not in candidate_metrics:
            result["status"] = "unresolved"
            result["reason"] = "Metric is missing from the reference or candidate entry."
            unresolved.append(rule.name)
            results.append(result)
            continue

        if rule.direction in {"higher_is_better", "lower_is_better"}:
            reference_numeric = numeric_scalar(reference_value)
            candidate_numeric = numeric_scalar(candidate_value)
            if reference_numeric is None or candidate_numeric is None:
                result["status"] = "unresolved"
                result["reason"] = "Metric values are not both numeric."
                unresolved.append(rule.name)
                results.append(result)
                continue

            if rule.direction == "higher_is_better":
                delta = candidate_numeric - reference_numeric
                regression = max(reference_numeric - candidate_numeric, 0.0)
            else:
                delta = reference_numeric - candidate_numeric
                regression = max(candidate_numeric - reference_numeric, 0.0)

            result["delta"] = delta
            result["regression"] = regression
            if regression > rule.allowed_regression:
                result["status"] = "regressed"
                result["reason"] = "Metric regressed beyond the allowed budget."
                regressions.append(rule.name)
            elif regression > 0:
                result["status"] = "budgeted_regression"
                result["reason"] = "Metric regressed but stayed within the allowed budget."
            elif delta == 0:
                result["status"] = "neutral"
                result["reason"] = "Metric stayed flat."
            else:
                result["status"] = "improved"
                result["reason"] = "Metric improved or held the protected side."
            results.append(result)
            continue

        reference_pass = pass_fail_value(reference_value)
        candidate_pass = pass_fail_value(candidate_value)
        if reference_pass is None or candidate_pass is None:
            result["status"] = "unresolved"
            result["reason"] = "Pass/fail metric values could not be interpreted."
            unresolved.append(rule.name)
            results.append(result)
            continue
        if not candidate_pass:
            result["status"] = "regressed"
            result["reason"] = "Candidate failed a protected pass/fail metric."
            regressions.append(rule.name)
        elif reference_pass == candidate_pass:
            result["status"] = "neutral"
            result["reason"] = "Pass/fail metric stayed green."
        else:
            result["status"] = "improved"
            result["reason"] = "Pass/fail metric improved."
        results.append(result)

    if regressions:
        overall_status = "regressed"
    elif unresolved:
        overall_status = "unresolved"
    else:
        overall_status = "ok"
    return {
        "overall_status": overall_status,
        "results": results,
        "regressions": regressions,
        "unresolved": unresolved,
        "unscored_metrics": unscored_metrics,
    }


def score_simplicity(reference: dict[str, Any], candidate: dict[str, Any], proxy: str) -> dict[str, Any]:
    if proxy == "none":
        return {
            "proxy": proxy,
            "status": "not_scored",
            "reference_value": None,
            "candidate_value": None,
            "reason": "No simplicity proxy was requested.",
        }

    reference_changes = reference.get("changes")
    candidate_changes = candidate.get("changes")
    reference_count = len(reference_changes) if isinstance(reference_changes, list) else 0
    candidate_count = len(candidate_changes) if isinstance(candidate_changes, list) else 0
    if candidate_count < reference_count:
        status = "simpler"
    elif candidate_count > reference_count:
        status = "more_complex"
    else:
        status = "same_complexity"
    return {
        "proxy": proxy,
        "status": status,
        "reference_value": reference_count,
        "candidate_value": candidate_count,
        "reason": "Compared the number of touched files as a simplicity proxy.",
    }


def hard_gate_report(candidate: dict[str, Any]) -> dict[str, Any]:
    hard_gates = candidate.get("hard_gates")
    if not isinstance(hard_gates, dict):
        return {
            "status": "unresolved",
            "failing_gates": [],
            "reason": "Candidate hard gates are missing or malformed.",
        }

    failing = [
        name
        for name, status in hard_gates.items()
        if not gate_passes(status)
    ]
    return {
        "status": "pass" if not failing else "fail",
        "failing_gates": failing,
        "gates": {str(name): gate_status(status) for name, status in hard_gates.items()},
        "reason": "All hard gates pass." if not failing else "One or more hard gates are not passing.",
    }


def build_score_report(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    *,
    task_id: str,
    secondary_rules: list[SecondaryRule],
    primary_neutral_threshold: float,
    simplicity_proxy: str,
) -> dict[str, Any]:
    hard_gates = hard_gate_report(candidate)
    primary_metric = compare_primary_metric(reference, candidate, primary_neutral_threshold)
    secondary_metrics = compare_secondary_metrics(reference, candidate, secondary_rules)
    simplicity = score_simplicity(reference, candidate, simplicity_proxy)

    recommendation = "needs_manual_review"
    reasons: list[str] = []
    if hard_gates["status"] == "unresolved":
        reasons.append("Candidate hard gates could not be interpreted.")
    elif hard_gates["status"] == "fail":
        recommendation = "reject"
        reasons.append("Candidate does not satisfy all hard gates.")
    else:
        reasons.append("Candidate satisfies all hard gates.")

    if recommendation != "reject":
        primary_status = primary_metric.get("status")
        if primary_status == "unresolved":
            reasons.append(str(primary_metric.get("reason")))
        else:
            reasons.append(f"Primary metric status: {primary_status}.")

        if secondary_metrics["overall_status"] == "regressed":
            recommendation = "reject"
            reasons.append(
                "Secondary guardrails regressed beyond their allowed budgets: "
                + ", ".join(secondary_metrics["regressions"])
                + "."
            )
        elif secondary_metrics["overall_status"] == "unresolved":
            reasons.append(
                "Some secondary guardrails could not be scored: "
                + ", ".join(secondary_metrics["unresolved"])
                + "."
            )
        else:
            reasons.append("No explicit secondary guardrail regressed beyond its allowed budget.")

        if recommendation != "reject":
            if primary_status == "improved" and secondary_metrics["overall_status"] == "ok":
                recommendation = "keep"
                reasons.append("Primary metric improved, so the candidate wins lexicographically.")
            elif primary_status == "neutral" and secondary_metrics["overall_status"] == "ok":
                if simplicity["status"] == "simpler":
                    recommendation = "keep"
                    reasons.append("Primary metric stayed neutral and the candidate is simpler on the selected proxy.")
                else:
                    recommendation = "reject"
                    reasons.append("Primary metric stayed neutral without a simplicity win, so there is no clear reason to keep the candidate.")
            elif primary_status == "worse":
                recommendation = "reject"
                reasons.append("Primary metric is worse than the reference state.")
            elif secondary_metrics["overall_status"] == "unresolved":
                recommendation = "needs_manual_review"
            else:
                recommendation = "needs_manual_review"

    return {
        "task_id": task_id,
        "reference_iteration": reference.get("iteration"),
        "candidate_iteration": candidate.get("iteration"),
        "recommendation": recommendation,
        "hard_gates": hard_gates,
        "primary_metric": primary_metric,
        "secondary_rules": [rule.as_dict() for rule in secondary_rules],
        "secondary_metrics": secondary_metrics,
        "simplicity": simplicity,
        "reasons": reasons,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Iteration Score Report",
        "",
        f"- Task ID: {report['task_id']}",
        f"- Reference iteration: {report['reference_iteration']}",
        f"- Candidate iteration: {report['candidate_iteration']}",
        f"- Recommendation: {report['recommendation']}",
        f"- Hard gates: {report['hard_gates']['status']}",
        f"- Primary metric: {report['primary_metric'].get('status', 'unknown')}",
        f"- Secondary guardrails: {report['secondary_metrics']['overall_status']}",
        f"- Simplicity proxy: {report['simplicity']['proxy']}",
        "",
        "## Reasons",
    ]
    for reason in report["reasons"]:
        lines.append(f"- {reason}")

    secondary_results = report["secondary_metrics"]["results"]
    if secondary_results:
        lines.extend(["", "## Secondary rules"])
        for result in secondary_results:
            lines.append(
                f"- {result['name']}: {result['status']} "
                f"(reference={result.get('reference_value')}, candidate={result.get('candidate_value')})"
            )

    if report["secondary_metrics"]["unscored_metrics"]:
        lines.extend(["", "## Unscored secondary metrics"])
        for name in report["secondary_metrics"]["unscored_metrics"]:
            lines.append(f"- {name}")

    lines.extend(
        [
            "",
            "## Simplicity",
            f"- Status: {report['simplicity']['status']}",
            f"- Reference value: {report['simplicity']['reference_value']}",
            f"- Candidate value: {report['simplicity']['candidate_value']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        entries = load_ledger_entries(args.ledger)
        candidate = find_entry(entries, task_id=args.task_id, iteration=args.candidate_iteration)
        reference = find_reference_entry(
            entries,
            task_id=args.task_id,
            candidate_iteration=args.candidate_iteration,
            reference_iteration=args.reference_iteration,
        )
        secondary_rules = [parse_secondary_rule(raw) for raw in args.secondary_rule]
        report = build_score_report(
            reference,
            candidate,
            task_id=args.task_id,
            secondary_rules=secondary_rules,
            primary_neutral_threshold=args.primary_neutral_threshold,
            simplicity_proxy=args.simplicity_proxy,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_summary(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
