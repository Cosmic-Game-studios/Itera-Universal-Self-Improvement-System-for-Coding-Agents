# Current task

- Task ID: 2026-03-20-python-support-scripts
- Task name: Add Python support scripts for the self-improvement loop
- Task type: feature
- Desired outcome: Extend the repository with practical Python helpers that support the `swe-self-improve` workflow directly, especially for bootstrapping `improvement/current-task.md` and appending validated iteration records to `improvement/ledger.jsonl`.
- Non-goals: Build a fully autonomous orchestration system, add third-party dependencies, or replace the existing explicit keep-or-revert workflow with opaque automation.

## Execution plan
1. Rewrite the live task contract for the support-script expansion and log a fresh baseline.
2. Implement Python helpers for task bootstrapping and iteration logging, reusing the existing ledger validator where possible.
3. Add regression tests and QA checks so the new helpers are verified mechanically.
4. Document the helpers in the skill docs, fallback docs, templates, and README so they become part of the supported workflow.
5. Run full verification, log the kept result, review the final diff, and publish the improved state.

## Constraints
- Use only the Python standard library.
- Keep the helpers deterministic and compatible with the current repository structure.
- Reuse existing validation logic instead of creating duplicate contract rules.
- Preserve the explicit human-readable workflow instead of hiding key decisions behind magic defaults.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/bootstrap_task.py --task-id demo-task --task-name "Demo task" --task-type feature --desired-outcome "Demo outcome" --plan-step "Draft the contract" --fast-eval "python3 qa/verify_skill_system.py" --full-gate "python3 qa/verify_skill_system.py" --primary-metric-name quality --primary-metric-direction higher_is_better --primary-metric-baseline "not started" --primary-metric-target "scaffolded" --output /tmp/swe-self-improve-demo-current-task.md --overwrite`
- `python3 tools/log_iteration.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --task-id demo-task --iteration 0 --eval-tier fast+full --hypothesis "Baseline" --hard-gate qa_verify=pass --primary-metric-name quality --primary-metric-baseline 0 --primary-metric-value 0 --primary-metric-direction higher_is_better --secondary-metric qa_checks=80 --evidence qa_verify=measured --kept true --summary "Baseline entry."`

## Full gates
- Verify the new helpers execute successfully, the repo stays green, and the workflow/docs now advertise the new support scripts coherently.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/bootstrap_task.py --task-id demo-task --task-name "Demo task" --task-type feature --desired-outcome "Demo outcome" --plan-step "Draft the contract" --fast-eval "python3 qa/verify_skill_system.py" --full-gate "python3 qa/verify_skill_system.py" --primary-metric-name quality --primary-metric-direction higher_is_better --primary-metric-baseline "not started" --primary-metric-target "scaffolded" --output /tmp/swe-self-improve-demo-current-task.md --overwrite`
- `python3 tools/log_iteration.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --task-id demo-task --iteration 0 --eval-tier fast+full --hypothesis "Baseline" --hard-gate qa_verify=pass --primary-metric-name quality --primary-metric-baseline 0 --primary-metric-value 0 --primary-metric-direction higher_is_better --secondary-metric qa_checks=80 --evidence qa_verify=measured --kept true --summary "Baseline entry."`
- `python3 tools/validate_ledger.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --format json`
- `rg -n "bootstrap_task.py|log_iteration.py|support scripts|helper" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py`

## Primary metric
- Name: practical support scripts are available for the core workflow
- Direction: higher_is_better
- Baseline: the repository already ships analysis and validation helpers, but it still lacks direct Python helpers for bootstrapping the task contract and appending validated ledger iterations.
- Target: the repository ships both helpers, documents them, and mechanically verifies that they work.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Helper scripts reuse the ledger contract instead of drifting from it
- Skill wording stays aligned between Codex and Claude

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/bootstrap_task.py --task-id demo-task --task-name "Demo task" --task-type feature --desired-outcome "Demo outcome" --plan-step "Draft the contract" --fast-eval "python3 qa/verify_skill_system.py" --full-gate "python3 qa/verify_skill_system.py" --primary-metric-name quality --primary-metric-direction higher_is_better --primary-metric-baseline "not started" --primary-metric-target "scaffolded" --output /tmp/swe-self-improve-demo-current-task.md --overwrite
python3 tools/log_iteration.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --task-id demo-task --iteration 0 --eval-tier fast+full --hypothesis "Baseline" --hard-gate qa_verify=pass --primary-metric-name quality --primary-metric-baseline 0 --primary-metric-value 0 --primary-metric-direction higher_is_better --secondary-metric qa_checks=80 --evidence qa_verify=measured --kept true --summary "Baseline entry."

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/bootstrap_task.py --task-id demo-task --task-name "Demo task" --task-type feature --desired-outcome "Demo outcome" --plan-step "Draft the contract" --fast-eval "python3 qa/verify_skill_system.py" --full-gate "python3 qa/verify_skill_system.py" --primary-metric-name quality --primary-metric-direction higher_is_better --primary-metric-baseline "not started" --primary-metric-target "scaffolded" --output /tmp/swe-self-improve-demo-current-task.md --overwrite
python3 tools/log_iteration.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --task-id demo-task --iteration 0 --eval-tier fast+full --hypothesis "Baseline" --hard-gate qa_verify=pass --primary-metric-name quality --primary-metric-baseline 0 --primary-metric-value 0 --primary-metric-direction higher_is_better --secondary-metric qa_checks=80 --evidence qa_verify=measured --kept true --summary "Baseline entry."
python3 tools/validate_ledger.py --ledger /tmp/swe-self-improve-demo-ledger.jsonl --format json
rg -n "bootstrap_task.py|log_iteration.py|support scripts|helper" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be enough if the helpers, tests, and docs stay aligned
- fixed seed / fixed input / fixed budget: fixed repository contents and fixed demo CLI arguments for the helper smoke checks
- proxy limitations: wording scans are structural proxies, so they must stay paired with real helper execution

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert helpers that duplicate existing contract logic instead of reusing the validator.
- Revert docs that advertise support scripts the QA suite does not actually exercise.

## Stop conditions
- The repository ships Python helpers for task bootstrapping and validated iteration logging
- Tests and QA both verify those helpers
- Docs and skill files reflect the new helper support
- Final verification passes cleanly
