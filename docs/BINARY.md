# Binary installs vs pip fallback

Stage-1 conversion path: **ship a small native binary where it helps**, keep **Python `pip` as the full product**.

## What the binary is

| Artifact | Commands | Not included |
| --- | --- | --- |
| `witnis-core` (Rust) | `discover` · `scan` · `index` · `search` · `overview` · `parity` | `look` · `pr-gate` · `verify` · MCP · Studio · `loop-init` |

Binary name on disk: `witnis-core` (crate `witnis-cli`).  
Full CLI entry point remains `witnis` (`uvx witnis` / `pip install witnis`).

## Full product (not the Core binary)

```bash
uvx witnis loop-init
uvx witnis pr-gate --base origin/main --head HEAD
```

Scripts: [`scripts/install.sh`](../scripts/install.sh) · [`scripts/install.ps1`](../scripts/install.ps1) (pip by default; optional `--core-binary`).

## Build locally

```bash
cargo build -p witnis-cli --release
# → target/release/witnis-core[.exe]
./target/release/witnis-core --help
```

Cross-platform CI: [`.github/workflows/release-binaries.yml`](../.github/workflows/release-binaries.yml)  
- `workflow_dispatch` → artifacts  
- tag `v*` → GitHub Release assets + checksums  

## Honesty

- A “single binary” here is **Core**, not a silent reimplementation of the Python adapters.  
- Full Rust `witnis` sharing all contracts is still **later** ([`rust-migration.md`](rust-migration.md) phase 7 · plan [`rust-full-binary.md`](rust-full-binary.md)).  
- Inspect the live matrix: `witnis-core parity`.  
- Optional speed-up: after a clone, `pip install -e ".[rust]"` + maturin for `witnis._native` — still not the release binary.
