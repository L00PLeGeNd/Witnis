# Technical depth — honest status

Witnis is an early **engineering witness**: strong product/architecture intent, real local Core. Depth work is gated before any “leading infrastructure” claim.

## Competitive bar (not grep)

Peers in the space: SCIP, LSIF, Kythe, IDE language servers.

Witnis must prove value **for agents** that those stacks do not package together:

- Evidence envelopes with explicit uncertainty
- Impact / blast-radius answers agents can cite
- **Gated + isolated** verification before “tests passed” claims
- Host-neutral MCP/CLI contracts without an LLM in Core

Beating `git grep` is necessary but not sufficient.

## Language depth

| Language | Depth today | Gaps |
|---|---|---|
| Python | AST symbols + imports / inherit / decorators / calls | Full stubs, dynamic attrs |
| JS/TS | Shallow symbols + imports / calls | Modules, framework wiring |
| Go | Shallow symbols + imports / calls | Interfaces across packages |
| Java | **Spring-aware P0**: implements, `@Autowired`/`@Inject`/`@Resource` field injects, ctor injects, typed field calls | `@Primary` multi-impl, AOP proxies, generics erasure, full classpath |

## Dual engines

Java trees prefer the **Python** indexer (Spring-aware). Rust gains `implements`; injects remain Python-first until ported. Parity tests: `tests/test_engine_parity.py` (CI).

## Benchmarks

| Suite | Meaning |
|---|---|
| `local` / `public` | Acceptance / smoke |
| `ground-truth` | Labeled P/R on fixtures (`benchmarks/ground-truth/`) |

External corpora (Flask, FastAPI, PetClinic, Express) are **pinned in manifest**. PetClinic **human-v2 adjudicated** (16 tasks; not dual-human); see [`benchmarks/petclinic-human-v2.md`](benchmarks/petclinic-human-v2.md).  
Honest misses (product + GT): [`FAILURE_CASES.md`](FAILURE_CASES.md).

## Authorize ≠ sandbox

Default verify path uses disposable worktree/copy, scrubbed env, timeouts, FS diff (`verify_isolate`). Still not a kernel/container jail. See `SECURITY.md`.

## Roadmap status

**External sequencing:** [`ROADMAP.md`](../ROADMAP.md) · [`docs/strategy/2026-open-source-landing-plan.md`](strategy/2026-open-source-landing-plan.md)  
**Engineering / experiments notebook:** [`docs/strategy/2026-Q4-next-phase-plan.md`](strategy/2026-Q4-next-phase-plan.md) (V1.1).

| Priority | Item | Status |
|---|---|---|
| P0 | Trusted Agent Loop: `pr-gate` (three-dot) + Action + Harnis templates | **landed** (keep hardening) |
| P0 | PetClinic human GT + Benchmark V1 P/R | human-v2 adjudicated (16 tasks); Direct+Indirect P/R 1.0 on subset after `uses_type` (F1 mitigated); dual-human still open |
| P0 | Failure-case gallery | **landed** [`FAILURE_CASES.md`](FAILURE_CASES.md) |
| P0 | Conversion: binary + browser demo | binary + `witnis browser-demo` landed; Studio redesign still deferred |
| P0 | Starter seed + Issue/Discussion templates | **landed** `examples/witnis-harnis-starter` + `.github/` templates |
| P1 | MCP directory listings | **payloads landed** (`docs/mcp-listings.md`); submit after push |
| P0 | Agent A/B **execution** | **paused** until baseline |
| P1 | Java/Spring semantic depth | **paused** — reassess after Stage-1 + GT |
| — | verify `automation_verified` honesty; worktree pin to revision; contradicted on fail | landed with loop |
| — | Architecture audit / D01–D03 / fixture DI / isolate / scene | landed; not real-project proof alone |

Earlier notes: `docs/superpowers/plans/2026-11-03-depth-over-surface.md`
