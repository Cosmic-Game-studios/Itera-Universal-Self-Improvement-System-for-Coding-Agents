# Durable repository patterns

Add only lessons likely to help future tasks.
Do not dump every experiment result here.

Recommended format:

## Pattern: <short title>
- Context:
- Signal:
- Caveat:

## Pattern: keep `qa_verify` as the universal hard gate
- Context: every kept self-improvement task in this repository has ended with the structural QA verifier.
- Signal: the existing ledger shows `qa_verify` passing in every kept run, even when the task focus changed from docs to tooling and publishing.
- Caveat: this gate is structural, so task-specific tests and runtime checks still need to be paired with it.

## Pattern: verify README changes on GitHub when Mermaid or positioning changes are involved
- Context: README work in this repository often includes Mermaid diagrams and GitHub-facing presentation changes.
- Signal: kept README iterations repeatedly paired local QA with a live GitHub README check to catch rendering and presentation issues that local text inspection could miss.
- Caveat: this is most important for README and diagram edits, not for every internal-only repository change.

## Pattern: update `improvement/` artifacts together with the kept change
- Context: the repository treats self-improvement as a logged workflow rather than a one-shot edit.
- Signal: kept runs consistently updated `improvement/current-task.md` and `improvement/ledger.jsonl` alongside the winning change, which made later review and pattern extraction easier.
- Caveat: avoid dumping transient exploration noise into durable artifacts; record the final kept state and only the iteration history the user asked to preserve.

## Pattern: make the execution plan explicit before the first edit
- Context: evaluation-first loops are easier to review and keep aligned when the intended order of attack is visible up front.
- Signal: the workflow became more robust once the skill, fallback docs, template, and QA all required an explicit execution plan instead of leaving planning implicit.
- Caveat: keep the plan short and concrete; the point is to guide the iteration loop, not to create heavyweight ceremony.

## Pattern: split large sweeps into area budgets before spending runs
- Context: very large repository-wide efforts become noisy and hard to keep bounded when all files share one flat iteration queue.
- Signal: program-mode guidance is clearer and safer when the repository is mapped into areas with explicit run budgets and checkpoints between areas.
- Caveat: area budgets are starting points, not rigid promises; reallocate when evidence says one area is lower value than expected.
