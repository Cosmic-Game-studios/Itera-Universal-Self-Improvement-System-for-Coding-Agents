from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

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
    "improvement/templates/hypothesis-backlog.json",
    "improvement/templates/ledger-entry.json",
    "tools/bootstrap_task.py",
    "tools/memory_context.py",
    "tools/loop_state.py",
    "tools/log_iteration.py",
    "tools/pattern_recognition.py",
    "tools/promote_patterns.py",
    "tools/rank_hypotheses.py",
    "tools/repo_area_plan.py",
    "tools/score_iteration.py",
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
live_task = read("improvement/current-task.md")
ledger_lines = read("improvement/ledger.jsonl").splitlines()
live_task_id_match = re.search(r"^- Task ID:\s*(.+?)\s*$", live_task, re.M)
live_task_id = live_task_id_match.group(1).strip() if live_task_id_match else None

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
    "readme_mentions_pattern_promotion_helper",
    "## pattern promotion helper" in readme.lower() and "tools/promote_patterns.py" in readme,
    "README documents the pattern promotion helper",
)
add(
    "readme_mentions_ledger_helper",
    "## ledger contract helper" in readme.lower() and "tools/validate_ledger.py" in readme,
    "README documents the ledger contract helper",
)
add(
    "readme_mentions_bootstrap_helper",
    "## task bootstrap helper" in readme.lower() and "tools/bootstrap_task.py" in readme,
    "README documents the task bootstrap helper",
)
add(
    "readme_mentions_log_iteration_helper",
    "## iteration logging helper" in readme.lower() and "tools/log_iteration.py" in readme,
    "README documents the iteration logging helper",
)
add(
    "readme_mentions_memory_helper",
    "## memory brief helper" in readme.lower() and "tools/memory_context.py" in readme,
    "README documents the memory brief helper",
)
add(
    "readme_mentions_score_helper",
    "## iteration scoring helper" in readme.lower() and "tools/score_iteration.py" in readme,
    "README documents the iteration scoring helper",
)
add(
    "readme_mentions_loop_state_helper",
    "## loop state helper" in readme.lower() and "tools/loop_state.py" in readme,
    "README documents the loop state helper",
)
add(
    "readme_mentions_hypothesis_ranking_helper",
    "## hypothesis ranking helper" in readme.lower() and "tools/rank_hypotheses.py" in readme,
    "README documents the hypothesis ranking helper",
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
for name, text in [
    ("codex_skill_mentions_memory_model", codex_skill),
    ("claude_skill_mentions_memory_model", claude_skill),
    ("agents_mention_memory_model", agents),
    ("claude_mention_memory_model", claude),
    ("global_codex_mentions_memory_model", global_codex),
    ("global_claude_mentions_memory_model", global_claude),
    ("readme_mentions_memory_model", readme),
]:
    lowered = text.lower()
    add(
        name,
        all(phrase in lowered for phrase in ["working memory", "episodic memory", "procedural memory"])
        and ("learned memory" in lowered or "durable lessons" in lowered),
        "mentions the four-memory model explicitly",
    )
for name, text in [
    ("codex_skill_mentions_score_helper", codex_skill),
    ("claude_skill_mentions_score_helper", claude_skill),
    ("agents_mention_score_helper", agents),
    ("claude_mention_score_helper", claude),
    ("global_codex_mentions_score_helper", global_codex),
    ("global_claude_mentions_score_helper", global_claude),
    ("readme_mentions_score_helper_usage", readme),
]:
    add(
        name,
        "score_iteration.py" in text.lower() or "iteration scoring helper" in text.lower(),
        "mentions the iteration scoring helper explicitly",
    )
for name, text in [
    ("codex_skill_mentions_hypothesis_ranking", codex_skill),
    ("claude_skill_mentions_hypothesis_ranking", claude_skill),
    ("agents_mention_hypothesis_ranking", agents),
    ("claude_mention_hypothesis_ranking", claude),
    ("global_codex_mentions_hypothesis_ranking", global_codex),
    ("global_claude_mentions_hypothesis_ranking", global_claude),
    ("readme_mentions_hypothesis_ranking_usage", readme),
]:
    add(
        name,
        "rank_hypotheses.py" in text.lower() or "hypothesis ranking helper" in text.lower(),
        "mentions the hypothesis ranking helper explicitly",
    )
for name, text in [
    ("codex_skill_mentions_pattern_promotion", codex_skill),
    ("claude_skill_mentions_pattern_promotion", claude_skill),
    ("agents_mention_pattern_promotion", agents),
    ("claude_mention_pattern_promotion", claude),
    ("global_codex_mentions_pattern_promotion", global_codex),
    ("global_claude_mentions_pattern_promotion", global_claude),
    ("readme_mentions_pattern_promotion_usage", readme),
]:
    add(
        name,
        "promote_patterns.py" in text.lower() or "pattern promotion helper" in text.lower(),
        "mentions the pattern promotion helper explicitly",
    )
for name, text in [
    ("codex_skill_mentions_loop_review", codex_skill),
    ("claude_skill_mentions_loop_review", claude_skill),
    ("agents_mention_loop_review", agents),
    ("claude_mention_loop_review", claude),
    ("global_codex_mentions_loop_review", global_codex),
    ("global_claude_mentions_loop_review", global_claude),
]:
    add(
        name,
        "loop_state.py" in text.lower()
        or "loop state" in text.lower()
        or "loop-state" in text.lower()
        or "loop-review" in text.lower(),
        "mentions loop-state review explicitly",
    )

# Live task contract
required_task_sections = [
    "## Execution plan",
    "## Constraints",
    "## Memory refresh",
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
    all(marker in live_task for marker in ["- Task ID:", "- Task name:", "- Task type:"]),
    "improvement/current-task.md includes live task metadata",
)
add(
    "current_task_has_core_sections",
    all(section in live_task for section in required_task_sections),
    "improvement/current-task.md includes the core self-improvement contract sections",
)
add(
    "template_has_execution_plan",
    "## Execution plan" in current_task,
    "improvement/templates/current-task.md includes an execution plan section",
)
add(
    "live_task_has_execution_plan",
    "## Execution plan" in live_task,
    "improvement/current-task.md includes an execution plan section",
)
add(
    "template_mentions_area_coverage",
    "## Optional: Area coverage plan" in current_task and "## Optional: Run budget allocation" in current_task,
    "improvement/templates/current-task.md includes optional area coverage and run budget sections",
)
add(
    "eval_contract_mentions_score_helper",
    "score_iteration.py" in eval_contract.lower(),
    "improvement/templates/eval-contract.md mentions the iteration scoring helper",
)
add(
    "eval_contract_mentions_hypothesis_ranking",
    "rank_hypotheses.py" in eval_contract.lower(),
    "improvement/templates/eval-contract.md mentions the hypothesis ranking helper",
)
add(
    "template_has_memory_refresh",
    "## Memory refresh" in current_task,
    "improvement/templates/current-task.md includes a memory refresh section",
)
add(
    "template_mentions_ranking_command",
    "ranking command" in current_task.lower() and "rank_hypotheses.py" in current_task.lower(),
    "improvement/templates/current-task.md includes a ranking-command reminder",
)
add(
    "template_mentions_promotion_command",
    "promotion command" in current_task.lower() and "promote_patterns.py" in current_task.lower(),
    "improvement/templates/current-task.md includes a promotion-command reminder",
)
add(
    "live_task_has_memory_refresh",
    "## Memory refresh" in live_task,
    "improvement/current-task.md includes a memory refresh section",
)
add(
    "eval_contract_mentions_pattern_promotion",
    "promote_patterns.py" in eval_contract.lower(),
    "improvement/templates/eval-contract.md mentions the pattern promotion helper",
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

promotion_helper_ok = False
promotion_helper_reports_counts = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "promote_patterns.py"),
            "--ledger",
            str(ROOT / "improvement" / "ledger.jsonl"),
            "--patterns",
            str(ROOT / "improvement" / "patterns.md"),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    promotion_payload = json.loads(result.stdout)
    if isinstance(promotion_payload, dict):
        promotion_helper_ok = True
        promotion_helper_reports_counts = (
            promotion_payload.get("total_entries") == len(ledger_payloads)
            and isinstance(promotion_payload.get("promotable_patterns"), list)
            and isinstance(promotion_payload.get("skipped_patterns"), list)
        )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    promotion_helper_ok = False

add(
    "pattern_promotion_helper_executes",
    promotion_helper_ok,
    "pattern promotion helper executes and returns JSON on the live ledger and patterns",
)
add(
    "pattern_promotion_helper_reports_counts",
    promotion_helper_ok and promotion_helper_reports_counts,
    "pattern promotion helper reports live entry counts plus promotable and skipped candidate lists",
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

bootstrap_helper_executes = False
bootstrap_helper_writes_contract = False
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "current-task.md"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "bootstrap_task.py"),
                "--task-id",
                "2026-03-20-demo-task",
                "--task-name",
                "Demo task",
                "--task-type",
                "feature",
                "--desired-outcome",
                "Scaffold a task contract",
                "--plan-step",
                "Draft the contract",
                "--fast-eval",
                "python3 qa/verify_skill_system.py",
                "--full-gate",
                "python3 qa/verify_skill_system.py",
                "--primary-metric-name",
                "quality",
                "--primary-metric-direction",
                "higher_is_better",
                "--primary-metric-baseline",
                "not started",
                "--primary-metric-target",
                "scaffolded",
                "--output",
                str(output),
                "--overwrite",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        bootstrap_helper_executes = output.exists()
        if bootstrap_helper_executes:
            generated = output.read_text(encoding="utf-8")
            bootstrap_helper_writes_contract = all(
                token in generated
                for token in [
                    "- Task ID: 2026-03-20-demo-task",
                    "## Execution plan",
                    "## Memory refresh",
                    "## Full gates",
                    "## Evaluation commands",
                    "python3 qa/verify_skill_system.py",
                ]
            )
except (OSError, subprocess.CalledProcessError):
    bootstrap_helper_executes = False

add(
    "bootstrap_helper_executes",
    bootstrap_helper_executes,
    "task bootstrap helper executes and writes an output file",
)
add(
    "bootstrap_helper_writes_contract",
    bootstrap_helper_executes and bootstrap_helper_writes_contract,
    "task bootstrap helper writes the expected task-contract sections",
)

log_iteration_helper_executes = False
log_iteration_helper_validates = False
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.jsonl"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "log_iteration.py"),
                "--ledger",
                str(ledger_path),
                "--task-id",
                "demo-task",
                "--iteration",
                "0",
                "--eval-tier",
                "fast+full",
                "--hypothesis",
                "Baseline",
                "--hard-gate",
                "qa_verify=pass",
                "--primary-metric-name",
                "quality",
                "--primary-metric-baseline",
                "0",
                "--primary-metric-value",
                "0",
                "--primary-metric-direction",
                "higher_is_better",
                "--secondary-metric",
                "qa_checks=80",
                "--evidence",
                "qa_verify=measured",
                "--mistake",
                "Forgot to refresh memory.",
                "--fix",
                "Used the helper instead of guessing.",
                "--prevention-rule",
                "Refresh memory before new hypotheses.",
                "--kept",
                "true",
                "--summary",
                "Baseline entry.",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        log_iteration_helper_executes = ledger_path.exists()
        report = payload.get("ledger_report", {}) if isinstance(payload, dict) else {}
        log_iteration_helper_validates = (
            isinstance(report, dict)
            and report.get("valid") is True
            and report.get("entry_count") == 1
        )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    log_iteration_helper_executes = False

add(
    "log_iteration_helper_executes",
    log_iteration_helper_executes,
    "iteration logging helper executes and writes a ledger file",
)
add(
    "log_iteration_helper_validates",
    log_iteration_helper_executes and log_iteration_helper_validates,
    "iteration logging helper appends a validated entry and reports a valid ledger",
)

memory_helper_executes = False
memory_helper_reports_task = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "memory_context.py"),
            "--task",
            str(ROOT / "improvement" / "current-task.md"),
            "--ledger",
            str(ROOT / "improvement" / "ledger.jsonl"),
            "--patterns",
            str(ROOT / "improvement" / "patterns.md"),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        memory_helper_executes = True
        working_memory = payload.get("working_memory", {})
        episodic_memory = payload.get("episodic_memory", {})
        memory_helper_reports_task = (
            isinstance(working_memory, dict)
            and working_memory.get("task_id") == live_task_id
            and isinstance(episodic_memory, dict)
            and isinstance(episodic_memory.get("same_task_history"), list)
            and isinstance(payload.get("recommended_refresh"), list)
        )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    memory_helper_executes = False

