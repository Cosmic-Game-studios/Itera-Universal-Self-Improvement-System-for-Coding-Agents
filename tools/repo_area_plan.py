from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IGNORED_DIRS = {".git", "__pycache__"}
IGNORED_FILES = {".DS_Store"}
AREA_WEIGHTS = {
    ".agents/": 1.4,
    ".claude/": 1.4,
    "qa/": 1.3,
    "tools/": 1.2,
    "improvement/": 1.1,
    "global-templates/": 1.0,
    "[root]": 1.0,
}
AREA_FOCUS = {
    ".agents/": "Codex skill rules, invocation config, and task adapters",
    ".claude/": "Claude skill parity and Claude-specific workflow behavior",
    "qa/": "structural verification, regression checks, and test safety",
    "tools/": "support tooling for planning, validation, and pattern extraction",
    "improvement/": "task contracts, ledgers, durable patterns, and templates",
    "global-templates/": "cross-repository starter defaults for Codex and Claude",
    "[root]": "top-level project docs, policies, and entrypoint guidance",
}


@dataclass(frozen=True)
class AreaPlan:
    area: str
    files: int
    weight: float
    score: float
    suggested_runs: int
    extensions: tuple[tuple[str, int], ...]
    notable_files: tuple[str, ...]
    focus: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "area": self.area,
            "files": self.files,
            "weight": self.weight,
            "score": round(self.score, 2),
            "suggested_runs": self.suggested_runs,
            "extensions": list(self.extensions),
            "notable_files": list(self.notable_files),
            "focus": self.focus,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a deterministic multi-area run plan for large repository sweeps.",
    )
    parser.add_argument("--root", type=Path, required=True, help="Repository root to scan.")
    parser.add_argument("--budget", type=int, default=600, help="Total run budget to distribute.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format.")
    return parser.parse_args()


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in IGNORED_FILES or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return files


def normalize_area(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    if len(rel.parts) == 1:
        return "[root]"
    return f"{rel.parts[0]}/"


def extension_name(path: Path) -> str:
    if path.suffix:
        return path.suffix
    return "[no extension]"


def area_weight(area: str) -> float:
    return AREA_WEIGHTS.get(area, 1.0)


def focus_for_area(area: str) -> str:
    return AREA_FOCUS.get(area, "files in this area should be swept as one bounded workstream")


def allocate_runs(scores: dict[str, float], budget: int) -> dict[str, int]:
    if budget <= 0:
        raise ValueError("budget must be greater than 0")
    ordered_areas = sorted(scores)
    if not ordered_areas:
        return {}
    if budget < len(ordered_areas):
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        allocation = {area: 0 for area in ordered_areas}
        for area, _ in ranked[:budget]:
            allocation[area] += 1
        return allocation

    allocation = {area: 1 for area in ordered_areas}
    remaining = budget - len(ordered_areas)
    total_score = sum(scores.values())
    raw_shares: dict[str, float] = {}
    for area in ordered_areas:
        raw = (scores[area] / total_score) * remaining if total_score else 0.0
        raw_shares[area] = raw
        allocation[area] += int(raw)

    assigned = sum(allocation.values())
    leftovers = budget - assigned
    ranked_remainders = sorted(
        ordered_areas,
        key=lambda area: (-(raw_shares[area] - int(raw_shares[area])), -scores[area], area),
    )
    for area in ranked_remainders[:leftovers]:
        allocation[area] += 1
    return allocation


def build_area_plans(root: Path, budget: int) -> list[AreaPlan]:
    files = iter_files(root)
    grouped_files: dict[str, list[Path]] = {}
    for path in files:
        grouped_files.setdefault(normalize_area(root, path), []).append(path)

    scores = {
        area: len(area_files) * area_weight(area)
        for area, area_files in grouped_files.items()
    }
    allocation = allocate_runs(scores, budget)
    plans: list[AreaPlan] = []
    for area, area_files in grouped_files.items():
        ext_counts = Counter(extension_name(path) for path in area_files)
        notable = tuple(
            str(path.relative_to(root))
            for path in sorted(area_files, key=lambda item: str(item.relative_to(root)))[:5]
        )
        plans.append(
            AreaPlan(
                area=area,
                files=len(area_files),
                weight=area_weight(area),
                score=scores[area],
                suggested_runs=allocation[area],
                extensions=tuple(sorted(ext_counts.items(), key=lambda item: (-item[1], item[0]))[:5]),
                notable_files=notable,
                focus=focus_for_area(area),
            )
        )
    plans.sort(key=lambda plan: (-plan.suggested_runs, -plan.score, plan.area))
    return plans


def render_markdown(root: Path, budget: int, plans: list[AreaPlan]) -> str:
    lines = [
        "# Repo Area Plan",
        "",
        f"- Root: `{root}`",
        f"- Total budget: {budget}",
        f"- Areas: {len(plans)}",
        "",
        "Suggested order: start with the highest-budget areas, but keep each area internally bounded.",
        "",
    ]
    for plan in plans:
        ext_summary = ", ".join(f"`{ext}` {count}" for ext, count in plan.extensions) or "none"
        notable_summary = ", ".join(f"`{path}`" for path in plan.notable_files) or "none"
        lines.extend(
            [
                f"## Area: {plan.area}",
                f"- Suggested runs: {plan.suggested_runs}",
                f"- Files: {plan.files}",
                f"- Score: {plan.score:.1f}",
                f"- Focus: {plan.focus}",
                f"- Extensions: {ext_summary}",
                f"- Notable files: {notable_summary}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_json(root: Path, budget: int, plans: list[AreaPlan]) -> str:
    payload = {
        "root": str(root),
        "budget": budget,
        "areas": [plan.as_dict() for plan in plans],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    args = parse_args()
    plans = build_area_plans(args.root.resolve(), args.budget)
    if args.format == "json":
        print(render_json(args.root.resolve(), args.budget, plans), end="")
    else:
        print(render_markdown(args.root.resolve(), args.budget, plans), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
