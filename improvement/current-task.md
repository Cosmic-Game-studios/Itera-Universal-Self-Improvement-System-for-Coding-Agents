# Current task

- Task ID: 2026-03-20-readme-comparison-and-positioning
- Task name: Add a with-vs-without comparison and strengthen the README positioning
- Task type: documentation
- Desired outcome: Make the README more compelling by improving the top-level value proposition and adding a clear comparison that shows how work changes with and without the `swe-self-improve` skill.
- Non-goals: Misrepresent project capabilities, remove the existing diagrams, or turn the README into hype without substance.

## Constraints
- Keep the explanation accurate to the current repository behavior.
- Use GitHub-safe Mermaid syntax.
- Make the README more persuasive through clarity and structure, not exaggerated claims.

## Fast-loop evals
- `rg -n 'Why This Repo Is Useful|With The Skill vs Without The Skill|Without the skill|With the skill|```mermaid' README.md`
- `python3 qa/verify_skill_system.py`
- `git diff -- README.md`

## Full gates
- Verify the README now has a stronger opening and a clear with-vs-without comparison.
- `python3 qa/verify_skill_system.py`
- Confirm on GitHub that the new Mermaid diagram renders and the README still reads cleanly.

## Primary metric
- Name: README communicates the value proposition and with-vs-without comparison more clearly
- Direction: higher_is_better
- Baseline: The README explains the system well, but the opening is still fairly generic and there is no direct visual comparison between working with the skill and working without it.
- Target: The README quickly tells visitors why the project is useful and shows the practical difference between using the skill and not using it.

## Secondary metrics
- QA verifier remains passing
- GitHub render stays error-free
- Existing workflow explanation remains accurate

## Evaluation commands
```bash
# fast-loop commands
rg -n 'Why This Repo Is Useful|With The Skill vs Without The Skill|Without the skill|With the skill|```mermaid' README.md
python3 qa/verify_skill_system.py
git diff -- README.md

# full-gate commands
python3 qa/verify_skill_system.py
git push
```

## Measurement notes
- deterministic or noisy: deterministic except for GitHub page rendering latency
- fixed seed / fixed sample / fixed budget: fixed README section and fixed GitHub repository page
- proxy limitations: quality of positioning is partly qualitative, so live GitHub review is still needed after local checks

## Iteration budget
- Max iterations: 2
- Time budget: one focused README pass and one GitHub verification pass

## Rollback plan
- Revert the new comparison and positioning sections if they reduce clarity or if the new diagram fails to render on GitHub.

## Stop conditions
- README has a stronger opening and a clear with-vs-without comparison
- QA verifier passes
- GitHub renders the new comparison diagram without error
