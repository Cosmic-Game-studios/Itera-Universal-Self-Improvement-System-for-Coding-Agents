# Current task

- Task ID: 2026-03-20-iteration-scoring-hardening
- Task name: Operationalize iteration scoring for keep-or-revert decisions
- Task type: feature
- Desired outcome: Add a deterministic helper that compares a candidate iteration against the current best state using hard gates, the primary metric, secondary guardrails, and a simplicity tie-break so keep-or-revert decisions become more operational.
- Non-goals:
- Replace engineering judgment with an opaque numeric score.
- Redesign the ledger contract around a completely new schema.
- Introduce third-party Python dependencies.

## Execution plan
- Rewrite the live task contract for iteration scoring and capture a fresh baseline.
- Implement a score_iteration helper that compares ledger entries with explicit secondary-metric rules and a simplicity tie-break.
- Add regression tests for hard-gate failures, primary-metric outcomes, secondary regressions, and neutral-primary tie-breaks.
- Wire the scoring helper into the skill docs, templates, README, and QA.
- Run full verification, log the kept result, review the final diff, and publish the improved state.

## Optional: Area coverage plan
- <root docs / skills / tools / qa / improvement / templates / other areas>

## Optional: Run budget allocation
- <area>: <planned runs>

## Constraints
- Use only the Python standard library.
- Keep the scoring logic transparent and reason-oriented instead of pretending a single scalar can fully replace judgment.
- Stay backward-compatible with the current ledger history and existing workflow artifacts.
- Prefer explicit secondary-metric rules over hidden heuristics.

## Memory refresh
- Working memory: `improvement/current-task.md`
- Episodic memory: `improvement/ledger.jsonl`
- Learned memory: `improvement/patterns.md`
- Procedural memory: `AGENTS.md` / `CLAUDE.md` / `SKILL.md`
- Refresh command: `python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary`
- Mistakes to avoid: keep-or-revert logic is still mostly prose, so a helper that hides why a candidate won or lost would recreate the same ambiguity in code form.
- Reusable fixes: prefer explicit comparison rules and reasoned output over a single opaque scalar, just like the memory helper kept its advice grounded in visible artifacts.

## Fast-loop evals
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/score_iteration.py --ledger improvement/ledger.jsonl --task-id 2026-03-20-agent-memory-hardening --candidate-iteration 1 --reference-iteration 0 --secondary-rule qa_passed_checks=higher_is_better@0 --secondary-rule unit_tests_ran=higher_is_better@0 --format summary

## Full gates
- Verify that the repository ships a usable scoring helper, green tests, green QA, and coherent docs for lexicographic keep-or-revert decisions.
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/score_iteration.py --ledger improvement/ledger.jsonl --task-id 2026-03-20-agent-memory-hardening --candidate-iteration 1 --reference-iteration 0 --secondary-rule qa_passed_checks=higher_is_better@0 --secondary-rule unit_tests_ran=higher_is_better@0 --format json
- rg -n 'score_iteration|iteration scoring|fitness vector|lexicographic|simplicity tie-break|secondary-rule' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools

## Primary metric
- Name: iteration scoring helper is operationally available across the workflow stack
- Direction: higher_is_better
- Baseline: the repository describes a fitness vector and keep rule, but it does not yet ship a dedicated helper that scores one iteration against another with explicit guardrails and a transparent recommendation.
- Target: the repository ships a deterministic scoring helper, regression tests, documentation, and QA so keep-or-revert decisions can be operationalized instead of remaining prose-only.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Ledger compatibility remains intact
- Scoring remains explainable instead of opaque

## Evaluation commands
```bash
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/score_iteration.py --ledger improvement/ledger.jsonl --task-id 2026-03-20-agent-memory-hardening --candidate-iteration 1 --reference-iteration 0 --secondary-rule qa_passed_checks=higher_is_better@0 --secondary-rule unit_tests_ran=higher_is_better@0 --format summary
python3 tools/score_iteration.py --ledger improvement/ledger.jsonl --task-id 2026-03-20-agent-memory-hardening --candidate-iteration 1 --reference-iteration 0 --secondary-rule qa_passed_checks=higher_is_better@0 --secondary-rule unit_tests_ran=higher_is_better@0 --format json
rg -n 'score_iteration|iteration scoring|fitness vector|lexicographic|simplicity tie-break|secondary-rule' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be sufficient if the helper, docs, and QA land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents and explicit ledger entries as input
- proxy limitations: doc scans are structural proxies and must stay paired with helper execution

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert any scoring rule that hides why a candidate won or lost.
- Revert any contract change that forces old ledger entries into a new incompatible shape.

## Stop conditions
- The repository ships an executable iteration scoring helper.
- Tests and QA verify the helper and its docs.
- The helper keeps the decision logic explainable and aligned with the published keep rule.
- Final verification passes cleanly.
