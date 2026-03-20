# Current task

- Task ID: 2026-03-20-memory-promotion-hardening
- Task name: Operationalize durable memory promotion from the ledger
- Task type: feature
- Desired outcome: Add a deterministic helper that turns recurring ledger learnings into candidate or applied durable patterns for improvement/patterns.md, with transparent dedupe instead of manual copy-paste.
- Non-goals:
- Blindly append every ledger memory note into patterns.md without review.
- Introduce third-party Python dependencies.
- Replace the existing pattern_recognition helper instead of building on it.

## Execution plan
- Rewrite the live task contract for memory promotion and capture a fresh baseline.
- Implement a promote_patterns helper with dry-run output, existing-pattern dedupe, and explicit apply mode.
- Add regression tests for candidate generation, dedupe behavior, and apply mode.
- Wire the new helper into docs, workflow guidance, and repository QA.
- Run full verification, log the kept result, review the final diff, and publish the improved state.

## Optional: Area coverage plan
- tools
- qa
- docs-and-skill-guidance
- improvement-memory-artifacts

## Optional: Run budget allocation
- tools: 1
- qa: 1
- docs-and-skill-guidance: 0
- improvement-memory-artifacts: 0

## Constraints
- Use only the Python standard library.
- Keep promotion transparent: dry-run by default and explicit apply mode for writing patterns.md.
- Stay compatible with the current ledger schema and existing durable-pattern format.
- Prefer promoting concise reusable lessons over noisy task-specific trivia.

## Memory refresh
- Working memory: improvement/current-task.md
- Episodic memory: improvement/ledger.jsonl
- Learned memory: improvement/patterns.md
- Procedural memory: AGENTS.md / CLAUDE.md / SKILL.md
- Refresh command: python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary
- Promotion command: python3 tools/promote_patterns.py --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary
- Mistakes to avoid: promoting one-off notes into durable patterns would recreate the same ambiguity we just removed from scoring and memory logging.
- Mistakes to avoid: silently rewriting `improvement/patterns.md` would make the learned-memory layer harder to trust and review.
- Reusable fixes: reuse the existing pattern-recognition signals and the structured `memory` payload from the ledger instead of inventing a second heuristic universe.
- Reusable fixes: keep the helper dry-run by default, apply only on explicit request, and dedupe against existing durable pattern titles before writing.

## Fast-loop evals
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/promote_patterns.py --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary

## Full gates
- Verify that the repository ships a usable promotion helper, green tests, green QA, and coherent docs for candidate/apply memory promotion.
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/promote_patterns.py --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format json
- rg -n 'promote_patterns|memory promotion|pattern promotion|durable pattern promotion' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools

## Primary metric
- Name: memory_promotion_helper_operationally_available
- Direction: higher_is_better
- Baseline: the repository can suggest pattern candidates with pattern_recognition.py, but it does not yet ship a helper that dedupes against patterns.md and promotes durable ledger learnings in a controlled way.
- Target: the repository ships a deterministic memory-promotion helper, regression tests, docs, and QA so durable ledger learnings can be promoted into patterns.md without manual copy-paste churn.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Pattern dedupe stays deterministic
- Promotion output remains transparent instead of silently mutating patterns.md

## Evaluation commands
```bash
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/promote_patterns.py --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary
python3 tools/promote_patterns.py --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format json
rg -n 'promote_patterns|memory promotion|pattern promotion|durable pattern promotion' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be sufficient if the helper, docs, and QA land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents and explicit ledger plus patterns files as input
- proxy limitations: README and doc scans are structural proxies and must stay paired with helper execution

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert any promotion logic that silently rewrites or duplicates durable patterns.
- Revert any candidate generation rule that turns weak one-off notes into durable lessons.

## Stop conditions
- The repository ships an executable memory-promotion helper.
- Tests and QA verify the helper and its docs.
- The helper keeps promotion transparent, deduplicated, and aligned with the published durable-pattern format.
- Final verification passes cleanly.
