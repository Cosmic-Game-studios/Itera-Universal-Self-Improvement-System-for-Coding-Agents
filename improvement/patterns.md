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

## Pattern: turn the ledger contract into an executable check
- Context: the ledger is the repository's memory for baselines, kept iterations, and durable pattern extraction.
- Signal: the workflow becomes safer when the live ledger and its example template are both validated by a dedicated tool instead of only being described in prose.
- Caveat: keep the validator strict on contract shape, but avoid overfitting it to one narrow metric style.

## Pattern: script the repetitive workflow edges
- Context: task scaffolding and ledger appends are repeated in almost every self-improvement run.
- Signal: small support scripts reduce copy-paste mistakes while keeping the contract explicit and human-reviewable.
- Caveat: helpers should stay thin wrappers around the documented workflow, not opaque automation that hides decisions.

## Pattern: review loop state before spending another iteration
- Context: bounded improvement works better when the team checks budget, recent failures, and the current best state instead of reflexively starting another hypothesis.
- Signal: a small advisory loop-state review step makes stop conditions more real and reduces mindless churn.
- Caveat: the review should inform judgment, not pretend that a heuristic can fully decide whether the task is done.

## Pattern: log reusable mistakes and prevention rules, not just outcomes
- Context: a self-improvement loop gets stronger when it remembers which errors happened, how they were corrected, and what rule should prevent them next time.
- Signal: structured episodic-memory fields make it easier to turn one iteration's lesson into the next iteration's starting context instead of repeating the same avoidable mistake.
- Caveat: keep the memory payload concise and grounded in explicit evidence; do not turn the ledger into a speculative diary.

## Pattern: prefer explicit scoring rules over opaque overall scores
- Context: keep-or-revert decisions are easier to trust when the comparison logic names the protected metrics and the allowed regressions instead of collapsing everything into one unexplained number.
- Signal: a rule-driven scoring helper makes the fitness vector operational while still preserving clear reasons for why a candidate was kept, rejected, or flagged for manual review.
- Caveat: scoring should support judgment, not replace it; unresolved or poorly specified metrics should stay visible instead of being guessed away.
