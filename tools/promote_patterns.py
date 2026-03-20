from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.memory_context import load_ledger_entries, parse_patterns
    from tools.pattern_recognition import load_ledger as load_pattern_ledger
    from tools.pattern_recognition import suggest_patterns
except ImportError:
    from memory_context import load_ledger_entries, parse_patterns  # type: ignore[no-redef]
    from pattern_recognition import load_ledger as load_pattern_ledger  # type: ignore[no-redef]
    from pattern_recognition import suggest_patterns  # type: ignore[no-redef]


TOKEN_RE = re.compile(r"[a-z0-9]+")
SEPARATOR_RE = re.compile(r"[_/.-]+")
STOPWORDS = {
    "about",
    "after",
    "again",
    "agent",
    "agents",
    "all",
    "also",
    "and",
    "are",
    "before",
    "being",
    "but",
    "can",
    "candidate",
    "change",
    "changes",
    "clear",
    "does",
    "each",
    "explicit",
    "for",
    "from",
    "future",
    "good",
    "have",
    "help",
    "into",
    "iteration",
    "iterations",
    "keep",
    "kept",
    "ledger",
    "lessons",
    "likely",
    "make",
    "memory",
    "more",
    "must",
    "next",
    "not",
    "only",
    "over",
    "past",
    "pattern",
    "patterns",
    "promote",
    "promotion",
    "repo",
    "repository",
    "result",
    "results",
    "rule",
    "rules",
    "same",
    "should",
    "signal",
    "skill",
    "state",
    "still",
    "task",
    "tasks",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "through",
    "using",
    "what",
    "when",
    "with",
    "without",
    "work",
    "workflow",
}
RECOGNITION_META_KEYS = {
    ".agents/",
    ".claude/",
    "AGENTS.md",
    "CLAUDE.md",
    "global-templates/",
}


@dataclass(frozen=True)
class PromotionCandidate:
    source: str
    source_kind: str
    title: str
    context: str
    signal: str
    caveat: str
    support: int
    score: int
    key: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "source_kind": self.source_kind,
            "title": self.title,
            "context": self.context,
            "signal": self.signal,
            "caveat": self.caveat,
            "support": self.support,
            "score": self.score,
            "key": self.key,
        }

    def as_markdown_block(self) -> str:
        return "\n".join(
            [
                f"## Pattern: {self.title}",
                f"- Context: {self.context}",
                f"- Signal: {self.signal}",
                f"- Caveat: {self.caveat}",
            ]
        )


@dataclass(frozen=True)
class SkippedCandidate:
    source: str
    title: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "title": self.title,
            "reason": self.reason,
        }


@dataclass
class MemoryProfile:
    text: str
    support: int
    fixes: Counter[str]
    mistakes: Counter[str]
    task_ids: set[str]


@dataclass(frozen=True)
class ExistingPatternFingerprint:
    title: str
    normalized_title: str
    text: str
    title_text: str
    signal_text: str
    tokens: frozenset[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote durable learnings from the ledger into improvement/patterns.md with transparent dedupe.",
    )
    parser.add_argument("--ledger", type=Path, default=Path("improvement/ledger.jsonl"), help="Path to improvement/ledger.jsonl.")
    parser.add_argument("--patterns", type=Path, default=Path("improvement/patterns.md"), help="Path to improvement/patterns.md.")
    parser.add_argument("--min-support", type=int, default=2, help="Minimum support for pattern-recognition candidates.")
    parser.add_argument(
        "--memory-min-support",
        type=int,
        default=1,
        help="Minimum support for structured-memory prevention rules.",
    )
    parser.add_argument("--limit", type=int, default=8, help="Maximum promotable candidates to keep after scoring.")
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Append promotable candidates to patterns.md instead of only reporting them.",
    )
    return parser.parse_args()


def clean_text(value: object) -> str:
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def clean_sentence(value: object) -> str:
    text = clean_text(value).strip()
    return text.rstrip(" .;:")


