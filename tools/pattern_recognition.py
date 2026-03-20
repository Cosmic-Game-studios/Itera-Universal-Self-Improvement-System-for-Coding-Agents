from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z][a-z0-9_-]{2,}")
META_AREAS = {"improvement/", "qa/"}
REPORTABLE_META_AREAS = {"improvement/"}
STOPWORDS = {
    "across",
    "about",
    "above",
    "after",
    "again",
    "agent",
    "against",
    "along",
    "also",
    "always",
    "and",
    "any",
    "around",
    "baseline",
    "because",
    "before",
    "being",
    "best",
    "between",
    "build",
    "change",
    "changed",
    "changes",
    "check",
    "checks",
    "clear",
    "code",
    "current",
    "direction",
    "entry",
    "every",
    "fail",
    "false",
    "file",
    "files",
    "found",
    "from",
    "gate",
    "gates",
    "have",
    "higher_is_better",
    "hypothesis",
    "improved",
    "improvement",
    "into",
    "iteration",
    "iterations",
    "keep",
    "kept",
    "ledger",
    "lower_is_better",
    "made",
    "metric",
    "more",
    "name",
    "often",
    "once",
    "only",
    "pass",
    "path",
    "present",
    "repo",
    "repository",
    "result",
    "results",
    "same",
    "summary",
    "task",
    "tasks",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "them",
    "they",
    "those",
    "through",
    "this",
    "touching",
    "tool",
    "true",
    "under",
    "using",
    "value",
    "verified",
    "what",
    "when",
    "where",
    "without",
    "with",
    "work",
    "would",
    "your",
    "the",
}


@dataclass(frozen=True)
class LedgerEntry:
    task_id: str
    iteration: int
    eval_tier: str
    hypothesis: str
    summary: str
    changes: tuple[str, ...]
    hard_gates: dict[str, str]
    kept: bool
    primary_metric_name: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, line_number: int) -> "LedgerEntry":
        if "task_id" not in payload:
            raise ValueError(f"Ledger line {line_number} is missing 'task_id'")
        kept = payload.get("kept")
        if not isinstance(kept, bool):
            raise ValueError(f"Ledger line {line_number} must contain boolean 'kept'")
        changes = tuple(str(item).strip() for item in payload.get("changes", []) if str(item).strip())
        hard_gates = {
            str(name).strip(): str(status).strip()
            for name, status in dict(payload.get("hard_gates", {})).items()
            if str(name).strip()
        }
        primary_metric = payload.get("primary_metric", {})
        primary_metric_name = None
        if isinstance(primary_metric, dict):
            name = primary_metric.get("name")
            if name is not None:
                primary_metric_name = str(name).strip() or None
        return cls(
            task_id=str(payload["task_id"]).strip(),
            iteration=int(payload.get("iteration", 0)),
            eval_tier=str(payload.get("eval_tier", "unknown")).strip(),
            hypothesis=str(payload.get("hypothesis", "")).strip(),
            summary=str(payload.get("summary", "")).strip(),
            changes=changes,
            hard_gates=hard_gates,
            kept=kept,
            primary_metric_name=primary_metric_name,
        )


@dataclass
class AreaProfile:
    support: int = 0
    signal_support: int = 0
    gate_counts: Counter[str] | None = None
    token_counts: Counter[str] | None = None

    def __post_init__(self) -> None:
        if self.gate_counts is None:
            self.gate_counts = Counter()
        if self.token_counts is None:
            self.token_counts = Counter()


@dataclass(frozen=True)
class PatternCandidate:
    kind: str
    key: str
    support: int
    total_kept: int
    top_gates: tuple[tuple[str, int], ...]
    top_terms: tuple[tuple[str, int], ...]
    title: str
    context: str
    signal: str
    caveat: str
    score: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "key": self.key,
            "support": self.support,
            "total_kept": self.total_kept,
            "top_gates": list(self.top_gates),
            "top_terms": list(self.top_terms),
            "title": self.title,
            "context": self.context,
            "signal": self.signal,
            "caveat": self.caveat,
            "score": self.score,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect recurring successful patterns from improvement/ledger.jsonl.",
    )
    parser.add_argument("--ledger", type=Path, required=True, help="Path to the ledger JSONL file.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--min-support",
        type=int,
        default=2,
        help="Minimum kept-entry support required before a pattern is suggested.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of suggested patterns to output.",
    )
    return parser.parse_args()


