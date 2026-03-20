from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
checks: list[tuple[str, bool, str]] = []


def add(name: str, ok: bool, detail: str) -> None:
    checks.append((name, ok, detail))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


# Core files
for rel in [
    "AGENTS.md",
    "CLAUDE.md",
    ".agents/skills/swe-self-improve/SKILL.md",
    ".claude/skills/swe-self-improve/SKILL.md",
    ".agents/skills/swe-self-improve/agents/openai.yaml",
    ".agents/skills/swe-self-improve/references/eval-catalog.md",
    ".claude/skills/swe-self-improve/references/eval-catalog.md",
    "global-templates/codex-home-AGENTS.md",
    "global-templates/claude-home-CLAUDE.md",
    "improvement/current-task.md",
    "improvement/patterns.md",
    "improvement/templates/current-task.md",
    "improvement/templates/eval-contract.md",
    "tools/pattern_recognition.py",
]:
    add(
        f"exists:{rel}",
        exists(rel),
        "required file present" if exists(rel) else "missing required file",
    )

codex_skill = read(".agents/skills/swe-self-improve/SKILL.md")
claude_skill = read(".claude/skills/swe-self-improve/SKILL.md")
readme = read("README.md")
agents = read("AGENTS.md")
claude = read("CLAUDE.md")
eval_catalog = read(".agents/skills/swe-self-improve/references/eval-catalog.md")
current_task = read("improvement/templates/current-task.md")
eval_contract = read("improvement/templates/eval-contract.md")
patterns = read("improvement/patterns.md")
ledger_lines = read("improvement/ledger.jsonl").splitlines()

# Frontmatter / policy
add(
    "codex_skill_has_name",
    bool(re.search(r"^name:\s*swe-self-improve\s*$", codex_skill, re.M)),
    "Codex skill has name frontmatter",
)
add(
    "codex_skill_has_description",
    "description:" in codex_skill.split("---", 2)[1],
    "Codex skill has description frontmatter",
)
add(
    "claude_skill_manual_only",
    "disable-model-invocation: true" in claude_skill,
    "Claude skill is manual-only",
)
add(
    "codex_manual_only",
    "allow_implicit_invocation: false"
    in read(".agents/skills/swe-self-improve/agents/openai.yaml"),
    "Codex skill disables implicit invocation",
)

# Size safety
add(
    "claude_skill_under_500_lines",
    len(claude_skill.splitlines()) < 500,
    f"Claude skill has {len(claude_skill.splitlines())} lines",
)
add(
    "project_claude_under_200_lines",
    len(claude.splitlines()) < 200,
    f"Project CLAUDE.md has {len(claude.splitlines())} lines",
)

# Tiered evaluation
for name, text, phrase in [
    ("agents_mentions_fast_loop", agents, "fast-loop"),
    ("claude_mentions_fast_loop", claude, "fast-loop"),
    ("skill_mentions_fast_loop", codex_skill, "fast-loop"),
    ("template_has_fast_loop", current_task, "fast-loop"),
    ("template_has_full_gates", current_task, "full gates"),
    ("eval_contract_has_full_gates", eval_contract, "full gates"),
]:
    add(name, phrase in text.lower(), f"contains {phrase}")

# Universal coverage heuristic
combined = "\n".join([codex_skill, eval_catalog, readme]).lower()
scenario_keywords = {
    "bugfix": ["bug", "reproduction"],
    "feature": ["feature", "acceptance"],
    "frontend": ["frontend", "accessibility"],
    "backend": ["backend", "api"],
    "ml": ["model training", "validation metric"],
    "perf": ["performance", "benchmark"],
    "refactor": ["refactor", "behavior-lock"],
    "infra": ["infra", "deployment"],
    "data": ["data", "etl"],
}
for scenario, kws in scenario_keywords.items():
    ok = all(kw in combined for kw in kws)
    add(f"scenario:{scenario}", ok, f"keywords: {', '.join(kws)}")

# Global install documentation
add(
    "readme_mentions_global_paths",
    "~/.codex/agents.md" in readme.lower() and "~/.claude/claude.md" in readme.lower(),
    "README documents global install paths",
)
add(
    "global_templates_readme_exists",
    exists("global-templates/README.md"),
    "global template README exists",
)
add(
    "readme_mentions_pattern_helper",
    "## pattern recognition helper" in readme.lower() and "tools/pattern_recognition.py" in readme,
    "README documents the pattern recognition helper",
)
add(
    "readme_mentions_20_run_self_application",
    "## 20-run self-application" in readme.lower() and "small reversible hypotheses" in readme.lower(),
    "README documents how to run a bounded 20-run self-application program",
)

