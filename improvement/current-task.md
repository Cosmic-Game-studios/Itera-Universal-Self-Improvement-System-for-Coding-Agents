# Current task

- Task ID: 2026-03-20-plan-required-in-skill
- Task name: Make planning an explicit required part of the self-improvement workflow
- Task type: refactor
- Desired outcome: Extend the Codex and Claude `swe-self-improve` skill so planning is an explicit mandatory step, and propagate that requirement through the fallback docs, task template, README guidance, and QA checks.
- Non-goals: Change the underlying keep-or-revert philosophy, introduce external dependencies, or weaken the existing evaluation-first discipline.

## Execution plan
1. Update the live task contract and baseline ledger for this planning-focused skill change.
2. Add explicit plan-first language to both skill files and both fallback workflow files.
3. Extend the task template and README so the planning requirement is visible to future users.
4. Strengthen QA so the repository fails if the planning requirement disappears from the workflow stack.
5. Run full verification, log the kept iteration, and publish the final state.

## Constraints
- Use only the Python standard library.
- Keep the workflow language aligned across Codex, Claude, and fallback docs.
- Prefer a small wording and verification diff over a broad rewrite.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `rg -n "execution plan|plan before|planning is mandatory|plan-first" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md improvement/templates/current-task.md README.md qa/verify_skill_system.py`

## Full gates
- Verify the skill stack consistently requires planning and the repository still passes its structural QA.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `rg -n "execution plan|plan before|planning is mandatory|plan-first" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md global-templates README.md improvement/templates/current-task.md qa/verify_skill_system.py`

## Primary metric
- Name: planning requirement is explicitly enforced across the workflow stack
- Direction: higher_is_better
- Baseline: the repository passes QA, but planning is only implied in scattered wording and is not explicitly enforced across the skill, fallback docs, template, and verifier.
- Target: the workflow stack explicitly requires a plan and QA fails if that requirement disappears.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Skill wording stays concise and aligned between Codex and Claude

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
rg -n "execution plan|plan before|planning is mandatory|plan-first" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md improvement/templates/current-task.md README.md qa/verify_skill_system.py

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
rg -n "execution plan|plan before|planning is mandatory|plan-first" .agents/skills/swe-self-improve .claude/skills/swe-self-improve AGENTS.md CLAUDE.md global-templates README.md improvement/templates/current-task.md qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline run and one kept implementation run should be enough if the wording stays aligned
- fixed seed / fixed input / fixed budget: fixed repository contents and repository-local QA/check searches
- proxy limitations: wording checks are structural proxies, so the final diff must still read coherently as a workflow change rather than keyword stuffing

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one verification pass

## Rollback / checkpoint strategy
- Revert any wording or QA additions that force awkward phrasing, drift Codex and Claude apart, or create brittle keyword-only checks.

## Stop conditions
- Planning is explicit in the skill, fallback docs, template, and README
- `qa/verify_skill_system.py` enforces the planning requirement
- Tests and QA both pass
