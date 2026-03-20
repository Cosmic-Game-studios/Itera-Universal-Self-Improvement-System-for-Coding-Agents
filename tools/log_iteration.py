from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

try:
    from tools.validate_ledger import (
        ACCEPTED_DIRECTIONS,
        ALLOWED_EVIDENCE_LABELS,
        render_summary,
        validate_entry,
        validate_ledger,
    )
except ImportError:
    from validate_ledger import (  # type: ignore[no-redef]
        ACCEPTED_DIRECTIONS,
        ALLOWED_EVIDENCE_LABELS,
        render_summary,
        validate_entry,
        validate_ledger,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append one validated iteration record to improvement/ledger.jsonl.",
    )
    parser.add_argument("--ledger", type=Path, default=Path("improvement/ledger.jsonl"), help="Ledger path.")
    parser.add_argument("--task-id", required=True, help="Task id for this iteration.")
    parser.add_argument("--iteration", type=int, required=True, help="Iteration number.")
    parser.add_argument("--eval-tier", required=True, help="Eval tier, such as fast+full.")
    parser.add_argument("--hypothesis", required=True, help="Hypothesis summary.")
    parser.add_argument("--change", action="append", default=[], help="Changed file path. Repeat as needed.")
    parser.add_argument("--hard-gate", action="append", default=[], help="Hard gate as name=status.")
    parser.add_argument("--primary-metric-name", required=True, help="Primary metric name.")
    parser.add_argument("--primary-metric-baseline", required=True, help="Primary metric baseline scalar.")
    parser.add_argument("--primary-metric-value", required=True, help="Primary metric value scalar.")
    parser.add_argument(
        "--primary-metric-direction",
        required=True,
        choices=tuple(sorted(ACCEPTED_DIRECTIONS)),
        help="Primary metric direction.",
    )
    parser.add_argument("--secondary-metric", action="append", default=[], help="Secondary metric as name=value.")
    parser.add_argument("--evidence", action="append", default=[], help="Evidence claim as name=label.")
    parser.add_argument("--kept", choices=("true", "false"), required=True, help="Whether the iteration was kept.")
    parser.add_argument("--summary", required=True, help="Short summary of the iteration outcome.")
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format after a successful append.",
    )
    return parser.parse_args()


def parse_scalar(text: str) -> Any:
    stripped = text.strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped
    if isinstance(value, (dict, list)):
        return stripped
    return value


def parse_pair(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError(f"Expected name=value pair, got: {raw}")
    name, value = raw.split("=", 1)
    key = name.strip()
    if not key:
        raise ValueError(f"Expected non-empty name in pair: {raw}")
    return key, value.strip()


def parse_string_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in items:
        key, value = parse_pair(raw)
        if not value:
            raise ValueError(f"Expected non-empty value for key '{key}'")
        mapping[key] = value
    return mapping


def parse_scalar_map(items: list[str]) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for raw in items:
        key, value = parse_pair(raw)
        mapping[key] = parse_scalar(value)
    return mapping


def parse_evidence_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in items:
        key, value = parse_pair(raw)
        if value not in ALLOWED_EVIDENCE_LABELS:
            allowed = ", ".join(sorted(ALLOWED_EVIDENCE_LABELS))
            raise ValueError(f"Evidence label for '{key}' must be one of: {allowed}")
        mapping[key] = value
    return mapping


def build_entry(args: argparse.Namespace) -> dict[str, Any]:
    baseline = parse_scalar(args.primary_metric_baseline)
    value = parse_scalar(args.primary_metric_value)
    if isinstance(baseline, (dict, list)) or isinstance(value, (dict, list)):
        raise ValueError("Primary metric baseline and value must be JSON scalars")

    entry = {
        "task_id": args.task_id,
        "iteration": args.iteration,
        "eval_tier": args.eval_tier,
        "hypothesis": args.hypothesis,
        "changes": [change.strip() for change in args.change if change.strip()],
        "hard_gates": parse_string_map(args.hard_gate),
        "primary_metric": {
            "name": args.primary_metric_name,
            "baseline": baseline,
            "value": value,
            "direction": args.primary_metric_direction,
        },
        "secondary_metrics": parse_scalar_map(args.secondary_metric),
        "evidence": parse_evidence_map(args.evidence),
        "kept": args.kept == "true",
        "summary": args.summary,
    }
    issues = validate_entry("entry 1", entry)
    if issues:
        message = "\n".join(f"- {issue.location}: {issue.message}" for issue in issues)
        raise ValueError(f"Entry does not satisfy the ledger contract:\n{message}")
    return entry


def append_entry(ledger: Path, entry: dict[str, Any]) -> dict[str, Any]:
    ledger.parent.mkdir(parents=True, exist_ok=True)

    if ledger.exists():
        existing_report = validate_ledger(ledger)
        if not existing_report.valid:
            raise ValueError(f"Existing ledger is invalid:\n{render_summary(existing_report)}")
        existing_text = ledger.read_text(encoding="utf-8")
    else:
        existing_text = ""

    prefix = existing_text
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    entry_line = json.dumps(entry, separators=(",", ":"), ensure_ascii=True)
    candidate_text = f"{prefix}{entry_line}\n"

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(candidate_text)
        tmp_path = Path(handle.name)
    try:
        candidate_report = validate_ledger(tmp_path)
        if not candidate_report.valid:
            raise ValueError(f"Updated ledger would be invalid:\n{render_summary(candidate_report)}")
        ledger.write_text(candidate_text, encoding="utf-8")
        return validate_ledger(ledger).as_dict()
    finally:
        tmp_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    try:
        entry = build_entry(args)
        report = append_entry(args.ledger, entry)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if args.format == "json":
        print(json.dumps({"appended": entry, "ledger_report": report}, indent=2, sort_keys=True))
    else:
        print(f"Appended iteration {entry['iteration']} for {entry['task_id']} to {args.ledger}")
        print(f"Ledger entries: {report['entry_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
