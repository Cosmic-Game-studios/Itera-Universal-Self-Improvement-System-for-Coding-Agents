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
DESIRED_OUTCOME_RE = re.compile(r"^- Desired outcome:\s*(.+?)\s*$", re.M)
TOKEN_RE = re.compile(r"[a-z][a-z0-9_-]{2,}")
STOPWORDS = {
    "about",
    "after",
    "again",
    "agent",
    "agents",
    "also",
    "and",
    "before",
    "between",
    "brief",
    "build",
    "change",
    "changes",
    "checks",
    "claude",
    "code",
    "coding",
    "contract",
    "current",
    "does",
    "done",
    "each",
    "execution",
    "fast",
    "from",
    "full",
    "have",
    "into",
    "iteration",
    "iterations",
    "kept",
    "ledger",
    "make",
    "memory",
    "more",
    "must",
    "next",
    "not",
    "only",
    "pass",
    "pattern",
    "patterns",
    "plan",
    "prevent",
    "procedural",
    "repo",
    "repository",
    "review",
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
    "they",
    "this",
    "those",
    "through",
    "tools",
    "using",
    "with",
    "without",
    "workflow",
    "workflows",
}
PROCEDURAL_MEMORY_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    ".agents/skills/swe-self-improve/SKILL.md",
    ".claude/skills/swe-self-improve/SKILL.md",
)


@dataclass(frozen=True)
class TaskContract:
    task_id: str | None
    task_name: str | None
    task_type: str | None
    desired_outcome: str | None
    non_goals: tuple[str, ...]
    execution_plan: tuple[str, ...]
    constraints: tuple[str, ...]
    memory_refresh: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    path: Path


@dataclass(frozen=True)
class PatternEntry:
    title: str
    context: str
    signal: str
    caveat: str

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "context": self.context,
            "signal": self.signal,
            "caveat": self.caveat,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a memory brief from current-task.md, ledger history, and durable patterns.",
    )
    parser.add_argument("--task", type=Path, default=Path("improvement/current-task.md"), help="Path to current-task.md.")
    parser.add_argument("--ledger", type=Path, default=Path("improvement/ledger.jsonl"), help="Path to improvement/ledger.jsonl.")
    parser.add_argument("--patterns", type=Path, default=Path("improvement/patterns.md"), help="Path to improvement/patterns.md.")
    parser.add_argument("--task-id", help="Override the task id instead of reading it from current-task.md.")
    parser.add_argument("--limit", type=int, default=4, help="Maximum number of related prior episodes to surface.")
    parser.add_argument("--pattern-limit", type=int, default=4, help="Maximum number of learned patterns to surface.")
    parser.add_argument("--format", choices=("summary", "json"), default="summary", help="Output format.")
    return parser.parse_args()


