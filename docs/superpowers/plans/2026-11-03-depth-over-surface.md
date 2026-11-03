# Plan: Depth over surface (Witnis)

## Goal

Stop growing tool/language surface. Prove (or honestly bound) **engineering understanding** on real relations, real ground truth, and dual-engine consistency.

## Non-goals

- More MCP tools / Studio locales / marketing claims of “industry-leading”
- Expanding to 5th/6th languages before Java/TS/Go/Python call graphs are trustworthy

## P0 tasks

### 1. Honest docs (this PR)

- State that public 21/21 is **acceptance**, not semantic accuracy
- Align README / contracts version strings with package version
- Separate **authorize gate** from **execution sandbox** in SECURITY

### 2. Ground-truth benchmark scaffold

- Schema under `benchmarks/ground-truth/`
- Metrics: symbol P/R, edge P/R, impact recall, evidence accuracy, false-pass rate
- No claim of 100% until corpora + human labels exist

### 3. Semantic fixture: Spring-style DI (Java)

- Tiny Apache-2.0 original fixture exercising `@Autowired` / interface→impl
- Document current Witnis **misses**; add failing or `xfail` expectations

### 4. Dual-engine contract tests

- Same repo → Python index vs Rust index → compare symbols/relations within tolerance
- Fail CI on unexplained diffs for supported fixtures

## P1 (next plans)

- Isolated verify workspace (temp dir / optional container / timeouts / net deny)
- Fixed-commit corpora: Flask/FastAPI slice, Spring PetClinic slice, TS service
- Agent task success / token cost experiments (manual protocol first)

## Success criteria for “mature witness”

- Published P/R on labeled real slices (not only mini fixtures)
- False-pass rate tracked for verify
- Python/Rust parity green on supported languages
- Limitations listed per language (Spring DI, AOP, dynamic calls, …)

## Progress (2026-11-03 → 1.9.0)

- [x] Honest docs: `docs/DEPTH.md`, README/PUBLIC/SECURITY
- [x] Ground-truth runner: `witnis bench --suite ground-truth` (Java DI + Python DI labels)
- [x] Java Spring-aware relations: implements / injects / typed field calls
- [x] Dual-engine parity tests in CI: `tests/test_engine_parity.py`
- [x] Verify isolation default: worktree/copy + scrubbed env + FS diff
- [x] Agent effect protocol scaffold: `docs/experiments/agent-effect-protocol.md`
- [ ] External corpora human labels (Flask / FastAPI / PetClinic / Express) — manifest pinned, labels open
- [ ] Container/OS jail + cgroup caps
- [ ] Automated agent A/B runner + published effect numbers
- [ ] Rust port of Java injects for full parity on DI trees
