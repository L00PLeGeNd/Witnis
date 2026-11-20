# Binary installs vs pip

**Ship a small native binary where it helps; Python `pip` / `uvx` is the full product.**

## What the binary is

| Artifact | Commands | Not included |
| --- | --- | --- |
| `witnis-core` (Rust) | `discover` · `scan` · `index` · `search` · `overview` · `parity` | `look` · `pr-gate` · `verify` · MCP · Studio · `loop-init` |

Binary name on disk: `witnis-core` (crate `witnis-cli`).  
Full CLI: `uvx witnis` / `pip install witnis`.

```bash
uvx witnis loop-init
uvx witnis pr-gate --base origin/main --head HEAD
```

Scripts: [`scripts/install.sh`](../scripts/install.sh) · [`scripts/install.ps1`](../scripts/install.ps1).

## Build locally

```bash
cargo build -p witnis-cli --release
# → target/release/witnis-core[.exe]
./target/release/witnis-core --help
```

CI: [`.github/workflows/release-binaries.yml`](../.github/workflows/release-binaries.yml) (`workflow_dispatch` or tag `v*.*.*`).

## Honesty

- The release binary is **Core**, not a silent reimplementation of the Python adapters.  
- Inspect the live matrix: `witnis-core parity`.  
- Optional: `pip install -e ".[rust]"` + maturin for `witnis._native` — still not the release binary.
