# Current task

- Task ID: 2026-03-20-agent-memory-hardening
- Task name: Operationalize memory for coding-agent self-improvement
- Task type: feature
- Desired outcome: Make the swe-self-improve workflow explicitly use working, episodic, learned, and procedural memory so future tasks can recall past mistakes, fixes, and prevention rules instead of repeating them.
- Non-goals:
- Build a hidden autonomous controller that replaces human judgment.
- Rewrite old ledger history into a new schema.
- Add third-party Python dependencies.

## Execution plan
- Rewrite the live task contract and capture a fresh baseline for the memory-hardening task.
- Extend the ledger contract plus logging helper with optional structured memory fields for mistakes, fixes, and prevention rules.
- Add a deterministic memory helper that composes current-task, ledger history, and durable patterns into a reusable brief for the next task or iteration.
- Propagate the memory model through the skill docs, fallback docs, templates, README, and QA checks.
- Run full verification, log the kept result, and review the final system for coherence.

## Optional: Area coverage plan
- <root docs / skills / tools / qa / improvement / templates / other areas>

## Optional: Run budget allocation
- <area>: <planned runs>

## Constraints
- Use only the Python standard library.
- Keep the memory layer advisory and transparent rather than opaque or magical.
- Preserve backward compatibility with existing ledger entries and current task files.
- Make the same memory model visible across Codex and Claude workflow surfaces.

## Memory refresh
- Working memory: `improvement/current-task.md`
- Episodic memory: `improvement/ledger.jsonl`
- Learned memory: `improvement/patterns.md`
- Procedural memory: `AGENTS.md` / `CLAUDE.md` / `SKILL.md`
- Refresh command: `python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary`
- Mistakes to avoid: there is no structured episodic-memory payload in the older runs yet, so the new helper and logging contract need to create that path without breaking history.
- Reusable fixes: keep the memory helper deterministic and grounded in explicit repository artifacts instead of inventing advice.

## Fast-loop evals
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary

## Full gates
- Verify that the repository ships a usable memory helper, structured episodic-memory support, green tests, green QA, and coherent docs across the skill stack.
- python3 -m unittest discover -s qa -p 'test_*.py'
- python3 qa/verify_skill_system.py
- python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format json
- rg -n 'working memory|episodic memory|procedural memory|learned memory|memory brief|mistakes|prevention' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools

## Primary metric
- Name: agent memory model is operationally available across the workflow stack
- Direction: higher_is_better
- Baseline: the repository documents iteration discipline but does not yet provide a first-class memory brief or structured episodic-memory fields for recording mistakes, fixes, and prevention rules.
- Target: the repository ships memory-aware helpers, ledger support, documentation, and QA so agents can refresh the current task, recall past mistakes, and reuse durable lessons before new work.

## Secondary metrics
- QA verifier remains green
- Existing unit tests remain green
- Live ledger stays backward-compatible and valid
- Memory guidance remains explicit and auditable

## Evaluation commands
```bash
python3 -m unittest discover -s qa -p 'test_*.py'
python3 qa/verify_skill_system.py
python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format summary
python3 tools/memory_context.py --task improvement/current-task.md --ledger improvement/ledger.jsonl --patterns improvement/patterns.md --format json
rg -n 'working memory|episodic memory|procedural memory|learned memory|memory brief|mistakes|prevention' README.md .agents/skills/swe-self-improve/SKILL.md .claude/skills/swe-self-improve/SKILL.md AGENTS.md CLAUDE.md global-templates improvement/templates qa tools
```

## Measurement notes
- deterministic or noisy: deterministic
- repeated runs needed: one baseline and one kept implementation run should be sufficient if the helper, docs, and QA land coherently
- fixed seed / fixed input / fixed budget: fixed repository contents with the live improvement artifacts as input
- proxy limitations: text scans are only structural proxies, so they must stay paired with helper execution and full verification

## Iteration budget
- Max iterations: 2
- Max task time: one focused implementation pass and one final verification pass

## Rollback / checkpoint strategy
- Revert any memory helper behavior that invents facts instead of summarizing explicit repository state.
- Revert any ledger contract tightening that would invalidate the repository's older entries without a compatibility path.

## Stop conditions
- The repository ships an explicit memory helper that runs on the live artifacts.
- The ledger can record mistakes, fixes, and prevention rules without breaking historical entries.
- Skill docs, fallback docs, templates, and README all encode the same four-memory model.
- Final verification passes cleanly.
