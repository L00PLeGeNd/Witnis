# Technical depth — honest status

Witnis is an early **engineering witness**: strong product/architecture intent, real local Core, **not** yet a mature cross-language semantic engine.

## What is proven today

- Local index → search / trace / impact → gated verify → CLI / MCP / SDK / Studio loop
- Evidence envelopes with explicit statuses and limitations
- Public **acceptance** suite green (`witnis bench --suite public`)
- Optional Rust acceleration with Python fallback

## What is **not** proven by 21/21

The public suite shows **21 acceptance checks** on self-built fixtures vs grep/regex baselines.

It does **not** show:

- Precision/recall of call graphs on large real repos
- Zero false negatives in impact analysis
- Superiority to mature code indexers (SCIP, LSIF, Kythe, IDE engines)
- That agents make fewer bad edits when using Witnis
- That `verify` cannot false-pass a broken change

Treat `scoreboard 21/21` as CI hygiene, not semantic leadership.

## Language depth (current)

| Language | Depth today | Important gaps |
|---|---|---|
| Python | AST symbols + imports / inherit / decorators / calls | Full name resolution, stubs, dynamic attrs |
| JS/TS | Shallow symbols + imports / calls | Modules, types, framework wiring |
| Go | Shallow symbols + imports / calls | Interfaces, methods across packages |
| Java | Shallow symbols + imports / calls | **DI (`@Autowired`), interface→impl, generics, overloads, AOP, proxies** |

Recognizing a call site ≠ resolving the callee. Spring-style injection is out of scope for the shallow Java path until a dedicated semantic pass exists.

## Dual engines (Python + Rust)

Risk: divergent results, schema drift, platform wheel failures.

Mitigation path: shared contracts + **parity tests** (`tests/test_engine_parity.py`) on fixed fixtures. Prefer one long-term Core; adapters stay multi-surface.

## Authorize gate ≠ sandbox

`WITNIS_ALLOW_VERIFY=1` + `--execute` is an **authorization gate**.

It is **not** OS/container isolation. See [`SECURITY.md`](../SECURITY.md). P1 work: temp workspace, timeouts, network deny, stronger allowlists, pre/post FS checks.

## Next investment (ordered)

1. Real-repo ground truth (P/R, impact recall, false-pass rate) — [`benchmarks/ground-truth/`](../benchmarks/ground-truth/)
2. Deeper relations for the four languages we already claim (Java DI first)
3. Verify isolation
4. Python/Rust parity as a merge gate

Plan notes: [`superpowers/plans/2026-11-03-depth-over-surface.md`](superpowers/plans/2026-11-03-depth-over-surface.md)
