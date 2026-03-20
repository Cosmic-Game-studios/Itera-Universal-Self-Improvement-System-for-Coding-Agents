# Current task

- Task ID: 2026-03-20-github-repo-import
- Task name: Publish the complete project into the target GitHub repository
- Task type: infra / deployment
- Desired outcome: Initialize Git for this project, preserve the existing remote `LICENSE`, commit the full project, and push it to `main` on the target GitHub repository.
- Non-goals: Change core project behavior, rewrite repository content unrelated to publishing, or force-push over unknown remote history.

## Constraints
- The remote already contains a `main` branch and one `LICENSE` commit, so integrate with it instead of overwriting it.
- Avoid committing transient local artifacts such as `.DS_Store`.
- Keep the repository content aligned with the verified local project state.

## Fast-loop evals
- `git status --short`
- `git log --oneline --decorate -n 3`
- `python3 qa/verify_skill_system.py`

## Full gates
- Verify the pushed remote branch contains the project files and expected head commit
- `python3 qa/verify_skill_system.py`

## Primary metric
- Name: target GitHub repository contains the complete project on `main`
- Direction: higher_is_better
- Baseline: Remote repository only contains `LICENSE`; this local directory is not yet a Git repository.
- Target: Remote `main` points to a commit that contains the full project tree plus the existing `LICENSE`.

## Secondary metrics
- QA verifier remains passing
- No unwanted local junk files are committed
- Remote history is advanced safely without force push

## Evaluation commands
```bash
# fast-loop commands
git status --short
git log --oneline --decorate -n 3
python3 qa/verify_skill_system.py

# full-gate commands
python3 qa/verify_skill_system.py
git ls-remote https://github.com/Cosmic-Game-studios/Itera-Universal-Self-Improvement-System-for-Coding-Agents.git
```

## Measurement notes
- deterministic or noisy: deterministic
- fixed seed / fixed sample / fixed budget: fixed local tree, fixed remote URL, static QA script
- proxy limitations: push success depends on available GitHub credentials in this environment

## Iteration budget
- Max iterations: 2
- Time budget: one focused repo-import pass with one verification pass

## Rollback plan
- If publish setup fails before push, keep the local filesystem intact and stop without forcing remote changes.

## Stop conditions
- Local project is committed on `main`, connected to the target remote, and push succeeds
- QA verifier passes on the published state
- If credentials block push, stop after preparing the repository and report the exact blocker
