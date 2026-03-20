# Current task

- Task ID: <yyyy-mm-dd-short-slug>
- Task name: <human readable>
- Task type: <bugfix | feature | frontend | backend | perf | refactor | ml | infra | data>
- Desired outcome:
- Non-goals:

## Execution plan
- <3-7 short ordered steps>

## Optional: Area coverage plan
- <root docs / skills / tools / qa / improvement / templates / other areas>

## Optional: Run budget allocation
- <area>: <planned runs>

## Constraints
- Must not break:
- Must not change:
- Budget / environment limits:

## Memory refresh
- Working memory: `improvement/current-task.md`
- Episodic memory: `improvement/ledger.jsonl`
- Learned memory: `improvement/patterns.md`
- Procedural memory: `AGENTS.md` / `CLAUDE.md` / `SKILL.md`
- Refresh command: <run `tools/memory_context.py` here if the repo ships one>
- Promotion command: <run `tools/promote_patterns.py` here if the repo ships one>
- Mistakes to avoid:
- Reusable fixes:

## Fast-loop evals
- <cheap checks run each iteration>
- <score_iteration helper command if the repo ships one>
- <loop-state helper command if the repo ships one>

## Full gates
- <broader checks required before final keep>
- <ledger validator command for improvement/ledger.jsonl if the repo ships one>

## Primary metric
- Name:
- Direction: <lower_is_better | higher_is_better | pass_fail>
- Baseline:
- Target:

## Secondary metrics
- <metric>: <guardrail>

## Evaluation commands
```bash
# fast-loop command 1
# fast-loop command 2
# full-gate command 1
# full-gate command 2
# ledger validator command if available
```

## Measurement notes
- deterministic or noisy:
- repeated runs needed:
- fixed seed / fixed input / fixed budget:
- proxy limitations:

## Iteration budget
- Max iterations:
- Max task time:

## Rollback / checkpoint strategy
- 

## Stop conditions
- 
