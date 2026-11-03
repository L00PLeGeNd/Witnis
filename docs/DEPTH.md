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

External corpora (Flask, FastAPI, PetClinic, Express) are **pinned in manifest**, labels pending human review.

## Authorize ≠ sandbox

Default verify path uses disposable worktree/copy, scrubbed env, timeouts, FS diff (`verify_isolate`). Still not a kernel/container jail. See `SECURITY.md`.

## Roadmap status

| Priority | Item | Status |
|---|---|---|
| P0 | Java/Spring semantics (implements / injects / typed calls) | **landed** on fixtures |
| P0 | Ground-truth runner + labels | **landed** (vendored); external labels open |
| P1 | Verify isolation | **landed** (worktree/copy + env + FS diff); container TBD |
| P1 | Dual-engine parity CI | **landed** |
| P2 | Agent effect experiment | **protocol + task scaffold** |

Plan: `docs/superpowers/plans/2026-11-03-depth-over-surface.md`
