# Global Claude Code instructions

These are user-level defaults for all repositories.
Use this as `~/.claude/CLAUDE.md` and keep project-specific details in each repo's own `CLAUDE.md`.

## Default operating model

For meaningful software-engineering tasks, use an evaluation-first improvement loop:

1. define the task, constraints, and non-goals
2. create a short execution plan before broad edits
3. identify fast-loop evals and full gates
4. establish a baseline when possible
5. test one hypothesis at a time
6. keep only changes that clearly win overall
7. revert failed or low-value iterations

## Universal preferences

- Prefer small, reversible changes.
- Prefer existing tooling, commands, and conventions.
- Avoid new dependencies unless the benefit is clear.
- Separate measured evidence from inference.
- Do not describe a change as better unless an evaluation supports it.
- Prefer simpler solutions when outcomes are similar.

## Tiered evaluation rule

Use fast-loop evals for cheap iteration and full gates before the final keep decision whenever broad validation is expensive.
Call out proxy-only results explicitly.

## Large program mode

If scope spans many areas or a very large run budget, split the repository into area workstreams first.
Allocate a run budget per area and avoid one giant cross-repository diff.

## Missing evals

If a task has no credible evaluation, create the smallest one that makes progress real before broad edits.

## Logging

When the repository contains `improvement/` templates or a self-improvement skill, use them.
If the repository ships helper scripts for task scaffolding or validated ledger appends, prefer them over ad hoc manual edits.
If the repository also ships a ledger validator, run it after appending iteration logs and before the final keep decision.
