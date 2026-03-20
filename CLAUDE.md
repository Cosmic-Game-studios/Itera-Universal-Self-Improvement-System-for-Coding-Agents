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
3. fast-loop evals
4. full gates
5. primary metric
6. secondary metrics
7. iteration budget
8. rollback strategy

## Baseline first

Whenever an evaluation exists, run a baseline before making major changes.
Document it in `improvement/current-task.md` and log it in `improvement/ledger.jsonl`.

## Iteration discipline

- one hypothesis per iteration
- smallest reversible diff
- run fast-loop evals each iteration
- run full-gate evals before final keep when needed
- prefer existing tooling
- avoid new dependencies unless clearly justified
- separate measured results from inference

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
Use `improvement/patterns.md` only for durable lessons that are likely to matter again.

## Simplicity bias

Do not keep tiny wins that create disproportionate complexity.
Equivalent behavior with less complexity is a valid improvement.
