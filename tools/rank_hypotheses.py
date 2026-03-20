from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from tools.loop_state import build_loop_state, load_ledger_entries, load_task_context
except ImportError:
    from loop_state import build_loop_state, load_ledger_entries, load_task_context  # type: ignore[no-redef]


TASK_NAME_RE = re.compile(r"^- Task name:\s*(.+?)\s*$", re.M)
DESIRED_OUTCOME_RE = re.compile(r"^- Desired outcome:\s*(.+?)\s*$", re.M)
TASK_TYPE_RE = re.compile(r"^- Task type:\s*(.+?)\s*$", re.M)
TOKEN_RE = re.compile(r"[a-z][a-z0-9_-]{2,}")
STOPWORDS = {
    "about",
    "after",
    "again",
    "agent",
    "agents",
    "all",
    "also",
    "and",
    "before",
    "between",
    "candidate",
    "change",
    "changes",
    "code",
    "current",
    "does",
    "each",
    "from",
    "helper",
    "high",
    "hypothesis",
    "hypotheses",
    "improvement",
    "into",
    "iteration",
    "iterations",
    "keep",
    "kept",
    "ledger",
    "loop",
    "more",
    "next",
    "only",
    "pattern",
    "patterns",
    "rank",
    "ranking",
    "repo",
    "repository",
    "review",
    "score",
    "self",
    "should",
    "skill",
    "state",
    "task",
    "than",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "through",
    "using",
    "with",
    "without",
    "workflow",
}
ALLOWED_EVIDENCE = {"measured", "inferred", "speculative"}
ALLOWED_KINDS = {"exploit", "explore", "stabilize"}
ALLOWED_MODES = {"auto", "exploit", "balanced", "plateau_escape", "recovery"}
EVIDENCE_BONUS = {
    "measured": 6,
    "inferred": 2,
    "speculative": -2,
}
MODE_KIND_BONUS = {
    "exploit": {"exploit": 7, "stabilize": 3, "explore": 0},
    "balanced": {"exploit": 4, "stabilize": 4, "explore": 3},
    "plateau_escape": {"exploit": 1, "stabilize": 4, "explore": 8},
    "recovery": {"exploit": 1, "stabilize": 8, "explore": -1},
}


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    summary: str
    kind: str
    expected_upside: int
    implementation_cost: int
    risk: int
    confidence: int
    reversibility: int
    evidence: str
    notes: str
    related_patterns: tuple[str, ...]
    related_prevention_rules: tuple[str, ...]
    blocked_by: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.hypothesis_id,
            "summary": self.summary,
            "kind": self.kind,
            "expected_upside": self.expected_upside,
            "implementation_cost": self.implementation_cost,
            "risk": self.risk,
            "confidence": self.confidence,
            "reversibility": self.reversibility,
            "evidence": self.evidence,
            "notes": self.notes,
            "related_patterns": list(self.related_patterns),
            "related_prevention_rules": list(self.related_prevention_rules),
            "blocked_by": list(self.blocked_by),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank candidate hypotheses with loop-state-aware strategy modes for stronger self-improvement.",
    )
    parser.add_argument("--backlog", type=Path, required=True, help="Path to a hypothesis backlog JSON file.")
    parser.add_argument("--task", type=Path, default=Path("improvement/current-task.md"), help="Path to current-task.md.")
    parser.add_argument("--ledger", type=Path, default=Path("improvement/ledger.jsonl"), help="Path to improvement/ledger.jsonl.")
    parser.add_argument("--task-id", help="Optional task id override for loop-state lookup.")
    parser.add_argument(
        "--mode",
        choices=tuple(sorted(ALLOWED_MODES)),
        default="auto",
        help="Ranking mode. Auto derives exploit, balanced, plateau_escape, or recovery from loop state.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Maximum ranked hypotheses to include in the output.")
    parser.add_argument("--format", choices=("summary", "json"), default="summary", help="Output format.")
    return parser.parse_args()


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def clean_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Field '{field_name}' must be a list of strings.")
    cleaned: list[str] = []
    for item in value:
        text = clean_text(item)
        if text:
            cleaned.append(text)
    return tuple(cleaned)


