# Witnis v1 stable contracts

**Contract version:** `stable` (reported by `witnis capabilities`)  
**Package version:** `1.9.0` (keep in sync with `pyproject.toml` / `Cargo.toml`)

## Envelope (all tools)

Every Core/MCP/CLI JSON payload includes:

- `status`: `success` | `partial` | `failed`
- `repository`: `{ name, root_path, revision? }` or `null`
- `result`: tool-specific object
- `evidence`: typed items with `status` (`observed` | `derived` | `verified` | `unverified` | `contradicted` | `stale` | …)
- `limitations`: human-readable caveats
- `generated_at`: ISO-8601 UTC

## Stable CLI

`index`, `refresh`, `overview`, `status`, `search`, `trace`, `impact`, `evidence`, `plan-verify`, `verify`, `studio`, `capabilities`, `bench`, `compare-baselines`

## Stable MCP

`repo_overview`, `repo_status`, `repo_search`, `trace_symbol`, `analyze_impact`, `get_evidence`, `create_verification_plan`, `run_verification`, `get_verification_report`, `list_capabilities`, `render_studio`

## Verification gate

`run_verification` / `witnis verify --execute` requires `WITNIS_ALLOW_VERIFY=1`.  
Without authorization, state is `blocked`.

## Compatibility promise (local v1)

- Stable names above will not be removed without a major version bump.
- Additional CLI/MCP tools may appear; treat non-stable names as evolving.
- Evidence statuses remain the primary uncertainty model (not a single float score).

## Out of contract

- Public GitHub publish timing
- Deep LSP / additional languages beyond Python + shallow JS/TS
- Cloud multi-tenant hosting
