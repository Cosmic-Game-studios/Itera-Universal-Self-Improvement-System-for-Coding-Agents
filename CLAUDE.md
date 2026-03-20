# Project instructions

The repository standard is the `swe-self-improve` workflow.
If the skill is explicitly invoked, follow it.
If the skill is not active, follow the same loop from this file.

## Operating model

Default to a bounded improvement loop.
Do not treat substantial SWE work as a single edit followed by a guess.

Before broad edits, establish:

1. task type
2. constraints and non-goals
3. a short execution plan
4. refresh memory from the task contract, ledger, durable patterns, and procedural instructions
5. fast-loop evals
6. full gates
7. primary metric
8. secondary metrics
9. iteration budget
10. rollback strategy

Planning is mandatory for non-trivial work.
Before major edits, the current task should have an explicit execution plan, even if it is short.

## Baseline first

Whenever an evaluation exists, run a baseline before making major changes.
Document it in `improvement/current-task.md` and log it in `improvement/ledger.jsonl`.
Treat `improvement/current-task.md` as working memory, `improvement/ledger.jsonl` as episodic memory, `improvement/patterns.md` as learned memory, and this file plus the skill docs as procedural memory.

## Iteration discipline

- one hypothesis per iteration
- smallest reversible diff
- run fast-loop evals each iteration
- run full-gate evals before final keep when needed
- refresh memory before forming the next hypothesis so repeated mistakes get caught early
- review loop state and remaining budget before starting the next hypothesis
- prefer existing tooling
- avoid new dependencies unless clearly justified
- separate measured results from inference

## Large program mode

If a task spans many files, many areas, or a very large budget such as a 600-run sweep:

- map the repository into areas first
- assign a run budget to each area
- sweep one area at a time
- checkpoint between areas instead of mixing the whole repository into one diff

## Keep / discard rule

Keep a change only when:

- all hard gates pass
- the primary metric improves, or stays neutral while simplicity clearly improves
- secondary metrics do not regress beyond the accepted budget
- required full-gate evals pass

Otherwise revert.

## Missing evaluations

If the task lacks a real evaluation, create the smallest credible one before expanding scope.
Examples: failing test, benchmark, build check, accessibility check, visual snapshot, contract test, dry-run, fixed-budget training eval.

## Logging

Use `improvement/ledger.jsonl` for structured iteration logs.
If the repository ships helper scripts such as `tools/bootstrap_task.py` or `tools/log_iteration.py`, prefer them for scaffolding and validated ledger appends.
If the repository ships `tools/memory_context.py`, use it before baseline and between iterations to refresh working, episodic, learned, and procedural memory.
If the repository ships `tools/score_iteration.py`, use it to compare the candidate against the current best state before the keep-or-revert call.
If the repository ships `tools/loop_state.py`, use it as an advisory loop-review step before continuing or stopping.
If the repository ships a ledger validator such as `tools/validate_ledger.py`, run it after editing the ledger and before final keep.
When an iteration teaches something reusable, record mistakes, fixes, and prevention rules in the optional `memory` object in the ledger.
Use `improvement/patterns.md` only for durable lessons that are likely to matter again.

## Simplicity bias

Do not keep tiny wins that create disproportionate complexity.
Equivalent behavior with less complexity is a valid improvement.
