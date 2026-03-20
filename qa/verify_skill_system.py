from __future__ import annotations

from pathlib import Path
import re
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
    "improvement/templates/current-task.md",
    "improvement/templates/eval-contract.md",
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
