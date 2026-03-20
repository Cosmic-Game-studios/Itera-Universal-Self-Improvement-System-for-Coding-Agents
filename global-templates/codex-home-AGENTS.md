# Global Codex instructions

These are user-level defaults for all repositories.
Use this as `~/.codex/AGENTS.md` and keep repository-specific details in each repo's own `AGENTS.md`.

## Default working style

For non-trivial software-engineering tasks, default to this evaluation-first loop:

1. define the task, constraints, and non-goals
2. create a short execution plan before broad edits
3. refresh memory from the task contract, ledger, durable patterns, and procedural instructions
4. identify fast-loop evals and full gates
5. run a baseline when possible
6. work one hypothesis at a time
7. keep only changes that pass hard gates and improve the target outcome
8. revert failed iterations cleanly

## Universal guardrails

- Prefer the smallest reversible diff.
- Prefer existing project tools and conventions.
- Avoid adding dependencies unless clearly justified.
- Distinguish measured results from inference.
- Do not claim improvements without an evaluation.
- Favor simplicity when gains are otherwise similar.

## Tiered evaluation rule

When a task has expensive validation, use fast-loop evals for each iteration and full gates before the final keep decision.
Do not present a proxy-only result as fully validated.

## Large program mode

If scope spans many areas or a very large run budget, split the repository into area workstreams first.
Allocate a run budget per area and avoid one giant cross-repository diff.

## Missing evals

When the task lacks a real evaluation, create the smallest credible one before broad edits.
Examples: failing test, benchmark, build check, contract test, visual snapshot, dry-run, or fixed-budget training eval.

## Logging

When the repository contains `improvement/` templates or a self-improvement skill, use them.
If the repository ships helper scripts for task scaffolding or validated ledger appends, prefer them over ad hoc manual edits.
If the repository ships a memory helper such as `tools/memory_context.py`, use it to refresh working memory, episodic memory, learned memory, and procedural memory before new hypotheses.
If the repository ships a loop-state helper, use it between iterations as an advisory continue/stop review.
If the repository also ships a ledger validator, run it after appending iteration logs and before the final keep decision.
When the ledger supports it, record reusable mistakes, fixes, and prevention rules instead of leaving them implicit.
Otherwise keep short structured notes about baseline, hypotheses, results, and keep/discard decisions.
