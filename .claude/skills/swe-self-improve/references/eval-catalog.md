# Eval Catalog

Use this catalog to build the task contract in `improvement/current-task.md`.
Choose the smallest set of hard gates that makes regressions unlikely, then choose one primary metric.
For most real tasks, split checks into:

- **fast-loop evals**: cheap checks run every iteration
- **full gates**: broader checks run before final keep

## 1. Bug fixing

### Typical fast-loop evals
- reproduction test
- targeted unit/integration tests
- lint/typecheck on touched areas

### Typical full gates
- relevant broader suite
- build and packaging checks

### Typical primary metric
- bug reproduction goes from failing to passing

### Useful secondary metrics
- changed-file count
- unrelated test failures
- runtime on the affected path
- readability / diff size

## 2. Feature work

### Typical fast-loop evals
- targeted acceptance checks
- narrow smoke tests
- build/lint/typecheck for touched surfaces

### Typical full gates
- broader acceptance or regression suite
- API or schema contract checks

### Typical primary metric
- feature acceptance criteria met

### Useful secondary metrics
- performance on touched path
- code size / complexity
- rollout safety

## 3. Frontend

### Typical fast-loop evals
- route/component build
- focused component or e2e test
- local accessibility smoke check

### Typical full gates
- full build / typecheck / lint
- broader visual or snapshot coverage
- broader accessibility and user-facing performance checks

### Typical primary metric
- acceptance correctness or user-visible performance target

### Useful secondary metrics
- bundle size
- LCP / INP / CLS or Lighthouse subscores
- snapshot / screenshot stability
- hydration errors
- JS errors in console

### Notes
Prefer before/after screenshots or visual assertions when the change is UI-heavy.
If no automated UX metric exists, mark UX judgments as inferred rather than measured.

## 4. Backend / API

### Typical fast-loop evals
- targeted unit tests
- focused integration tests
- local benchmark on the hot path

### Typical full gates
- full relevant service tests
- schema/contracts
- migration validation when relevant

### Typical primary metric
- correctness for the target behavior

### Useful secondary metrics
- p95 or p99 latency
- DB query count
- allocation count
- memory footprint
- log noise / operational complexity

## 5. Performance tuning

### Typical fast-loop evals
- stable microbenchmark
- hot-path correctness tests

### Typical full gates
- broader benchmark suite
- representative workload replay when available

### Typical primary metric
- p95 latency, throughput, CPU time, memory, bundle size, etc.

### Useful secondary metrics
- code complexity increase
- variance across runs
- maintainability / readability

### Notes
Keep the benchmark setup fixed across iterations.
Use medians or repeated runs if measurements are noisy.

## 6. Refactor

### Typical fast-loop evals
- behavior-lock tests for touched modules
- build / lint / typecheck

### Typical full gates
- broader regression suite
- packaging/public API verification

### Typical primary metric
- preserved behavior with reduced structural complexity

### Useful secondary metrics
- lines deleted
- duplication reduced
- cyclomatic complexity
- module boundary clarity
- onboarding readability

### Notes
For refactors, the “primary metric” is often partly qualitative.
Compensate by making hard gates especially strong.

## 7. Model training / ML experimentation

### Typical fast-loop evals
- reduced-budget training/eval run
- fixed seed/config smoke run

### Typical full gates
- final validation metric on the real comparison budget
- logging and reproducibility checks

### Typical primary metric
- validation loss / accuracy / reward / task score under a fixed budget

### Useful secondary metrics
- wall-clock time
- VRAM / RAM
- throughput
- parameter count
- code simplicity

### Notes
This is the closest match to Karpathy-style autoresearch.
Keep the time/data budget fixed for fair comparison.
Do not compare a cheap proxy run to a full-budget baseline without calling out the limitation.

## 8. Infra / deployment

### Typical fast-loop evals
- formatter / validator
- dry-run / plan
- narrow config linting

### Typical full gates
- policy/security checks
- broader rollout or dependency review
- explicit rollback validation

### Typical primary metric
- successful, low-risk configuration change toward the target outcome

### Useful secondary metrics
- blast radius
- rollback clarity
- number of moving parts
- secret handling risk
- observability coverage

### Notes
Prefer plan-first workflows and explicit rollback notes.

## 9. Data pipelines / ETL

### Typical fast-loop evals
- sample transform run
- schema checks on representative data

### Typical full gates
- larger sample or backfill rehearsal
- idempotency and completeness checks

### Typical primary metric
- correctness / completeness of transformed output

### Useful secondary metrics
- runtime
- cloud cost
- memory
- operator burden

## 10. When you truly cannot measure much

Use the smallest credible proxy.
Examples:
- reproducible manual checklist
- golden file comparison
- snapshot diff
- script that exercises the key path
- pair of before/after screenshots

When using a proxy, say explicitly that the result is only partially measured.
If the proxy is the only available evaluation, say that the final outcome remains provisional.
