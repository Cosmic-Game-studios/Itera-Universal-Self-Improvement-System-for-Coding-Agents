# Current task

- Task ID: 2026-03-20-loop-review-hardening
- Task name: Harden the skill loop with explicit loop-state review
- Task type: refactor
- Desired outcome: Improve the `swe-self-improve` loop itself by adding explicit support for post-iteration review, including a Python helper that summarizes task progress, remaining budget, next iteration number, and stop/continue signals from the live task contract plus ledger.
- Non-goals: Build a fully autonomous agent controller, silently decide user intent from heuristics alone, or replace the existing human-readable keep-or-revert workflow with opaque automation.

## Execution plan
1. Rewrite the live task contract for loop-review hardening and log a fresh baseline.
2. Implement a deterministic loop-state helper that reads `improvement/current-task.md` and `improvement/ledger.jsonl`.
3. Add regression tests and QA checks so the helper is exercised on both synthetic and live repository state.
4. Update the skill docs, fallback docs, and README so loop-state review becomes an explicit supported step in the workflow.
5. Run full verification, log the kept result, review the final diff, and publish the improved state.

## Constraints
- Use only the Python standard library.
- Keep recommendations advisory, not magical or overly confident.
- Reuse the repository's current task and ledger artifacts instead of inventing parallel state files.
- Preserve compatibility with the current live ledger history and current-task format.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/loop_state.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --format summary`

## Full gates
- Verify that the repository now supports explicit loop-state review with a working helper, green tests, green QA, and coherent documentation across the skill stack.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/loop_state.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --format json`
- `rg -n "loop state|loop review|continue|stop condition|next iteration" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py`

## Primary metric
- Name: loop review support is explicitly available across the workflow stack
- Direction: higher_is_better
- Baseline: the repository has planning, logging, validation, and helper scripts, but the loop still lacks a dedicated review helper for checking current task state, remaining budget, next iteration number, and basic stop/continue signals.
- Target: the repository ships a loop-state helper, verifies it in tests and QA, and documents loop review as an explicit part of the workflow.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- The helper works on the live repo state without rewriting artifacts
- Skill wording stays aligned between Codex and Claude

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/loop_state.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --format summary

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/loop_state.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --format json
rg -n "loop state|loop review|continue|stop condition|next iteration" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be enough if the helper, tests, and docs land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents with the live current-task and ledger files as input
- proxy limitations: wording checks are structural proxies, so they must stay paired with helper execution

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert any loop-review heuristic that overclaims certainty or misreads the current task contract in common valid cases.
- Revert docs that advertise a loop-state step without the QA suite executing the helper.

## Stop conditions
- The repository ships a working loop-state helper
- Tests and QA both verify the helper
- The skill stack explicitly mentions loop-state review between iterations
- Final verification passes cleanly
