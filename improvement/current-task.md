# Current task

- Task ID: 2026-03-20-readme-system-diagram
- Task name: Add a clearer high-level system diagram to the README
- Task type: documentation
- Desired outcome: Extend the README with a second GitHub-safe Mermaid diagram that shows the high-level relationship between the user, the current coding agent, the skill files, and the persistent `improvement/` artifacts.
- Non-goals: Change the workflow semantics, remove the existing iteration-flow diagram, or introduce Mermaid features that GitHub may render inconsistently.

## Constraints
- Keep the explanation accurate to the current repository behavior.
- Use Mermaid syntax that GitHub accepts reliably.
- Keep the diff small and focused on the README plus task logging.

## Fast-loop evals
- `rg -n 'System view|Iteration flow|```mermaid' README.md`
- `python3 qa/verify_skill_system.py`
- `git diff -- README.md`

## Full gates
- Verify the README still presents the same workflow, now with both a system view and an iteration flow.
- `python3 qa/verify_skill_system.py`
- Confirm on GitHub that both Mermaid diagrams render without error.

## Primary metric
- Name: README has a clearer high-level system diagram that renders on GitHub
- Direction: higher_is_better
- Baseline: The README currently has one working iteration-flow Mermaid diagram and a role table, but no separate visual system overview.
- Target: The README includes a second Mermaid system diagram that makes the architecture easier to grasp at a glance.

## Secondary metrics
- QA verifier remains passing
- GitHub render stays error-free
- Existing README meaning remains accurate

## Evaluation commands
```bash
# fast-loop commands
rg -n 'System view|Iteration flow|```mermaid' README.md
python3 qa/verify_skill_system.py
git diff -- README.md

# full-gate commands
python3 qa/verify_skill_system.py
git push
```

## Measurement notes
- deterministic or noisy: deterministic except for GitHub page rendering latency
- fixed seed / fixed sample / fixed budget: fixed README section and fixed GitHub repository page
- proxy limitations: local checks can confirm syntax presence, but final success depends on GitHub's Mermaid renderer, so a browser check is required

## Iteration budget
- Max iterations: 2
- Time budget: one focused README documentation pass and one GitHub verification pass

## Rollback plan
- Revert the new diagram block if GitHub fails to render it or if it makes the section harder to understand.

## Stop conditions
- README contains a second, clearer Mermaid system diagram
- QA verifier passes
- GitHub renders both diagrams without error