def bounded_int(payload: dict[str, Any], field_name: str) -> int:
    raw = payload.get(field_name)
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ValueError(f"Field '{field_name}' must be an integer between 0 and 5.")
    if raw < 0 or raw > 5:
        raise ValueError(f"Field '{field_name}' must be between 0 and 5.")
    return raw


def hypothesis_from_dict(payload: dict[str, Any], *, index: int) -> Hypothesis:
    raw_id = clean_text(payload.get("id", ""))
    if not raw_id:
        raise ValueError(f"Hypothesis {index} is missing a non-empty 'id'.")
    summary = clean_text(payload.get("summary", ""))
    if not summary:
        raise ValueError(f"Hypothesis {index} is missing a non-empty 'summary'.")
    kind = clean_text(payload.get("kind", "")).lower()
    if kind not in ALLOWED_KINDS:
        allowed = ", ".join(sorted(ALLOWED_KINDS))
        raise ValueError(f"Hypothesis {index} has invalid 'kind'. Expected one of: {allowed}.")
    evidence = clean_text(payload.get("evidence", "")).lower()
    if evidence not in ALLOWED_EVIDENCE:
        allowed = ", ".join(sorted(ALLOWED_EVIDENCE))
        raise ValueError(f"Hypothesis {index} has invalid 'evidence'. Expected one of: {allowed}.")

    return Hypothesis(
        hypothesis_id=raw_id,
        summary=summary,
        kind=kind,
        expected_upside=bounded_int(payload, "expected_upside"),
        implementation_cost=bounded_int(payload, "implementation_cost"),
        risk=bounded_int(payload, "risk"),
        confidence=bounded_int(payload, "confidence"),
        reversibility=bounded_int(payload, "reversibility"),
        evidence=evidence,
        notes=clean_text(payload.get("notes", "")),
        related_patterns=clean_list(payload.get("related_patterns"), field_name="related_patterns"),
        related_prevention_rules=clean_list(
            payload.get("related_prevention_rules"),
            field_name="related_prevention_rules",
        ),
        blocked_by=clean_list(payload.get("blocked_by"), field_name="blocked_by"),
    )


def load_backlog(path: Path) -> list[Hypothesis]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        raw_items = payload.get("hypotheses")
    else:
        raise ValueError("Backlog must be a JSON array or an object containing a 'hypotheses' array.")
    if not isinstance(raw_items, list):
        raise ValueError("Backlog must contain a 'hypotheses' array.")

    hypotheses: list[Hypothesis] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Hypothesis {index} must be a JSON object.")
        hypothesis = hypothesis_from_dict(raw, index=index)
        if hypothesis.hypothesis_id in seen_ids:
            raise ValueError(f"Backlog repeats hypothesis id '{hypothesis.hypothesis_id}'.")
        seen_ids.add(hypothesis.hypothesis_id)
        hypotheses.append(hypothesis)
    if not hypotheses:
        raise ValueError("Backlog must contain at least one hypothesis.")
    return hypotheses