def normalize_title(value: str) -> str:
    lowered = value.lower().replace("`", " ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def expand_token(token: str) -> set[str]:
    variants = {token}
    if token.endswith("ies") and len(token) > 4:
        variants.add(token[:-3] + "y")
    if token.endswith("s") and len(token) > 4:
        variants.add(token[:-1])
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        variants.add(stem)
        if len(stem) >= 4 and not stem.endswith("e"):
            variants.add(stem + "e")
    if token.endswith("ed") and len(token) > 4:
        stem = token[:-2]
        variants.add(stem)
        if len(stem) >= 4 and not stem.endswith("e"):
            variants.add(stem + "e")
    return {variant for variant in variants if len(variant) >= 3}


def token_set(text: str) -> frozenset[str]:
    prepared = SEPARATOR_RE.sub(" ", text.lower().replace("`", " "))
    tokens: set[str] = set()
    for raw in TOKEN_RE.findall(prepared):
        if raw.isdigit() or len(raw) < 3 or raw in STOPWORDS:
            continue
        for variant in expand_token(raw):
            if variant not in STOPWORDS:
                tokens.add(variant)
    return frozenset(sorted(tokens))


def existing_fingerprints(path: Path) -> list[ExistingPatternFingerprint]:
    fingerprints: list[ExistingPatternFingerprint] = []
    for entry in parse_patterns(path):
        text = " ".join(part for part in [entry.title, entry.context, entry.signal, entry.caveat] if part).strip()
        fingerprints.append(
            ExistingPatternFingerprint(
                title=entry.title,
                normalized_title=normalize_title(entry.title),
                text=text.lower(),
                title_text=entry.title.lower(),
                signal_text=entry.signal.lower(),
                tokens=token_set(text),
            )
        )
    return fingerprints


def build_recognition_candidates(ledger_path: Path, *, min_support: int) -> list[PromotionCandidate]:
    candidates = suggest_patterns(load_pattern_ledger(ledger_path), min_support=min_support, limit=50)
    promoted: list[PromotionCandidate] = []
    for candidate in candidates:
        if candidate.kind == "area" and candidate.key in RECOGNITION_META_KEYS:
            continue
        promoted.append(
            PromotionCandidate(
                source="pattern_recognition",
                source_kind=f"recognition_{candidate.kind}",
                title=candidate.title,
                context=candidate.context,
                signal=candidate.signal,
                caveat=candidate.caveat,
                support=candidate.support,
                score=candidate.score,
                key=f"{candidate.kind}:{candidate.key}",
            )
        )
    return promoted


def build_memory_candidates(entries: list[dict[str, object]], *, min_support: int) -> list[PromotionCandidate]:
    profiles: dict[str, MemoryProfile] = {}
    for entry in entries:
        if entry.get("kept") is not True:
            continue
        memory = entry.get("memory")
        if not isinstance(memory, dict):
            continue
        raw_rules = memory.get("prevention_rules", [])
        if not isinstance(raw_rules, list):
            continue
        rules = sorted({clean_sentence(rule) for rule in raw_rules if clean_sentence(rule)})
        if not rules:
            continue

        fixes = Counter(clean_sentence(item) for item in memory.get("fixes", []) if clean_sentence(item))
        mistakes = Counter(clean_sentence(item) for item in memory.get("mistakes", []) if clean_sentence(item))
        task_id = clean_text(entry.get("task_id", "unknown-task")) or "unknown-task"

        for rule in rules:
            key = normalize_title(rule)
            profile = profiles.get(key)
            if profile is None:
                profile = MemoryProfile(
                    text=rule,
                    support=0,
                    fixes=Counter(),
                    mistakes=Counter(),
                    task_ids=set(),
                )
                profiles[key] = profile
            profile.support += 1
            profile.fixes.update(fixes)
            profile.mistakes.update(mistakes)
            profile.task_ids.add(task_id)

    candidates: list[PromotionCandidate] = []
    for key, profile in sorted(profiles.items()):
        if profile.support < min_support:
            continue
        fixes = [item for item, _ in sorted(profile.fixes.items(), key=lambda pair: (-pair[1], pair[0]))[:2]]
        mistakes = [item for item, _ in sorted(profile.mistakes.items(), key=lambda pair: (-pair[1], pair[0]))[:2]]
        signal_bits: list[str] = []
        if fixes:
            signal_bits.append("Associated fixes: " + ", ".join(f"`{item}`" for item in fixes) + ".")
        if mistakes:
            signal_bits.append("Mistakes it helps prevent: " + ", ".join(f"`{item}`" for item in mistakes) + ".")
        if not signal_bits:
            signal_bits.append("Structured episodic memory marked this rule as reusable.")
        candidates.append(
            PromotionCandidate(
                source="ledger_memory",
                source_kind="prevention_rule",
                title=profile.text[:1].lower() + profile.text[1:] if profile.text[:1].isalpha() else profile.text,
                context=(
                    f"Derived from {profile.support} kept iteration"
                    f"{'' if profile.support == 1 else 's'} with structured episodic-memory prevention rules"
                    + (
                        f" across {len(profile.task_ids)} tasks."
                        if len(profile.task_ids) > 1
                        else "."
                    )
                ),
                signal=" ".join(signal_bits),
                caveat=(
                    "Derived from one kept episode; review it before treating it as fully durable."
                    if profile.support == 1
                    else "Repeated across kept episodes, but still confirm it is repository-wide rather than task-local."
                ),
                support=profile.support,
                score=profile.support * 25 + len(fixes) * 3 + len(mistakes),
                key=f"memory:{key}",
            )
        )
    candidates.sort(key=lambda item: (-item.score, -item.support, item.title))
    return candidates


def overlap_ratio(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left & right
    if not intersection:
        return 0.0
    return len(intersection) / float(min(len(left), len(right)))


def duplicate_reason(candidate: PromotionCandidate, existing: ExistingPatternFingerprint) -> str | None:
    candidate_title = normalize_title(candidate.title)
    if candidate_title == existing.normalized_title:
        return f"duplicate title of existing pattern `{existing.title}`"

    if candidate.key:
        _, _, raw_key = candidate.key.partition(":")
        focused_existing = " ".join([existing.title_text, existing.signal_text]).strip()
        if raw_key and raw_key.lower() in focused_existing:
            return f"existing pattern `{existing.title}` already references `{raw_key}`"
        key_tokens = token_set(raw_key)
        focused_tokens = token_set(focused_existing)
        if key_tokens and key_tokens.issubset(focused_tokens):
            return f"existing pattern `{existing.title}` already covers the key signals behind `{raw_key}`"

    candidate_tokens = token_set(" ".join([candidate.title, candidate.context, candidate.signal]))
    shared = candidate_tokens & existing.tokens
    if len(shared) >= 4 and overlap_ratio(candidate_tokens, existing.tokens) >= 0.35:
        return f"near-duplicate of existing pattern `{existing.title}`"
    return None


def dedupe_candidates(
    candidates: list[PromotionCandidate],
    *,
    existing: list[ExistingPatternFingerprint],
    limit: int,
) -> tuple[list[PromotionCandidate], list[SkippedCandidate]]:
    promotable: list[PromotionCandidate] = []
    skipped: list[SkippedCandidate] = []
    seen_titles: dict[str, str] = {}

    for candidate in sorted(candidates, key=lambda item: (-item.score, -item.support, item.source, item.title)):
        normalized = normalize_title(candidate.title)
        if normalized in seen_titles:
            skipped.append(
                SkippedCandidate(
                    source=candidate.source,
                    title=candidate.title,
                    reason=f"duplicate generated title of `{seen_titles[normalized]}`",
                )
            )
            continue

        match_reason = None
        for fingerprint in existing:
            match_reason = duplicate_reason(candidate, fingerprint)
            if match_reason is not None:
                break
        if match_reason is not None:
            skipped.append(
                SkippedCandidate(
                    source=candidate.source,
                    title=candidate.title,
                    reason=match_reason,
                )
            )
            continue

        promotable.append(candidate)
        seen_titles[normalized] = candidate.title
        if len(promotable) >= limit:
            break

    return promotable, skipped


def append_patterns(path: Path, candidates: list[PromotionCandidate]) -> list[str]:
    if not candidates:
        return []

    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    blocks = "\n\n".join(candidate.as_markdown_block() for candidate in candidates).rstrip() + "\n"
    if existing.strip():
        updated = existing.rstrip() + "\n\n" + blocks
    else:
        updated = blocks
    path.write_text(updated, encoding="utf-8")
    return [candidate.title for candidate in candidates]


def render_summary(
    ledger_path: Path,
    patterns_path: Path,
    *,
    total_entries: int,
    kept_entries: int,
    existing_pattern_count: int,
    recognition_candidates: list[PromotionCandidate],
    memory_candidates: list[PromotionCandidate],
    promotable: list[PromotionCandidate],
    skipped: list[SkippedCandidate],
    applied: list[str],
) -> str:
    lines = [
        "# Pattern Promotion Report",
        "",
        f"- Ledger: `{ledger_path}`",
        f"- Patterns: `{patterns_path}`",
        f"- Total entries: {total_entries}",
        f"- Kept entries: {kept_entries}",
        f"- Existing durable patterns: {existing_pattern_count}",
        f"- Recognition candidates reviewed: {len(recognition_candidates)}",
        f"- Memory candidates reviewed: {len(memory_candidates)}",
        f"- Promotable candidates: {len(promotable)}",
        f"- Skipped candidates: {len(skipped)}",
        f"- Applied patterns: {len(applied)}",
        "",
    ]
    if promotable:
        for candidate in promotable:
            lines.extend(
                [
                    f"## Promote: {candidate.title}",
                    f"- Source: `{candidate.source}` / `{candidate.source_kind}`",
                    f"- Support: {candidate.support}",
                    f"- Context: {candidate.context}",
                    f"- Signal: {candidate.signal}",
                    f"- Caveat: {candidate.caveat}",
                    "",
                ]
            )
    else:
        lines.append("No new durable patterns cleared the current dedupe and support thresholds.")
        lines.append("")

    if skipped:
        lines.append("## Skipped")
        for candidate in skipped[:5]:
            lines.append(f"- `{candidate.title}`: {candidate.reason}")
        lines.append("")

    if applied:
        lines.append("## Applied")
        for title in applied:
            lines.append(f"- `{title}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(
    ledger_path: Path,
    patterns_path: Path,
    *,
    total_entries: int,
    kept_entries: int,
    existing_pattern_count: int,
    recognition_candidates: list[PromotionCandidate],
    memory_candidates: list[PromotionCandidate],
    promotable: list[PromotionCandidate],
    skipped: list[SkippedCandidate],
    applied: list[str],
) -> str:
    payload = {
        "ledger": str(ledger_path),
        "patterns": str(patterns_path),
        "total_entries": total_entries,
        "kept_entries": kept_entries,
        "existing_pattern_count": existing_pattern_count,
        "recognition_candidates": [candidate.as_dict() for candidate in recognition_candidates],
        "memory_candidates": [candidate.as_dict() for candidate in memory_candidates],
        "promotable_patterns": [candidate.as_dict() for candidate in promotable],
        "skipped_patterns": [candidate.as_dict() for candidate in skipped],
        "applied_patterns": applied,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    args = parse_args()
    entries = load_ledger_entries(args.ledger)
    existing = existing_fingerprints(args.patterns)
    recognition_candidates = build_recognition_candidates(args.ledger, min_support=args.min_support)
    memory_candidates = build_memory_candidates(entries, min_support=args.memory_min_support)
    promotable, skipped = dedupe_candidates(
        [*recognition_candidates, *memory_candidates],
        existing=existing,
        limit=args.limit,
    )
    applied = append_patterns(args.patterns, promotable) if args.apply else []

    total_entries = len(entries)
    kept_entries = sum(1 for entry in entries if entry.get("kept") is True)
    if args.format == "json":
        print(
            render_json(
                args.ledger,
                args.patterns,
                total_entries=total_entries,
                kept_entries=kept_entries,
                existing_pattern_count=len(existing),
                recognition_candidates=recognition_candidates,
                memory_candidates=memory_candidates,
                promotable=promotable,
                skipped=skipped,
                applied=applied,
            ),
            end="",
        )
    else:
        print(
            render_summary(
                args.ledger,
                args.patterns,
                total_entries=total_entries,
                kept_entries=kept_entries,
                existing_pattern_count=len(existing),
                recognition_candidates=recognition_candidates,
                memory_candidates=memory_candidates,
                promotable=promotable,
                skipped=skipped,
                applied=applied,
            ),
            end="",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
