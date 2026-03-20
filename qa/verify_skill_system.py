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
    "improvement/templates/ledger-entry.json",
    "tools/pattern_recognition.py",
    "tools/repo_area_plan.py",
    "tools/validate_ledger.py",
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
global_codex = read("global-templates/codex-home-AGENTS.md")
global_claude = read("global-templates/claude-home-CLAUDE.md")
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
for name, text in [
    ("codex_skill_requires_execution_plan", codex_skill),
    ("claude_skill_requires_execution_plan", claude_skill),
    ("agents_require_execution_plan", agents),
    ("claude_require_execution_plan", claude),
    ("global_codex_requires_execution_plan", global_codex),
    ("global_claude_requires_execution_plan", global_claude),
    ("readme_mentions_execution_plan", readme),
]:
    add(name, "execution plan" in text.lower(), "mentions execution plan explicitly")
for name, text in [
    ("codex_skill_mentions_program_mode", codex_skill),
    ("claude_skill_mentions_program_mode", claude_skill),
    ("agents_mention_program_mode", agents),
    ("claude_mention_program_mode", claude),
    ("global_codex_mentions_program_mode", global_codex),
    ("global_claude_mentions_program_mode", global_claude),
    ("readme_mentions_program_mode", readme),
]:
    add(name, "program mode" in text.lower(), "mentions large-program mode explicitly")

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
    "readme_mentions_ledger_helper",
    "## ledger contract helper" in readme.lower() and "tools/validate_ledger.py" in readme,
    "README documents the ledger contract helper",
)
add(
    "readme_mentions_20_run_self_application",
    "## 20-run self-application" in readme.lower() and "small reversible hypotheses" in readme.lower(),
    "README documents how to run a bounded 20-run self-application program",
)
for name, text in [
    ("codex_skill_mentions_ledger_validation", codex_skill),
    ("claude_skill_mentions_ledger_validation", claude_skill),
    ("agents_mention_ledger_validation", agents),
    ("claude_mention_ledger_validation", claude),
    ("global_codex_mentions_ledger_validation", global_codex),
    ("global_claude_mentions_ledger_validation", global_claude),
]:
    add(
        name,
        "validate_ledger" in text.lower() or "ledger validator" in text.lower(),
        "mentions ledger validation explicitly",
    )

# Live task contract
required_task_sections = [
    "## Execution plan",
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
add(
    "template_has_execution_plan",
    "## Execution plan" in current_task,
    "improvement/templates/current-task.md includes an execution plan section",
)
add(
    "live_task_has_execution_plan",
    "## Execution plan" in read("improvement/current-task.md"),
    "improvement/current-task.md includes an execution plan section",
)
add(
    "template_mentions_area_coverage",
    "## Optional: Area coverage plan" in current_task and "## Optional: Run budget allocation" in current_task,
    "improvement/templates/current-task.md includes optional area coverage and run budget sections",
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

repo_area_planner_ok = False
repo_area_planner_budget_ok = False
repo_area_planner_has_areas = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "repo_area_plan.py"),
            "--root",
            str(ROOT),
            "--budget",
            "600",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    planner_payload = json.loads(result.stdout)
    if isinstance(planner_payload, dict):
        repo_area_planner_ok = True
        areas = planner_payload.get("areas", [])
        repo_area_planner_has_areas = isinstance(areas, list) and len(areas) > 0
        repo_area_planner_budget_ok = sum(
            area.get("suggested_runs", 0)
            for area in areas
            if isinstance(area, dict)
        ) == 600
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    repo_area_planner_ok = False

add(
    "repo_area_planner_executes",
    repo_area_planner_ok,
    "repo area planner executes and returns JSON for a 600-run sweep",
)
add(
    "repo_area_planner_allocates_budget",
    repo_area_planner_ok and repo_area_planner_has_areas and repo_area_planner_budget_ok,
    "repo area planner returns at least one area and allocates the full 600-run budget",
)

ledger_validator_live_ok = False
ledger_validator_live_matches_count = False
ledger_validator_template_ok = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_ledger.py"),
            "--ledger",
            str(ROOT / "improvement" / "ledger.jsonl"),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    validator_payload = json.loads(result.stdout)
    if isinstance(validator_payload, dict):
        ledger_validator_live_ok = validator_payload.get("valid") is True
        ledger_validator_live_matches_count = validator_payload.get("entry_count") == len(ledger_payloads)
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    ledger_validator_live_ok = False

try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_ledger.py"),
            "--ledger",
            str(ROOT / "improvement" / "templates" / "ledger-entry.json"),
            "--single-json",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    template_payload = json.loads(result.stdout)
    if isinstance(template_payload, dict):
        ledger_validator_template_ok = template_payload.get("valid") is True and template_payload.get("entry_count") == 1
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    ledger_validator_template_ok = False

add(
    "ledger_validator_live_passes",
    ledger_validator_live_ok and ledger_validator_live_matches_count,
    "ledger validator passes on the live ledger and reports the correct entry count",
)
add(
    "ledger_validator_template_passes",
    ledger_validator_template_ok,
    "ledger validator passes on the example ledger-entry template",
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