def extract_line(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_name: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current_name = line[3:].strip()
            sections[current_name] = []
            continue
        if current_name is not None:
            sections[current_name].append(line)
    return sections


def section_bullets(lines: list[str]) -> tuple[str, ...]:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return tuple(item for item in bullets if item)


def top_level_bullets_after_label(text: str, label: str) -> tuple[str, ...]:
    lines = text.splitlines()
    target = f"- {label}:"
    for index, raw_line in enumerate(lines):
        if raw_line.strip() != target:
            continue
        bullets: list[str] = []
        for next_line in lines[index + 1 :]:
            stripped = next_line.strip()
            if not stripped:
                if bullets:
                    break
                continue
            if stripped.startswith("## "):
                break
            if stripped.startswith("- "):
                bullets.append(stripped[2:].strip())
                continue
            break
        return tuple(item for item in bullets if item)
    return ()


def load_task_contract(path: Path) -> TaskContract:
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    return TaskContract(
        task_id=extract_line(TASK_ID_RE, text),
        task_name=extract_line(TASK_NAME_RE, text),
        task_type=extract_line(TASK_TYPE_RE, text),
        desired_outcome=extract_line(DESIRED_OUTCOME_RE, text),
        non_goals=top_level_bullets_after_label(text, "Non-goals"),
        execution_plan=section_bullets(sections.get("Execution plan", [])),
        constraints=section_bullets(sections.get("Constraints", [])),
        memory_refresh=section_bullets(sections.get("Memory refresh", [])),
        stop_conditions=section_bullets(sections.get("Stop conditions", [])),
        path=path,
    )


def load_ledger_entries(path: Path) -> list[dict[str, Any]]:
    report = validate_ledger(path)
    if not report.valid:
        raise ValueError("Ledger must be valid before building a memory brief.")

    entries: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def parse_patterns(path: Path) -> list[PatternEntry]:
    title: str | None = None
    context = ""
    signal = ""
    caveat = ""
    patterns: list[PatternEntry] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("## Pattern:"):
            if title is not None:
                patterns.append(PatternEntry(title=title, context=context, signal=signal, caveat=caveat))
            title = line.split(":", 1)[1].strip()
            context = ""
            signal = ""
            caveat = ""
            continue
        stripped = line.strip()
        if stripped.startswith("- Context:"):
            context = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- Signal:"):
            signal = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("- Caveat:"):
            caveat = stripped.split(":", 1)[1].strip()

    if title is not None:
        patterns.append(PatternEntry(title=title, context=context, signal=signal, caveat=caveat))
    return patterns


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


def task_keywords(task: TaskContract) -> set[str]:
    return collect_tokens(
        task.task_name,
        task.task_type,
        task.desired_outcome,
        " ".join(task.non_goals),
        " ".join(task.execution_plan),
        " ".join(task.constraints),
        " ".join(task.stop_conditions),
    )


def memory_lists(entry: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    payload = entry.get("memory")
    if not isinstance(payload, dict):
        return [], [], []

    def strings_for(key: str) -> list[str]:
        value = payload.get(key)
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    return (
        strings_for("mistakes"),
        strings_for("fixes"),
        strings_for("prevention_rules"),
    )


def entry_score(entry: dict[str, Any], keywords: set[str]) -> int:
    primary_metric = entry.get("primary_metric")
    primary_metric_name = ""
    if isinstance(primary_metric, dict):
        primary_metric_name = str(primary_metric.get("name", "")).strip()
    mistakes, fixes, prevention_rules = memory_lists(entry)
    entry_tokens = collect_tokens(
        str(entry.get("task_id", "")),
        str(entry.get("hypothesis", "")),
        str(entry.get("summary", "")),
        primary_metric_name,
        " ".join(str(item) for item in entry.get("changes", []) if str(item).strip()),
        " ".join(mistakes),
        " ".join(fixes),
        " ".join(prevention_rules),
    )
    overlap = len(keywords & entry_tokens)
    memory_bonus = len(mistakes) + len(fixes) + len(prevention_rules)
    kept_bonus = 2 if entry.get("kept") is True else 0
    return overlap * 10 + memory_bonus * 2 + kept_bonus


def dedupe(items: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


def select_related_entries(
    task_id: str | None,
    entries: list[dict[str, Any]],
    keywords: set[str],
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    same_task = [entry for entry in entries if entry.get("task_id") == task_id]
    same_task.sort(key=lambda entry: int(entry.get("iteration", -1)))

    scored_other_entries: list[tuple[int, int, dict[str, Any]]] = []
    for index, entry in enumerate(entries):
        if entry.get("task_id") == task_id:
            continue
        score = entry_score(entry, keywords)
        if score <= 0:
            continue
        scored_other_entries.append((score, index, entry))

    scored_other_entries.sort(key=lambda item: (item[0], item[1]), reverse=True)
    related = [entry for _, _, entry in scored_other_entries[:limit]]
    return same_task, related


def score_patterns(patterns: list[PatternEntry], keywords: set[str], limit: int) -> list[dict[str, Any]]:
    scored: list[tuple[int, int, PatternEntry]] = []
    for index, pattern in enumerate(patterns):
        score = len(
            keywords
            & collect_tokens(pattern.title, pattern.context, pattern.signal, pattern.caveat)
        )
        scored.append((score, index, pattern))
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)

    top = [pattern for score, _, pattern in scored if score > 0][:limit]
    if not top:
        top = patterns[:limit]
    return [pattern.as_dict() for pattern in top]


def summarize_episode(entry: dict[str, Any]) -> dict[str, Any]:
    mistakes, fixes, prevention_rules = memory_lists(entry)
    return {
        "task_id": entry.get("task_id"),
        "iteration": entry.get("iteration"),
        "kept": entry.get("kept"),
        "hypothesis": entry.get("hypothesis"),
        "summary": entry.get("summary"),
        "mistakes": mistakes,
        "fixes": fixes,
        "prevention_rules": prevention_rules,
    }


def procedural_rules(root: Path) -> list[str]:
    texts = []
    for rel in PROCEDURAL_MEMORY_PATHS:
        path = root / rel
        if path.exists():
            texts.append(path.read_text(encoding="utf-8").lower())
    combined = "\n".join(texts)
    rules: list[str] = []
    if "execution plan" in combined:
        rules.append("Create an execution plan before major edits.")
    if "baseline" in combined:
        rules.append("Run and log a baseline before meaningful changes when a credible eval exists.")
    if "one hypothesis" in combined:
        rules.append("Work on one hypothesis at a time.")
    if "validate_ledger" in combined or "ledger validator" in combined:
        rules.append("Validate the ledger after appending iteration history.")
    if "memory_context.py" in combined or "working memory" in combined:
        rules.append("Refresh the four memory layers before forming the next hypothesis or task plan.")
    return rules


def build_memory_brief(
    task: TaskContract,
    entries: list[dict[str, Any]],
    patterns: list[PatternEntry],
    *,
    task_id: str | None,
    related_limit: int,
    pattern_limit: int,
    root: Path,
) -> dict[str, Any]:
    keywords = task_keywords(task)
    same_task, related = select_related_entries(task_id, entries, keywords, related_limit)
    same_task_summaries = [summarize_episode(entry) for entry in same_task]
    related_summaries = [summarize_episode(entry) for entry in related]

    mistakes = dedupe(
        [item for episode in [*same_task_summaries, *related_summaries] for item in episode["mistakes"]],
        limit=6,
    )
    fixes = dedupe(
        [item for episode in [*same_task_summaries, *related_summaries] for item in episode["fixes"]],
        limit=6,
    )
    prevention_rules = dedupe(
        [item for episode in [*same_task_summaries, *related_summaries] for item in episode["prevention_rules"]],
        limit=6,
    )
    learned_patterns = score_patterns(patterns, keywords, pattern_limit)
    procedure_rules = procedural_rules(root)

    recommended_refresh = dedupe(
        [
            "Review the current-task contract before broad edits so the goal and non-goals stay active.",
            *[f"Avoid repeating: {item}" for item in mistakes[:2]],
            *[f"Reuse this fix: {item}" for item in fixes[:2]],
            *prevention_rules[:3],
            *[
                f"Pattern to remember: {pattern['title']}."
                for pattern in learned_patterns[:2]
                if isinstance(pattern, dict) and pattern.get("title")
            ],
            *procedure_rules[:2],
        ],
        limit=8,
    )

    return {
        "task_id": task_id,
        "working_memory": {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "desired_outcome": task.desired_outcome,
            "non_goals": list(task.non_goals),
            "execution_plan": list(task.execution_plan),
            "constraints": list(task.constraints),
            "memory_refresh": list(task.memory_refresh),
            "stop_conditions": list(task.stop_conditions),
            "task_path": str(task.path),
        },
        "episodic_memory": {
            "same_task_history": same_task_summaries,
            "related_history": related_summaries,
            "mistakes_to_avoid": mistakes,
            "reusable_fixes": fixes,
            "prevention_rules": prevention_rules,
        },
        "learned_memory": {
            "patterns": learned_patterns,
            "patterns_path": str(root / "improvement" / "patterns.md"),
        },
        "procedural_memory": {
            "paths": [str(root / rel) for rel in PROCEDURAL_MEMORY_PATHS if (root / rel).exists()],
            "rules": procedure_rules,
        },
        "recommended_refresh": recommended_refresh,
    }


def render_summary(brief: dict[str, Any]) -> str:
    working = brief["working_memory"]
    episodic = brief["episodic_memory"]
    learned = brief["learned_memory"]
    procedural = brief["procedural_memory"]

    lines = [
        "# Memory Brief",
        "",
        f"- Task ID: {brief.get('task_id') or working.get('task_id') or 'unknown'}",
        f"- Task name: {working.get('task_name') or 'unknown'}",
        f"- Task type: {working.get('task_type') or 'unknown'}",
        f"- Desired outcome: {working.get('desired_outcome') or 'unknown'}",
        "",
        "## Working memory",
    ]
    for item in working.get("execution_plan", [])[:4]:
        lines.append(f"- Plan step: {item}")
    for item in working.get("constraints", [])[:3]:
        lines.append(f"- Constraint: {item}")

    lines.extend(["", "## Episodic memory"])
    lines.append(f"- Same-task entries reviewed: {len(episodic.get('same_task_history', []))}")
    lines.append(f"- Related prior episodes reviewed: {len(episodic.get('related_history', []))}")
    for item in episodic.get("mistakes_to_avoid", [])[:3]:
        lines.append(f"- Mistake to avoid: {item}")
    for item in episodic.get("reusable_fixes", [])[:3]:
        lines.append(f"- Reusable fix: {item}")
    for item in episodic.get("prevention_rules", [])[:3]:
        lines.append(f"- Prevention rule: {item}")

    lines.extend(["", "## Learned memory"])
    for pattern in learned.get("patterns", [])[:3]:
        if isinstance(pattern, dict):
            lines.append(f"- Pattern: {pattern.get('title', 'unknown')}")
            signal = str(pattern.get("signal", "")).strip()
            if signal:
                lines.append(f"- Signal: {signal}")

    lines.extend(["", "## Procedural memory"])
    for item in procedural.get("rules", [])[:4]:
        lines.append(f"- Rule: {item}")

    lines.extend(["", "## Recommended refresh"])
    for item in brief.get("recommended_refresh", [])[:6]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    task = load_task_contract(args.task)
    entries = load_ledger_entries(args.ledger)
    patterns = parse_patterns(args.patterns)
    root = args.task.resolve().parents[1]
    task_id = args.task_id or task.task_id
    brief = build_memory_brief(
        task,
        entries,
        patterns,
        task_id=task_id,
        related_limit=max(args.limit, 0),
        pattern_limit=max(args.pattern_limit, 0),
        root=root,
    )
    if args.format == "json":
        print(json.dumps(brief, indent=2, sort_keys=True))
    else:
        print(render_summary(brief), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
