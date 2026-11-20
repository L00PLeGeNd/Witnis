# Trusted Agent Loop

**Product definition:** evidence-backed blast-radius for agent changes, the same envelope on MCP and GitHub PRs, gated verify, and Harnis as a **stdio MCP seatbelt** (not an OS sandbox).

```text
Agent intent
   ├─► Witnis look / impact / pr-gate   (claims + evidence statuses)
   ├─► PR/CI sticky comment + check    (distribution)
   ├─► plan-verify → authorize → verify (proof)
   └─► Harnis mcp/hooks                (what tools may run)
```

## Four gates

| Gate | What it does | What it is not |
| --- | --- | --- |
| Witnis evidence | Index, impact, envelopes (`observed` / `derived` / `verified` / `stale` / `contradicted` / …) | Full program proof or runtime tracing |
| PR gate | `witnis pr-gate` three-dot (`base...head`) markdown + Action | “Human approved” stamp |
| Gated verify | `WITNIS_ALLOW_VERIFY=1` + `--execute`; soft isolate | Container/cgroup jail |
| Harnis | Proxy `tools/call` + path `resources/read`; optional editor hooks | Kernel sandbox |

## One-command bootstrap

```bash
cd /path/to/your-repo
uvx witnis loop-init
# → .witnis/mcp.loop.json  (npx harnis … -- witnis mcp + absolute WITNIS_DB)
# → .harnis/policy.json    (coding-agent seatbelt; left alone if already present)
# → index under .witnis/index.sqlite
```

Flags: `--no-harnis` · `--deny-verify` · `--python-harnis` · `--no-index`.  
Merge `mcp.loop.json` into Claude Code / Cline / Cursor. Harnis remains a separate package ([npm](https://www.npmjs.com/package/harnis) / PyPI); Witnis only writes the wrap.

Copy-paste seed (policy + MCP example + Action): [`examples/witnis-harnis-starter/`](../examples/witnis-harnis-starter/).

## CLI

```bash
witnis index .          # incremental by default; --full only when needed
witnis refresh          # after local edits / pull
witnis pr-gate --base origin/main --head HEAD --format markdown -o pr-gate.md
witnis export-bundle --target <symbol> -o bundle.json
# plan included by default (state blocked until authorized)
WITNIS_ALLOW_VERIFY=1 witnis pr-gate --base origin/main --head HEAD --execute-verify
```

`--strict` fails the process on failed / uncertain / contradicted signals.

## GitHub Action

- Composite: [`.github/actions/pr-gate`](../.github/actions/pr-gate/action.yml)
- Consumer example: [`examples/github-actions/witnis-pr-gate.yml`](../examples/github-actions/witnis-pr-gate.yml)
- Dogfood in this repo: CI job `pr-gate-dogfood` on every PR (sticky comment + check); `pr-gate-smoke` on push (`HEAD~1...HEAD`, no comment)

Permissions: `contents: read`, `pull-requests: write`, `checks: write`. Fetch full history (`fetch-depth: 0`).

Default PR runs **do not** execute verify. Optional `workflow_dispatch` + secret `WITNIS_ALLOW_VERIFY=1`.

## MCP + Harnis

Default path: **`witnis loop-init`** (Harnis accessory on by default).

Hand templates:

- [`examples/mcp.example.json`](../examples/mcp.example.json) — Witnis alone
- [`examples/mcp.witnis-behind-harnis.json`](../examples/mcp.witnis-behind-harnis.json) — seatbelt wrap
- [`examples/mcp.cline.json`](../examples/mcp.cline.json)
- [`examples/mcp.claude-code.json`](../examples/mcp.claude-code.json)
- [`examples/policy.harnis-deny-verify.json`](../examples/policy.harnis-deny-verify.json) — optional Harnis deny of `run_verification`

Honest wrap (what `loop-init` emits):

```text
npx -y harnis mcp --preset coding-agent --policy <abs>/.harnis/policy.json -- witnis mcp
```

Set absolute `WITNIS_DB`. Use Harnis hooks for editor Shell/Write ([Harnis `examples/hooks.json`](https://github.com/L00PLeGeNd/Harnis/blob/main/examples/hooks.json)).

## Versus Blastline / impact-only Actions

They comment reachability / tests. Witnis comments **evidence statuses**, **limitations**, **blocked vs automation-verified**, and pairs with **Harnis**. Do not claim monopoly or superior graphs; claim the loop.

## Failure cases (expected)

Full gallery (F1–F10): [`FAILURE_CASES.md`](FAILURE_CASES.md).

- Index STALE vs live HEAD → warning banner; re-index (**F6**)
- Single-commit `change-impact` ≠ full PR → use `pr-gate` (**F5**)
- `state=verified` after execute → **automation only**, skipped ≠ human review (**F7**)
- Harnis without wrap / without hooks → unconstrained host tools (**F8**)
- Symlink / renamed tools / URL MCP → see Harnis threat model (**F8**)

## Security references

- [`SECURITY.md`](../SECURITY.md) — authorize ≠ sandbox
- [Harnis `THREAT_MODEL.md`](https://github.com/L00PLeGeNd/Harnis/blob/main/THREAT_MODEL.md) — seatbelt scope
