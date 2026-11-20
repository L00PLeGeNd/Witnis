# Extension points

Extend Witnis without breaking the evidence envelope.

| Kind | OK | Not OK |
| --- | --- | --- |
| New read-only Core analysis behind existing envelope fields | yes | A second evidence schema |
| CLI / MCP adapter calling Core | yes | Bypassing `status` / `evidence` / `limitations` |
| Optional native (`witnis._native`) on the same path | yes | Silent change when native is missing |
| Harnis wrap around `witnis mcp` | yes (separate repo) | Claiming Harnis is an OS sandbox |

Stable shapes: [`contracts-v1.md`](contracts-v1.md).

## Seams

1. Core (`src/witnis/core/…` or `crates/witnis-core`) — envelope-ready results.  
2. CLI / MCP — thin adapters; no new trust semantics.  
3. Verify allowlist — isolation + `automation_verified` honesty only.  
4. Fixtures + benches — new claims need a fixture; link misses in [`FAILURE_CASES.md`](FAILURE_CASES.md).

## Not in scope right now

- LLM Agent A/B execution  
- Java AOP / full classpath  
- Marketplace GitHub App  
- Studio redesign beyond `witnis browser-demo`

See [`SECURITY.md`](../SECURITY.md).
