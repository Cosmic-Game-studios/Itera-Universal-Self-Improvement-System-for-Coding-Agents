# Project working agreements

The repository standard is the `swe-self-improve` workflow.
If the skill is explicitly invoked, follow it.
If the skill is not active, follow the same loop from this file.

## Default mode

Treat meaningful SWE work as a bounded improvement loop, not a one-shot edit.

Before broad edits:

1. identify the task type
2. define constraints and non-goals
3. write or infer a short execution plan
4. define fast-loop evals
5. define full gates
6. define the primary metric
7. define secondary metrics
8. set an iteration budget
9. record or infer a rollback strategy

Planning is mandatory for non-trivial work.
Before major edits, the current task should have an explicit execution plan, even if it is short.

## Baseline first

Whenever a credible evaluation exists, run a baseline before changing code.
Capture the current state in `improvement/current-task.md` and append the baseline result to `improvement/ledger.jsonl`.

## Iteration discipline

- Work on one hypothesis at a time.
- Prefer the smallest reversible diff.
- Run fast-loop evals on every iteration.
- Run full-gate evals before final keep when they are more expensive.
- Prefer existing tools, commands, and dependencies.
- Do not add new production dependencies unless clearly justified.
- Distinguish measured facts from inferred judgments.

## Large program mode

If a task spans many files, many areas, or a very large budget such as a 600-run sweep:

- map the repository into areas first
- assign a run budget to each area
- sweep one area at a time
- checkpoint between areas instead of mixing the whole repository into one diff

## Keep / discard rule

Keep a change only when:

- all hard gates pass, and
- the primary metric improves, or remains effectively neutral while simplicity materially improves, and
- no unacceptable regression appears in secondary metrics, and
- any required full-gate eval also passes.

Otherwise revert to the last good checkpoint.

## Git discipline

For multi-iteration tasks, prefer a dedicated branch such as `improve/<date>-<slug>` when appropriate.
Checkpoint before risky edits.
Use git to inspect diffs and revert failed iterations cleanly.

## Logging

Use `improvement/ledger.jsonl` for iteration logs.
Keep logs machine-readable.
If the repository ships helper scripts such as `tools/bootstrap_task.py` or `tools/log_iteration.py`, prefer them for scaffolding and validated ledger appends.
If the repository ships a ledger validator such as `tools/validate_ledger.py`, run it after editing the ledger and before final keep.
Do not commit transient logs unless the user asks for them in version control.

## When evals are missing

If no reliable evaluation exists, create the smallest credible one before major changes:

- a reproduction test
- a benchmark
- a build check
- a screenshot/snapshot comparison
- a contract/integration check
- a training/eval script with a fixed budget
- a dry-run or validation pass

## Simplicity bias

Small wins that add large complexity are usually not worth keeping.
Equal behavior with simpler code is a real improvement.