add(
    "memory_helper_executes",
    memory_helper_executes,
    "memory brief helper executes and returns JSON on the live task, ledger, and patterns",
)
add(
    "memory_helper_reports_task",
    memory_helper_executes and memory_helper_reports_task,
    "memory brief helper reports the live task id and episodic-memory structure",
)

hypothesis_ranking_helper_executes = False
hypothesis_ranking_helper_reports_mode = False
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        backlog_path = Path(tmpdir) / "hypothesis-backlog.json"
        backlog_path.write_text(
            json.dumps(
                {
                    "hypotheses": [
                        {
                            "id": "tighten-known-guardrail",
                            "summary": "Tighten a known guardrail around the next hypothesis selection.",
                            "kind": "exploit",
                            "expected_upside": 4,
                            "implementation_cost": 2,
                            "risk": 1,
                            "confidence": 4,
                            "reversibility": 4,
                            "evidence": "measured",
                            "notes": "Grounded in existing workflow behavior.",
                            "related_patterns": ["Prefer grounded follow-ups when the loop is already improving."],
                            "related_prevention_rules": [],
                            "blocked_by": [],
                        },
                        {
                            "id": "plateau-escape-probe",
                            "summary": "Probe a more exploratory next hypothesis when the loop goes flat.",
                            "kind": "explore",
                            "expected_upside": 4,
                            "implementation_cost": 1,
                            "risk": 1,
                            "confidence": 3,
                            "reversibility": 4,
                            "evidence": "inferred",
                            "notes": "Useful for plateau escape.",
                            "related_patterns": [],
                            "related_prevention_rules": ["Switch search mode after a flat loop trend."],
                            "blocked_by": [],
                        },
                    ]
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "rank_hypotheses.py"),
                "--backlog",
                str(backlog_path),
                "--task",
                str(ROOT / "improvement" / "current-task.md"),
                "--ledger",
                str(ROOT / "improvement" / "ledger.jsonl"),
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            hypothesis_ranking_helper_executes = True
            ranked = payload.get("ranked_hypotheses")
            hypothesis_ranking_helper_reports_mode = (
                payload.get("selected_mode") in {"exploit", "balanced", "plateau_escape", "recovery"}
                and isinstance(ranked, list)
                and len(ranked) > 0
                and isinstance(payload.get("recommended_next_hypothesis"), str)
            )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    hypothesis_ranking_helper_executes = False

add(
    "hypothesis_ranking_helper_executes",
    hypothesis_ranking_helper_executes,
    "hypothesis ranking helper executes and returns JSON on a synthetic backlog plus the live loop state",
)
add(
    "hypothesis_ranking_helper_reports_mode",
    hypothesis_ranking_helper_executes and hypothesis_ranking_helper_reports_mode,
    "hypothesis ranking helper reports a valid selected mode, ranked candidates, and a recommendation",
)

score_helper_executes = False
score_helper_recommends_keep = False
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.jsonl"
        ledger_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "task_id": "demo-task",
                            "iteration": 0,
                            "eval_tier": "fast+full",
                            "hypothesis": "baseline",
                            "changes": [],
                            "hard_gates": {"qa_verify": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 0,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 80},
                            "evidence": {"quality": "measured"},
                            "kept": True,
                            "summary": "baseline",
                        }
                    ),
                    json.dumps(
                        {
                            "task_id": "demo-task",
                            "iteration": 1,
                            "eval_tier": "fast+full",
                            "hypothesis": "candidate",
                            "changes": ["README.md"],
                            "hard_gates": {"qa_verify": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 1,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 82},
                            "evidence": {"quality": "measured"},
                            "kept": False,
                            "summary": "candidate",
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "score_iteration.py"),
                "--ledger",
                str(ledger_path),
                "--task-id",
                "demo-task",
                "--candidate-iteration",
                "1",
                "--reference-iteration",
                "0",
                "--secondary-rule",
                "qa_checks=higher_is_better@0",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            score_helper_executes = True
            score_helper_recommends_keep = payload.get("recommendation") == "keep"
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    score_helper_executes = False

add(
    "score_helper_executes",
    score_helper_executes,
    "iteration scoring helper executes and returns JSON on a synthetic ledger comparison",
)
add(
    "score_helper_recommends_keep",
    score_helper_executes and score_helper_recommends_keep,
    "iteration scoring helper recommends keeping a clearly improved candidate",
)

promotion_apply_executes = False
promotion_apply_writes_patterns = False
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.jsonl"
        patterns_path = Path(tmpdir) / "patterns.md"
        ledger_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "task_id": "demo-memory-task",
                            "iteration": 0,
                            "eval_tier": "fast+full",
                            "hypothesis": "baseline",
                            "changes": [],
                            "hard_gates": {"qa_verify": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 0,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 80},
                            "evidence": {"quality": "measured", "qa_checks": "measured"},
                            "kept": True,
                            "summary": "baseline",
                        }
                    ),
                    json.dumps(
                        {
                            "task_id": "demo-memory-task",
                            "iteration": 1,
                            "eval_tier": "fast+full",
                            "hypothesis": "candidate",
                            "changes": ["tools/log_iteration.py"],
                            "hard_gates": {"qa_verify": "pass"},
                            "primary_metric": {
                                "name": "quality",
                                "baseline": 0,
                                "value": 1,
                                "direction": "higher_is_better",
                            },
                            "secondary_metrics": {"qa_checks": 82},
                            "evidence": {"quality": "measured", "qa_checks": "measured"},
                            "memory": {
                                "mistakes": ["Forgot to validate the ledger after appending entries."],
                                "fixes": ["Ran the validator immediately after logging the iteration."],
                                "prevention_rules": ["Always validate the ledger after appending iteration logs."],
                            },
                            "kept": True,
                            "summary": "candidate",
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        patterns_path.write_text("# Durable repository patterns\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "promote_patterns.py"),
                "--ledger",
                str(ledger_path),
                "--patterns",
                str(patterns_path),
                "--apply",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        promotion_apply_executes = isinstance(payload, dict) and isinstance(payload.get("applied_patterns"), list)
        updated_patterns = patterns_path.read_text(encoding="utf-8")
        promotion_apply_writes_patterns = (
            "always validate the ledger after appending iteration logs" in updated_patterns.lower()
            and len(payload.get("applied_patterns", [])) >= 1
        )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    promotion_apply_executes = False

add(
    "pattern_promotion_apply_executes",
    promotion_apply_executes,
    "pattern promotion helper supports explicit apply mode on a synthetic ledger/patterns pair",
)
add(
    "pattern_promotion_apply_writes_patterns",
    promotion_apply_executes and promotion_apply_writes_patterns,
    "pattern promotion helper appends a promoted durable pattern during explicit apply mode",
)

loop_state_helper_executes = False
loop_state_helper_reports_task = False
try:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "loop_state.py"),
            "--task",
            str(ROOT / "improvement" / "current-task.md"),
            "--ledger",
            str(ROOT / "improvement" / "ledger.jsonl"),
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        loop_state_helper_executes = True
        loop_state_helper_reports_task = (
            payload.get("task_id") == live_task_id
            and isinstance(payload.get("recommendation"), str)
            and isinstance(payload.get("next_iteration"), int)
            and payload.get("next_iteration") >= 1
            and payload.get("baseline_present") is True
        )
except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
    loop_state_helper_executes = False

add(
    "loop_state_helper_executes",
    loop_state_helper_executes,
    "loop-state helper executes and returns JSON on the live task and ledger",
)
add(
    "loop_state_helper_reports_task",
    loop_state_helper_executes and loop_state_helper_reports_task,
    "loop-state helper reports the live task id plus an advisory recommendation and next iteration",
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
