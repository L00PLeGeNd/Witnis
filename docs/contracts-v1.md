# Witnis v1 stable contracts

**Contract version:** `stable` (reported by `witnis capabilities`)  
**Package version:** `1.11.1` (keep in sync with `pyproject.toml` / `Cargo.toml`)

## Envelope (all tools)

Every Core/MCP/CLI JSON payload includes:

- `status`: `success` | `partial` | `failed`
- `repository`: `{ name, root_path, revision? }` or `null`
- `result`: tool-specific object
- `evidence`: typed items with `status` (`observed` | `derived` | `verified` | `unverified` | `contradicted` | `stale` | `failed` | `skipped` | `uncertain` | …)
- `limitations`: human-readable caveats
- `generated_at`: ISO-8601 UTC

### Evidence status legend (product)

| Status | Meaning |
| --- | --- |
| `observed` | Seen in git or index |
| `derived` | Inferred from relations / hunk overlap |
| `verified` | An allowlisted **automation** step passed |
| `unverified` / `uncertain` | Weak or incomplete signal |
| `stale` | Index revision drifted from live HEAD |
| `contradicted` | Later verify failure undercuts prior comfort |
| `skipped` | Step not executed — **never** means human review |
| `failed` | Step or check failed |

### Verification result honesty

`result.state = verified` after `verify --execute` means **automation_verified** (pytest/compileall/syntax/import-graph allowlist).  
Flags: `automation_verified`, `skipped_only`. Skipped manual/analysis steps do **not** prove human review.

## Stable CLI

`index`, `refresh`, `overview`, `status`, `search`, `trace`, `impact`, `evidence`, `plan-verify`, `verify`, `studio`, `capabilities`, `bench`, `compare-baselines`

## Evolving CLI (Trusted Agent Loop)

`loop-init`, `pr-gate`, `change-impact`, `explain-change`, `compare` — `loop-init` bootstraps MCP×Harnis configs; PR three-dot gate is the supported distribution path; single-commit `change-impact` remains for tip commits.

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
