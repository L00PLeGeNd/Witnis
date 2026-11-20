# Technical depth

Witnis is a local engineering witness: evidence envelopes, blast-radius impact, gated verify. Not a claim of SCIP/LSIF/Kythe parity.

## Language depth

| Language | Depth today | Gaps |
|---|---|---|
| Python | AST symbols + imports / inherit / decorators / calls | Full stubs, dynamic attrs |
| JS/TS | Shallow symbols + imports / calls | Modules, framework wiring |
| Go | Shallow symbols + imports / calls | Interfaces across packages |
| Java | Spring-aware: implements, `@Autowired`/`@Inject`/`@Resource`, ctor injects, typed field calls | `@Primary` multi-impl, AOP proxies, generics erasure, full classpath |

Java trees prefer the **Python** indexer (Spring-aware). Rust Core has partial parity; CI: `tests/test_engine_parity.py`.

## Benchmarks

| Suite | Meaning |
|---|---|
| `local` / `public` | Acceptance / smoke |
| `ground-truth` | Labeled P/R (`benchmarks/ground-truth/`) |

PetClinic human-v2 (adjudicated, **not** dual-human): [`benchmarks/petclinic-human-v2.md`](benchmarks/petclinic-human-v2.md).  
`git grep Person` vs impact: [`benchmarks/petclinic-person-grep-vs-impact.md`](benchmarks/petclinic-person-grep-vs-impact.md) (analysis pack only — not LLM Agent A/B).  
Honest misses: [`FAILURE_CASES.md`](FAILURE_CASES.md).

## Authorize ≠ sandbox

Default verify uses disposable worktree/copy, scrubbed env, timeouts, FS diff. Not a kernel/container jail. See [`SECURITY.md`](../SECURITY.md).