# Live task contract
required_task_sections = [
    "## Constraints",
    "## Fast-loop evals",
    "## Full gates",
    "## Primary metric",
    "## Secondary metrics",
    "## Evaluation commands",
    "## Measurement notes",
    "## Iteration budget",
    "## Rollback / checkpoint strategy",
    "## Stop conditions",
]
add(
    "current_task_has_metadata",
    all(marker in read("improvement/current-task.md") for marker in ["- Task ID:", "- Task name:", "- Task type:"]),
    "improvement/current-task.md includes live task metadata",
)
add(
    "current_task_has_core_sections",
    all(section in read("improvement/current-task.md") for section in required_task_sections),
    "improvement/current-task.md includes the core self-improvement contract sections",
)

# Ledger integrity
ledger_payloads: list[dict[str, object]] = []
ledger_json_valid = True
ledger_shape_valid = True
for raw_line in ledger_lines:
    line = raw_line.strip()
    if not line:
        continue
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        ledger_json_valid = False
        break
    if not isinstance(payload, dict):
        ledger_shape_valid = False
        continue
    ledger_payloads.append(payload)
    if not isinstance(payload.get("task_id"), str):
        ledger_shape_valid = False
    if not isinstance(payload.get("iteration"), int):
        ledger_shape_valid = False
    if not isinstance(payload.get("kept"), bool):
        ledger_shape_valid = False
add(
    "ledger_jsonl_valid",
    ledger_json_valid,
    "improvement/ledger.jsonl parses as JSONL",
)
add(
    "ledger_entries_have_core_fields",
    ledger_json_valid and ledger_shape_valid,
    "ledger entries contain string task_id, int iteration, and bool kept fields",
)

pattern_tool_ok = False
pattern_tool_has_suggestions = False
pattern_tool_matches_ledger = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "pattern_recognition.py"),
            "--ledger",
            str(ROOT / "improvement" / "ledger.jsonl"),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    pattern_payload = json.loads(result.stdout)
    if isinstance(pattern_payload, dict):
        pattern_tool_ok = True
        suggestions = pattern_payload.get("suggested_patterns", [])
        pattern_tool_has_suggestions = isinstance(suggestions, list) and len(suggestions) > 0
        pattern_tool_matches_ledger = pattern_payload.get("total_entries") == len(ledger_payloads)
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    pattern_tool_ok = False

add(
    "pattern_helper_json_executes",
    pattern_tool_ok,
    "pattern recognition helper executes and returns JSON on the live ledger",
)
add(
    "pattern_helper_returns_suggestions",
    pattern_tool_ok and pattern_tool_has_suggestions and pattern_tool_matches_ledger,
    "pattern helper returns at least one suggestion and reports the live ledger size correctly",
)

# Durable patterns
real_pattern_count = len(re.findall(r"^## Pattern: (?!<).+", patterns, re.M))
pattern_sections = [
    section
    for section in re.split(r"^## Pattern: ", patterns, flags=re.M)[1:]
    if not section.startswith("<")
]
pattern_fields_ok = True
for section in pattern_sections:
    if not all(field in section for field in ["- Context:", "- Signal:", "- Caveat:"]):
        pattern_fields_ok = False
        break
add(
    "patterns_has_real_entries",
    real_pattern_count > 0,
    f"improvement/patterns.md has {real_pattern_count} durable pattern entries",
)
add(
    "patterns_use_recommended_fields",
    pattern_fields_ok and len(pattern_sections) == real_pattern_count,
    "each durable pattern uses Context, Signal, and Caveat fields",
)

# Workflow redundancy
add(
    "agents_has_skill_fallback",
    "if the skill is not active" in agents.lower(),
    "AGENTS encodes fallback workflow when skill is not active",
)
add(
    "claude_has_skill_fallback",
    "if the skill is not active" in claude.lower(),
    "CLAUDE encodes fallback workflow when skill is not active",
)

failed = [c for c in checks if not c[1]]
passed = [c for c in checks if c[1]]

print("# Skill System QA Report")
print()
print(f"- Passed: {len(passed)}")
print(f"- Failed: {len(failed)}")
print()
for name, ok, detail in checks:
    icon = "PASS" if ok else "FAIL"
    print(f"- [{icon}] {name}: {detail}")

if failed:
    sys.exit(1)