def load_ledger(path: Path) -> list[LedgerEntry]:
    entries: list[LedgerEntry] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ledger line {line_number} is not valid JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Ledger line {line_number} must be a JSON object")
        entries.append(LedgerEntry.from_dict(payload, line_number=line_number))
    return entries


def normalize_area(path: str) -> str:
    cleaned = path.strip().replace("\\", "/")
    parts = [part for part in cleaned.split("/") if part and part != "."]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}/"


def normalize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 5:
        return token[:-3] + "y"
    return token


def entry_tokens(entry: LedgerEntry) -> set[str]:
    text = " ".join(
        part
        for part in [
            entry.task_id,
            entry.hypothesis,
            entry.summary,
            entry.primary_metric_name or "",
        ]
        if part
    ).lower()
    tokens: set[str] = set()
    for raw_token in TOKEN_RE.findall(text):
        token = normalize_token(raw_token)
        if len(token) < 4 or token in STOPWORDS or token.isdigit():
            continue
        tokens.add(token)
    return tokens


def passed_gates(entry: LedgerEntry) -> set[str]:
    return {
        gate
        for gate, status in entry.hard_gates.items()
        if status.lower() == "pass"
    }


def focused_signal_area(areas: set[str]) -> str | None:
    content_areas = sorted(area for area in areas if area not in META_AREAS)
    if len(content_areas) == 1:
        return content_areas[0]
    if not content_areas and len(areas) == 1:
        return next(iter(areas))
    return None


def build_area_profiles(entries: list[LedgerEntry]) -> dict[str, AreaProfile]:
    profiles: dict[str, AreaProfile] = defaultdict(AreaProfile)
    for entry in entries:
        if not entry.kept:
            continue
        areas = {
            area
            for area in (normalize_area(path) for path in entry.changes)
            if area
        }
        if not areas:
            continue
        tokens = entry_tokens(entry)
        gates = passed_gates(entry)
        ordered_tokens = sorted(tokens)
        ordered_gates = sorted(gates)
        for area in sorted(areas):
            profile = profiles[area]
            profile.support += 1
        signal_area = focused_signal_area(areas)
        if signal_area is None:
            continue
        profile = profiles[signal_area]
        profile.signal_support += 1
        profile.gate_counts.update(ordered_gates)
        profile.token_counts.update(ordered_tokens)
    return dict(profiles)


def build_gate_profiles(entries: list[LedgerEntry]) -> dict[str, Counter[str]]:
    token_counts_by_gate: dict[str, Counter[str]] = defaultdict(Counter)
    for entry in entries:
        if not entry.kept:
            continue
        ordered_tokens = sorted(entry_tokens(entry))
        for gate in sorted(passed_gates(entry)):
            token_counts_by_gate[gate].update(ordered_tokens)
    return dict(token_counts_by_gate)


def top_terms(counter: Counter[str], *, exclude: set[str], limit: int = 3) -> tuple[tuple[str, int], ...]:
    results: list[tuple[str, int]] = []
    for token, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        if token in exclude:
            continue
        results.append((token, count))
        if len(results) >= limit:
            break
    return tuple(results)


def top_counts(counter: Counter[str], *, limit: int = 3) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit])


def area_title(area: str, gates: tuple[tuple[str, int], ...]) -> str:
    subject = area.rstrip("/") if area.endswith("/") else area
    if area == "improvement/":
        return "improvement artifacts should stay in sync with kept work"
    if any(gate == "github_readme_check" for gate, _ in gates):
        return f"{subject} changes should be verified on GitHub"
    return f"{subject} work benefits from repeatable verification"


def caveat_for_support(support: int, total_kept: int, *, docs_heavy: bool) -> str:
    parts: list[str] = []
    if support < 3:
        parts.append("This suggestion is based on a small sample")
    if docs_heavy:
        parts.append("current history is documentation-heavy")
    if not parts:
        parts.append("validate against broader future history before treating it as durable")
    return "; ".join(parts) + "."


