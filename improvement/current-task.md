# Current task

- Task ID: 2026-03-20-github-mermaid-fix
- Task name: Fix the GitHub Mermaid rendering error in the agent-flow diagram
- Task type: documentation
- Desired outcome: Update the README Mermaid diagram so GitHub renders it successfully while preserving the explanation of how the skill affects the current agent.
- Non-goals: Change the meaning of the workflow, redesign unrelated README sections, or alter runtime skill behavior.

## Constraints
- Keep the explanation accurate to the current repository behavior.
- Use Mermaid syntax that GitHub accepts reliably.
- Keep the diff small and documentation-focused.

## Fast-loop evals
- `rg -n '<br/>|`' README.md`
- `python3 qa/verify_skill_system.py`
- `git diff -- README.md`

## Full gates
- Verify the README still explains the same agent flow after the syntax simplification.
- `python3 qa/verify_skill_system.py`
- Confirm the GitHub repository page no longer shows the Mermaid lexical error.

## Primary metric
- Name: GitHub README diagram renders without Mermaid syntax errors
- Direction: higher_is_better
- Baseline: GitHub reports a Mermaid lexical error on the current diagram; the offending nodes contain inline-code backticks and HTML `<br/>` inside labels.
- Target: The diagram renders on GitHub and still communicates the same flow.

## Secondary metrics
- QA verifier remains passing
- README meaning stays accurate
- Git diff remains limited to the Mermaid fix and task logging

## Evaluation commands
```bash
# fast-loop commands
rg -n '<br/>|`' README.md
python3 qa/verify_skill_system.py
git diff -- README.md

# full-gate commands
python3 qa/verify_skill_system.py
git push
```

## Measurement notes
- deterministic or noisy: deterministic except for GitHub page rendering latency
- fixed seed / fixed sample / fixed budget: fixed README section and fixed GitHub repository page
- proxy limitations: local grep can confirm removal of risky syntax, but final success depends on GitHub's Mermaid renderer, so a browser check is required

## Iteration budget
- Max iterations: 2
- Time budget: one focused README syntax fix and one GitHub verification pass

## Rollback plan
- Revert the README Mermaid hunk if the simplified labels reduce clarity or GitHub still fails to render.

## Stop conditions
- The Mermaid block is simplified to GitHub-compatible syntax
- QA verifier passes
- GitHub renders the README diagram without the reported lexical error
