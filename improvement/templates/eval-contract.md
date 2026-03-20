# Eval contract

## Objective
What exactly is being improved?

## Fast-loop evals
What cheap checks run every iteration?

## Full gates
What broader checks must pass before the final keep decision?

## Primary metric
What single metric mostly decides keep vs discard?

## Secondary metrics
Which guardrails matter?

## Commands
List the exact commands, scripts, or manual checklist.
Separate fast-loop and full-gate commands.
If the repo ships `tools/rank_hypotheses.py`, include the backlog-ranking command here when the task has multiple plausible next hypotheses.
If the repo ships `tools/score_iteration.py`, include the candidate-versus-reference scoring command here.
If the repo ships `tools/promote_patterns.py`, include the promotion-review command here when the task may produce reusable durable lessons.

## Measurement notes
- deterministic or noisy?
- repeated runs needed?
- fixed seed / fixed input / fixed budget?
- what is a proxy vs a final measurement?

## Acceptance rule
Write the keep / discard rule in one sentence.
If `tools/score_iteration.py` exists, keep the prose rule aligned with the helper's recommendation logic.
