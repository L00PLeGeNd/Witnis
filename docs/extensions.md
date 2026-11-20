# Extension points (contracts-safe)

How to extend Witnis without breaking the Trusted Agent Loop envelope.

## What “extension” means here

| Kind | OK | Not OK |
| --- | --- | --- |
| New **read-only** Core analysis behind existing envelope fields | yes | Inventing a second evidence schema |
| Adapter (CLI flag, MCP tool alias, Studio card) calling Core | yes | Bypassing `status` / `evidence` / `limitations` |
| Optional native (`witnis._native`) accelerating the same path | yes | Silent behavior change when native is missing |
| Harnis policy / wrap around `witnis mcp` | yes (separate repo) | Claiming Harnis is an OS sandbox |
| Vector / RAG plugin | optional, out of Core | Shipping as default witness |

Stable shapes: [`contracts-v1.md`](contracts-v1.md).  
Rust port order: [`rust-full-binary.md`](rust-full-binary.md).

## Seams (preferred order)

1. **Core library** (`src/witnis/core/…` or `crates/witnis-core`) — pure functions that return envelope-ready dicts / structs.  
2. **CLI / MCP adapters** — thin parsers that call Core; no new trust semantics.  
3. **Verify allowlist** — add steps only with isolation + honesty flags (`automation_verified`, never pretend human review).  
4. **Fixtures + benches** — every new claim needs a fixture and a FAILURE_CASES note if it can miss.

## Adding a Core tool (checklist)

1. Define result fields against `contracts-v1.md` (envelope + evidence statuses).  
2. Implement in Core; keep Python path working if Rust/native is absent.  
3. Wire CLI and/or MCP with the **same** JSON.  
4. Add a fixture or ground-truth task; link honest misses in [`FAILURE_CASES.md`](FAILURE_CASES.md).  
5. Update `witnis capabilities` / `witnis-core parity` if the surface is binary-relevant.  
6. Do **not** bump “leadership” marketing copy for a single new edge type.

## Explicit non-extension points (for now)

- LLM Agent A/B **execution** (paused; analysis pack is not)  
- Java AOP / transaction deep dive  
- Historical Knowledge store  
- Marketplace GitHub App (Action-first stays)  
- Studio redesign beyond the browser demo  

## Related

- [`adopter-path.md`](adopter-path.md) — day-2 workflow  
- [`SECURITY.md`](../SECURITY.md) — gate ≠ sandbox  
- [`community/good-first-issue-pipeline.md`](community/good-first-issue-pipeline.md) — where newcomer extensions start  
