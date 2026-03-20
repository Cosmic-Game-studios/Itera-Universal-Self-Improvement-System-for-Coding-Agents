# Current task

- Task ID: 2026-03-20-self-improve-20-runs
- Task name: Use the skill to improve this repository itself until the ledger reaches 20 runs
- Task type: refactor
- Desired outcome: Strengthen the repository's own self-improvement scaffolding with a bounded multi-run program that improves QA coverage, durable pattern capture, and self-application documentation while bringing the ledger to 20 total runs.
- Non-goals: Inflate the ledger with fake no-op wins, introduce external dependencies, or make claims that were not supported by repository-local evaluation.

## Constraints
- Use only the Python standard library.
- Keep each iteration small and reversible.
- Prefer improvements that measurably strengthen self-improvement support in this repo.

## Fast-loop evals
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format markdown`

## Full gates
- Verify the repository still passes QA, the pattern tool still emits stable output, and the self-improvement artifacts become more useful for future runs.
- `python3 -m unittest discover -s qa -p 'test_*.py'`
- `python3 qa/verify_skill_system.py`
- `python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format json`

## Primary metric
- Name: self-improvement support checks passing in `qa/verify_skill_system.py`
- Direction: higher_is_better
- Baseline: 37 passed checks before this new self-improvement program begins.
- Target: Increase the number of meaningful passed support checks while keeping all hard gates green.

## Secondary metrics
- Total ledger entries reaches 20
- `improvement/patterns.md` contains durable reviewed lessons
- Unit test count stays green or improves
- Pattern-recognition output remains deterministic for the same ledger input

## Evaluation commands
```bash
# fast-loop commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format markdown

# full-gate commands
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/pattern_recognition.py --ledger improvement/ledger.jsonl --format json
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one run per hypothesis, with final gates on the kept state
- fixed seed / fixed input / fixed budget: fixed repository contents and fixed ledger history per iteration
- proxy limitations: QA pass-count is only meaningful when new checks correspond to real repository guarantees rather than metric gaming

## Iteration budget
- Max iterations: 7
- Max task time: one focused multi-run self-improvement session that brings the total ledger history to 20 entries

## Rollback / checkpoint strategy
- Keep only iterations that increase real repository support while preserving green gates; discard speculative or metric-gamed changes.

## Stop conditions
- Ledger has 20 total entries
- `qa/verify_skill_system.py` still passes
- The kept state leaves the repository materially better at running future `swe-self-improve` loops on itself
