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

- **Python** — AST symbols + imports / inherit / decorators / calls. Gaps: full stubs, dynamic attrs.
- **JS/TS** — shallow symbols + imports / calls. Gaps: modules, framework wiring.
- **Go** — shallow symbols + imports / calls. Gaps: interfaces across packages.
- **Java** — Spring-aware P0: implements, `@Autowired`/`@Inject`/`@Resource` field injects, ctor injects, typed field calls. Gaps: `@Primary` multi-impl, AOP proxies, generics erasure, full classpath.

## Dual engines

Java trees prefer the **Python** indexer (Spring-aware). Rust gains `implements`; injects remain Python-first until ported. Parity tests: `tests/test_engine_parity.py` (CI).

## Benchmarks

- `local` / `public` — acceptance / smoke
- `ground-truth` — labeled P/R on fixtures (`benchmarks/ground-truth/`)

External corpora (Flask, FastAPI, PetClinic, Express) are **pinned in manifest**, labels pending human review.

## Authorize ≠ sandbox

Default verify path uses disposable worktree/copy, scrubbed env, timeouts, FS diff (`verify_isolate`). Still not a kernel/container jail. See `SECURITY.md`.

## Roadmap status

**Governing plan:** [`docs/strategy/2026-Q4-next-phase-plan.md`](strategy/2026-Q4-next-phase-plan.md) (V1.0, 12 weeks).

- **P0** Architecture audit + capability/defect inventory — **next**, no feature sprawl
- **P0** Benchmark V1 + annotation rules — with audit
- **P0** Agent A/B **execution** — **paused** until baseline
- **P1** Java/Spring semantic depth — after baseline
- Fixture DI / GT / isolate / parity / scene — earlier landings; not real-project proof

Earlier notes: `docs/superpowers/plans/2026-11-03-depth-over-surface.md`
