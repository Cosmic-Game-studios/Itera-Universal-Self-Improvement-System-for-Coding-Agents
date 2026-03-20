---
name: swe-self-improve
description: Run a bounded, evaluation-first self-improvement loop for software engineering tasks such as bug fixing, feature work, refactors, frontend changes, backend/API changes, model training, performance tuning, deployment workflows, and data pipelines. Use when iterative keep-or-revert improvement is better than a one-shot edit. Do not use for trivial cosmetic edits.
---

# Universal SWE Self-Improvement Loop

Use this skill when the user wants to build, fix, refactor, optimize, tune, or otherwise improve a software system and the work benefits from **iteration with measurement** instead of a single-pass change.

Do **not** use this skill for trivial one-file cosmetic edits that do not need evaluation.

## Goal

Turn a software-engineering task into a bounded improvement program:

1. define the target
2. define how success is measured
3. make a short execution plan
4. establish a baseline
5. try one hypothesis at a time
6. keep or discard each iteration
7. stop when the budget is exhausted or the curve flattens

## Inputs

From the user prompt and repository, determine:

- task type
- desired outcome
- forbidden regressions
- execution plan shape
- available evaluation commands or scripts
- acceptable iteration budget
- rollback method

If `improvement/current-task.md` already exists, update it instead of creating a conflicting version.

For large program mode, also determine:

- area coverage map
- run budget per area
- checkpoint boundaries between areas

## Files to maintain

- `improvement/current-task.md`
- `improvement/ledger.jsonl`
- optionally `improvement/patterns.md` for durable lessons

If the `improvement/` directory does not exist, create it and initialize the above files.

If the repository ships a planner such as `tools/repo_area_plan.py`, use it for large multi-area programs before broad edits.
If the repository ships a ledger validator such as `tools/validate_ledger.py`, run it after updating `improvement/ledger.jsonl` and before finalizing a kept state.

## Memory model

Treat the workflow artifacts as four explicit memory layers:

- working memory: `improvement/current-task.md`
- episodic memory: `improvement/ledger.jsonl`
- learned memory: `improvement/patterns.md`
- procedural memory: `AGENTS.md`, `CLAUDE.md`, and this skill

If the repository ships `tools/memory_context.py`, use it to refresh those layers before baseline, before forming the next hypothesis, and before starting a new related task.
When an iteration teaches something reusable, record the mistake, the fix, and a prevention rule in the optional `memory` object in `improvement/ledger.jsonl`.

## Step 1: Create the task contract and execution plan

Write or update `improvement/current-task.md` with:

1. task name and short slug
2. task type
3. desired outcome
4. non-goals
5. execution plan with 3-7 concrete steps
6. memory refresh notes that point at working, episodic, learned, and procedural memory
7. fast-loop evals
8. full gates
9. primary metric
10. secondary metrics
11. evaluation commands
12. iteration budget
13. rollback/checkpoint plan
14. stop conditions

Use the template in `improvement/templates/current-task.md` if present.
If the repository ships `tools/bootstrap_task.py`, use it when that is the fastest way to scaffold a clean task contract from the template shape.
If the repository ships `tools/memory_context.py`, run it and copy the most relevant reminders into the task contract's memory refresh section.

Planning is mandatory for non-trivial use of this skill.
Before baseline or meaningful edits, create a short execution plan.
It can stay concise, but it must exist and should be reflected in `improvement/current-task.md` when that artifact is in use.

## Step 2: Establish baseline

Before changing code, run the best available baseline evaluation.
This baseline is mandatory whenever a credible evaluation exists.

If the task has both fast-loop evals and full gates, run whichever baseline is feasible up front, then run the full-gate baseline before the final keep decision if it was deferred for cost reasons.

Log the baseline in `improvement/ledger.jsonl` with iteration `0` and `kept: true`.

## Step 3: Form hypotheses

Before generating hypotheses, refresh memory from:

- the active task contract
- the ledger history for the same or similar tasks
- durable patterns that already survived earlier work
- the procedural rules in the repository instructions

Generate 2-5 plausible improvement hypotheses.
Rank them by expected upside divided by risk and implementation cost.
Start with the smallest high-leverage hypothesis.

Good hypotheses are:

- specific
- testable
- reversible
- narrow in scope

Bad hypotheses are vague or require changing many systems at once.

## Program mode for large sweeps

When the user asks for a broad repository sweep, many files, many areas, or a very large budget such as a 600-run program:

1. do not treat the work as one giant flat queue
2. map the repository into areas first
3. assign a sub-budget to each area
4. run one area at a time with its own checkpoints
5. keep the best known state between areas

For program mode, prefer an explicit area coverage plan and run budget allocation in `improvement/current-task.md`.
If a planner tool is available, use it before assigning budgets manually.

## Step 4: Run the iteration loop

For each iteration:

1. checkpoint the current good state
2. implement one hypothesis with the smallest credible diff
3. run fast-loop evals
4. if the iteration looks promising, run any required full-gate evals before marking it kept
5. log results in `improvement/ledger.jsonl`
6. compare to the current best state
7. keep or revert
8. refresh memory, then review loop state, remaining budget, and stop/continue signals before choosing the next hypothesis

If the repository ships `tools/loop_state.py`, use it after logging and before deciding whether to continue, replan, or stop.
If the repository ships `tools/memory_context.py`, use it after logging to remind yourself which mistakes, fixes, and durable patterns should influence the next iteration.

### Fast-loop evals vs full gates

Use fast-loop evals for cheap, frequent feedback.
Use full gates for broader or more expensive validation.

Examples:

