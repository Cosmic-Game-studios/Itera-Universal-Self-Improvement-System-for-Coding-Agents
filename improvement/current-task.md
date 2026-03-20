# Current task

- Task ID: 2026-03-20-ledger-contract-hardening
- Task name: Harden the self-improvement ledger contract
- Task type: refactor
- Desired outcome: Upgrade the skill system so `improvement/ledger.jsonl` is enforced by a real validator tool, covered by tests, wired into QA, and documented as part of the standard keep-or-revert workflow.
- Non-goals: Rewrite historical ledger entries, add third-party dependencies, or make the ledger contract so rigid that normal SWE tasks can no longer log reasonable measured results.

## Execution plan
1. Rewrite the live task contract for ledger-contract hardening and log a fresh baseline.
2. Implement a standard-library ledger validation helper that checks the documented logging contract and reports useful failures.
3. Add regression tests and QA coverage so both the live ledger and the example template are validated mechanically.
4. Propagate the stronger ledger-validation rule through the skills, fallback docs, templates, README, and durable patterns.
5. Run full verification, log the kept result, review the final diff, and publish the improved state.

## Constraints
- Use only the Python standard library.
- Keep the validator compatible with the repository's existing ledger history.
- Strengthen the contract without turning the workflow into heavy ceremony.
- Keep Codex, Claude, fallback docs, and README wording aligned.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/validate_ledger.py --ledger improvement/ledger.jsonl --format summary`

## Full gates
- Verify the live ledger and the example ledger template both satisfy the documented contract, while the rest of the repository remains green.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/validate_ledger.py --ledger improvement/ledger.jsonl --format json`
- `python3 tools/validate_ledger.py --ledger improvement/templates/ledger-entry.json --single-json --format json`
- `rg -n "validate_ledger|ledger contract|ledger-entry.json|Evidence labels" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py`

## Primary metric
- Name: ledger contract is explicitly enforced end to end
- Direction: higher_is_better
- Baseline: the repository parses the live ledger and checks a few core fields, but it does not yet ship a dedicated ledger validator or mechanically validate the documented ledger-entry template.
- Target: the repository ships a validator, verifies the live ledger plus template with it, and documents ledger validation as part of the workflow.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- The validator works on both JSONL and single-object example input
- Skill wording stays aligned between Codex and Claude

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/validate_ledger.py --ledger improvement/ledger.jsonl --format summary

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/validate_ledger.py --ledger improvement/ledger.jsonl --format json
python3 tools/validate_ledger.py --ledger improvement/templates/ledger-entry.json --single-json --format json
rg -n "validate_ledger|ledger contract|ledger-entry.json|Evidence labels" README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline run and one kept implementation run should be enough if the validator, tests, and docs land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents and the current live ledger plus shipped example template
- proxy limitations: wording checks are still structural proxies, so they must stay paired with real validator execution

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one full verification pass

## Rollback / checkpoint strategy
- Revert any validator rules that reject the repository's valid existing ledger history without a strong contract reason.
- Revert documentation churn that does not map to an actual executable validation step.

## Stop conditions
- The repository ships a working ledger validator
- QA uses that validator on the live ledger and the example template
- Docs and skill files reflect the stronger ledger-validation workflow
- Tests and QA both pass
