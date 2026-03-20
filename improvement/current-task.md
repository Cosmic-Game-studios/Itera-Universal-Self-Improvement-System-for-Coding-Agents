# Current task

- Task ID: 2026-03-20-hypothesis-ranking-hardening
- Task name: Operationalize hypothesis ranking for stronger self-improvement
- Task type: feature
- Desired outcome: Add a deterministic helper that ranks candidate hypotheses using leverage, risk, cost, confidence, reversibility, and loop-state-aware mode selection so the next iteration is chosen more intelligently.
- Non-goals:
- Replace engineering judgment with a single opaque score.
- Auto-generate code changes instead of helping the team rank hypotheses.
- Introduce third-party Python dependencies.

## Execution plan
- Rewrite the live task contract for hypothesis ranking and capture a fresh baseline.
- Implement a rank_hypotheses helper with explicit backlog input and loop-state-aware ranking modes.
- Add regression tests for validation, ranking order, and automatic mode selection.
- Wire the helper into the skill docs, templates, bootstrapper, README, and repository QA.
- Run full verification, log the kept result, review the final diff, and publish the improved state.

## Optional: Area coverage plan
- tools
- qa
- docs-and-skill-guidance
- improvement-templates-and-artifacts

## Optional: Run budget allocation
- tools: 1
- qa: 1
- docs-and-skill-guidance: 0
- improvement-templates-and-artifacts: 0

## Constraints
- Use only the Python standard library.
- Keep the ranking logic transparent and reason-oriented instead of pretending it can replace judgment.
- Stay compatible with the existing task contract, ledger, and memory model.
- Bias the helper toward stronger self-improvement by making plateau or failure states change the ranking mode explicitly.

## Memory refresh
- Working memory: improvement/current-task.md
- Episodic memory: improvement/ledger.jsonl
- Learned memory: improvement/patterns.md
- Procedural memory: AGENTS.md / CLAUDE.md / SKILL.md
- Refresh command: python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary
- Ranking command: python3 tools/rank_hypotheses.py --backlog improvement/templates/hypothesis-backlog.json --task improvement/current-task.md --ledger improvement/ledger.jsonl --format summary
- Mistakes to avoid: keep-or-revert decisions were still mostly described in prose, which made the published fitness vector harder to apply consistently.
- Mistakes to avoid: loop-state review could say when to continue or replan, but it could not yet rank a backlog and switch search mode explicitly.
- Reusable fixes: use explicit, reasoned scoring when a loop decision should not rely on intuition alone.
- Reusable fixes: favor thin helpers that make the next loop step operational, reviewable, and compatible with the existing memory layers.
- Reusable fixes: make the next-hypothesis choice mode-aware so plateau and recovery states do not keep spending runs the same way as steady progress.

## Fast-loop evals
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/rank_hypotheses.py --backlog improvement/templates/hypothesis-backlog.json --task improvement/current-task.md --ledger improvement/ledger.jsonl --format summary

## Full gates
- Verify that the repository ships a usable hypothesis-ranking helper, green tests, green QA, and coherent docs for loop-state-aware next-hypothesis selection.
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/rank_hypotheses.py --backlog improvement/templates/hypothesis-backlog.json --task improvement/current-task.md --ledger improvement/ledger.jsonl --format json
- rg -n 'rank_hypotheses|hypothesis ranking|next hypothesis|plateau_escape|exploit|explore|replan' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools

## Primary metric
- Name: hypothesis_ranking_helper_operationally_available
- Direction: higher_is_better
- Baseline: the skill describes forming and ranking 2-5 hypotheses, but it does not yet ship an executable helper for backlog validation, mode-aware ranking, and next-hypothesis selection.
- Target: the repository ships a deterministic hypothesis-ranking helper, regression tests, docs, and QA so hypothesis selection is more deliberate and self-improvement can climb faster.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Ranking output remains transparent and explainable
- Plateau or failure states change ranking mode deterministically

## Evaluation commands
```bash
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/rank_hypotheses.py --backlog improvement/templates/hypothesis-backlog.json --task improvement/current-task.md --ledger improvement/ledger.jsonl --format summary
python3 tools/rank_hypotheses.py --backlog improvement/templates/hypothesis-backlog.json --task improvement/current-task.md --ledger improvement/ledger.jsonl --format json
rg -n 'rank_hypotheses|hypothesis ranking|next hypothesis|plateau_escape|exploit|explore|replan' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be sufficient if helper, docs, and QA land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents plus a deterministic example backlog
- proxy limitations: doc scans are structural proxies and must stay paired with helper execution on a synthetic backlog

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert any ranking rule that hides why a hypothesis won or lost.
- Revert any mode-selection logic that changes behavior without explicit reasons tied to loop state.

## Stop conditions
- The repository ships an executable hypothesis-ranking helper.
- Tests and QA verify the helper and its docs.
- The helper keeps ranking transparent and loop-state-aware.
- Final verification passes cleanly.