def suggest_patterns(
    entries: list[LedgerEntry],
    *,
    min_support: int = 2,
    limit: int = 5,
) -> list[PatternCandidate]:
    kept_entries = [entry for entry in entries if entry.kept]
    total_kept = len(kept_entries)
    if total_kept == 0:
        return []

    area_profiles = build_area_profiles(kept_entries)
    gate_token_profiles = build_gate_profiles(kept_entries)
    gate_support = Counter(gate for entry in kept_entries for gate in passed_gates(entry))
    docs_heavy = sum(1 for entry in kept_entries if "readme" in entry_tokens(entry)) >= max(2, total_kept // 2)

    candidates: list[PatternCandidate] = []

    for area, profile in area_profiles.items():
        if profile.support < min_support:
            continue
        if area in META_AREAS and area not in REPORTABLE_META_AREAS and profile.signal_support == 0:
            continue
        area_key_token = normalize_token(area.lower().replace("/", "").replace(".", ""))
        gates = top_counts(profile.gate_counts, limit=3)
        terms = top_terms(profile.token_counts, exclude={area_key_token}, limit=3)
        signal_basis = profile.signal_support or profile.support
        gate_bits = ", ".join(f"`{gate}` {count}/{signal_basis}" for gate, count in gates) or "no repeated pass gates"
        term_bits = ", ".join(f"`{term}`" for term, _ in terms) or "no strong recurring terms yet"
        subject = f"`{area}`"
        context = f"Found in {profile.support} kept iterations touching {subject}."
        if 0 < profile.signal_support < profile.support:
            context += f" Area-specific signals were only clear in {profile.signal_support} focused iterations."
        elif profile.signal_support == 0:
            context += " History is mixed across multiple content areas, so the tool avoids attributing area-specific signals."
        candidates.append(
            PatternCandidate(
                kind="area",
                key=area,
                support=profile.support,
                total_kept=total_kept,
                top_gates=gates,
                top_terms=terms,
                title=area_title(area, gates),
                context=context,
                signal=f"Repeated pass gates: {gate_bits}. Common themes: {term_bits}.",
                caveat=caveat_for_support(profile.support, total_kept, docs_heavy=docs_heavy),
                score=profile.support * 10 + sum(count for _, count in gates[:2]),
            )
        )

    for gate, support in gate_support.items():
        if support < min_support:
            continue
        ratio = support / total_kept
        if ratio < 0.6:
            continue
        terms = top_terms(gate_token_profiles.get(gate, Counter()), exclude={normalize_token(gate.lower())}, limit=3)
        term_bits = ", ".join(f"`{term}`" for term, _ in terms) or "no strong recurring terms yet"
        candidates.append(
            PatternCandidate(
                kind="gate",
                key=gate,
                support=support,
                total_kept=total_kept,
                top_gates=((gate, support),),
                top_terms=terms,
                title=f"`{gate}` is a recurring keep gate",
                context=f"It appears as passing in {support} of {total_kept} kept iterations.",
                signal=f"Most associated themes: {term_bits}.",
                caveat=caveat_for_support(support, total_kept, docs_heavy=docs_heavy),
                score=support * 9,
            )
        )

    candidates.sort(key=lambda candidate: (-candidate.score, -candidate.support, candidate.kind, candidate.key))
    return candidates[:limit]


def render_markdown(path: Path, entries: list[LedgerEntry], candidates: list[PatternCandidate]) -> str:
    kept_entries = [entry for entry in entries if entry.kept]
    lines = [
        "# Pattern Recognition Report",
        "",
        f"- Ledger: `{path}`",
        f"- Total entries: {len(entries)}",
        f"- Kept entries: {len(kept_entries)}",
        f"- Suggested patterns: {len(candidates)}",
        "",
    ]
    if not candidates:
        lines.append("No pattern suggestions met the current support threshold.")
        return "\n".join(lines)

    for candidate in candidates:
        lines.extend(
            [
                f"## Pattern: {candidate.title}",
                f"- Kind: `{candidate.kind}`",
                f"- Support: {candidate.support}/{candidate.total_kept} kept iterations",
                f"- Context: {candidate.context}",
                f"- Signal: {candidate.signal}",
                f"- Caveat: {candidate.caveat}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_json(path: Path, entries: list[LedgerEntry], candidates: list[PatternCandidate]) -> str:
    payload = {
        "ledger": str(path),
        "total_entries": len(entries),
        "kept_entries": sum(1 for entry in entries if entry.kept),
        "suggested_patterns": [candidate.as_dict() for candidate in candidates],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    args = parse_args()
    entries = load_ledger(args.ledger)
    candidates = suggest_patterns(entries, min_support=args.min_support, limit=args.limit)
    if args.format == "json":
        print(render_json(args.ledger, entries, candidates), end="")
    else:
        print(render_markdown(args.ledger, entries, candidates), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