- fast-loop: targeted tests, small benchmark, route build, reduced-budget training eval
- full gates: full test suite, broader benchmark, integration matrix, full validation set, policy/security check

Never finalize a change based only on a cheap proxy if a broader full-gate check is required.
If you defer full gates during exploration, say so explicitly.

### Keep rule

Keep the iteration only if:

- all hard gates pass, and
- the primary metric improves, or stays effectively neutral while simplicity materially improves, and
- no unacceptable regression appears in any protected metric, and
- any required full-gate eval also passes

### Revert rule

Revert immediately if:

- a hard gate fails and the fix is not a quick, local correction
- the primary metric is worse
- the change adds complexity with little measurable upside
- the change breaks a non-goal or forbidden regression boundary
- a required full-gate eval fails

## Step 5: Final verification

Before presenting the final kept change as the winner, run the full-gate evaluation set for the current best state unless it has already been run on that exact state.
If only proxy evaluations were feasible, say clearly that the result is provisional.

## Step 6: Stop conditions

Stop when any of these are true:

- iteration budget exhausted
- user goal satisfied
- recent iterations plateau
- remaining ideas are materially higher risk than likely benefit
- evaluation cost is too high for further low-confidence exploration

Do not continue indefinitely by default.
Open-ended looping is appropriate only when the user explicitly asks for long-running autonomous exploration and the task has a safe, repeatable eval.
If the repository ships `tools/loop_state.py`, prefer it as an advisory review step before stopping or spending another iteration.

## Logging format

Append one JSON object per line to `improvement/ledger.jsonl`.
Use this shape:

```json
{"task_id":"2026-03-20-homepage-speed","iteration":1,"eval_tier":"fast+full","hypothesis":"lazy-load non-critical widgets","changes":["src/home/Hero.tsx","src/home/widgets.ts"],"hard_gates":{"build":"pass","tests":"pass","lint":"pass"},"primary_metric":{"name":"lcp_ms","baseline":2800,"value":2450,"direction":"lower_is_better"},"secondary_metrics":{"bundle_kb":312.4,"a11y_violations":0},"evidence":{"lcp_ms":"measured","bundle_kb":"measured","ux_risk":"inferred"},"memory":{"mistakes":["Earlier draft skipped the broader regression gate."],"fixes":["Ran the full-gate check before keeping the optimization."],"prevention_rules":["Do not keep proxy-only wins when a required full gate exists."]},"kept":true,"summary":"Improved LCP without bundle regression."}
```

### Evidence labels

For each important claim, mark it as one of:

- `measured`
- `inferred`
- `speculative`

Prefer measured evidence whenever possible.

### Optional memory payload

When an iteration teaches something likely to matter again, add a `memory` object with:

- `mistakes`
- `fixes`
- `prevention_rules`

If the repository ships a validator such as `tools/validate_ledger.py`, use it on `improvement/ledger.jsonl` after appending entries.
If the repository also ships an example object such as `improvement/templates/ledger-entry.json`, validate that too when changing the documented logging contract.
If the repository ships `tools/log_iteration.py`, prefer it for appending validated entries instead of hand-editing JSONL.
If the repository ships `tools/memory_context.py`, use it to turn the ledger and patterns back into a usable brief before the next hypothesis or task.

## Fitness vector

Treat evaluation as a lexicographic fitness vector:

1. **hard gates** must pass
2. **primary metric** decides the main winner
3. **secondary metrics** prevent hidden regressions
4. **simplicity / maintainability** breaks ties

This means a “faster but broken” or “slightly better but much uglier” change does not win.

## Task-type adapters

For detailed guidance, read `references/eval-catalog.md`.

### Bug fix

First create or run a reproduction.
Prefer a failing test before broad edits.
Success means the bug is fixed and nearby behavior still passes.

### Feature work

Translate the requested feature into acceptance checks.
Prefer incremental delivery and tests/snapshots where possible.

### Frontend

Protect build, typecheck, lint, visual stability, and accessibility.
Track bundle size and user-facing performance when relevant.

### Backend / API

Protect tests, schema/contracts, and correctness.
Track latency, query count, memory, and operational complexity when relevant.

### Model training / ML

Use a fixed budget, fixed seed/config where possible, and a clear validation metric.
Track runtime, VRAM, throughput, and code simplicity in addition to the main metric.

### Refactor

Behavior-lock first.
Prefer narrow structural cleanup over sweeping rewrites.
Measure complexity reduction if possible.

### Infra / deployment

Prefer validate/plan/dry-run before apply.
Track rollback clarity and blast radius.

### Data / ETL

Protect schema validity, sample correctness, and idempotency where relevant.
Track cost, runtime, and operator burden.

## Missing evals

When no credible evaluation exists, create the smallest one that makes progress real.
Examples:

- reproduction test
- benchmark harness
- snapshot test
- dry-run/plan validation
- fixed-budget training eval
- script that exercises the critical path

Do not claim strong improvement without some evaluation.

## Pattern learning

If you learn something that is likely to matter again in this repository, append a concise note to `improvement/patterns.md`.
Only store durable lessons, not ephemeral experiment noise.

Good durable lesson format:

```md
## Pattern: prefer request-scoped cache in product search
- Context: repeated DB hits in search aggregation path
- Signal: reduced query count and p95 latency in two separate tasks
- Caveat: safe only when tenant and locale are part of the cache key
```

## Communication style while using this skill

When reporting progress:

- say what step of the execution plan you are on
- say what hypothesis you tried
- say what you measured
- say whether you kept or reverted it
- make uncertainty explicit

Do not describe a change as an improvement unless the evaluation contract supports it.
