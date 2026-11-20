# Toward a fuller Rust `witnis` binary

Stage-3 planning doc. **Today’s release binary remains `witnis-core`** ([`BINARY.md`](BINARY.md)). Full adapters (MCP, verify, Studio, `loop-init`) stay on Python until contracts move without breakage.

## Parity snapshot

```bash
cargo run -p witnis-cli -- parity
# or: witnis-core parity
```

| Surface | In `witnis-core` | Needs `witnis` (pip) |
| --- | --- | --- |
| discover / scan / index / search / overview | yes | — |
| `impact` (1-hop Direct + 2-hop Transitive `uses_type`) | yes (Phase 7.1) | full envelope + heuristic test slice |
| `parity` (this matrix) | yes | — |
| look / trace / evidence | no | yes |
| pr-gate / change-impact | no | yes |
| plan-verify / verify | no | yes |
| loop-init / mcp / studio / bench / scene | no | yes |

Machine-readable list: `witnis-core parity` → `shipped` / `pip_only` / `next_ports`.

## Phase 7 milestones (not a rewrite clock)

| Step | Goal | Gate |
| --- | --- | --- |
| 7.0 | This doc + `parity` command | landed |
| 7.1 | Port `impact` (read-only 1-hop + 2-hop) + Java Spring edges (`injects`, `uses_type`, typed calls) into Rust Core | landed |
| 7.2 | Port `trace` | Fixture + public bench green |
| 7.3 | Port `pr-gate` core analysis (no GitHub Action glue) | Dogfood Action still calls pip or thin wrapper |
| 7.4 | Decide: thin Rust `witnis` wrapper vs keep pip as product CLI | Explicit ROADMAP call — do not silently drop MCP |

## Rules

1. Evidence envelopes stay identical (`docs/contracts-v1.md`).  
2. Missing Core commands must fail loudly or redirect — never fake `verified`.  
3. Harnis wrap / MCP stay Python until 7.4.  
4. Prefer porting CPU-bound index/impact paths; leave Typer/MCP glue last.

## Related

- [`rust-migration.md`](rust-migration.md) — phases 0–6d done  
- [`BINARY.md`](BINARY.md) — install story  
- [`FAILURE_CASES.md`](FAILURE_CASES.md) — honesty bar for any new Rust claims  
