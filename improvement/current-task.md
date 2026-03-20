# Current task

- Task ID: 2026-03-20-pattern-recognition-tool
- Task name: Build a ledger-based pattern recognition tool
- Task type: data
- Desired outcome: Add a small tool that reads `improvement/ledger.jsonl`, detects recurring successful patterns, and outputs ranked pattern suggestions that can help maintain `improvement/patterns.md`.
- Non-goals: Introduce external dependencies, invent unsupported benchmark claims, or auto-edit `improvement/patterns.md` without an explicit review step.

## Constraints
- Use only the Python standard library.
- Keep the logic robust for sparse or uneven ledger history.
- Add tests that cover parsing, normalization, and pattern suggestion behavior.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format markdown`
- `python3 qa/verify_skill_system.py`

## Full gates
- Verify the tool produces stable suggestions on the current ledger and handles representative synthetic histories.
- `python3 qa/verify_skill_system.py`
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format json`

## Primary metric
- Name: pattern recognition tool produces useful ranked suggestions from the ledger
- Direction: higher_is_better
- Baseline: No dedicated tool exists; `python3 -m unittest discover -s qa -p 'test_*.py'` currently reports `NO TESTS RAN`.
- Target: The repository contains a tested CLI that emits structured pattern suggestions from ledger history.

## Secondary metrics
- QA verifier remains passing
- Tool output remains deterministic for the same ledger input
- Current repository instructions and templates remain unchanged in meaning

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format markdown
python3 qa/verify_skill_system.py

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format json
python3 qa/verify_skill_system.py
```

## Measurement notes
- deterministic or noisy: deterministic
- fixed seed / fixed sample / fixed budget: fixed ledger file and fixed synthetic test inputs
- proxy limitations: usefulness of detected patterns is partly heuristic, so tests should assert structure and representative ranking rather than exact prose everywhere

## Iteration budget
- Max iterations: 2
- Time budget: one focused implementation pass and one verification pass

## Rollback plan
- Revert the new tool and tests if they produce misleading pattern suggestions or fail deterministic checks.

## Stop conditions
- The repository has a working pattern-recognition CLI
- Tests pass
- QA verifier passes
