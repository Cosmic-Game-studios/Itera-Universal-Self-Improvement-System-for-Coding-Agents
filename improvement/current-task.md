# Current task

- Task ID: 2026-03-20-program-mode-600-run-sweeps
- Task name: Extend the skill for large multi-area 600-run programs
- Task type: refactor
- Desired outcome: Extend the repository so `swe-self-improve` can explicitly support large, thorough, multi-area programs such as a 600-run repository sweep, including documentation, templates, and a small planner tool for area coverage and budget allocation.
- Non-goals: Actually fabricate 600 fake iterations in the ledger, introduce external dependencies, or replace the existing bounded keep-or-revert philosophy with uncontrolled autonomous churn.

## Execution plan
1. Update the task contract and log a baseline for the program-mode expansion.
2. Add a repo-area planning tool that can scan the repository and propose area coverage plus run-budget splits for large sweeps.
3. Extend the skills, fallback docs, templates, and README with an explicit program-mode / 600-run workflow.
4. Strengthen QA so the repository verifies the new program-mode support instead of leaving it as informal prose.
5. Run full verification, log the kept change, and publish the final state.

## Optional: Area coverage plan
- `[root]`: top-level docs and repo guidance
- `.agents/`: Codex skill and Codex-side references
- `.claude/`: Claude skill and Claude-side references
- `global-templates/`: shipped user-level defaults
- `improvement/`: contracts, ledger, patterns, and templates
- `qa/`: verifier and tests
- `tools/`: repo support tooling and planners

## Optional: Run budget allocation
- Use `tools/repo_area_plan.py --root . --budget 600` as the canonical area budget suggestion for repo-wide sweeps.
- Keep this implementation task itself bounded to 2 iterations even though it is adding 600-run program support.

## Constraints
- Use only the Python standard library.
- Keep the workflow language aligned across Codex, Claude, fallback docs, and templates.
- Prefer support for real staged large-run programs, not hype or fake autonomous claims.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/repo_area_plan.py --root . --budget 600 --format markdown`

## Full gates
- Verify the skill stack consistently documents large multi-area program mode, the planner tool works, and the repository still passes structural QA.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/repo_area_plan.py --root . --budget 600 --format json`
- `rg -n "program mode|600-run|area coverage|run budget" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md global-templates README.md improvement/templates qa/verify_skill_system.py`

## Primary metric
- Name: large-program support is explicitly available across the workflow stack
- Direction: higher_is_better
- Baseline: the repository passes QA, but it does not yet provide a dedicated repo-area planner or explicit 600-run program-mode guidance for sweeping all areas.
- Target: the repository ships explicit program-mode guidance plus a working planner tool for large multi-area sweeps, and QA enforces that support.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Skill wording stays aligned between Codex and Claude
- Planner output is deterministic for the same repository and budget

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/repo_area_plan.py --root . --budget 600 --format markdown

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/repo_area_plan.py --root . --budget 600 --format json
rg -n "program mode|600-run|area coverage|run budget" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md global-templates README.md improvement/templates qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline run and one kept implementation run should be enough if the planner and docs land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents and a fixed run budget of 600 for planner verification
- proxy limitations: wording checks remain structural proxies, so the final tool and docs still need to read as a real operating model rather than keyword stuffing

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one verification pass

## Rollback / checkpoint strategy
- Revert any additions that only simulate a 600-run mode rhetorically, create brittle QA checks, or make the workflow look less bounded and trustworthy.

## Stop conditions
- Program mode for large multi-area sweeps is explicit in the skill stack
- The repo ships a working planner for large-budget area coverage
- `qa/verify_skill_system.py` enforces the new support
- Tests and QA both pass