def extract_line(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = clean_text(match.group(1))
    return value or None


def normalize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 5:
        return token[:-3] + "y"
    return token


def collect_tokens(*parts: str | None) -> set[str]:
    tokens: set[str] = set()
    for part in parts:
        if not part:
            continue
        for raw_token in TOKEN_RE.findall(part.lower()):
            token = normalize_token(raw_token)
            if len(token) < 4 or token in STOPWORDS or token.isdigit():
                continue
            tokens.add(token)
    return tokens


def task_keywords(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return collect_tokens(
        extract_line(TASK_NAME_RE, text),
        extract_line(DESIRED_OUTCOME_RE, text),
        extract_line(TASK_TYPE_RE, text),
        text,
    )


def determine_mode(
    requested_mode: str,
    *,
    task_path: Path,
    ledger_path: Path,
    task_id_override: str | None,
) -> tuple[str, list[str], dict[str, Any] | None]:
    if requested_mode != "auto":
        return requested_mode, [f"Mode was explicitly set to `{requested_mode}`."], None

    task = load_task_context(task_path)
    task_id = task_id_override or task.task_id
    if not task_id:
        raise ValueError("Could not determine task id for automatic mode selection.")
    state = build_loop_state(task, load_ledger_entries(ledger_path), task_id)

    if state["recent_failed_iterations"] >= 2:
        return "recovery", ["Two or more recent iterations failed to keep, so recovery mode is safer."], state
    if state["primary_metric_trend"] == "flat":
        return "plateau_escape", ["Recent kept progress is flat, so plateau-escape mode should value exploratory ideas more."], state
    if state["primary_metric_trend"] == "worse":
        return "recovery", ["Recent kept progress got worse, so recovery mode should prioritize stabilizing ideas."], state
    if state["primary_metric_trend"] == "improving":
        return "exploit", ["Recent kept progress is improving, so exploit mode should prioritize the strongest grounded follow-up."], state
    return "balanced", ["Automatic mode defaulted to balanced because the loop does not yet show a strong exploit or recovery signal."], state


def hypothesis_tokens(hypothesis: Hypothesis) -> set[str]:
    return collect_tokens(
        hypothesis.summary,
        hypothesis.notes,
        " ".join(hypothesis.related_patterns),
        " ".join(hypothesis.related_prevention_rules),
    )


def rank_hypothesis(
    hypothesis: Hypothesis,
    *,
    mode: str,
    task_keyword_set: set[str],
) -> dict[str, Any]:
    positive = (
        hypothesis.expected_upside * 7
        + hypothesis.confidence * 4
        + hypothesis.reversibility * 3
    )
    penalties = (
        hypothesis.risk * 5
        + hypothesis.implementation_cost * 3
        + len(hypothesis.blocked_by) * 4
    )
    evidence_bonus = EVIDENCE_BONUS[hypothesis.evidence]
    mode_bonus = MODE_KIND_BONUS[mode][hypothesis.kind]
    alignment = min(len(task_keyword_set & hypothesis_tokens(hypothesis)), 4)
    alignment_bonus = alignment * 2
    grounding_bonus = min(len(hypothesis.related_patterns), 2) * 2 + min(len(hypothesis.related_prevention_rules), 2) * 2
    total = positive + evidence_bonus + mode_bonus + alignment_bonus + grounding_bonus - penalties

    reasons = [
        f"Expected upside contributes {hypothesis.expected_upside * 7} points.",
        f"Confidence and reversibility contribute {hypothesis.confidence * 4 + hypothesis.reversibility * 3} points.",
        f"`{mode}` mode gives `{hypothesis.kind}` hypotheses a {mode_bonus:+d} point bias.",
        f"Evidence level `{hypothesis.evidence}` contributes {evidence_bonus:+d} points.",
    ]
    if alignment_bonus:
        reasons.append(f"Task-keyword alignment contributes {alignment_bonus} points.")
    if grounding_bonus:
        reasons.append(f"Related patterns and prevention rules contribute {grounding_bonus} points.")
    reasons.append(
        f"Risk, implementation cost, and blockers subtract {penalties} points."
    )

    warnings: list[str] = []
    if hypothesis.risk >= 4:
        warnings.append("High risk hypothesis.")
    if hypothesis.implementation_cost >= 4:
        warnings.append("High implementation cost hypothesis.")
    if hypothesis.blocked_by:
        warnings.append("Blocked by: " + "; ".join(hypothesis.blocked_by))
    if hypothesis.evidence == "speculative":
        warnings.append("Speculative evidence; treat as an exploration candidate, not a default first move.")

    return {
        "hypothesis": hypothesis.as_dict(),
        "score": total,
        "mode": mode,
        "positive_points": positive,
        "penalty_points": penalties,
        "evidence_bonus": evidence_bonus,
        "mode_bonus": mode_bonus,
        "alignment_bonus": alignment_bonus,
        "grounding_bonus": grounding_bonus,
        "reasons": reasons,
        "warnings": warnings,
    }


def rank_hypotheses(
    hypotheses: list[Hypothesis],
    *,
    mode: str,
    task_keyword_set: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    ranked = [
        rank_hypothesis(hypothesis, mode=mode, task_keyword_set=task_keyword_set)
        for hypothesis in hypotheses
    ]
    ranked.sort(
        key=lambda item: (
            -item["score"],
            item["hypothesis"]["risk"],
            item["hypothesis"]["implementation_cost"],
            -item["hypothesis"]["expected_upside"],
            item["hypothesis"]["id"],
        )
    )
    return ranked[:limit]


def render_summary(
    backlog_path: Path,
    ranked: list[dict[str, Any]],
    *,
    mode: str,
    mode_reasons: list[str],
    loop_state: dict[str, Any] | None,
) -> str:
    lines = [
        "# Hypothesis Ranking Report",
        "",
        f"- Backlog: `{backlog_path}`",
        f"- Selected mode: `{mode}`",
        f"- Ranked hypotheses: {len(ranked)}",
    ]
    if loop_state is not None:
        lines.extend(
            [
                f"- Loop recommendation: `{loop_state.get('recommendation')}`",
                f"- Primary metric trend: `{loop_state.get('primary_metric_trend')}`",
                f"- Recent failed iterations: {loop_state.get('recent_failed_iterations')}",
            ]
        )
    lines.extend(["", "## Mode reasons"])
    for reason in mode_reasons:
        lines.append(f"- {reason}")

    if ranked:
        top = ranked[0]
        lines.extend(
            [
                "",
                "## Recommended next hypothesis",
                f"- ID: `{top['hypothesis']['id']}`",
                f"- Kind: `{top['hypothesis']['kind']}`",
                f"- Score: {top['score']}",
                f"- Summary: {top['hypothesis']['summary']}",
            ]
        )

    for item in ranked:
        hypothesis = item["hypothesis"]
        lines.extend(
            [
                "",
                f"## `{hypothesis['id']}`",
                f"- Kind: `{hypothesis['kind']}`",
                f"- Score: {item['score']}",
                f"- Summary: {hypothesis['summary']}",
                f"- Reasons: {' '.join(item['reasons'])}",
            ]
        )
        if item["warnings"]:
            lines.append(f"- Warnings: {' '.join(item['warnings'])}")
    return "\n".join(lines).rstrip() + "\n"


def render_json(
    backlog_path: Path,
    ranked: list[dict[str, Any]],
    *,
    mode: str,
    mode_reasons: list[str],
    loop_state: dict[str, Any] | None,
) -> str:
    payload = {
        "backlog": str(backlog_path),
        "selected_mode": mode,
        "mode_reasons": mode_reasons,
        "loop_state": loop_state,
        "ranked_hypotheses": ranked,
        "recommended_next_hypothesis": ranked[0]["hypothesis"]["id"] if ranked else None,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    args = parse_args()
    try:
        hypotheses = load_backlog(args.backlog)
        mode, mode_reasons, loop_state = determine_mode(
            args.mode,
            task_path=args.task,
            ledger_path=args.ledger,
            task_id_override=args.task_id,
        )
        ranked = rank_hypotheses(
            hypotheses,
            mode=mode,
            task_keyword_set=task_keywords(args.task),
            limit=args.limit,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc))

    if args.format == "json":
        print(render_json(args.backlog, ranked, mode=mode, mode_reasons=mode_reasons, loop_state=loop_state), end="")
    else:
        print(render_summary(args.backlog, ranked, mode=mode, mode_reasons=mode_reasons, loop_state=loop_state), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
